"""Frozen-universe r004 primary-loss audit (angle-free matching, le90 outcome)."""
from __future__ import annotations
import argparse, json, math, pickle
from pathlib import Path
import numpy as np
from orientbench.core.geometry import canonical_longside_theta, angle_error_rad

def arr(x): return np.asarray(x.detach().cpu(),float)
def pairs(rec):
 g,p=arr(rec['gt_instances']['bboxes']),arr(rec['pred_instances']['bboxes']); out=[]; used=set()
 for gi,z in enumerate(g):
  best=None
  for pi,q in enumerate(p):
   if pi in used: continue
   dc=math.hypot(z[0]-q[0],z[1]-q[1])/max(math.sqrt(z[2]*z[3]),1)
   ar=(q[2]*q[3])/max(z[2]*z[3],1e-9); ss=sum(abs(math.log(a/b)) for a,b in zip(sorted(z[2:4]),sorted(q[2:4])))
   if dc<=.5 and .25<=ar<=4 and ss<=math.log(4): best=min(best,(dc+ss,pi)) if best else (dc+ss,pi)
  if best: used.add(best[1]);out.append((gi,best[1]))
 return out
def load(p):
 with open(p,'rb') as f:return pickle.load(f)
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,required=True);a.add_argument('--out',type=Path,required=True);x=a.parse_args(); R={}
 for m in ('oriented_rcnn_r50','rotated_rtmdet_m'):
  base=x.root/'inference/test'/m; clean=load(base/'clean/predictions.pkl'); cm={r['img_id']:(r,pairs(r)) for r in clean}; cells=[]
  for label in ('blur_1.5','blur_1.25','downsample_2','downsample_1.75'):
   vals=[]
   for r1 in load(base/label/'predictions.pkl'):
    r0,pp=cm[r1['img_id']]; p0,p1=arr(r0['pred_instances']['bboxes']),arr(r1['pred_instances']['bboxes']); g=arr(r0['gt_instances']['bboxes']); q1={gi:pi for gi,pi in pairs(r1)}
    for gi,pi0 in pp:
     e0=angle_error_rad(canonical_longside_theta(*p0[pi0,2:5]),canonical_longside_theta(*g[gi,2:5])); y0=e0/(math.pi/2)
     if gi in q1:
      e1=angle_error_rad(canonical_longside_theta(*p1[q1[gi],2:5]),canonical_longside_theta(*g[gi,2:5])); ca=(e1-e0)/(math.pi/2); miss=0
     else: ca=0;miss=1-y0
     vals.append((r0['img_id'],1,miss,ca,miss+ca))
   by={};
   for im,_,mi,an,d in vals: by.setdefault(im,[]).append((mi,an,d))
   means=np.array([[np.mean([v[i] for v in z]) for i in range(3)] for z in by.values()])
   cells.append({'condition':label,'images':len(by),'objects':len(vals),'missing':float(means[:,0].mean()),'retained_angle':float(means[:,1].mean()),'deltaY':float(means[:,2].mean())})
  R[m]=cells
 x.out.parent.mkdir(parents=True,exist_ok=True);x.out.write_text(json.dumps(R,indent=2)+'\n')
if __name__=='__main__':main()
