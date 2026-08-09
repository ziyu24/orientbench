#!/usr/bin/env python3
"""Independent feasibility validator; it never imports generator decisions."""
from __future__ import annotations
import argparse,csv,hashlib,json,math,os,sys
from pathlib import Path
import numpy as np,pandas as pd

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
from orientbench.metrics.nrc_auc import nrc_auc
from scripts.m069_common import delta_theta_075
DEFAULT=ROOT/"outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809"
R014=ROOT/"outputs/persistent_artifacts/orientbench_r014";LABEL=ROOT/"outputs/persistent_artifacts/m069_fullval_reliability"
UNITS={"A":("DIOR-R","DIOR-R/22"),"B":("DIOR-R","DIOR-R/3"),"C":("DIOR-R","DIOR-R/61"),"D":("FAIR1M","FAIR1M-v1.0/24"),"E":("SODA-A","SODA-A/23"),"F":("SODA-A","SODA-A/4")}
SCORES={"raw_confidence":"detection_score","linear_source_frozen":"score_ar_size_linear","tta_angle":"tta_angle","tta_localization":"tta_localization","S0":"S0","learned_EQS":"EQS"};BASE=["raw_confidence","linear_source_frozen","tta_angle","tta_localization"]
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1<<20),b''):h.update(b)
 return h.hexdigest()
def label(unit):
 rows=[]
 with (LABEL/unit/'matched_fullval.jsonl').open() as f:
  for line in f:
   r=json.loads(line);g=r['gt_obb'];w,h=float(g['obb_w']),float(g['obb_h']);ar=max(w,h)/max(min(w,h),1e-6)
   if ar>=2.1:rows.append((str(r['image_id']),int(r['pred_id']),float(np.clip(float(r['angle_error'])/max(float(delta_theta_075(ar)),1),0,3))))
 return pd.DataFrame(rows,columns=['image_id','pred_id','risk_cap3'])
def metric(score,risk):
 score=np.asarray(score,float);risk=np.asarray(risk,float);o=np.argsort(-score,kind='stable');s=score[o];r=risk[o];b=np.r_[0,np.where(s[1:]!=s[:-1])[0]+1];n=np.diff(np.r_[b,len(s)]);rs=np.add.reduceat(r,b);cn=np.cumsum(n);cr=np.cumsum(rs);cov=cn/len(r);gr=cr/len(r);out={'AUGRC':float(np.trapz(np.r_[0,gr],np.r_[0,cov])),'AURC':float(np.mean(np.cumsum(r)/np.arange(1,len(r)+1))),'NRC':float(nrc_auc(score,risk)['nrc_auc']),'nonempty_coverage':float(cov[-1])}
 for q in (.7,.9):i=int(np.searchsorted(cov,q));out[f'Risk@{int(q*100)}']=float(cr[i]/cn[i]);out[f'actual_coverage@{int(q*100)}']=float(cov[i])
 return out
def raw_frames():
 frames={};soda=pd.read_csv(R014/'soda_tile_to_mother_r014.csv',dtype=str).set_index('tile_id').mother_scene_id.to_dict()
 for u in UNITS:
  f=pd.read_parquet(R014/f'features/{u}.parquet');s=pd.read_parquet(R014/f'scores/{u}.parquet');x=f.merge(s,on=['image_id','pred_id'],suffixes=('','_score'),validate='one_to_one').merge(label(u),on=['image_id','pred_id'],validate='one_to_one');x['tta_angle']=-x.u_axis;x['tta_localization']=-(x.missing_fraction+x.iou_loss);x['S0']=-(x.u_axis+x.missing_fraction+x.iou_loss);x['residual']=x.risk_cap3/3;x['cluster']=x.image_id.astype(str).map(soda) if UNITS[u][0]=='SODA-A' else x.image_id.astype(str);frames[u]=x
 return frames
def as_bool(v):return str(v).strip().lower() in ('true','1','yes')
def validate_manifest(base):
 p=base/'evidence_manifest.json'
 if not p.exists():return {'present':False,'pass':True,'entries':0}
 m=json.loads(p.read_text());bad=[];selfs=[]
 for r in m['entries']:
  if r['path']=='evidence_manifest.json':selfs.append(r);continue
  q=base/r['path']
  if not q.is_file() or q.stat().st_size!=r['bytes'] or sha(q)!=r['sha256']:bad.append(r['path'])
 goodself=len(selfs)==1 and selfs[0]['bytes']=='N/A_SELF_REFERENCE' and selfs[0]['sha256']=='N/A_SELF_REFERENCE'
 return {'present':True,'pass':not bad and goodself,'entries':len(m['entries']),'bad':bad,'self_tokens_pass':goodself}
def main():
 a=argparse.ArgumentParser();a.add_argument('--root',type=Path,default=DEFAULT);a.add_argument('--no-write',action='store_true');a.add_argument('--manifest-only',action='store_true');args=a.parse_args();base=args.root
 manifest=validate_manifest(base)
 if args.manifest_only:
  print(json.dumps(manifest));raise SystemExit(0 if manifest['pass'] and manifest['present'] else 2)
 if not manifest['pass']:print(json.dumps({'status':'FAIL','manifest':manifest}));raise SystemExit(2)
 inv=pd.read_csv(base/'track_m_asset_inventory.csv');hash_bad=[]
 for r in inv.to_dict('records'):
  p=ROOT/str(r['path']) if not str(r['path']).startswith('outputs/persistent_artifacts/orientbench_topjournal_feasibility') else base/Path(str(r['path'])).name
  # Derived row paths are verified by the evidence manifest; source paths are independently hashed here.
  if 'derived fixed-score' not in str(r['role']) and (not p.is_file() or sha(p)!=str(r['SHA256'])):hash_bad.append(str(r['path']))
 frames=raw_frames();published=pd.read_csv(base/'track_m_metrics.csv');checks=[];computed=[]
 for u,x in frames.items():
  derived=pd.read_parquet(base/f'track_m_rows/{u}.parquet').sort_values(['image_id','pred_id']).reset_index(drop=True)
  expected=x[['image_id','pred_id','cluster','risk_cap3','residual',*SCORES.values()]].sort_values(['image_id','pred_id']).reset_index(drop=True)
  same_keys=derived[['image_id','pred_id']].astype(str).equals(expected[['image_id','pred_id']].astype(str))
  same_values=len(derived)==len(expected) and np.allclose(derived.drop(columns=['image_id','pred_id','cluster']).to_numpy(float),expected.drop(columns=['image_id','pred_id','cluster']).to_numpy(float),rtol=0,atol=0,equal_nan=True)
  same_clusters=derived.cluster.astype(str).equals(expected.cluster.astype(str))
  checks.append({'item':f'derived_rows:{u}','max_abs_error':0 if same_keys and same_values and same_clusters else math.inf,'atol':0,'pass':same_keys and same_values and same_clusters})
 for u,x in frames.items():
  for name,col in SCORES.items():computed.append({'level':'unit','dataset':UNITS[u][0],'unit':u,'score':name,**metric(x[col],x.residual)})
 for d in ('DIOR-R','FAIR1M','SODA-A'):
  units=[u for u,v in UNITS.items() if v[0]==d]
  for name in SCORES:
   part=[r for r in computed if r['level']=='unit' and r['unit'] in units and r['score']==name];computed.append({'level':'dataset_aggregate','dataset':d,'unit':'equal-unit mean','score':name,**{k:float(np.mean([r[k] for r in part])) for k in ('AUGRC','AURC','NRC','Risk@70','Risk@90','actual_coverage@70','actual_coverage@90','nonempty_coverage')}})
 for r in computed:
  p=published[(published.level==r['level'])&(published.dataset==r['dataset'])&(published.unit==r['unit'])&(published.score==r['score'])].iloc[0]
  for k in ('AUGRC','AURC','NRC','Risk@70','Risk@90','actual_coverage@70','actual_coverage@90','nonempty_coverage'):
   e=abs(float(p[k])-r[k]);checks.append({'item':f"{r['level']}:{r['unit']}:{r['score']}:{k}",'max_abs_error':e,'atol':1e-12,'pass':e<=1e-12})
 agg=[r for r in computed if r['level']=='dataset_aggregate'];rev=[];dom=[]
 for d in ('DIOR-R','FAIR1M','SODA-A'):
  s=next(r for r in agg if r['dataset']==d and r['score']=='S0')
  for b in BASE:
   x=next(r for r in agg if r['dataset']==d and r['score']==b)
   if s['NRC']<x['NRC'] and (s['AUGRC']>x['AUGRC'] or s['Risk@70']>x['Risk@70'] or s['Risk@90']>x['Risk@90']):rev.append(f'{d}:{b}')
   if x['AUGRC']<s['AUGRC']:dom.append(f'{d}:{b}')
 mstate='METRIC_REVERSAL' if rev else ('BASELINE_DOMINATED' if dom else 'ROBUST_CANDIDATE')
 cluster_published=pd.read_csv(base/'track_m_cluster_universe.csv',dtype={'cluster':str})
 expected_clusters=[]
 soda=pd.read_csv(R014/'soda_tile_to_mother_r014.csv',dtype=str).set_index('tile_id').mother_scene_id.to_dict()
 for u,(dataset,_) in UNITS.items():
  universe=pd.read_csv(LABEL/u/'image_universe.csv',dtype=str).image_id.astype(str)
  clusters=sorted({soda[i] for i in universe} if dataset=='SODA-A' else set(universe))
  x=frames[u];expected_clusters.extend({'unit':u,'dataset':dataset,'cluster':str(c),'eligible_rows':int((x.cluster.astype(str)==str(c)).sum())} for c in clusters)
 ep=pd.DataFrame(expected_clusters).sort_values(['unit','cluster']).reset_index(drop=True);cp=cluster_published.sort_values(['unit','cluster']).reset_index(drop=True)
 cluster_pass=len(ep)==len(cp) and ep.astype(str).equals(cp.astype(str))
 checks.append({'item':'cluster_universe_exact','max_abs_error':0 if cluster_pass else math.inf,'atol':0,'pass':cluster_pass})
 dinv=pd.read_csv(base/'track_d_candidate_inventory.csv');hits=pd.read_csv(base/'track_d_prior_outcome_hits.csv')
 status_checks=[]
 for r in dinv.to_dict('records'):
  contaminated=any(str(h.get('candidate'))==str(r['candidate']) and as_bool(h.get('outcome_bearing')) for h in hits.to_dict('records'))
  expected_status='CONTAMINATED' if contaminated else 'LICENSE_BLOCKED' if not as_bool(r['license_clear']) else 'INCOMPATIBLE_ANGLE_CONTRACT' if not as_bool(r['angle_contract_closed']) else 'MISSING_ASSET' if not as_bool(r['dataset_present']) or not as_bool(r['common_3_family_assets']) else 'ELIGIBLE_CANDIDATE'
  status_checks.append({'candidate':r['candidate'],'expected':expected_status,'published':r['status'],'pass':expected_status==r['status']})
 eligible=dinv[(dinv.auxiliary_only==False)&(dinv.status=='ELIGIBLE_CANDIDATE')]
 registered_hash_failures=[]
 for r in pd.read_csv(base/'track_d_icdar_registered_assets.csv').to_dict('records'):
  p=Path(str(r['path']))
  if as_bool(r['present']) and (not p.is_file() or p.stat().st_size!=int(r['bytes']) or sha(p)!=str(r['sha256'])):registered_hash_failures.append(str(p))
 gate='PASS_TO_METHOD_DESIGN' if mstate=='ROBUST_CANDIDATE' and len(eligible)>=2 else ('INCONCLUSIVE_FEASIBILITY' if mstate=='INSUFFICIENT_ASSETS' and len(eligible)>=2 else 'FAIL_TO_MEASUREMENT_ONLY')
 boot=pd.read_csv(base/'track_m_bootstrap.csv');bootpass=len(boot)==10000 and boot.replicate.tolist()==list(range(10000)) and np.isfinite(boot.filter(like='__S0_minus_').to_numpy()).all() and boot.worker_pid.nunique()==39
 states={'track_m':mstate,'track_d_eligible':len(eligible),'joint_gate':gate};expected={'track_m':json.loads((base/'track_m_status.json').read_text())['state'],'joint_gate':json.loads((base/'joint_gate.json').read_text())['joint_gate']}
 ok=not hash_bad and not registered_hash_failures and all(x['pass'] for x in checks) and all(x['pass'] for x in status_checks) and bootpass and states['track_m']==expected['track_m'] and states['joint_gate']==expected['joint_gate']
 out={'status':'PASS' if ok else 'FAIL','generator_gate_token_trusted':False,'source_hash_failures':hash_bad,'registered_asset_hash_failures':registered_hash_failures,'metric_checks':checks,'track_d_status_checks':status_checks,'bootstrap_complete':bootpass,'bootstrap_replicates':len(boot),'worker_count':boot.worker_pid.nunique(),'recomputed':states,'published':expected,'manifest':manifest,'atol':1e-12,'rtol':0}
 if not args.no_write:(base/'validator.json').write_text(json.dumps(out,indent=2)+'\n')
 print(json.dumps({'status':out['status'],'track_m':mstate,'joint_gate':gate}));raise SystemExit(0 if ok else 2)
if __name__=='__main__':main()
