#!/usr/bin/env python3
"""Frozen r042 outer held-out OER production fit; no target labels enter fitting."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT=Path('outputs/persistent_artifacts/orientbench_oer_stagea_r042_20260817')
IN=Path('audit_bundles/r036/inputs/qsetod_rows.parquet')
Z=['detection_score','log_pred_ar','log_area','class_name']; E=['u_axis','missing_fraction','iou_loss']
PARAM=dict(loss='squared_error',max_iter=200,max_leaf_nodes=15,learning_rate=.05,l2_regularization=.1,random_state=20260817)

def features(d): return d[Z].copy()
def hgb(cols=Z):
 nums=[x for x in cols if x!='class_name']; ts=[]
 if nums: ts.append(('num',SimpleImputer(strategy='median'),nums))
 if 'class_name' in cols: ts.append(('cls',make_pipeline(SimpleImputer(strategy='most_frequent'),OneHotEncoder(handle_unknown='ignore',sparse_output=False)),['class_name']))
 return make_pipeline(ColumnTransformer(ts,sparse_threshold=0),HistGradientBoostingRegressor(**PARAM))
def fold(d): return d.dataset.astype(str).str.cat(d.cluster.astype(str),sep='|').map(lambda x:int(__import__('hashlib').md5(x.encode()).hexdigest(),16)%5).to_numpy()
def oof_residual(train):
 f=fold(train); py=np.empty(len(train)); pe=np.empty((len(train),3))
 for k in range(5):
  a=f!=k;b=~a
  my=hgb().fit(features(train.loc[a]),train.loc[a,'Y']);py[b]=my.predict(features(train.loc[b]))
  for j,e in enumerate(E):
   m=hgb().fit(features(train.loc[a]),train.loc[a,e]);pe[b,j]=m.predict(features(train.loc[b]))
 return py,pe
def augrc(y,r):
 o=np.argsort(r,kind='mergesort'); y=y[o];r=r[o];n=len(y);i=0;loss=area=0.
 while i<n:
  j=i+1
  while j<n and r[j]==r[i]:j+=1
  old=loss;loss+=y[i:j].sum()/n;area+=.5*(old+loss)*(j-i)/n;i=j
 return area
def main():
 ROOT.mkdir(parents=True,exist_ok=True); d=pd.read_parquet(IN)
 d['Y']=np.clip(d.angle_error/90.,0,1); d=d[d.gt_ar>=2.1].copy()
 forbid={'Y','angle_error','gt_ar','unit','dataset'}
 assert not (forbid & set(Z+E))
 out=[]
 for u in sorted(d.unit.unique()):
  target=d[d.unit==u].copy(); td=target.dataset.iloc[0]; tf=target.detector.iloc[0]
  train=d[(d.dataset!=td)&(d.detector!=tf)].copy()
  assert not (set(train.dataset)=={td}) and not (train.dataset.eq(td).any() or train.detector.eq(tf).any())
  oy,oe=oof_residual(train); ridge=make_pipeline(StandardScaler(),Ridge(alpha=1.,fit_intercept=True)).fit(train[E].to_numpy()-oe,train.Y.to_numpy()-oy)
  my=hgb().fit(features(train),train.Y); mes=[hgb().fit(features(train),train[e]) for e in E]
  mz=my.predict(features(target)); te=target[E].to_numpy()-np.column_stack([m.predict(features(target)) for m in mes])
  oer=np.clip(mz+ridge.predict(te),0,1)
  # frozen deployable controls
  ar=hgb(['log_pred_ar']).fit(train[['log_pred_ar']],train.Y).predict(target[['log_pred_ar']])
  zplus=hgb(Z+E).fit(train[Z+E],train.Y).predict(target[Z+E])
  tta=np.mean((target[E].to_numpy()-train[E].mean().to_numpy())/train[E].std().replace(0,1).to_numpy(),axis=1)
  controls={'score':1-target.detection_score.to_numpy(),'pure_ar':ar,'m_y_z':mz,'generic_tta':tta,'z_plus_e':zplus}
  strongest=min(controls,key=lambda k:augrc(target.Y.to_numpy(),controls[k]))
  q=target[['row_id','unit','dataset','detector','cluster','class_name','Y','detection_score','log_pred_ar','log_area']+E].copy()
  q['risk_oer']=oer;q['m_y_z']=mz;q['ridge_adjustment']=ridge.predict(te);q['resid_u_axis']=te[:,0];q['resid_missing_fraction']=te[:,1];q['resid_iou_loss']=te[:,2]
  q['strongest_baseline']=strongest;q['risk_baseline']=controls[strongest];q['risk_z_plus_e']=zplus
  out.append(q)
 pd.concat(out,ignore_index=True).to_parquet(ROOT/'heldout_predictions.parquet',index=False)
 json.dump({'units':sorted(d.unit.unique()),'rows':int(sum(map(len,out))),'features_z':Z,'features_e':E,'params':PARAM},open(ROOT/'fit_manifest.json','w'),indent=2)
if __name__=='__main__':main()
