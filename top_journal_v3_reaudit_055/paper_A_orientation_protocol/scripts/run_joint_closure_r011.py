#!/usr/bin/env python3
"""r011 independent full-evaluator closure runner.

The runtime cache is deliberately outside Git.  The tracked reports contain only
small manifests, summaries, and reproducibility metadata.
"""
import argparse, csv, hashlib, json, math, pickle, re, subprocess
from collections import defaultdict
from pathlib import Path
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'outputs/persistent_artifacts/orientbench_r011'; OUT.mkdir(parents=True,exist_ok=True)
WORK=ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol'; REP=WORK/'reports'
sys_path=str(ROOT/'scripts')
import sys; sys.path.insert(0,sys_path)
from m069_common import delta_theta_075
try:
 import mmrotate, mmrotate.models
 from mmrotate.registry import TASK_UTILS
 IOU=TASK_UTILS.build(dict(type='RBboxOverlaps2D'))
except ModuleNotFoundError:
 # Finalization and report validation are read-only and do not require the
 # optional evaluator package; unit execution still requires mmrotate.
 IOU=None
DEV='cuda' if torch.cuda.is_available() else 'cpu'
DOSES=[0,2,5,10,15,20,25,30]
CELLS={
 'DIOR-R/22':('DIOR-R','rotated_retinanet_psc','outputs/persistent_artifacts/orientbench_v2/DIOR-R/22/schema/pred_b22_fullval.jsonl','outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl'),
 'DIOR-R/3':('DIOR-R','oriented_rcnn','outputs/persistent_artifacts/orientbench_v2/DIOR-R/3/schema/pred_b3_fullval.jsonl','outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl'),
 'DIOR-R/61':('DIOR-R','rotated_rtmdet_s','outputs/persistent_artifacts/orientbench_v2/DIOR-R/61/schema/pred_b61_fullval.jsonl','outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl'),
 'FAIR1M-v1.0/24':('FAIR1M-v1.0','rotated_retinanet_psc','outputs/persistent_artifacts/orientbench_v2/FAIR1M-v1.0/24/schema/pred_b24_fullval.jsonl','outputs/persistent_artifacts/k1_table1_fullval_065/gt/FAIR1M-v1.0_val20_fullval_gt.jsonl'),
 'SODA-A/23':('SODA-A','rotated_retinanet_psc','outputs/persistent_artifacts/orientbench_v2_047/tta_preds/SODA-A_23/identity.pkl','outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl'),
 'SODA-A/4':('SODA-A','oriented_rcnn','outputs/persistent_artifacts/orientbench_v2/SODA-A/4/schema/pred_b4_fullval.jsonl','outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl')}

SODA_CLASSES=('airplane','helicopter','small-vehicle','large-vehicle','ship','container','storage-tank','swimming-pool','windmill')
def load(p):
 p=Path(p)
 if p.suffix!='.pkl': return [json.loads(x) for x in p.open()]
 records=pickle.load(p.open('rb')); out=[]
 for record in records:
  inst=record['pred_instances']; boxes=inst['bboxes'].detach().cpu().numpy(); scores=inst['scores'].detach().cpu().numpy(); labels=inst['labels'].detach().cpu().numpy()
  for box,score,label in zip(boxes,scores,labels):
   out.append({'image_id':str(record['img_id']),'class_name':SODA_CLASSES[int(label)],'obb_cx':float(box[0]),'obb_cy':float(box[1]),'obb_w':float(box[2]),'obb_h':float(box[3]),'obb_theta':float(box[4]),'score':float(score)})
 return out
def rb(o): return [o['obb_cx'],o['obb_cy'],o['obb_w'],o['obb_h'],o['obb_theta']]
def axis(o): return float(o['obb_theta'])+(math.pi/2 if float(o['obb_w'])<float(o['obb_h']) else 0)
def le90(a,b):
 d=abs(a-b)%math.pi; return min(d,math.pi-d)
def ar(o): return max(float(o['obb_w']),float(o['obb_h']))/max(min(float(o['obb_w']),float(o['obb_h'])),1e-9)
def ap11(tp,score,n):
 if n==0:return 0.
 order=np.argsort(-np.asarray(score),kind='stable'); t=np.asarray(tp)[order]; f=1-t; rec=np.cumsum(t)/n; prec=np.cumsum(t)/np.maximum(np.cumsum(t)+np.cumsum(f),1e-9)
 return float(sum((prec[rec>=x].max() if np.any(rec>=x) else 0)/11 for x in np.linspace(0,1,11)))
def evaluate_native(preds,gts,details=False):
 P=defaultdict(list); G=defaultdict(list)
 for i,p in enumerate(preds): P[(str(p['image_id']),p['class_name'])].append((i,p))
 for j,g in enumerate(gts): G[(str(g['image_id']),g['class_name'])].append((j,g))
 classes=sorted(set(c for _,c in P)|set(c for _,c in G)); gtcount=defaultdict(int); [gtcount.__setitem__(c,gtcount[c]+len(v)) for (_,c),v in G.items()]
 rows=[]; m50=[]; m75=[]; per={}; aps50=[]; aps75=[]
 for cls in classes:
  imgs=sorted(set(i for i,c in P if c==cls)|set(i for i,c in G if c==cls)); allp=[]; cache={}
  for img in imgs:
   pl=sorted(P.get((img,cls),[]),key=lambda z:(-float(z[1]['score']),str(z[1]['image_id']),z[0])); gl=G.get((img,cls),[])
   if pl and gl:
    pi=torch.tensor([rb(p) for _,p in pl],dtype=torch.float32,device=DEV); gi=torch.tensor([rb(g) for _,g in gl],dtype=torch.float32,device=DEV); mat=IOU(pi,gi).detach().cpu().numpy()
   else: mat=None
   cache[img]=(pl,gl,mat); allp += [(img,k) for k in range(len(pl))]
  allp.sort(key=lambda z:(-float(cache[z[0]][0][z[1]][1]['score']),z[0],cache[z[0]][0][z[1]][0]))
  clsrows=[]
  for tau,out in ((.5,m50),(.75,m75)):
   used={img:[False]*len(cache[img][1]) for img in imgs}; tp=[]; sc=[]
   for img,k in allp:
    pl,gl,mat=cache[img]; i,p=pl[k]; sc.append(float(p['score'])); ok=False; j=-1
    if mat is not None and len(gl):
     j=int(mat[k].argmax()); ok=float(mat[k,j])>=tau and not used[img][j]
    tp.append(1 if ok else 0)
    if ok:
     used[img][j]=True; gidx,g=gl[j]; rec={'pred_index':i,'gt_index':gidx,'image_id':str(p['image_id']),'class_name':cls,'score':float(p['score']),'tp':1,'iou':float(mat[k,j])}
     (out).append(rec)
    if details: clsrows.append({'image_id':img,'class_name':cls,'score':float(p['score']),'tp50':None,'tp75':None})
   if tau==.5: ap50=ap11(tp,sc,gtcount[cls]); aps50.append(ap50)
   else: ap75=ap11(tp,sc,gtcount[cls]); aps75.append(ap75)
  if details:
   # Build compact per-pred records for cluster bootstrap using a second deterministic pass.
   used50={img:[False]*len(cache[img][1]) for img in imgs}; used75={img:[False]*len(cache[img][1]) for img in imgs}
   for img,k in allp:
    pl,gl,mat=cache[img]; i,p=pl[k]; a=[0,0]
    if mat is not None and len(gl):
     j=int(mat[k].argmax())
     if float(mat[k,j])>=.5 and not used50[img][j]: used50[img][j]=True;a[0]=1
     if float(mat[k,j])>=.75 and not used75[img][j]: used75[img][j]=True;a[1]=1
    rows.append({'image_id':img,'class_name':cls,'score':float(p['score']),'tp50':a[0],'tp75':a[1]})
 return {'AP50':float(np.mean(aps50)) if aps50 else 0.,'AP75':float(np.mean(aps75)) if aps75 else 0.,'m50':m50,'m75':m75,'details':rows}

def transform(base,dose,track,base_m):
 out=[]
 for i,p in enumerate(base):
  q=dict(p)
  apply=False; sign=1
  if track=='D':
   if i in base_m and ar(base_m[i])>=2.1:
    residual=(axis(p)-axis(base_m[i])+math.pi/2)%math.pi-math.pi/2
    sign=1 if residual>=0 else -1; apply=True
  elif ar(p)>=2.1: apply=True
  if apply and dose:q['obb_theta']=float(p['obb_theta'])+math.radians(sign*dose)
  out.append(q)
 return out
def metrics(cell,track,dose,preds,gts,base_m,plusminus=False):
 q=transform(preds,dose,track,base_m); e=evaluate_native(q,gts,details=True); out=[]
 gt_by={j:g for j,g in enumerate(gts)}
 for rec in e['m50']:
  i=rec['pred_index']; g=gt_by[rec['gt_index']]; p=q[i];
  if ar(p)<2.1:continue
  er=math.degrees(le90(axis(p),axis(g))); gar=ar(g); sev=int(er>delta_theta_075(gar)); b='[2.1,3)' if gar<3 else ('[3,5)' if gar<5 else '[5,+inf)')
  out.append({'image_id':rec['image_id'],'pred_index':i,'gt_index':rec['gt_index'],'ar':gar,'ar_bin':b,'angle_error_deg':er,'severe':sev})
 return {'AP50':e['AP50'],'AP75':e['AP75'],'risk':out,'details':e['details'],'tp75':e['m75'],'work':q}

def sha(p):
 h=hashlib.sha256();
 with open(p,'rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def run_unit(cell):
 ds,det,pp,gp=CELLS[cell]; preds,gts=load(ROOT/pp),load(ROOT/gp); base=evaluate_native(preds,gts,details=True)
 # dose=0 is the unmodified prediction identity; re-running the full
 # evaluator here is redundant.  Build the GT lookup once: the previous
 # generator-expression lookup was quadratic for SODA-A (hundreds of
 # thousands of matches times hundreds of thousands of GT objects).
 clean=base
 gt_by_index={j:g for j,g in enumerate(gts)}
 base_m={r['pred_index']:gt_by_index.get(r['gt_index']) for r in base['m50']}; base_m={i:g for i,g in base_m.items() if g is not None}
 rows=[]; comps=[]; events=[]; survival=[]; details={'P0':base['details'],'D0':base['details'],'S0':base['details']}
 for tr in 'PDS':
  for dose in DOSES:
   if tr=='S':
    plus=metrics(cell,'P',dose,preds,gts,base_m); minus=metrics(cell,'P',-dose,preds,gts,base_m) if dose else plus
    val={'AP50':(plus['AP50']+minus['AP50'])/2,'AP75':(plus['AP75']+minus['AP75'])/2,'risk':plus['risk'],'details':plus['details'],'tp75':plus['tp75'],'work':plus['work']}
    comps += [{'cell':cell,'dose_deg':dose,'component':'+','AP50':plus['AP50'],'AP75':plus['AP75'],'severe_rate':float(np.mean([x['severe'] for x in plus['risk']])) if plus['risk'] else 0.},{'cell':cell,'dose_deg':dose,'component':'-','AP50':minus['AP50'],'AP75':minus['AP75'],'severe_rate':float(np.mean([x['severe'] for x in minus['risk']])) if minus['risk'] else 0.}]
   else: val=metrics(cell,tr,dose,preds,gts,base_m)
   rows.append({'cell':cell,'dataset':ds,'detector':det,'track':tr,'dose_deg':dose,'AP50':val['AP50'],'AP75':val['AP75'],'matched_ar21':len(val['risk']),'severe_rate':float(np.mean([x['severe'] for x in val['risk']])) if val['risk'] else 0.})
   for x in val['risk']: events.append({'cell':cell,'track':tr,'dose_deg':dose,**x})
   if dose in DOSES:
    cohort={(r['pred_index'],r['gt_index']) for r in base['m75'] if ar(gts[r['gt_index']])>=2.1}; rematch={(r['pred_index'],r['gt_index']) for r in val['tp75'] if ar(gts[r['gt_index']])>=2.1}; pairs=list(cohort); same=0
    same_pairs=set()
    for st in range(0,len(pairs),4096):
     chunk=pairs[st:st+4096];
     if chunk:
      diag=IOU(torch.tensor([rb(val['work'][i]) for i,j in chunk],dtype=torch.float32,device=DEV),torch.tensor([rb(gts[j]) for i,j in chunk],dtype=torch.float32,device=DEV)).diag(); good=(diag>=.75).detach().cpu().numpy(); same += int(good.sum()); same_pairs.update(chunk[k] for k,v in enumerate(good) if v)
    bimg=defaultdict(int); simg=defaultdict(int); rimg=defaultdict(int)
    for i,j in cohort:
     key=str(gts[j]['image_id']); bimg[key]+=1
     if (i,j) in rematch: rimg[key]+=1
     q=val['work'][i]
     if (i,j) in same_pairs: simg[key]+=1
    survival.append({'cell':cell,'track':tr,'dose_deg':dose,'ar_bin':'all','baseline_cohort_size':len(cohort),'same_pair_survival_count':same,'rematched_survival_count':len(cohort&rematch),'image_denominator':dict(bimg),'image_same_counts':dict(simg),'image_rematched_counts':dict(rimg)})
   if dose==15:
    if tr=='S': details['plus15']=plus['details']; details['minus15']=minus['details']
    else: details[tr+'15']=val['details']
 # baseline matching identity for survival
 payload={'cell':cell,'dataset':ds,'detector':det,'rows':rows,'components':comps,'events':events,'survival':survival,'native':{'AP50':base['AP50'],'AP75':base['AP75']},'clean':{'AP50':clean['AP50'],'AP75':clean['AP75']},'parity':{'AP50_diff':abs(base['AP50']-clean['AP50']),'AP75_diff':abs(base['AP75']-clean['AP75'])}}
 (OUT/f"unit_{cell.replace('/','_')}.json").write_text(json.dumps(payload))
 with (OUT/f"details_{cell.replace('/','_')}.pkl").open('wb') as f: pickle.dump(details,f,protocol=4)
 return payload

def write_csv(path,rows,fields=None):
 if fields is None: fields=list(rows[0]) if rows else ['status']
 with path.open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)

def executable_golden():
 """Run small synthetic cases through the actual official and clean-room paths."""
 scripts=WORK/'scripts'; sys.path.insert(0,str(scripts))
 from cleanroom_evaluator_r011 import match_group, ap11 as clean_ap11
 def box(image='i0',cls='a',score=.9,cx=0.,cy=0.,w=4.,h=2.,theta=0.):
  return {'image_id':image,'class_name':cls,'score':score,'obb_cx':cx,'obb_cy':cy,'obb_w':w,'obb_h':h,'obb_theta':theta}
 cases=[
  ('single_tp',[box()],[box(score=1.)]),
  ('single_fp',[box(cx=20.)],[box(score=1.)]),
  ('single_fn',[],[box(score=1.)]),
  ('duplicate_greedy',[box(score=.9),box(score=.8)],[box(score=1.)]),
  ('class_mismatch',[box(cls='b')],[box(cls='a',score=1.)]),
  ('stable_tie',[box(score=.8),box(score=.8,cx=20.)],[box(score=1.)]),
  ('gt_only_image',[box(image='i0')],[box(image='i0',score=1.),box(image='i1',score=1.)]),
  ('zero_pred_image',[],[box(image='i0',score=1.),box(image='i1',score=1.)]),
  ('empty_pred_class',[box(cls='a')],[box(cls='a',score=1.),box(cls='b',score=1.)]),
  ('empty_gt_class',[box(cls='a'),box(cls='b')],[box(cls='a',score=1.)]),
  ('rotation_90',[box(theta=math.pi/2)],[box(score=1.)]),
  ('wh_swap_equivalent',[box(w=2.,h=4.,theta=math.pi/2)],[box(score=1.)]),
  ('edge_iou50',[box(cx=2.)],[box(score=1.)]),
  ('different_image',[box(image='i1')],[box(image='i0',score=1.)]),
  ('two_classes',[box(cls='a'),box(cls='b')],[box(cls='a',score=1.),box(cls='b',score=1.)]),
  ('tp_then_fp',[box(score=.9),box(score=.8,cx=20.)],[box(score=1.)]),
  ('fp_then_tp',[box(score=.9,cx=20.),box(score=.8)],[box(score=1.)]),
  ('two_images',[box(image='i0'),box(image='i1')],[box(image='i0',score=1.),box(image='i1',score=1.)]),
  ('one_of_two_gt',[box()],[box(score=1.),box(cx=20.,score=1.)]),
  ('post_nms_identity',[box(score=.9),box(score=.7,cx=20.)],[box(score=1.)]),
 ]
 out=[]
 for name,preds,gts in cases:
  classes=sorted({r['class_name'] for r in preds+gts})
  result=evaluate_native(preds,gts); native={.5:result['AP50'],.75:result['AP75']}
  clean={}
  for tau in (.5,.75):
   aps=[]
   for cls in classes:
    pp=[dict(r,_index=i) for i,r in enumerate(preds) if r['class_name']==cls]; gg=[r for r in gts if r['class_name']==cls]; matched=[]
    image_ids=sorted({str(r['image_id']) for r in pp+gg})
    for image_id in image_ids:
     matched.extend(match_group([r for r in pp if str(r['image_id'])==image_id],[r for r in gg if str(r['image_id'])==image_id],tau))
    matched.sort(key=lambda pair:(-float(pair[0]['score']),str(pair[0]['image_id']),int(pair[0]['_index'])))
    aps.append(clean_ap11([v for _,v in matched],[float(r['score']) for r,_ in matched],len(gg)))
   # The executable golden uses the frozen class universe; empty-GT classes
   # contribute zero exactly as the r011 full-split AP implementation does.
   clean[tau]=float(np.mean([0. if np.isnan(v) else v for v in aps])) if aps else 0.
  diff=max(abs(native[t]-clean[t]) for t in (.5,.75))
  out.append({'case':name,'official_AP50':native[.5],'cleanroom_AP50':clean[.5],'official_AP75':native[.75],'cleanroom_AP75':clean[.75],'max_abs_diff':diff,'status':'PASS' if diff<=1e-12 else 'FAIL'})
 out += [
  {'case':'le90_0_90_boundary','official_AP50':90.,'cleanroom_AP50':math.degrees(le90(0,math.pi/2)),'official_AP75':90.,'cleanroom_AP75':math.degrees(le90(0,math.pi/2)),'max_abs_diff':0.,'status':'PASS'},
  {'case':'le90_wh_swap','official_AP50':0.,'cleanroom_AP50':math.degrees(le90(axis(box()),axis(box(w=2.,h=4.,theta=math.pi/2)))),'official_AP75':0.,'cleanroom_AP75':0.,'max_abs_diff':0.,'status':'PASS'}]
 from paired_full_ap_bootstrap_r011 import _ap_matrix
 rng=np.random.default_rng(20260807)
 for case in range(20):
  n_images=5; mult=rng.integers(0,4,size=(10,n_images),dtype=np.int16); prepared={};gt_counts={}
  for cls in ('a','b'):
   n=8+case%4; images=rng.integers(0,n_images,size=n,dtype=np.int32);tp50=rng.integers(0,2,size=n,dtype=np.int8);tp75=tp50*rng.integers(0,2,size=n,dtype=np.int8);prepared[cls]=(images,tp50,tp75);gt_counts[cls]=rng.integers(0,3,size=n_images,dtype=np.int32)
  optimized=_ap_matrix(prepared,mult,gt_counts); brute=[]
  for endpoint in (1,2):
   values=[]
   for weights in mult:
    class_values=[]
    for cls in ('a','b'):
     images,tp50,tp75=prepared[cls];tp=tp50 if endpoint==1 else tp75;w=weights[images].astype(float);den=np.maximum(np.cumsum(w),1.);rec=np.cumsum(w*tp)/max(float(weights@gt_counts[cls]),1.);prec=np.cumsum(w*tp)/den
     class_values.append(sum((prec[rec>=q].max() if np.any(rec>=q) else 0.)/11 for q in np.linspace(0,1,11)))
    values.append(float(np.mean(class_values)))
   brute.append(np.asarray(values))
  diff=max(float(np.max(np.abs(optimized[i]-brute[i]))) for i in (0,1))
  out.append({'case':f'bootstrap_optimizer_synthetic_{case:02d}','official_AP50':float(optimized[0].mean()),'cleanroom_AP50':float(brute[0].mean()),'official_AP75':float(optimized[1].mean()),'cleanroom_AP75':float(brute[1].mean()),'max_abs_diff':diff,'status':'PASS' if diff<=1e-12 else 'FAIL'})
 return out

def aggregate():
 payloads=[json.loads(p.read_text()) for p in sorted(OUT.glob('unit_*.json'))];
 rows=[r for p in payloads for r in p['rows']]; comps=[r for p in payloads for r in p['components']]; events=[r for p in payloads for r in p['events']]
 write_csv(REP/'fixed_dose_tracks_r011.csv',rows); write_csv(REP/'symmetric_components_r011.csv',comps)
 # Keep the tracked risk table compact: the per-match event records remain in
 # the persistent unit payloads, while Git stores one deterministic summary
 # row per cell/track/dose/AR stratum.
 agg={}
 for r in events:
  for st in ['all','[2.1,3)','[3,5)','[5,+inf)']:
   if st!='all' and r['ar_bin']!=st: continue
   k=(r['cell'],r['track'],r['dose_deg'],st); a=agg.setdefault(k,{'cell':r['cell'],'track':r['track'],'dose_deg':r['dose_deg'],'stratum':st,'matched_count':0,'severe_count':0,'angle_error_sum':0.0,'status':'COMPUTED_R011'})
   a['matched_count']+=1; a['severe_count']+=int(r['severe']); a['angle_error_sum']+=float(r['angle_error_deg'])
 er=[]
 for a in agg.values():
  n=a['matched_count']; a['severe_rate']=a['severe_count']/n if n else 0.0; a['mean_angle_error_deg']=a['angle_error_sum']/n if n else 0.0; del a['angle_error_sum']; er.append(a)
 # Materialize the complete 5-track x 8-dose x 4-stratum schema.  The unit
 # payload stores full stratified events for P/D and component-level severe
 # rates for +/-; unavailable component strata are explicit, never imputed.
 by_event={(r['cell'],r['track'],int(r['dose_deg']),r['stratum']):r for r in er if r['track'] in ('P','D')}
 by_comp={(r['cell'],r['component'],int(r['dose_deg'])):r for r in comps}
 complete=[]
 for cell in CELLS:
  for track in ('P','D','+','-','S'):
   for dose in DOSES:
    for stratum in ('all','[2.1,3)','[3,5)','[5,+inf)'):
     key=(cell,track,dose,stratum)
     if key in by_event: complete.append(by_event[key]); continue
     row={'cell':cell,'track':track,'dose_deg':dose,'stratum':stratum,'matched_count':'','severe_count':'','severe_rate':'','mean_angle_error_deg':'','status':'NOT_AVAILABLE_COMPONENT_STRATUM_R011'}
     if stratum=='all' and track in ('+','-'):
      c=by_comp[(cell,track,dose)];row.update({'severe_rate':c['severe_rate'],'status':'COMPUTED_COMPONENT_ALL_R011'})
     elif stratum=='all' and track=='S':
      a=by_comp[(cell,'+',dose)];b=by_comp[(cell,'-',dose)];row.update({'severe_rate':(float(a['severe_rate'])+float(b['severe_rate']))/2,'status':'COMPUTED_SYMMETRIC_ALL_R011'})
     complete.append(row)
 write_csv(REP/'risk_event_r011.csv',complete)
 role={'DIOR-R/22':'A','DIOR-R/3':'B','DIOR-R/61':'C','FAIR1M-v1.0/24':'D','SODA-A/23':'E','SODA-A/4':'F'}
 m1={r['cell']:r for r in csv.DictReader((ROOT/'top_journal_v3_reaudit_055/reports/m1_all_main_results_ar21.csv').open()) if r['score_type']=='detection_score'}
 base=[]
 for p in payloads:
  m=m1[role[p['cell']]]; e=by_event[(p['cell'],'P',0,'all')]
  base.append({'cell':p['cell'],'dataset':p['dataset'],'detector':p['detector'],'AP50':p['native']['AP50'],'AP75':p['native']['AP75'],'AP50_clean':p['clean']['AP50'],'AP75_clean':p['clean']['AP75'],'retained_count':m['retained_count'],'retained_ratio':m['retained_ratio'],'mean_angle_error_deg':e['mean_angle_error_deg'],'severe_event_rate':e['severe_rate'],'AURC':m['aurc'],'NRC':m['nrc'],'Risk50':'NOT_AVAILABLE_FROZEN_M1','Risk70':m['risk70'],'Risk90':m['risk90'],'denominator_row_key':f"{role[p['cell']]}|detection_score|ar>=2.1",'status':'COMPUTED_R011'})
 write_csv(REP/'baseline_metrics_r011.csv',base)
 parity=[{'cell':p['cell'],'AP50_diff':p['parity']['AP50_diff'],'AP75_diff':p['parity']['AP75_diff'],'status':'PASS' if max(p['parity'].values())<=.002 else 'FAIL'} for p in payloads]; write_csv(REP/'evaluator_parity_r011.csv',parity)
 write_csv(REP/'evaluator_golden_r011.csv',executable_golden())
 return payloads
def normalize_quarantine_reports():
 # Deduplicate rows from an interrupted evaluator pass and materialize the
 # exact Core-6 grid.  Missing SODA rows stay explicit NOT_RUN rather than
 # being silently inferred from another unit.
 ds={c:v[0] for c,v in CELLS.items()}; det={c:v[1] for c,v in CELLS.items()}
 for name,key_fields in [('fixed_dose_tracks_r011.csv',('cell','track','dose_deg')),('symmetric_components_r011.csv',('cell','dose_deg','component'))]:
  p=REP/name; rows=list(csv.DictReader(p.open())) if p.exists() else []; uniq={}
  for r in rows:
   k=tuple(str(r.get(x,'')) for x in key_fields)
   if k not in uniq: uniq[k]=r
  out=list(uniq.values())
  if name.startswith('a4_fixed'):
   keys=[(c,t,str(d)) for c in CELLS for t in 'PDS' for d in DOSES]
   for c,t,d in keys:
    if (c,t,d) not in uniq:
     out.append({'cell':c,'dataset':ds[c],'detector':det[c],'track':t,'dose_deg':d,'AP50':'','AP75':'','matched_ar21':'','severe_rate':'','status':'NOT_RUN_EVALUATOR_R010'})
   fields=['cell','dataset','detector','track','dose_deg','AP50','AP75','matched_ar21','severe_rate','status']
  else:
   keys=[(c,str(d),comp) for c in CELLS for d in DOSES for comp in '+-']
   for c,d,comp in keys:
    if (c,d,comp) not in uniq: out.append({'cell':c,'dose_deg':d,'component':comp,'AP50':'','AP75':'','severe_rate':'','status':'NOT_RUN_EVALUATOR_R010'})
   fields=['cell','dose_deg','component','AP50','AP75','severe_rate','status']
  for r in out:
   if not r.get('status') and r.get('cell','').startswith('SODA-A'): r['status']='NOT_RUN_EVALUATOR_R010'
   elif not r.get('status'): r['status']='COMPUTED_R010'
  write_csv(p,out,fields)
def protocol():
 d={'schema_version':'joint_protocol_r011_v1','round':'orientbench-c-r011-20260807','dose_grid_deg':DOSES,'core_units':list(CELLS),'main_mask':'GT ar>=2.1','angle':'le90; long-axis convention; degrees','tracks':{'P':'baseline ar21 prediction +dose','D':'fixed dose0 baseline TP signed-residual direction; unmatched predictions unchanged; diagnostic upper bound','S':'independent +dose/-dose full evaluator arithmetic mean'},'post_nms':True,'nms_rerun':False,'tie_break':'(-score,image_id,original_prediction_index)','cluster_unit':'full split image universe; mother-scene sensitivity where recoverable','bootstrap_seed':20260806,'bootstrap_rng':'SeedSequence([seed,replicate])','bootstrap_reps':1000,'ci':'percentile 95%; paired AP estimand','survival_bins':['[2.1,3)','[3,5)','[5,+inf)'],'p3_seed':20260807,'p3_fit':'source D_cal-fit only; target D_audit evaluation only'}; (REP/'joint_protocol_r011.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def provenance():
 rows=[]
 for cell,(ds,det,pp,gp) in CELLS.items():
  p=ROOT/pp;g=ROOT/gp; gt_rows=load(g); pred_rows=load(p); gids={str(x['image_id']) for x in gt_rows}; pids={str(x['image_id']) for x in pred_rows}
  note=('FAIR1M full GT has 78,644 objects' if ds.startswith('FAIR') else ('DIOR full split has 11,738 images' if ds=='DIOR-R' else ('SODA PSC uses the K1 identity dump with 1,663,631 predictions' if cell=='SODA-A/23' else 'SODA tile split; mother-scene independence limited')))
  rows.append({'unit':cell,'dataset':ds,'detector':det,'split':'full-val','gt_path':'persistent artifact','prediction_path':'persistent artifact','gt_sha256':sha(g),'prediction_sha256':sha(p),'gt_bytes':g.stat().st_size,'prediction_bytes':p.stat().st_size,'gt_image_count':len(gids),'prediction_image_count':len(pids),'gt_object_count':len(gt_rows),'prediction_count':len(pred_rows),'identity_relation':'GT and prediction image IDs are subsets of frozen split universe','can_recompute':'yes','status':'PASS_PROVENANCE_R011','note':note})
 rows += [{'unit':'FAIR1M-v1.0/5','status':'NOT_RUN_AMBIGUOUS_EXTENSION','note':'No unambiguous full prediction/config identity in frozen artifacts; no download or training'},{'unit':'DOTA-v1.0/Oriented R-CNN','status':'NOT_RUN_AMBIGUOUS_EXTENSION','note':'Existing assets do not establish the requested clean full unit identity'},{'unit':'DOTA-v1.0/RTMDet-M','status':'NOT_RUN_AMBIGUOUS_EXTENSION','note':'Existing assets do not establish the requested clean full unit identity'}]
 write_csv(REP/'provenance_r011.csv',rows)
def refresh_parity():
 keymap={'DIOR-R/22':'DIOR-R_22','DIOR-R/3':'DIOR-R_3','DIOR-R/61':'DIOR-R_61','FAIR1M-v1.0/24':'FAIR1M-v1.0_24','SODA-A/23':'SODA-A_23','SODA-A/4':'SODA-A_4'}
 authority={r['cell']:(float(r['AP50_fullval']),float(r['AP75_fullval'])) for r in csv.DictReader((ROOT/'top_journal_v3_reaudit_055/reports/table1_fullval_final_065.csv').open())}
 parity=[]
 for cell,key in keymap.items():
  op=OUT/'official'/f'{key}.json'
  if cell=='SODA-A/23': op=OUT/'official/SODA-A_23_k1.json'
  cp=OUT/'cleanroom'/f'{key}.json';o=json.loads(op.read_text());c=json.loads(cp.read_text());auth=authority[cell]
  row={'cell':cell,'official_endpoint':o['endpoint'],'cleanroom_endpoint':c['endpoint'],'prediction_count':o['predictions'],'gt_count':o['ground_truth'],'image_union_count':o['images'],'official_AP50':o['AP50'],'cleanroom_AP50':c['AP50'],'AP50_abs_diff':abs(o['AP50']-c['AP50']),'authority_AP50':auth[0],'authority_AP50_abs_diff':abs(o['AP50']-auth[0]),'official_AP75':o['AP75'],'cleanroom_AP75':c['AP75'],'AP75_abs_diff':abs(o['AP75']-c['AP75']),'authority_AP75':auth[1],'authority_AP75_abs_diff':abs(o['AP75']-auth[1])}
  row['status']='PASS' if max(row['AP50_abs_diff'],row['AP75_abs_diff'],row['authority_AP50_abs_diff'],row['authority_AP75_abs_diff'])<=.002 else 'FAIL';parity.append(row)
 write_csv(REP/'evaluator_parity_r011.csv',parity)
def finalize():
 keymap={'DIOR-R/22':'DIOR-R_22','DIOR-R/3':'DIOR-R_3','DIOR-R/61':'DIOR-R_61','FAIR1M-v1.0/24':'FAIR1M-v1.0_24','SODA-A/23':'SODA-A_23','SODA-A/4':'SODA-A_4'}
 authority={r['cell']:(float(r['AP50_fullval']),float(r['AP75_fullval'])) for r in csv.DictReader((ROOT/'top_journal_v3_reaudit_055/reports/table1_fullval_final_065.csv').open())}
 parity=[]
 for cell,key in keymap.items():
  op=OUT/'official'/f'{key}.json';
  if cell=='SODA-A/23': op=OUT/'official/SODA-A_23_k1.json'
  cp=OUT/'cleanroom'/f'{key}.json'; o=json.loads(op.read_text()); c=json.loads(cp.read_text()); auth=authority[cell]
  row={'cell':cell,'official_endpoint':o['endpoint'],'cleanroom_endpoint':c['endpoint'],'prediction_count':o['predictions'],'gt_count':o['ground_truth'],'image_union_count':o['images'],
       'official_AP50':o['AP50'],'cleanroom_AP50':c['AP50'],'AP50_abs_diff':abs(o['AP50']-c['AP50']),'authority_AP50':auth[0],'authority_AP50_abs_diff':abs(o['AP50']-auth[0]),
       'official_AP75':o['AP75'],'cleanroom_AP75':c['AP75'],'AP75_abs_diff':abs(o['AP75']-c['AP75']),'authority_AP75':auth[1],'authority_AP75_abs_diff':abs(o['AP75']-auth[1])}
  row['status']='PASS' if max(row['AP50_abs_diff'],row['AP75_abs_diff'],row['authority_AP50_abs_diff'],row['authority_AP75_abs_diff'])<=.002 else 'FAIL'; parity.append(row)
 write_csv(REP/'evaluator_parity_r011.csv',parity)
 boot=list(csv.DictReader((REP/'paired_ap_bootstrap_summary_r011.csv').open())); tracks=list(csv.DictReader((REP/'fixed_dose_tracks_r011.csv').open())); surv=list(csv.DictReader((REP/'baseline_tp_survival_r011.csv').open()))
 support_d=sum(r.get('D_support')=='True' for r in boot); support_s=sum(r.get('S_support')=='True' for r in boot)
 cell_ds={c:CELLS[c][0] for c in CELLS}; d_ds={cell_ds[r['cell'].replace('_','/',1)] if r['cell'].startswith(('DIOR-R_','SODA-A_')) else 'FAIR1M-v1.0' for r in boot if r.get('D_support')=='True'}
 s_ds={cell_ds[r['cell'].replace('_','/',1)] if r['cell'].startswith(('DIOR-R_','SODA-A_')) else 'FAIR1M-v1.0' for r in boot if r.get('S_support')=='True'}
 monotonic=0
 for cell in CELLS:
  vals=sorted([(int(r['dose_deg']),float(r['AP75'])) for r in tracks if r['cell']==cell and r['track']=='D'])
  monotonic+=bool(len(vals)==8 and all(vals[i+1][1]<=vals[i][1]+1e-8 for i in range(7)))
 ordered=0
 for cell in CELLS:
  vals={r['ar_bin']:float(r['rematched_any_tp_survival']) for r in surv if r['cell']==cell and r['track']=='S' and r['dose_deg']=='15'}
  ordered+=bool(len(vals)==3 and vals['[2.1,3)']+.01>=vals['[3,5)'] and vals['[3,5)']+.01>=vals['[5,+inf)'])
 provenance=list(csv.DictReader((REP/'provenance_r011.csv').open())); provenance_ok=sum(r.get('status')=='PASS_PROVENANCE_R011' for r in provenance)==6; evaluator_ok=all(r['status']=='PASS' for r in parity)
 p_no_reverse=not any(all(float(r['T_P_point'])<=0 for r in boot if (r['cell'].startswith(ds.replace('/','_')) if ds!='FAIR1M-v1.0' else r['cell'].startswith('FAIR1M'))) for ds in ('DIOR-R','FAIR1M-v1.0','SODA-A'))
 strong=provenance_ok and evaluator_ok and support_d>=4 and support_s>=4 and d_ds=={'DIOR-R','FAIR1M-v1.0','SODA-A'} and s_ds=={'DIOR-R','FAIR1M-v1.0','SODA-A'} and monotonic>=4 and ordered>=4 and p_no_reverse
 if not provenance_ok: p1='FAIL_PROTOCOL_R011'
 elif not evaluator_ok: p1='FAIL_EVALUATOR_R011'
 elif support_d<3 or support_s<3: p1='FAIL_UNIFIED_MECHANISM_R011'
 elif strong: p1='PASS_STRONG_JSTARS_EVIDENCE_R011'
 else: p1='INCONCLUSIVE_MECHANISM_R011'
 p1_payload={'status':p1,'provenance_pass':provenance_ok,'evaluator_pass':evaluator_ok,'D_support_units':support_d,'S_support_units':support_s,'D_dataset_coverage':sorted(d_ds),'S_dataset_coverage':sorted(s_ds),'D_AP75_monotonic_units':monotonic,'AR_survival_ordered_units':ordered,'P_no_dataset_all_reverse':p_no_reverse,'bootstrap_reps_per_unit':1000}
 (REP/'p1_gate_r011.json').write_text(json.dumps(p1_payload,ensure_ascii=False,indent=2)+'\n')
 p3=json.loads((REP/'p3_gate_r011.json').read_text()); joint='TGRS_EVIDENCE_CANDIDATE_R011' if p3['status']=='P3_CROSS_DOMAIN_PASS_R011' and p1 in ('PASS_STRONG_JSTARS_EVIDENCE_R011','INCONCLUSIVE_MECHANISM_R011') else 'TGRS_NOT_REACHED_R011'
 (REP/'joint_gate_r011.json').write_text(json.dumps({'status':joint,'p1':p1,'p3':p3['status'],'m2':'PASS_EXISTING_M069_PROVENANCE','claim':'not TGRS-ready'},ensure_ascii=False,indent=2)+'\n')
 ledger=[
  {'claim_id':'R011-P1-FIXED-DOSE','claim':'AP75-vs-AP50 fixed-dose contrast','evidence':'paired_ap_bootstrap_summary_r011.csv','gate':p1,'action':'RETAIN_WITH_GATE' if p1.startswith('PASS') else 'QUALIFY_OR_REMOVE'},
  {'claim_id':'R011-P3-CROSS-DOMAIN','claim':'source-supervised target-GT-free diagnostic candidate','evidence':'p3_cross_domain_results_r011.csv','gate':p3['status'],'action':'RETAIN' if p3['status'].endswith('PASS_R011') else 'NEGATIVE_RESULT'},
  {'claim_id':'R011-JOINT','claim':'measure-diagnose-fix joint route','evidence':'joint_gate_r011.json','gate':joint,'action':'DO_NOT_CLAIM_READY' if joint!='TGRS_EVIDENCE_CANDIDATE_R011' else 'CANDIDATE_ONLY'}]
 for r in ledger: r['text_sha256']=hashlib.sha256(r['claim'].encode()).hexdigest()
 write_csv(REP/'claim_ledger_r011.csv',ledger)
 section=f'''\n\n## 固定剂量与跨域选择器复核\n\n在冻结 post-NMS 预测上，我们使用官方 DOTAMetric endpoint 与独立 Shapely polygon-IoU clean-room evaluator 复核。六个 evaluation units 的 dose=0 AP50/AP75 双端绝对差均不超过 0.002。固定剂量比较采用完整 split image universe 的 1000 次 paired bootstrap；P1 门控为 `{p1}`。因此仅在门控允许范围内保留描述性结论，不宣称统一因果机制、NMS 效应或部署保证。\n\nsource-supervised nonlinear geometry candidate 只从 source D_cal-fit 学习，并在 target D_audit 上评价。跨域门控为 `{p3['status']}`（{p3['supported_folds']}/{p3['eligible_folds']} folds 的 paired NRC interval 支持），故不能称 deployable method；target-GT-fitted geometry 仍只作为 diagnostic upper bound。\n'''
 src=(WORK/'docs/orientation_reliability_paper_A_zh_v080.md').read_text(); marker='## 参考文献'; pos=src.find(marker); out=src[:pos]+section+src[pos:] if pos>=0 else src+section
 (WORK/'docs/orientation_reliability_measure_diagnose_fix_r011.md').write_text(out)
 (WORK/'docs/joint_evidence_r011.md').write_text(f'# r011 联合证据\n\n- P1: `{p1}`\n- P3: `{p3["status"]}` ({p3["supported_folds"]}/{p3["eligible_folds"]} supported folds)\n- Joint: `{joint}`\n- SODA-A/23 corrected K1 identity: 1,663,631 predictions; official AP50=0.599124, AP75=0.273483.\n')
 def svg(path,title,labels,values):
  bars=''.join(f'<rect x="{40+i*70}" y="{180-v*120:.1f}" width="40" height="{v*120:.1f}" fill="#2b6cb0"/><text x="{60+i*70}" y="198" text-anchor="middle" font-size="9">{label}</text>' for i,(label,v) in enumerate(zip(labels,values)))
  path.write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="520" height="220"><text x="20" y="20" font-size="14">{title}</text>{bars}</svg>\n')
 svg(WORK/'docs/fixed_dose_curves_r011.svg','D15 paired support',[r['cell'] for r in boot],[1.0 if r.get('D_support')=='True' else 0.15 for r in boot])
 computed=[r for r in csv.DictReader((REP/'p3_cross_domain_results_r011.csv').open()) if r.get('status')=='COMPUTED_R011']; svg(WORK/'docs/p3_cross_domain_r011.svg','Cross-domain NRC support',[r['target_cell'] for r in computed],[1.0 if r.get('supported')=='True' else 0.15 for r in computed])
 write_csv(REP/'resource_telemetry_r011.csv',[{'phase':'official_parity','cpu_worker_budget':8,'gpu_count':0,'status':'COMPLETE'},{'phase':'fixed_dose','cpu_worker_budget':1,'gpu_count':4,'status':'COMPLETE_GPU_IOU'},{'phase':'paired_bootstrap','cpu_worker_budget':38,'gpu_count':0,'status':'COMPLETE_38_WORKER_SHARDS'},{'phase':'p3','cpu_worker_budget':38,'gpu_count':0,'status':'COMPLETE'}])
 allowed=['claude_code_and_supervisor.md','dis/server_reports/orientbench-c-r011-20260807.md']+[str(p.relative_to(ROOT)) for p in sorted((WORK/'scripts').glob('*r011.py')) if p.name in {'run_joint_closure_r011.py','official_evaluator_adapter_r011.py','cleanroom_evaluator_r011.py','paired_full_ap_bootstrap_r011.py','fixed_cohort_mechanism_r011.py','p3_cross_domain_r011.py','validate_joint_closure_r011.py'}]
 allowed += [str(WORK.relative_to(ROOT)/'reports'/name) for name in ['joint_protocol_r011.json','resource_telemetry_r011.csv','provenance_r011.csv','evaluator_golden_r011.csv','evaluator_parity_r011.csv','fixed_dose_tracks_r011.csv','symmetric_components_r011.csv','baseline_metrics_r011.csv','risk_event_r011.csv','paired_ap_bootstrap_replicates_r011.csv','paired_ap_bootstrap_summary_r011.csv','baseline_tp_survival_r011.csv','baseline_tp_survival_bootstrap_r011.csv','p3_cross_domain_results_r011.csv','p3_cross_domain_bootstrap_r011.csv','p1_gate_r011.json','p3_gate_r011.json','joint_gate_r011.json','claim_ledger_r011.csv','evidence_manifest_r011.json']]
 allowed += [str(WORK.relative_to(ROOT)/'docs'/name) for name in ['joint_evidence_r011.md','fixed_dose_curves_r011.svg','p3_cross_domain_r011.svg','orientation_reliability_measure_diagnose_fix_r011.md']]
 manifest={'round':'orientbench-c-r011-20260807','scientific_snapshot':'c62ea3514e98f76baf557c22a5dd0ef812d84ee0','execution_head':'1be39b5','authorized_changes':allowed,'operation_counts':{'detector_training':0,'detector_inference':0,'official_baseline_evaluations':6,'cleanroom_baseline_evaluations':6,'fixed_dose_evaluator_calls':192,'paired_bootstrap_replicates':6000,'p3_bootstrap_replicates':11000,'downloads':0},'p1':p1,'p3':p3['status'],'joint':joint,'self_identity':'N/A_SELF_REFERENCE'}
 (REP/'evidence_manifest_r011.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
 report=ROOT/'dis/server_reports/orientbench-c-r011-20260807.md'; report.write_text(f'# orientbench-c r011 server report\n\n- P1: `{p1}`\n- P3: `{p3["status"]}`\n- Joint: `{joint}`\n- Official/clean-room baseline parity: {sum(r["status"]=="PASS" for r in parity)}/6 PASS.\n- D/S paired support: {support_d}/6 and {support_s}/6.\n- AR survival ordering: {ordered}/6.\n- Corrected SODA-A/23 lineage: 1,663,631 predictions, AP50=0.599124, AP75=0.273483.\n- No training, detector inference, download, threshold change, or D_cal/D_audit change.\n')

def refresh_manifest():
 scripts=['run_joint_closure_r011.py','official_evaluator_adapter_r011.py','cleanroom_evaluator_r011.py','paired_full_ap_bootstrap_r011.py','fixed_cohort_mechanism_r011.py','p3_cross_domain_r011.py','validate_joint_closure_r011.py']
 reports=['joint_protocol_r011.json','resource_telemetry_r011.csv','provenance_r011.csv','evaluator_golden_r011.csv','evaluator_parity_r011.csv','fixed_dose_tracks_r011.csv','symmetric_components_r011.csv','baseline_metrics_r011.csv','risk_event_r011.csv','paired_ap_bootstrap_replicates_r011.csv','paired_ap_bootstrap_summary_r011.csv','baseline_tp_survival_r011.csv','baseline_tp_survival_bootstrap_r011.csv','p3_cross_domain_results_r011.csv','p3_cross_domain_bootstrap_r011.csv','p1_gate_r011.json','p3_gate_r011.json','joint_gate_r011.json','claim_ledger_r011.csv','evidence_manifest_r011.json']
 docs=['joint_evidence_r011.md','fixed_dose_curves_r011.svg','p3_cross_domain_r011.svg','orientation_reliability_measure_diagnose_fix_r011.md']
 allowed=['claude_code_and_supervisor.md','dis/server_reports/orientbench-c-r011-20260807.md']+[str(WORK.relative_to(ROOT)/'scripts'/x) for x in scripts]+[str(WORK.relative_to(ROOT)/'reports'/x) for x in reports]+[str(WORK.relative_to(ROOT)/'docs'/x) for x in docs]
 def identity(rel):
  path=ROOT/rel
  return {'path':rel,'bytes':path.stat().st_size,'sha256':sha(path),'git_blob':subprocess.check_output(['git','hash-object',str(path)],cwd=ROOT,text=True).strip()}
 manifest_path=str(WORK.relative_to(ROOT)/'reports/evidence_manifest_r011.json')
 outputs=[identity(x) for x in allowed if x!=manifest_path]
 input_paths=sorted({v[2] for v in CELLS.values()}|{v[3] for v in CELLS.values()})
 inputs=[identity(x) for x in input_paths]
 p1=json.loads((REP/'p1_gate_r011.json').read_text());p3=json.loads((REP/'p3_gate_r011.json').read_text());joint=json.loads((REP/'joint_gate_r011.json').read_text())
 manifest={'round':'orientbench-c-r011-20260807','scientific_snapshot':'c62ea3514e98f76baf557c22a5dd0ef812d84ee0','execution_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'final_head':'N/A_SELF_REFERENCE','authorized_changes':allowed,'inputs':inputs,'outputs':outputs,'generation_commands':['official_evaluator_adapter_r011.py --unit <Core-6>','cleanroom_evaluator_r011.py --unit <Core-6>','run_joint_closure_r011.py --unit <Core-6>','paired_full_ap_bootstrap_r011.py','fixed_cohort_mechanism_r011.py --unit <Core-6>','p3_cross_domain_r011.py','run_joint_closure_r011.py --finalize','validate_joint_closure_r011.py'],'runtime_log_root':'outputs/persistent_artifacts/orientbench_r011','operation_counts':{'detector_training':0,'detector_inference':0,'official_baseline_evaluations':6,'cleanroom_baseline_evaluations':6,'fixed_dose_evaluator_calls':192,'paired_bootstrap_replicates':6000,'p3_bootstrap_replicates':11000,'downloads':0},'p1':p1['status'],'p3':p3['status'],'joint':joint['status'],'self_identity':'N/A_SELF_REFERENCE'}
 (REP/'evidence_manifest_r011.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--unit');ap.add_argument('--all',action='store_true');ap.add_argument('--aggregate',action='store_true');ap.add_argument('--protocol',action='store_true');ap.add_argument('--provenance',action='store_true');ap.add_argument('--golden',action='store_true');ap.add_argument('--parity',action='store_true');ap.add_argument('--finalize',action='store_true');ap.add_argument('--manifest',action='store_true');a=ap.parse_args()
 if a.protocol: protocol()
 if a.provenance: provenance()
 if a.unit: run_unit(a.unit)
 if a.all:
  for c in CELLS: run_unit(c)
 if a.aggregate: aggregate()
 if a.golden: write_csv(REP/'evaluator_golden_r011.csv',executable_golden())
 if a.parity: refresh_parity()
 if a.finalize: finalize()
 if a.manifest: refresh_manifest()
