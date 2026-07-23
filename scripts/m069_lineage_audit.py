#!/usr/bin/env python3
"""Audit command-069 DIOR replacement lineage and clean DOTA artifacts.

This is deliberately a read-only artifact verifier.  It never imports the
detector stack and cannot start inference or training.  The audit report and
resolution note are written atomically, then the command exits nonzero until
all three DIOR A-C replacement manifests are complete and internally valid.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
from pathlib import Path
from typing import Any, Callable


ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
REPORT_DIR = ROOT / "reports"
DOC_DIR = ROOT / "docs"

DIOR_SPLIT_DIR = Path("/home/rspip/cqc/data/dataset/DIOR/splits")
DIOR_052_INDEX = ROOT / "top_journal_v3/reports/full_matched_tables_052.csv"
DIOR_052_ROOT = ROOT / "outputs/persistent_artifacts/orientbench_real_052/matched_tables/DIOR-R"
DIOR_069_ROOT = ROOT / "outputs/persistent_artifacts/m069_fullval_reliability"
DIOR_AUDIT_CSV = REPORT_DIR / "069_dior_partial_gt_lineage_audit.csv"

DOTA_ROOT = ROOT / "top_journal_v3_reaudit_055/reports/m_dota_clean_perinstance"
DOTA_METRICS_ROOT = ROOT / "top_journal_v3_reaudit_055/reports/k4b_dota"
DOTA_DATA_ROOT = Path("/home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10/val")
DOTA_LOG = ROOT / "top_journal_v3_reaudit_055/logs/m069/m_dota_dump.log"
DOTA_GENERATOR = ROOT / "scripts/m_dota_dump.py"
DOTA_MANIFEST_CSV = REPORT_DIR / "069_dota_clean_artifact_manifest.csv"

RESOLUTION_DOC = DOC_DIR / "069_dior_partial_gt_lineage_resolution.md"

EXPECTED_DIOR_IMAGES = 11738
EXPECTED_DIOR_GT = 124445
EXPECTED_DIOR_TEST_MIN = 11726
EXPECTED_DIOR_TEST_MAX = 23463
EXPECTED_DOTA_IMAGES = 5297
EXPECTED_DOTA_GT = 55804

DIOR_SPECS = {
    "A": {
        "cell_id": "DIOR-R/22",
        "old_baseline_id": "22",
        "detector": "rotated_retinanet_psc",
    },
    "B": {
        "cell_id": "DIOR-R/3",
        "old_baseline_id": "3",
        "detector": "oriented_rcnn",
    },
    "C": {
        "cell_id": "DIOR-R/61",
        "old_baseline_id": "61",
        "detector": "rotated_rtmdet_s",
    },
}

DOTA_SPECS = {
    "DOTA-v1.0/orcnn": {
        "detector": "oriented_rcnn",
        "artifact": DOTA_ROOT / "DOTA_orcnn.jsonl",
        "metrics": DOTA_METRICS_ROOT / "DOTA-v1.0_orcnn.json",
        "checkpoint": Path(
            "/home/rspip/cqc/pro/study/pth_data/"
            "baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/"
            "best_mAP_7061_epoch_11.pth"
        ),
        "config": Path(
            "/home/rspip/cqc/pro/study/pth_data/"
            "baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/config.py"
        ),
        "expected_rows": 48889,
        "expected_ap50": 0.7061,
        "log_key": "orcnn",
    },
    "DOTA-v1.0/rtmdet": {
        "detector": "rotated_rtmdet_m",
        "artifact": DOTA_ROOT / "DOTA_rtmdet.jsonl",
        "metrics": DOTA_METRICS_ROOT / "DOTA-v1.0_rtmdet.json",
        "checkpoint": Path(
            "/home/rspip/cqc/pro/study/pth_data/"
            "baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/"
            "best_mAP_7161_epoch_31.pth"
        ),
        "config": Path(
            "/home/rspip/cqc/pro/study/pth_data/"
            "baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/config.py"
        ),
        "expected_rows": 51736,
        "expected_ap50": 0.7161,
        "log_key": "rtmdet",
    },
}

DIOR_FIELDS = [
    "record_type",
    "cell",
    "cell_id",
    "detector",
    "generation",
    "status",
    "integrity_pass",
    "artifact_path",
    "artifact_bytes",
    "artifact_sha256",
    "manifest_path",
    "manifest_sha256",
    "universe_path",
    "universe_sha256",
    "gt_path",
    "gt_sha256",
    "source_split",
    "source_id_domain",
    "metadata_image_count",
    "artifact_unique_matched_images",
    "image_id_min",
    "image_id_max",
    "n_gt",
    "n_predictions",
    "n_matched",
    "test_id_set_exact",
    "checkpoint_path",
    "checkpoint_sha256",
    "config_path",
    "config_sha256",
    "partial_bytes",
    "dev_shm_dependency",
    "can_recompute",
    "supersedes",
    "superseded_by",
    "notes",
]

DOTA_FIELDS = [
    "cell",
    "dataset",
    "detector",
    "status",
    "integrity_pass",
    "schema_version",
    "artifact_path",
    "artifact_bytes",
    "artifact_sha256",
    "row_count",
    "unique_matched_images",
    "eval_image_count",
    "gt_count",
    "source_dataset_path",
    "annotation_file_count",
    "nonempty_annotation_file_count",
    "annotation_object_count",
    "metrics_path",
    "metrics_sha256",
    "generation_script",
    "generation_script_sha256",
    "generation_log",
    "generation_log_sha256",
    "checkpoint_path",
    "checkpoint_sha256",
    "config_path",
    "config_sha256",
    "ap50",
    "split",
    "dota20_excluded",
    "dev_shm_dependency",
    "can_recompute",
    "notes",
]


def _rel(path: Path) -> str:
    path = path.resolve()
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def _atomic_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp.{os.getpid()}")
    try:
        with temporary.open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + f".tmp.{os.getpid()}")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def _load_split(name: str) -> set[int]:
    path = DIOR_SPLIT_DIR / f"{name}.txt"
    values = {int(line.strip()) for line in path.open(encoding="utf-8") if line.strip()}
    if len(values) != sum(1 for line in path.open(encoding="utf-8") if line.strip()):
        raise RuntimeError(f"duplicate IDs in frozen DIOR {name} split: {path}")
    return values


def _parse_jsonl(
    path: Path,
    validate: Callable[[dict[str, Any], int, list[str]], None],
) -> dict[str, Any]:
    digest = hashlib.sha256()
    image_ids: set[str] = set()
    issues: list[str] = []
    row_count = 0
    saw_dev_shm = False
    with path.open("rb") as stream:
        for line_number, raw in enumerate(stream, 1):
            digest.update(raw)
            if not raw.strip():
                issues.append(f"blank_line:{line_number}")
                continue
            row_count += 1
            if b"/dev/shm" in raw:
                saw_dev_shm = True
            try:
                row = json.loads(raw)
            except Exception as exc:
                issues.append(f"invalid_json:{line_number}:{type(exc).__name__}")
                if len(issues) >= 20:
                    break
                continue
            image_ids.add(str(row.get("image_id", "")))
            validate(row, line_number, issues)
            if len(issues) >= 20:
                break
    return {
        "sha256": digest.hexdigest(),
        "rows": row_count,
        "image_ids": image_ids,
        "issues": issues,
        "saw_dev_shm": saw_dev_shm,
    }


def _old_index_rows() -> dict[str, dict[str, str]]:
    with DIOR_052_INDEX.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    return {row["cell_id"]: row for row in rows if row["dataset"] == "DIOR-R"}


def _audit_old_dior(trainval_ids: set[int], test_ids: set[int]) -> tuple[list[dict[str, Any]], bool]:
    index = _old_index_rows()
    output: list[dict[str, Any]] = []
    all_integrity = True
    for cell, spec in DIOR_SPECS.items():
        cell_id = spec["cell_id"]
        meta = index.get(cell_id)
        issues: list[str] = []
        if meta is None:
            raise RuntimeError(f"052 lineage index lacks {cell_id}: {DIOR_052_INDEX}")
        artifact = ROOT / meta["matched_table_path"]

        def validate(row: dict[str, Any], line_number: int, errors: list[str]) -> None:
            if row.get("cell_id") != cell_id:
                errors.append(f"cell_id:{line_number}")
            if row.get("dataset") != "DIOR-R":
                errors.append(f"dataset:{line_number}")
            try:
                image_id = int(str(row["image_id"]))
            except Exception:
                errors.append(f"nonnumeric_image_id:{line_number}")
                return
            if image_id not in trainval_ids:
                errors.append(f"not_trainval_id:{line_number}:{image_id}")
            if image_id in test_ids:
                errors.append(f"test_overlap:{line_number}:{image_id}")

        stats = _parse_jsonl(artifact, validate)
        issues.extend(stats["issues"])
        observed_ids = {int(value) for value in stats["image_ids"] if value.isdigit()}
        actual_sha = stats["sha256"]
        if actual_sha != meta["matched_table_sha256"]:
            issues.append("matched_sha256_drift")
        if stats["rows"] != int(meta["n_matched"]):
            issues.append("n_matched_drift")
        if int(meta["n_gt"]) != 35436:
            issues.append("unexpected_052_gt_count")
        if not str(meta["gt_path"]).startswith("/dev/shm/"):
            issues.append("052_gt_path_not_recorded_as_dev_shm")
        integrity = not issues
        all_integrity &= integrity
        output.append({
            "record_type": "superseded_052",
            "cell": cell,
            "cell_id": cell_id,
            "detector": spec["detector"],
            "generation": "052",
            "status": (
                "SUPERSEDED_WRONG_SPLIT_PARTIAL_GT"
                if integrity else "SUPERSEDED_ARTIFACT_DRIFT"
            ),
            "integrity_pass": integrity,
            "artifact_path": _rel(artifact),
            "artifact_bytes": artifact.stat().st_size,
            "artifact_sha256": actual_sha,
            "manifest_path": _rel(DIOR_052_INDEX),
            "manifest_sha256": _sha256(DIOR_052_INDEX),
            "universe_path": "",
            "universe_sha256": "",
            "gt_path": meta["gt_path"],
            "gt_sha256": meta["gt_sha256"],
            "source_split": "DIOR trainval wrong/partial image domain",
            "source_id_domain": (
                f"matched IDs {min(observed_ids)}..{max(observed_ids)}; "
                "all in trainval; zero overlap with test"
            ),
            "metadata_image_count": int(meta["n_images"]),
            "artifact_unique_matched_images": len(observed_ids),
            "image_id_min": min(observed_ids),
            "image_id_max": max(observed_ids),
            "n_gt": int(meta["n_gt"]),
            "n_predictions": int(meta["n_predictions"]),
            "n_matched": stats["rows"],
            "test_id_set_exact": False,
            "checkpoint_path": meta["source_checkpoint"],
            "checkpoint_sha256": meta["checkpoint_sha256"],
            "config_path": meta["config_path"],
            "config_sha256": "",
            "partial_bytes": "",
            "dev_shm_dependency": "historical GT path missing; forbidden for formal use",
            "can_recompute": False,
            "supersedes": "",
            "superseded_by": f"069 replacement cell {cell}",
            "notes": (
                "GT metadata n=35436; source image domain covers 5863..11725 "
                "rather than frozen DIOR test 11726..23463; " + "|".join(issues)
            ).rstrip("; |"),
        })
    return output, all_integrity


_GT_CACHE: dict[Path, dict[str, Any]] = {}


def _persistent_gt_stats(path: Path) -> dict[str, Any]:
    cached = _GT_CACHE.get(path)
    if cached is not None:
        return cached
    digest = hashlib.sha256()
    image_ids: set[int] = set()
    rows = 0
    with path.open("rb") as stream:
        for raw in stream:
            digest.update(raw)
            if not raw.strip():
                continue
            row = json.loads(raw)
            rows += 1
            image_ids.add(int(str(row["image_id"])))
    cached = {"sha256": digest.hexdigest(), "rows": rows, "image_ids": image_ids}
    _GT_CACHE[path] = cached
    return cached


def _resolve_manifest_path(value: str) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def _audit_new_dior(test_ids: set[int]) -> tuple[list[dict[str, Any]], bool]:
    output: list[dict[str, Any]] = []
    all_complete = True
    for cell, spec in DIOR_SPECS.items():
        directory = DIOR_069_ROOT / cell
        artifact = directory / "matched_fullval.jsonl"
        universe = directory / "image_universe.csv"
        manifest_path = directory / "manifest.json"
        artifact_partial = directory / "matched_fullval.jsonl.partial"
        universe_partial = directory / "image_universe.csv.partial"
        partial_bytes = sum(
            path.stat().st_size for path in (artifact_partial, universe_partial) if path.is_file()
        )
        base = {
            "record_type": "replacement_069",
            "cell": cell,
            "cell_id": spec["cell_id"],
            "detector": spec["detector"],
            "generation": "069",
            "artifact_path": _rel(artifact),
            "manifest_path": _rel(manifest_path),
            "universe_path": _rel(universe),
            "source_split": "DIOR trainval->test full-validation",
            "source_id_domain": f"frozen test IDs {EXPECTED_DIOR_TEST_MIN}..{EXPECTED_DIOR_TEST_MAX}",
            "metadata_image_count": "",
            "artifact_unique_matched_images": "",
            "image_id_min": "",
            "image_id_max": "",
            "n_gt": "",
            "n_predictions": "",
            "n_matched": "",
            "test_id_set_exact": False,
            "partial_bytes": partial_bytes,
            "dev_shm_dependency": False,
            "can_recompute": False,
            "supersedes": f"052 {spec['cell_id']} wrong-split partial-GT lineage",
            "superseded_by": "",
        }
        required = (artifact, universe, manifest_path)
        if not all(path.is_file() and path.stat().st_size > 0 for path in required):
            status = "PARTIAL_RESUMABLE" if partial_bytes else "NOT_STARTED"
            missing = [path.name for path in required if not path.is_file() or path.stat().st_size == 0]
            output.append({
                **base,
                "status": status,
                "integrity_pass": False,
                "artifact_bytes": artifact.stat().st_size if artifact.is_file() else "",
                "artifact_sha256": "",
                "manifest_sha256": "",
                "universe_sha256": "",
                "gt_path": "",
                "gt_sha256": "",
                "checkpoint_path": "",
                "checkpoint_sha256": "",
                "config_path": "",
                "config_sha256": "",
                "notes": "final artifacts absent; sentinel/partial is not completion: " + ",".join(missing),
            })
            all_complete = False
            continue

        issues: list[str] = []
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as exc:
            manifest = {}
            issues.append(f"invalid_manifest:{type(exc).__name__}")
        expected_manifest = {
            "status": "complete",
            "cell": cell,
            "cell_id": spec["cell_id"],
            "dataset": "DIOR-R",
            "detector": spec["detector"],
            "split": "full-validation",
            "n_images": EXPECTED_DIOR_IMAGES,
            "n_gt": EXPECTED_DIOR_GT,
            "tta_enabled": True,
        }
        for key, expected in expected_manifest.items():
            if manifest.get(key) != expected:
                issues.append(f"manifest_{key}={manifest.get(key)!r}")

        required_universe_fields = {
            "cell", "dataset", "image_id", "image_path",
            "d_cal_daudit_split_flag", "n_gt", "n_predictions",
        }
        universe_ids: set[int] = set()
        universe_rows = 0
        universe_gt = 0
        universe_predictions = 0
        with universe.open(newline="", encoding="utf-8") as stream:
            reader = csv.DictReader(stream)
            if not required_universe_fields.issubset(reader.fieldnames or []):
                issues.append("universe_schema_missing_fields")
            for line_number, row in enumerate(reader, 2):
                universe_rows += 1
                try:
                    image_id = int(row["image_id"])
                    universe_gt += int(row["n_gt"])
                    universe_predictions += int(row["n_predictions"])
                except Exception:
                    issues.append(f"universe_parse:{line_number}")
                    continue
                universe_ids.add(image_id)
                if row.get("cell") != cell or row.get("dataset") != "DIOR-R":
                    issues.append(f"universe_identity:{line_number}")
                if row.get("d_cal_daudit_split_flag") not in {"D_cal", "D_audit"}:
                    issues.append(f"universe_split_flag:{line_number}")
                if "/dev/shm" in row.get("image_path", ""):
                    issues.append(f"universe_dev_shm:{line_number}")
                if len(issues) >= 20:
                    break
        if universe_rows != EXPECTED_DIOR_IMAGES:
            issues.append(f"universe_rows={universe_rows}")
        if universe_ids != test_ids:
            issues.append("universe_test_id_set_mismatch")
        if universe_gt != EXPECTED_DIOR_GT:
            issues.append(f"universe_gt={universe_gt}")

        required_matched_fields = {
            "cell_id", "cell", "dataset", "detector", "image_id", "pred_id", "gt_id",
            "score", "pred_obb", "gt_obb", "match_iou", "angle_error", "aspect_ratio",
            "near_square", "split", "d_cal_daudit_split_flag", "source_checkpoint",
            "checkpoint_sha256", "config_path", "is_real_detector_output", "lineage",
        }

        def validate(row: dict[str, Any], line_number: int, errors: list[str]) -> None:
            if not required_matched_fields.issubset(row):
                errors.append(f"matched_schema:{line_number}")
                return
            if (
                row.get("cell") != cell
                or row.get("cell_id") != spec["cell_id"]
                or row.get("dataset") != "DIOR-R"
                or row.get("detector") != spec["detector"]
            ):
                errors.append(f"matched_identity:{line_number}")
            try:
                image_id = int(str(row["image_id"]))
            except Exception:
                errors.append(f"matched_image_id:{line_number}")
                return
            if image_id not in test_ids:
                errors.append(f"matched_not_test:{line_number}:{image_id}")
            if row.get("split") != "fullval" or row.get("lineage") != "m069_fullval_reliability":
                errors.append(f"matched_lineage:{line_number}")
            if row.get("is_real_detector_output") is not True:
                errors.append(f"matched_not_real:{line_number}")

        stats = _parse_jsonl(artifact, validate)
        issues.extend(stats["issues"])
        if stats["saw_dev_shm"]:
            issues.append("matched_dev_shm_dependency")
        if stats["rows"] == 0:
            issues.append("matched_empty")
        if stats["rows"] != manifest.get("n_matched"):
            issues.append(f"matched_rows={stats['rows']}")
        if stats["sha256"] != manifest.get("matched_sha256"):
            issues.append("matched_sha256_manifest_mismatch")
        if artifact.stat().st_size != manifest.get("matched_bytes"):
            issues.append("matched_bytes_manifest_mismatch")

        universe_sha = _sha256(universe)
        if universe_sha != manifest.get("universe_sha256"):
            issues.append("universe_sha256_manifest_mismatch")
        if universe.stat().st_size != manifest.get("universe_bytes"):
            issues.append("universe_bytes_manifest_mismatch")

        gt_path = _resolve_manifest_path(str(manifest.get("gt_path", "")))
        checkpoint = Path(str(manifest.get("checkpoint_path", "")))
        config = Path(str(manifest.get("config_path", "")))
        gt_sha = checkpoint_sha = config_sha = ""
        if not gt_path.is_file() or str(gt_path).startswith("/dev/shm/"):
            issues.append("persistent_gt_missing_or_dev_shm")
        else:
            gt_stats = _persistent_gt_stats(gt_path)
            gt_sha = gt_stats["sha256"]
            if gt_sha != manifest.get("gt_sha256"):
                issues.append("gt_sha256_manifest_mismatch")
            if gt_stats["rows"] != EXPECTED_DIOR_GT or gt_stats["image_ids"] != test_ids:
                issues.append("gt_not_exact_test_fullval")
        if not checkpoint.is_file():
            issues.append("checkpoint_missing")
        else:
            checkpoint_sha = _sha256(checkpoint)
            if checkpoint_sha != manifest.get("checkpoint_sha256"):
                issues.append("checkpoint_sha256_manifest_mismatch")
        if not config.is_file():
            issues.append("config_missing")
        else:
            config_sha = _sha256(config)
            if config_sha != manifest.get("config_sha256"):
                issues.append("config_sha256_manifest_mismatch")
        if artifact_partial.exists() or universe_partial.exists():
            issues.append("stale_partial_after_complete_manifest")

        integrity = not issues
        all_complete &= integrity
        numeric_ids = {int(value) for value in stats["image_ids"] if value.isdigit()}
        output.append({
            **base,
            "status": "AUTHORITATIVE_FULLVAL" if integrity else "FAILED_VALIDATION",
            "integrity_pass": integrity,
            "artifact_bytes": artifact.stat().st_size,
            "artifact_sha256": stats["sha256"],
            "manifest_sha256": _sha256(manifest_path),
            "universe_sha256": universe_sha,
            "gt_path": _rel(gt_path),
            "gt_sha256": gt_sha,
            "metadata_image_count": manifest.get("n_images", ""),
            "artifact_unique_matched_images": len(numeric_ids),
            "image_id_min": min(numeric_ids) if numeric_ids else "",
            "image_id_max": max(numeric_ids) if numeric_ids else "",
            "n_gt": manifest.get("n_gt", ""),
            "n_predictions": manifest.get("n_predictions", ""),
            "n_matched": stats["rows"],
            "test_id_set_exact": universe_ids == test_ids,
            "checkpoint_path": str(checkpoint),
            "checkpoint_sha256": checkpoint_sha,
            "config_path": str(config),
            "config_sha256": config_sha,
            "dev_shm_dependency": stats["saw_dev_shm"],
            "can_recompute": bool(manifest.get("can_recompute")) and integrity,
            "notes": "verified manifest/file/schema/test-universe/GT/checkpoint/config" if integrity else "|".join(issues),
        })
    return output, all_complete


def _dota_dataset_counts() -> tuple[int, int, int]:
    annotation_files = sorted((DOTA_DATA_ROOT / "annfiles").glob("*.txt"))
    nonempty = 0
    objects = 0
    for path in annotation_files:
        file_objects = sum(1 for line in path.open(encoding="utf-8") if line.strip())
        nonempty += int(file_objects > 0)
        objects += file_objects
    return len(annotation_files), nonempty, objects


def _audit_dota() -> tuple[list[dict[str, Any]], bool]:
    annotation_files, nonempty_files, object_count = _dota_dataset_counts()
    shared_issues: list[str] = []
    if annotation_files != EXPECTED_DOTA_IMAGES:
        shared_issues.append(f"annotation_files={annotation_files}")
    if object_count != EXPECTED_DOTA_GT:
        shared_issues.append(f"annotation_objects={object_count}")
    log_text = DOTA_LOG.read_text(encoding="utf-8") if DOTA_LOG.is_file() else ""
    generator_sha = _sha256(DOTA_GENERATOR) if DOTA_GENERATOR.is_file() else ""
    log_sha = _sha256(DOTA_LOG) if DOTA_LOG.is_file() else ""
    rows: list[dict[str, Any]] = []
    all_valid = not shared_issues
    for cell, spec in DOTA_SPECS.items():
        artifact = spec["artifact"]
        metrics_path = spec["metrics"]
        issues = list(shared_issues)
        if not artifact.is_file() or artifact.stat().st_size == 0:
            issues.append("artifact_missing_or_empty")
        if not metrics_path.is_file():
            issues.append("metrics_missing")
        try:
            metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
        except Exception as exc:
            metrics = {}
            issues.append(f"metrics_invalid:{type(exc).__name__}")

        required_fields = {
            "cell_id", "dataset", "detector", "image_id", "pred_id", "gt_id", "score",
            "pred_obb", "gt_obb", "match_iou", "angle_error", "aspect_ratio", "near_square",
            "size_bin", "split", "d_cal_daudit_split_flag", "is_real_detector_output",
        }

        def validate(row: dict[str, Any], line_number: int, errors: list[str]) -> None:
            if not required_fields.issubset(row):
                errors.append(f"schema:{line_number}")
                return
            if (
                row.get("cell_id") != cell
                or row.get("dataset") != "DOTA-v1.0"
                or row.get("detector") != spec["detector"]
            ):
                errors.append(f"identity:{line_number}")
            if row.get("split") != "fullval" or row.get("d_cal_daudit_split_flag") != "D_audit":
                errors.append(f"split:{line_number}")
            if row.get("is_real_detector_output") is not True:
                errors.append(f"not_real:{line_number}")
            try:
                values = [float(row[key]) for key in ("score", "match_iou", "angle_error", "aspect_ratio")]
                if not all(math.isfinite(value) for value in values) or values[1] < 0.5:
                    errors.append(f"numeric_contract:{line_number}")
            except Exception:
                errors.append(f"numeric_parse:{line_number}")

        stats = (
            _parse_jsonl(artifact, validate)
            if artifact.is_file() and artifact.stat().st_size > 0
            else {"sha256": "", "rows": 0, "image_ids": set(), "issues": [], "saw_dev_shm": False}
        )
        issues.extend(stats["issues"])
        if stats["saw_dev_shm"]:
            issues.append("artifact_dev_shm_dependency")
        expected_metrics = {
            "cell": cell,
            "detector": spec["detector"],
            "n_gt_fullval": EXPECTED_DOTA_GT,
            "n_matched": spec["expected_rows"],
            "AP50": spec["expected_ap50"],
        }
        for key, expected in expected_metrics.items():
            if metrics.get(key) != expected:
                issues.append(f"metrics_{key}={metrics.get(key)!r}")
        if stats["rows"] != spec["expected_rows"]:
            issues.append(f"rows={stats['rows']}")
        if metrics.get("gt_source") != str(DOTA_DATA_ROOT):
            issues.append("metrics_gt_source_mismatch")
        if metrics.get("can_recompute") != "yes":
            issues.append("metrics_can_recompute_not_yes")
        if f"{spec['log_key']}: n_eval={EXPECTED_DOTA_IMAGES}" not in log_text:
            issues.append("generation_log_missing_n_eval")
        if f"{spec['log_key']}: DONE rows={spec['expected_rows']}" not in log_text:
            issues.append("generation_log_missing_done")

        checkpoint = spec["checkpoint"]
        config = spec["config"]
        if not checkpoint.is_file():
            issues.append("checkpoint_missing")
        if not config.is_file():
            issues.append("config_missing")
        if not generator_sha:
            issues.append("generation_script_missing")
        if not log_sha:
            issues.append("generation_log_missing")
        if "DOTA-v1.0/20" in stats["image_ids"] or cell == "DOTA-v1.0/20":
            issues.append("dota20_included")

        integrity = not issues
        all_valid &= integrity
        rows.append({
            "cell": cell,
            "dataset": "DOTA-v1.0",
            "detector": spec["detector"],
            "status": "AUTHORITATIVE_CLEAN_FULLVAL" if integrity else "FAILED_VALIDATION",
            "integrity_pass": integrity,
            "schema_version": "m_dota_clean_perinstance_v1",
            "artifact_path": _rel(artifact),
            "artifact_bytes": artifact.stat().st_size if artifact.is_file() else "",
            "artifact_sha256": stats["sha256"],
            "row_count": stats["rows"],
            "unique_matched_images": len(stats["image_ids"]),
            "eval_image_count": EXPECTED_DOTA_IMAGES,
            "gt_count": EXPECTED_DOTA_GT,
            "source_dataset_path": str(DOTA_DATA_ROOT),
            "annotation_file_count": annotation_files,
            "nonempty_annotation_file_count": nonempty_files,
            "annotation_object_count": object_count,
            "metrics_path": _rel(metrics_path),
            "metrics_sha256": _sha256(metrics_path) if metrics_path.is_file() else "",
            "generation_script": _rel(DOTA_GENERATOR),
            "generation_script_sha256": generator_sha,
            "generation_log": _rel(DOTA_LOG),
            "generation_log_sha256": log_sha,
            "checkpoint_path": str(checkpoint),
            "checkpoint_sha256": _sha256(checkpoint) if checkpoint.is_file() else "",
            "config_path": str(config),
            "config_sha256": _sha256(config) if config.is_file() else "",
            "ap50": metrics.get("AP50", ""),
            "split": "dota1.0/split_ss_dota10/val full-validation",
            "dota20_excluded": integrity,
            "dev_shm_dependency": stats["saw_dev_shm"],
            "can_recompute": integrity,
            "notes": (
                "5297-tile/55804-GT persistent val; matched-only artifact bound to "
                "K4b metrics, frozen checkpoint/config, generator and normal-end log; DOTA#20 excluded"
                if integrity else "|".join(issues)
            ),
        })
    return rows, all_valid


def _render_doc(
    old_rows: list[dict[str, Any]],
    new_rows: list[dict[str, Any]],
    dota_rows: list[dict[str, Any]],
    ready: bool,
) -> str:
    decision = (
        "RESOLVED：A-C 均已由冻结 checkpoint 的 DIOR test full-validation 持久化产物替代，"
        "旧 052 reliability lineage 不再进入正式结果。"
        if ready
        else "NOT_RESOLVED：A-C 的正确 DIOR test full-validation 产物尚未全部完成并通过校验；"
        "本脚本保持 fail-closed，旧 052 数字不得进入正式结果。"
    )
    lines = [
        "# 069 DIOR partial-GT lineage 清债",
        "",
        f"**当前裁决：{decision}**",
        "",
        "## 已 supersede 的 052 lineage",
        "",
        "| cell | 052 状态 | matched rows | matched images | observed IDs | n_gt | sha256 |",
        "|---|---|---:|---:|---|---:|---|",
    ]
    for row in old_rows:
        lines.append(
            f"| {row['cell']} / {row['cell_id']} | {row['status']} | {row['n_matched']} | "
            f"{row['artifact_unique_matched_images']} | {row['image_id_min']}..{row['image_id_max']} | "
            f"{row['n_gt']} | `{row['artifact_sha256']}` |"
        )
    lines += [
        "",
        "052 的 GT metadata 只有 35,436 个实例，记录的源域为 DIOR trainval 子域；"
        "matched IDs 全在 5,863..11,725，和冻结 test IDs 11,726..23,463 零重叠。"
        "其 GT 路径位于已丢失的 `/dev/shm`，因此只保留 provenance，不具备正式复算资格。",
        "",
        "## 069 replacement A-C",
        "",
        "| cell | 状态 | final matched | manifest | images | n_gt | test ID set exact |",
        "|---|---|---|---|---:|---:|---|",
    ]
    for row in new_rows:
        lines.append(
            f"| {row['cell']} / {row['cell_id']} | {row['status']} | "
            f"`{row['artifact_path']}` | `{row['manifest_path']}` | "
            f"{row['metadata_image_count']} | {row['n_gt']} | {row['test_id_set_exact']} |"
        )
    lines += [
        "",
        "转正条件同时要求：manifest `status=complete`；11,738 图 universe 与冻结 test ID 集完全一致；"
        "GT 总数 124,445；matched/universe/GT/checkpoint/config 的 sha256 与 manifest 一致；"
        "TTA 为正式启用状态；无 `/dev/shm` 依赖；无完成后的残留 `.partial`。",
        "",
        "## DOTA clean full-val artifact",
        "",
        "| cell | 状态 | rows | matched images | eval images | n_gt | sha256 | DOTA#20 |",
        "|---|---|---:|---:|---:|---:|---|---|",
    ]
    for row in dota_rows:
        lines.append(
            f"| {row['cell']} | {row['status']} | {row['row_count']} | "
            f"{row['unique_matched_images']} | {row['eval_image_count']} | {row['gt_count']} | "
            f"`{row['artifact_sha256']}` | excluded |"
        )
    lines += [
        "",
        "DOTA 两个 JSONL 是 matched-instance artifact；其 full-val 身份由 5,297-tile/55,804-GT "
        "持久化 val 数据、K4b metrics、冻结 checkpoint/config、生成脚本及正常结束日志联合绑定。"
        "权威 metadata 见 `reports/069_dota_clean_artifact_manifest.csv`。DOTA#20 不在产物中。",
        "",
        "## 复核入口",
        "",
        "```bash",
        "python scripts/m069_lineage_audit.py",
        "```",
        "",
        "该命令不导入 detector/GPU 依赖，只读核验并原子更新本页和两份 CSV。"
        "在 A-C 全部转正前返回非零，sentinel 或 `.partial` 不构成完成证据。",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    trainval_ids = _load_split("trainval")
    test_ids = _load_split("test")
    if len(trainval_ids) != 11725 or len(test_ids) != EXPECTED_DIOR_IMAGES:
        raise RuntimeError("frozen DIOR split counts changed")
    if trainval_ids & test_ids:
        raise RuntimeError("frozen DIOR trainval/test sets overlap")
    if min(test_ids) != EXPECTED_DIOR_TEST_MIN or max(test_ids) != EXPECTED_DIOR_TEST_MAX:
        raise RuntimeError("frozen DIOR test ID bounds changed")

    old_rows, old_integrity = _audit_old_dior(trainval_ids, test_ids)
    new_rows, dior_complete = _audit_new_dior(test_ids)
    dota_rows, dota_valid = _audit_dota()
    ready = old_integrity and dior_complete and dota_valid

    _atomic_csv(DIOR_AUDIT_CSV, old_rows + new_rows, DIOR_FIELDS)
    _atomic_csv(DOTA_MANIFEST_CSV, dota_rows, DOTA_FIELDS)
    _atomic_text(RESOLUTION_DOC, _render_doc(old_rows, new_rows, dota_rows, ready))

    if not ready:
        pending = [row["cell"] for row in new_rows if row["status"] != "AUTHORITATIVE_FULLVAL"]
        failures = [row["cell"] for row in dota_rows if row["status"] != "AUTHORITATIVE_CLEAN_FULLVAL"]
        print(
            "069_LINEAGE_NOT_RESOLVED "
            f"dior_pending={','.join(pending) or 'none'} "
            f"dota_failures={','.join(failures) or 'none'} "
            f"old_integrity={old_integrity}",
            file=sys.stderr,
        )
        return 2
    print("069_LINEAGE_RESOLVED dior=A,B,C dota=orcnn,rtmdet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
