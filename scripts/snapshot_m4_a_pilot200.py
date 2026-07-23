#!/usr/bin/env python3
"""Export A's latest genuine first-200 draft into the frozen pilot schema."""
from __future__ import annotations

import csv
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation"
FIELDS = [
    "assignment_version", "annotator_slot", "task_order", "task_id", "dataset",
    "crop_relpath", "long_side_angle_deg_le90", "ambiguous", "skip", "notes",
    "annotator_id", "annotation_timestamp_utc",
]


def main() -> None:
    tasks = json.loads((PKG / "annotator_A/pilot_200/task_manifest.json").read_text())
    state = json.loads((PKG / "annotator_A/outputs/draft_state.json").read_text())
    if len(tasks) != 200:
        raise RuntimeError("A pilot task count is not 200")
    rows = []
    for task in tasks:
        record = state["records"].get(task["task_id"], {})
        row = task.copy()
        angle = record.get("angle")
        row["long_side_angle_deg_le90"] = "" if angle is None else f"{float(angle) % 180:.6f}"
        row["ambiguous"] = "1" if record.get("ambiguous") else "0"
        row["skip"] = "1" if record.get("skip") else "0"
        row["notes"] = record.get("notes", "")
        row["annotator_id"] = state.get("annotator_id", "")
        row["annotation_timestamp_utc"] = state.get("saved_at_utc", "") if record else ""
        rows.append(row)
    csv_path = PKG / "internal/pilot_200_A_snapshot.csv"
    temporary = csv_path.with_suffix(".csv.tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, csv_path)
    json_path = PKG / "internal/pilot_200_A_snapshot.json"
    temporary_json = json_path.with_suffix(".json.tmp")
    temporary_json.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary_json, json_path)


if __name__ == "__main__":
    main()
