#!/usr/bin/env python3
"""Combine a slot's frozen completed rows and newly exported remaining rows."""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path

FIELDS = [
    "assignment_version", "annotator_slot", "task_order", "task_id", "dataset",
    "crop_relpath", "long_side_angle_deg_le90", "ambiguous", "skip", "notes",
    "annotator_id", "annotation_timestamp_utc",
]


def read(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", choices=["A", "B"], required=True)
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--completed", type=Path, required=True)
    parser.add_argument("--remaining", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    tasks = read(args.tasks)
    task_by_id = {row["task_id"]: row for row in tasks}
    rows = read(args.completed) + read(args.remaining)
    by_id = {row["task_id"]: row for row in rows}
    if len(tasks) != 1500 or len(rows) != 1500 or len(by_id) != 1500:
        raise RuntimeError(f"slot {args.slot} must combine to 1500 unique rows")
    if set(by_id) != set(task_by_id):
        raise RuntimeError(f"slot {args.slot} combined target set mismatch")
    ordered = []
    for task in tasks:
        row = by_id[task["task_id"]]
        for key in ("assignment_version", "annotator_slot", "task_id", "dataset", "crop_relpath"):
            if row[key] != task[key]:
                raise RuntimeError(f"slot {args.slot}: changed {key}")
        row["task_order"] = task["task_order"]
        ordered.append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(ordered)
    os.replace(temporary, args.output)


if __name__ == "__main__":
    main()
