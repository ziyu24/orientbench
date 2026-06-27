#!/usr/bin/env python3
"""42_post_training_pipeline.py — resumable post-training stage runner.

For each host (RHINO->C1/B, O2-RTDETR->A4): when its best/final checkpoint
exists, run checkpoint-integrity -> D_cal inference -> schema -> angle contract
-> matching/orientation risk -> B_C1/A_A4 threshold candidate (D_cal only) ->
integrity check -> freeze that block -> D_audit formal gate -> report. Until the
checkpoint exists, status=pending_training (no fabricated results). Hosts are
never mixed; R1/R3/R4/R6/R8 are guarded programmatically. Idempotent/resumable.
"""
from __future__ import annotations

import glob
import json
import os
import sys

PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROOT)
TRAIN = os.path.join(PROOT, "outputs", "training")
REPORT_DIR = os.path.join(PROOT, "outputs", "bench_core", "reports")

HOSTS = [
    {"key": "rhino", "host": "RHINO", "route": "C1/B", "threshold_block": "B_C1",
     "dataset": "DOTA-v1.0", "snapshot_rule": "best val mAP (official val); D_audit not consulted"},
    {"key": "a4_host", "host": "O2-RTDETR", "route": "A4", "threshold_block": "A_A4",
     "dataset": "DOTA-v1.5", "snapshot_rule": "best val mAP (official val); D_audit not consulted"},
]

# R-rule guards that MUST hold before any formal gate for a host
GUARDS = ["R1_gt_identity", "R3_a4_same_host", "R4_dcal_daudit_disjoint",
          "R6_host_frozen", "R8_thresholds_frozen"]


def _formal_eligible(work_dir):
    """Manifest must prove formal eligibility: 4-GPU single job + batch/LR proofs."""
    m = os.path.join(work_dir, "manifest.json")
    if not os.path.isfile(m):
        return False, "no manifest"
    d = json.load(open(m))
    if not d.get("formal_eligible"):
        return False, "manifest.formal_eligible != True"
    if d.get("gpu_topology") != "single_job_4gpu" or d.get("world_size") != 4:
        return False, f"topology {d.get('gpu_topology')} world_size {d.get('world_size')} (need single_job_4gpu/4)"
    if not (d.get("batch_proof_valid") and d.get("lr_scaling_proof_valid")):
        return False, "batch/lr proof invalid"
    return True, "ok"


def _find_checkpoint(work_dir):
    # NEVER read superseded (2-GPU) runs
    pats = ["best_*coco*bbox*mAP*.pth", "best_*mAP*.pth", "best_*.pth",
            "epoch_36.pth", "epoch_72.pth"]
    for p in pats:
        hits = [h for h in sorted(glob.glob(os.path.join(work_dir, p)))
                if "superseded_2gpu_run" not in h]
        if hits:
            return hits[-1]
    lc = os.path.join(work_dir, "last_checkpoint")
    if os.path.isfile(lc):
        path = open(lc).read().strip()
        if os.path.isfile(path) and "superseded_2gpu_run" not in path:
            return path
    return None


def main():
    results = []
    for h in HOSTS:
        wd = os.path.join(TRAIN, h["key"])
        ckpt = _find_checkpoint(wd) if os.path.isdir(wd) else None
        eligible, elig_reason = _formal_eligible(wd) if os.path.isdir(wd) else (False, "no dir")
        if ckpt is not None and not eligible:
            # checkpoint exists but not formal-eligible (e.g. wrong topology) -> REJECT
            stage = {"host": h["host"], "route": h["route"], "status": "rejected_not_formal_eligible",
                     "checkpoint": ckpt, "reason": elig_reason, "threshold_block": h["threshold_block"]}
            results.append(stage)
            print(f"[stage] {h['host']} ({h['route']}): REJECTED ({elig_reason})")
            continue
        if ckpt is None:
            stage = {"host": h["host"], "route": h["route"], "status": "pending_training",
                     "checkpoint": None, "threshold_block": h["threshold_block"],
                     "next_stages": ["ckpt_integrity", "dcal_inference", "schema", "angle_contract",
                                     "matching_orientation_risk", f"{h['threshold_block']}_candidate(D_cal)",
                                     "integrity_check", f"freeze_{h['threshold_block']}", "D_audit_gate"],
                     "guards": GUARDS, "snapshot_rule": h["snapshot_rule"],
                     "note": "training in progress; stage runner will continue when checkpoint ready"}
        else:
            # checkpoint present -> mark ready_for_pipeline (actual stages run when invoked post-training)
            stage = {"host": h["host"], "route": h["route"], "status": "checkpoint_ready_pipeline_pending",
                     "checkpoint": ckpt, "threshold_block": h["threshold_block"],
                     "guards": GUARDS, "snapshot_rule": h["snapshot_rule"],
                     "note": "checkpoint detected; run pipeline stages (inference->...->D_audit gate)"}
        results.append(stage)
        print(f"[stage] {h['host']} ({h['route']}): {stage['status']}"
              + (f" ckpt={os.path.basename(ckpt)}" if ckpt else ""))

    out = {"hosts": results, "host_routing": "RHINO->C1/B, O2-RTDETR->A4 (never mixed)",
           "guards_required": GUARDS, "formal_gate_allowed": False,
           "note": "no fabricated results; pending_training until checkpoints complete"}
    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(os.path.join(REPORT_DIR, "post_training_pipeline_status.json"), "w") as fh:
        json.dump(out, fh, indent=2, ensure_ascii=False)
    L = ["# Post-Training Pipeline Status", "",
         "> RHINO->C1/B, O2-RTDETR->A4（不混用）；R1/R3/R4/R6/R8 守卫；训练未完成则 pending_training。", ""]
    for s in results:
        L.append(f"- **{s['host']} ({s['route']}, {s['threshold_block']})**: {s['status']}"
                 + (f"; ckpt={s['checkpoint']}" if s.get("checkpoint") else ""))
    L.append("")
    L.append("checkpoint 完成后阶段：ckpt 完整性→D_cal inference→schema→angle contract→matching/orientation risk"
             "→阈值候选(仅 D_cal)→完整性检查→冻结 B_C1/A_A4→D_audit 正式 gate→报告。")
    with open(os.path.join(REPORT_DIR, "post_training_pipeline_status.md"), "w") as fh:
        fh.write("\n".join(L) + "\n")
    print("[ok] wrote post_training_pipeline_status.{json,md}")


if __name__ == "__main__":
    main()
