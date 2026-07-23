#!/usr/bin/env python3
"""Validate and merge the two independent Command-070 M4 annotation returns."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
TOOL = ROOT / "annotation_tools/m4_angle_annotation"
TASK_FIELDS_070 = {
    "assignment_version", "annotator_slot", "task_order", "task_id", "dataset",
    "crop_relpath", "long_side_angle_deg_le90", "ambiguous", "skip", "annotator_id",
    "annotation_timestamp_utc",
}
TASK_FIELDS_071 = TASK_FIELDS_070 | {"notes"}
FORBIDDEN = {"gt_angle", "gt_obb", "pred_angle", "pred_obb", "phase_mod",
             "reliability_score", "score", "angle_error", "canonical_anon_id"}
PAIR_FIELDS = [
    "anon_id", "dataset", "image_id", "pred_id", "matched_gt_class",
    "matched_gt_size_bin", "matched_gt_aspect_ratio", "matched_gt_ar_bin",
    "formal_ar21_eligible", "formal_stratum", "angleA", "angleB", "cannotA",
    "cannotB", "annotatorA_id_sha256", "annotatorB_id_sha256", "pair_status",
    "human_usable",
]


def read_csv(path: Path) -> tuple[list[dict], list[str]]:
    if not path.is_file():
        return [], []
    with path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        return list(reader), reader.fieldnames or []


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp, path)


def privacy_hash(value: str) -> str:
    return hashlib.sha256(("m4-annotator:" + value).encode()).hexdigest() if value else ""


def binary(value: str, name: str) -> bool:
    value = (value or "").strip().lower()
    if value in ("", "0", "false"):
        return False
    if value in ("1", "true"):
        return True
    raise ValueError(f"{name} must be blank/0/1")


def validate_return(rows: list[dict], fields: list[str], slot: str,
                    task_rows: list[dict]) -> tuple[dict, str, list[str]]:
    errors = []
    if set(fields) not in (TASK_FIELDS_070, TASK_FIELDS_071):
        errors.append(f"slot {slot}: raw schema mismatch")
    if FORBIDDEN.intersection(fields):
        errors.append(f"slot {slot}: forbidden fields present")
    task = {row["task_id"]: row for row in task_rows}
    raw = {}
    identities = set()
    for row in rows:
        identifier = row.get("task_id", "")
        if not identifier or identifier in raw or identifier not in task:
            errors.append(f"slot {slot}: duplicate/unknown task_id")
            continue
        expected = task[identifier]
        for key in ("assignment_version", "annotator_slot", "task_order", "task_id", "dataset", "crop_relpath"):
            if row.get(key, "") != expected.get(key, ""):
                errors.append(f"slot {slot}: changed {key} for {identifier}")
        if row.get("annotator_slot") != slot:
            errors.append(f"slot {slot}: wrong annotator slot")
        identity = row.get("annotator_id", "").strip()
        if identity:
            identities.add(identity)
        try:
            ambiguous = binary(row.get("ambiguous", ""), "ambiguous")
            skip = binary(row.get("skip", ""), "skip")
            angle_text = row.get("long_side_angle_deg_le90", "").strip()
            if sum((ambiguous, skip, bool(angle_text))) > 1:
                raise ValueError("angle/ambiguous/skip are mutually exclusive")
            if angle_text:
                angle = float(angle_text)
                if row.get("assignment_version", "").startswith("m4-071"):
                    if not 0.0 <= angle < 180.0:
                        raise ValueError("angle outside [0,180)")
                elif not -90.0 <= angle < 90.0:
                    raise ValueError("angle outside [-90,90)")
                state = "LABELED"
            elif ambiguous:
                angle = None
                state = "AMBIGUOUS"
            elif skip:
                angle = None
                state = "SKIP"
            else:
                angle = None
                state = "PENDING"
            raw[identifier] = {"state": state, "angle": angle, "row": row}
        except (TypeError, ValueError) as exc:
            errors.append(f"slot {slot}: {identifier}: {exc}")
    if len(identities) > 1:
        errors.append(f"slot {slot}: multiple annotator identities")
    identity = next(iter(identities)) if len(identities) == 1 else ""
    return raw, identity, errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--task-a", type=Path, default=TOOL / "annotator_A/tasks.csv")
    parser.add_argument("--task-b", type=Path, default=TOOL / "annotator_B/tasks.csv")
    parser.add_argument("--raw-a", type=Path, default=TOOL / "annotator_A/annotatorA_raw.csv")
    parser.add_argument("--raw-b", type=Path, default=TOOL / "annotator_B/annotatorB_raw.csv")
    parser.add_argument("--mapping", type=Path, default=TOOL / "internal_mapping_070.csv")
    parser.add_argument("--manifest", type=Path, default=ROOT / "reports/m4_human_annotation_sampling_manifest.csv")
    parser.add_argument("--output", type=Path, default=ROOT / "reports/m4_human_annotation_pairs.csv")
    parser.add_argument("--audit", type=Path, default=ROOT / "reports/m4_human_annotation_merge_audit.json")
    parser.add_argument("--min-per-dataset", type=int, default=200)
    args = parser.parse_args()

    tasks_a, fields_a = read_csv(args.task_a)
    tasks_b, fields_b = read_csv(args.task_b)
    mapping_rows, _ = read_csv(args.mapping)
    manifest_rows, _ = read_csv(args.manifest)
    raw_a, raw_fields_a = read_csv(args.raw_a)
    raw_b, raw_fields_b = read_csv(args.raw_b)
    errors = []
    if set(fields_a) not in (TASK_FIELDS_070, TASK_FIELDS_071) or set(fields_b) not in (
            TASK_FIELDS_070, TASK_FIELDS_071):
        errors.append("formal task schema mismatch")
    map_by_slot = {(row["annotator_slot"], row["task_id"]): row["canonical_anon_id"] for row in mapping_rows}
    manifest = {row["anon_id"]: row for row in manifest_rows}
    state_a, id_a, errors_a = validate_return(raw_a, raw_fields_a, "A", tasks_a) if raw_a else ({}, "", [])
    state_b, id_b, errors_b = validate_return(raw_b, raw_fields_b, "B", tasks_b) if raw_b else ({}, "", [])
    errors.extend(errors_a + errors_b)
    if id_a and id_b and id_a == id_b:
        errors.append("annotator A and B identities must differ")

    canonical_to_task = {"A": {}, "B": {}}
    for slot, tasks in (("A", tasks_a), ("B", tasks_b)):
        for task in tasks:
            canonical = map_by_slot.get((slot, task["task_id"]))
            if canonical:
                canonical_to_task[slot][canonical] = task["task_id"]
    if set(canonical_to_task["A"]) != set(canonical_to_task["B"]) or set(canonical_to_task["A"]) != set(manifest):
        errors.append("A/B/mapping/manifest target sets differ")

    pairs = []
    usable_counts = Counter()
    decision_complete_counts = Counter()
    for canonical, meta in manifest.items():
        a = state_a.get(canonical_to_task["A"].get(canonical, ""), {"state": "PENDING", "angle": None})
        b = state_b.get(canonical_to_task["B"].get(canonical, ""), {"state": "PENDING", "angle": None})
        complete = a["state"] == b["state"] == "LABELED"
        decision_complete = a["state"] != "PENDING" and b["state"] != "PENDING"
        if complete:
            usable_counts[meta["dataset"]] += 1
        if decision_complete:
            decision_complete_counts[meta["dataset"]] += 1
        pairs.append({
            "anon_id": canonical, "dataset": meta["dataset"], "image_id": meta["image_id"],
            "pred_id": meta["pred_id"], "matched_gt_class": meta["matched_gt_class"],
            "matched_gt_size_bin": meta["matched_gt_size_bin"],
            "matched_gt_aspect_ratio": meta["matched_gt_aspect_ratio"],
            "matched_gt_ar_bin": meta["matched_gt_ar_bin"],
            "formal_ar21_eligible": meta["formal_ar21_eligible"],
            "formal_stratum": meta["formal_stratum"],
            "angleA": "" if a["angle"] is None else f"{a['angle']:.6f}",
            "angleB": "" if b["angle"] is None else f"{b['angle']:.6f}",
            "cannotA": "1" if a["state"] in ("AMBIGUOUS", "SKIP") else "0",
            "cannotB": "1" if b["state"] in ("AMBIGUOUS", "SKIP") else "0",
            "annotatorA_id_sha256": privacy_hash(id_a), "annotatorB_id_sha256": privacy_hash(id_b),
            "pair_status": "COMPLETE" if complete else f"{a['state']}|{b['state']}",
            "human_usable": str(complete),
        })
    write_csv(args.output, pairs, PAIR_FIELDS)
    expected_datasets = {"DIOR-R", "FAIR1M-v1.0", "SODA-A"}
    # Ambiguous and skip are valid human decisions, not missing annotations.
    # The preregistered minimum applies to independently completed targets;
    # usable numeric angle pairs are reported separately.
    complete = (not errors and id_a and id_b and
                all(decision_complete_counts[dataset] >= args.min_per_dataset
                    for dataset in expected_datasets))
    status = "COMPLETE_INDEPENDENT_DOUBLE_ANNOTATION" if complete else "HUMAN_BLOCKED"
    audit = {
        "status": status, "errors": errors, "raw_a_exists": args.raw_a.is_file(),
        "raw_b_exists": args.raw_b.is_file(), "annotator_identities_distinct": bool(id_a and id_b and id_a != id_b),
        "usable_counts": dict(usable_counts), "minimum_per_dataset": args.min_per_dataset,
        "decision_complete_counts": dict(decision_complete_counts),
        "minimum_applies_to": "independently completed targets (angle/ambiguous/skip)",
        "pairs": len(pairs), "human_usable": sum(row["human_usable"] == "True" for row in pairs),
    }
    args.audit.parent.mkdir(parents=True, exist_ok=True)
    args.audit.write_text(json.dumps(audit, indent=2, sort_keys=True) + "\n")
    print(f"MERGE_{status} usable={audit['human_usable']}")
    return 2 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
