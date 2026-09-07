"""Calibrate only the second existing model, then compare fixed two-call actions."""
import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys
import time
import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from orientbench.r017.run_pilot import _local, _normalise
from orientbench.r017.measurement import weighted_log_loss
from orientbench.r018.evaluate import digest, read, write
from orientbench.r018.metrics import rasterize_direct
from orientbench.r019.registration import check_support, loss_surface, select_shift, shifted_core
from orientbench.r020.metrics import measure, summarise


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project-root',type=Path,default=Path.cwd())
    parser.add_argument('--dataset-root',type=Path,required=True)
    parser.add_argument('--out',type=Path,required=True)
    parser.add_argument('--device',default='cuda:0')
    args=parser.parse_args()
    root,out=args.project_root.resolve(),args.out.resolve()
    if not out.is_relative_to(root/'runs/r020'):
        raise ValueError('new artifacts must stay in runs/r020')
    out.mkdir(parents=True,exist_ok=False)
    start=time.monotonic()
    cfg=read(root/'configs/r020/protocol.json')
    old, previous, control=[root/f'runs/r{n}/artifacts' for n in ('017','018','019')]
    manifest_path=root/'configs/r017/data_manifest.json'
    if digest(manifest_path)!=cfg['data_manifest_sha256']:
        raise ValueError('frozen cohort changed')
    manifest=read(manifest_path)
    train,cal=manifest['training_tiles'],manifest['calibration_tiles']
    if len(train)!=256 or len(cal)!=128 or set(train)&set(cal):
        raise ValueError('frozen train/calibration identity changed')
    audit18,audit19=[read(root/f'doc/R0{n}_B_REVIEW_20260907.json') for n in (18,19)]
    if digest(previous/'input_bindings.json')!=audit18['source_hashes']['input_bindings.json']:
        raise ValueError('r018 input bindings changed')
    if digest(control/'frozen_shifts.json')!=audit19['source_hashes']['frozen_shifts.json']:
        raise ValueError('B-accepted first model shifts changed')
    bindings=read(previous/'input_bindings.json')
    first=read(control/'frozen_shifts.json')['shifts']
    pi,margin=cfg['foreground_fraction'],cfg['margin_pixels']
    if abs(read(old/'training_loss_definition.json')['foreground_fraction']-pi)>1e-14:
        raise ValueError('training weights changed')
    checkpoints={s:old/'checkpoints'/f'seed{s}_epoch30.pt' for s in (1701,1702)}
    for s,p in checkpoints.items():
        if digest(p)!=cfg['checkpoint_sha256'][str(s)]:
            raise ValueError('existing model changed')
    evidence={'protocol':digest(root/'configs/r020/protocol.json'),'manifest':digest(manifest_path),
              'first_model_shifts':digest(control/'frozen_shifts.json'),'train_cache':{},
              'new_train_predictions':{},'calibration_cache':{},'calibration_predictions':{},'labels':{}}

    def budget():
        if time.monotonic()-start>cfg['wall_hours_total']*3600:
            raise RuntimeError('fixed total time budget exhausted')

    def load_cache(split,tile,images=False):
        path=old/'cache'/split/f'{tile}.npz'
        h=digest(path)
        if h!=bindings['cache'][tile]:
            raise ValueError('existing cache changed')
        evidence[split+'_cache'][tile]=h
        with np.load(path) as z:
            x,y,v=z['image'] if images else None,z['label'],z['valid']
        check_support(y,v,448)
        if images and x.shape!=(4,3,448,448):
            raise ValueError('wrong four-view image shape')
        return x,y,v

    import torch
    from torchvision.models.segmentation import fcn_resnet50
    checkpoint=torch.load(checkpoints[1702],map_location='cpu',weights_only=True)
    if checkpoint['seed']!=1702 or checkpoint['epoch']!=30:
        raise ValueError('wrong second model metadata')
    model=fcn_resnet50(weights=None,weights_backbone=None,num_classes=1,aux_loss=False)
    model.load_state_dict(checkpoint['model'],strict=True)
    model.to(args.device).eval()
    predictions=out/'train_predictions_seed1702'
    predictions.mkdir()
    inference_seconds,saved_bytes=0.,0
    with torch.inference_mode():
        for index,tile in enumerate(train):
            budget()
            x,_,_=load_cache('train',tile,images=True)
            tick=time.monotonic()
            tensor=torch.from_numpy(x.astype(np.float32)).to(args.device)
            p=torch.sigmoid(model(_normalise(tensor))['out'][:,0]).cpu().numpy()
            inference_seconds+=time.monotonic()-tick
            if p.shape!=(4,448,448) or not np.isfinite(p).all():
                raise ValueError('invalid second-model training prediction')
            path=predictions/f'{tile}.npz'
            np.savez_compressed(path,base=p)
            evidence['new_train_predictions'][tile]=digest(path)
            saved_bytes+=path.stat().st_size
            if inference_seconds>cfg['gpu_hours_total']*3600 or saved_bytes>cfg['prediction_bytes_limit']:
                raise RuntimeError('fixed forward/artifact budget exhausted')
            if (index+1)%32==0:
                print(f'Second existing model training predictions: {index+1}/256',flush=True)
    del model,checkpoint,tensor
    if args.device.startswith('cuda'):
        torch.cuda.empty_cache()
    surfaces=np.zeros((4,65,65),dtype=np.float64)
    for tile in train:
        budget()
        _,y,v=load_cache('train',tile)
        with np.load(predictions/f'{tile}.npz') as z:
            p=z['base']
        for i in range(4):
            surfaces[i]+=loss_surface(p[i],y,v,pi,margin)/256
    second=[select_shift(s,margin) for s in surfaces]
    direct=np.zeros((4,2))
    for tile in train:
        budget()
        _,y,v=load_cache('train',tile)
        with np.load(predictions/f'{tile}.npz') as z:
            p=z['base']
        for i,s in enumerate(second):
            for j,(dy,dx) in enumerate(((0,0),(s['dy'],s['dx']))):
                direct[i,j]+=weighted_log_loss(shifted_core(p[i],dy,dx,margin),y[32:416,32:416],v[32:416,32:416],pi)/256
    expected=np.array([[s['train_loss_zero'],s['train_loss_selected']] for s in second])
    error=float(np.max(np.abs(direct-expected)))
    if error>1e-10:
        raise ValueError('training FFT/direct verification failed')
    np.savez_compressed(out/'second_model_training_surfaces.npz',surfaces=surfaces,direct=direct)
    write(out/'frozen_shifts.json',{'frozen_utc':datetime.now(timezone.utc).isoformat(),
          '1701':first,'1702':second,'fft_direct_max_abs_difference':error,'evidence':evidence})

    # Second-model translations are now fixed. No calibration pixels above.
    hashes={p['file']:p['sha256'] for p in audit18['prediction_files']}
    labels={p['tile']:p for p in manifest['labels']}
    rows={name:{arm:[] for arm in ('zero_core','aligned_core')} for name in ('actual_cached_labels','direct448_label_sensitivity')}
    for tile in cal:
        budget()
        _,y,v=load_cache('calibration',tile)
        bases=[]
        for seed in (1701,1702):
            path=previous/'predictions'/f'seed{seed}_{tile}.npz'
            if digest(path)!=hashes[path.name]:
                raise ValueError('B-audited calibration probability changed')
            evidence['calibration_predictions'][path.name]=hashes[path.name]
            with np.load(path) as z:
                bases.append(z['base'])
        if any(p.shape!=(4,448,448) for p in bases):
            raise ValueError('complete four-view maps required')
        p=np.stack(bases)
        aligned=np.stack([np.stack([shifted_core(p[j,i],s['dy'],s['dx'],margin)
                                   for i,s in enumerate(shifts)]) for j,shifts in enumerate((first,second))])
        path=_local(args.dataset_root,labels[tile]['key'])
        if digest(path)!=bindings['labels'][tile]:
            raise ValueError('native label changed')
        evidence['labels'][tile]=bindings['labels'][tile]
        x0,y0=map(int,tile.split('_'))
        direct_y=rasterize_direct(read(path),(.5,0,x0,0,-.5,y0+450),'EPSG:32616')
        for name,target in zip(rows,(y,direct_y)):
            for arm,maps in (('zero_core',p[...,32:416,32:416]),('aligned_core',aligned)):
                rows[name][arm].append({'tile':tile,**measure(maps,target[32:416,32:416],v[32:416,32:416],pi)})
    summary={}
    for name,arms in rows.items():
        summary[name]={}
        for arm,values in arms.items():
            write(out/f'{name}_{arm}_rows.json',values)
            summary[name][arm]=summarise(values,cal)
    summary['resources']={'new_forward_images':1024,'inference_seconds':inference_seconds,
                          'wall_seconds':time.monotonic()-start,'new_prediction_bytes':saved_bytes,'new_network_fits':0}
    summary['shifts']={'1701':first,'1702':second}
    summary['assignment_scope']='Two fixed assignments evaluated; average their losses/IoU, never average their four predictions. Each deployable assignment uses exactly two forwards.'
    write(out/'input_bindings.json',evidence)
    write(out/'summary.json',summary)
    print(summary['actual_cached_labels']['aligned_core']['means'],flush=True)


if __name__=='__main__':
    main()
