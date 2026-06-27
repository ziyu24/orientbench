#!/usr/bin/env python3
"""91_verify_full_matrix_partial.py — read-only verification of 019 full-matrix partial."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import subprocess
import sys
import time

P = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REP = os.path.join(P, "outputs", "bench_core", "reports")
FROZEN_THR_SHA = "b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae"
FORBIDDEN = ["full benchmark complete", "9-detector matrix complete", "all datasets covered",
             "genuine physical multi-view solved", "complete project gate", "ARS-DETR substituted RHINO"]


def main():
    checks = []

    def chk(n, ok, d=""):
        checks.append({"check": n, "ok": bool(ok), "detail": str(d)})

    # release package
    rel = os.path.join(P, "outputs/releases/dota_scoped_milestone_v1")
    for f in ("RELEASE_NOTES.md", "MANIFEST.json", "SHA256SUMS.txt"):
        chk(f"release:{f}", os.path.isfile(os.path.join(rel, f)))

    # DOTA milestone still verifies (run 90 read-only)
    r = subprocess.run([sys.executable, os.path.join(P, "scripts", "90_verify_dota_scoped_milestone.py")],
                       capture_output=True, text=True)
    chk("dota_milestone_verifies", r.returncode == 0, r.stdout.strip().splitlines()[-1] if r.stdout else "")

    # thresholds.yaml unchanged (frozen)
    cur = hashlib.sha256(open(os.path.join(P, "configs/thresholds.yaml"), "rb").read()).hexdigest()
    chk("thresholds_unchanged", cur == FROZEN_THR_SHA, cur[:16])

    # required matrix reports
    for f in ("full_matrix_execution_plan.csv", "full_matrix_schema_validation.csv",
              "full_matrix_metrics_summary.csv", "full_project_coverage_report.json",
              "gpu_policy_record.json"):
        chk(f"exists:{f}", os.path.isfile(os.path.join(REP, f)))

    # no forbidden overclaims in matrix/coverage reports
    bad = []
    for f in ("full_matrix_metrics_summary.md", "full_project_coverage_report.md",
              "full_matrix_execution_plan.md", "full_matrix_probe_summary.md"):
        p = os.path.join(REP, f)
        if os.path.isfile(p):
            t = open(p).read().lower()
            for ph in FORBIDDEN:
                if ph.lower() in t:
                    bad.append(f"{f}:{ph}")
    chk("no_forbidden_overclaims", not bad, bad)

    # formal claims only for DOTA; non-DOTA exploratory
    met = list(csv.DictReader(open(os.path.join(REP, "full_matrix_metrics_summary.csv"))))
    nondota_formal = [m for m in met if m["dataset"] not in ("DOTA-v1.0", "DOTA-v1.5")
                      and "formal" in m.get("formal_scope", "") and "exploratory" not in m.get("formal_scope", "")]
    chk("formal_only_dota", not nondota_formal, nondota_formal)

    # coverage口径
    cov = json.load(open(os.path.join(REP, "full_project_coverage_report.json")))
    chk("full_project_incomplete", cov["full_project_complete"] is False)
    chk("full_matrix_partial", cov["full_matrix_status"] == "partial")
    chk("dota_milestone_pass", cov["dota_scoped_milestone"] == "pass")
    chk("training_not_needed", cov["training_needed_now"] is False)

    # GPU policy: every GPU task world_size=4, no batch override, no OOM rescue
    gp = json.load(open(os.path.join(REP, "gpu_policy_record.json")))
    chk("all_gpu_tasks_world_size_4", all(t["world_size"] == 4 for t in gp["tasks"]),
        [t["cell"] for t in gp["tasks"] if t["world_size"] != 4])
    chk("no_batch_override", gp["batch_override_anywhere"] is False)
    chk("no_oom_batch_lowering", gp["oom_batch_lowering"] is False)
    chk("no_oom", all(not t["oom"] for t in gp["tasks"]))

    ok_all = all(c["ok"] for c in checks)
    out = {"time": time.strftime("%Y-%m-%d %H:%M:%S %Z"), "verdict": "VERIFIED" if ok_all else "FAILED",
           "n_checks": len(checks), "n_pass": sum(c["ok"] for c in checks),
           "full_matrix_status": "partial", "full_project_complete": False,
           "dota_scoped_milestone": "pass", "checks": checks}
    json.dump(out, open(os.path.join(REP, "verification_full_matrix_partial.json"), "w"), indent=2, ensure_ascii=False)
    L = ["# Full-Matrix Partial Verification (read-only)", "", f"> {out['time']}",
         f"> verdict: **{out['verdict']}** ({out['n_pass']}/{out['n_checks']})",
         "> full_matrix_status=partial; full_project_complete=false; dota_scoped_milestone=pass", "",
         "| check | ok | detail |", "|---|---|---|"]
    for c in checks:
        L.append(f"| {c['check']} | {'✓' if c['ok'] else '✗'} | {c['detail']} |")
    open(os.path.join(REP, "verification_full_matrix_partial.md"), "w").write("\n".join(L) + "\n")
    print(f"[verify-matrix] {out['verdict']} {out['n_pass']}/{out['n_checks']}")
    return 0 if ok_all else 1


if __name__ == "__main__":
    raise SystemExit(main())
