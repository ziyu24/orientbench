#!/usr/bin/env python3
"""User-authorized r025 DOTA external replication: DIOR-frozen linear probe."""
from __future__ import annotations
import argparse, hashlib, json, math, multiprocessing as mp, pickle, sys, time
from pathlib import Path
import numpy as np
import pandas as pd
import torch
from mmcv.ops import box_iou_rotated
from mmengine.config import Config
from mmengine.registry import init_default_scope
from mmrotate.evaluation import eval_rbbox_map
from mmrotate.registry import DATASETS
from mmrotate.structures.bbox import QuadriBoxes

ROOT=Path(__file__).resolve().parents[2]
RAW=ROOT/'outputs/persistent_artifacts/orientbench_r019/prelabel/raw'
MAP=ROOT/'outputs/persistent_artifacts/orientbench_r019/prelabel/tile_to_mother.csv'
DOTA=Path('/home/rspip/cqc/data/dataset/dota/split_ss_dota10_dota15/val')
DELTA=ROOT/'top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json'
CFG=ROOT/'outputs/persistent_artifacts/orientbench_r019/prelabel/image_only_registry.json'
EXPECTED={'orcnn':(.7061,.4517),'rtmdet':(.7161,.4868)}
# Exact DIOR A/B/C r014 score reconstruction (the user-authorized external probe).
BETA=np.array([-.23342829,.00830977,.02817757,.00753967],float)
UNITS=('orcnn','rtmdet'); COHORTS=('MAIN','NORMALIZED_ALL_AR'); PROBES=('raw_confidence','linear_source_frozen'); ENDPOINTS=('AUGRC','Risk@70')

def h(p):
 x=hashlib.sha256();
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):x.update(b)
 return x.hexdigest()
def angle(w,h,t): return (math.degrees(float(t))+(90 if h>w else 0))%180
def ad(a,b):
 z=abs((a-b)%180);return min(z,180-z)
def delta():
 d=json.loads(DELTA.read_text());q=sorted((float(a),float(b))for a,b in zip(d['ar'],d['dtheta_075'])if b is not None);x=np.array([a for a,_ in q]);y=np.array([b for _,b in q]);c=min(a*b for a,b in q if a>=max(8,x[-1]/2))
 def f(a):
  a=np.asarray(a,float);z=np.interp(a,x,y);z[a<x[0]]=np.inf;m=a>x[-1];z[m]=np.maximum(0,c/a[m]-2*float(d['solve_tolerance_deg']));return z
 return f
def gt():
 # The migrated host retains mother-scene annfiles but not the 5297 tile
 # annfiles.  The persisted object below is the direct DOTA-val tile GT
 # conversion from the prelabel stage, not a prior match/risk/statistic.
 cached=ROOT/'outputs/persistent_artifacts/orientbench_r019/postlabel/dota_gt_fresh.pkl'
 if cached.is_file():
  with cached.open('rb') as f: return pickle.load(f)
 init_default_scope('mmrotate'); reg=json.loads(CFG.read_text()); cf=Config.fromfile(reg['units']['orcnn']['config']); sp=cf.val_dataloader.dataset;sp['data_root']=str(DOTA)+'/';sp['ann_file']='annfiles/';sp['data_prefix']={'img_path':'images/'};sp['img_suffix']='png'; ds=DATASETS.build(sp);ds.full_init();out={}
 for inf in ds.data_list:
  ins=inf.get('instances',[]);poly=[x['bbox'] for x in ins]; rb=QuadriBoxes(torch.tensor(poly,dtype=torch.float32)).convert_to('rbox').tensor.numpy() if poly else np.empty((0,5),np.float32);out[str(inf['img_id'])]={'b':rb.astype(np.float32),'l':np.array([x['bbox_label']for x in ins],np.int64),'i':np.array([x.get('ignore_flag',0)for x in ins],np.int64)}
 if len(out)!=5297:raise RuntimeError(f'GT tiles {len(out)}')
 return out
def load(u):
 with (RAW/u/'identity.pkl').open('rb')as f:r=pickle.load(f)
 return sorted(r,key=lambda z:str(z['img_id']))
def ap(rs,g):
 de=[];an=[]
 for r in rs:
  p=r['pred_instances'];b=p['bboxes'].detach().cpu().numpy().astype(np.float32);s=p['scores'].detach().cpu().numpy().astype(np.float32);l=p['labels'].detach().cpu().numpy();de.append([np.c_[b[l==c],s[l==c]]for c in range(15)]);z=g[str(r['img_id'])];zzb=z['b'] if 'b'in z else z['boxes'];zzl=z['l'] if 'l'in z else z['labels'];zzi=z['i'] if 'i'in z else z['ignored'];k=zzi==0;an.append({'bboxes':zzb[k],'labels':zzl[k],'bboxes_ignore':zzb[~k],'labels_ignore':zzl[~k]})
 return float(eval_rbbox_map(de,an,iou_thr=.5,use_07_metric=True,nproc=38,logger='silent')[0]),float(eval_rbbox_map(de,an,iou_thr=.75,use_07_metric=True,nproc=38,logger='silent')[0])
def match(u,rs,g,m,dth):
 rows=[]
 for r in rs:
  im=str(r['img_id']);p=r['pred_instances'];pb=p['bboxes'].detach().cpu().float();ps=p['scores'].detach().cpu().numpy();pl=p['labels'].detach().cpu().numpy();z=g[im];zzb=z['b'] if 'b'in z else z['boxes'];zzl=z['l'] if 'l'in z else z['labels'];zzi=z['i'] if 'i'in z else z['ignored'];k=zzi==0;gb=torch.from_numpy(zzb[k]).float();gl=zzl[k]
  if not len(pb)or not len(gb):continue
  ov=box_iou_rotated(pb,gb).cpu().numpy();used=set()
  for pi in sorted(range(len(pb)),key=lambda j:(-float(ps[j]),j)):
   can=[(float(ov[pi,j]),j)for j in range(len(gb))if j not in used and pl[pi]==gl[j]and ov[pi,j]>=.5]
   if not can:continue
   io,gi=min(can,key=lambda x:(-x[0],x[1]));used.add(gi);pw,ph,pt=float(pb[pi,2]),float(pb[pi,3]),float(pb[pi,4]);gw,gh,gt=float(gb[gi,2]),float(gb[gi,3]),float(gb[gi,4]);ar=max(gw,gh)/max(min(gw,gh),1e-6);e=ad(angle(pw,ph,pt),angle(gw,gh,gt));risk=min(e/max(float(dth(np.array([ar]))[0]),1),3)/3;sc=float(ps[pi]);logit=float(np.clip(math.log(max(sc,1e-6)/max(1-sc,1e-6)),-13.815511,13.815511));pa=max(pw,ph)/max(min(pw,ph),1e-6);lpa=float(np.clip(math.log(max(pa,1+1e-6)),0,4.605170));hla=float(np.clip(.5*math.log(max(pw*ph,1e-6)),-6.907755,9.210340));lin=float(BETA@[1,logit,lpa,hla]);rows.append((im,m[im],pi,gi,pl[pi],io,ar,e,risk,sc,lin))
 return pd.DataFrame(rows,columns=['image_id','mother','pred_id','gt_id','class_id','iou','ar','angle_error','risk','raw_confidence','linear_source_frozen'])
def met(s,r,w=None):
 o=np.argsort(-s,kind='stable');s=s[o];r=r[o];w=np.ones(len(o))if w is None else w[o];n=w.sum();st=np.r_[0,np.flatnonzero(s[1:]!=s[:-1])+1];cw=np.add.reduceat(w,st);cr=np.add.reduceat(w*r,st);k=cw>0;cw,cr=cw[k],cr[k];cc=np.cumsum(cw);rr=np.cumsum(cr);a=float(np.sum((np.r_[0,rr[:-1]/n]+rr/n)*cw/n/2));j=int(np.searchsorted(cc,.7*n));return a,float(rr[j]/cc[j])
def accepted(s,q):
 o=np.argsort(-s,kind='stable');z=s[o];st=np.r_[0,np.flatnonzero(z[1:]!=z[:-1])+1];j=int(np.searchsorted(np.cumsum(np.diff(np.r_[st,len(s)])),q*len(s)));return s>=z[st[j]]
def worker(x):
 rep,draw=x;c=np.bincount(draw,minlength=len(MOTHERS));out=[]
 for u in UNITS:
  for co in COHORTS:
   f=FRAMES[u];a=f.ar.to_numpy()>=2.1 if co=='MAIN' else np.ones(len(f),bool);z=f.loc[a];w=c[np.array([POS[v]for v in z.mother])]
   for p in PROBES:out.extend(met(z[p].to_numpy(),z.risk.to_numpy(),w))
 return rep,np.array(out)
def main():
 apx=argparse.ArgumentParser();apx.add_argument('--output',type=Path,required=True);a=apx.parse_args();a.output.mkdir(parents=True);start=time.time();g=gt();m=pd.read_csv(MAP);mother=dict(zip(m.stem,m.mother));global MOTHERS,POS,FRAMES;MOTHERS=sorted(set(mother.values()));POS={x:i for i,x in enumerate(MOTHERS)};dth=delta();FRAMES={};par=[]
 for u in UNITS:
  r=load(u);p50,p75=ap(r,g);ok=abs(p50-EXPECTED[u][0])<=.002 and abs(p75-EXPECTED[u][1])<=.002;par.append({'unit':u,'ap50':p50,'ap75':p75,'expected_ap50':EXPECTED[u][0],'expected_ap75':EXPECTED[u][1],'pass':ok});
  if not ok:raise RuntimeError('AP parity '+u)
  FRAMES[u]=match(u,r,g,mother,dth);FRAMES[u].to_parquet(a.output/f'matched_{u}.parquet',index=False)
 pd.DataFrame(par).to_csv(a.output/'official_ap_parity.csv',index=False);rng=np.random.RandomState(20260813);draws=[rng.randint(0,len(MOTHERS),len(MOTHERS))for _ in range(10000)];point=[]
 for u in UNITS:
  for co in COHORTS:
   f=FRAMES[u];z=f[f.ar>=2.1]if co=='MAIN'else f
   for p in PROBES:point.append({'unit':u,'cohort':co,'probe':p,'AUGRC':met(z[p].to_numpy(),z.risk.to_numpy())[0],'Risk@70':met(z[p].to_numpy(),z.risk.to_numpy())[1],'rows':len(z)})
 with mp.get_context('fork').Pool(39)as pool:
  boot=np.empty((10000,16));
  for i,v in pool.imap_unordered(worker,enumerate(draws),chunksize=1):boot[i]=v
 np.save(a.output/'bootstrap.npy',boot);pd.DataFrame(point).to_csv(a.output/'point_metrics.csv',index=False);json.dump({'status':'COMPLETE','elapsed_seconds':time.time()-start,'mothers':len(MOTHERS),'tiles':len(mother),'dior_frozen_beta':BETA.tolist()},open(a.output/'run.json','w'),indent=2)
if __name__=='__main__':main()
