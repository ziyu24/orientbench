#!/usr/bin/env python3
"""One sealed HRSC D_audit matching/evaluation pass for r045."""
import csv,json,math,pickle,xml.etree.ElementTree as ET
from pathlib import Path
import cv2,numpy as np,pandas as pd

ROOT=Path('/home/rspip/cqc/pro/study/orientbench'); DATA=Path('/home/rspip/cqc/data/dataset/HRSC2016')
OUT=ROOT/'outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/target_analysis'; OUT.mkdir(parents=True,exist_ok=True)
ids=[r['image_id'] for r in csv.DictReader(open(ROOT/'outputs/bench_core/splits/D_audit_hrsc_trainval.csv'))]
threshold=.05102584883570671
def canon(b):
 x,y,w,h,t=map(float,b[:5]);
 if h>w:w,h,t=h,w,t+math.pi/2
 return np.array([x,y,w,h,((t+math.pi/2)%math.pi)-math.pi/2])
def poly(b):
 x,y,w,h,t=canon(b); q=np.array([[w/2,h/2],[-w/2,h/2],[-w/2,-h/2],[w/2,-h/2]],np.float32);c,s=math.cos(t),math.sin(t);return (q@np.array([[c,s],[-s,c]],np.float32)+[x,y]).astype(np.float32)
def iou(a,b):
 pa,pb=poly(a),poly(b); aa,ab=abs(cv2.contourArea(pa)),abs(cv2.contourArea(pb));inter,_=cv2.intersectConvexConvex(pa,pb);return inter/max(aa+ab-inter,1e-12)
def gt(i):
 r=ET.parse(DATA/'annfiles'/f'{i}.xml').getroot();return [canon([o.find(k).text for k in ['mbox_cx','mbox_cy','mbox_w','mbox_h','mbox_ang']]) for o in r.findall('HRSC_Objects/HRSC_Object')]
def load(p,legacy=False):
 x=pickle.load(open(p,'rb'));out={}
 if legacy:
  for i,a in zip(ids,x):out[i]=[(canon(b[:5]),float(b[5])) for z in a for b in np.asarray(z)]
 else:
  for z in x:
   pi=z['pred_instances'];out[str(z['img_id'])]=[(canon(b),float(s)) for b,s in zip(pi['bboxes'].cpu().numpy(),pi['scores'].cpu().numpy())]
 return out
def rows(preds,keep):
 res=[]
 for i in ids:
  used=set()
  for n,(b,s) in enumerate(sorted(preds[i],key=lambda x:-x[1])):
   if not keep(s):continue
   opts=[(iou(b,g),j) for j,g in enumerate(gt(i)) if j not in used];v,j=max(opts,default=(0,-1))
   if v<.5:continue
   used.add(j);g=gt(i)[j]; ar=g[2]/g[3]
   if ar<2.1:continue
   e=abs((b[4]-g[4])%math.pi);e=min(e,math.pi-e);d=min(1.,ar/2*math.sin(e));res.append([i,n,s,ar,math.degrees(e),d,int(d>.25),int(d>.5),int(d>1)])
 return pd.DataFrame(res,columns=['image_id','pred_id','score','gt_ar','angle_error_deg','d_tip','z025','z050','z100'])
r50=load(ROOT/'outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/target_predictions/hrsc_r50_audit.pkl');lsk=load(ROOT/'outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/target_predictions/hrsc_lsknet_audit.pkl',True)
a=rows(lsk,lambda s:True);o=rows(r50,lambda s:s>=threshold);a.to_csv(OUT/'ap_policy_rows.csv',index=False);o.to_csv(OUT/'orientation_policy_rows.csv',index=False)
def im(df,col):return df.groupby('image_id')[col].mean().reindex(ids,fill_value=0.).to_numpy()
rng=np.random.default_rng(20260818); ix=rng.integers(0,len(ids),(10000,len(ids)))
out={}
for q,c in [(0.25,'z025'),(.5,'z050'),(1.,'z100')]:
 da,do=im(a,'d_tip'),im(o,'d_tip'); ra,ro=im(a,c),im(o,c); dc=da-do; ds=ra-ro
 out[str(q)]={'delta_cont':float(dc.mean()),'delta_cont_ci':[float(x) for x in np.quantile(dc[ix].mean(1),[.025,.975])],'delta_severe':float(ds.mean()),'delta_severe_ci':[float(x) for x in np.quantile(ds[ix].mean(1),[.025,.975])],'orientation_risk':float(ro.mean()),'coverage':float(len(o)/max(1,len(a)))}
(OUT/'target_metrics.json').write_text(json.dumps({'seed':20260818,'images':len(ids),'threshold':threshold,'q':out},indent=2)+'\n')
