#!/usr/bin/env python3
"""Verify SUPERVISOR_052 real dump and matched-table completion."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

REQUIRED = [
    ROOT / "top_journal_v3/reports/dota20_phase_mod_forward_dump_052.csv",
    ROOT / "top_journal_v3/docs/dota20_phase_mod_forward_dump_052.md",
    ROOT / "top_journal_v3/reports/full_matched_tables_052.csv",
    ROOT / "top_journal_v3/docs/full_matched_tables_052.md",
    ROOT / "top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv",
    ROOT / "top_journal_v3/docs/psc_phase_mod_permatched_full_052.md",
    ROOT / "top_journal_v3/reports/tta_circular_variance_full_052.csv",
    ROOT / "top_journal_v3/docs/tta_circular_variance_full_052.md",
    ROOT / "top_journal_v3/docs/evidence_ready_for_p1_p5_rerun_052.md",
    ROOT / "outputs/persistent_artifacts/manifest_052.json",
    ROOT / "outputs/persistent_artifacts/orientbench_real_052/dota20_phase_mod/DOTA-v1.0_20.pkl",
]

FULL_CELLS = {
    "DOTA-v1.0/20", "DIOR-R/22", "FAIR1M-v1.0/24", "SODA-A/23",
    "DIOR-R/3", "DIOR-R/61", "SODA-A/4",
}
PSC_CELLS = {"DOTA-v1.0/20", "DIOR-R/22", "FAIR1M-v1.0/24", "SODA-A/23"}
TTA_CELLS = {
    "DIOR-R/3", "DIOR-R/22", "DIOR-R/61", "FAIR1M-v1.0/5",
    "FAIR1M-v1.0/24", "SODA-A/4", "SODA-A/23",
}


def fail(msg: str) -> None:
    print(f"FAIL: {msg}")
    sys.exit(1)


def git_changed_paths() -> list[str]:
    out = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
    paths = []
    for line in out.splitlines():
        if not line.strip():
            continue
        paths.append(line[3:] if len(line) > 3 else line)
    return paths


def check_required() -> None:
    missing = [str(p) for p in REQUIRED if not p.exists()]
    if missing:
        fail("missing required outputs: " + ", ".join(missing))


def check_manifest() -> None:
    manifest = json.loads((ROOT / "outputs/persistent_artifacts/manifest_052.json").read_text(encoding="utf-8"))
    if manifest.get("host_training_started"):
        fail("manifest says host training started")
    if manifest.get("thresholds_modified") or manifest.get("dcal_daudit_modified") or manifest.get("full_matrix_added"):
        fail("manifest flags forbidden modification/full matrix")
    arts = manifest.get("artifacts", [])
    if not arts:
        fail("manifest has no artifacts")
    for art in arts:
        for key in ["path", "sha256", "source_checkpoint", "split", "can_recompute"]:
            if key not in art or art[key] in ("", None):
                fail(f"manifest artifact missing {key}: {art}")
        if art.get("is_synthetic_or_proxy") or not art.get("is_real_detector_output", True):
            fail(f"manifest artifact is synthetic/proxy: {art.get('path')}")


def check_full_tables() -> None:
    rows = list(csv.DictReader((ROOT / "top_journal_v3/reports/full_matched_tables_052.csv").open()))
    seen = {r["cell_id"] for r in rows}
    if seen != FULL_CELLS:
        fail(f"full matched cells mismatch: {seen}")
    for r in rows:
        if r["status"] != "complete_full_real":
            fail(f"full matched status not complete: {r}")
        if r["is_full_not_capped"] != "True":
            fail(f"full matched capped/sample flag bad: {r}")
        if int(r["n_predictions"]) <= 0 or int(r["n_matched"]) <= 0:
            fail(f"full matched counts bad: {r}")
        table = ROOT / r["matched_table_path"]
        if not table.exists() or table.stat().st_size <= 0:
            fail(f"matched table missing/empty: {table}")


def stream_cells(path: Path, cell_key: str = "cell_id") -> dict[str, int]:
    counts: dict[str, int] = {}
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cell = row.get(cell_key, "")
            counts[cell] = counts.get(cell, 0) + 1
    return counts


def check_psc() -> None:
    counts = stream_cells(ROOT / "top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv")
    if set(counts) != PSC_CELLS:
        fail(f"PSC cells mismatch: {counts}")
    if any(v <= 0 for v in counts.values()):
        fail(f"PSC per-matched empty cell: {counts}")


def check_tta() -> None:
    counts: dict[str, int] = {}
    path = ROOT / "top_journal_v3/reports/tta_circular_variance_full_052.csv"
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            cell = row["cell_id"]
            counts[cell] = counts.get(cell, 0) + 1
            if row["theta_to_2theta"] != "True":
                fail(f"TTA row lacks theta_to_2theta: {row}")
            if row["naive_linear_std_used"] != "False":
                fail(f"TTA row uses naive std: {row}")
            if row["status"] != "complete_full_real_circular":
                fail(f"TTA row status bad: {row}")
    if set(counts) != TTA_CELLS:
        fail(f"TTA cells mismatch: {counts}")
    if any(v <= 0 for v in counts.values()):
        fail(f"TTA empty cell: {counts}")


def check_forbidden_paths() -> None:
    bad_patterns = [
        "thresholds.yaml",
        "D_cal",
        "D_audit",
        "d_cal",
        "d_audit",
    ]
    changed = git_changed_paths()
    bad = [p for p in changed if any(x in p for x in bad_patterns)]
    if bad:
        fail("forbidden path appears modified/untracked: " + ", ".join(bad))


def check_report_wrapper() -> None:
    report = ROOT / "top_journal_v3/docs/codex_latest_report.md"
    if not report.exists():
        return
    text = report.read_text(encoding="utf-8")
    if not (text.startswith("👇👇👇👇👇👇") and text.rstrip().endswith("👆👆👆👆👆👆")):
        fail("codex_latest_report wrapper invalid")


def main() -> None:
    check_required()
    check_manifest()
    check_full_tables()
    check_psc()
    check_tta()
    check_forbidden_paths()
    check_report_wrapper()
    print("PASS: 052 real dump and full matched-table verification")


if __name__ == "__main__":
    main()
