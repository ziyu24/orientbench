"""Independent r014 statistic/input verifier; no import from producer or stats modules."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw',type=Path,required=True);p.add_argument('--audit',type=Path,required=True);p.add_argument('--summary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();names=[f'{k}_{s}' for k in ('resnet50','vit_b16') for s in (1201,1202,1203)];z=[np.load(a.raw/f'raw_{n}.npz') for n in names];ids=z[0]['object_id'];co=z[0]['component'];y=z[0]['labels'];audit={x['object_id']:x for x in map(json.loads,open(a.audit/'source_records.jsonl')) if x['partition']=='calibration'}
 if len(ids)!=7416 or set(ids)!=set(audit) or any(not(np.array_equal(ids,x['object_id']) and np.array_equal(co,x['component']) and np.array_equal(y,x['labels']) and np.allclose(x['p_avg'],x['p_view'].mean(1),atol=0,rtol=0)) for x in z):raise RuntimeError('raw/source identity')
 pr=np.array([x['p_avg'][...,1] for x in z]).reshape(2,3,3,len(ids),3);h=pr>.5;v=np.zeros((2,3,3,3,25,2));have=np.zeros((3,25,2),bool)
 for m in range(2):
  for s in range(3):
   for arm in range(3):
    for k in range(3):
     for j in range(25):
      for c in range(2):
       ix=np.flatnonzero((co==j)&(y[:,k]==c));have[k,j,c]=len(ix)>0
       if len(ix):v[m,s,arm,k,j,c]=np.mean(h[m,s,arm,ix,k]!=c)
 rng=np.random.Generator(np.random.PCG64(12012));idsdraw=rng.integers(0,25,(50000,25));w=np.zeros((50000,25));np.add.at(w,(np.arange(50000)[:,None],idsdraw),1);rr=np.zeros((50000,2,3,3,3));rp=np.zeros((2,3,3,3))
 for m in range(2):
  for s in range(3):
   for arm in range(3):
    for k in range(3):
     rr[:,m,s,k,arm]=.5*((w@v[m,s,arm,k,:,0])/(w@have[k,:,0])+(w@v[m,s,arm,k,:,1])/(w@have[k,:,1]));rp[m,s,k,arm]=.5*(v[m,s,arm,k,:,0][have[k,:,0]].mean()+v[m,s,arm,k,:,1][have[k,:,1]].mean())
 d=(((rr[...,1]+rr[...,2])/2-rr[...,0]).mean(2)).reshape(50000,6);pt=(((rp[...,1]+rp[...,2])/2-rp[...,0]).mean(1)).reshape(6);sd=d.std(0,ddof=1);q=float(np.quantile(np.max(np.abs((d-pt)/sd),1),.95,method='linear'));s0=json.load(open(a.summary));match=np.allclose(pt,np.asarray(s0['delta']).reshape(6),atol=1e-10,rtol=0) and np.allclose(sd,s0['sd'],atol=1e-10,rtol=0) and abs(q-s0['q'])<=1e-10
 a.out.write_text(json.dumps({'independent':True,'objects':len(ids),'components':len(np.unique(co)),'affected':int(sum(x['affected'] for x in audit.values())),'delta':pt.tolist(),'sd':sd.tolist(),'q':q,'matches_primary':bool(match),'max_abs_delta_difference':float(np.max(np.abs(pt-np.asarray(s0['delta']).reshape(6)))),'probabilities_valid':bool(all(np.isfinite(x['p_view']).all() and np.allclose(x['p_view'].sum(-1),1,atol=1e-6) for x in z))},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
