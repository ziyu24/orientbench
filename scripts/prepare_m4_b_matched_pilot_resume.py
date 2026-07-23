#!/usr/bin/env python3
"""Resume B on A's canonical first 200 while preserving B's genuine overlap."""
from __future__ import annotations

import csv
import json
import os
import random
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation"
TASK_FIELDS = [
    "assignment_version", "annotator_slot", "task_order", "task_id", "dataset",
    "crop_relpath", "long_side_angle_deg_le90", "ambiguous", "skip", "notes",
    "annotator_id", "annotation_timestamp_utc",
]


def atomic_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    os.replace(temp, path)


def main() -> None:
    mapping_rows = list(csv.DictReader((PKG / "internal/instance_id_mapping.csv").open()))
    mapping = {(row["annotator_slot"], row["task_id"]): row["canonical_anon_id"]
               for row in mapping_rows}
    a_tasks = json.loads((PKG / "annotator_A/task_manifest.json").read_text())[:200]
    target = {mapping[("A", row["task_id"])] for row in a_tasks}
    b_tasks = [row.copy() for row in json.loads(
        (PKG / "annotator_B/task_manifest.json").read_text()
    ) if mapping[("B", row["task_id"])] in target]
    b_state_path = PKG / "annotator_B/outputs/draft_state.json"
    b_state = json.loads(b_state_path.read_text())
    completed = {
        task_id: record for task_id, record in b_state["records"].items()
        if mapping[("B", task_id)] in target
    }
    pending_tasks = [row for row in b_tasks if row["task_id"] not in completed]
    completed_tasks = [row for row in b_tasks if row["task_id"] in completed]
    random.Random(71202).shuffle(pending_tasks)
    random.Random(71203).shuffle(completed_tasks)
    ordered = pending_tasks + completed_tasks
    for index, row in enumerate(ordered, 1):
        row["task_order"] = str(index)

    pilot_dir = PKG / "annotator_B/pilot_200"
    atomic_json(pilot_dir / "task_manifest.json", ordered)
    csv_temp = (pilot_dir / "task_manifest.csv").with_suffix(".csv.tmp")
    with csv_temp.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=TASK_FIELDS)
        writer.writeheader()
        writer.writerows(ordered)
    os.replace(csv_temp, pilot_dir / "task_manifest.csv")

    pilot_output = PKG / "annotator_B/outputs_pilot_200"
    pilot_output.mkdir(parents=True, exist_ok=True)
    pilot_draft = pilot_output / "draft_state.json"
    if pilot_draft.exists():
        raise RuntimeError("pilot draft already exists; refusing to overwrite human work")
    atomic_json(pilot_draft, {
        "current_index": 0,
        "annotator_id": b_state.get("annotator_id", ""),
        "records": completed,
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
    })
    atomic_json(PKG / "internal/pilot_200_B_resume_audit.json", {
        "target_instances": 200,
        "preserved_genuine_b_annotations": len(completed),
        "remaining_for_b": len(pending_tasks),
        "source_full_b_records": len(b_state["records"]),
        "source_full_b_saved_at_utc": b_state.get("saved_at_utc"),
        "no_annotation_values_modified": True,
    })
    print(json.dumps({"preserved": len(completed), "remaining": len(pending_tasks)}))


if __name__ == "__main__":
    main()
