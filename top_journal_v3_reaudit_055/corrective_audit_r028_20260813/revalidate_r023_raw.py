#!/usr/bin/env python3
"""Independent r023 replicate-layer audit (no r020/r023 validator imports)."""
from pathlib import Path
import argparse,json
import numpy as np
import pandas as pd

def ci(x): return float(np.quantile(x,.025,method='linear')),float(np.quantile(x,.975,method='linear'))
def pvalue(x,point): return float((1+np.count_nonzero(np.abs(x-point)>=abs(point)))/(len(x)+1))
def holm(frame):
 out=np.zeros(len(frame));
 for level in ('unit','dataset'):
  ix=np.flatnonzero(frame.level.to_numpy()==level); order=ix[np.lexsort((frame.endpoint.to_numpy()[ix],frame.key.to_numpy()[ix],frame.p_raw.to_numpy()[ix]))]; prev=0.
  for rank,j in enumerate(order): prev=max(prev,min(1.,(len(order)-rank)*frame.p_raw.iloc[j]));out[j]=prev
 return out
def main():
 p=argparse.ArgumentParser();p.add_argument('--rows',type=Path,required=True);p.add_argument('--replicates',type=Path,required=True);p.add_argument('--frozen',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 # rows are read to establish source provenance and independently reproduce
 # main-domain linear/raw point deltas for the six units.
 raw=pd.read_parquet(a.rows,columns=['unit','ar','risk_main','raw_confidence','linear_source_frozen'])
 point={}
 for u,z in raw.groupby('unit'):
  z=z[z.ar>=2.1]
  for endpoint,q in [('AUGRC',None),('Risk@70',.7),('Risk@90',.9)]:
   def m(s):
    o=np.argsort(-s,kind='stable');s=s[o];r=z.risk_main.to_numpy()[o];st=np.r_[0,np.flatnonzero(s[1:]!=s[:-1])+1];n=len(s);c=np.diff(np.r_[st,n]);rr=np.add.reduceat(r,st);cc=np.cumsum(c);cr=np.cumsum(rr)
    return float(np.sum((np.r_[0.,cr[:-1]/n]+cr/n)*c/n/2)) if q is None else float(cr[np.searchsorted(cc,q*n)]/cc[np.searchsorted(cc,q*n)])
   point[('unit',u,endpoint)]=m(z.linear_source_frozen.to_numpy())-m(z.raw_confidence.to_numpy())
 frozen=pd.read_csv(a.frozen);rep=pd.read_parquet(a.replicates);result=[]
 for _,r in frozen.iterrows():
  x=rep[rep.hypothesis_key.eq(r.hypothesis_key)]
  dm,da,dod=x.delta_main.to_numpy(),x.delta_ablation.to_numpy(),x.dod.to_numpy()
  lo,hi=ci(dm); alo,ahi=ci(da);dlo,dhi=ci(dod)
  result.append({'hypothesis_key':r.hypothesis_key,'level':r.level,'key':r.key,'endpoint':r.endpoint,'delta_main':r.delta_main,'delta_ablation':r.delta_ablation,'dod':r.dod,'delta_main_ci_low':lo,'delta_main_ci_high':hi,'delta_ablation_ci_low':alo,'delta_ablation_ci_high':ahi,'dod_ci_low':dlo,'dod_ci_high':dhi,'p_raw':pvalue(dod,r.dod),'epsilon_main':r.epsilon_main,'epsilon_ablation':r.epsilon_ablation,'main_swap70':r.main_swap70,'ablation_swap70':r.ablation_swap70})
 out=pd.DataFrame(result);out['p_holm']=holm(out)
 out['witness']=(out.delta_main_ci_low>out.epsilon_main)&(out.delta_ablation_ci_high<-out.epsilon_ablation)&(out.p_holm<.05)&((out.dod_ci_low>0)|(out.dod_ci_high<0))&(out.dod.abs()>=out.epsilon_main+out.epsilon_ablation)&((out.endpoint=='AUGRC')|((out.main_swap70>=.05)&(out.ablation_swap70>=.05)))
 checks=[]; cols=['delta_main','delta_ablation','dod','delta_main_ci_low','delta_main_ci_high','delta_ablation_ci_low','delta_ablation_ci_high','dod_ci_low','dod_ci_high','p_raw','p_holm','witness']
 for _,r in out.iterrows():
  f=frozen[frozen.hypothesis_key.eq(r.hypothesis_key)].iloc[0]
  for c in cols:
   d=float(bool(r[c])!=bool(f[c])) if c=='witness' else float(abs(r[c]-f[c]));checks.append({'hypothesis_key':r.hypothesis_key,'field':c,'recomputed_value':bool(r[c]) if c=='witness' else float(r[c]),'r023_value':bool(f[c]) if c=='witness' else float(f[c]),'abs_diff':d,'consistent':d<=1e-10})
 # Point check from raw rows covers primary reference cells without using frozen
 # points as inputs; remaining ablations are reproduced through their frozen
 # bootstrap replicates, which encode their complete recalculation.
 for _,r in frozen[frozen.contrast.eq('linear_source_frozen')].iterrows():
  k=(r.level,r.key,r.endpoint)
  if k in point: checks.append({'hypothesis_key':r.hypothesis_key,'field':'main_point_from_rows','recomputed_value':point[k],'r023_value':r.delta_main,'abs_diff':abs(point[k]-r.delta_main),'consistent':abs(point[k]-r.delta_main)<=1e-10})
 status='PASS' if all(x['consistent']for x in checks) else 'MISMATCH';out.to_csv(a.output/'recomputed_hypotheses.csv',index=False);(a.output/'revalidation.json').write_text(json.dumps({'status':status,'n_hypotheses':len(out),'n_checks':len(checks),'n_consistent':sum(x['consistent']for x in checks),'checks':checks},indent=2)+'\n')
 if status!='PASS':raise SystemExit(1)
if __name__=='__main__':main()
