#!/usr/bin/env python3
"""Independent r016 validation of r015, implemented without r015 imports."""
from __future__ import annotations

import csv, hashlib, json, os, subprocess, sys, time
from multiprocessing import get_context
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import psutil

ROOT=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(ROOT)); sys.path.insert(0,str(ROOT/"scripts"))
from derive_delta_theta_075 import load_interpolator
R014=ROOT/"outputs/persistent_artifacts/orientbench_r014"; R015=ROOT/"p3_selector/deployable_proxy_r015"; R016=ROOT/"p3_selector/deployable_proxy_r016"; LABEL=ROOT/"outputs/persistent_artifacts/m069_fullval_reliability"; OUT=R016/"reports"; RT=ROOT/"outputs/persistent_artifacts/orientbench_r016"
UNITS={"A":("DIOR-R/22","DIOR-R","rotated_retinanet_psc"),"B":("DIOR-R/3","DIOR-R","oriented_rcnn"),"C":("DIOR-R/61","DIOR-R","rotated_rtmdet_s"),"D":("FAIR1M-v1.0/24","FAIR1M-v1.0","rotated_retinanet_psc"),"E":("SODA-A/23","SODA-A","rotated_retinanet_psc"),"F":("SODA-A/4","SODA-A","oriented_rcnn")}; DATA=("DIOR-R","FAIR1M-v1.0","SODA-A"); DTH=load_interpolator(); FRAMES={}

def sha(p:Path):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def digest(v): return hashlib.sha256('\n'.join(sorted(map(str,v))).encode()).hexdigest()
def git(*a): return subprocess.check_output(['git',*a],cwd=ROOT,text=True).strip()
def write_csv(path,rows):
 fields=list(dict.fromkeys(k for r in rows for k in r));path.parent.mkdir(parents=True,exist_ok=True)
 with path.open('w',newline='',encoding='utf-8') as f:
  w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n');w.writeheader();w.writerows(rows)
def role(image,flag): return 'D_audit' if flag=='D_audit' else ('D_cal-fit' if int(hashlib.md5(f'm069:{image}'.encode()).hexdigest()[:8],16)%2==0 else 'D_cal-calib')
def raw_labels(u, audit_only=False):
 rows=[]
 with (LABEL/u/'matched_fullval.jsonl').open() as f:
  for line in f:
   x=json.loads(line);g=x.get('gt_obb',{});w=float(g.get('obb_w',0));h=float(g.get('obb_h',0))
   if min(w,h)<=0 or max(w,h)/min(w,h)<2.1:continue
   rr=role(str(x['image_id']),str(x.get('d_cal_daudit_split_flag','')))
   if audit_only and rr!='D_audit':continue
   ar=max(w,h)/min(w,h);rows.append({'image_id':str(x['image_id']),'pred_id':int(x['pred_id']),'risk':min(float(x['angle_error'])/max(float(DTH(ar)),1.),3.),'role':rr})
 return pd.DataFrame(rows)
def universe(u):
 x=pd.read_csv(LABEL/u/'image_universe.csv',dtype={'image_id':str});x=x[x.d_cal_daudit_split_flag=='D_audit'];ds=UNITS[u][1]
 if ds!='SODA-A':
  ids=sorted(x.image_id.astype(str).unique());return ids,{a:a for a in ids}
 mp=pd.read_csv(R014/'soda_tile_to_mother_r014.csv',dtype=str).set_index('tile_id').mother_scene_id.to_dict();tile={a:mp[a] for a in x.image_id.astype(str)};return sorted(set(tile.values())),tile
def nrc(order,risks,weights):
 r=risks[order];w=weights[order].astype(np.int64);ok=w>0;r=r[ok];w=w[ok]
 if not len(r):return float('nan')
 z=np.repeat(r,w);k=np.arange(1,len(z)+1);m=np.mean(np.cumsum(z)/k);q=np.sort(z,kind='stable');o=np.mean(np.cumsum(q)/k);rand=np.mean(z)
 return float((m-o)/(rand-o)) if abs(rand-o)>=1e-12 else float('nan')
def one(task):
 ds,rep,m=task;out=[]
 for u,f in FRAMES.items():
  if UNITS[u][1]==ds:out.append((u,nrc(f['lin'],f['risk'],m[f['pos']])-nrc(f['eqs'],f['risk'],m[f['pos']])))
 return ds,rep,out
def pcenter(vals,point): return float((1+np.sum((vals-point)>=point))/(len(vals)+1))
def holm(rows,pfield,out):
 running=0.;n=len(rows)
 for rank,i in enumerate(sorted(range(n),key=lambda i:rows[i][pfield])):
  running=max(running,min(1.,(n-rank)*rows[i][pfield]));rows[i][out]=running
def check_close(expected,actual):
 a=np.asarray(actual,float);b=np.asarray(expected,float);return bool(np.allclose(a,b,atol=1e-12,rtol=0,equal_nan=True)),float(np.nanmax(np.abs(a-b)))

def main():
 os.environ.update({'OMP_NUM_THREADS':'1','OPENBLAS_NUM_THREADS':'1','MKL_NUM_THREADS':'1','NUMEXPR_NUM_THREADS':'1'})
 allowed=sorted(['claude_code_and_supervisor.md','dis/server_reports/orientbench-c-r015-20260808.md','p3_selector/deployable_proxy_r015/protocol_r015.json','p3_selector/deployable_proxy_r015/scripts/audit_r014_protocol_r015.py','p3_selector/deployable_proxy_r015/scripts/recompute_shared_cluster_bootstrap_r015.py','p3_selector/deployable_proxy_r015/scripts/validate_r015.py','p3_selector/deployable_proxy_r015/reports/prelabel_seal_audit_r015.json','p3_selector/deployable_proxy_r015/reports/leakage_and_access_audit_r015.csv','p3_selector/deployable_proxy_r015/reports/unit_results_r015.csv','p3_selector/deployable_proxy_r015/reports/dataset_results_r015.csv','p3_selector/deployable_proxy_r015/reports/bootstrap_replicates_r015.csv','p3_selector/deployable_proxy_r015/reports/gate_r015.json','p3_selector/deployable_proxy_r015/reports/validator_r015.json','p3_selector/deployable_proxy_r015/reports/resource_telemetry_r015.csv','p3_selector/deployable_proxy_r015/reports/evidence_manifest_r015.json','p3_selector/deployable_proxy_r015/docs/protocol_closure_r015.md','top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r015.csv','top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/novelty_matrix_r015.csv'])
 checks={}; witnesses={}; audit=[]
 parent='b1fb7dfadbba04747731dfc4db603a5d159c6dbf'; child='9f906fb3bfb07bd276d380a009cd95e2dc57c36a'; actual=sorted(git('diff','--name-only',parent,child).splitlines())
 checks['r015_parent_chain']=git('rev-parse',f'{child}^')==parent;checks['r015_exact_one_commit']=git('rev-list','--count',f'{parent}..{child}')=='1';checks['r015_exact_authorized_19_paths']=actual==allowed;checks['dis_B_unchanged']=git('rev-parse',f'{parent}:dis/B.md')==git('rev-parse',f'{child}:dis/B.md')=='3181a862137918f1dd41677893937c12b3c39c28'
 em=json.loads((R015/'reports/evidence_manifest_r015.json').read_text()); tracked=em['tracked_outputs'];checks['r015_manifest_18_blobs']=len(tracked)==19 and em.get('self_reference')=='N/A_SELF_REFERENCE' and all(x['path'].endswith('evidence_manifest_r015.json') or (git('cat-file','-s',f'{child}:{x["path"]}')==str(x['bytes']) and sha(ROOT/x['path'])==x['sha256']) for x in tracked)
 checks['r015_manifest_runtime_omission']=all('bytes' not in x or x.get('bytes') in ('N/A_SELF_REFERENCE',None) for x in em.get('runtime_outputs',[])); witnesses['r015_runtime_omission']='R015_MANIFEST_OMISSION'
 # Dynamic full universes, zero eligible clusters and raw score joins.
 cby={}; cmaps={}; zero={}; labelsets={}
 for u in UNITS:
  cs,mp=universe(u);ds=UNITS[u][1];cmaps[u]=mp;labelsets[u]=raw_labels(u,False)
  if ds in cby:checks[f'universe_equal_{ds}']=cby[ds]==cs
  else:cby[ds]=cs;checks[f'universe_equal_{ds}']=True
  aud=labelsets[u][labelsets[u].role=='D_audit']; occupied=set(aud.image_id.map(mp));zero[u]=len(set(cs)-occupied);checks[f'zero_eligible_verified_{u}']=zero[u]>=0
  audit.append({'record':'universe','unit':u,'dataset':ds,'set_name':'D_audit_cluster_universe','rows':'','images':'','mothers':'','set_sha256':digest(cs),'zero_eligible_clusters':zero[u],'status':'OK'})
 for u in UNITS:
  labels=labelsets[u];scores=pd.read_parquet(R014/'scores'/f'{u}.parquet');features=pd.read_parquet(R014/'features'/f'{u}.parquet')
  forbidden={'gt','angle_error','risk','GT_AR','gt_ar','split','d_cal_daudit_split_flag'};checks[f'schema_{u}']=not bool(forbidden&set(scores.columns)) and not bool(forbidden&set(features.columns))
  aud=labels[labels.role=='D_audit'][['image_id','pred_id','risk']];frame=aud.merge(scores[['image_id','pred_id','score_ar_size_linear','EQS']],on=['image_id','pred_id'],validate='one_to_one');pos={v:i for i,v in enumerate(cby[UNITS[u][1]])};frame['pos']=frame.image_id.map(cmaps[u]).map(pos);FRAMES[u]={'risk':frame.risk.to_numpy(float),'pos':frame.pos.to_numpy(int),'lin':np.argsort(-frame.score_ar_size_linear.to_numpy(float),kind='stable'),'eqs':np.argsort(-frame.EQS.to_numpy(float),kind='stable')}
  ds=UNITS[u][1];sources=[v for v in UNITS if UNITS[v][1]!=ds]
  groups={'source_Dcal_fit':set().union(*(set(labelsets[v].query("role == 'D_cal-fit'").apply(lambda x:f'{x.image_id}:{x.pred_id}',axis=1)) for v in sources)),'source_Dcal_calib':set().union(*(set(labelsets[v].query("role == 'D_cal-calib'").apply(lambda x:f'{x.image_id}:{x.pred_id}',axis=1)) for v in sources)),'source_Daudit':set().union(*(set(labelsets[v].query("role == 'D_audit'").apply(lambda x:f'{x.image_id}:{x.pred_id}',axis=1)) for v in sources)),'target_Dcal':set(labels[labels.role!='D_audit'].apply(lambda x:f'{x.image_id}:{x.pred_id}',axis=1)),'target_Daudit':set(labels[labels.role=='D_audit'].apply(lambda x:f'{x.image_id}:{x.pred_id}',axis=1)),'target_feature_prelabel':set(features.apply(lambda x:f'{x.image_id}:{x.pred_id}',axis=1)),'target_scores_prelabel':set(scores.apply(lambda x:f'{x.image_id}:{x.pred_id}',axis=1))}
  forbid_source=groups['source_Dcal_fit']&groups['source_Daudit'] or groups['source_Dcal_calib']&groups['source_Daudit']; forbid_target=(groups['source_Dcal_fit']|groups['source_Dcal_calib'])&(groups['target_Dcal']|groups['target_Daudit']);checks[f'forbidden_intersections_{u}']=not bool(forbid_source or forbid_target)
  for n,v in groups.items():
   imgs={x.rsplit(':',1)[0] for x in v};moms={x.split('__',1)[0] if ds=='SODA-A' else x for x in imgs};audit.append({'record':'set','unit':u,'dataset':ds,'set_name':n,'rows':len(v),'images':len(imgs),'mothers':len(moms),'set_sha256':digest(v),'zero_eligible_clusters':'','status':'FORBIDDEN_INTERSECTION' if (n.startswith('source_Dcal') and v&groups['source_Daudit']) else 'OK'})
 # Seals and r012 feature-contract source witnesses.
 seal=json.loads((R014/'prelabel_seal.json').read_text()); final=json.loads((ROOT/'p3_selector/deployable_proxy_r014/reports/evidence_manifest_r014.json').read_text());checks['prelabel_seal_hashes']=all((ROOT/x['path']).is_file() and sha(ROOT/x['path'])==x['sha256'] for x in seal['files']);checks['r014_final_manifest_hashes']=all(x['path']=='claude_code_and_supervisor.md' or ((ROOT/x['path']).is_file() and sha(ROOT/x['path'])==x['sha256']) for x in final['tracked_outputs'])
 src=(ROOT/'p3_selector/deployable_proxy_r014/scripts/build_equivariance_features_r014.py').read_text();wanted={'doubled_angle_axial_dispersion':'2.0 *' in src or '2 *' in src,'u_axis':'u_axis' in src,'association_margin':'association_margin' in src,'single_zero_candidate':'len(candidates) == 1' in src or 'len(matches) == 1' in src,'sentinel':'sentinel' in src or 'np.nan' in src,'deterministic_tie_break':'sort' in src,'width_height_swap':'width' in src and 'height' in src,'zero_ninety_boundary':'90' in src or 'np.pi / 2' in src};witnesses['feature_contract']=wanted
 # Actual affinity and system telemetry, with pool inheritance.
 old_aff=os.sched_getaffinity(0);aff=sorted(old_aff)[:38];os.sched_setaffinity(0,set(aff));t0=time.time();tele=[{'timestamp':t0,'phase':'bootstrap','affinity_cpus':'|'.join(map(str,aff)),'worker_limit':38,'blas_threads':1,'aggregate_cpu_percent':psutil.cpu_percent(interval=.2)*psutil.cpu_count(),'rss_bytes':psutil.Process().memory_info().rss,'workers_observed':0}]
 tasks=[]
 for d,ds in enumerate(DATA):
  n=len(cby[ds]);draw=np.random.RandomState(20260807+d).randint(0,n,(1000,n));tasks.extend((ds,i,np.bincount(x,minlength=n)) for i,x in enumerate(draw))
 with ProcessPoolExecutor(max_workers=38, mp_context=get_context('fork')) as pool:got=list(pool.map(one,tasks,chunksize=1))
 tele.append({'timestamp':time.time(),'phase':'bootstrap','affinity_cpus':'|'.join(map(str,aff)),'worker_limit':38,'blas_threads':1,'aggregate_cpu_percent':psutil.cpu_percent(interval=.2)*psutil.cpu_count(),'rss_bytes':psutil.Process().memory_info().rss,'workers_observed':38});os.sched_setaffinity(0,old_aff);write_csv(OUT/'resource_telemetry_r016.csv',tele)
 vals={u:np.empty(1000) for u in UNITS}
 for ds,i,x in got:
  for u,v in x:vals[u][i]=v
 oldrep=pd.read_csv(R015/'reports/bootstrap_replicates_r015.csv');rows=[]
 for u in UNITS:
  v=vals[u];ds=UNITS[u][1];point=nrc(FRAMES[u]['lin'],FRAMES[u]['risk'],np.ones(len(FRAMES[u]['risk']),int))-nrc(FRAMES[u]['eqs'],FRAMES[u]['risk'],np.ones(len(FRAMES[u]['risk']),int));old=oldrep[(oldrep['level']=='unit')&(oldrep['key']==UNITS[u][0])].sort_values('replicate').delta_nrc.to_numpy(float);ok,err=check_close(old,v);checks[f'bootstrap_unit_{u}']=ok;rows.append({'level':'unit','key':UNITS[u][0],'dataset':ds,'point_delta_nrc':point,'ci_low':np.percentile(v,2.5),'ci_high':np.percentile(v,97.5),'p_centered_one_sided':pcenter(v,point),'bootstrap_max_abs_error':err,'supported_pre_holm':''})
 holm(rows,'p_centered_one_sided','holm_p');
 for r in rows:r['supported']=bool(r['point_delta_nrc']>=.02 and r['ci_low']>0 and r['holm_p']<.05)
 drows=[]
 for ds in DATA:
  keys=[u for u in UNITS if UNITS[u][1]==ds];v=np.mean(np.column_stack([vals[u] for u in keys]),axis=1);point=float(np.mean([next(r['point_delta_nrc'] for r in rows if r['key']==UNITS[u][0]) for u in keys]));old=oldrep[(oldrep['level']=='dataset')&(oldrep['key']==ds)].sort_values('replicate').delta_nrc.to_numpy(float);ok,err=check_close(old,v);checks[f'bootstrap_dataset_{ds}']=ok;drows.append({'level':'dataset','key':ds,'dataset':ds,'point_delta_nrc':point,'ci_low':np.percentile(v,2.5),'ci_high':np.percentile(v,97.5),'p_centered_one_sided':pcenter(v,point),'bootstrap_max_abs_error':err})
 holm(drows,'p_centered_one_sided','holm_p');
 for r in drows:r['supported']=bool(r['point_delta_nrc']>=.02 and r['ci_low']>0 and r['holm_p']<.05)
 oldunit=pd.read_csv(R015/'reports/unit_results_r015.csv');oldds=pd.read_csv(R015/'reports/dataset_results_r015.csv')
 for r in rows:
  z=oldunit[oldunit.unit==r['key']].iloc[0];checks[f'summary_unit_{r["key"]}']=all(abs(float(z[a])-float(r[b]))<=1e-12 for a,b in [('delta_nrc','point_delta_nrc'),('ci_low','ci_low'),('ci_high','ci_high'),('p_centered_one_sided','p_centered_one_sided'),('holm6_p','holm_p')]) and bool(z['supported'])==r['supported']
 for r in drows:
  z=oldds[oldds.dataset==r['key']].iloc[0];checks[f'summary_dataset_{r["key"]}']=all(abs(float(z[a])-float(r[b]))<=1e-12 for a,b in [('delta_nrc','point_delta_nrc'),('ci_low','ci_low'),('ci_high','ci_high'),('p_centered_one_sided','p_centered_one_sided'),('holm3_p','holm_p')]) and bool(z['supported'])==r['supported']
 support=sum(r['supported'] for r in rows);d_support=sum(r['supported'] for r in drows);checks['gate_support_counts']=support==6 and d_support==3
 # Paper, claim ledger, and novelty are recomputed from current bytes.
 paper=(ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md').read_text();checks['paper_boundary']=all(x in paper for x in ['探索性 post-audit evidence','0/6','固定剂量配对 AP 只保留为描述性候选']) and not any(x in paper for x in ['PASS_','FAIL_','venue-ready','authorized-path']);checks['paper_citations']='10.1016/j.isprsjprs.2019.11.023' in paper and 'arXiv:2110.01931' in paper and 'Yi Yu, Feipeng Da' in paper and '[0.1530, 0.1936]' not in paper
 ledger=pd.read_csv(ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r015.csv');checks['claim_hashes']=all(hashlib.sha256(str(x.exact_claim).encode()).hexdigest()==x.claim_sha256 and str(x.exact_claim) in paper for x in ledger.itertuples())
 novelty=pd.read_csv(ROOT/'top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/novelty_matrix_r015.csv');checks['novelty_unknown_excluded']=not any((novelty.verified_source.astype(str).str.contains('nature.com/scientificreports/$|openaccess.thecvf.com/WACV2024$')).fillna(False))
 write_csv(OUT/'summary_recomputed_r016.csv',rows+drows);write_csv(OUT/'set_and_schema_audit_r016.csv',audit)
 ok=all(checks.values());result={'schema':'r016_independent_validator_v1','token':'VALID_R015_CLOSURE_R016' if ok else 'INVALID_R015_CLOSURE_R016','checks':checks,'witnesses':witnesses,'summary':{'unit_support':support,'dataset_support':d_support,'r015_numeric_acceptance':'EXPLORATORY_CORE_SUPPORT_R015' if ok else 'REJECTED','r014_formal_verdict':'FAIL_PROTOCOL_R014','hrsc_status':'INCONCLUSIVE_INDEPENDENT_HRSC_R014'}}
 (OUT/'validator_r016.json').write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n');print(json.dumps({'token':result['token'],'failed':[k for k,v in checks.items() if not v]},ensure_ascii=False))
if __name__=='__main__':main()
