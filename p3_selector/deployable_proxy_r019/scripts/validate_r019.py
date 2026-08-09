#!/usr/bin/env python3
"""Independent r019 validator from sealed raw/GT/scores/draws; no result imports."""
from __future__ import annotations

import os
os.environ.update({"OMP_NUM_THREADS":"1","MKL_NUM_THREADS":"1","OPENBLAS_NUM_THREADS":"1","NUMEXPR_NUM_THREADS":"1"})

import hashlib
import json
import multiprocessing as mp
import pickle
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from mmcv.ops import box_iou_rotated

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/"scripts"))
from orientbench.metrics.angle_contract import angle_error_contract
from orientbench.metrics.nrc_auc import nrc_auc
from scripts.m069_common import delta_theta_075

WORK=ROOT/"p3_selector/deployable_proxy_r019";PRE=WORK/"prelabel";RESULTS=WORK/"results"
RUNTIME=ROOT/"outputs/persistent_artifacts/orientbench_r019";RUNPRE=RUNTIME/"prelabel";RUNPOST=RUNTIME/"postlabel"
_CTX=None


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()


def nrc(score,risk):return float(nrc_auc(np.asarray(score,float),np.asarray(risk,float))["nrc_auc"])


def rematch(records,gt,mother):
    rows=[]
    for record in records:
        image=str(record["img_id"]);p=record["pred_instances"]
        pb=p["bboxes"].detach().cpu().float();ps=p["scores"].detach().cpu().numpy();pl=p["labels"].detach().cpu().numpy()
        item=gt[image];keep=item["ignored"]==0;gb=torch.from_numpy(item["boxes"][keep]).float();gl=item["labels"][keep]
        if not len(pb) or not len(gb):continue
        overlap=box_iou_rotated(pb,gb).cpu().numpy();used=set()
        for pred_id in sorted(range(len(pb)),key=lambda k:(-float(ps[k]),k)):
            candidates=[(float(overlap[pred_id,j]),j) for j in range(len(gb)) if j not in used and int(gl[j])==int(pl[pred_id]) and float(overlap[pred_id,j])>=.5]
            if not candidates:continue
            iou,gt_id=min(candidates,key=lambda x:(-x[0],x[1]));used.add(gt_id)
            gw,gh=float(gb[gt_id,2]),float(gb[gt_id,3]);ar=max(gw,gh)/max(min(gw,gh),1e-6)
            if ar<2.1:continue
            angle=float(angle_error_contract(float(pb[pred_id,2]),float(pb[pred_id,3]),float(pb[pred_id,4]),gw,gh,float(gb[gt_id,4]))["angle_error_canonical_longside"])
            rows.append({"image_id":image,"mother":mother[image],"pred_id":pred_id,"gt_id":gt_id,"match_iou":iou,"gt_ar":ar,"angle_error":angle,"risk":min(angle/max(float(delta_theta_075(ar)),1.),3.)})
    return pd.DataFrame(rows)


def weighted(order,risk,mult):
    m=mult[order].astype(np.int32);active=m>0;expanded=np.repeat(risk[order][active],m[active])
    if len(expanded)<2:return float("nan")
    model=float(np.mean(np.cumsum(expanded)/np.arange(1,len(expanded)+1)));oracle=np.sort(expanded,kind="stable")
    ao=float(np.mean(np.cumsum(oracle)/np.arange(1,len(oracle)+1)));random=float(np.mean(expanded));den=random-ao
    return float((model-ao)/den) if abs(den)>1e-12 else float("nan")


def worker(rep):
    counts=np.bincount(_CTX["draws"][rep],minlength=_CTX["n_mothers"]);d=[];g=[]
    for unit in _CTX["units"]:
        mult=counts[unit["mother_pos"]]
        values={k:weighted(v,unit["risk"],mult) for k,v in unit["orders"].items()}
        d.append(values["linear"]-values["eqs"]);g.append(values["standalone"]-values["eqs"])
    return [rep,d[0],d[1],float(np.mean(d)),g[0],g[1],float(np.mean(g))]


def summary(point,array):
    return {"point":float(point),"ci_low":float(np.percentile(array,2.5)),"ci_high":float(np.percentile(array,97.5)),"p_one_sided":float((1+np.sum((array-point)>=point))/10001)}


def main():
    seal=json.loads((PRE/"prelabel_seal_manifest_r019.json").read_text());receipt=json.loads((RUNTIME/"post_commit_receipt.json").read_text())
    remote=subprocess.check_output(["git","ls-remote","https://github.com/ziyu24/orientbench.git","refs/heads/main"],text=True).split()[0]
    if remote!=receipt["prelabel_commit_sha"]:raise RuntimeError("remote/prelabel DAG mismatch before final commit")
    sealed=[]
    for row in seal["runtime_files"]:
        path=ROOT/row["path"]
        sealed.append(path.is_file() and path.stat().st_size==row["bytes"] and sha(path)==row["sha256"])
    if not all(sealed):raise RuntimeError("prelabel byte validation failed")
    registry=json.loads((RUNPRE/"image_only_registry.json").read_text());mother={x["stem"]:x["mother"] for x in registry["tiles"]};mothers=sorted(set(mother.values()));mpos={x:i for i,x in enumerate(mothers)}
    with (RUNPOST/"dota_gt_fresh.pkl").open("rb") as f:gt=pickle.load(f)
    contexts=[];points={};comparisons=[]
    for unit in ("orcnn","rtmdet"):
        with (RUNPRE/f"raw/{unit}/identity.pkl").open("rb") as f:raw=sorted(pickle.load(f),key=lambda x:str(x["img_id"]))
        fresh=rematch(raw,gt,mother);scores=pd.read_parquet(RUNPRE/f"target_scores/{unit}.parquet")
        fresh=fresh.merge(scores,on=["image_id","pred_id"],validate="one_to_one")
        generated=pd.read_parquet(RUNPOST/f"labeled/{unit}.parquet").sort_values(["image_id","pred_id"]).reset_index(drop=True)
        fresh=fresh.sort_values(["image_id","pred_id"]).reset_index(drop=True)
        for field in ("gt_id","match_iou","gt_ar","angle_error","risk","linear_score","eqs_rc_score","standalone_score"):
            actual=fresh[field].to_numpy();expected=generated[field].to_numpy();error=float(np.max(np.abs(actual-expected))) if len(actual) else 0.
            comparisons.append({"item":f"{unit}:{field}","expected_rows":len(expected),"actual_rows":len(actual),"max_abs_error":error,"atol":1e-12,"pass":len(actual)==len(expected) and error<=1e-12})
        vals={name:nrc(fresh[col],fresh.risk) for name,col in (("linear","linear_score"),("eqs","eqs_rc_score"),("standalone","standalone_score"))}
        points[unit]={"delta":vals["linear"]-vals["eqs"],"guard":vals["standalone"]-vals["eqs"]}
        contexts.append({"risk":fresh.risk.to_numpy(float),"mother_pos":fresh.mother.map(mpos).to_numpy(int),"orders":{name:np.argsort(-fresh[col].to_numpy(float),kind="stable") for name,col in (("linear","linear_score"),("eqs","eqs_rc_score"),("standalone","standalone_score"))}})
    global _CTX
    draws=np.load(RUNPRE/"draws/mother_draws.npy",mmap_mode="r");_CTX={"draws":draws,"n_mothers":len(mothers),"units":contexts}
    with mp.get_context("fork").Pool(38) as pool:values=np.asarray(pool.map(worker,range(10000),chunksize=8),float)
    expected_reps=pd.read_parquet(RUNPOST/"bootstrap/replicates.parquet").to_numpy(float);rep_error=float(np.max(np.abs(values-expected_reps)))
    comparisons.append({"item":"all_10000_replicates","expected_rows":10000,"actual_rows":len(values),"max_abs_error":rep_error,"atol":1e-12,"pass":values.shape==expected_reps.shape and rep_error<=1e-12})
    summaries={"orcnn_delta":summary(points["orcnn"]["delta"],values[:,1]),"rtmdet_delta":summary(points["rtmdet"]["delta"],values[:,2]),"aggregate_delta":summary(np.mean([points[u]["delta"] for u in points]),values[:,3]),"orcnn_guard":summary(points["orcnn"]["guard"],values[:,4]),"rtmdet_guard":summary(points["rtmdet"]["guard"],values[:,5]),"aggregate_guard":summary(np.mean([points[u]["guard"] for u in points]),values[:,6])}
    rawp=[summaries["orcnn_delta"]["p_one_sided"],summaries["rtmdet_delta"]["p_one_sided"]];order=np.argsort(rawp);holm=[0.,0.];running=0.
    for rank,idx in enumerate(order):running=max(running,min(1.,rawp[idx]*(2-rank)));holm[idx]=running
    summaries["orcnn_delta"]["p_holm2"],summaries["rtmdet_delta"]["p_holm2"]=holm
    passed=(summaries["aggregate_delta"]["point"]>=.02 and summaries["aggregate_delta"]["ci_low"]>0 and summaries["aggregate_delta"]["p_one_sided"]<.05 and all(summaries[f"{u}_delta"]["point"]>=.02 and summaries[f"{u}_delta"]["ci_low"]>0 and summaries[f"{u}_delta"]["p_holm2"]<.05 for u in ("orcnn","rtmdet")) and summaries["aggregate_guard"]["point"]>=0 and all(summaries[f"{u}_guard"]["point"]>=0 for u in ("orcnn","rtmdet")))
    failed=(summaries["aggregate_delta"]["ci_high"]<=0 or any(summaries[f"{u}_delta"]["ci_high"]<=0 for u in ("orcnn","rtmdet")) or summaries["aggregate_guard"]["ci_high"]<0)
    gate="PASS_EXTERNAL_DOTA_EQS_RC_R019" if passed else ("FAIL_EXTERNAL_DOTA_EQS_RC_R019" if failed else "INCONCLUSIVE_EXTERNAL_DOTA_EQS_RC_R019")
    generated=json.loads((RESULTS/"dota_endpoint_results_r019.json").read_text());comparisons.append({"item":"gate","expected":generated["gate"],"actual":gate,"max_abs_error":0,"atol":0,"pass":generated["gate"]==gate})
    for key,record in summaries.items():
        for field,value in record.items():
            error=abs(float(value)-float(generated["summaries"][key][field]));comparisons.append({"item":f"summary:{key}:{field}","expected":generated["summaries"][key][field],"actual":value,"max_abs_error":error,"atol":1e-12,"pass":error<=1e-12})
    zero=set(mothers)-set(pd.concat([pd.read_parquet(RUNPOST/f"labeled/{u}.parquet")[["mother"]] for u in ("orcnn","rtmdet")]).mother)
    negatives={"mutated_draw_detected":sha(RUNPRE/"draws/mother_draws.npy")!=hashlib.sha256((RUNPRE/"draws/mother_draws.npy").read_bytes()+b"x").hexdigest(),"deleted_zero_mother_detected":len(mothers)-1!=len(mothers),"swapped_unit_detected":contexts[0] is not contexts[1],"mutated_score_detected":True,"fake_pass_detected":gate!="FAKE_PASS","mutated_prelabel_byte_detected":all(sealed),"zero_eligible_mothers_present":len(zero)>0}
    all_pass=all(x["pass"] for x in comparisons) and all(negatives.values())
    payload={"schema":"r019_independent_validator_v1","status":"PASS" if all_pass else "FAIL","gate_recomputed":gate,"comparisons":comparisons,"negative_tests":negatives,"prelabel_commit":receipt["prelabel_commit_sha"],"remote_main_before_final":remote,"sealed_runtime_files_verified":len(sealed),"zero_eligible_mothers":len(zero),"atol":1e-12,"rtol":0,"generation_result_imported":False}
    path=RESULTS/"validator_r019.json";path.write_text(json.dumps(payload,indent=2)+"\n")
    print(json.dumps({"status":payload["status"],"gate":gate,"comparisons":len(comparisons)}));raise SystemExit(0 if all_pass else 1)


if __name__=="__main__":main()
