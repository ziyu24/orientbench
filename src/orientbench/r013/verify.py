"""Independent r013 raw-prediction verifier; it imports no producer/statistics code."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw-dir',type=Path,required=True);p.add_argument('--summary',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();names=[f'{k}_{s}' for k in ('resnet50','vit_b16') for s in (1201,1202,1203)];z=[np.load(a.raw_dir/f'raw_{n}.npz') for n in names];oid=z[0]['object_id'];comp=z[0]['component'];y=z[0]['labels']
 if any(not(np.array_equal(oid,x['object_id']) and np.array_equal(comp,x['component']) and np.array_equal(y,x['labels'])) for x in z[1:]):raise RuntimeError('row identity')
 pr=np.array([x['prob'] for x in z]).reshape(2,3,3,len(oid),3);hard=pr>.5;single=np.empty((2,3,3),bool)
 cm=np.zeros((2,3,3,3,25,2));ok=np.zeros((3,25,2),bool)
 for m in range(2):
  for s in range(3):
   for arm in range(3):
    for k in range(3):
     single[m,s,k]=np.all(hard[m,s,arm,:,k]==hard[m,s,arm,0,k])
     for j in range(25):
      for c in range(2):
       ix=np.flatnonzero((comp==j)&(y[:,k]==c));ok[k,j,c]=len(ix)>0
       if len(ix):cm[m,s,arm,k,j,c]=np.mean(hard[m,s,arm,ix,k]!=c)
 rng=np.random.Generator(np.random.PCG64(12012));D=[];C=[];draw=[]
 for _ in range(50):
  ids=rng.integers(0,25,(1000,25));w=np.zeros((1000,25));np.add.at(w,(np.arange(1000)[:,None],ids),1);rr=np.zeros((1000,2,3,3,3))
  for m in range(2):
   for s in range(3):
    for arm in range(3):
     for k in range(3):
      rr[:,m,s,k,arm]=.5*((w@cm[m,s,arm,k,:,0])/(w@ok[k,:,0])+(w@cm[m,s,arm,k,:,1])/(w@ok[k,:,1]))
  D.append(((rr[...,1]+rr[...,2])/2-rr[...,0]).mean(2));C.append(rr[...,0].mean(2));draw.append(ids)
 d=np.concatenate(D);c=np.concatenate(C);rp=np.zeros((2,3,3,3))
 for m in range(2):
  for s in range(3):
   for arm in range(3):
    for k in range(3):rp[m,s,k,arm]=.5*(cm[m,s,arm,k,:,0][ok[k,:,0]].mean()+cm[m,s,arm,k,:,1][ok[k,:,1]].mean())
 pt=(((rp[...,1]+rp[...,2])/2-rp[...,0]).mean(1)).reshape(6);sd=d.reshape(50000,6).std(0,ddof=1);q=float(np.quantile(np.max(np.abs((d.reshape(50000,6)-pt)/sd),1),.95,method='linear'));summary=json.load(open(a.summary));valid=bool(np.allclose(pt,summary['delta'],atol=1e-12) and np.allclose(sd,summary['sd'],atol=1e-12) and abs(q-summary['q'])<1e-12)
 a.out.write_text(json.dumps({'independent':True,'raw_rows':int(len(oid)),'components':int(len(np.unique(comp))),'all_heads_nonconstant':bool((~single).all()),'head_nonconstant':(~single).tolist(),'delta':pt.tolist(),'sd':sd.tolist(),'q':q,'matches_summary':valid,'mutation_all_pass':all(all(json.loads(str(x['mutation'])).values()) for x in z)},sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
