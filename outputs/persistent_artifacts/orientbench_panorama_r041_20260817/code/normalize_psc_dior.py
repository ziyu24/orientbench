#!/usr/bin/env python3
"""Normalize the completed PSC DIOR three-view dumps into r041's common rows."""
import csv, glob, math, multiprocessing as mp, os, pickle
from pathlib import Path
import cv2, numpy as np, pandas as pd

ROOT=Path('outputs/persistent_artifacts/orientbench_panorama_r041_20260817')
UNIT=os.environ.get('R041_UNIT','unit_022_psc_dior'); OUTPUT_STEM=os.environ.get('R041_OUTPUT_STEM','psc_dior'); V=ROOT/'units'/UNIT/'views'
LEGACY_MMROTATE=os.environ.get('R041_LEGACY_MMROTATE','0') == '1'
ANN=Path('top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test')
RAW_IMAGES=Path('/home/rspip/cqc/data/dataset/DIOR/images/test')
CLASSES=['airplane','airport','baseballfield','basketballcourt','bridge','chimney','dam','Expressway-Service-area','Expressway-toll-station','golffield','groundtrackfield','harbor','overpass','ship','stadium','storagetank','tenniscourt','trainstation','vehicle','windmill']
SCHEMA=['unit_id','image_id','pred_id','gt_id','class_id','cluster_id','angle_error_deg','Y','detection_score','pred_w','pred_h','gt_w','gt_h','pred_ar','gt_ar','pred_area','iou','u_axis','missing_fraction','iou_loss','center_dispersion','scale_dispersion','score_dispersion','association_ambiguity']

def canon(b):
 c=np.array(b[:5],float); c[4]=((c[4]+math.pi/2)%math.pi)-math.pi/2
 if c[3]>c[2]: c[2],c[3]=c[3],c[2]; c[4]=((c[4]+math.pi/2+math.pi/2)%math.pi)-math.pi/2
 return c
def poly(b):
 x,y,w,h,t=canon(b); q=np.array([[w/2,h/2],[-w/2,h/2],[-w/2,-h/2],[w/2,-h/2]],np.float32); c,s=math.cos(t),math.sin(t); return q@np.array([[c,s],[-s,c]],np.float32)+np.array([x,y],np.float32)
def riou(a,b):
 pa,pb=poly(a),poly(b); aa,ab=abs(cv2.contourArea(pa)),abs(cv2.contourArea(pb)); inter,_=cv2.intersectConvexConvex(pa,pb); return float(inter/max(aa+ab-inter,1e-9))
def gt(i):
 out=[]
 for line in (ANN/f'{i}.txt').read_text().splitlines():
  z=line.split();
  if len(z)<10 or z[8] not in CLASSES: continue
  p=np.array(z[:8],np.float32).reshape(4,2); (x,y),(w,h),ang=cv2.minAreaRect(p); out.append((canon([x,y,w,h,math.radians(ang)]),CLASSES.index(z[8])))
 return out
def read(p):
 raw=pickle.load(open(p,'rb')); out=[]
 if LEGACY_MMROTATE:
  # The legacy DIORDataset writes results in its glob.glob traversal order.
  # Preserve that order exactly; lexical sorting would associate predictions
  # with the wrong images on this transferred filesystem.
  ids=[Path(x).stem for x in glob.glob(str(ANN/'*.txt'))]
  if len(raw)!=len(ids): raise RuntimeError(f'legacy result/image count mismatch: {len(raw)} != {len(ids)}')
  for iid,r in zip(ids,raw):
   im=cv2.imread(str(RAW_IMAGES/f'{iid}.jpg'))
   if im is None: raise FileNotFoundError(RAW_IMAGES/f'{iid}.jpg')
   ps=[]
   for label, boxes in enumerate(r):
    for b in np.asarray(boxes): ps.append((canon(b[:5]),float(b[5]),label))
   out.append((iid,tuple(im.shape[:2]),ps))
  return out
 for r in raw:
  pi=r['pred_instances']; cv=lambda a: np.asarray(a.cpu() if hasattr(a,'cpu') else a)
  out.append((str(r['img_id']),tuple(r['ori_shape'][:2]),[(canon(b),float(s),int(l)) for b,s,l in zip(cv(pi['bboxes']),cv(pi['scores']),cv(pi['labels']))]))
 return out
def inv(b,sh,v):
 q=canon(b); h,w=sh
 if v=='hflip': q[0],q[4]=w-q[0],math.pi-q[4]
 if v=='vflip': q[1],q[4]=h-q[1],-q[4]
 return canon(q)
VIEWS=None
def process_one(ix):
 iid,sh,ps=VIEWS['identity'][ix]; gs=gt(iid); used=set(); rows=[]
 for pid,(b,s,l) in enumerate(sorted(ps,key=lambda x:-x[1])):
  opts=[(riou(b,g),j) for j,(g,c) in enumerate(gs) if j not in used and c==l]; best,j=max(opts,default=(0,-1))
  if best<.5: continue
  used.add(j); g,_=gs[j]; assoc=[(b,s,1.)]; amb=[]
  for vn in ('hflip','vflip'):
   c=sorted([(riou(b,inv(q,sh,vn)),inv(q,sh,vn),qs) for q,qs,ql in VIEWS[vn][ix][2] if ql==l],reverse=True,key=lambda x:x[0]); amb.append(1-(c[0][0]-c[1][0] if len(c)>1 else c[0][0] if c else 0))
   if c and c[0][0]>=.5: assoc.append((c[0][1],c[0][2],c[0][0]))
  a=np.array([x[0] for x in assoc]); z=abs(np.mean(np.exp(2j*a[:,4]))); de=abs((b[4]-g[4])%math.pi); de=math.degrees(min(de,math.pi-de)); areas=a[:,2]*a[:,3]
  rows.append([UNIT,iid,pid,j,l,iid,de,de/90,s,b[2],b[3],g[2],g[3],b[2]/max(b[3],1e-9),g[2]/max(g[3],1e-9),b[2]*b[3],best,1-z,1-len(assoc)/3,1-np.mean([x[2] for x in assoc]),float(np.std(np.linalg.norm(a[:,:2]-a[:,:2].mean(0),axis=1))),float(np.std(np.log(np.maximum(areas,1e-9)))),float(np.std([x[1] for x in assoc])),float(np.mean(amb))])
 return rows
def main():
 paths={'identity':ROOT/'units'/UNIT/'parity'/'identity.pkl','hflip':V/'hflip.pkl','vflip':V/'vflip.pkl'}
 global VIEWS; VIEWS={k:read(p) for k,p in paths.items()}; rows=[]
 with mp.get_context('fork').Pool(processes=40) as pool:
  for part in pool.imap_unordered(process_one,range(len(VIEWS['identity'])),chunksize=24): rows.extend(part)
 out=ROOT/'normalized'; out.mkdir(exist_ok=True); pd.DataFrame(sorted(rows,key=lambda r:(r[1],r[2])),columns=SCHEMA).to_csv(out/f'matched_rows_{OUTPUT_STEM}.csv',index=False)
if __name__=='__main__': main()
