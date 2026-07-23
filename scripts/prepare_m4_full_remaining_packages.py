#!/usr/bin/env python3
"""Build A/B task packages containing only genuinely unfinished full-set items."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation"
FIELDS = [
    "assignment_version", "annotator_slot", "task_order", "task_id", "dataset",
    "crop_relpath", "long_side_angle_deg_le90", "ambiguous", "skip", "notes",
    "annotator_id", "annotation_timestamp_utc",
]


def atomic_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def decided(record: dict) -> bool:
    return (
        record.get("angle") is not None
        or bool(record.get("ambiguous"))
        or bool(record.get("skip"))
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    source_paths = {
        "A": [PKG / "annotator_A/outputs/draft_state.json"],
        "B": [
            PKG / "annotator_B/outputs/draft_state.json",
            PKG / "annotator_B/outputs_pilot_176_remaining/draft_state.json",
        ],
    }
    expected = {"A": (195, 1305), "B": (377, 1123)}
    summary = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "full_target_each": 1500,
        "slots": {},
    }
    for slot in "AB":
        annotator = PKG / f"annotator_{slot}"
        tasks = json.loads((annotator / "task_manifest.json").read_text())
        task_by_id = {row["task_id"]: row for row in tasks}
        records = {}
        identities = set()
        source_hashes = {}
        for path in source_paths[slot]:
            state = json.loads(path.read_text())
            if state.get("annotator_id"):
                identities.add(state["annotator_id"])
            source_hashes[str(path.relative_to(ROOT))] = sha256(path)
            for task_id, record in state["records"].items():
                if task_id not in task_by_id or not decided(record):
                    continue
                if task_id in records and records[task_id] != record:
                    raise RuntimeError(f"conflicting genuine records for {slot}/{task_id}")
                records[task_id] = record
        if len(identities) != 1:
            raise RuntimeError(f"slot {slot} must have one stable annotator identity")

        completed = []
        for task_id, record in records.items():
            row = task_by_id[task_id].copy()
            angle = record.get("angle")
            row["long_side_angle_deg_le90"] = "" if angle is None else f"{float(angle) % 180:.6f}"
            row["ambiguous"] = "1" if record.get("ambiguous") else "0"
            row["skip"] = "1" if record.get("skip") else "0"
            row["notes"] = record.get("notes", "")
            row["annotator_id"] = next(iter(identities))
            row["annotation_timestamp_utc"] = ""
            completed.append(row)
        completed.sort(key=lambda row: int(task_by_id[row["task_id"]]["task_order"]))

        remaining = [row.copy() for row in tasks if row["task_id"] not in records]
        random.Random(71501 if slot == "A" else 71502).shuffle(remaining)
        for order, row in enumerate(remaining, 1):
            row["task_order"] = str(order)
        if (len(completed), len(remaining)) != expected[slot]:
            raise RuntimeError(
                f"unexpected {slot} completed/remaining: {len(completed)}/{len(remaining)}"
            )

        task_dir = annotator / "full_remaining"
        atomic_csv(task_dir / "task_manifest.csv", remaining)
        atomic_json(task_dir / "task_manifest.json", remaining)
        atomic_csv(PKG / f"internal/full_{slot}_completed_snapshot.csv", completed)
        atomic_json(PKG / f"internal/full_{slot}_completed_snapshot.json", completed)

        output = annotator / "outputs_full_remaining"
        output.mkdir(parents=True, exist_ok=True)
        existing = list(output.iterdir())
        if existing:
            raise RuntimeError(f"refusing to overwrite {slot} remaining output: {existing}")
        atomic_json(output / "draft_state.json", {
            "current_index": 0,
            "annotator_id": next(iter(identities)),
            "records": {},
            "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        counts = Counter(row["dataset"] for row in remaining)
        summary["slots"][slot] = {
            "genuine_completed": len(completed),
            "remaining_displayed": len(remaining),
            "remaining_by_dataset": dict(sorted(counts.items())),
            "source_draft_sha256": source_hashes,
            "completed_snapshot": f"internal/full_{slot}_completed_snapshot.csv",
            "no_annotation_values_modified": True,
        }
    atomic_json(PKG / "internal/full_remaining_package_summary.json", summary)
    print(json.dumps(summary["slots"], ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
