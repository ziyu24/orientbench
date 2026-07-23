#!/usr/bin/env python3
"""Verify SUPERVISOR_049 evidence package constraints."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "top_journal_v3"

REQUIRED = [
    "docs/p1_constructive_decoupling_experiment.md",
    "reports/p1_angle_perturb_dose_response.csv",
    "reports/p1_reverse_perturb_decoupling.csv",
    "figures/iou_delta_theta_aspect_ratio_curve.csv",
    "figures/iou_delta_theta_aspect_ratio_curve.md",
    "docs/p2_conformal_orientation_risk_control.md",
    "reports/conformal_within_cell_risk_control.csv",
    "reports/conformal_shift_violation_audit.csv",
    "docs/p3_psc_free_mechanism_tests.md",
    "reports/psc_dota20_phase_mod.csv",
    "reports/psc_phase_mod_aliasing_hist.csv",
    "reports/psc_phase_mod_confounding_check.csv",
    "docs/p4_uncertainty_baselines_circular_stats.md",
    "reports/uncertainty_baselines_nrc.csv",
    "docs/p5_downstream_selective_orientation_task.md",
    "reports/downstream_selective_orientation.csv",
    "figures/nrc_interpretation_schematic.md",
    "figures/nrc_interpretation_schematic.csv",
    "docs/related_work_references_patch.md",
    "docs/top_journal_evidence_decision_049.md",
    "docs/codex_latest_report.md",
    "reports/heartbeat_049.json",
]

FORBIDDEN_TEXT = [
    "TPAMI ready",
    "CVPR ready",
    "full project complete",
    "PSC angle head finally proven broken",
    "DOTA #20 validation",
    "oracle_gain",
    "retained oracle",
]


def git_status(path: str) -> str:
    p = subprocess.run(["git", "status", "--short", "--", path], cwd=ROOT, text=True, capture_output=True, check=False)
    return p.stdout.strip()


def main() -> int:
    checks = []
    failures = []

    ag = ROOT / "AGENTS.md"
    checks.append({"check": "AGENTS.md exists/readable", "pass": ag.exists() and ag.stat().st_size > 0})

    checks.append({"check": "top_journal_v3 workspace exists", "pass": OUT.exists()})
    for rel in REQUIRED:
        ok = (OUT / rel).exists() and (OUT / rel).stat().st_size > 0
        checks.append({"check": f"required output {rel}", "pass": ok})
        if not ok:
            failures.append(f"missing_or_empty:{rel}")

    latest = (OUT / "docs/codex_latest_report.md").read_text(encoding="utf-8") if (OUT / "docs/codex_latest_report.md").exists() else ""
    fence_ok = latest.startswith("👇👇👇👇👇👇\n") and latest.rstrip().endswith("👆👆👆👆👆👆")
    checks.append({"check": "codex_latest_report has entrance/exit", "pass": fence_ok})
    if not fence_ok:
        failures.append("latest_report_fence")

    all_text = ""
    for p in OUT.rglob("*"):
        if "__pycache__" in p.parts or p.name.startswith("verification_top_journal_evidence_v2_049"):
            continue
        if p.name == "verify_top_journal_evidence_v2_049.py":
            continue
        if p.is_file() and p.suffix.lower() in {".md", ".py", ".csv", ".json", ".txt"}:
            all_text += "\n" + p.read_text(encoding="utf-8", errors="ignore")
    for bad in FORBIDDEN_TEXT:
        ok = bad not in all_text
        checks.append({"check": f"forbidden text absent: {bad}", "pass": ok})
        if not ok:
            failures.append(f"forbidden_text:{bad}")

    conformal_ok = "conformal 是阈值/保证层，不是普通 selection score" in latest or "not as a new selection score" in all_text
    checks.append({"check": "conformal not written as ordinary score", "pass": conformal_ok})
    if not conformal_ok:
        failures.append("conformal_wording")

    circular_ok = "theta -> 2theta" in all_text.lower() and "naive linear" in all_text.lower()
    checks.append({"check": "angle variance circular statistics documented", "pass": circular_ok})
    if not circular_ok:
        failures.append("circular_stats")

    for rel in ["configs/thresholds.yaml", "outputs/bench_core/splits"]:
        st = git_status(rel)
        ok = st == "" or all(line.startswith("??") for line in st.splitlines())
        checks.append({"check": f"no tracked modification to {rel}", "pass": ok, "status": st})
        if not ok:
            failures.append(f"tracked_modified:{rel}:{st}")

    large = [str(p.relative_to(ROOT)) for p in OUT.rglob("*") if p.is_file() and p.stat().st_size > 50 * 1024 * 1024]
    checks.append({"check": "no large files in top_journal_v3", "pass": not large, "large_files": large})
    if large:
        failures.append("large_files")

    result = {
        "status": "pass" if not failures else "fail",
        "failures": failures,
        "checks": checks,
    }
    out = OUT / "reports/verification_top_journal_evidence_v2_049.json"
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    md = OUT / "reports/verification_top_journal_evidence_v2_049.md"
    md.write_text(
        "# Verification 049\n\n"
        f"status: {result['status']}\n\n"
        + "\n".join(f"- {'PASS' if c['pass'] else 'FAIL'}: {c['check']}" for c in checks)
        + "\n",
        encoding="utf-8",
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
