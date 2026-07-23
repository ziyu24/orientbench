#!/usr/bin/env python3
"""Materialize only the 176 still-unlabeled B tasks and freeze the prior 24."""
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


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary, path)


def main() -> None:
    pilot200 = json.loads((PKG / "annotator_B/pilot_200/task_manifest.json").read_text())
    state = json.loads((PKG / "annotator_B/outputs_pilot_200/draft_state.json").read_text())
    completed = state["records"]
    remaining = [row.copy() for row in pilot200 if row["task_id"] not in completed]
    done_tasks = {row["task_id"]: row for row in pilot200 if row["task_id"] in completed}
    if len(pilot200) != 200 or len(completed) != 24 or len(remaining) != 176:
        raise RuntimeError(
            f"expected 200/24/176, got {len(pilot200)}/{len(completed)}/{len(remaining)}"
        )
    for index, row in enumerate(remaining, 1):
        row["task_order"] = str(index)

    target = PKG / "annotator_B/pilot_176_remaining"
    write_csv(target / "task_manifest.csv", remaining)
    write_json(target / "task_manifest.json", remaining)

    frozen = []
    for task_id, record in completed.items():
        row = done_tasks[task_id].copy()
        angle = record.get("angle")
        row["long_side_angle_deg_le90"] = "" if angle is None else f"{float(angle) % 180:.6f}"
        row["ambiguous"] = "1" if record.get("ambiguous") else "0"
        row["skip"] = "1" if record.get("skip") else "0"
        row["notes"] = record.get("notes", "")
        row["annotator_id"] = state.get("annotator_id", "")
        row["annotation_timestamp_utc"] = state.get("saved_at_utc", "")
        frozen.append(row)
    frozen.sort(key=lambda row: int(row["task_order"]))
    write_csv(PKG / "internal/pilot_200_B_initial24_snapshot.csv", frozen)
    write_json(PKG / "internal/pilot_200_B_initial24_snapshot.json", frozen)

    output = PKG / "annotator_B/outputs_pilot_176_remaining"
    output.mkdir(parents=True, exist_ok=True)
    if list(output.iterdir()):
        raise RuntimeError("remaining-176 output directory is not empty")
    write_json(PKG / "internal/pilot_176_remaining_summary.json", {
        "already_completed_and_hidden": 24,
        "displayed_remaining_tasks": 176,
        "total_matched_pilot": 200,
        "new_output_records": 0,
    })
    print("B_REMAINING_READY displayed=176 preserved=24")


if __name__ == "__main__":
    main()
