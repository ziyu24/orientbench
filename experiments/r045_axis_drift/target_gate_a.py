#!/usr/bin/env python3
"""Implementation A for the sealed r045 HRSC application gate."""
from __future__ import annotations

import argparse, csv, hashlib, json, math, pickle
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
from scipy.stats import binom

Q_GRID=(0.25,0.50,1.00)

def canon(b):
    x,y,w,h,t=map(float,b[:5])
    if h>w: w,h,t=h,w,t+math.pi/2
    return np.array([x,y,w,h,((t+math.pi/2)%math.pi)-math.pi/2],float)

def poly(b):
    x,y,w,h,t=canon(b); p=np.array([[w/2,h/2],[-w/2,h/2],[-w/2,-h/2],[w/2,-h/2]],np.float32)
    c,s=math.cos(t),math.sin(t)
    return p@np.array([[c,s],[-s,c]],np.float32)+np.array([x,y],np.float32)

def riou(a,b):
    pa,pb=poly(a),poly(b); aa,ab=abs(cv2.contourArea(pa)),abs(cv2.contourArea(pb)); inter,_=cv2.intersectConvexConvex(pa,pb)
    return float(inter/max(aa+ab-inter,1e-12))

def err(a,b):
    d=abs(canon(a)[4]-canon(b)[4])%math.pi
    return math.degrees(min(d,math.pi-d))

def gt_boxes(task):
    image_id,ann_dir=task; root=ET.parse(Path(ann_dir)/f'{image_id}.xml').getroot(); out=[]
    for o in root.findall('HRSC_Objects/HRSC_Object'):
        out.append(canon([float(o.find(k).text) for k in ('mbox_cx','mbox_cy','mbox_w','mbox_h','mbox_ang')]))
    return image_id,out

def arr(x): return np.asarray(x.detach().cpu() if hasattr(x,'detach') else x)

def load_preds(path,ids):
    raw=pickle.load(open(path,'rb')); out={}
    if raw and isinstance(raw[0],dict):
        for z in raw:
            pi=z['pred_instances']; out[str(z['img_id'])]=[(canon(b),float(s),int(l)) for b,s,l in zip(arr(pi['bboxes']),arr(pi['scores']),arr(pi['labels']))]
    else:
        if len(raw)!=len(ids): raise RuntimeError(f'legacy order mismatch {len(raw)} != {len(ids)}')
        for iid,per_class in zip(ids,raw):
            out[iid]=[(canon(b[:5]),float(b[5]),lab) for lab,boxes in enumerate(per_class) for b in np.asarray(boxes)]
    if set(out)!=set(ids): raise RuntimeError('prediction/split member mismatch')
    return out

def match_one(task):
    family,iid,preds,gts=task; used=set(); rows=[]
    for pred_id,(box,score,label) in enumerate(sorted(preds,key=lambda z:-z[1])):
        opts=[(riou(box,g),j) for j,g in enumerate(gts) if j not in used and label==0]
        best,j=max(opts,default=(0.,-1))
        if best<.5: continue
        used.add(j); g=gts[j]; e=err(box,g); ar=float(g[2]/max(g[3],1e-12)); d=min(1.,(ar/2.)*math.sin(math.radians(e)))
        rows.append(dict(family=family,image_id=iid,prediction_id=pred_id,gt_id=j,score=score,iou=best,angle_error_deg=e,gt_ar=ar,d_tip=d,z_0_25=int(d>.25),z_0_50=int(d>.5),z_1_00=int(d>1.)))
    return rows

def hb(values,alpha=.05):
    values=np.asarray(values,float); n=len(values); mean=float(values.mean()); h=min(1.,mean+math.sqrt(math.log(1/alpha)/(2*n))); k=int(math.ceil(n*mean-1e-12)); lo,hi=mean,1.
    for _ in range(80):
        mid=(lo+hi)/2
        if math.e*binom.cdf(k,n,mid)<=alpha: hi=mid
        else: lo=mid
    return min(h,hi)

def ap50(pred,gts,ids,threshold):
    det=sorted([(s,i,b) for i in ids for b,s,l in pred[i] if l==0 and s>=threshold],reverse=True,key=lambda z:z[0]); used={i:set() for i in ids}; tp=[]; fp=[]
    for s,i,b in det:
        opts=[(riou(b,g),j) for j,g in enumerate(gts[i]) if j not in used[i]]; best,j=max(opts,default=(0.,-1))
        ok=best>=.5; tp.append(int(ok)); fp.append(int(not ok))
        if ok: used[i].add(j)
    if not tp:return 0.
    tp=np.cumsum(tp); fp=np.cumsum(fp); rec=tp/max(sum(len(gts[i]) for i in ids),1); prec=tp/np.maximum(tp+fp,1); mr=np.r_[0.,rec,1.]; mp=np.r_[0.,prec,0.]; mp=np.maximum.accumulate(mp[::-1])[::-1]
    return float(np.sum((mr[1:]-mr[:-1])*mp[1:]))

def boot_chunk(task):
    idx,dc,ds=task
    return np.column_stack((dc[idx].mean(1),ds[idx].mean(1)))

def main():
    p=argparse.ArgumentParser(); p.add_argument('--split',required=True); p.add_argument('--ann-dir',required=True); p.add_argument('--ap-pred',required=True); p.add_argument('--orientation-pred',required=True); p.add_argument('--threshold',type=float,required=True); p.add_argument('--out',required=True); a=p.parse_args()
    out=Path(a.out); out.mkdir(parents=True,exist_ok=True); ids=[r['image_id'] for r in csv.DictReader(open(a.split))]
    with ProcessPoolExecutor(max_workers=48) as ex: gts=dict(ex.map(gt_boxes,[(i,a.ann_dir) for i in ids]))
    preds={'ap':load_preds(a.ap_pred,ids),'orientation':load_preds(a.orientation_pred,ids)}
    tasks=[(f,i,preds[f][i],gts[i]) for f in preds for i in ids]
    with ProcessPoolExecutor(max_workers=48) as ex: nested=list(ex.map(match_one,tasks))
    rows=pd.DataFrame([r for x in nested for r in x]); rows.to_csv(out/'target_instance_rows_a.csv',index=False)
    full_eligible={f:int(((rows.family==f)&(rows.gt_ar>=2.1)).sum()) for f in preds}; image_tables={}; summary={}
    for f in preds:
        t=-math.inf if f=='ap' else a.threshold; x=rows[(rows.family==f)&(rows.score>=t)&(rows.gt_ar>=2.1)]
        im=pd.DataFrame({'image_id':ids})
        for col in ('d_tip','z_0_25','z_0_50','z_1_00'): im[col]=im.image_id.map(x.groupby('image_id')[col].mean()).fillna(0.)
        im.to_csv(out/f'target_image_rows_{f}_a.csv',index=False); image_tables[f]=im
        summary[f]={'mean_d_tip':float(im.d_tip.mean()),'risk_z_0_25':float(im.z_0_25.mean()),'risk_z_0_50':float(im.z_0_50.mean()),'risk_z_1_00':float(im.z_1_00.mean()),'hb_ucb_z_0_50':hb(im.z_0_50),'eligible_matched_coverage':float(len(x)/max(full_eligible[f],1)),'eligible_retained':len(x),'eligible_full':full_eligible[f],'ap50':ap50(preds[f],gts,ids,t)}
    dc=image_tables['ap'].d_tip.to_numpy()-image_tables['orientation'].d_tip.to_numpy(); ds=image_tables['ap'].z_0_50.to_numpy()-image_tables['orientation'].z_0_50.to_numpy(); rng=np.random.default_rng(20260818); idx=rng.integers(0,len(ids),size=(10000,len(ids))); chunks=np.array_split(idx,48)
    with ProcessPoolExecutor(max_workers=48) as ex: bv=np.concatenate(list(ex.map(boot_chunk,[(c,dc,ds) for c in chunks])))
    delta_cont=float(dc.mean()); delta_severe=float(ds.mean()); ci_cont=[float(x) for x in np.quantile(bv[:,0],[.025,.975])]; ci_severe=[float(x) for x in np.quantile(bv[:,1],[.025,.975])]
    sens={f'{q:.2f}':float(image_tables['ap'][f'z_{q:.2f}'.replace('.','_')].mean()-image_tables['orientation'][f'z_{q:.2f}'.replace('.','_')].mean()) for q in Q_GRID}
    checks={'decision_change':True,'continuous':delta_cont>=.02 and ci_cont[0]>0,'severe':delta_severe>0 and ci_severe[0]>0,'risk_ucb':summary['orientation']['hb_ucb_z_0_50']<=.10,'eligible_coverage':summary['orientation']['eligible_matched_coverage']>=.70,'ap50_survival':summary['orientation']['ap50']>=summary['ap']['ap50']-.02,'sensitivity':sum(v>0 for v in sens.values())>=2 and sens['0.50']>0}
    result={'schema_version':2,'terminal_state':'JPRS_DECISION_STUDY_PASS' if all(checks.values()) else 'APPLICATION_SHIFT_FAIL','images':len(ids),'threshold':a.threshold,'policies':summary,'delta_cont':delta_cont,'delta_cont_ci95':ci_cont,'delta_severe':delta_severe,'delta_severe_ci95':ci_severe,'sensitivity_delta':sens,'checks':checks,'bootstrap':{'replicates':10000,'seed':20260818,'workers':48,'exchange_unit':'image','paired':True},'matching':{'workers':48,'class_aware':True,'riou_threshold':.5,'gt_ar_min':2.1}}
    (out/'implementation_a.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,indent=2))

if __name__=='__main__': main()
