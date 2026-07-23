"""Build the blinded M4 long-axis double-annotation package.

The private sampling manifest uses matched-GT *non-angular* class, size, and
aspect ratio for the formal ar>=2.1 mask and the proxy-vs-human strata.  Prediction
geometry is used only to locate and crop the matched object.  Neither geometry role,
nor any GT/model angle or OBB, is exported to the A/B task CSVs.
"""

import argparse
import csv
import hashlib
import json
import math
import os
import random
import sys
from collections import defaultdict
from functools import lru_cache

sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench/scripts")
import m069_common as M


ROOT = "/home/rspip/cqc/pro/study/orientbench"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
TOOL = f"{ROOT}/annotation_tools/m4_angle_annotation"
CROP_DIR = f"{TOOL}/crops"
MANIFEST_PATH = f"{REP}/m4_human_annotation_sampling_manifest.csv"
BUILD_AUDIT_PATH = f"{REP}/m4_human_annotation_build_audit.json"
TARGET_PER_DATASET = 500
MIN_PER_DATASET = 200
DEFAULT_SEED = 20260712

DS_CELL = {
    "DIOR-R": "A",
    "FAIR1M-v1.0": "D",
    "SODA-A": "E",
}

IMAGE_ROOTS = {
    "DIOR-R": [
        "/home/rspip/cqc/data/dataset/DIOR/images/test",
        "/home/rspip/cqc/data/dataset/DIOR/images/trainval",
    ],
    "FAIR1M-v1.0": [
        "/home/rspip/cqc/data/dataset/fair1m1.0/split/val_20/images",
        "/home/rspip/cqc/data/dataset/fair1m1.0/split_ss_fair1m1.0/val/images",
    ],
    "SODA-A": [
        "/home/rspip/cqc/data/dataset/SODA-A/dota_format_tiled_ss/val_tiled/images",
    ],
}

IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".tif", ".tiff")
FORBIDDEN_BLIND_FIELDS = {
    "angle_error",
    "gt_angle",
    "gt_obb",
    "model_angle",
    "pred_angle",
    "pred_theta",
    "obb_theta",
    "phase_mod",
    "score",
    "matched_gt_class",
    "matched_gt_area_px2",
    "matched_gt_size_bin",
    "matched_gt_aspect_ratio",
    "matched_gt_ar_bin",
    "formal_ar21_eligible",
    "formal_stratum",
    "formal_geometry_source",
    "formal_class_source",
    "locator_geometry_source",
    "locator_cx",
    "locator_cy",
    "locator_box_xmin",
    "locator_box_ymin",
    "locator_box_xmax",
    "locator_box_ymax",
}

MANIFEST_FIELDS = [
    "anon_id",
    "dataset",
    "image_id",
    "pred_id",
    "matched_gt_class",
    "matched_gt_area_px2",
    "matched_gt_size_bin",
    "matched_gt_aspect_ratio",
    "matched_gt_ar_bin",
    "formal_ar21_eligible",
    "formal_stratum",
    "formal_geometry_source",
    "formal_class_source",
    "locator_geometry_source",
    "source_image_path",
    "source_image_sha256",
    "image_width",
    "image_height",
    "locator_cx",
    "locator_cy",
    "locator_box_xmin",
    "locator_box_ymin",
    "locator_box_xmax",
    "locator_box_ymax",
    "crop_xmin",
    "crop_ymin",
    "crop_xmax",
    "crop_ymax",
    "crop_relpath",
    "crop_sha256",
    "source_record_path",
    "source_record_sha256",
    "source_record_line",
    "sampling_seed",
    "sampling_rank",
]

TASK_FIELDS = [
    "assignment_version",
    "annotator_slot",
    "task_order",
    "anon_id",
    "dataset",
    "image_id",
    "pred_id",
    "crop_relpath",
    "long_side_angle_deg_le90",
    "cannot_determine",
    "annotator_id",
    "annotation_timestamp_utc",
]


def ar_bin(aspect_ratio):
    if aspect_ratio < 1.6:
        return "ar<1.6"
    if aspect_ratio < 2.1:
        return "1.6<=ar<2.1"
    return "ar>=2.1"


def size_bin(area):
    side = math.sqrt(max(float(area), 0.0))
    if side < 32:
        return "small"
    if side < 96:
        return "medium"
    return "large"


@lru_cache(maxsize=None)
def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve_image_path(dataset, image_id):
    image_id = str(image_id)
    stem, ext = os.path.splitext(image_id)
    names = [image_id] if ext.lower() in IMAGE_EXTENSIONS else [image_id + e for e in IMAGE_EXTENSIONS]
    for root in IMAGE_ROOTS[dataset]:
        for name in names:
            path = os.path.join(root, name)
            if os.path.isfile(path):
                return os.path.realpath(path)
    return None


def iter_candidates(dataset, cell):
    """Yield candidates with separated formal GT strata and prediction locators."""
    source_path = M.CELLS[cell][2]
    with open(source_path) as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            record = json.loads(line)
            pred = record.get("pred_obb") or {}
            gt = record.get("gt_obb") or {}
            try:
                cx = float(pred["obb_cx"])
                cy = float(pred["obb_cy"])
                width = abs(float(pred["obb_w"]))
                height = abs(float(pred["obb_h"]))
                gt_width = abs(float(gt["obb_w"]))
                gt_height = abs(float(gt["obb_h"]))
            except (KeyError, TypeError, ValueError):
                continue
            if (
                not all(math.isfinite(v) for v in (cx, cy, width, height, gt_width, gt_height))
                or min(width, height, gt_width, gt_height) <= 0
            ):
                continue
            image_id = str(record.get("image_id", ""))
            pred_id = str(record.get("pred_id", line_number - 1))
            image_path = resolve_image_path(dataset, image_id)
            if image_path is None:
                continue
            gt_aspect_ratio = max(gt_width, gt_height) / min(gt_width, gt_height)
            gt_area = gt_width * gt_height
            gt_size_bin = size_bin(gt_area)
            # Full-val matching is class constrained, so this serialized class is
            # also the matched-GT class without exporting a GT OBB or angle.
            gt_class = str(record.get("class", "unknown"))
            yield {
                "dataset": dataset,
                "image_id": image_id,
                "pred_id": pred_id,
                "matched_gt_class": gt_class,
                "matched_gt_area_px2": gt_area,
                "matched_gt_size_bin": gt_size_bin,
                "matched_gt_aspect_ratio": gt_aspect_ratio,
                "matched_gt_ar_bin": ar_bin(gt_aspect_ratio),
                "source_image_path": image_path,
                "locator_cx": cx,
                "locator_cy": cy,
                "locator_width": width,
                "locator_height": height,
                "source_record_path": source_path,
                "source_record_line": line_number,
            }


def _spread_images(rows, rng):
    rows = list(rows)
    rng.shuffle(rows)
    first, repeated, seen = [], [], set()
    for row in rows:
        image_id = row["image_id"]
        if image_id in seen:
            repeated.append(row)
        else:
            seen.add(image_id)
            first.append(row)
    return first + repeated


def _proportional_quotas(groups, target):
    """Allocate a nonzero quota per stratum, then fill to exactly target."""
    keys = sorted(groups)
    available = {key: len(groups[key]) for key in keys}
    total = sum(available.values())
    if target >= total:
        return available
    if len(keys) > target:
        # Preserve the largest strata when there are more strata than slots.
        chosen = sorted(keys, key=lambda key: (-available[key], key))[:target]
        return {key: (1 if key in chosen else 0) for key in keys}

    raw = {key: target * available[key] / total for key in keys}
    quota = {key: min(available[key], max(1, int(math.floor(raw[key])))) for key in keys}
    while sum(quota.values()) > target:
        candidates = [key for key in keys if quota[key] > 1]
        key = max(candidates, key=lambda item: (quota[item] - raw[item], quota[item], item))
        quota[key] -= 1
    while sum(quota.values()) < target:
        candidates = [key for key in keys if quota[key] < available[key]]
        if not candidates:
            break
        key = max(candidates, key=lambda item: (raw[item] - quota[item], available[item] - quota[item], item))
        quota[key] += 1
    return quota


def stratified_sample(candidates, target=TARGET_PER_DATASET, seed=DEFAULT_SEED):
    candidates = list(candidates)
    if len(candidates) < MIN_PER_DATASET:
        raise RuntimeError(f"only {len(candidates)} locatable candidates; need >= {MIN_PER_DATASET}")
    target = min(int(target), len(candidates))
    groups = defaultdict(list)
    for row in candidates:
        key = (
            row["matched_gt_class"],
            row["matched_gt_size_bin"],
            row["matched_gt_ar_bin"],
        )
        groups[key].append(row)
    quota = _proportional_quotas(groups, target)
    picks = []
    for index, key in enumerate(sorted(groups)):
        rng = random.Random(seed + index * 7919)
        ordered = _spread_images(groups[key], rng)
        picks.extend(ordered[: quota[key]])
    random.Random(seed + 104729).shuffle(picks)
    if len(picks) != target:
        raise AssertionError(f"sampler returned {len(picks)} rows, expected {target}")
    return picks


def _crop_geometry(cx, cy, width, height, image_width, image_height):
    half = max(48.0, 0.90 * max(width, height))
    xmin = max(0, int(math.floor(cx - half)))
    ymin = max(0, int(math.floor(cy - half)))
    xmax = min(int(image_width), int(math.ceil(cx + half)))
    ymax = min(int(image_height), int(math.ceil(cy + half)))
    if xmax <= xmin or ymax <= ymin:
        raise ValueError("empty crop")
    return xmin, ymin, xmax, ymax


def materialize_manifest_row(candidate, sampling_seed, sampling_rank, write_crop=True):
    from PIL import Image

    identity = f"{candidate['dataset']}:{candidate['image_id']}:{candidate['pred_id']}"
    anon_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
    with Image.open(candidate["source_image_path"]) as image:
        image_width, image_height = image.size
        crop_box = _crop_geometry(
            candidate["locator_cx"],
            candidate["locator_cy"],
            candidate["locator_width"],
            candidate["locator_height"],
            image_width,
            image_height,
        )
        crop_relpath = f"crops/{anon_id}.jpg"
        if write_crop:
            os.makedirs(CROP_DIR, exist_ok=True)
            crop = image.convert("RGB").crop(crop_box)
            crop.thumbnail((768, 768))
            crop.save(os.path.join(TOOL, crop_relpath), format="JPEG", quality=92, optimize=True)
    crop_path = os.path.join(TOOL, crop_relpath)
    crop_sha = sha256_file(crop_path) if write_crop else ""

    radius = max(24.0, 0.55 * max(candidate["locator_width"], candidate["locator_height"]))
    locator_box = (
        max(0.0, candidate["locator_cx"] - radius),
        max(0.0, candidate["locator_cy"] - radius),
        min(float(image_width), candidate["locator_cx"] + radius),
        min(float(image_height), candidate["locator_cy"] + radius),
    )
    return {
        "anon_id": anon_id,
        "dataset": candidate["dataset"],
        "image_id": candidate["image_id"],
        "pred_id": candidate["pred_id"],
        "matched_gt_class": candidate["matched_gt_class"],
        "matched_gt_area_px2": round(candidate["matched_gt_area_px2"], 4),
        "matched_gt_size_bin": candidate["matched_gt_size_bin"],
        "matched_gt_aspect_ratio": round(candidate["matched_gt_aspect_ratio"], 6),
        "matched_gt_ar_bin": candidate["matched_gt_ar_bin"],
        "formal_ar21_eligible": str(candidate["matched_gt_aspect_ratio"] >= 2.1),
        "formal_stratum": (
            f"{candidate['matched_gt_class']}|{candidate['matched_gt_size_bin']}|"
            f"{candidate['matched_gt_ar_bin']}"
        ),
        "formal_geometry_source": "matched_GT_box_nonangular",
        "formal_class_source": "matched_GT_class_via_class_constrained_match",
        "locator_geometry_source": "matched_prediction_box_nonangular",
        "source_image_path": candidate["source_image_path"],
        "source_image_sha256": sha256_file(candidate["source_image_path"]),
        "image_width": image_width,
        "image_height": image_height,
        "locator_cx": round(candidate["locator_cx"], 2),
        "locator_cy": round(candidate["locator_cy"], 2),
        "locator_box_xmin": round(locator_box[0], 2),
        "locator_box_ymin": round(locator_box[1], 2),
        "locator_box_xmax": round(locator_box[2], 2),
        "locator_box_ymax": round(locator_box[3], 2),
        "crop_xmin": crop_box[0],
        "crop_ymin": crop_box[1],
        "crop_xmax": crop_box[2],
        "crop_ymax": crop_box[3],
        "crop_relpath": crop_relpath,
        "crop_sha256": crop_sha,
        "source_record_path": candidate["source_record_path"],
        "source_record_sha256": sha256_file(candidate["source_record_path"]),
        "source_record_line": candidate["source_record_line"],
        "sampling_seed": sampling_seed,
        "sampling_rank": sampling_rank,
    }


def write_csv(path, fieldnames, rows):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    temporary = path + ".tmp"
    with open(temporary, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def build_task_rows(manifest, slot, seed, assignment_version):
    ordered = list(manifest)
    random.Random(seed).shuffle(ordered)
    rows = []
    for task_order, row in enumerate(ordered, 1):
        rows.append({
            "assignment_version": assignment_version,
            "annotator_slot": slot,
            "task_order": task_order,
            "anon_id": row["anon_id"],
            "dataset": row["dataset"],
            "image_id": row["image_id"],
            "pred_id": row["pred_id"],
            "crop_relpath": row["crop_relpath"],
            "long_side_angle_deg_le90": "",
            "cannot_determine": "",
            "annotator_id": "",
            "annotation_timestamp_utc": "",
        })
    return rows


def validate_blinded_task(rows):
    if not rows:
        raise ValueError("empty annotation task")
    fields = set(rows[0])
    if fields != set(TASK_FIELDS):
        raise ValueError(
            f"blind task schema differs from frozen allowlist: extra={sorted(fields - set(TASK_FIELDS))}; "
            f"missing={sorted(set(TASK_FIELDS) - fields)}"
        )
    leaked = FORBIDDEN_BLIND_FIELDS.intersection(fields)
    if leaked:
        raise ValueError(f"blind task contains forbidden fields: {sorted(leaked)}")
    if any(row["long_side_angle_deg_le90"] or row["cannot_determine"] for row in rows):
        raise ValueError("task contains pre-filled annotation values")
    ids = [row["anon_id"] for row in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate anon_id in task")


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", type=int, default=TARGET_PER_DATASET)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--no-crops", action="store_true", help="fixture/debug only; official package must include crops")
    parser.add_argument("--force", action="store_true", help="allow rebuilding tasks after raw-label files exist")
    args = parser.parse_args(argv)

    raw_paths = [f"{TOOL}/annotatorA_raw.csv", f"{TOOL}/annotatorB_raw.csv"]
    if not args.force and any(os.path.exists(path) for path in raw_paths):
        raise SystemExit("refusing to rebuild assignments after raw human labels exist; use --force only after audit")

    os.makedirs(TOOL, exist_ok=True)
    manifest = []
    per_dataset = {}
    for dataset_index, (dataset, cell) in enumerate(DS_CELL.items()):
        M.verify_fullval_lineage(cell)
        dataset_seed = args.seed + dataset_index * 100003
        candidates = list(iter_candidates(dataset, cell))
        picks = stratified_sample(candidates, target=args.target, seed=dataset_seed)
        if len(picks) < MIN_PER_DATASET:
            raise RuntimeError(f"{dataset}: selected {len(picks)} < {MIN_PER_DATASET}")
        for rank, candidate in enumerate(picks, 1):
            manifest.append(
                materialize_manifest_row(
                    candidate,
                    sampling_seed=dataset_seed,
                    sampling_rank=rank,
                    write_crop=not args.no_crops,
                )
            )
        per_dataset[dataset] = {
            "candidate_count": len(candidates),
            "selected_count": len(picks),
            "unique_images": len({row["image_id"] for row in picks}),
            "available_size_bins": sorted({row["matched_gt_size_bin"] for row in candidates}),
            "available_ar_bins": sorted({row["matched_gt_ar_bin"] for row in candidates}),
            "available_classes": sorted({row["matched_gt_class"] for row in candidates}),
            "selected_size_bins": sorted({row["matched_gt_size_bin"] for row in picks}),
            "selected_ar_bins": sorted({row["matched_gt_ar_bin"] for row in picks}),
            "selected_classes": sorted({row["matched_gt_class"] for row in picks}),
        }

    if len({row["anon_id"] for row in manifest}) != len(manifest):
        raise RuntimeError("anon_id collision")
    if not args.no_crops and any(
        not row["crop_sha256"]
        or sha256_file(os.path.join(TOOL, row["crop_relpath"])) != row["crop_sha256"]
        for row in manifest
    ):
        raise RuntimeError("materialized crop SHA validation failed")
    write_csv(MANIFEST_PATH, MANIFEST_FIELDS, manifest)
    manifest_sha = sha256_file(MANIFEST_PATH)
    assignment_version = f"m4-v3-{manifest_sha[:12]}"
    task_a = build_task_rows(manifest, "A", args.seed + 101, assignment_version)
    task_b = build_task_rows(manifest, "B", args.seed + 202, assignment_version)
    validate_blinded_task(task_a)
    validate_blinded_task(task_b)
    if [row["anon_id"] for row in task_a] == [row["anon_id"] for row in task_b]:
        task_b = task_b[1:] + task_b[:1]
    if {row["anon_id"] for row in task_a} != {row["anon_id"] for row in task_b}:
        raise RuntimeError("annotator assignments do not contain the same target set")

    task_a_path = f"{TOOL}/annotatorA_tasks.csv"
    task_b_path = f"{TOOL}/annotatorB_tasks.csv"
    write_csv(task_a_path, TASK_FIELDS, task_a)
    write_csv(task_b_path, TASK_FIELDS, task_b)
    audit = {
        "status": "READY_FOR_TWO_INDEPENDENT_HUMAN_ANNOTATORS" if not args.no_crops else "FIXTURE_ONLY_CROPS_NOT_MATERIALIZED",
        "assignment_version": assignment_version,
        "minimum_per_dataset": MIN_PER_DATASET,
        "target_per_dataset": args.target,
        "per_dataset": per_dataset,
        "manifest": {"path": MANIFEST_PATH, "sha256": manifest_sha, "rows": len(manifest)},
        "annotator_a_task": {"path": task_a_path, "sha256": sha256_file(task_a_path), "rows": len(task_a)},
        "annotator_b_task": {"path": task_b_path, "sha256": sha256_file(task_b_path), "rows": len(task_b)},
        "same_target_set": True,
        "different_random_order": True,
        "gt_or_model_angle_exported": False,
        "gt_or_model_obb_exported_to_tasks": False,
        "formal_strata_geometry": "matched_GT_box_nonangular",
        "formal_class_source": "matched_GT_class_via_class_constrained_match",
        "formal_mask_definition": "matched_GT_aspect_ratio>=2.1",
        "locator_geometry": "matched_prediction_box_nonangular",
        "task_schema_is_exact_allowlist": True,
        "crops_materialized": not args.no_crops,
        "crop_sha256_bound_in_manifest": not args.no_crops,
        "source_record_sha256_bound_in_manifest": True,
    }
    with open(BUILD_AUDIT_PATH + ".tmp", "w") as handle:
        json.dump(audit, handle, indent=2, ensure_ascii=False)
    os.replace(BUILD_AUDIT_PATH + ".tmp", BUILD_AUDIT_PATH)
    print(f"HUMAN_TOOLING_READY rows={len(manifest)} version={assignment_version}")


if __name__ == "__main__":
    main()
