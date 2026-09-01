#!/usr/bin/env python3
"""Independent CPU audit for r002 risk semantics.

This module intentionally does not import r002's label, risk, NRC or gate
implementation.  Runtime locations are supplied only through environment
variables so the committed code is portable and contains no host paths.
"""
from __future__ import annotations
import hashlib,json,math,os,pickle
from collections import defaultdict
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from mmcv.ops import box_iou_rotated
from mmrotate.structures.bbox import qbox2rbox

ROOT=Path(os.environ['ORIENTBENCH_ROOT']); R=Path(os.environ['R002_RUNTIME']); OUT=Path(os.environ['R002_CORRECTION_OUT'])
import sys;sys.path[:0]=[str(ROOT),str(ROOT/'scripts')]
from orientbench.data.splits import assign_split
from m069_common import split_role
from derive_delta_theta_075 import load_interpolator
DTH=load_interpolator()
UNITS={'A':('DIOR-R','dior22'),'B':('DIOR-R','dior3'),'C':('DIOR-R','dior61'),'D':('FAIR1M-v1.0','fair24'),'E':('SODA-A','soda23'),'F':('SODA-A','soda4')}
ANN={'A':Path(os.environ['R002_DIOR_ANN']),'B':Path(os.environ['R002_DIOR_ANN']),'C':Path(os.environ['R002_DIOR_ANN']),'D':Path(os.environ['R002_FAIR_ANN']),'E':Path(os.environ['R002_SODA_ANN']),'F':Path(os.environ['R002_SODA_ANN'])}
AB=('airplane','airport','baseballfield','basketballcourt','bridge','chimney','dam','Expressway-Service-area','Expressway-toll-station','golffield','groundtrackfield','harbor','overpass','ship','stadium','storagetank','tenniscourt','trainstation','vehicle','windmill')
C=('airplane','airport','baseballfield','basketballcourt','bridge','chimney','Expressway-Service-area','Expressway-toll-station','dam','golffield','groundtrackfield','harbor','overpass','ship','stadium','storagetank','tenniscourt','trainstation','vehicle','windmill')
SODA=('airplane','helicopter','small-vehicle','large-vehicle','ship','container','storage-tank','swimming-pool','windmill')
FAIR=('Passenger Ship','Liquid Cargo Ship','Dry Cargo Ship','Motorboat','Fishing Boat','Warship','Engineering Ship','other-ship','Tugboat','Small Car','Cargo Truck','Van','Trailer','other-vehicle','Dump Truck','Bus','Tractor','Excavator','Truck Tractor','Boeing737','Boeing747','Boeing777','Boeing787','other-airplane','C919','A220','A321','A330','A350','ARJ21','Tennis Court','Football Field','Basketball Court','Baseball Field','Intersection','Bridge','Roundabout')
def classes(u):return FAIR if u=='D' else SODA if u in 'EF' else C if u=='C' else AB
def sha_frame(x):
 h=hashlib.sha256();h.update(pd.util.hash_pandas_object(x,index=False).values.tobytes());return h.hexdigest()
def le90(a,b):
 d=abs(a-b)%math.pi;return min(d,math.pi-d)
def long_axis(a,w,h):return (a+(math.pi/2 if w<h else 0.0))%math.pi
def parse(path):
 boxes=[];names=[];ids=[]
 for k,line in enumerate(path.read_text(errors='ignore').splitlines()):
  f=line.split()
  if len(f)<10 or f[-1]!='0':continue
  try:boxes.append([float(v) for v in f[:8]])
  except ValueError:continue
  names.append(' '.join(f[8:-1]));ids.append(k)
 if not boxes:return torch.empty((0,5)),np.asarray([],object),np.asarray([],int)
 return qbox2rbox(torch.tensor(boxes,dtype=torch.float32)),np.asarray(names),np.asarray(ids)
def metrics(score,risk):
 s=np.asarray(score,float);r=np.asarray(risk,float);o=np.argsort(-s,kind='stable');z=r[o];cum=np.cumsum(z)/np.arange(1,len(z)+1);oracle=np.mean(np.cumsum(np.sort(r,kind='stable'))/np.arange(1,len(r)+1));ar=float(np.mean(cum));
 return {'NRC':float((ar-oracle)/(np.mean(r)-oracle)),'AUGRC':ar,'Risk@70':float(cum[math.ceil(.7*len(z))-1]),'Risk@90':float(cum[math.ceil(.9*len(z))-1])}
def unit(u):
 ds,slug=UNITS[u]; raw=R/'raw'/slug/'identity.pkl'
 with raw.open('rb') as f: records=pickle.load(f)
 rows=[]; names=classes(u)
 for rec in records:
  image=str(rec['img_id']);inst=rec['pred_instances'];pb=inst['bboxes'].tensor if hasattr(inst['bboxes'],'tensor') else inst['bboxes'];pb=pb.cpu().float();ps=inst['scores'].cpu().numpy();pl=inst['labels'].cpu().numpy();gb,gn,gid=parse(ANN[u]/f'{image}.txt')
  for cls in np.unique(pl):
   pi=np.flatnonzero(pl==cls);gi=np.flatnonzero(gn==names[int(cls)]) if int(cls)<len(names) else []
   if not len(pi) or not len(gi):continue
   io=box_iou_rotated(pb[pi],gb[gi]).cpu().numpy(); used=set()
   for local in sorted(range(len(pi)),key=lambda j:(-float(ps[pi[j]]),int(pi[j]))):
    can=[(float(io[local,j]),j) for j in range(len(gi)) if j not in used]
    if not can:break
    val,j=max(can)
    if val<.5:continue
    used.add(j); p=pb[pi[local]];g=gb[gi[j]];gw,gh=float(g[2]),float(g[3]);ar=max(gw,gh)/max(min(gw,gh),1e-6)
    if ar<2.1:continue
    pred_rad=float(p[4]);gt_rad=float(g[4]);err_rad=le90(long_axis(pred_rad,float(p[2]),float(p[3])),long_axis(gt_rad,gw,gh));err_deg=math.degrees(err_rad);delta=float(DTH(ar));risk=min(err_deg/max(delta,1.0),3.0); assigned=assign_split(image);role='D_audit' if assigned=='D_audit' else 'D_cal-'+split_role(image)
    rows.append({'image_id':image,'pred_id':int(pi[local]),'gt_id':int(gid[gi[j]]),'class_id':int(cls),'cluster':image.split('__',1)[0] if ds=='SODA-A' else image,'role':role,'pred_angle_rad':pred_rad,'pred_angle_deg':math.degrees(pred_rad),'gt_angle_rad':gt_rad,'gt_angle_deg':math.degrees(gt_rad),'pred_long_axis_rad':long_axis(pred_rad,float(p[2]),float(p[3])),'gt_long_axis_rad':long_axis(gt_rad,gw,gh),'le90_error_rad':err_rad,'le90_error_deg':err_deg,'gt_width':gw,'gt_height':gh,'gt_ar':ar,'delta_075_deg':delta,'geometry_risk':risk,'identity_iou':val})
 out=pd.DataFrame(rows);feat=pd.read_parquet(R/'features'/f'{u}.parquet');out=out.merge(feat[['image_id','pred_id','class_id','detection_score','u_axis','missing_fraction','iou_loss']],on=['image_id','pred_id','class_id'],validate='one_to_one');out['standalone_score']=-(out.u_axis+out.missing_fraction+out.iou_loss)
 for p in sorted((R/'g1').glob(f'sealed_scores_*_{u}_seed*.parquet')):
  z=pd.read_parquet(p);seed=int(z.seed.iloc[0]); out=out.merge(z[['image_id','pred_id','class_id','predicted_risk','fusion_score']],on=['image_id','pred_id','class_id'],validate='one_to_one');out=out.rename(columns={'predicted_risk':f'gr_eqs_predicted_risk_{seed}','fusion_score':f'fusion_score_{seed}'})
 q=out[out.role=='D_audit']; row={'unit':u,'dataset':ds,'rows':len(q),'clusters':q.cluster.nunique(),'row_hash':sha_frame(q[['image_id','pred_id','gt_id','cluster']]),'risk_min':float(q.geometry_risk.min()),'risk_mean':float(q.geometry_risk.mean()),'risk_p90':float(q.geometry_risk.quantile(.9))};row.update(metrics(q.standalone_score,q.geometry_risk));
 OUT.mkdir(parents=True,exist_ok=True);(OUT/'compact_rows').mkdir(exist_ok=True);out.to_parquet(OUT/'compact_rows'/f'{u}.parquet',compression='zstd',index=False);return row
def main():
 rows=[unit(u) for u in UNITS];pd.DataFrame(rows).to_csv(OUT/'r002_independent_metrics.csv',index=False);print(json.dumps(rows))
if __name__=='__main__':main()
