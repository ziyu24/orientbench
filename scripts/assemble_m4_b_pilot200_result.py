#!/usr/bin/env python3
"""Combine B's preserved 24 returns with the newly exported remaining 176."""
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
    parser.add_argument("--tasks", type=Path, required=True)
    parser.add_argument("--initial", type=Path, required=True)
    parser.add_argument("--remaining", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    tasks = read(args.tasks)
    task_by_id = {row["task_id"]: row for row in tasks}
    results = read(args.initial) + read(args.remaining)
    by_id = {row["task_id"]: row for row in results}
    if len(tasks) != 200 or len(results) != 200 or len(by_id) != 200:
        raise RuntimeError("B combined return must contain 200 unique rows")
    if set(by_id) != set(task_by_id):
        raise RuntimeError("B combined return does not match the frozen 200 tasks")
    ordered = []
    for task in tasks:
        row = by_id[task["task_id"]]
        for key in ("assignment_version", "annotator_slot", "task_id", "dataset", "crop_relpath"):
            if row[key] != task[key]:
                raise RuntimeError(f"changed {key} for {task['task_id']}")
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
