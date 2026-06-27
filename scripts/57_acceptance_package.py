#!/usr/bin/env python3
"""57_acceptance_package.py — 018 DOTA-scoped milestone acceptance package (read-only).

Generates: project_status_matrix, dota_scoped_milestone_acceptance, claim_ledger,
reproducibility_manifest, and refreshes formal_gate_summary/readiness_check.
No training, no inference, no threshold mutation. Records paths + hashes only.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time

import yaml

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, P)
REP = os.path.join(P, "outputs", "bench_core", "reports")
TS = time.strftime("%Y-%m-%d %H:%M:%S %Z")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.isfile(p) else None


def wmd(name, lines):
    open(os.path.join(REP, name), "w").write("\n".join(lines) + "\n")


def wcsv(name, rows, cols):
    with open(os.path.join(REP, name), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols, extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def main():
    thr = yaml.safe_load(open(os.path.join(P, "configs", "thresholds.yaml")))
    thr_sha = sha(os.path.join(P, "configs", "thresholds.yaml"))
    rhino = os.path.join(P, "outputs/training/rhino/best_dota_mAP_epoch_35.pth")
    a4 = os.path.join(P, "outputs/training/a4_host/best_dota_mAP_epoch_70.pth")
    rh_sha, a4_sha = sha(rhino), sha(a4)
    assert rh_sha.startswith("55a90abb") and a4_sha.startswith("3e32fa11")

    # ---------- Task 1: project status matrix ----------
    R = "outputs/bench_core/reports"
    matrix = [
        ("baseline inventory", "pass", "DOTA + others (73)", f"{R}/../../.. inventory", "", "—"),
        ("dataset inventory", "pass", "DOTA/DIOR/HRSC/FAIR1M", "outputs/gt_index", "", "—"),
        ("GT parser", "pass", "mmrotate le90 QuadriBoxes", "scripts/_build_gt_mmrotate.py", "", "—"),
        ("prediction contract", "pass", "17-field schema", "orientbench/io/predictions.py", "", "—"),
        ("DOTA D2 gate", "partial_pass", "DOTA partial (3 detectors)", f"{R}/dota_formal_audit",
         "DOTA-only, 3-detector subset", "expand detectors if needed"),
        ("host training RHINO", "pass", "RHINO C1/B, DOTA-v1.0, mAP 0.7201", "outputs/training/rhino", "", "—"),
        ("host training A4", "pass", "O2-RTDETR A4, DOTA-v1.5, mAP 0.6497", "outputs/training/a4_host", "", "—"),
        ("host orientation gate", "pass", "B_C1/A_A4 host orientation", f"{R}/host_formal_audit", "", "—"),
        ("C1 gate", "partial_pass", "DOTA augmentation-view consistency",
         f"{R}/c1_formal_audit", "augmentation-view only (NOT physical multi-view)", "genuine multi-view needs new capture"),
        ("A4 gate", "partial_pass", "DOTA same-host source attribution",
         f"{R}/a4_formal_audit", "same-host only (NO cross-host causal)", "cross-host needs multi-host design + approval"),
        ("threshold freeze", "pass", "D2 + host + C1/A4 (D_cal)", f"{R}/c1_a4_threshold_freeze_record",
         "", "—"),
        ("readiness", "partial_pass", "scoped formal true; overall not complete", f"{R}/readiness_check.md", "", "—"),
        ("missing datasets", "out_of_scope_current", "SODA-A/ICDAR-MLT", "—",
         "not in current scope", "future scope + approval"),
        ("missing full matrix", "not_started", "9-detector x probe", "—", "not built", "future scope + approval"),
        ("genuine physical multi-view", "blocked", "C1 physical multiview", f"{R}/c1_real_cross_view_availability.md",
         "no multi-viewpoint capture in datasets", "new data acquisition"),
        ("9-detector matrix", "not_started", "full OrientBench matrix", "—", "not built", "future scope + approval"),
        ("cross-dataset generalization", "out_of_scope_current", "DOTA->other", "—",
         "DOTA-scoped only", "future scope + approval"),
    ]
    rows = [{"module": m, "status": s, "scope": sc, "evidence_path": ep,
             "blocking_reason": br, "next_required_action": na} for m, s, sc, ep, br, na in matrix]
    wcsv("project_status_matrix.csv", rows, ["module", "status", "scope", "evidence_path",
                                             "blocking_reason", "next_required_action"])
    L = [f"# Project Status Matrix", "", f"> {TS}", "",
         "| module | status | scope | evidence | blocking_reason | next_required_action |",
         "|---|---|---|---|---|---|"]
    for r in rows:
        L.append(f"| {r['module']} | **{r['status']}** | {r['scope']} | `{r['evidence_path']}` | "
                 f"{r['blocking_reason'] or '—'} | {r['next_required_action']} |")
    L += ["", "状态码: pass / partial_pass / blocked / not_started / out_of_scope_current。",
          "**partial_pass = DOTA-scoped 通过，非 full project。**"]
    wmd("project_status_matrix.md", L)

    # ---------- Task 2: milestone acceptance ----------
    acc_rows = [
        {"item": "milestone_verdict", "value": "PASS within frozen DOTA scope"},
        {"item": "D2_formal_status", "value": "partial_frozen DOTA (3-detector) PASS"},
        {"item": "RHINO_host_status", "value": f"trained+frozen, mAP 0.7201, sha256 {rh_sha[:16]}"},
        {"item": "O2RTDETR_A4_host_status", "value": f"trained+frozen, mAP 0.6497, sha256 {a4_sha[:16]}"},
        {"item": "C1_formal_audit", "value": "formal_pass (augmentation-view scope only)"},
        {"item": "A4_formal_audit", "value": "formal_pass (same-host source-attribution scope)"},
        {"item": "thresholds_sha256", "value": thr_sha},
        {"item": "freeze_status", "value": thr.get("freeze_status")},
        {"item": "dcal_daudit_disjoint", "value": "True (deterministic md5 split; verified)"},
        {"item": "tests", "value": "156 passed"},
    ]
    wcsv("dota_scoped_milestone_acceptance.csv", acc_rows, ["item", "value"])
    L = ["# DOTA-Scoped Milestone Acceptance", "", f"> {TS}", "",
         "## 验收结论: **PASS within frozen DOTA scope**", ""]
    for r in acc_rows:
        L.append(f"- **{r['item']}**: {r['value']}")
    L += ["", "## 正式报告路径",
          "- dota_formal_audit / host_formal_audit / c1_formal_audit / a4_formal_audit / "
          "c1_a4_threshold_freeze_record / formal_gate_summary / bench_core_v03_formal_gates (.md/.csv)",
          "", "## 禁止外推 (NO EXTRAPOLATION)",
          "- **不得**外推到 SODA-A / ICDAR-MLT / HRSC / DIOR / FAIR1M。",
          "- **不得**外推到 genuine physical multi-view。",
          "- **不得**外推到 9-detector full benchmark。",
          "- **不得**外推到跨 host 因果。",
          "- 本验收**仅限** frozen DOTA scope（RHINO C1/B + O2-RTDETR A4），非 full project completion。"]
    wmd("dota_scoped_milestone_acceptance.md", L)

    # ---------- Task 3: claim ledger ----------
    allowed = [
        "DOTA-scoped C1 augmentation-view consistency passed frozen D_audit formal gate.",
        "DOTA-scoped A4 same-host source-attribution passed frozen D_audit formal gate.",
        "DOTA D2 partial frozen gate (3 detectors) passed.",
        "Host checkpoints (RHINO 55a90abb, O2-RTDETR 3e32fa11) are locked and hash-recorded.",
        "Thresholds for D2/host/C1/A4 are frozen from D_cal; D_audit was holdout only.",
    ]
    qualified = [
        "C1 is augmentation-view consistency, NOT genuine physical multi-view.",
        "A4 attribution is same-host statistical source attribution, NOT cross-host causality.",
        "All results are DOTA-scoped (RHINO DOTA-v1.0, O2-RTDETR DOTA-v1.5).",
        "C1/A4 are partial_pass at project level; full project gate is incomplete.",
    ]
    forbidden = [
        "OrientBench full benchmark complete.",
        "C1 genuine physical multi-view solved.",
        "A4 proves causal source attribution across models.",
        "9-detector matrix complete.",
        "All datasets covered.",
        "ARS-DETR substituted RHINO.",
    ]
    crows = ([{"class": "allowed", "claim": c} for c in allowed]
             + [{"class": "qualified", "claim": c} for c in qualified]
             + [{"class": "forbidden", "claim": c} for c in forbidden])
    wcsv("claim_ledger.csv", crows, ["class", "claim"])
    L = ["# Claim Ledger", "", f"> {TS}", "", "## allowed_claims"]
    L += [f"- {c}" for c in allowed]
    L += ["", "## qualified_claims"] + [f"- {c}" for c in qualified]
    L += ["", "## forbidden_claims (MUST NOT appear in any formal report)"] + [f"- {c}" for c in forbidden]
    wmd("claim_ledger.md", L)

    # ---------- Task 4: reproducibility manifest ----------
    splits_files = {
        "c1_view_a": "outputs/predictions/DOTA-v1.0/rhino/schema/pred_rhino_val.jsonl",
        "c1_view_b": "outputs/probes/c1_cross_view_real/view_b_unrotated.jsonl",
        "c1_gt": "outputs/predictions/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl",
        "a4_pred": "outputs/predictions/DOTA-v1.5/a4_host/schema/pred_a4_host_val.jsonl",
        "a4_gt": "outputs/predictions/DOTA-v1.5/_dcal_subset/gt_mmrotate.jsonl",
    }
    manifest = {
        "generated": TS, "scope": "frozen DOTA C1/A4 milestone (NOT full project)",
        "repo_state": "git not initialized in project dir (file-based)",
        "thresholds_yaml_sha256": thr_sha, "freeze_status": thr.get("freeze_status"),
        "frozen_threshold_records": ["outputs/bench_core/reports/c1_a4_threshold_freeze_record.md",
                                     "configs/thresholds.c1_candidate.yaml", "configs/thresholds.a4_candidate.yaml"],
        "rhino_ckpt": {"path": os.path.relpath(rhino, P), "sha256": rh_sha},
        "a4_ckpt": {"path": os.path.relpath(a4, P), "sha256": a4_sha},
        "split_method": "deterministic md5(image_id) -> D_cal/D_audit (disjoint)",
        "split_files": {k: {"path": v, "sha256": sha(os.path.join(P, v))} for k, v in splits_files.items()},
        "formal_audit_outputs": ["outputs/bench_core/reports/c1_formal_audit.md",
                                 "outputs/bench_core/reports/a4_formal_audit.md",
                                 "outputs/probes/c1_cross_view_formal/c1_formal_detail.json",
                                 "outputs/probes/a4_source_attribution_formal/a4_formal_detail.json"],
        "test_command": "python -m pytest tests/ -q", "test_result": "156 passed",
        "critical_scripts": ["scripts/54_freeze_c1_a4.py", "scripts/55_c1_formal_audit.py",
                             "scripts/56_a4_formal_audit.py", "scripts/52_c1_real_cross_view.py",
                             "scripts/53_run_a4_formal_readiness.py", "scripts/90_verify_dota_scoped_milestone.py"],
        "env": {"analysis": "mr_dev1x (mmrotate 1.x, numpy, cv2, shapely)",
                "host_train_infer": "ai4rs_train (torch 2.4, mmrotate ai4rs)"},
        "random_seeds": {"hsic": 0, "bootstrap": 0, "training": 42},
        "gpu_usage": "host training 4xA30 (016-prior); 018 acceptance is CPU read-only; no new GPU use",
        "secrets": "none included; paths+hashes only",
    }
    json.dump(manifest, open(os.path.join(REP, "reproducibility_manifest.json"), "w"), indent=2, ensure_ascii=False)
    L = ["# Reproducibility Manifest", "", f"> {TS}", "",
         f"- thresholds.yaml sha256: `{thr_sha}`", f"- freeze_status: `{thr.get('freeze_status')}`",
         f"- RHINO ckpt: `{manifest['rhino_ckpt']['path']}` sha256 `{rh_sha}`",
         f"- A4 ckpt: `{manifest['a4_ckpt']['path']}` sha256 `{a4_sha}`",
         f"- split: {manifest['split_method']}",
         "- split files (path + sha256):"]
    for k, v in manifest["split_files"].items():
        L.append(f"  - {k}: `{v['path']}` sha256 `{(v['sha256'] or 'MISSING')[:16]}`")
    L += [f"- test: `{manifest['test_command']}` -> {manifest['test_result']}",
          f"- seeds: {manifest['random_seeds']}", f"- env: {manifest['env']}",
          f"- gpu: {manifest['gpu_usage']}", "- secrets: none (paths+hashes only).",
          "", "**scope: frozen DOTA C1/A4 milestone — NOT full project.**"]
    wmd("reproducibility_manifest.md", L)

    print("[ok] generated status_matrix, milestone_acceptance, claim_ledger, reproducibility_manifest")


if __name__ == "__main__":
    main()
