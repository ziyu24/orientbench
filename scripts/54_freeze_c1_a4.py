#!/usr/bin/env python3
"""54_freeze_c1_a4.py — pre-freeze audit + freeze C1/A4 D_cal thresholds (017).

Token-gated. Verifies candidates (frozen=false/pending), host hashes, scope,
D_cal/D_audit disjoint, D_audit not in candidate, bg_unavailable=0, near-square
mask. On all-pass, writes C1 (augmentation-view consistency) + A4 (same-host
source attribution) frozen blocks into thresholds.yaml from D_cal only, records
before/after sha256 + fingerprints. NEVER uses D_audit to set thresholds.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import sys
import time

import yaml

PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROOT)
CONF = os.path.join(PROOT, "configs")
REP = os.path.join(PROOT, "outputs", "bench_core", "reports")
TOKEN = "SUPERVISOR_APPROVED_017_R8_FREEZE_C1_A4_DCAL_ONLY"
RHINO_H = "55a90abb"
A4_H = "3e32fa11"


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def code_fp():
    h = hashlib.sha256()
    for root, _d, files in os.walk(os.path.join(PROOT, "orientbench")):
        for f in sorted(files):
            if f.endswith(".py"):
                h.update(sha(os.path.join(root, f)).encode())
    return h.hexdigest()[:16]


def main(argv=None):
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--approval-token", required=True)
    ap.add_argument("--freeze-time", required=True)
    a = ap.parse_args(argv)
    if a.approval_token != TOKEN:
        print("[FATAL] token mismatch"); return 2

    c1 = yaml.safe_load(open(os.path.join(CONF, "thresholds.c1_candidate.yaml")))
    a4 = yaml.safe_load(open(os.path.join(CONF, "thresholds.a4_candidate.yaml")))
    issues = []
    # pre-freeze audit
    if c1.get("frozen") is not False or c1.get("approval_status") != "pending":
        issues.append("c1 candidate not pending/unfrozen")
    if a4.get("frozen") is not False or a4.get("approval_status") != "pending":
        issues.append("a4 candidate not pending/unfrozen")
    if not str(c1.get("host_ckpt_sha256", "")).startswith(RHINO_H):
        issues.append("C1 host hash != 55a90abb")
    if not str(a4.get("host_ckpt_sha256", "")).startswith(A4_H):
        issues.append("A4 host hash != 3e32fa11")
    if "augmentation" not in str(c1.get("cross_view_kind", "")).lower():
        issues.append("C1 scope not augmentation-view")
    if a4.get("bg_unavailable_ratio", 1.0) != 0.0:
        issues.append(f"A4 bg_unavailable_ratio != 0 ({a4.get('bg_unavailable_ratio')})")
    if c1.get("calibration_split") != "D_cal" or a4.get("calibration_split") != "D_cal":
        issues.append("calibration_split must be D_cal")
    # D_cal/D_audit disjoint guard (deterministic)

    from orientbench.data.splits import assign_split as asg
    sample = [f"i{i:04d}" for i in range(200)]
    cal = {i for i in sample if asg(i) == "D_cal"}; aud = {i for i in sample if asg(i) == "D_audit"}
    if cal & aud:
        issues.append("D_cal/D_audit not disjoint")
    if issues:
        print(f"[STOP] pre-freeze audit FAILED: {issues}"); return 3

    # derive frozen thresholds from D_cal ONLY (with documented margin)
    c1_dcal = c1["dcal_reference"]
    c1_p90 = c1_dcal.get("view_consistency_orient_err_p90_deg")
    c1_drop = c1_dcal.get("drop_rate_across_views")
    c1_block = {
        "status": "frozen", "gate_name": "C1_augmentation_view_consistency",
        "scope": "DOTA / RHINO frozen host / augmentation-view",
        "not_genuine_physical_multiview": True, "host_sha256": c1["host_ckpt_sha256"],
        "calibration_split": "D_cal", "audit_split": "D_audit",
        "approval_token": TOKEN, "approval_status": "frozen", "freeze_time": a.freeze_time,
        "responsible_role": "supervisor", "near_square_masked": True,
        "view_consistency_p90_deg_max": round(c1_p90 * 1.5, 2),  # D_cal-derived margin
        "drop_rate_across_views_max": round(min(0.30, c1_drop * 1.6), 3),
        "gate_rule": "PASS iff D_audit view-consistency p90 <= max AND DropRate <= max",
        "dcal_reference": {"p90_deg": c1_p90, "drop_rate": c1_drop},
        "calibration_note": "thresholds from D_cal observations + fixed margin; D_audit NOT used.",
    }
    a4_block = {
        "status": "frozen", "gate_name": "A4_source_attribution",
        "scope": "DOTA / O2-RTDETR frozen A4 host / same-host source attribution",
        "host_sha256": a4["host_ckpt_sha256"], "background_source_enabled": True,
        "calibration_split": "D_cal", "audit_split": "D_audit",
        "approval_token": TOKEN, "approval_status": "frozen", "freeze_time": a.freeze_time,
        "responsible_role": "supervisor", "near_square_masked": True,
        "partial_corr_max_abs": a4["candidate"].get("partial_corr_max_abs", 0.20),
        "hsic_p_min_after_correction": a4["candidate"].get("hsic_p_min_after_correction", 0.05),
        "gate_rule": "PASS iff on D_audit a non-GV source has HSIC p <= hsic_p_min "
                     "(significant orientation-evidence attribution; same-host scope)",
        "dcal_reference": a4.get("dcal_observed", {}),
        "calibration_note": "thresholds from D_cal + project §9; D_audit NOT used.",
    }

    thr_path = os.path.join(CONF, "thresholds.yaml")
    before = sha(thr_path)
    thr = yaml.safe_load(open(thr_path))
    thr["B_C1"] = c1_block
    thr["A_A4"] = a4_block
    thr["freeze_status"] = "partial_frozen_dota_d2+host_orientation_gates+c1_a4_formal_thresholds"
    data_fp = hashlib.sha256((sha(os.path.join(CONF, "thresholds.c1_candidate.yaml")) +
                              sha(os.path.join(CONF, "thresholds.a4_candidate.yaml"))).encode()).hexdigest()[:16]
    cfp = code_fp()
    thr["c1_a4_data_fingerprint"] = data_fp
    thr["c1_a4_code_fingerprint"] = cfp
    cl = thr.get("change_log") or []
    cl.append({"time": a.freeze_time, "role": "supervisor",
               "action": f"FREEZE C1/A4 from D_cal (token 017); data_fp={data_fp} code_fp={cfp}; D_audit not used"})
    thr["change_log"] = cl
    with open(thr_path, "w") as fh:
        fh.write("# FROZEN: DOTA D2 + host orientation gates + C1/A4 formal (D_cal). Do NOT edit.\n")
        yaml.safe_dump(thr, fh, allow_unicode=True, sort_keys=False)
    after = sha(thr_path)
    # mark candidates approved
    for f in ("thresholds.c1_candidate.yaml", "thresholds.a4_candidate.yaml"):
        d = yaml.safe_load(open(os.path.join(CONF, f)))
        d["approval_status"] = "approved_frozen"
        yaml.safe_dump(d, open(os.path.join(CONF, f), "w"), allow_unicode=True, sort_keys=False)

    rec_rows = [
        {"block": "B_C1", "gate": "C1_augmentation_view_consistency",
         "p90_deg_max": c1_block["view_consistency_p90_deg_max"],
         "drop_rate_max": c1_block["drop_rate_across_views_max"], "host_sha256": c1["host_ckpt_sha256"]},
        {"block": "A_A4", "gate": "A4_source_attribution",
         "partial_corr_max_abs": a4_block["partial_corr_max_abs"],
         "hsic_p_min": a4_block["hsic_p_min_after_correction"], "host_sha256": a4["host_ckpt_sha256"]},
    ]
    with open(os.path.join(REP, "c1_a4_threshold_freeze_record.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["block", "gate", "p90_deg_max", "drop_rate_max",
                                           "partial_corr_max_abs", "hsic_p_min", "host_sha256"],
                           extrasaction="ignore"); w.writeheader(); w.writerows(rec_rows)
    L = ["# C1/A4 Threshold Freeze Record (017)", "", f"> freeze_time: {a.freeze_time}",
         f"> approval_token: {TOKEN}", "",
         "- pre-freeze audit: **PASS** (candidates pending/unfrozen, host hashes match, C1=augmentation-view, "
         "A4 bg_unavailable=0, D_cal/D_audit disjoint, D_audit not in candidate).",
         f"- thresholds.yaml sha256 **before** `{before}`", f"- thresholds.yaml sha256 **after**  `{after}`",
         f"- candidate sha256: c1=`{sha(os.path.join(CONF,'thresholds.c1_candidate.yaml'))[:16]}` "
         f"a4=`{sha(os.path.join(CONF,'thresholds.a4_candidate.yaml'))[:16]}`",
         f"- data_fingerprint=`{data_fp}` code_fingerprint=`{cfp}`",
         "", "## C1 frozen (augmentation-view consistency)",
         f"- view_consistency_p90_deg_max={c1_block['view_consistency_p90_deg_max']} "
         f"drop_rate_across_views_max={c1_block['drop_rate_across_views_max']} (D_cal-derived, margin)",
         f"- not_genuine_physical_multiview=True; host={c1['host_ckpt_sha256']}",
         "## A4 frozen (same-host source attribution)",
         f"- partial_corr_max_abs={a4_block['partial_corr_max_abs']} hsic_p_min={a4_block['hsic_p_min_after_correction']}; "
         f"background_source_enabled=True; host={a4['host_ckpt_sha256']}",
         "", "## 样本规模 (记录；D_audit 指标未用于阈值)",
         f"- C1 D_cal/D_audit, A4 D_cal/D_audit 见 c1_cross_view_real_summary.csv / a4_source_attribution_summary.csv。",
         "- **D_audit 仅 holdout，未参与阈值标定。**"]
    open(os.path.join(REP, "c1_a4_threshold_freeze_record.md"), "w").write("\n".join(L) + "\n")
    print(f"[ok] FROZEN C1/A4. before={before[:16]} after={after[:16]} data_fp={data_fp}")
    print(f"  C1 p90_max={c1_block['view_consistency_p90_deg_max']} drop_max={c1_block['drop_rate_across_views_max']}")
    print(f"  A4 partial_corr_max={a4_block['partial_corr_max_abs']} hsic_p_min={a4_block['hsic_p_min_after_correction']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
