#!/usr/bin/env python3
"""Build two self-contained, mutually blinded M4 annotation execution packages."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import random
import shutil
from collections import Counter
from pathlib import Path

from PIL import Image

ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
TOOL = ROOT / "annotation_tools/m4_angle_annotation"
MANIFEST = ROOT / "reports/m4_human_annotation_sampling_manifest.csv"
INTERNAL = TOOL / "internal_mapping_070.csv"
VALIDATION = ROOT / "reports/m4_human_annotation_package_validation.csv"
VERSION = "m4-070-final-v1"
TASK_FIELDS = [
    "assignment_version", "annotator_slot", "task_order", "task_id", "dataset",
    "crop_relpath", "long_side_angle_deg_le90", "ambiguous", "skip",
    "annotator_id", "annotation_timestamp_utc",
]
FORBIDDEN = {
    "gt_angle", "gt_obb", "pred_angle", "pred_obb", "detector_prediction", "phase_mod",
    "reliability_score", "score", "angle_error", "canonical_anon_id", "image_id", "pred_id",
}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def task_id(slot: str, canonical: str) -> str:
    return hashlib.sha256(f"m4-070:{slot}:{canonical}".encode()).hexdigest()[:20]


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp, path)


def main() -> int:
    preserved_checks = {
        "browser_start_save_restore_export_csv_json", "merge_script_smoke",
        "disagreement_analysis_smoke", "smoke_data_isolated_from_formal_results",
    }
    preserved = []
    if VALIDATION.is_file():
        preserved = [row for row in csv.DictReader(VALIDATION.open())
                     if row.get("check") in preserved_checks]
    manifest = list(csv.DictReader(MANIFEST.open()))
    counts = Counter(row["dataset"] for row in manifest)
    expected = {"DIOR-R": 500, "FAIR1M-v1.0": 500, "SODA-A": 500}
    if counts != Counter(expected):
        raise RuntimeError(f"unexpected sampling counts: {counts}")
    rows_by_slot = {}
    mapping = []
    validation = []
    for slot, seed in (("A", 7001), ("B", 7002)):
        package = TOOL / f"annotator_{slot}"
        crops = package / "crops"
        package.mkdir(parents=True, exist_ok=True)
        crops.mkdir(parents=True, exist_ok=True)
        order = list(manifest)
        random.Random(seed).shuffle(order)
        tasks = []
        for index, row in enumerate(order, 1):
            canonical = row["anon_id"]
            identifier = task_id(slot, canonical)
            source = TOOL / row["crop_relpath"]
            if not source.is_file() or sha256(source) != row["crop_sha256"]:
                raise RuntimeError(f"missing or changed crop: {source}")
            with Image.open(source) as image:
                image.verify()
            destination = crops / f"{identifier}.jpg"
            if destination.exists():
                if sha256(destination) != sha256(source):
                    raise RuntimeError(f"refuse to overwrite changed package crop: {destination}")
            else:
                os.link(source, destination)
            tasks.append({
                "assignment_version": VERSION, "annotator_slot": slot,
                "task_order": index, "task_id": identifier, "dataset": row["dataset"],
                "crop_relpath": f"crops/{identifier}.jpg", "long_side_angle_deg_le90": "",
                "ambiguous": "", "skip": "", "annotator_id": "",
                "annotation_timestamp_utc": "",
            })
            mapping.append({
                "assignment_version": VERSION, "annotator_slot": slot,
                "task_id": identifier, "canonical_anon_id": canonical,
                "dataset": row["dataset"], "task_order": index,
                "package_crop_sha256": sha256(destination),
            })
        write_csv(package / "tasks.csv", tasks, TASK_FIELDS)
        shutil.copy2(TOOL / "index.html", package / "index.html")
        shutil.copy2(TOOL / "README_ANNOTATOR_ZH.md", package / "README_ANNOTATOR_ZH.md")
        rows_by_slot[slot] = tasks
        validation.append({
            "check": f"annotator_{slot}_package", "status": "PASS", "dataset": "ALL",
            "count": len(tasks), "evidence": f"different_random_seed={seed}; self-contained crops=1500",
        })
    write_csv(INTERNAL, mapping, list(mapping[0]))

    ids_a = {row["task_id"] for row in rows_by_slot["A"]}
    ids_b = {row["task_id"] for row in rows_by_slot["B"]}
    canonical_a = {row["canonical_anon_id"] for row in mapping if row["annotator_slot"] == "A"}
    canonical_b = {row["canonical_anon_id"] for row in mapping if row["annotator_slot"] == "B"}
    validation.extend([
        {"check": "different_anonymous_ids", "status": "PASS" if not ids_a & ids_b else "FAIL",
         "dataset": "ALL", "count": len(ids_a & ids_b), "evidence": "A/B task_id sets disjoint"},
        {"check": "same_target_set", "status": "PASS" if canonical_a == canonical_b else "FAIL",
         "dataset": "ALL", "count": len(canonical_a), "evidence": "private mapping only"},
        {"check": "different_random_order", "status": "PASS" if [r["dataset"] + r["task_id"] for r in rows_by_slot["A"]] != [r["dataset"] + r["task_id"] for r in rows_by_slot["B"]] else "FAIL",
         "dataset": "ALL", "count": 1500, "evidence": "independent fixed random seeds"},
        {"check": "blind_schema", "status": "PASS" if not FORBIDDEN.intersection(TASK_FIELDS) else "FAIL",
         "dataset": "ALL", "count": len(TASK_FIELDS), "evidence": "allowlisted task schema"},
    ])
    for dataset, expected_count in expected.items():
        subset = [row for row in manifest if row["dataset"] == dataset]
        ar21 = sum(row["formal_ar21_eligible"] == "True" for row in subset)
        readable = sum(Path(row["source_image_path"]).is_file() for row in subset)
        strata = len({(row["matched_gt_class"], row["matched_gt_size_bin"], row["matched_gt_ar_bin"])
                      for row in subset})
        status = "PASS" if len(subset) == expected_count and readable == expected_count and ar21 >= 200 else "FAIL"
        validation.append({
            "check": "dataset_sampling_and_source_validation", "status": status,
            "dataset": dataset, "count": len(subset),
            "evidence": f"source_images_readable={readable}; ar21={ar21}; nonempty_strata={strata}",
        })
    write_csv(VALIDATION, validation + preserved, list(validation[0]))
    if any(row["status"] != "PASS" for row in validation):
        raise RuntimeError("annotation package validation failed")
    audit = {
        "status": "READY_FOR_TWO_INDEPENDENT_HUMAN_ANNOTATORS",
        "assignment_version": VERSION, "counts": expected,
        "real_human_results": 0, "human_status": "HUMAN_BLOCKED",
        "internal_mapping": str(INTERNAL.relative_to(ROOT)),
    }
    (TOOL / "package_build_audit_070.json").write_text(json.dumps(audit, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
