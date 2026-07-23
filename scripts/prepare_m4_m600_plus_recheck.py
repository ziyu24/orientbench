#!/usr/bin/env python3
"""Prepare 74 new matched targets plus blinded rechecks of one-sided labels."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import shutil
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
ASSIGN_FIELDS = [
    "annotator_slot", "task_id", "canonical_anon_id", "task_kind",
    "original_task_id", "original_pair_status", "original_missing_state",
]


def read_csv(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def atomic_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def atomic_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    os.replace(temporary, path)


def anon_id(slot: str, canonical: str) -> str:
    return hashlib.sha256(f"m4-m600-recheck-v1:{slot}:{canonical}".encode()).hexdigest()[:20]


def main() -> None:
    mapping_rows = read_csv(PKG / "internal/instance_id_mapping.csv")
    to_canonical = {(row["annotator_slot"], row["task_id"]): row["canonical_anon_id"]
                    for row in mapping_rows}
    full = {slot: json.loads((PKG / f"annotator_{slot}/task_manifest.json").read_text())
            for slot in "AB"}
    task_by_id = {slot: {row["task_id"]: row for row in full[slot]} for slot in "AB"}
    by_canonical = {slot: {to_canonical[(slot, row["task_id"])]: row for row in full[slot]}
                    for slot in "AB"}
    b526_sampling = read_csv(PKG / "internal/b526_sampling_manifest.csv")
    existing = {row["anon_id"] for row in b526_sampling}
    sampling = read_csv(ROOT / "reports/m4_human_annotation_sampling_manifest.csv")
    additions = []
    needed = {"DIOR-R": 30, "FAIR1M-v1.0": 23, "SODA-A": 21}
    for dataset, count in needed.items():
        candidates = [row for row in sampling if row["dataset"] == dataset and row["anon_id"] not in existing]
        candidates.sort(key=lambda row: int(row["sampling_rank"]))
        additions.extend(candidates[:count])
    if len(additions) != 74 or Counter(row["dataset"] for row in additions) != Counter(needed):
        raise RuntimeError("could not construct the preregistered 30/23/21 top-up")
    new_ids = {row["anon_id"] for row in additions}
    target_sampling = b526_sampling + additions
    if Counter(row["dataset"] for row in target_sampling) != Counter(
            {"DIOR-R": 200, "FAIR1M-v1.0": 200, "SODA-A": 200}):
        raise RuntimeError("m600 target is not exactly 200 per dataset")

    pairs = read_csv(ROOT / "reports/m4_b526_pairs.csv")
    rechecks = {"A": [], "B": []}
    for row in pairs:
        if "|" not in row["pair_status"]:
            continue
        left, right = row["pair_status"].split("|")
        if left == "LABELED" and right in {"AMBIGUOUS", "SKIP"}:
            rechecks["B"].append((row, right))
        elif right == "LABELED" and left in {"AMBIGUOUS", "SKIP"}:
            rechecks["A"].append((row, left))
    if len(rechecks["A"]) != 12 or len(rechecks["B"]) != 17:
        raise RuntimeError("expected A=12 and B=17 one-sided rechecks")

    assignment_rows = []
    summary = {"created_at_utc": datetime.now(timezone.utc).isoformat(), "slots": {}}
    for slot in "AB":
        tasks = []
        for canonical in sorted(new_ids):
            row = by_canonical[slot][canonical].copy()
            tasks.append(row)
            assignment_rows.append({
                "annotator_slot": slot, "task_id": row["task_id"],
                "canonical_anon_id": canonical, "task_kind": "NEW_M600_TARGET",
                "original_task_id": row["task_id"], "original_pair_status": "",
                "original_missing_state": "",
            })
        for pair, missing_state in rechecks[slot]:
            canonical = pair["anon_id"]
            original = by_canonical[slot][canonical]
            new_id = anon_id(slot, canonical)
            source = PKG / f"annotator_{slot}" / original["crop_relpath"]
            target = PKG / f"annotator_{slot}/images/{new_id}.jpg"
            if target.exists():
                if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(source.read_bytes()).digest():
                    raise RuntimeError(f"recheck image collision: {target}")
            else:
                shutil.copy2(source, target)
            row = {
                "assignment_version": "m4-m600-recheck-v1", "annotator_slot": slot,
                "task_order": "", "task_id": new_id, "dataset": original["dataset"],
                "crop_relpath": f"images/{new_id}.jpg", "long_side_angle_deg_le90": "",
                "ambiguous": "", "skip": "", "notes": "", "annotator_id": "",
                "annotation_timestamp_utc": "",
            }
            tasks.append(row)
            assignment_rows.append({
                "annotator_slot": slot, "task_id": new_id,
                "canonical_anon_id": canonical, "task_kind": "ONE_SIDED_RECHECK",
                "original_task_id": original["task_id"],
                "original_pair_status": pair["pair_status"],
                "original_missing_state": missing_state,
            })
        random.Random(71600 if slot == "A" else 71601).shuffle(tasks)
        for order, row in enumerate(tasks, 1):
            row["task_order"] = str(order)
        task_dir = PKG / f"annotator_{slot}/m600_plus_recheck"
        atomic_csv(task_dir / "task_manifest.csv", tasks, FIELDS)
        atomic_json(task_dir / "task_manifest.json", tasks)
        output = PKG / f"annotator_{slot}/outputs_m600_plus_recheck"
        output.mkdir(parents=True, exist_ok=True)
        if list(output.iterdir()):
            raise RuntimeError(f"refusing to overwrite {slot} m600 output")
        prior_state = json.loads((PKG / f"annotator_{slot}/outputs/draft_state.json").read_text())
        atomic_json(output / "draft_state.json", {
            "current_index": 0, "annotator_id": prior_state["annotator_id"],
            "records": {}, "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        })
        summary["slots"][slot] = {
            "displayed_total": len(tasks), "new_m600_targets": 74,
            "one_sided_rechecks": len(rechecks[slot]),
            "displayed_by_dataset": dict(sorted(Counter(row["dataset"] for row in tasks).items())),
        }

    atomic_csv(PKG / "internal/m600_tranche_assignment.csv", assignment_rows, ASSIGN_FIELDS)
    atomic_json(PKG / "internal/m600_tranche_assignment.json", assignment_rows)
    atomic_csv(PKG / "internal/m600_sampling_manifest.csv", target_sampling, list(target_sampling[0]))
    for slot in "AB":
        target_tasks = [by_canonical[slot][row["anon_id"]].copy() for row in target_sampling]
        atomic_csv(PKG / f"annotator_{slot}/m600_target/task_manifest.csv", target_tasks, FIELDS)
        atomic_json(PKG / f"annotator_{slot}/m600_target/task_manifest.json", target_tasks)
    summary["m600_target_by_dataset"] = dict(Counter(row["dataset"] for row in target_sampling))
    summary["selection_rule"] = "lowest unused frozen sampling_rank within each dataset"
    summary["recheck_primary_policy"] = "original annotations remain primary; rechecks are secondary"
    atomic_json(PKG / "internal/m600_plus_recheck_summary.json", summary)
    print(json.dumps(summary, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
