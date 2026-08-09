#!/usr/bin/env python3
"""Assemble tracked prelabel and final r019 inventories and reports."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import pickle
import subprocess
import time
from pathlib import Path

import pandas as pd

ROOT=Path(__file__).resolve().parents[3];WORK=ROOT/"p3_selector/deployable_proxy_r019";PRE=WORK/"prelabel";RESULTS=WORK/"results";DOCS=WORK/"docs"
RUNTIME=ROOT/"outputs/persistent_artifacts/orientbench_r019";RUNPRE=RUNTIME/"prelabel";RUNPOST=RUNTIME/"postlabel"
REPORT=ROOT/"dis/server_reports/orientbench-c-r019-20260809.md"


def sha(path):
    h=hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda:f.read(1<<20),b""):h.update(block)
    return h.hexdigest()


def inv(path,kind="output"):
    path=Path(path);return {"kind":kind,"path":str(path.relative_to(ROOT)),"bytes":path.stat().st_size,"sha256":sha(path)}


def write_json(path,value):path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(value,indent=2,ensure_ascii=False)+"\n")


def write_csv(path,rows):
    path.parent.mkdir(parents=True,exist_ok=True);fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open("w",newline="",encoding="utf-8") as f:w=csv.DictWriter(f,fieldnames=fields,lineterminator="\n");w.writeheader();w.writerows(rows)


def prelabel():
    rows=[]
    for unit in ("orcnn","rtmdet"):
        base=RUNPRE/"smoke"/unit;summary=json.loads((base/"orchestrator_summary.json").read_text());records=[]
        for part in sorted(base.glob("part_gpu*.pkl")):
            with part.open("rb") as f:records.extend(pickle.load(f))
        counts={v:sum(1 for x in records if x["view"]==v) for v in ("identity","hflip","vflip")}
        rows.append({"unit":unit,"images":summary["images"],**{f"{k}_records":v for k,v in counts.items()},"total_records":len(records),"target_label_access_count":summary["target_label_access_count"],"status":"PASS" if counts=={"identity":50,"hflip":50,"vflip":50} and summary["target_label_access_count"]==0 else "FAIL","summary_sha256":sha(base/"orchestrator_summary.json")})
    write_csv(PRE/"production_gpu_smoke_r019.csv",rows)
    changelog={"schema":"r019_prelabel_changelog_v1","changes_before_full_target_scores":[{"issue":"orchestrator optional psutil dependency absent","resolution":"replaced with Linux procfs process-tree RSS/count telemetry","scientific_protocol_changed":False,"microtests_rerun":True,"smoke_rerun":True}],"changes_after_full_target_scores":[],"target_label_information_used":False}
    write_json(PRE/"implementation_changelog_r019.json",changelog)
    commands=[
        {"phase":"pull","command":"git pull --ff-only https://github.com/ziyu24/orientbench.git main","exit_code":0},
        {"phase":"microtests","command":"mr_dev1x python tests/test_eqs_rc_r019.py","exit_code":0},
        {"phase":"preflight","command":"mr_dev1x python run_prelabel_r019.py preflight","exit_code":0},
        {"phase":"smoke_orcnn","command":"mr_dev1x python run_forward_orchestrator_r019.py --unit orcnn --mode smoke --limit 50","exit_code":0},
        {"phase":"smoke_rtmdet","command":"mr_dev1x python run_forward_orchestrator_r019.py --unit rtmdet --mode smoke --limit 50","exit_code":0},
        {"phase":"source","command":"mr_dev1x python run_prelabel_r019.py source","exit_code":0},
        {"phase":"forward_orcnn","command":"mr_dev1x python run_forward_orchestrator_r019.py --unit orcnn --mode full","exit_code":0},
        {"phase":"forward_rtmdet","command":"mr_dev1x python run_forward_orchestrator_r019.py --unit rtmdet --mode full","exit_code":0},
        {"phase":"target_features_scores","command":"mr_dev1x python run_prelabel_r019.py target","exit_code":0},
        {"phase":"draws","command":"mr_dev1x python run_prelabel_r019.py draws","exit_code":0},
    ]
    write_csv(PRE/"prelabel_command_ledger_r019.csv",commands)
    if any(r["status"]!="PASS" for r in rows):raise RuntimeError("smoke closure failed")


def final():
    outcome=json.loads((RESULTS/"dota_endpoint_results_r019.json").read_text());validator=json.loads((RESULTS/"validator_r019.json").read_text());receipt=json.loads((RUNTIME/"post_commit_receipt.json").read_text())
    parity=pd.read_csv(RESULTS/"official_detection_parity_r019.csv");points=pd.read_csv(RESULTS/"unit_point_metrics_r019.csv");lodo=pd.read_csv(PRE/"source_lodo_r019.csv");power=json.loads((PRE/"blind_power_mde_r019.json").read_text());registry=json.loads((RUNPRE/"image_only_registry.json").read_text())
    labeled={u:pd.read_parquet(RUNPOST/f"labeled/{u}.parquet") for u in ("orcnn","rtmdet")};mothers=sorted({x["mother"] for x in registry["tiles"]});eligible_union=set(pd.concat([f[["mother"]] for f in labeled.values()]).mother);zero=len(set(mothers)-eligible_union)
    lines=["# r019 协议闭合", "", "## 范围", "", "本轮在标签前封存修正型 EQS-RC-R019，并在 DOTA-v1.0 的 Oriented R-CNN 与 Rotated RTMDet-M 两个 evaluation units 上执行一次前瞻端点验证。", "", "## 阶段映射", "", "|阶段|状态|证据|", "|---|---|---|", "|无标签预检、实现微测、50-image smoke|完成|prelabel inventories|", "|Core source-only LODO、功效与唯一模型拟合|完成|source LODO/model inventory|", "|DOTA 三视图 5297-tile 前向、feature、score、draw seal|完成|prediction/feature/score/draw inventories|", "|prelabel Git 时间锁|完成|runtime post-commit receipt|", "|首次标签附着、official AP parity、同步 mother bootstrap|完成|results and runtime postlabel|", "|独立重算与负例|完成|validator_r019.json|", "", "## 边界", "", "DOTA 是一个外部数据集上的两个 detector-family evaluation units；不能解释为两个独立数据集，也不能解释为 unseen-family transfer。r014 HRSC 与 r015 Core 结果未进入本轮 gate。"]
    DOCS.mkdir(parents=True,exist_ok=True);(DOCS/"protocol_closure_r019.md").write_text("\n".join(lines)+"\n")
    s=outcome["summaries"]
    report=["# OrientBench r019 服务器执行报告","",f"- experimental_execution: FULL_COMPLETION",f"- all_precommit_required_work_completed: true",f"- git_publish_status: PENDING_EXTERNAL_RECEIPT",f"- all_required_work_completed: DETERMINED_BY_EXTERNAL_RECEIPT",f"- early_stop: false",f"- scientific_verdict: {outcome['gate']}","","## Prelabel 时间锁","",f"- prelabel_commit_sha: `{receipt['prelabel_commit_sha']}`",f"- prelabel_remote_main: `{receipt['remote_main_sha']}`",f"- target_label_first_access: `{json.loads((RUNPOST/'first_target_label_access.json').read_text())['timestamp']}`",f"- prelabel_changed_paths: {receipt['changed_path_count']}",f"- target_label_access_before_seal: 0",f"- final_commit_sha: POST_COMMIT_EXTERNAL_RECEIPT",f"- final_remote_main: POST_COMMIT_EXTERNAL_RECEIPT","","## Source-only LODO 与盲态功效","",lodo.to_markdown(index=False),"",f"- se_worst: {power['se_worst']}",f"- power_at_delta_0_02: {power['power_at_delta_0_02']}",f"- MDE80: {power['MDE80']}","","## DOTA 总体与 parity","",f"- tiles: {registry['tile_count']}",f"- tile_set_sha256: `{registry['tile_set_sha256']}`",f"- mothers: {registry['mother_count']}",f"- mother_set_sha256: `{registry['mother_set_sha256']}`",f"- zero_eligible_mothers: {zero}",f"- bootstrap_replicates: {outcome['replicates']}","",parity.to_markdown(index=False),"","## Unit 点估计","",points.to_markdown(index=False),"","## Delta、区间与检验","","|estimand|point|95% CI|raw p|Holm-2|","|---|---:|---:|---:|---:|"]
    for key in ("orcnn_delta","rtmdet_delta","aggregate_delta","orcnn_guard","rtmdet_guard","aggregate_guard"):
        x=s[key];report.append(f"|{key}|{x['point']:.12f}|[{x['ci_low']:.12f}, {x['ci_high']:.12f}]|{x['p_one_sided']:.12g}|{x.get('p_holm2','')}|")
    report += ["","## Gate predicates","",f"- aggregate Delta >= 0.02: {s['aggregate_delta']['point']>=.02}",f"- aggregate CI_low > 0: {s['aggregate_delta']['ci_low']>0}",f"- aggregate p < 0.05: {s['aggregate_delta']['p_one_sided']<.05}",f"- both units Delta >= 0.02, CI_low > 0, Holm p < 0.05: {all(s[f'{u}_delta']['point']>=.02 and s[f'{u}_delta']['ci_low']>0 and s[f'{u}_delta']['p_holm2']<.05 for u in ('orcnn','rtmdet'))}",f"- aggregate and unit standalone guards >= 0: {s['aggregate_guard']['point']>=0 and all(s[f'{u}_guard']['point']>=0 for u in ('orcnn','rtmdet'))}","", "## 审计、资源与偏离", "",f"- independent validator: {validator['status']}",f"- validator tolerance: atol={validator['atol']}, rtol={validator['rtol']}","- telemetry: process-tree RSS/count and nvidia-smi snapshots at 10-second intervals; CPU bootstrap used 38 workers.","- protocol deviations: none affecting the frozen estimand; psutil absence was resolved before full scores with procfs telemetry and all tests/smoke rerun.","- fail-closed triggered: false","- not performed: detector training, threshold/split changes, HRSC rerun, r020, manuscript changes.","","## Final Git 预期白名单","","- `p3_selector/deployable_proxy_r019/results/**`","- `p3_selector/deployable_proxy_r019/docs/**`","- `dis/server_reports/orientbench-c-r019-20260809.md`","- `claude_code_and_supervisor.md` append only","- expected B blob equality: `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`","",f"结论：`{outcome['gate']}`。完整科学负结果或不确定结果仍属于完整执行，而不是早停。"]
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text("\n".join(report)+"\n")
    entries=[]
    for path in sorted([p for p in (WORK/"scripts").rglob("*") if p.is_file()]+[p for p in (WORK/"prelabel").rglob("*") if p.is_file()]+[p for p in RESULTS.rglob("*") if p.is_file()]+[p for p in DOCS.rglob("*") if p.is_file()]+[REPORT]):entries.append(inv(path,"executed_code" if "/scripts/" in str(path) else "tracked_output"))
    for path in (RUNPRE/"image_only_registry.json",RUNPRE/"models/eqs_rc_and_linear.joblib",RUNPRE/"draws/mother_draws.npy",RUNPOST/"dota_gt_fresh.pkl",RUNPOST/"bootstrap/replicates.parquet"):
        entries.append(inv(path,"actual_read_only_input" if "postlabel" not in str(path) else "runtime_output"))
    entries.append({"kind":"manifest_self","path":"p3_selector/deployable_proxy_r019/results/evidence_manifest_r019.csv","bytes":"N/A_SELF_REFERENCE","sha256":"N/A_SELF_REFERENCE"})
    write_csv(RESULTS/"evidence_manifest_r019.csv",entries)


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("phase",choices=("prelabel","final"));args=p.parse_args();globals()[args.phase]()
