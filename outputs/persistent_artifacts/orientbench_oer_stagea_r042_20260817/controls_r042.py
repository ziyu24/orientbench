#!/usr/bin/env python3
from pathlib import Path
import numpy as np,pandas as pd
R=Path('outputs/persistent_artifacts/orientbench_oer_stagea_r042_20260817')
def a(y,r):
 o=np.argsort(r,kind='mergesort');y=y[o];r=r[o];i=0;l=z=0.;n=len(y)
 while i<n:
  j=i+1
  while j<n and r[j]==r[i]:j+=1
  q=l;l+=y[i:j].sum()/n;z+=.5*(q+l)*(j-i)/n;i=j
 return z
d=pd.read_parquet(R/'heldout_predictions.parquet');out=[]
for u,x in d.groupby('unit'):
 es=[]
 for _,g in x.groupby('class_name'):
  if len(g)>=100:es.append(a(g.Y.to_numpy(),g.risk_baseline.to_numpy())-a(g.Y.to_numpy(),g.risk_oer.to_numpy()))
 rng=np.random.default_rng(20260817+ord(u));p=[]
 for _ in range(100):
  q=x.copy();q['r']=q.m_y_z+q.groupby('class_name').ridge_adjustment.transform(lambda v:rng.permutation(v.to_numpy()))
  p.append(a(q.Y.to_numpy(),q.risk_baseline.to_numpy())-a(q.Y.to_numpy(),q.r.to_numpy()))
 delta=a(x.Y.to_numpy(),x.risk_baseline.to_numpy())-a(x.Y.to_numpy(),x.risk_oer.to_numpy())
 out.append({'unit':u,'equal_class_delta':float(np.mean(es)),'common_support_delta':delta,'permutation_median_delta':float(np.median(p)),'permutation_residual_ratio':None if delta<=0 else float(np.median(np.maximum(p,0))/delta)})
pd.DataFrame(out).to_csv(R/'controls_r042.csv',index=False)
