#!/usr/bin/env python3
"""Verify 053 real-artifact P1-P5 rerun outputs."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "top_journal_v3" / "reports"
DOCS = ROOT / "top_journal_v3" / "docs"
FIGURES = ROOT / "top_journal_v3" / "figures"
MANIFEST_052 = ROOT / "outputs" / "persistent_artifacts" / "manifest_052.json"


REQUIRED = [
    DOCS / "p1_constructive_decoupling_experiment.md",
    REPORTS / "p1_angle_perturb_dose_response.csv",
    REPORTS / "p1_reverse_perturb_decoupling.csv",
    FIGURES / "iou_delta_theta_aspect_ratio_curve.csv",
    FIGURES / "iou_delta_theta_aspect_ratio_curve.md",
    DOCS / "p2_conformal_orientation_risk_control.md",
    REPORTS / "conformal_within_cell_risk_control.csv",
    REPORTS / "conformal_shift_violation_audit.csv",
    DOCS / "p3_psc_free_mechanism_tests.md",
    REPORTS / "psc_dota20_phase_mod.csv",
    REPORTS / "psc_phase_mod_aliasing_hist.csv",
    REPORTS / "psc_phase_mod_confounding_check.csv",
    DOCS / "p4_uncertainty_baselines_circular_stats.md",
    REPORTS / "uncertainty_baselines_nrc.csv",
    DOCS / "p5_downstream_selective_orientation_task.md",
    REPORTS / "downstream_selective_orientation.csv",
    DOCS / "writing_sync_patch_053.md",
    DOCS / "top_journal_evidence_decision_053.md",
    DOCS / "codex_latest_report.md",
    MANIFEST_052,
]


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as f:
        return list(csv.DictReader(f))


def git_lines(args: list[str]) -> list[str]:
    proc = subprocess.run(["git", *args], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if proc.returncode not in (0, 1):
        fail(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return [line for line in proc.stdout.splitlines() if line.strip()]


def main() -> None:
    missing = [str(p.relative_to(ROOT)) for p in REQUIRED if not p.exists()]
    if missing:
        fail("missing required outputs: " + ", ".join(missing))

    manifest = json.loads(MANIFEST_052.read_text())
    if "artifacts" not in manifest:
        fail("manifest_052.json lacks artifacts list")
    if any(a.get("synthetic_or_proxy") for a in manifest.get("artifacts", [])):
        fail("manifest_052 contains synthetic_or_proxy final artifact")

    p1 = read_csv(REPORTS / "p1_angle_perturb_dose_response.csv")
    if not p1 or any(r.get("source") != "052_real_schema_rematched" for r in p1):
        fail("P1 dose-response rows are not all 052 real rematched source")
    if any(r.get("synthetic_or_proxy") not in ("False", "false", "0") for r in p1):
        fail("P1 dose-response has synthetic/proxy rows")
    if not {"0", "5", "15", "30"}.issubset({r.get("epsilon_deg") for r in p1}):
        fail("P1 dose-response lacks required epsilon levels")

    p1_rev = read_csv(REPORTS / "p1_reverse_perturb_decoupling.csv")
    if not p1_rev or any(r.get("source") != "052_real_schema_rematched" for r in p1_rev):
        fail("P1 reverse rows are not all 052 real rematched source")
    if any(r.get("synthetic_or_proxy") not in ("False", "false", "0") for r in p1_rev):
        fail("P1 reverse has synthetic/proxy rows")

    p2 = read_csv(REPORTS / "conformal_within_cell_risk_control.csv")
    if not p2 or any(r.get("conformal_layer_not_score") not in ("True", "true", "1") for r in p2):
        fail("P2 does not mark conformal as guarantee layer")
    if any(r.get("source") != "052_full_real_matched_tables" for r in p2):
        fail("P2 rows are not sourced from 052 full real matched tables")
    p2_doc = (DOCS / "p2_conformal_orientation_risk_control.md").read_text()
    if "frozen D_cal/D_audit" not in p2_doc:
        fail("P2 doc does not declare frozen D_cal/D_audit")

    p3 = read_csv(REPORTS / "psc_dota20_phase_mod.csv")
    if not p3 or not any(r.get("cell_id") == "DOTA-v1.0/20" and r.get("source") == "052_permatched_phase_mod_full" for r in p3):
        fail("P3 DOTA #20 per-matched phase_mod evidence missing")

    tta = read_csv(ROOT / "top_journal_v3" / "reports" / "tta_circular_variance_full_052.csv")
    if not tta:
        fail("052 TTA circular table empty")
    sample = tta[:1000]
    if any(r.get("theta_to_2theta") not in ("True", "true", "1") for r in sample):
        fail("TTA rows do not declare theta->2theta circular statistics")
    if any(r.get("naive_linear_std_used") not in ("False", "false", "0") for r in sample):
        fail("TTA rows use naive linear std")
    p4 = read_csv(REPORTS / "uncertainty_baselines_nrc.csv")
    if not p4 or not any(r.get("baseline") == "TTA circular variance" and r.get("uses_circular_statistics") in ("True", "true", "1") for r in p4):
        fail("P4 lacks TTA circular variance baseline")

    p5 = read_csv(REPORTS / "downstream_selective_orientation.csv")
    if not p5:
        fail("P5 downstream table empty")
    if any(r.get("uses_real_matched_predictions") not in ("True", "true", "1") for r in p5):
        fail("P5 has rows not marked real matched predictions")
    if any(r.get("is_proxy") not in ("False", "false", "0") for r in p5):
        fail("P5 has proxy rows")

    latest = (DOCS / "codex_latest_report.md").read_text()
    if latest.count("👇👇👇👇👇👇") != 1 or latest.count("👆👆👆👆👆👆") != 1:
        fail("codex_latest_report does not have exactly one entry/exit wrapper")

    forbidden = ["TPAMI ready", "CVPR ready", "full project complete", "PSC angle head finally proven broken"]
    docs_text = "\n".join(p.read_text(errors="ignore") for p in DOCS.glob("*053*.md"))
    for phrase in forbidden:
        if phrase in docs_text:
            fail(f"forbidden phrase present: {phrase}")

    protected = git_lines(["diff", "--name-only", "--", "thresholds.yaml", "configs/thresholds.yaml"])
    protected += [p for p in git_lines(["diff", "--name-only"]) if "D_cal" in p or "D_audit" in p]
    if protected:
        fail("protected files modified: " + ", ".join(protected))

    tracked_big = []
    for line in git_lines(["ls-files", "-z"]):
        for name in line.split("\0"):
            if not name:
                continue
            p = ROOT / name
            if p.exists() and p.is_file() and p.stat().st_size > 100_000_000:
                tracked_big.append(name)
    if tracked_big:
        fail("tracked big files detected: " + ", ".join(tracked_big[:10]))

    print("PASS verify_real_evidence_p1_p5_rerun_053")


if __name__ == "__main__":
    main()
