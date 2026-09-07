"""Bounded materialization and frozen FCN forward passes; labels read separately."""
from pathlib import Path
import time
import numpy as np
from orientbench.r017.run_pilot import acquire, _local, _normalise
from orientbench.r018.evaluate import read, write, digest
from orientbench.r018.metrics import rasterize_direct


class Assets:
    def __init__(self,root,dataset,out,manifest,cfg,device):
        self.root,self.dataset,self.out,self.manifest,self.cfg,self.device=root,dataset,out,manifest,cfg,device
        self.start=time.monotonic()
        self.forward_seconds,self.forward_images,self.prediction_bytes=0.,0,0
        write(out/'download_ledger.json',[])
        self.evidence={'existing':{},'images':{},'labels':{},'new_predictions':{}}
        self.records={(r['split'],r['tile'],r['view']):r for r in manifest['images_to_materialize']}
        self.labels={r['tile']:r for r in manifest['labels']}
        self.old={}
        for task in ('r018','r019','r020'):
            path=root/f'runs/{task}/artifacts/input_bindings.json'
            review=read(root/f'doc/{task.upper()}_B_REVIEW_20260907.json')
            if digest(path)!=review['source_hashes']['input_bindings.json']:
                raise ValueError('accepted previous input bindings changed')
            self.old[task]=read(path)
        self.old_cal_hashes={r['file']:r['sha256'] for r in read(root/'doc/R018_B_REVIEW_20260907.json')['prediction_files']}
        if digest(root/'configs/r017/data_manifest.json')!=cfg['old_manifest_sha256']:
            raise ValueError('original development cohort changed')
        if abs(read(root/'runs/r017/artifacts/training_loss_definition.json')['foreground_fraction']-cfg['foreground_fraction'])>1e-14:
            raise ValueError('actual frozen loss weights changed')
        for seed in (1701,1702):
            path=root/f'runs/r017/artifacts/checkpoints/seed{seed}_epoch30.pt'
            if digest(path)!=cfg['checkpoint_sha256'][str(seed)]:
                raise ValueError('frozen model changed')

    def budget(self):
        if time.monotonic()-self.start>self.cfg['wall_hours_total']*3600:
            raise RuntimeError('fixed wall-clock budget exhausted')

    def acquire_images(self,splits):
        items=[r for r in self.manifest['images_to_materialize'] if r['split'] in splits]
        acquire(items,self.dataset,self.out/'download_ledger.json',self.cfg['download_bytes_limit'])
        for r in items:
            self.evidence['images'][r['key']]=digest(_local(self.dataset,r['key']))

    def image(self,split,tile,view):
        import rasterio
        import torch
        import torch.nn.functional as F
        path=_local(self.dataset,self.records[split,tile,view]['key'])
        x0,y0=map(int,tile.split('_'))
        with rasterio.open(path) as ds:
            if (ds.width,ds.height,ds.count)!=(900,900,4) or ds.crs.to_epsg()!=32616:
                raise ValueError('unexpected native raster grid')
            if not np.allclose(tuple(ds.transform)[:6],(.5,0,x0,0,-.5,y0+450),rtol=0,atol=1e-8):
                raise ValueError('native ground/tile identity mismatch')
            raw=ds.read((1,2,3)).astype(np.float32)
            valid=np.all(np.isfinite(raw),axis=0)&np.all(ds.read_masks((1,2,3))>0,axis=0)
            if ds.nodata is not None:
                valid &= ~np.any(raw==ds.nodata,axis=0)
        if not valid.all():
            raise ValueError('fixed full support changed; no selective region dropping')
        # Preserve the actual r017 model input, including the float16 cache step.
        image=F.interpolate(torch.from_numpy(raw)[None],size=(448,448),mode='bilinear',align_corners=False)[0]
        return image.numpy().astype(np.float16).astype(np.float32)

    def forward(self,splits,seeds):
        import torch
        from torchvision.models.segmentation import fcn_resnet50
        for seed in seeds:
            checkpoint=torch.load(self.root/f'runs/r017/artifacts/checkpoints/seed{seed}_epoch30.pt',map_location='cpu',weights_only=True)
            if checkpoint['seed']!=seed or checkpoint['epoch']!=30:
                raise ValueError('wrong model metadata')
            model=fcn_resnet50(weights=None,weights_backbone=None,num_classes=1,aux_loss=False)
            model.load_state_dict(checkpoint['model'],strict=True)
            model.to(self.device).eval()
            with torch.inference_mode():
                for split in splits:
                    views=self.manifest['held_views'] if split=='held' else self.manifest['new_development_views']
                    tiles=self.manifest[split+'_tiles']
                    directory=self.out/'predictions'/split/str(seed)
                    directory.mkdir(parents=True,exist_ok=True)
                    for tile in tiles:
                        self.budget()
                        image=np.stack([self.image(split,tile,v) for v in views])
                        tick=time.monotonic()
                        x=torch.from_numpy(image).to(self.device)
                        p=torch.sigmoid(model(_normalise(x))['out'][:,0]).cpu().numpy()
                        self.forward_seconds+=time.monotonic()-tick
                        self.forward_images+=len(views)
                        if p.shape!=(4,448,448) or not np.isfinite(p).all():
                            raise ValueError('invalid complete predictions')
                        path=directory/f'{tile}.npz'
                        np.savez_compressed(path,base=p)
                        self.prediction_bytes+=path.stat().st_size
                        self.evidence['new_predictions'][str(path.relative_to(self.out))]=digest(path)
                        if self.forward_seconds>self.cfg['gpu_hours_total']*3600 or self.prediction_bytes>self.cfg['prediction_bytes_limit']:
                            raise RuntimeError('fixed inference or prediction size limit exceeded')
                    print(f'Finished {split} seed{seed}: {len(tiles)} regions',flush=True)
            del model,checkpoint,x
            if self.device.startswith('cuda'):
                torch.cuda.empty_cache()

    def probabilities(self,split,tile,seeds=(1701,1702)):
        result=[]
        for seed in seeds:
            path=self.out/'predictions'/split/str(seed)/f'{tile}.npz'
            with np.load(path) as z:
                new=z['base']
            if split=='held':
                result.append(new)
                continue
            if split=='fit':
                task='r019' if seed==1701 else 'r020'
                directory='train_predictions' if seed==1701 else 'train_predictions_seed1702'
                key='train_predictions' if seed==1701 else 'new_train_predictions'
                old_path=self.root/f'runs/{task}/artifacts'/directory/f'{tile}.npz'
                expected=self.old[task][key][tile]
            else:
                old_path=self.root/'runs/r018/artifacts/predictions'/f'seed{seed}_{tile}.npz'
                expected=self.old_cal_hashes[old_path.name]
            if digest(old_path)!=expected:
                raise ValueError('accepted old probability changed')
            self.evidence['existing'][str(old_path.relative_to(self.root))]=expected
            with np.load(old_path) as z:
                old=z['base']
            result.append(np.concatenate([old,new]))
        return np.stack(result)

    def development_label(self,split,tile):
        path=self.root/'runs/r017/artifacts/cache'/('train' if split=='fit' else 'calibration')/f'{tile}.npz'
        if digest(path)!=self.old['r018']['cache'][tile]:
            raise ValueError('original training target changed')
        with np.load(path) as z:
            y,v=z['label'],z['valid']
        if y.shape!=(448,448) or not v.all():
            raise ValueError('previous full target support changed')
        return y

    def acquire_held_labels(self):
        acquire([self.labels[t] for t in self.manifest['held_tiles']],self.dataset,self.out/'download_ledger.json',self.cfg['download_bytes_limit'])

    def held_labels(self,tile):
        import torch
        import torch.nn.functional as F
        path=_local(self.dataset,self.labels[tile]['key'])
        payload=read(path)
        self.evidence['labels'][tile]=digest(path)
        x0,y0=map(int,tile.split('_'))
        transform=(.5,0,x0,0,-.5,y0+450)
        fine=rasterize_direct(payload,transform,'EPSG:32616',side=900)
        actual=F.interpolate(torch.from_numpy(fine.astype(np.float32))[None,None],size=(448,448),mode='nearest')[0,0].numpy()>.5
        return actual,rasterize_direct(payload,transform,'EPSG:32616')

    def save_evidence(self):
        write(self.out/'input_bindings.json',self.evidence)
        return {'new_forward_images':self.forward_images,'inference_seconds':self.forward_seconds,
                'wall_seconds':time.monotonic()-self.start,'new_prediction_bytes':self.prediction_bytes,
                'downloaded_bytes':sum(r.get('received_bytes',0) for r in read(self.out/'download_ledger.json')),
                'new_network_fits':0}
