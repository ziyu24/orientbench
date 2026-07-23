#!/usr/bin/env python3
"""Combine a frozen tranche prefix and a newly exported remainder."""
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path


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
    rows = read(args.initial) + read(args.remaining)
    task_by_id = {row["task_id"]: row for row in tasks}
    by_id = {row["task_id"]: row for row in rows}
    if len(rows) != len(tasks) or len(by_id) != len(tasks) or set(by_id) != set(task_by_id):
        raise RuntimeError("combined tranche does not exactly cover its frozen target")
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
        writer = csv.DictWriter(handle, fieldnames=list(ordered[0]))
        writer.writeheader()
        writer.writerows(ordered)
    os.replace(temporary, args.output)


if __name__ == "__main__":
    main()
