"""Read-only B replay of held probabilities, labels, frozen decisions and blocks."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import numpy as np


def review(root,dataset):
    sys.path.insert(0,str(root/'src'))
    from orientbench.r018.evaluate import read,digest
    from orientbench.r017.run_pilot import _local
    from orientbench.r022.run import load_frozen
    from rasterio.features import rasterize
    from rasterio.crs import CRS
    from affine import Affine
    started=datetime.now(timezone.utc).isoformat()
    out=root/'runs/r022/artifacts'
    cfg=read(root/'configs/r022/protocol.json')
    m=read(root/'configs/r021/data_manifest.json')
    if digest(root/'configs/r021/data_manifest.json')!=cfg['data_manifest_sha256']:
        raise ValueError('cohort changed')
    for name,expected in cfg['frozen_source_sha256'].items():
        if digest(root/'runs/r021/artifacts/retry'/name)!=expected:
            raise ValueError('frozen development changed')
        if name in ('forecaster.npz','calibration.json','frozen_shifts.json') and digest(out/name)!=expected:
            raise ValueError('development copy changed')
    bindings=read(out/'input_bindings.json')
    for key,expected in bindings['images'].items():
        if digest(_local(dataset,key))!=expected:
            raise ValueError('image changed')
    for key,expected in bindings['new_predictions'].items():
        if digest(out/key)!=expected:
            raise ValueError('prediction changed')
    decisions=read(out/'decisions.json')
    for file,key in (('forecaster.npz','forecaster_sha256'),('calibration.json','calibration_sha256'),('frozen_shifts.json','shifts_sha256')):
        if digest(out/file)!=decisions[key]:
            raise ValueError('decision inputs changed')
    cal=read(out/'calibration.json')
    model=load_frozen(out/'forecaster.npz',cal)
    shifts=read(out/'frozen_shifts.json')['held']
    geometry=np.array([m['geometry'][v]['look_xy'] for v in m['held_views']])
    names=('transport','independence','geometry','ridge')
    table={(r['tile'],r['anchor']):r for r in decisions['records']}
    expected_keys={(t,i) for t in m['held_tiles'] for i in range(4)}
    if set(table)!=expected_keys or len(decisions['records'])!=256:
        raise ValueError('decision table incomplete or duplicated')
    saved_outcomes={(r['label'],r['tile'],r['anchor']):r['costs'] for r in read(out/'held_action_outcomes.json')}
    labels={r['tile']:r for r in m['labels']}
    rows={k:[] for k in ('actual_labels','direct448_sensitivity')}
    maxima={'forecast':0.,'action_cost':0.,'rows':0.,'summary':0.}
    action_count=np.zeros((4,4),int)
    selected_gain=[];prediction_sizes=0
    for tile in m['held_tiles']:
        maps=[]
        for s,seed in enumerate((1701,1702)):
            path=out/f'predictions/held/{seed}/{tile}.npz'
            prediction_sizes+=path.stat().st_size
            with np.load(path) as z:
                p=z['base'].astype(float)
            if p.shape!=(4,448,448) or not np.isfinite(p).all() or np.any((p<0)|(p>1)):
                raise ValueError('invalid complete probabilities')
            maps.append(np.array([p[j,32+v['dy']:416+v['dy'],32+v['dx']:416+v['dx']] for j,v in enumerate(shifts[s])]))
        first,second=maps
        path=_local(dataset,labels[tile]['key'])
        if digest(path)!=bindings['labels'][tile]:
            raise ValueError('label changed')
        payload=read(path)
        if CRS.from_user_input(payload['crs']['properties']['name'])!=CRS.from_epsg(32616):
            raise ValueError('label coordinate mismatch')
        shapes=[(f['geometry'],1) for f in payload['features']]
        x0,y0=map(int,tile.split('_'))
        transform=Affine(.5,0,x0,0,-.5,y0+450)
        def target(side):
            return rasterize(shapes,out_shape=(side,side),transform=transform*Affine.scale(900/side),
                             fill=0,all_touched=False,dtype='uint8') if shapes else np.zeros((side,side),np.uint8)
        fine=target(900)
        index=np.floor(np.arange(448)*900/448).astype(int)
        actual=fine[np.ix_(index,index)]
        targets=(actual,target(448))
        for i in range(4):
            decision=table[tile,i]
            scores={int(j):s for j,s in decision['scores'].items()}
            if set(scores)!=set(range(4))-{i}:
                raise ValueError('missing candidate')
            actions={}
            for name in names:
                chosen=i;best=0.
                for j in range(4):
                    if j!=i and scores[j][name]>best:
                        chosen,best=j,scores[j][name]
                if chosen!=decision['actions'][name]:
                    raise ValueError('saved action not given by frozen rule')
                actions[name]=chosen
            action_count[i,actions['transport']]+=1
            for j in scores:
                replay=model.predict(first[i],geometry[i],geometry[j])
                maxima['forecast']=max(maxima['forecast'],max(abs(replay[n]-scores[j][n]) for n in names))
            for label,y_full in zip(rows,targets):
                y=y_full[32:416,32:416].astype(float);costs={}
                for j in range(4):
                    q=np.clip((first[i]+second[j])/2,1e-6,1-1e-6)
                    costs[j]=float(np.mean(-y*np.log(q)/(2*model.pi)-(1-y)*np.log1p(-q)/(2*(1-model.pi))))
                    maxima['action_cost']=max(maxima['action_cost'],abs(costs[j]-saved_outcomes[label,tile,i][str(j)]))
                far=max((j for j in range(4) if j!=i),key=lambda j:float(np.sum((geometry[i]-geometry[j])**2)))
                nadir=min(range(4),key=lambda j:float(np.sum(geometry[j]**2)))
                values={n:costs[actions[n]] for n in names}
                values.update(stop=costs[i],max_separation=costs[far],near_nadir=costs[nadir],oracle=min(costs.values()))
                for name in names:
                    errors=np.array([scores[j][name]-(costs[i]-costs[j]) for j in scores])
                    values.update({f'mae_{name}':float(np.abs(errors).mean()),f'bias_{name}':float(errors.mean()),
                                   f'acquire_{name}':float(actions[name]!=i)})
                values.update(policy_gain=values[cal['selected_baseline']]-values['transport'],
                              mae_gain=values['mae_ridge']-values['mae_transport'],
                              transport_oracle_regret=values['transport']-values['oracle'])
                rows[label].append({'tile':tile,'anchor':i,**values})
                if label=='actual_labels':
                    j=actions['transport']
                    selected_gain.append({'anchor':i,'predicted':scores[j]['transport'] if j!=i else 0.,
                                          'actual':costs[i]-costs[j]})
    saved=read(out/'summary.json');summaries={}
    blocks=list(dict.fromkeys(tuple(int(x)//2700 for x in t.split('_')) for t in m['held_tiles']))
    draws=np.random.Generator(np.random.PCG64(17021)).integers(0,len(blocks),(20000,len(blocks)))
    for label,records in rows.items():
        prior={(r['tile'],r['anchor']):r for r in read(out/f'{label}_rows.json')}
        if set(prior)!=expected_keys or len(records)!=256:
            raise ValueError('incomplete risk table')
        keys=[k for k in records[0] if k not in ('tile','anchor')]
        for r in records:
            maxima['rows']=max(maxima['rows'],max(abs(r[k]-prior[r['tile'],r['anchor']][k]) for k in keys))
        values={k:[] for k in keys}
        for b in blocks:
            tiles=[t for t in m['held_tiles'] if tuple(int(x)//2700 for x in t.split('_'))==b]
            for k in keys:
                values[k].append(float(np.mean([np.mean([r[k] for r in records if r['tile']==t]) for t in tiles])))
        means={k:float(np.mean(v)) for k,v in values.items()}
        intervals={k:np.quantile(np.asarray(v)[draws].mean(1),[.0125,.9875]).tolist() for k,v in values.items()}
        for k in keys:
            maxima['summary']=max(maxima['summary'],abs(means[k]-saved[label]['means'][k]),
                float(np.max(np.abs(np.array(intervals[k])-saved[label]['intervals_97_5'][k]))))
        summaries[label]={'means':means,'intervals_97_5':intervals,'block_values':values}
    if max(maxima.values())>1e-10:
        raise ValueError('replay mismatch: '+str(maxima))
    ledger=read(out/'download_ledger.json')
    received=sum(r['received_bytes'] for r in ledger)
    if received!=saved['resources']['downloaded_bytes'] or prediction_sizes!=saved['resources']['new_prediction_bytes']:
        raise ValueError('resource totals differ')
    times={str(seed):[p.stat().st_mtime for p in (out/f'predictions/held/{seed}').glob('*.npz')] for seed in (1701,1702)}
    dt=(out/'decisions.json').stat().st_mtime
    native=read(out/'native_support.json')
    if len(native)!=256 or any(any(v['core_invalid']) for v in native.values()):
        raise ValueError('saved support incomplete')
    return {'observed_start_utc':started,'observed_end_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Read-only full 64 held region / two model probability replay; independent native label raster and loss/block aggregation; frozen forecast replay reuses original predictor, not an independent model implementation. No forward, fitting or server writes.',
        'max_abs_differences':maxima,'recomputed':summaries,'verified_images':len(bindings['images']),
        'verified_prediction_files':len(bindings['new_predictions']),'verified_labels':len(bindings['labels']),
        'resources_recomputed':{'downloaded_bytes':received,'new_prediction_bytes':prediction_sizes},
        'mtime_order':{'all_first_before_decisions':max(times['1701'])<=dt,'all_second_after_decisions':min(times['1702'])>=dt,
                      'all_labels_after_second':min(_local(dataset,labels[t]['key']).stat().st_mtime for t in m['held_tiles'])>=max(times['1702'])},
        'selected_baseline':cal['selected_baseline'],'transport_action_counts_by_anchor':action_count.tolist(),
        'descriptive_anchor_results':[{ 'anchor':i, 'view':m['held_views'][i],
            **{k:float(np.mean([r[k] for r in rows['actual_labels'] if r['anchor']==i])) for k in ('policy_gain','mae_gain','transport','max_separation')},
            'selected_predicted_gain':float(np.mean([r['predicted'] for r in selected_gain if r['anchor']==i])),
            'selected_actual_gain':float(np.mean([r['actual'] for r in selected_gain if r['anchor']==i]))} for i in range(4)],
        'source_hashes':{p.name:digest(p) for p in out.iterdir() if p.is_file()}}


if __name__=='__main__':
    print(json.dumps(review(Path('/home/rspip/cqc/study/orientbench'),Path('/home/rspip/cqc/data/dataset')),indent=2))
