#!/usr/bin/env python3
"""Independent raw-input recomputation and mutation-sensitive validator B."""
import argparse, csv, json, math, pickle, sys
import xml.etree.ElementTree as ET
from pathlib import Path

import cv2
import numpy as np
from scipy.stats import binom

QS=(.25,.50,1.)

def box5(v):
    x,y,w,h,t=[float(q) for q in v[:5]]
    if w<h: w,h,t=h,w,t+np.pi/2
    t=(t+np.pi/2)%np.pi-np.pi/2
    return np.array((x,y,w,h,t))

def pts(v):
    x,y,w,h,t=box5(v); u=np.array(((w/2,h/2),(-w/2,h/2),(-w/2,-h/2),(w/2,-h/2)),np.float32)
    return u@np.array(((np.cos(t),np.sin(t)),(-np.sin(t),np.cos(t))),np.float32)+np.array((x,y),np.float32)

def overlap(a,b):
    pa,pb=pts(a),pts(b); inter=cv2.intersectConvexConvex(pa,pb)[0]
    return float(inter/max(abs(cv2.contourArea(pa))+abs(cv2.contourArea(pb))-inter,1e-12))

def angular(a,b):
    z=abs(box5(a)[4]-box5(b)[4])%np.pi
    return float(np.degrees(min(z,np.pi-z)))

def load_gt(folder,iid):
    doc=ET.parse(Path(folder)/(iid+'.xml')).getroot(); ans=[]
    for obj in doc.findall('HRSC_Objects/HRSC_Object'):
        ans.append(box5(tuple(float(obj.find(x).text) for x in ('mbox_cx','mbox_cy','mbox_w','mbox_h','mbox_ang'))))
    return ans

def numpy(x): return np.asarray(x.cpu() if hasattr(x,'cpu') else x)

def predictions(filename,ids):
    raw=pickle.load(open(filename,'rb')); ans={}
    if isinstance(raw[0],dict):
        for sample in raw:
            p=sample['pred_instances']; ans[str(sample['img_id'])]=[(box5(b),float(s),int(c)) for b,s,c in zip(numpy(p['bboxes']),numpy(p['scores']),numpy(p['labels']))]
    else:
        for iid,classes in zip(ids,raw): ans[iid]=[(box5(b[:5]),float(b[5]),c) for c,bb in enumerate(classes) for b in np.asarray(bb)]
    return ans

def matched(pred,truth,ids,mutation=None):
    ans={i:[] for i in ids}; first=True
    for iid in ids:
        used=set()
        for pid,(b,s,c) in enumerate(sorted(pred[iid],key=lambda x:-x[1])):
            opts=[(overlap(b,g),j) for j,g in enumerate(truth[iid]) if j not in used and c==0]; ov,j=max(opts,default=(0.,-1))
            if ov<.5: continue
            used.add(j); g=truth[iid]; g=g[j]; e=angular(b,g); ar=box5(g)[2]/box5(g)[3]
            if first and mutation=='angle_error': e+=1.; first=False
            if first and mutation=='gt_ar': ar*=1.1; first=False
            d=min(1.,ar/2*np.sin(np.radians(e)))
            ans[iid].append((s,ar,d,tuple(int(d>q) for q in QS)))
    return ans

def image_arrays(match,ids,threshold):
    d=[]; zs=[[],[],[]]; eligible=retained=0
    for iid in ids:
        base=[r for r in match[iid] if r[1]>=2.1]; keep=[r for r in base if r[0]>=threshold]; eligible+=len(base); retained+=len(keep)
        d.append(np.mean([r[2] for r in keep]) if keep else 0.)
        for k in range(3): zs[k].append(np.mean([r[3][k] for r in keep]) if keep else 0.)
    return np.asarray(d),[np.asarray(z) for z in zs],retained/max(eligible,1),retained,eligible

def upper(v):
    n=len(v); m=float(np.mean(v)); h=min(1.,m+np.sqrt(np.log(20)/(2*n))); k=int(np.ceil(n*m-1e-12)); lo,hi=m,1.
    for _ in range(80):
        q=(lo+hi)/2
        if np.e*binom.cdf(k,n,q)<=.05: hi=q
        else: lo=q
    return float(min(h,hi))

def average_precision(pred,truth,ids,cut):
    ranked=sorted(((s,i,b) for i in ids for b,s,c in pred[i] if c==0 and s>=cut),key=lambda x:-x[0]); used={i:set() for i in ids}; tp=[]
    for s,i,b in ranked:
        choices=[(overlap(b,g),j) for j,g in enumerate(truth[i]) if j not in used[i]]; ov,j=max(choices,default=(0.,-1)); ok=ov>=.5; tp.append(ok)
        if ok: used[i].add(j)
    t=np.cumsum(tp); f=np.cumsum(np.logical_not(tp)); r=t/sum(map(len,truth.values())); p=t/np.maximum(t+f,1); r=np.r_[0,r,1]; p=np.maximum.accumulate(np.r_[0,p,0][::-1])[::-1]
    return float(np.sum(np.diff(r)*p[1:]))

def main():
    q=argparse.ArgumentParser(); q.add_argument('--split',required=True); q.add_argument('--ann-dir',required=True); q.add_argument('--dcal-pred',required=True); q.add_argument('--ap-pred',required=True); q.add_argument('--orientation-pred',required=True); q.add_argument('--implementation-a',required=True); q.add_argument('--out',required=True); q.add_argument('--mutation',choices=['split_member','target_threshold','angle_error','gt_ar','policy_token']); a=q.parse_args()
    ids=[r['image_id'] for r in csv.DictReader(open(a.split))]
    if a.mutation=='split_member': ids=ids[:-1]
    dcal=pickle.load(open(a.dcal_pred,'rb')); scores=np.concatenate([numpy(x['pred_instances']['scores']) for x in dcal]); threshold=float(np.quantile(scores,.1,method='higher'))
    if a.mutation=='target_threshold': threshold+=.01
    if a.mutation=='policy_token': print('policy token mismatch',file=sys.stderr); return 9
    truth={i:load_gt(a.ann_dir,i) for i in ids}; pp={'ap':predictions(a.ap_pred,ids),'orientation':predictions(a.orientation_pred,ids)}
    mm={f:matched(pp[f],truth,ids,a.mutation) for f in pp}; tables={}; summary={}
    for f in pp:
        cut=-np.inf if f=='ap' else threshold; d,z,cov,n,n0=image_arrays(mm[f],ids,cut); tables[f]=(d,z)
        summary[f]={'mean_d_tip':float(d.mean()),'risk_z_0_25':float(z[0].mean()),'risk_z_0_50':float(z[1].mean()),'risk_z_1_00':float(z[2].mean()),'hb_ucb_z_0_50':upper(z[1]),'eligible_matched_coverage':float(cov),'eligible_retained':n,'eligible_full':n0,'ap50':average_precision(pp[f],truth,ids,cut)}
    dc=tables['ap'][0]-tables['orientation'][0]; ds=tables['ap'][1][1]-tables['orientation'][1][1]; rng=np.random.default_rng(20260818); idx=rng.integers(0,len(ids),(10000,len(ids))); bc=dc[idx].mean(1); bs=ds[idx].mean(1)
    result={'images':len(ids),'threshold':threshold,'policies':summary,'delta_cont':float(dc.mean()),'delta_cont_ci95':[float(x) for x in np.quantile(bc,[.025,.975])],'delta_severe':float(ds.mean()),'delta_severe_ci95':[float(x) for x in np.quantile(bs,[.025,.975])],'sensitivity_delta':{f'{x:.2f}':float(tables['ap'][1][k].mean()-tables['orientation'][1][k].mean()) for k,x in enumerate(QS)}}
    ref=json.load(open(a.implementation_a)); diffs=[]
    def chk(name,x,y,tol):
        if abs(float(x)-float(y))>tol: diffs.append({'field':name,'a':y,'b':x,'tolerance':tol})
    chk('images',result['images'],ref['images'],0); chk('threshold',threshold,ref['threshold'],1e-12)
    for f in pp:
        for key,value in summary[f].items(): chk(f'{f}.{key}',value,ref['policies'][f][key],1e-12)
    for key in ('delta_cont','delta_severe'): chk(key,result[key],ref[key],1e-12)
    for key in ('delta_cont_ci95','delta_severe_ci95'):
        for k in range(2): chk(f'{key}[{k}]',result[key][k],ref[key][k],1e-10)
    for key,value in result['sensitivity_delta'].items(): chk('sensitivity.'+key,value,ref['sensitivity_delta'][key],1e-12)
    payload={'schema_version':2,'pristine':a.mutation is None,'mutation':a.mutation,'status':'PASS' if not diffs else 'FAIL','differences':diffs,'recomputed':result,'tolerances':{'deterministic':1e-12,'bootstrap_endpoints':1e-10}}
    Path(a.out).write_text(json.dumps(payload,indent=2,sort_keys=True)+'\n')
    return 0 if not diffs else 7

if __name__=='__main__': sys.exit(main())
