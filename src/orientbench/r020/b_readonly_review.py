"""Independent B CPU replay of fixed r020 actions and spatial summaries."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import numpy as np


def read(path):
    return json.loads(path.read_text())


def review(root, dataset):
    start = datetime.now(timezone.utc).isoformat()
    url = subprocess.check_output(['git','-C',str(root),'remote','get-url','origin'],text=True).strip()
    if url not in ('https://github.com/ziyu24/orientbench.git','https://github.com/ziyu24/orientbench'):
        raise ValueError('wrong repository')
    sys.path.insert(0,str(root/'src'))
    from orientbench.r018.b_readonly_review import loss, sha
    from affine import Affine
    from rasterio.crs import CRS
    from rasterio.features import rasterize
    original, prior, control, out = [root/f'runs/r{n}/artifacts' for n in ('017','018','019','020')]
    manifest = read(root/'configs/r017/data_manifest.json')
    cfg = read(root/'configs/r020/protocol.json')
    bindings, frozen, saved = [read(out/f) for f in ('input_bindings.json','frozen_shifts.json','summary.json')]
    if sha(root/'configs/r017/data_manifest.json') != cfg['data_manifest_sha256']:
        raise ValueError('cohort changed')
    for seed in (1701,1702):
        if sha(original/'checkpoints'/f'seed{seed}_epoch30.pt') != cfg['checkpoint_sha256'][str(seed)]:
            raise ValueError('checkpoint changed')
    if sha(control/'frozen_shifts.json') != bindings['first_model_shifts']:
        raise ValueError('first-model calibration changed')
    if frozen['1701'] != read(control/'frozen_shifts.json')['shifts']:
        raise ValueError('first model shifts not reused exactly')
    pi = cfg['foreground_fraction']
    crop = lambda p,dy=0,dx=0:p[...,32+dy:416+dy,32+dx:416+dx]
    train = np.zeros((4,2))
    for tile in manifest['training_tiles']:
        cp,pp=original/'cache/train'/f'{tile}.npz',out/'train_predictions_seed1702'/f'{tile}.npz'
        if sha(cp)!=bindings['train_cache'][tile] or sha(pp)!=bindings['new_train_predictions'][tile]:
            raise ValueError('training input changed')
        with np.load(cp) as z:
            y,v=crop(z['label']),crop(z['valid'])
        with np.load(pp) as z:
            p=z['base']
        for i,s in enumerate(frozen['1702']):
            for j,(dy,dx) in enumerate(((0,0),(s['dy'],s['dx']))):
                train[i,j]+=loss(crop(p[i],dy,dx),y,v,pi)/256
    with np.load(out/'second_model_training_surfaces.npz') as z:
        surfaces=z['surfaces']
    training_error=0.
    for i,s in enumerate(frozen['1702']):
        shifts=[tuple(map(int,q-32)) for q in np.argwhere(surfaces[i]<=surfaces[i].min()+1e-12)]
        expected=min(shifts,key=lambda q:(q[0]**2+q[1]**2,q[0],q[1]))
        if expected!=(s['dy'],s['dx']):
            raise ValueError('frozen shift is not saved surface minimum')
        for j,(dy,dx) in enumerate(((0,0),expected)):
            training_error=max(training_error,abs(train[i,j]-surfaces[i,32+dy,32+dx]))
    names=('actual_cached_labels','direct448_label_sensitivity')
    arms=('zero_core','aligned_core')
    tables={n:{a:read(out/f'{n}_{a}_rows.json') for a in arms} for n in names}
    lookup={n:{a:{r['tile']:r for r in rows} for a,rows in ts.items()} for n,ts in tables.items()}
    for ts in tables.values():
        for rows in ts.values():
            if len(rows)!=128 or {r['tile'] for r in rows}!=set(manifest['calibration_tiles']):
                raise ValueError('incomplete or duplicate rows')
    labels={r['tile']:r for r in manifest['labels']}
    probability_error,iou_error=0.,0
    for tile in manifest['calibration_tiles']:
        cp=original/'cache/calibration'/f'{tile}.npz'
        if sha(cp)!=bindings['calibration_cache'][tile]:
            raise ValueError('calibration cache changed')
        with np.load(cp) as z:
            y,v=z['label'],crop(z['valid'])
        bases=[]
        for seed in (1701,1702):
            pp=prior/'predictions'/f'seed{seed}_{tile}.npz'
            if sha(pp)!=bindings['calibration_predictions'][pp.name]:
                raise ValueError('calibration predictions changed')
            with np.load(pp) as z:
                bases.append(z['base'].astype(np.float64))
        key=labels[tile]['key'].split('spacenet/SN4_buildings/train/AOI_6_Atlanta/')[1]
        lp=dataset/'SpaceNet4/train'/key
        if sha(lp)!=bindings['labels'][tile]:
            raise ValueError('native label changed')
        payload=read(lp)
        assert CRS.from_user_input(payload['crs']['properties']['name']).to_epsg()==32616
        x0,y0=map(int,tile.split('_'))
        shapes=[(f['geometry'],1) for f in payload['features']]
        direct=(rasterize(shapes,out_shape=(448,448),transform=Affine(450/448,0,x0,0,-450/448,y0+450),
                          all_touched=False,dtype='uint8').astype(bool) if shapes else np.zeros((448,448),bool))
        for name,target in zip(names,(y,direct)):
            target=crop(target)
            for arm in arms:
                ps=[]
                for i,seed in enumerate((1701,1702)):
                    shifts=frozen[str(seed)] if arm=='aligned_core' else [{'dy':0,'dx':0}]*4
                    ps.append(np.stack([crop(bases[i][j],s['dy'],s['dx']) for j,s in enumerate(shifts)]))
                p,q=ps
                maps={'same_a':(p[0]+q[0])*.5,'same_b':(p[1]+q[1])*.5}
                for pair,i,j in (('av',0,3),('au',0,2),('bu',1,2),('bv',1,3)):
                    maps[pair+'_12']=(p[i]+q[j])*.5
                    maps[pair+'_21']=(q[i]+p[j])*.5
                values={f'loss_{k}':loss(prob,target,v,pi) for k,prob in maps.items()}
                for pair in ('av','au','bu','bv'):
                    values['loss_'+pair]=(values['loss_'+pair+'_12']+values['loss_'+pair+'_21'])*.5
                values['gain_a']=values['loss_same_a']-values['loss_av']
                values['gain_b']=values['loss_same_b']-values['loss_bu']
                values['crossed_i']=(values['loss_au']-values['loss_av']+values['loss_bv']-values['loss_bu'])*.5
                row=lookup[name][arm][tile]
                probability_error=max(probability_error,max(abs(row[k]-value) for k,value in values.items()))
                for k,prob in maps.items():
                    pred=prob>=.5
                    counts=(int((pred&target&v).sum()),int(((pred|target)&v).sum()))
                    iou_error=max(iou_error,*(abs(c-row[f'iou_{k}_{s}']) for c,s in zip(counts,('intersection','union'))))
    block=lambda t:tuple(int(v)//2700 for v in t.split('_'))
    blocks=list(dict.fromkeys(map(block,manifest['calibration_tiles'])))
    index=np.random.Generator(np.random.PCG64(17017)).integers(0,16,(20000,16))
    aggregate_error=0.
    recomputed={}
    for name,ts in tables.items():
        recomputed[name]={}
        for arm,rows in ts.items():
            keys=[k for k in rows[0] if k.startswith(('loss_','gain_')) or k=='crossed_i']
            vals={k:np.array([np.mean([r[k] for r in rows if block(r['tile'])==b]) for b in blocks]) for k in keys}
            means={k:float(x.mean()) for k,x in vals.items()}
            ci={k:np.quantile(v[index].mean(1),[.0125,.9875]).tolist() for k,v in vals.items() if k.startswith('gain_')}
            ci95={k:np.quantile(v[index].mean(1),[.025,.975]).tolist() for k,v in vals.items()}
            for k in keys:
                aggregate_error=max(aggregate_error,abs(means[k]-saved[name][arm]['means'][k]),
                                    *np.abs(np.array(ci95[k])-saved[name][arm]['descriptive_95_intervals'][k]))
            for k in ci:
                aggregate_error=max(aggregate_error,*np.abs(np.array(ci[k])-saved[name][arm]['two_primary_bonferroni_97_5_intervals'][k]))
            iou={}
            for key in rows[0]:
                if key.startswith('iou_') and key.endswith('_intersection'):
                    uk=key.replace('_intersection','_union')
                    ratios=[]
                    for b in blocks:
                        group=[r for r in rows if block(r['tile'])==b]
                        den=sum(r[uk] for r in group)
                        ratios.append(None if den==0 else sum(r[key] for r in group)/den)
                    metric=key[4:-13]
                    iou[metric]=None if None in ratios else float(np.mean(ratios))
                    if iou[metric] is None:
                        assert saved[name][arm]['iou'][metric]['mean'] is None
                    else:
                        aggregate_error=max(aggregate_error,abs(iou[metric]-saved[name][arm]['iou'][metric]['mean']))
            for pair in ('av','au','bu','bv'):
                values=[iou[pair+'_'+a] for a in ('12','21')]
                mean=None if None in values else float(np.mean(values))
                reported=saved[name][arm]['iou'][pair+'_assignment_average']
                if mean is None:
                    assert reported is None
                else:
                    aggregate_error=max(aggregate_error,abs(mean-reported))
                iou[pair+'_assignment_average']=mean
            recomputed[name][arm]={'means':means,'primary_97_5_intervals':ci,'iou':iou}
    if max(training_error,probability_error,aggregate_error)>1e-10 or iou_error:
        raise ValueError('independent replay differs')
    return {'observed_start_utc':start,'observed_end_utc':datetime.now(timezone.utc).isoformat(),
            'scope':'Read-only CPU replay: 256 second-model training tiles, both models on128 calibration tiles, four row tables. No forward, fitting or server writes. Saved surface minima checked; unselected surface values not recomputed.',
            'training_max_abs_difference':float(training_error),'probability_metric_max_abs_difference':float(probability_error),
            'iou_count_max_abs_difference':int(iou_error),'aggregate_max_abs_difference':float(aggregate_error),
            'recomputed':recomputed,'reported_resources':saved['resources'],
            'source_hashes':{p.name:sha(p) for p in out.glob('*.json')}}


if __name__=='__main__':
    print(json.dumps(review(Path('/home/rspip/cqc/study/orientbench'),Path('/home/rspip/cqc/data/dataset'))),flush=True)
