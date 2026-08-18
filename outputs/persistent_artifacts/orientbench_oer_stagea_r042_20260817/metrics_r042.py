#!/usr/bin/env python3
"""Frozen r042 AUGRC and parallel cluster bootstrap."""
from pathlib import Path
import numpy as np, pandas as pd
from numba import njit, prange
ROOT=Path('outputs/persistent_artifacts/orientbench_oer_stagea_r042_20260817')
def aug(y,r):
 o=np.argsort(r,kind='mergesort');y=y[o];r=r[o];n=len(y);i=0;l=a=0.
 while i<n:
  j=i+1
  while j<n and r[j]==r[i]:j+=1
  old=l;l+=y[i:j].sum()/n;a+=.5*(old+l)*(j-i)/n;i=j
 return a
@njit
def augw(y,r,cid,m):
 W=0.
 for i in range(len(y)): W+=m[cid[i]]
 l=a=0.;i=0
 while i<len(y):
  j=i+1
  while j<len(y) and r[j]==r[i]:j+=1
  old=l;wg=0.
  for k in range(i,j):
   w=m[cid[k]];l+=w*y[k]/W;wg+=w/W
  a+=.5*(old+l)*wg;i=j
 return a
@njit
def one(yb,rb,cidb,yo,ro,cido,nc,seed):
 np.random.seed(seed);m=np.zeros(nc,np.int64)
 for _ in range(nc):m[np.random.randint(nc)]+=1
 return augw(yb,rb,cidb,m)-augw(yo,ro,cido,m)
@njit(parallel=True)
def boot(yb,rb,cidb,yo,ro,cido,nc):
 z=np.empty(10000)
 for b in prange(10000):z[b]=one(yb,rb,cidb,yo,ro,cido,nc,20260817+b)
 return z
def main():
 d=pd.read_parquet(ROOT/'heldout_predictions.parquet');out=[]
 for u,x in d.groupby('unit',sort=True):
  base=aug(x.Y.to_numpy(),x.risk_baseline.to_numpy());oer=aug(x.Y.to_numpy(),x.risk_oer.to_numpy());cs=x.cluster.unique();ci=pd.Categorical(x.cluster,categories=cs).codes;ob=np.argsort(x.risk_baseline.to_numpy(),kind='mergesort');oo=np.argsort(x.risk_oer.to_numpy(),kind='mergesort')
  z=boot(x.Y.to_numpy()[ob],x.risk_baseline.to_numpy()[ob],ci[ob],x.Y.to_numpy()[oo],x.risk_oer.to_numpy()[oo],ci[oo],len(cs));delta=base-oer
  out.append(dict(unit=u,dataset=x.dataset.iloc[0],detector=x.detector.iloc[0],augrc_baseline=base,augrc_oer=oer,delta=delta,ci_low=np.quantile(z,.025),ci_high=np.quantile(z,.975),p_raw=(1+(z-delta>=delta).sum())/10001,strongest=x.strongest_baseline.iloc[0]))
 pd.DataFrame(out).to_csv(ROOT/'unit_metrics.csv',index=False)
if __name__=='__main__':main()
