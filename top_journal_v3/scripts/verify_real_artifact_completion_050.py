#!/usr/bin/env python3
"""Verify SUPERVISOR_050 real-artifact package."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "top_journal_v3"
REPORTS = OUT / "reports"
DOCS = OUT / "docs"


REQUIRED = [
    "docs/real_artifact_inventory_050.md",
    "reports/real_artifact_inventory_050.csv",
    "reports/real_artifact_regeneration_050.csv",
    "reports/psc_track_a_dump_050.csv",
    "docs/psc_track_a_dump_050.md",
    "reports/uncertainty_real_artifacts_050.csv",
    "docs/uncertainty_real_artifacts_050.md",
    "docs/p1_constructive_decoupling_experiment.md",
    "reports/p1_angle_perturb_dose_response.csv",
    "reports/p1_reverse_perturb_decoupling.csv",
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
    "docs/top_journal_evidence_decision_050.md",
    "docs/codex_latest_report.md",
    "reports/heartbeat_050.json",
]


FORBIDDEN = [
    "TPAMI ready",
    "CVPR ready",
    "full project complete",
    "PSC angle head finally proven broken",
    "DOTA #20 validation",
    "oracle_gain",
    "retained oracle",
]


def git_status(path: str) -> str:
    p = subprocess.run(["git", "status", "--short", "--", path], cwd=ROOT, capture_output=True, text=True, check=False)
    return p.stdout.strip()


def check_csv_no_proxy(path: Path, failures: list[str]) -> bool:
    if not path.exists() or path.stat().st_size == 0:
        failures.append(f"missing:{path}")
        return False
    try:
        df = pd.read_csv(path)
    except Exception as e:
        failures.append(f"csv_read:{path}:{e}")
        return False
    if "synthetic_or_proxy" in df.columns:
        bad = df["synthetic_or_proxy"].astype(str).str.lower().isin(["true", "1", "yes"]).any()
        if bad:
            failures.append(f"proxy_rows:{path}")
            return False
    return True


def main() -> int:
    failures: list[str] = []
    checks: list[dict] = []

    for rel in REQUIRED:
        p = OUT / rel
        ok = p.exists() and p.stat().st_size > 0
        checks.append({"check": f"required {rel}", "pass": ok})
        if not ok:
            failures.append(f"missing:{rel}")

    manifest = ROOT / "outputs/persistent_artifacts/manifest_050.json"
    ok = manifest.exists() and manifest.stat().st_size > 0
    checks.append({"check": "manifest_050.json exists", "pass": ok})
    if not ok:
        failures.append("missing:manifest_050.json")
    else:
        m = json.loads(manifest.read_text(encoding="utf-8"))
        ok = not m.get("host_training_started") and not m.get("thresholds_modified") and not m.get("dcal_daudit_modified")
        checks.append({"check": "manifest records no training/threshold/split modification", "pass": ok})
        if not ok:
            failures.append("manifest_policy")

    for rel in [
        "reports/p1_angle_perturb_dose_response.csv",
        "reports/p1_reverse_perturb_decoupling.csv",
        "reports/conformal_within_cell_risk_control.csv",
        "reports/downstream_selective_orientation.csv",
    ]:
        ok = check_csv_no_proxy(OUT / rel, failures)
        checks.append({"check": f"no synthetic/proxy rows in {rel}", "pass": ok})

    p2 = pd.read_csv(REPORTS / "conformal_within_cell_risk_control.csv") if (REPORTS / "conformal_within_cell_risk_control.csv").exists() else pd.DataFrame()
    ok = len(p2) > 0 and "uses_real_D_cal_D_audit" in p2.columns and p2["uses_real_D_cal_D_audit"].astype(str).str.lower().eq("true").all()
    checks.append({"check": "P2 uses real D_cal/D_audit", "pass": ok})
    if not ok:
        failures.append("p2_real_split")

    p3 = pd.read_csv(REPORTS / "psc_track_a_dump_050.csv") if (REPORTS / "psc_track_a_dump_050.csv").exists() else pd.DataFrame()
    ok = len(p3) > 0 and "phase_mod_status" in p3.columns
    checks.append({"check": "P3 per-instance Track A dump status recorded", "pass": ok})
    if not ok:
        failures.append("p3_tracka_status")

    p4_text = (DOCS / "p4_uncertainty_baselines_circular_stats.md").read_text(encoding="utf-8") if (DOCS / "p4_uncertainty_baselines_circular_stats.md").exists() else ""
    ok = "theta -> 2theta" in p4_text and "naive linear std is forbidden" in p4_text
    checks.append({"check": "P4 circular statistics documented", "pass": ok})
    if not ok:
        failures.append("p4_circular")

    p5 = pd.read_csv(REPORTS / "downstream_selective_orientation.csv") if (REPORTS / "downstream_selective_orientation.csv").exists() else pd.DataFrame()
    ok = len(p5) > 0 and "uses_real_matched_predictions" in p5.columns and p5["uses_real_matched_predictions"].astype(str).str.lower().eq("true").all()
    checks.append({"check": "P5 uses real matched predictions", "pass": ok})
    if not ok:
        failures.append("p5_real")

    latest = (DOCS / "codex_latest_report.md").read_text(encoding="utf-8") if (DOCS / "codex_latest_report.md").exists() else ""
    ok = latest.startswith("👇👇👇👇👇👇\n") and latest.rstrip().endswith("👆👆👆👆👆👆")
    checks.append({"check": "latest report entrance/exit", "pass": ok})
    if not ok:
        failures.append("latest_fence")

    all_text = ""
    for p in OUT.rglob("*"):
        if "049" in p.name or p.name.startswith("verify_top_journal_evidence_v2_049"):
            continue
        if p.is_file() and "__pycache__" not in p.parts and not p.name.startswith("verification_real_artifact_completion_050"):
            if p.suffix.lower() in {".md", ".py", ".csv", ".json", ".txt"} and p.name != "verify_real_artifact_completion_050.py":
                all_text += "\n" + p.read_text(encoding="utf-8", errors="ignore")
    for bad in FORBIDDEN:
        ok = bad not in all_text
        checks.append({"check": f"forbidden text absent: {bad}", "pass": ok})
        if not ok:
            failures.append(f"forbidden:{bad}")

    for rel in ["configs/thresholds.yaml", "outputs/bench_core/splits"]:
        st = git_status(rel)
        ok = st == "" or all(line.startswith("??") for line in st.splitlines())
        checks.append({"check": f"no tracked modification {rel}", "pass": ok, "status": st})
        if not ok:
            failures.append(f"git_modified:{rel}")

    large = [str(p.relative_to(ROOT)) for p in OUT.rglob("*") if p.is_file() and p.stat().st_size > 50 * 1024 * 1024]
    ok = not large
    checks.append({"check": "git no large files under top_journal_v3", "pass": ok, "large_files": large})
    if not ok:
        failures.append("large_files")

    result = {"status": "pass" if not failures else "fail", "failures": failures, "checks": checks}
    (REPORTS / "verification_real_artifact_completion_050.json").write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    (REPORTS / "verification_real_artifact_completion_050.md").write_text(
        "# Verification 050\n\n"
        f"status: {result['status']}\n\n"
        + "\n".join(f"- {'PASS' if c['pass'] else 'FAIL'}: {c['check']}" for c in checks)
        + "\n",
        encoding="utf-8",
    )
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
