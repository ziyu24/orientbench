"""Generate r013 component-equal risks and frozen synchronous bootstrap evidence."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import numpy as np
KINDS=('resnet50','vit_b16');SEEDS=(1201,1202,1203);ARMS=('clean','minus10','plus10')
def component_values(prob,labels,component):
 out=np.zeros((2,3,3,3,25,2),float); has=np.zeros((3,25,2),bool); hard=prob>.5
 for ai in range(2):
  for si in range(3):
   for k in range(3):
    for c in range(2):
     for j in range(25):
      m=(component==j)&(labels[:,k]==c);has[k,j,c]=m.any()
      if m.any():out[ai,si,:,k,j,c]=np.mean(hard[ai,si][:,m,k] != c,axis=1)
 return out,has,hard
def risks(counts,values,has):
 b=len(counts)
 # Explicit arm dimension avoids a hidden broadcast in the component calculation.
 r=np.empty((b,2,3,3,3))
 for ai in range(2):
  for si in range(3):
   for k in range(3):
    for arm in range(3):
     v0=values[ai,si,arm,k,:,0];v1=values[ai,si,arm,k,:,1]
     r[:,ai,si,k,arm]=.5*((counts@v0)/(counts@has[k,:,0])+(counts@v1)/(counts@has[k,:,1]))
 return r
def main():
 p=argparse.ArgumentParser();p.add_argument('--raw-dir',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 xs=[];meta=None
 for kind in KINDS:
  q=[]
  for seed in SEEDS:
   z=np.load(a.raw_dir/f'raw_{kind}_{seed}.npz');q.append(z['prob'])
   here=(z['object_id'],z['component'],z['labels'])
   if meta is None:meta=here
   elif any(not np.array_equal(x,y) for x,y in zip(meta,here)):raise RuntimeError('raw row identity mismatch')
  xs.append(q)
 prob=np.array(xs);oid,comp,labels=meta
 values,has,hard=component_values(prob,labels,comp)
 if not has.any(2).all():raise RuntimeError('component support failure')
 point=risks(np.ones((1,25)),values,has)[0];rng=np.random.Generator(np.random.PCG64(12012));draws=[];rep=[];zero=0
 while sum(len(x) for x in draws)<50000:
  n=min(1000,50000-sum(len(x) for x in draws));d=rng.integers(0,25,(n,25));cnt=np.zeros((n,25),int);np.add.at(cnt,(np.arange(n)[:,None],d),1)
  valid=np.ones(n,bool)
  for k in range(3):
   for c in range(2):valid&=(cnt@has[k,:,c])>0
  zero+=int((~valid).sum());draws.append(d[valid]);rep.append(risks(cnt[valid],values,has))
 draw=np.concatenate(draws)[:50000];R=np.concatenate(rep)[:50000];delta=(((R[...,1]+R[...,2])/2)-R[...,0]).mean(2);dpoint=(((point[...,1]+point[...,2])/2)-point[...,0]).mean(1)
 flat=delta.reshape(50000,6);dp=dpoint.reshape(6);sd=flat.std(0,ddof=1);M=np.max(np.abs((flat-dp)/sd),1);q=float(np.quantile(M,.95,method='linear'));lo=dp-q*sd;hi=dp+q*sd;power=np.mean(.020+flat-dp-q*sd>0,0)
 clean=R[...,0].mean(2).reshape(50000,6);cp=point[...,0].mean(1).reshape(6);cs=clean.std(0,ddof=1);cq=float(np.quantile(np.max(np.abs((clean-cp)/cs),1),.95,method='linear'));clo=cp-cq*cs;chi=cp+cq*cs
 utility=np.array([[not np.all(hard[ai,si,0,:,k]==hard[ai,si,0,0,k]) for k in range(3)] for ai in range(2) for si in range(3)]).reshape(2,3,3)
 np.save(a.out/'bootstrap_draws.npy',draw);np.savez_compressed(a.out/'bootstrap_replicates.npz',risk=R,delta=delta,clean=clean)
 payload={'protocol':'r013-h1a-v1','zero_denominator_draws':zero,'point_risk':point.tolist(),'delta':dpoint.tolist(),'sd':sd.tolist(),'q':q,'simultaneous_lower':lo.tolist(),'simultaneous_upper':hi.tolist(),'power':power.tolist(),'clean_risk':cp.tolist(),'clean_q':cq,'clean_simultaneous_lower':clo.tolist(),'clean_simultaneous_upper':chi.tolist(),'all_heads_nonconstant':bool(utility.all()),'head_nonconstant':utility.tolist(),'raw_shape':list(prob.shape)}
 (a.out/'summary.json').write_text(json.dumps(payload,sort_keys=True,indent=2)+'\n')
if __name__=='__main__':main()
