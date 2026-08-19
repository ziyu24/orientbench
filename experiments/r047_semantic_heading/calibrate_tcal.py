#!/usr/bin/env python3
"""Open only T_cal XMLs and create paired AHC calibration rows."""
import json,math, pickle, sys, xml.etree.ElementTree as ET
from pathlib import Path
import cv2,numpy as np,torch
from scipy.stats import binom
ROOT=Path(__file__).resolve().parents[2]; OUT=ROOT/'outputs/persistent_artifacts/orientbench_semantic_heading_r047_20260818'; DATA=Path('/home/rspip/cqc/data/dataset/HRSC2016')
sys.path.insert(0,str(ROOT/'experiments/r047_semantic_heading'))
from formal_train import Arm, crop
if not hasattr(np,'_core'):
 sys.modules.setdefault('numpy._core',np.core);sys.modules.setdefault('numpy._core.multiarray',np.core.multiarray);sys.modules.setdefault('numpy._core.numeric',np.core.numeric)

def box_iou(a,b):
 r1=((float(a[0]),float(a[1])),(float(a[2]),float(a[3])),math.degrees(float(a[4])))
 r2=((float(b[0]),float(b[1])),(float(b[2]),float(b[3])),math.degrees(float(b[4])))
 area=float(a[2])*float(a[3])+float(b[2])*float(b[3]); inter=cv2.rotatedRectangleIntersection(r1,r2)[1]
 if inter is None:return 0.
 return float(cv2.contourArea(inter))/(area-float(cv2.contourArea(inter)))
def gt_rows(iid):
 out=[]; root=ET.parse(DATA/'annfiles'/f'{iid}.xml').getroot()
 for j,o in enumerate(root.findall('HRSC_Objects/HRSC_Object')):
  f=lambda k:float(o.find(k).text); cx,cy,w,h,a,hx,hy=[f(k) for k in ('mbox_cx','mbox_cy','mbox_w','mbox_h','mbox_ang','header_x','header_y')]
  if h>w:w,h,a=h,w,a+math.pi/2
  a=(a+math.pi/2)%math.pi-math.pi/2; dx,dy=hx-cx,hy-cy; u=(math.cos(a),math.sin(a))
  if math.hypot(dx,dy)<.1*w or abs(dx*u[0]+dy*u[1])<.1*w:continue
  out.append({'instance_id':f'{iid}:{j}','box':(cx,cy,w,h,a),'label':int(dx*u[0]+dy*u[1]>0)})
 return out
def pred_map(path,kind):
 x=pickle.load(open(path,'rb')); d={}
 for z in x:
  iid=str(z.get('img_id')) if isinstance(z,dict) else None
  if iid is not None:
   b=z['pred_instances']['bboxes'].detach().cpu().numpy(); s=z['pred_instances']['scores'].detach().cpu().numpy(); d[iid]=[(tuple(q[:5]),float(sc)) for q,sc in zip(b,s) if float(sc)>=.05]
  else: raise RuntimeError('unexpected prediction schema')
 return d
def legacy_map(path,ids):
 x=pickle.load(open(path,'rb'));return {iid:[(tuple(q[:5]),float(q[5])) for q in arr[0]] for iid,arr in zip(ids,x)}
def main():
 ids=(OUT/'partitions/T_cal_ids.txt').read_text().split(); r50=pred_map(OUT/'tcal_r50_predictions.pkl','r50'); lsk=legacy_map(OUT/'tcal_lsknet_predictions.pkl',ids)
 device=torch.device('cuda' if torch.cuda.is_available() else 'cpu'); m=Arm('AHC').to(device); ck=torch.load(OUT/'formal/AHC_retry/best.pt',map_location='cpu');m.load_state_dict(ck);m.eval()
 rows=[]
 with torch.no_grad():
  for iid in ids:
   gs=gt_rows(iid)
   for g in gs:
    views=[('GT_BOX',g['box'],g['label'],1.0)]
    for name,pm in [('PRED_BOX_R50',r50.get(iid,[])),('PRED_BOX_LSKNET',lsk.get(iid,[]))]:
     cand=sorted(pm,key=lambda x:x[1],reverse=True); hit=max(cand,key=lambda x:box_iou(g['box'],x[0]),default=None)
     if hit is None or box_iou(g['box'],hit[0])<.5: continue
     pb=hit[0]; a=pb[4]; u=(math.cos(a),math.sin(a)); dx,dy=g['box'][0]-g['box'][0],g['box'][1]-g['box'][1]
     # The GT header direction is represented by the GT long-axis sign; transfer it to matched predicted axis.
     label=g['label'] if math.cos(g['box'][4]-a)>=0 else 1-g['label']; views.append((name,pb,label,hit[1]))
    for view,b,y,det_score in views:
     xm,xp,w,_=crop((iid,*b[:4],b[4],y),False); z=m(xm.unsqueeze(0).to(device),xp.unsqueeze(0).to(device),w.unsqueeze(0).to(device)).item(); p=1/(1+math.exp(-z)); conf=max(p,1-p); pred=int(p>=.5)
     rows.append({'row_id':f"{iid}|{g['instance_id']}|{view}",'image_id':iid,'instance_id':g['instance_id'],'view':view,'prob':p,'confidence':conf,'error':int(pred!=y),'detector_score':det_score})
 out=OUT/'tcal_rows.jsonl'; out.write_text(''.join(json.dumps(x)+'\n' for x in rows));
 summary={'rows':len(rows),'images':len(ids),'views':sorted(set(x['view'] for x in rows)),'xml_scope':'T_cal only','t_audit_xml_opened':False}
 for view in summary['views']:
  rr=[x for x in rows if x['view']==view]; best=None
  for q in (.9,.8,.7):
   thr=float(np.quantile([x['confidence'] for x in rr],1-q)); kept=[x for x in rr if x['confidence']>=thr]
   by={i:[z for z in kept if z['image_id']==i] for i in set(x['image_id'] for x in rr)}
   losses=[sum(z['error'] for z in by[i])/max(len(by[i]),1) for i in sorted(by)]
   n=len(losses); empirical=float(np.mean(losses)); k=int(math.floor(sum(losses)))
   # Bentkus inversion specified by the frozen plan; image losses are bounded in [0,1].
   lo,hi=empirical,1.0
   for _ in range(60):
    mid=(lo+hi)/2
    if math.e*float(binom.cdf(k,n,mid))<=.005: hi=mid
    else: lo=mid
   u=hi
   if q>=.7 and u<=.15 and best is None:best={'nominal':q,'threshold':thr,'coverage':len(kept)/max(len(rr),1),'risk':empirical,'ucb':u,'n_images':n,'sum_image_loss':sum(losses)}
  summary[view]=best or {'safe':False}
 (OUT/'tcal_summary.json').write_text(json.dumps(summary,indent=2)+'\n'); print(json.dumps(summary))
if __name__=='__main__':main()
