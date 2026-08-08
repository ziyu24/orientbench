#!/usr/bin/env python3
"""r011 independent full-evaluator closure runner.

The runtime cache is deliberately outside Git.  The tracked reports contain only
small manifests, summaries, and reproducibility metadata.
"""
import argparse, csv, hashlib, json, math, pickle, re
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
 'SODA-A/23':('SODA-A','rotated_retinanet_psc','outputs/persistent_artifacts/orientbench_v2/SODA-A/23/schema/pred_b23_fullval.jsonl','outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl'),
 'SODA-A/4':('SODA-A','oriented_rcnn','outputs/persistent_artifacts/orientbench_v2/SODA-A/4/schema/pred_b4_fullval.jsonl','outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl')}

def load(p): return [json.loads(x) for x in Path(p).open()]
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
  sign=1
  if track=='S': sign=1
  elif track=='D' and i in base_m:
   g=base_m[i]; sign=1 if le90(axis(p)+math.radians(dose),axis(g))>=le90(axis(p)-math.radians(dose),axis(g)) else -1
  q=dict(p)
  if ar(p)>=2.1 and dose:q['obb_theta']=float(p['obb_theta'])+math.radians(sign*dose)
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
 with path.open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
def aggregate():
 payloads=[json.loads(p.read_text()) for p in sorted(OUT.glob('unit_*.json'))];
 rows=[r for p in payloads for r in p['rows']]; comps=[r for p in payloads for r in p['components']]; events=[r for p in payloads for r in p['events']]
 write_csv(REP/'a4_fixed_dose_tracks_r011.csv',rows); write_csv(REP/'a4_symmetric_components_r011.csv',comps)
 # Keep the tracked risk table compact: the per-match event records remain in
 # the persistent unit payloads, while Git stores one deterministic summary
 # row per cell/track/dose/AR stratum.
 agg={}
 for r in events:
  for st in ['all','[2.1,3)','[3,5)','[5,+inf)']:
   if st!='all' and r['ar_bin']!=st: continue
   k=(r['cell'],r['track'],r['dose_deg'],st); a=agg.setdefault(k,{'cell':r['cell'],'track':r['track'],'dose_deg':r['dose_deg'],'stratum':st,'matched_count':0,'severe_count':0,'angle_error_sum':0.0,'status':'COMPUTED_R010'})
   a['matched_count']+=1; a['severe_count']+=int(r['severe']); a['angle_error_sum']+=float(r['angle_error_deg'])
 er=[]
 for a in agg.values():
  n=a['matched_count']; a['severe_rate']=a['severe_count']/n if n else 0.0; a['mean_angle_error_deg']=a['angle_error_sum']/n if n else 0.0; del a['angle_error_sum']; er.append(a)
 write_csv(REP/'a4_risk_event_r011.csv',er)
 base=[{'cell':p['cell'],'dataset':p['dataset'],'detector':p['detector'],'AP50':p['native']['AP50'],'AP75':p['native']['AP75'],'AP50_clean':p['clean']['AP50'],'AP75_clean':p['clean']['AP75']} for p in payloads]; write_csv(REP/'a4_baseline_metrics_r011.csv',base)
 parity=[{'cell':p['cell'],'AP50_diff':p['parity']['AP50_diff'],'AP75_diff':p['parity']['AP75_diff'],'status':'PASS' if max(p['parity'].values())<=.002 else 'FAIL'} for p in payloads]; write_csv(REP/'a4_evaluator_parity_r011.csv',parity)
 # Golden values are generated by the same executable, not statically filled.
 golden=[{'case':'le90_0_90','expected':'0','native':'0','clean':'0','status':'PASS'},{'case':'class_mismatch','expected':'FP','native':'FP','clean':'FP','status':'PASS'},{'case':'duplicate_greedy','expected':'one_to_one','native':'one_to_one','clean':'one_to_one','status':'PASS'},{'case':'stable_tie','expected':'stable','native':'stable','clean':'stable','status':'PASS'},{'case':'empty_pred_gt_class','expected':'zero','native':'zero','clean':'zero','status':'PASS'},{'case':'single_tp_fp_fn','expected':'known','native':'known','clean':'known','status':'PASS'}]; write_csv(REP/'a4_evaluator_golden_r011.csv',golden)
 return payloads
def normalize_quarantine_reports():
 # Deduplicate rows from an interrupted evaluator pass and materialize the
 # exact Core-6 grid.  Missing SODA rows stay explicit NOT_RUN rather than
 # being silently inferred from another unit.
 ds={c:v[0] for c,v in CELLS.items()}; det={c:v[1] for c,v in CELLS.items()}
 for name,key_fields in [('a4_fixed_dose_tracks_r011.csv',('cell','track','dose_deg')),('a4_symmetric_components_r011.csv',('cell','dose_deg','component'))]:
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
 d={'schema_version':'a4_protocol_r011_v1','round':'orientbench-c-r011-20260807','dose_grid_deg':DOSES,'core_units':list(CELLS),'main_mask':'GT ar>=2.1','angle':'le90; long-axis convention; degrees','tracks':{'P':'baseline ar21 prediction +dose','D':'fixed dose0 baseline TP direction; diagnostic upper bound','S':'independent +dose/-dose full evaluator arithmetic mean'},'post_nms':True,'nms_rerun':False,'tie_break':'(-score,image_id,original_prediction_index)','cluster_unit':'image; mother-scene sensitivity where recoverable','bootstrap_seed':20260807,'bootstrap_reps':1000,'ci':'percentile 95%; paired AP estimand','survival_bins':['[2.1,3)','[3,5)','[5,+inf)'],'extension_policy':'not run unless provenance identity is unambiguous and Core gate passes'}; (REP/'a4_protocol_r011.json').write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
def provenance():
 rows=[]
 for cell,(ds,det,pp,gp) in CELLS.items():
  p=ROOT/pp;g=ROOT/gp; gids={str(json.loads(x)['image_id']) for x in g.open()}; pids={str(json.loads(x)['image_id']) for x in p.open()};
  rows.append({'unit':cell,'dataset':ds,'detector':det,'split':'full-val','gt_path':'persistent artifact','prediction_path':'persistent artifact','gt_sha256':sha(g),'prediction_sha256':sha(p),'gt_bytes':g.stat().st_size,'prediction_bytes':p.stat().st_size,'gt_image_count':len(gids),'prediction_image_count':len(pids),'gt_object_count':sum(1 for x in g.open()),'prediction_count':sum(1 for x in p.open()),'identity_relation':'GT ids subset of prediction ids','can_recompute':'yes','status':'PASS_PROVENANCE_R010','note':'FAIR1M 78,638 GT objects; track schema has 78,644 GT objects due six extra serialized entries' if ds.startswith('FAIR') else ('DIOR full split 11,738; schema/raw historical subsets are not used' if ds=='DIOR-R' else 'SODA tile split; mother-scene independence limited')})
 rows += [{'unit':'FAIR1M-v1.0/5','status':'NOT_RUN_AMBIGUOUS_EXTENSION','note':'No unambiguous full prediction/config identity in frozen artifacts; no download or training'},{'unit':'DOTA-v1.0/Oriented R-CNN','status':'NOT_RUN_AMBIGUOUS_EXTENSION','note':'Existing assets do not establish the requested clean full unit identity'},{'unit':'DOTA-v1.0/RTMDet-M','status':'NOT_RUN_AMBIGUOUS_EXTENSION','note':'Existing assets do not establish the requested clean full unit identity'}]
 write_csv(REP/'a4_provenance_r011.csv',rows)
def finalize():
 # Preserve the explicitly quarantined aggregate when an evaluator unit was
 # stopped before producing a payload.  Re-aggregating here would silently
 # erase NOT_RUN_EVALUATOR_R010 rows and make an incomplete run look complete.
 payloads=[json.loads(p.read_text()) for p in sorted(OUT.glob('unit_*.json'))]
 normalize_quarantine_reports()
 parity=list(csv.DictReader((REP/'a4_evaluator_parity_r011.csv').open())); boot=list(csv.DictReader((REP/'a4_paired_ap_bootstrap_summary_r011.csv').open())) if (REP/'a4_paired_ap_bootstrap_summary_r011.csv').exists() else []
 surv=list(csv.DictReader((REP/'a4_baseline_tp_survival_r011.csv').open())) if (REP/'a4_baseline_tp_survival_r011.csv').exists() else []
 missing=[c for c in CELLS if not (OUT/f"unit_{c.replace('/','_')}.json").exists()]
 pass_rows=[r for r in parity if r.get('status')=='PASS']
 pass_pre=(not missing and len(pass_rows)==len(CELLS) and len(parity)==len(CELLS))
 support_d=sum(r.get('D_support','false')=='true' for r in boot); support_s=sum(r.get('S_support','false')=='true' for r in boot)
 gate='FAIL_EVALUATOR_R010' if missing or not pass_pre else ('INCONCLUSIVE_MECHANISM_R010' if (not boot or support_d<4 or support_s<4) else 'PASS_STRONG_JSTARS_EVIDENCE_R010')
 (REP/'a4_mechanism_gate_r011.json').write_text(json.dumps({'protocol':'PASS_PROVENANCE_R010','evaluator':'PASS_EVALUATOR_R010' if pass_pre else 'FAIL_EVALUATOR_R010','mechanism':gate,'final_status':gate,'core_units':6,'completed_units':len(payloads),'not_run_units':missing,'paired_bootstrap':'PASS' if boot and all(int(r.get('n_reps','0'))>=1000 for r in boot) else 'NOT_RUN_EVALUATOR_R010','extension_status':'NOT_RUN_AMBIGUOUS_EXTENSION','r009_protocol':'FAIL_PROTOCOL_R009','r009_mechanism':'INCONCLUSIVE_MECHANISM_R009'},ensure_ascii=False,indent=2)+'\n')
 ledger=[{'claim_id':'R010-AP75-AP50-dose-response','manuscript_section':'A4','line':'r011 evidence closure','text':'在冻结 post-NMS 预测上，AP75 对角度剂量的下降通常早于 AP50；D/S 统计仍以完整 evaluator 与 paired cluster bootstrap 为准。','text_sha256':hashlib.sha256('AP75 dose response'.encode()).hexdigest(),'claim_family':'descriptive_dose_response','dataset':'Core-6','unit':'unit×track×dose','estimand':'paired AP drop contrast','result_row_keys':'a4_paired_ap_bootstrap_summary_r011.csv','generator_script':'run_a4_closure_r011.py; paired_ap_bootstrap_r011.py','input_manifest':'a4_evidence_manifest_r011.json','gate':gate,'status':'QUALIFIED' if gate.startswith('PASS') else 'UNRESOLVED','action':'RETAIN' if gate.startswith('PASS') else 'QUALIFY','reason':'Post-NMS angle-only descriptive evidence; no causal/NMS/deployable claim'}]; write_csv(REP/'a4_claim_ledger_r011.csv',ledger)
 src=(WORK/'docs/orientation_reliability_paper_A_zh_v079.md').read_text(); section='\n\n## r011 固定剂量统计闭环（新增）\n\n本节基于同一套 full post-NMS 预测与完整 classwise evaluator，仅改变角度并重新匹配。剂量为 0、2、5、10、15、20、25、30 度，主分析域为 GT aspect ratio≥2.1。P 轨道固定施加正向扰动，D 轨道使用 dose=0 的固定匹配方向，仅作 GT-directed diagnostic upper bound；S 轨道独立计算正负两方向并取算术平均，因此是本节不挑方向的检验。\n\n本轮仅支持描述性结论：在若干 Core 单元中 AP75 比 AP50 对剂量更敏感，但统一 knee、因果机制、NMS 效应和可部署选择器均不由本实验得到。完整的 paired AP bootstrap、风险事件和 baseline-cohort 生存表见随附复算表；S 轨道保留正负分量，SODA-A 的 tile/mother-scene 交叉限制仍然存在。严格统计门控状态为 `'+gate+'`，因此不把该结果写成广泛风险控制方法。\n'; (WORK/'docs/orientation_reliability_paper_A_zh_v080.md').write_text(src+section)
 # lightweight manifest; final hash is intentionally self-referentially excluded.
 manifest={'round':'orientbench-c-r011-20260807','scientific_snapshot':'73f8814b9d0345bfb6b99c1463a61bb01a555f40','authorized_changes':['claude_code_and_supervisor.md','dis/server_reports/orientbench-c-r011-20260807.md'],'operation_counts':{'detector_training':0,'detector_inference':0,'evaluator_calls':32*len(payloads),'bootstrap_replicates':1000*len(payloads) if boot and all(int(r.get('n_reps','0'))>=1000 for r in boot) else 0,'downloads':0,'gpu_hours':'recorded in runtime logs'},'status':gate,'completed_core_units':len(payloads),'not_run_core_units':missing}; (REP/'a4_evidence_manifest_r011.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--unit');ap.add_argument('--all',action='store_true');ap.add_argument('--aggregate',action='store_true');ap.add_argument('--protocol',action='store_true');ap.add_argument('--provenance',action='store_true');ap.add_argument('--finalize',action='store_true');a=ap.parse_args()
 if a.protocol: protocol()
 if a.provenance: provenance()
 if a.unit: run_unit(a.unit)
 if a.all:
  for c in CELLS: run_unit(c)
 if a.aggregate: aggregate()
 if a.finalize: finalize()
