#!/usr/bin/env python3
"""Generate the sealed-asset top-journal feasibility audit without new outcomes."""
from __future__ import annotations

import os
os.environ.update({"OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1","NUMEXPR_NUM_THREADS":"1"})

import csv, hashlib, json, math, multiprocessing as mp, pickle, re, resource, subprocess, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
from orientbench.metrics.nrc_auc import nrc_auc
from scripts.m069_common import delta_theta_075

RUNTIME=ROOT/"outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809"
CODE=ROOT/"top_journal_v3_reaudit_055/feasibility_gate_20260809"
R014=ROOT/"outputs/persistent_artifacts/orientbench_r014"
LABEL=ROOT/"outputs/persistent_artifacts/m069_fullval_reliability"
UNITS={"A":("DIOR-R","DIOR-R/22"),"B":("DIOR-R","DIOR-R/3"),"C":("DIOR-R","DIOR-R/61"),"D":("FAIR1M","FAIR1M-v1.0/24"),"E":("SODA-A","SODA-A/23"),"F":("SODA-A","SODA-A/4")}
SCORES={"raw_confidence":"detection_score","linear_source_frozen":"score_ar_size_linear","tta_angle":"tta_angle","tta_localization":"tta_localization","S0":"S0","learned_EQS":"EQS"}
BASELINES=["raw_confidence","linear_source_frozen","tta_angle","tta_localization"]
_BOOT=None

def sha(path):
 h=hashlib.sha256()
 with Path(path).open("rb") as f:
  for b in iter(lambda:f.read(1<<20),b""):h.update(b)
 return h.hexdigest()
def setsha(values):return hashlib.sha256("\n".join(sorted(map(str,values))).encode()).hexdigest()
def write_json(name,v):p=RUNTIME/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+"\n")
def write_csv(name,rows):
 p=RUNTIME/name;p.parent.mkdir(parents=True,exist_ok=True);fields=list(dict.fromkeys(k for r in rows for k in r))
 with p.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)
def run(command,phase):
 start=time.time();p=subprocess.run(command,cwd=ROOT,text=True,capture_output=True);end=time.time()
 log=RUNTIME/"logs"/f"{phase}.log";log.parent.mkdir(parents=True,exist_ok=True);log.write_text(p.stdout+"\nSTDERR\n"+p.stderr)
 return {"phase":phase,"command":" ".join(command),"cwd":str(ROOT),"inputs":"","start":start,"end":end,"exit_code":p.returncode,"log":str(log.relative_to(ROOT)),"log_sha256":sha(log)}

def preflight():
 paths=[ROOT/"AGENTS.md",Path("/home/rspip/cqc/pro/study/pth_data/readme.md"),ROOT/"dis/sug.md",ROOT/"dis/collaboration_protocol.md"]
 reads=[{"path":str(p),"bytes":p.stat().st_size,"sha256":sha(p)} for p in paths]
 head=subprocess.check_output(["git","rev-parse","HEAD"],cwd=ROOT,text=True).strip();remote=subprocess.check_output(["git","ls-remote","https://github.com/ziyu24/orientbench.git","refs/heads/main"],text=True).split()[0]
 payload={"status":"PASS","reads":reads,"head":head,"remote_main":remote,"current_branch":subprocess.check_output(["git","branch","--show-current"],cwd=ROOT,text=True).strip(),"default_branch":"main","upstream":subprocess.check_output(["git","rev-parse","--abbrev-ref","@{upstream}"],cwd=ROOT,text=True).strip(),"origin_url":subprocess.check_output(["git","remote","get-url","origin"],cwd=ROOT,text=True).strip(),"worktree_clean_at_start":True,"worktree_start_witness":"shell preflight before authorized runtime/code creation","B_blob":subprocess.check_output(["git","rev-parse","HEAD:dis/B.md"],cwd=ROOT,text=True).strip(),"runtime_absent_at_start":True,"write_scope":"four authorized classes","access_control":"no GPU/download/train/inference/new target outcome"}
 if head!=remote or payload["B_blob"]!="c0c2571f3a5c828673b39e6458ceaed5f14c5a6a":raise RuntimeError("preflight identity failed")
 write_json("preflight.json",payload)

def label_rows(unit):
 out=[]
 with (LABEL/unit/"matched_fullval.jsonl").open() as f:
  for line in f:
   r=json.loads(line);g=r["gt_obb"];w,h=float(g["obb_w"]),float(g["obb_h"]);ar=max(w,h)/max(min(w,h),1e-6)
   if ar<2.1:continue
   risk=float(np.clip(float(r["angle_error"])/max(float(delta_theta_075(ar)),1.),0,3))
   out.append((str(r["image_id"]),int(r["pred_id"]),risk))
 return pd.DataFrame(out,columns=["image_id","pred_id","risk_cap3"])

def load_assets():
 inv=[];frames={};cluster_universe=[]
 soda=pd.read_csv(R014/"soda_tile_to_mother_r014.csv",dtype=str).set_index("tile_id").mother_scene_id.to_dict()
 tta=pd.read_csv(ROOT/"p3_selector/deployable_proxy_r014/reports/tta_inventory_r014.csv")
 for unit,(dataset,identity) in UNITS.items():
  feature=R014/f"features/{unit}.parquet";scorep=R014/f"scores/{unit}.parquet";labelp=LABEL/unit/"matched_fullval.jsonl";universep=LABEL/unit/"image_universe.csv"
  for path,role in ((feature,"prediction-only features"),(scorep,"sealed scores"),(labelp,"row-level risk label"),(universep,"cluster universe")):
   inv.append({"unit":unit,"dataset":dataset,"path":str(path.relative_to(ROOT)),"role":role,"source commit/manifest":"r014 inventory / m069 manifest","bytes":path.stat().st_size,"SHA256":sha(path),"schema":path.suffix.lstrip('.'),"row count":"computed below","unique row-key witness":"computed below","cluster count/set SHA":"computed below","actual access log":"execution_ledger.csv"})
  f=pd.read_parquet(feature);s=pd.read_parquet(scorep);lab=label_rows(unit)
  x=f.merge(s,on=["image_id","pred_id"],suffixes=("","_score"),validate="one_to_one").merge(lab,on=["image_id","pred_id"],validate="one_to_one")
  x["tta_angle"]=-x.u_axis;x["tta_localization"]=-(x.missing_fraction+x.iou_loss);x["S0"]=-(x.u_axis+x.missing_fraction+x.iou_loss);x["residual"]=x.risk_cap3/3
  x["cluster"]=x.image_id.map(soda) if dataset=="SODA-A" else x.image_id.astype(str)
  if x.cluster.isna().any() or x.duplicated(["image_id","pred_id"]).any():raise RuntimeError(f"row/cluster mismatch {unit}")
  universe=pd.read_csv(universep,dtype=str).image_id.astype(str);clusters=sorted({soda[i] for i in universe} if dataset=="SODA-A" else set(universe))
  cluster_universe.extend({"unit":unit,"dataset":dataset,"cluster":c,"eligible_rows":int((x.cluster==c).sum())} for c in clusters)
  keysha=setsha(f"{a}:{b}" for a,b in zip(x.image_id,x.pred_id));csha=setsha(clusters)
  for row in inv[-4:]:row["row count"]=len(x) if row["role"]!="cluster universe" else len(universe);row["unique row-key witness"]=keysha;row["cluster count/set SHA"]=f"{len(clusters)}/{csha}"
  keep=["image_id","pred_id","cluster","risk_cap3","residual"]+list(SCORES.values());x=x[keep].copy()
  p=RUNTIME/f"track_m_rows/{unit}.parquet";p.parent.mkdir(parents=True,exist_ok=True);x.to_parquet(p,index=False,compression="zstd");frames[unit]=x
  inv.append({"unit":unit,"dataset":dataset,"path":str(p.relative_to(ROOT)),"role":"derived fixed-score audit rows","source commit/manifest":"this audit from byte-exact inputs","bytes":p.stat().st_size,"SHA256":sha(p),"schema":"parquet","row count":len(x),"unique row-key witness":keysha,"cluster count/set SHA":f"{len(clusters)}/{csha}","actual access log":"execution_ledger.csv"})
 write_csv("track_m_asset_inventory.csv",inv);write_csv("track_m_cluster_universe.csv",cluster_universe)
 return frames,cluster_universe

def metrics(score,risk):
 score=np.asarray(score,float);risk=np.asarray(risk,float);order=np.argsort(-score,kind="stable");ss=score[order];rr=risk[order];bounds=np.r_[0,np.where(ss[1:]!=ss[:-1])[0]+1];counts=np.diff(np.r_[bounds,len(ss)]);rs=np.add.reduceat(rr,bounds);cum_n=np.cumsum(counts);cum_r=np.cumsum(rs);cov=cum_n/len(rr);gr=cum_r/len(rr);aug=float(np.trapz(np.r_[0,gr],np.r_[0,cov]));aurc=float(np.mean(np.cumsum(rr)/np.arange(1,len(rr)+1)));nrc=float(nrc_auc(score,risk)["nrc_auc"])
 result={"AUGRC":aug,"AURC":aurc,"NRC":nrc,"nonempty_coverage":float(cov[-1])}
 curve=[]
 for c,g,r in zip(cov,gr,cum_r/cum_n):curve.append((float(c),float(g),float(r)))
 for q in (.7,.9):
  i=int(np.searchsorted(cov,q,side="left"));result[f"Risk@{int(q*100)}"]=float(curve[i][2]);result[f"actual_coverage@{int(q*100)}"]=float(curve[i][0])
 return result,curve

def point_metrics(frames):
 rows=[];curves=[]
 for unit,x in frames.items():
  dataset=UNITS[unit][0]
  for name,col in SCORES.items():
   m,c=metrics(x[col],x.residual);rows.append({"level":"unit","dataset":dataset,"unit":unit,"score":name,"risk_scale":"residual","rows":len(x),**m})
   curves.extend({"dataset":dataset,"unit":unit,"score":name,"coverage":a,"generalized_risk":b,"selective_risk":d} for a,b,d in c)
 for dataset in ("DIOR-R","FAIR1M","SODA-A"):
  units=[u for u,v in UNITS.items() if v[0]==dataset]
  for name in SCORES:
   part=[r for r in rows if r["level"]=="unit" and r["unit"] in units and r["score"]==name];rows.append({"level":"dataset_aggregate","dataset":dataset,"unit":"equal-unit mean","score":name,"risk_scale":"residual","rows":sum(r["rows"] for r in part),**{k:float(np.mean([r[k] for r in part])) for k in ("AUGRC","AURC","NRC","Risk@70","Risk@90","actual_coverage@70","actual_coverage@90","nonempty_coverage")}})
 write_csv("track_m_metrics.csv",rows);write_csv("track_m_risk_coverage.csv",curves);return rows

def prep_boot(frames,clusters):
 by_unit={}
 for unit,x in frames.items():
  universe=[r["cluster"] for r in clusters if r["unit"]==unit];pos={c:i for i,c in enumerate(universe)}
  by_unit[unit]={"residual":x.residual.to_numpy(float),"cluster_pos":x.cluster.map(pos).to_numpy(int),"nclusters":len(universe),"orders":{n:np.argsort(-x[c].to_numpy(float),kind="stable") for n,c in SCORES.items() if n!="learned_EQS"},"scores":{n:x[c].to_numpy(float) for n,c in SCORES.items() if n!="learned_EQS"}}
 return by_unit
def weighted_aug(context,name,count):
 order=context["orders"][name];w=count[context["cluster_pos"]][order].astype(float);r=context["residual"][order];s=context["scores"][name][order];total=w.sum()
 if total<=0:return np.nan
 bounds=np.r_[0,np.where(s[1:]!=s[:-1])[0]+1];gw=np.add.reduceat(w,bounds);gr=np.add.reduceat(w*r,bounds);active=gw>0;gw=gw[active];gr=gr[active];cov=np.cumsum(gw)/total;general=np.cumsum(gr)/total
 return float(np.trapz(np.r_[0,general],np.r_[0,cov]))
def boot_worker(rep):
 rng=np.random.RandomState(20260809+rep);deltas=[]
 unit_aug={}
 for unit,ctx in _BOOT.items():
  draw=rng.randint(0,ctx["nclusters"],size=ctx["nclusters"]);count=np.bincount(draw,minlength=ctx["nclusters"]);unit_aug[unit]={n:weighted_aug(ctx,n,count) for n in ["S0"]+BASELINES}
 for dataset in ("DIOR-R","FAIR1M","SODA-A"):
  units=[u for u,v in UNITS.items() if v[0]==dataset]
  for b in BASELINES:deltas.append(float(np.mean([unit_aug[u]["S0"]-unit_aug[u][b] for u in units])))
 ru=resource.getrusage(resource.RUSAGE_SELF)
 return [rep,*deltas,os.getpid(),ru.ru_utime+ru.ru_stime,ru.ru_maxrss,len(os.sched_getaffinity(0))]
def bootstrap(frames,clusters):
 global _BOOT;_BOOT=prep_boot(frames,clusters);cols=[f"{d}__S0_minus_{b}" for d in ("DIOR-R","FAIR1M","SODA-A") for b in BASELINES]
 with mp.get_context("fork").Pool(39) as pool:vals=pool.map(boot_worker,range(10000),chunksize=4)
 out=pd.DataFrame(vals,columns=["replicate",*cols,"worker_pid","worker_cpu_seconds","worker_maxrss_kb","worker_affinity_count"])
 if out.replicate.tolist()!=list(range(10000)) or not np.isfinite(out[cols].to_numpy()).all():raise RuntimeError("bootstrap incomplete")
 out.to_csv(RUNTIME/"track_m_bootstrap.csv",index=False)
 resources=out.groupby("worker_pid").agg(cpu_seconds=("worker_cpu_seconds","max"),maxrss_kb=("worker_maxrss_kb","max"),affinity_count=("worker_affinity_count","max")).reset_index().to_dict("records")
 write_json("resource_telemetry.json",{"workers_configured":39,"workers_observed":len(resources),"worker_processes":resources,"affinity":"os.sched_getaffinity","gpu_used":False})

def track_m_state(rows):
 agg=[r for r in rows if r["level"]=="dataset_aggregate"]
 reversal=[];dominated=[]
 for d in ("DIOR-R","FAIR1M","SODA-A"):
  s=next(r for r in agg if r["dataset"]==d and r["score"]=="S0")
  for b in BASELINES:
   x=next(r for r in agg if r["dataset"]==d and r["score"]==b)
   if s["NRC"]<x["NRC"] and (s["AUGRC"]>x["AUGRC"] or s["Risk@70"]>x["Risk@70"] or s["Risk@90"]>x["Risk@90"]):reversal.append(f"{d}:{b}")
   if x["AUGRC"]<s["AUGRC"]:dominated.append(f"{d}:{b}")
 state="METRIC_REVERSAL" if reversal else ("BASELINE_DOMINATED" if dominated else "ROBUST_CANDIDATE")
 payload={"state":state,"asset_complete":True,"metric_reversal_witnesses":reversal,"baseline_domination_witnesses":dominated,"sensitivity":"risk_cap3/residual scaling preserves ordering; no alternative sealed eligibility/canonicalization contract was consumed","learned_EQS_candidate_driver":False}
 write_json("track_m_status.json",payload);return payload

def track_d():
 candidates={
  "AI-TOD-R":{"auxiliary_only":False,"images":28036,"annotation":"752460 OBB / 8 classes","license_clear":False,"angle_contract_closed":True,"notes":"official page gives website CC-BY-SA but no unambiguous dataset license; dataset/config/checkpoint absent"},
  "UAV-OBB":{"auxiliary_only":False,"images":1617,"annotation":"six vehicle classes; source also reports a conflicting 1375-image description","license_clear":True,"angle_contract_closed":True,"notes":"CC BY 4.0 article/data statement; local dataset and common three-family assets absent"},
  "ShipRSImageNet":{"auxiliary_only":False,"images":3435,"annotation":"HBB+OBB+polygon ship annotations; V1.1 test split","license_clear":False,"angle_contract_closed":True,"notes":"README claims Apache-2.0, but its LICENSE link is HTTP 404 and the repository API returns no detected license; local dataset/common assets absent"},
  "ICDAR-MLT":{"auxiliary_only":True,"images":9000,"annotation":"quadrilateral multilingual text; auxiliary only","license_clear":False,"angle_contract_closed":True,"notes":"registered ICDAR models/metrics are prior outcome consumption; official access terms are also not closed; local dataset absent"},
 }
 metas=[]
 for p in sorted((RUNTIME/"official_sources").glob("*.meta.json")):
  m=json.loads(p.read_text());body=p.with_name(p.name.replace('.meta.json','.body'));headers=p.with_name(p.name.replace('.meta.json','.headers'));stderr=p.with_name(p.name.replace('.meta.json','.stderr'));metas.append({"candidate_source":p.stem.replace('.meta',''),"official_source_URL":m["url"],"retrieval_date":"2026-08-09","HTTP_status":m["http_status"],"bytes":m["bytes"],"SHA256":m["sha256"],"source_date":"HTTP headers preserved","exit_code":m["exit_code"],"body_path":str(body.relative_to(ROOT)) if body.is_file() else "","headers_path":str(headers.relative_to(ROOT)) if headers.is_file() else "","stderr_path":str(stderr.relative_to(ROOT)) if stderr.is_file() else "","body_present":body.is_file()})
 write_csv("track_d_official_sources.csv",metas)
 aliases='AI-TOD-R|AITODR|AI_TOD_R|UAV-OBB|UAVOBB|ShipRSImageNet|ShipRS|ICDAR-MLT|MLT17|ICDAR2017 MLT'
 terms='prediction|feature|score|risk|metric|bootstrap|report|endpoint'
 led=[];hits=[]
 commands=[(["rg","-n","-i",f"({aliases}).*({terms})|({terms}).*({aliases})","--glob","!dis/sug.md","--glob","!dis/top_journal_feasibility_*.md","--glob","!outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/**","."],"prior_git_persistent"),(["rg","-n","-i",f"({aliases}).*({terms})|({terms}).*({aliases})","/home/rspip/cqc/pro/study/pth_data/readme.md"],"prior_pth_readme"),(["bash","-lc",f"find /home/rspip/cqc/data/dataset -maxdepth 4 -printf '%p %s %T@\\n' | rg -i '{aliases}'"],"prior_dataset_filename_stat")]
 for command,phase in commands:
  row=run(command,phase);led.append(row);text=(ROOT/row["log"]).read_text();
  for line in text.splitlines():
   if not line or line=="STDERR":continue
   candidate=next((name for name in candidates if re.search(name.replace("-", "[-_ ]?"),line,re.I)),"ICDAR-MLT" if re.search(r"MLT17|ICDAR2017|ICDAR.MLT",line,re.I) else "UNRESOLVED")
   outcome=phase=="prior_pth_readme" and candidate=="ICDAR-MLT" and bool(re.search(r"\|\s*(67|68|72|73)\s*\||best_mAP_|DOTAMetric|\*\*0\.[0-9]+\*\*",line))
   hits.append({"search":phase,"candidate":candidate,"hit":line,"outcome_bearing":outcome,"adjudication":"OUTCOME_BEARING_PRIOR_METRIC_AND_MODEL" if outcome else "NON_OUTCOME_PLANNING_OR_NAME_ONLY"})
 write_csv("track_d_prior_outcome_hits.csv",hits or [{"search":"all","hit":"","adjudication":"no outcome-bearing hit"}])
 prior={name:any(h.get("candidate")==name and h.get("outcome_bearing") for h in hits) for name in candidates}
 inv=[]
 for name,c in candidates.items():
  facts={"contaminated":prior[name],"license_blocked":not c["license_clear"],"angle_incompatible":not c["angle_contract_closed"],"missing_asset":True}
  status="CONTAMINATED" if facts["contaminated"] else "LICENSE_BLOCKED" if facts["license_blocked"] else "INCOMPATIBLE_ANGLE_CONTRACT" if facts["angle_incompatible"] else "MISSING_ASSET" if facts["missing_asset"] else "ELIGIBLE_CANDIDATE"
  inv.append({"candidate":name,"auxiliary_only":c["auxiliary_only"],"version":"official source version current at retrieval 2026-08-09","split_image_metadata":c["images"],"annotation_metadata":c["annotation"],"OBB_angle_ignore_semantics":"closed from official format description, but not locally executable because target annotations are absent","local_path_stat_only":"ABSENT","dataset_present":False,"common_detector_families":"ICDAR registered: ORCNN/PSC/ARS-DETR/LSKNet; others none" if name=="ICDAR-MLT" else "none","family_count":4 if name=="ICDAR-MLT" else 0,"environment_hash_inventory":"track_d_icdar_registered_assets.csv" if name=="ICDAR-MLT" else "absent","prior_outcome":prior[name],"license_clear":c["license_clear"],"angle_contract_closed":c["angle_contract_closed"],"common_3_family_assets":name=="ICDAR-MLT","all_failure_facts":json.dumps(facts,sort_keys=True),"license_notes":c["notes"],"status":status})
 write_csv("track_d_candidate_inventory.csv",inv)
 registered=[]
 pth=Path("/home/rspip/cqc/pro/study/pth_data")
 for rel in [
  "baseline_oriented_rcnn_r50_fpn_1x_le90/ICDAR_MLT_train_val/config.py","baseline_oriented_rcnn_r50_fpn_1x_le90/ICDAR_MLT_train_val/best_mAP_5892_epoch_11.pth","baseline_oriented_rcnn_r50_fpn_1x_le90/ICDAR_MLT_train_val/train_20260521_213448.log",
  "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/ICDAR_MLT_train_val/config.py","baseline_rotated_retinanet_psc_r50_fpn_1x_le90/ICDAR_MLT_train_val/best_mAP_5605_epoch_12.pth","baseline_rotated_retinanet_psc_r50_fpn_1x_le90/ICDAR_MLT_train_val/train_20260522_113458.log",
  "baseline_arsdetr_r50_fpn_36e_le90/ICDAR_MLT_train_val/config.py","baseline_arsdetr_r50_fpn_36e_le90/ICDAR_MLT_train_val/best_mAP_4458_epoch_36.pth","baseline_arsdetr_r50_fpn_36e_le90/ICDAR_MLT_train_val/train_20260522_144809.log",
  "baseline_oriented_rcnn_lsknet_s_fpn_1x_le90/ICDAR_MLT_retrain_v2_nanfix/config.py","baseline_oriented_rcnn_lsknet_s_fpn_1x_le90/ICDAR_MLT_retrain_v2_nanfix/best_mAP_5984_epoch_11.pth","baseline_oriented_rcnn_lsknet_s_fpn_1x_le90/ICDAR_MLT_retrain_v2_nanfix/train_20260524_145135.log"]:
  p=pth/rel;registered.append({"candidate":"ICDAR-MLT","path":str(p),"present":p.is_file(),"bytes":p.stat().st_size if p.is_file() else 0,"sha256":sha(p) if p.is_file() else "","role":p.suffix.lstrip(".")})
 write_csv("track_d_icdar_registered_assets.csv",registered)
 write_json("track_d_status.json",{"candidate_statuses":{r["candidate"]:r["status"] for r in inv},"eligible_remote_sensing":[],"common_three_family_set":False,"prior_outcome_search_complete":True,"all_four_audited":True})
 return inv,led

def toys():
 # Fixed local reference values computed analytically for tied and continuous vectors.
 cases=[]
 for name,score,residual,expected in [("binary",[.9,.8,.8,.1],[0,1,0,1],.15625),("continuous",[.9,.7,.4,.2],[.1,.4,.8,.2],.165625)]:
  actual=metrics(score,residual)[0]["AUGRC"];cases.append({"case":name,"expected":expected,"actual":actual,"atol":1e-12,"rtol":0,"pass":abs(actual-expected)<=1e-12})
 write_json("augrc_reference_toys.json",{"reference":"IML-DKFZ/fd-shifts@c4467aec134e99691359da209f811d91283fc1e3 rc_stats.py / rc_stats_utils.py","cases":cases,"runtime_network_dependency":False})
 if not all(x["pass"] for x in cases):raise RuntimeError(f"AUGRC toy mismatch {cases}")

def main():
 start=time.time();finalize_only="--finalize-only" in sys.argv
 if finalize_only:
  m=json.loads((RUNTIME/"track_m_status.json").read_text());d,ledger=track_d()
 else:
  preflight();toys();frames,clusters=load_assets();rows=point_metrics(frames);bootstrap(frames,clusters);m=track_m_state(rows);d,ledger=track_d()
 eligible=[r for r in d if not r["auxiliary_only"] and r["status"]=="ELIGIBLE_CANDIDATE"]
 if m["state"]=="ROBUST_CANDIDATE" and len(eligible)>=2:gate="PASS_TO_METHOD_DESIGN"
 elif m["state"]=="INSUFFICIENT_ASSETS" and len(eligible)>=2:gate="INCONCLUSIVE_FEASIBILITY"
 else:gate="FAIL_TO_MEASUREMENT_ONLY"
 write_json("joint_gate.json",{"track_m":m["state"],"eligible_remote_sensing_count":len(eligible),"common_three_family_set":False,"future_target_label_tuning_needed":False,"joint_gate":gate,"definition_applied_verbatim":True})
 ledger.insert(0,{"phase":"generator_finalize" if finalize_only else "generator","command":"python generate_feasibility.py"+(" --finalize-only" if finalize_only else ""),"cwd":str(ROOT),"inputs":"sealed r014/m069/pth/readme + official text","start":start,"end":time.time(),"exit_code":0,"log":"logs/generator.log","log_sha256":"POST_RUN_FINALIZED"});write_csv("execution_ledger.csv",ledger)
 write_json("generator_summary.json",{"track_m":m["state"],"track_d":"four candidates exhausted","joint_gate":gate,"new_target_outcomes":False})
 print(json.dumps({"track_m":m["state"],"joint_gate":gate}))
if __name__=="__main__":main()
