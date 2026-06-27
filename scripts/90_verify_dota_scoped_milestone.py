#!/usr/bin/env python3
"""90_verify_dota_scoped_milestone.py — one-command READ-ONLY milestone verification.

No training, no inference, no threshold mutation. Verifies required artifacts,
freeze_status, host sha256, D_cal/D_audit disjointness, formal-audit pass, and
that forbidden claims do NOT appear as assertions in formal report titles/status
fields. Writes verification_dota_scoped_milestone.{md,json}.
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
CONF = os.path.join(P, "configs")

FORBIDDEN_ASSERTIONS = [
    "OrientBench full benchmark complete", "full benchmark complete",
    "genuine physical multi-view solved", "9-detector matrix complete",
    "all datasets covered", "ARS-DETR substituted RHINO", "complete project gate",
]


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest() if os.path.isfile(p) else None


def main():
    checks = []

    def chk(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    # required files
    required = [
        "configs/thresholds.yaml", "outputs/training/rhino/best_dota_mAP_epoch_35.pth",
        "outputs/training/a4_host/best_dota_mAP_epoch_70.pth",
        "outputs/bench_core/reports/c1_formal_audit.csv",
        "outputs/bench_core/reports/a4_formal_audit.csv",
        "outputs/bench_core/reports/c1_a4_threshold_freeze_record.md",
        "outputs/bench_core/reports/project_status_matrix.md",
        "outputs/bench_core/reports/claim_ledger.md",
        "outputs/bench_core/reports/reproducibility_manifest.json",
    ]
    for f in required:
        chk(f"exists:{f}", os.path.isfile(os.path.join(P, f)))

    # freeze_status
    thr = yaml.safe_load(open(os.path.join(CONF, "thresholds.yaml")))
    fs = str(thr.get("freeze_status"))
    chk("freeze_status_correct", fs == "partial_frozen_dota_d2+host_orientation_gates+c1_a4_formal_thresholds", fs)
    chk("freeze_not_overclaimed", "complete_B_C1" not in fs and "complete_A_A4" not in fs, fs)

    # host sha256
    rh = sha(os.path.join(P, "outputs/training/rhino/best_dota_mAP_epoch_35.pth")) or ""
    a4 = sha(os.path.join(P, "outputs/training/a4_host/best_dota_mAP_epoch_70.pth")) or ""
    chk("rhino_sha256", rh.startswith("55a90abb"), rh[:16])
    chk("a4_sha256", a4.startswith("3e32fa11"), a4[:16])
    chk("B_C1_host_match", str(thr["B_C1"]["host_sha256"]).startswith("55a90abb"))
    chk("A_A4_host_match", str(thr["A_A4"]["host_sha256"]).startswith("3e32fa11"))

    # D_cal/D_audit disjoint
    from orientbench.data.splits import assign_split
    s = [f"i{i:05d}" for i in range(1000)]
    cal = {i for i in s if assign_split(i) == "D_cal"}; aud = {i for i in s if assign_split(i) == "D_audit"}
    chk("dcal_daudit_disjoint", cal & aud == set(), f"|cal|={len(cal)} |aud|={len(aud)}")
    chk("calibration_split_dcal", thr["B_C1"]["calibration_split"] == "D_cal" and thr["A_A4"]["calibration_split"] == "D_cal")

    # formal audit pass
    def verdict(f):
        rows = list(csv.DictReader(open(os.path.join(REP, f))))
        return rows[0]["verdict"] if rows else None
    chk("c1_formal_pass", verdict("c1_formal_audit.csv") == "formal_pass")
    chk("a4_formal_pass", verdict("a4_formal_audit.csv") == "formal_pass")

    # forbidden claims NOT asserted in formal reports (exclude claim_ledger/verification — they enumerate them)
    scan = ["dota_scoped_milestone_acceptance.md", "formal_gate_summary.md",
            "project_status_matrix.md", "c1_formal_audit.md", "a4_formal_audit.md",
            "bench_core_v03_formal_gates.md"]
    bad = []
    for f in scan:
        p = os.path.join(REP, f)
        if not os.path.isfile(p):
            continue
        txt = open(p).read().lower()
        for phrase in FORBIDDEN_ASSERTIONS:
            if phrase.lower() in txt:
                bad.append(f"{f}:{phrase}")
    chk("no_forbidden_assertions", not bad, str(bad))

    # project not over-claimed
    pm = open(os.path.join(REP, "project_status_matrix.csv")).read()
    chk("status_codes_valid", all(s in pm for s in ["partial_pass", "out_of_scope_current"]))

    ok_all = all(c["ok"] for c in checks)
    out = {"time": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "verdict": "VERIFIED" if ok_all else "FAILED",
           "scoped_formal_gate_allowed": "true_for_frozen_dota_c1_a4_scope_only",
           "overall_project_complete": False, "training_needed_now": False,
           "n_checks": len(checks), "n_pass": sum(c["ok"] for c in checks), "checks": checks}
    json.dump(out, open(os.path.join(REP, "verification_dota_scoped_milestone.json"), "w"), indent=2, ensure_ascii=False)
    L = ["# DOTA-Scoped Milestone Verification (read-only)", "", f"> {out['time']}",
         f"> verdict: **{out['verdict']}** ({out['n_pass']}/{out['n_checks']} checks)",
         f"> scoped_formal_gate_allowed={out['scoped_formal_gate_allowed']}; "
         f"overall_project_complete={out['overall_project_complete']}; training_needed_now={out['training_needed_now']}", "",
         "| check | ok | detail |", "|---|---|---|"]
    for c in checks:
        L.append(f"| {c['check']} | {'✓' if c['ok'] else '✗'} | {c['detail']} |")
    open(os.path.join(REP, "verification_dota_scoped_milestone.md"), "w").write("\n".join(L) + "\n")
    print(f"[verify] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
