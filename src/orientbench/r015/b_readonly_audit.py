"""Read-only B audit of r015 existing probabilities; no model inference or artifact writes."""
import argparse, csv, hashlib, json, math
from pathlib import Path
import numpy as np

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def main(root, dataset):
    base=root/'runs/r015/artifacts'
    pre=json.loads((base/'preflight.json').read_text())
    g0=json.loads((root/'runs/r012/final_repair_artifacts/primary.json').read_text())
    eligible={x['object_id']:x for x in json.loads((root/'runs/r012/final_repair_artifacts/eligible_manifest.json').read_text())}
    official=json.loads((dataset/'real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson').read_text())['features']
    meta=list(csv.DictReader((dataset/'real/metadata_annotations/RarePlanes_Public_Metadata.csv').open()))
    sources={(int(x['loc_id']),x['image_id'].split('_',1)[1]):x['image_id'] for x in meta}
    groups=g0['split']['calibration']; canonical=sorted(groups)
    true_comp={int(loc):i for i,key in enumerate(canonical) for loc in key.split(':',1)[1].split(',')}
    producer_comp={int(loc):i for i,key in enumerate(groups) for loc in key.split(':',1)[1].split(',')}
    cal=pre['records']['calibration']; oid=np.array([r['object_id'] for r in cal])
    assert len(oid)==7416 and len(set(oid))==7416
    labels=np.array([[int(official[i]['properties']['wing_type']=='straight'),
                      int(official[i]['properties']['num_engines']==2),
                      int(official[i]['properties']['propulsion']=='jet')] for i in oid])
    comp=np.array([true_comp[int(official[i]['properties']['loc_id'])] for i in oid])
    expected_producer=np.array([producer_comp[int(official[i]['properties']['loc_id'])] for i in oid])
    for part in ('train','calibration'):
        previous=root/('runs/r012/h1a/canvases/train/manifest.json' if part=='train' else 'runs/r013/calibration/canvases/manifest.json')
        expected={r['object_id'] for r in json.loads(previous.read_text())['records']}
        assert {r['object_id'] for r in pre['records'][part]}==expected
        for r in pre['records'][part]:
            q=official[r['object_id']]['properties']; e=eligible[r['object_id']]
            assert sources[(int(q['loc_id']),q['cat_id'])]==r['image_id']==e['source_cog']
            assert r['labels']==[int(q['wing_type']=='straight'),int(q['num_engines']==2),int(q['propulsion']=='jet')]
            assert all(r[k]==e[k] for k in ('center','L','S','theta'))
    K=('resnet50','vit_b16'); N=(96,224); S=(1501,1502,1503)
    Q=('I2','I8','O0','O5','O10','O20','T0')
    correct=np.zeros((2,2,3,7,7416,3),np.float64); wrong=np.zeros_like(correct)
    probability_records=[]; heads=[]; discord=[]; hard_rule_diffs=0; max_sum=0.
    for mi,k in enumerate(K):
      for ni,n in enumerate(N):
       for si,s in enumerate(S):
        raw={}
        for strategy in ('I','O','T'):
            p=base/'evaluation'/f'{strategy}_{k}_{n}_{s}'/'probabilities.npz'
            z=np.load(p,allow_pickle=False)
            assert np.array_equal(z['object_id'],oid) and np.array_equal(z['labels'],labels)
            assert np.array_equal(z['component'],expected_producer)
            probability_records.append({'tag':f'{strategy}_{k}_{n}_{s}','sha256':digest(p)})
            raw[strategy]={v:z[v] for v in z.files if v not in ('object_id','component','labels')}
        for qi,q in enumerate(Q):
            strategy=q[0]
            conditions=[q] if q in ('I2','I8','O0','T0') else ['O-'+q[1:],q]
            decisions=[]; legacy=[]
            for name in conditions:
                p=raw[strategy][name]
                assert p.shape==(7416,8 if name=='I8' else 2,3,2)
                assert np.isfinite(p).all() and np.min(p)>=0 and np.max(p)<=1
                max_sum=max(max_sum,float(np.max(np.abs(p.astype(np.float64).sum(-1)-1))))
                assert max_sum<1e-6
                avg=p.astype(np.float64).mean(1)
                h=avg.argmax(-1)
                old=p.mean(1)[...,1]>.5
                hard_rule_diffs+=int(np.sum(h!=old))
                decisions.append(h);legacy.append(old)
            correct[mi,ni,si,qi]=np.mean([h!=labels for h in decisions],axis=0)
            wrong[mi,ni,si,qi]=(np.stack(legacy).mean(0)>.5)!=labels
            if len(decisions)==2:
                discord.append({'model':k,'size':n,'seed':s,'dose':q,'disagree_attribute_decisions':int(np.sum(decisions[0]!=decisions[1]))})
            else:
                heads.append({'model':k,'size':n,'seed':s,'condition':q,'constant':[(len(np.unique(decisions[0][:,a]))==1) for a in range(3)]})
    def cells(errors,codes,keys):
        out=np.zeros((2,2,3,7,3,25,2));present=np.zeros((3,25,2))
        for a in range(3):
          for ci,key in enumerate(keys):
           for klass in (0,1):
            ix=(codes==key)&(labels[:,a]==klass);present[a,ci,klass]=ix.any()
            if ix.any():out[...,a,ci,klass]=errors[...,ix,a].mean(-1)
        return out,present
    def risks(weights,table,present):
        # All fits remain separate until component/class risk is computed.
        result=np.zeros((len(weights),2,2,3,7,3))
        for a in range(3):
          for klass in (0,1):
            den=weights@present[a,:,klass]
            assert np.all(den>0),('zero denominator',a,klass)
            flat=table[...,a,:,klass].reshape(84,25)
            value=(weights@flat.T).reshape(len(weights),2,2,3,7)
            result[...,a]+=.5*value/den[:,None,None,None,None]
        return result
    def family(r):
        m=r.mean(-1).mean(3);v=[];names=[]
        for mi,k in enumerate(K):
          for ni,n in enumerate(N):
            for which,idx in (('G2',0),('G8',1)):
              for d,j in ((0,2),(5,3),(10,4),(20,5)):
                v.append(m[:,mi,ni,idx]-m[:,mi,ni,j]);names.append(f'{which}_{k}_{n}_d{d}')
            v.extend([m[:,mi,ni,2]-m[:,mi,ni,6],m[:,mi,ni,0],m[:,mi,ni,2]])
            names.extend([f'A_{k}_{n}',f'R_I2_{k}_{n}',f'R_O0_{k}_{n}'])
        for mi,k in enumerate(K):
            v.append(m[:,mi,0,0]-m[:,mi,0,2]-m[:,mi,1,0]+m[:,mi,1,2]);names.append(f'J_{k}')
        return np.stack(v,-1),names
    saved_draws=np.load(base/'statistics/bootstrap_draws.npy')
    draws=np.random.Generator(np.random.PCG64(15015)).integers(0,25,(50000,25))
    assert np.array_equal(draws,saved_draws)
    weights=np.zeros((50000,25))
    np.add.at(weights,(np.arange(50000)[:,None],draws),1)
    oldkeys=sorted(np.unique(expected_producer),key=lambda x:str(x))
    oldtable,oldpres=cells(wrong,expected_producer,oldkeys)
    oldpoint,names=family(risks(np.ones((1,25)),oldtable,oldpres))
    oldboot,_=family(risks(weights,oldtable,oldpres))
    summary=json.loads((base/'statistics/summary.json').read_text())
    assert names==summary['dimensions']
    olddiff=float(np.max(np.abs(oldpoint[0]-summary['point'])))
    saved=np.load(base/'statistics/bootstrap_replicates.npy')
    saved_diff=float(np.max(np.abs(oldboot-saved)))
    table,present=cells(correct,comp,np.arange(25))
    riskpoint=risks(np.ones((1,25)),table,present)
    point,names=family(riskpoint);point=point[0]
    boot,_=family(risks(weights,table,present))
    sd=boot.std(0,ddof=1);active=sd>0
    assert not np.any((~active)&np.any(np.abs(boot-point)>1e-12,axis=0))
    q=float(np.quantile(np.max(np.abs((boot[:,active]-point[active])/sd[active]),axis=1),.95,method='linear'))
    lo=point-q*sd;hi=point+q*sd
    leave_weights=np.ones((25,25))-np.eye(25)
    loo,_=family(risks(leave_weights,table,present))
    records=[{'name':name,'point':float(point[j]),'lower':float(lo[j]),'upper':float(hi[j]),
              'loo_min':float(loo[:,j].min()),'loo_max':float(loo[:,j].max())} for j,name in enumerate(names)]
    risks_by_cell=[]
    for mi,k in enumerate(K):
      for ni,n in enumerate(N):
       m=riskpoint[0,mi,ni].mean(0).mean(-1)
       risks_by_cell.append({'architecture':k,'size':n,'macro_risks':dict(zip(Q,m.tolist())),
                            'attribute_risks':riskpoint[0,mi,ni].mean(0).tolist(),
                            'seed_risks':riskpoint[0,mi,ni].mean(-1).tolist()})
    canonical_old_order=[groups[int(i)] for i in oldkeys]
    result={'objects':7416,'components':25,'full_input_identity':True,'probability_files':36,
            'max_probability_sum_error':max_sum,'hard_rule_difference_count':hard_rule_diffs,
            'old_point_max_abs_difference':olddiff,'old_float32_bootstrap_max_abs_difference':saved_diff,
            'draws_exact':True,'old_component_order':canonical_old_order,'correct_component_order':canonical,
            'source_order_positions_different':sum(a!=b for a,b in zip(canonical_old_order,canonical)),
            'correct_q95':q,'old_q95':summary['simultaneous_q95'],
            'dose_point_max_abs_correction':float(np.max(np.abs(point-np.array(summary['point'])))),
            'records':records,'risks':risks_by_cell,'head_constants':heads,'dose_disagreements':discord,
            'probability_bindings':probability_records,
            'scope':'Existing model outputs only; corrected error aggregation and component ordering; training recipe is not repaired.'}
    print(json.dumps(result,sort_keys=True,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--dataset',type=Path,required=True)
    a=p.parse_args();main(a.root,a.dataset)
