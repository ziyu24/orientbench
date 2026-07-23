#!/usr/bin/env python3
"""Machine-side validation of the final M4 A/B package using isolated smoke labels."""
from __future__ import annotations

import csv
import json
import shutil
import subprocess
from pathlib import Path

ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
PY = Path("/home/rspip/anaconda3/envs/mr_dev1x/bin/python")
TOOL = ROOT / "annotation_tools/m4_angle_annotation"
TMP = Path("/dev/shm/m4_070_annotation_validation")
VALIDATION = ROOT / "reports/m4_human_annotation_package_validation.csv"


def load(path: Path):
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), reader.fieldnames or []


def write(path: Path, rows: list[dict], fields: list[str]):
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    if TMP.exists():
        shutil.rmtree(TMP)
    TMP.mkdir(parents=True)
    for slot in ("A", "B"):
        tasks, fields = load(TOOL / f"annotator_{slot}/tasks.csv")
        for index, row in enumerate(tasks):
            row["long_side_angle_deg_le90"] = f"{((index * 7 + (2 if slot == 'B' else 0)) % 170) - 85:.3f}"
            row["ambiguous"] = "0"
            row["skip"] = "0"
            row["annotator_id"] = f"SMOKE_{slot}_NOT_HUMAN"
            row["annotation_timestamp_utc"] = "2000-01-01T00:00:00Z"
        write(TMP / f"raw_{slot}.csv", tasks, fields)
    merge_output = TMP / "pairs.csv"
    merge_audit = TMP / "merge_audit.json"
    subprocess.run([
        str(PY), str(ROOT / "scripts/merge_m4_human_annotations.py"),
        "--raw-a", str(TMP / "raw_A.csv"), "--raw-b", str(TMP / "raw_B.csv"),
        "--output", str(merge_output), "--audit", str(merge_audit),
        "--min-per-dataset", "1",
    ], check=True, cwd=ROOT)
    analysis_output = TMP / "disagreement.csv"
    analysis_audit = TMP / "analysis_audit.json"
    subprocess.run([
        str(PY), str(ROOT / "scripts/analyze_m4_human_disagreement.py"),
        "--pairs", str(merge_output), "--merge-audit", str(merge_audit),
        "--output", str(analysis_output), "--analysis-audit", str(analysis_audit),
        "--proxy-output", str(TMP / "proxy.csv"),
    ], check=True, cwd=ROOT)
    merge = json.loads(merge_audit.read_text())
    analysis = json.loads(analysis_audit.read_text())
    browser_csv = Path("/dev/shm/m4_annotation_smoke_A.csv")
    browser_json = Path("/dev/shm/m4_annotation_smoke_A.json")
    browser_rows, browser_fields = load(browser_csv)
    browser_json_rows = json.loads(browser_json.read_text())
    browser_ok = (
        browser_csv.is_file() and browser_json.is_file() and len(browser_rows) == 1500
        and len(browser_json_rows) == 1500
        and browser_rows[0]["long_side_angle_deg_le90"] == "23.400"
        and browser_json_rows[0]["long_side_angle_deg_le90"] == "23.400"
    )
    formal_raw_absent = not (TOOL / "annotator_A/annotatorA_raw.csv").exists() and not (
        TOOL / "annotator_B/annotatorB_raw.csv").exists()
    additions = [
        {"check": "browser_start_save_restore_export_csv_json", "status": "PASS" if browser_ok else "FAIL",
         "dataset": "TEST_ONLY", "count": len(browser_rows), "evidence": "Playwright headless browser; isolated /dev/shm downloads"},
        {"check": "merge_script_smoke", "status": "PASS" if merge.get("status") == "COMPLETE_INDEPENDENT_DOUBLE_ANNOTATION" else "FAIL",
         "dataset": "TEST_ONLY", "count": merge.get("human_usable", 0), "evidence": str(merge_audit)},
        {"check": "disagreement_analysis_smoke", "status": "PASS" if analysis.get("status") == "COMPLETE_INDEPENDENT_DOUBLE_ANNOTATION" else "FAIL",
         "dataset": "TEST_ONLY", "count": analysis.get("usable_pairs", 0), "evidence": str(analysis_audit)},
        {"check": "smoke_data_isolated_from_formal_results", "status": "PASS" if formal_raw_absent else "FAIL",
         "dataset": "ALL", "count": 0, "evidence": "formal A/B raw files absent; official status remains HUMAN_BLOCKED"},
    ]
    existing, fields = load(VALIDATION)
    existing = [row for row in existing if row["check"] not in {item["check"] for item in additions}]
    write(VALIDATION, existing + additions, fields)
    if any(item["status"] != "PASS" for item in additions):
        raise RuntimeError(additions)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
