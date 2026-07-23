#!/usr/bin/env python3
"""Freeze B's current 526 decisions and prepare only A's unmatched tasks."""
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


def decided(record: dict) -> bool:
    return record.get("angle") is not None or bool(record.get("ambiguous")) or bool(record.get("skip"))


def atomic_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict], fields: list[str] = FIELDS) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def export_rows(tasks: dict[str, dict], records: dict[str, dict], identity: str) -> list[dict]:
    rows = []
    for task_id, record in records.items():
        row = tasks[task_id].copy()
        angle = record.get("angle")
        row["long_side_angle_deg_le90"] = "" if angle is None else f"{float(angle) % 180:.6f}"
        row["ambiguous"] = "1" if record.get("ambiguous") else "0"
        row["skip"] = "1" if record.get("skip") else "0"
        row["notes"] = record.get("notes", "")
        row["annotator_id"] = identity
        row["annotation_timestamp_utc"] = ""
        rows.append(row)
    return rows


def collect(slot: str, paths: list[Path], tasks: dict[str, dict]) -> tuple[dict, str, dict]:
    records = {}
    identities = set()
    hashes = {}
    for path in paths:
        state = json.loads(path.read_text())
        hashes[str(path.relative_to(ROOT))] = sha256(path)
        if state.get("annotator_id"):
            identities.add(state["annotator_id"])
        for task_id, record in state.get("records", {}).items():
            if task_id not in tasks or not decided(record):
                continue
            if task_id in records and records[task_id] != record:
                raise RuntimeError(f"conflicting {slot} record: {task_id}")
            records[task_id] = record
    if len(identities) != 1:
        raise RuntimeError(f"slot {slot} identity is not stable")
    return records, next(iter(identities)), hashes


def main() -> None:
    full = {slot: json.loads((PKG / f"annotator_{slot}/task_manifest.json").read_text())
            for slot in "AB"}
    tasks = {slot: {row["task_id"]: row for row in full[slot]} for slot in "AB"}
    mapping_rows = list(csv.DictReader((PKG / "internal/instance_id_mapping.csv").open()))
    to_canonical = {(row["annotator_slot"], row["task_id"]): row["canonical_anon_id"]
                    for row in mapping_rows}
    from_canonical = {slot: {to_canonical[(slot, row["task_id"])]: row["task_id"]
                             for row in full[slot]} for slot in "AB"}

    a_records, a_identity, a_hashes = collect("A", [
        PKG / "annotator_A/outputs/draft_state.json",
        PKG / "annotator_A/outputs_full_remaining/draft_state.json",
    ], tasks["A"])
    b_records, b_identity, b_hashes = collect("B", [
        PKG / "annotator_B/outputs/draft_state.json",
        PKG / "annotator_B/outputs_pilot_176_remaining/draft_state.json",
        PKG / "annotator_B/outputs_full_remaining/draft_state.json",
    ], tasks["B"])
    b_target = {to_canonical[("B", task_id)] for task_id in b_records}
    if len(b_target) != 526:
        raise RuntimeError(f"expected frozen B target 526, got {len(b_target)}")
    a_on_target = {
        task_id: record for task_id, record in a_records.items()
        if to_canonical[("A", task_id)] in b_target
    }
    a_done_canonical = {to_canonical[("A", task_id)] for task_id in a_on_target}
    missing_canonical = b_target - a_done_canonical
    if len(a_on_target) != 195 or len(missing_canonical) != 331:
        raise RuntimeError(
            f"expected A 195 completed + 331 missing, got {len(a_on_target)} + {len(missing_canonical)}"
        )

    a_target_tasks = [tasks["A"][from_canonical["A"][canonical]].copy()
                      for canonical in sorted(b_target)]
    b_target_tasks = [tasks["B"][from_canonical["B"][canonical]].copy()
                      for canonical in sorted(b_target)]
    a_missing = [tasks["A"][from_canonical["A"][canonical]].copy()
                 for canonical in missing_canonical]
    random.Random(71526).shuffle(a_missing)
    for index, row in enumerate(a_missing, 1):
        row["task_order"] = str(index)

    atomic_csv(PKG / "annotator_A/b526_target/task_manifest.csv", a_target_tasks)
    atomic_json(PKG / "annotator_A/b526_target/task_manifest.json", a_target_tasks)
    atomic_csv(PKG / "annotator_B/b526_target/task_manifest.csv", b_target_tasks)
    atomic_json(PKG / "annotator_B/b526_target/task_manifest.json", b_target_tasks)
    atomic_csv(PKG / "annotator_A/b526_remaining/task_manifest.csv", a_missing)
    atomic_json(PKG / "annotator_A/b526_remaining/task_manifest.json", a_missing)

    a_snapshot = export_rows(tasks["A"], a_on_target, a_identity)
    b_snapshot = export_rows(tasks["B"], b_records, b_identity)
    atomic_csv(PKG / "internal/b526_A_initial195_snapshot.csv", a_snapshot)
    atomic_json(PKG / "internal/b526_A_initial195_snapshot.json", a_snapshot)
    atomic_csv(PKG / "internal/b526_B_frozen_snapshot.csv", b_snapshot)
    atomic_json(PKG / "internal/b526_B_frozen_snapshot.json", b_snapshot)

    sampling = list(csv.DictReader((ROOT / "reports/m4_human_annotation_sampling_manifest.csv").open()))
    target_sampling = [row for row in sampling if row["anon_id"] in b_target]
    atomic_csv(PKG / "internal/b526_sampling_manifest.csv", target_sampling, list(target_sampling[0]))

    output = PKG / "annotator_A/outputs_b526_remaining"
    output.mkdir(parents=True, exist_ok=True)
    if list(output.iterdir()):
        raise RuntimeError(f"refusing to overwrite A b526 output: {list(output.iterdir())}")
    atomic_json(output / "draft_state.json", {
        "current_index": 0,
        "annotator_id": a_identity,
        "records": {},
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    summary = {
        "status": "A_ANNOTATION_REQUIRED",
        "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
        "b_frozen_completed": len(b_records),
        "a_already_completed_on_target": len(a_on_target),
        "a_remaining_displayed": len(a_missing),
        "target_by_dataset": dict(sorted(Counter(
            tasks["B"][task_id]["dataset"] for task_id in b_records
        ).items())),
        "a_remaining_by_dataset": dict(sorted(Counter(row["dataset"] for row in a_missing).items())),
        "source_sha256": {"A": a_hashes, "B": b_hashes},
        "b_service_should_pause_until_analysis": True,
    }
    atomic_json(PKG / "internal/b526_package_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
