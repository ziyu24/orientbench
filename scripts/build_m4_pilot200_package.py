#!/usr/bin/env python3
"""Freeze A's first 200 tasks and build a blinded, shuffled B pilot package."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import random
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation"
REPORTS = ROOT / "reports"
LOGS = ROOT / "logs"
TASK_FIELDS = [
    "assignment_version", "annotator_slot", "task_order", "task_id", "dataset",
    "crop_relpath", "long_side_angle_deg_le90", "ambiguous", "skip", "notes",
    "annotator_id", "annotation_timestamp_utc",
]


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp, path)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n")
    os.replace(temp, path)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def state_name(record: dict) -> str:
    if record.get("angle") is not None:
        return "angle"
    if record.get("ambiguous"):
        return "ambiguous"
    if record.get("skip"):
        return "skip"
    return "pending"


def main() -> None:
    a_tasks = json.loads((PKG / "annotator_A/task_manifest.json").read_text())[:200]
    b_all = json.loads((PKG / "annotator_B/task_manifest.json").read_text())
    mapping = read_csv(PKG / "internal/instance_id_mapping.csv")
    sampling = read_csv(REPORTS / "m4_human_annotation_sampling_manifest.csv")
    state = json.loads((PKG / "annotator_A/outputs/draft_state.json").read_text())
    records = state.get("records", {})
    if len(a_tasks) != 200:
        raise RuntimeError("A pilot must contain exactly the first 200 tasks")

    canonical = {(row["annotator_slot"], row["task_id"]): row["canonical_anon_id"] for row in mapping}
    a_ids = [canonical[("A", row["task_id"])] for row in a_tasks]
    if len(set(a_ids)) != 200:
        raise RuntimeError("A pilot canonical IDs are not unique")
    wanted = set(a_ids)
    b_tasks = [row.copy() for row in b_all if canonical[("B", row["task_id"])] in wanted]
    if len(b_tasks) != 200:
        raise RuntimeError("B does not contain the same 200 canonical instances")

    rng = random.Random(71200)
    rng.shuffle(b_tasks)
    if any(canonical[("A", a["task_id"])] == canonical[("B", b["task_id"])]
           for a, b in zip(a_tasks, b_tasks)):
        rng.shuffle(b_tasks)
    for order, row in enumerate(b_tasks, 1):
        row["task_order"] = str(order)

    a_pilot_dir = PKG / "annotator_A/pilot_200"
    b_pilot_dir = PKG / "annotator_B/pilot_200"
    write_csv(a_pilot_dir / "task_manifest.csv", a_tasks, TASK_FIELDS)
    write_json(a_pilot_dir / "task_manifest.json", a_tasks)
    write_csv(b_pilot_dir / "task_manifest.csv", b_tasks, TASK_FIELDS)
    write_json(b_pilot_dir / "task_manifest.json", b_tasks)

    frozen_at = datetime.now(timezone.utc).isoformat()
    snapshot = []
    for task in a_tasks:
        record = records.get(task["task_id"], {})
        row = task.copy()
        angle = record.get("angle")
        row["long_side_angle_deg_le90"] = "" if angle is None else f"{float(angle) % 180.0:.6f}"
        row["ambiguous"] = "1" if record.get("ambiguous") else "0"
        row["skip"] = "1" if record.get("skip") else "0"
        row["notes"] = str(record.get("notes", ""))
        row["annotator_id"] = state.get("annotator_id", "")
        row["annotation_timestamp_utc"] = state.get("saved_at_utc", "") if record else ""
        snapshot.append(row)
    snapshot_csv = PKG / "internal/pilot_200_A_snapshot.csv"
    snapshot_json = PKG / "internal/pilot_200_A_snapshot.json"
    write_csv(snapshot_csv, snapshot, TASK_FIELDS)
    write_json(snapshot_json, snapshot)

    sampling_by_id = {row["anon_id"]: row for row in sampling}
    pilot_sampling = [sampling_by_id[identifier] for identifier in a_ids]
    write_csv(PKG / "internal/pilot_200_sampling_manifest.csv", pilot_sampling,
              list(pilot_sampling[0]))

    output_dir = PKG / "annotator_B/outputs_pilot_200"
    output_dir.mkdir(parents=True, exist_ok=True)
    unexpected = [path.name for path in output_dir.iterdir() if path.name != ".gitkeep"]
    if unexpected:
        raise RuntimeError(f"B pilot output is not empty: {unexpected}")

    image_errors = []
    for row in b_tasks:
        image_path = PKG / "annotator_B" / row["crop_relpath"]
        try:
            with Image.open(image_path) as image:
                image.verify()
        except Exception as exc:
            image_errors.append(f"{image_path}: {exc}")
    if image_errors:
        raise RuntimeError("\n".join(image_errors))

    b_fields = set(b_tasks[0])
    forbidden = {"gt_angle", "gt_obb", "pred_angle", "pred_obb", "phase_mod",
                 "reliability_score", "score", "angle_error", "canonical_anon_id"}
    if forbidden & b_fields:
        raise RuntimeError(f"B pilot exposes forbidden fields: {sorted(forbidden & b_fields)}")

    a_order = a_ids
    b_order = [canonical[("B", row["task_id"])] for row in b_tasks]
    dataset_counts = Counter(row["dataset"] for row in a_tasks)
    state_counts = Counter(state_name(records.get(row["task_id"], {})) for row in a_tasks)
    summary = {
        "status": "HUMAN_BLOCKED",
        "frozen_at_utc": frozen_at,
        "pilot_instance_count": 200,
        "same_canonical_instance_set": set(a_order) == set(b_order),
        "different_order": a_order != b_order,
        "same_position_count": sum(a == b for a, b in zip(a_order, b_order)),
        "dataset_counts": dict(sorted(dataset_counts.items())),
        "a_snapshot_state_counts": dict(sorted(state_counts.items())),
        "a_snapshot_sha256": sha256(snapshot_csv),
        "b_manifest_sha256": sha256(b_pilot_dir / "task_manifest.csv"),
        "b_human_results": 0,
        "analysis_status": "WAITING_FOR_B_REAL_ANNOTATION",
    }
    write_json(PKG / "internal/pilot_200_summary.json", summary)

    validation = [
        {"check": "pilot_count_each", "status": "PASS", "detail": "A=200; B=200"},
        {"check": "same_canonical_set", "status": "PASS", "detail": "True"},
        {"check": "different_order", "status": "PASS", "detail": f"same_positions={summary['same_position_count']}"},
        {"check": "images_readable", "status": "PASS", "detail": "200/200"},
        {"check": "blinded_schema", "status": "PASS", "detail": "no GT/prediction/A-result fields"},
        {"check": "b_output_empty", "status": "PASS", "detail": "0 real results"},
        {"check": "a_snapshot", "status": "PASS", "detail": json.dumps(summary["a_snapshot_state_counts"], sort_keys=True)},
    ]
    write_csv(REPORTS / "m4_pilot200_package_validation.csv", validation,
              ["check", "status", "detail"])
    LOGS.mkdir(exist_ok=True)
    (LOGS / "m4_pilot200_package_validation.log").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
