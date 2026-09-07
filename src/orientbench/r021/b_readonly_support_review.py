"""B review of saved development artifacts and native held support; no held outcomes."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import numpy as np


def review(root, dataset):
    sys.path.insert(0, str(root/'src'))
    from orientbench.r018.evaluate import read, digest
    from orientbench.r017.run_pilot import _local
    from orientbench.r021.data import Assets
    from orientbench.r021.forecast import Transport, evaluate_policies, block_summary
    from orientbench.r021.run import align, BASELINES
    import rasterio
    started = datetime.now(timezone.utc).isoformat()
    out = root/'runs/r021/artifacts/retry'
    m = read(root/'configs/r021/data_manifest.json')
    binding = read(out/'input_bindings.json')
    files = {p.name: {'bytes':p.stat().st_size, 'sha256':digest(p)} for p in out.iterdir() if p.is_file()}
    counts = {}
    for name in ('existing','new_predictions','images'):
        for key, expected in binding[name].items():
            path = root/key if name=='existing' else out/key if name=='new_predictions' else _local(dataset,key)
            if digest(path)!=expected:
                raise ValueError('saved source hash mismatch: '+key)
        counts[name] = len(binding[name])
    shifts = read(out/'frozen_shifts.json')
    bad = []
    for item in m['images_to_materialize']:
        if item['split']!='held':
            continue
        with rasterio.open(_local(dataset,item['key'])) as ds:
            raw=ds.read((1,2,3))
            valid=np.all(np.isfinite(raw),0)&np.all(ds.read_masks((1,2,3))>0,0)
            if ds.nodata is not None:
                valid &= ~np.any(raw==ds.nodata,0)
        if valid.all():
            continue
        y,x=np.where(~valid)
        v=m['held_views'].index(item['view'])
        source=(np.arange(448)+.5)*900/448-.5
        lo=np.floor(source).astype(int);hi=lo+1
        supported=valid[np.ix_(lo,lo)]&valid[np.ix_(lo,hi)]&valid[np.ix_(hi,lo)]&valid[np.ix_(hi,hi)]
        record={'tile':item['tile'],'view':item['view'],'native_invalid':int((~valid).sum()),
                'native_bbox_yx':[int(y.min()),int(x.min()),int(y.max()),int(x.max())],
                'invalid_nonzero_rgb_values':int(np.count_nonzero(raw[:,~valid])),
                'invalid_core':int((~supported[32:416,32:416]).sum()),'invalid_shifted_cores':[]}
        for model in shifts['held']:
            dy,dx=model[v]['dy'],model[v]['dx']
            record['invalid_shifted_cores'].append(int((~supported[32+dy:416+dy,32+dx:416+dx]).sum()))
        bad.append(record)
    with np.load(out/'forecaster.npz') as z:
        model=Transport(z['geometry'],z['counts'],z['pair_risk'],float(z['pi']))
        for name in ('xmean','xscale','coef','ymean'):
            setattr(model,name,z[name])
        model.bias=dict(zip(z['bias_names'].tolist(),z['bias_values'].tolist()))
    cal=read(out/'calibration.json')
    if model.bias!=cal['bias'] or digest(out/'forecaster.npz')!=cal['forecaster_sha256']:
        raise ValueError('calibration/model mismatch')
    records=read(out/'development_calibration_raw.json')
    if len(records)!=512 or len({(r['tile'],r['anchor']) for r in records})!=512:
        raise ValueError('incomplete calibration records')
    # Reopen accepted calibration maps and targets, independently compute loss;
    # construct an Assets reader without invoking its writing initializer.
    assets=Assets.__new__(Assets)
    assets.root,assets.out=root,out
    assets.old={t:read(root/f'runs/{t}/artifacts/input_bindings.json') for t in ('r018','r019','r020')}
    assets.old_cal_hashes={r['file']:r['sha256'] for r in read(root/'doc/R018_B_REVIEW_20260907.json')['prediction_files']}
    assets.evidence={'existing':{}}
    rows=[];error_loss=0.;error_forecast=0.
    lookup={(r['tile'],r['anchor']):r for r in records}
    for tile in m['calibration_tiles']:
        p=assets.probabilities('calibration',tile)
        first,second=[align(p[s],shifts['development'][s]) for s in range(2)]
        y=assets.development_label('calibration',tile)[32:416,32:416].astype(float)
        for i in range(8):
            saved=lookup[tile,i];costs={};scores={}
            for j in range(8):
                q=np.clip((first[i].astype(float)+second[j].astype(float))/2,1e-6,1-1e-6)
                costs[j]=float(np.mean(-y*np.log(q)/(2*model.pi)-(1-y)*np.log1p(-q)/(2*(1-model.pi))))
                error_loss=max(error_loss,abs(costs[j]-saved['costs'][str(j)]))
                if i!=j:
                    scores[j]=model.predict(first[i],model.geometry[i],model.geometry[j])
                    error_forecast=max(error_forecast,max(abs(scores[j][n]-model.bias[n]-saved['scores'][str(j)][n]) for n in model.bias))
            rows.append({'tile':tile,'anchor':i,**evaluate_policies(costs,scores,i,model.geometry)})
    summary=block_summary(rows,m['calibration_tiles'],anchors=range(8))
    error_summary=max(abs(summary['means'][k]-cal['summary']['means'][k]) for k in summary['means'])
    baseline=min(BASELINES,key=lambda n:summary['means'][n])
    if max(error_loss,error_forecast,error_summary)>1e-10 or baseline!=cal['selected_baseline']:
        raise ValueError('development replay differs')
    labels={r['tile']:r for r in m['labels']}
    return {'observed_start_utc':started,'observed_end_utc':datetime.now(timezone.utc).isoformat(),
        'scope':'Read-only hash verification, all 256 held native support checks, full 64-region development probability/forecast replay. No network forward or held labels/outcomes.',
        'source_files':files,'verified_binding_counts':counts,'incomplete_native_support':bad,
        'development_loss_max_abs_difference':error_loss,'development_forecast_max_abs_difference':error_forecast,
        'development_summary_max_abs_difference':error_summary,'selected_baseline':baseline,
        'held_prediction_files':len(list((out/'predictions/held').rglob('*.npz'))),
        'held_outcome_files_present':[f for f in ('decisions.json','summary.json','held_action_outcomes.json') if (out/f).exists()],
        'held_label_files_existing':sum(_local(dataset,labels[t]['key']).exists() for t in m['held_tiles']),
        'download_accounting':'Retained recursive retry ledgers do not establish total traffic or non-exceedance. Image content hashes establish identity, not historical download bytes.'}


if __name__=='__main__':
    print(json.dumps(review(Path('/home/rspip/cqc/study/orientbench'),Path('/home/rspip/cqc/data/dataset')),indent=2))
