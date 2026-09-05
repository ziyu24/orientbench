"""r014 corrected component-equal H1a statistics from complete two-view probabilities."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
K=('resnet50','vit_b16');S=(1201,1202,1203)
def load(raw):
 z=[];meta=None
 for k in K:
  row=[]
  for s in S:
   x=np.load(raw/f'raw_{k}_{s}.npz');row.append(x['p_avg'][...,1]);m=(x['object_id'],x['component'],x['labels'])
   if meta is None:meta=m
   elif any(not np.array_equal(a,b) for a,b in zip(meta,m)):raise RuntimeError('raw identity')
  z.append(row)
 return np.array(z),meta
def table(p,y,c):
 h=p>.5;v=np.zeros((2,3,3,3,25,2));present=np.zeros((3,25,2),bool)
 for mi in range(2):
  for si in range(3):
   for arm in range(3):
    for a in range(3):
     for j in range(25):
      for klass in range(2):
       ix=(c==j)&(y[:,a]==klass);present[a,j,klass]=ix.any()
       if ix.any():v[mi,si,arm,a,j,klass]=np.mean(h[mi,si,arm,ix,a]!=klass)
 return v,present,h
def risks(w,v,p):
 n=len(w);r=np.empty((n,2,3,3,3))
 for mi in range(2):
  for si in range(3):
   for arm in range(3):
    for a in range(3):r[:,mi,si,a,arm]=.5*((w@v[mi,si,arm,a,:,0])/(w@p[a,:,0])+(w@v[mi,si,arm,a,:,1])/(w@p[a,:,1]))
 return r
def main():
 q=argparse.ArgumentParser();q.add_argument('--raw',type=Path,required=True);q.add_argument('--out',type=Path,required=True);a=q.parse_args();a.out.mkdir(parents=True,exist_ok=True);prob,(oid,comp,y)=load(a.raw);v,p,h=table(prob,y,comp)
 if not p.any(2).all():raise RuntimeError('support')
 point=risks(np.ones((1,25)),v,p)[0];rng=np.random.Generator(np.random.PCG64(12012));ids=rng.integers(0,25,(50000,25));w=np.zeros((50000,25));np.add.at(w,(np.arange(50000)[:,None],ids),1);R=risks(w,v,p);delta=(((R[...,1]+R[...,2])/2-R[...,0]).mean(2));dp=(((point[...,1]+point[...,2])/2-point[...,0]).mean(1));flat=delta.reshape(50000,6);dpf=dp.reshape(6);sd=flat.std(0,ddof=1);q95=float(np.quantile(np.max(np.abs((flat-dpf)/sd),1),.95,method='linear'));lo=dpf-q95*sd;hi=dpf+q95*sd;power=np.mean(.020+flat-dpf-q95*sd>0,0);clean=R[...,0].mean(2).reshape(50000,6);cp=point[...,0].mean(1).reshape(6);cs=clean.std(0,ddof=1);cq=float(np.quantile(np.max(np.abs((clean-cp)/cs),1),.95,method='linear'));single=np.array([[[np.all(h[mi,si,0,:,aa]==h[mi,si,0,0,aa]) for aa in range(3)]for si in range(3)]for mi in range(2)])
 np.save(a.out/'bootstrap_draws.npy',ids);np.savez_compressed(a.out/'bootstrap_replicates.npz',risk=R,delta=delta,clean=clean)
 out={'delta':dp.tolist(),'sd':sd.tolist(),'q':q95,'simultaneous_lower':lo.tolist(),'simultaneous_upper':hi.tolist(),'power':power.tolist(),'clean_risk':cp.tolist(),'clean_sd':cs.tolist(),'clean_q':cq,'clean_simultaneous_upper':(cp+cq*cs).tolist(),'all_heads_nonconstant':bool((~single).all()),'head_nonconstant':(~single).tolist(),'zero_denominator_draws':0,'objects':len(oid),'components':len(np.unique(comp))};(a.out/'summary.json').write_text(json.dumps(out,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
