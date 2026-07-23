#!/usr/bin/env python3
"""Aggregate the preregistered PSC Phase-1 forward artifacts.

This script never trains or runs a detector. It validates the six frozen K2 PSC
forward manifests, performs only the analyses registered on 2026-07-12, and then
applies the frozen four-condition split gate. Missing forward artifacts cause an
early nonzero exit without overwriting the historical 069 result names.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
from scipy.stats import kendalltau, spearmanr

ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
REPO = ROOT / "top_journal_v3_reaudit_055"
REPORTS = REPO / "reports"
DOCS = ROOT / "docs"
LOG = REPO / "logs/m069/psc_phase1.log"
FORWARD_ROOT = ROOT / "outputs/persistent_artifacts/m069_psc_phase1"
NATIVE_ROOT = FORWARD_ROOT / "native_signals"
K2_EVAL = REPORTS / "k2_eval"
K2_ARTIFACT_MANIFEST = REPORTS / "k2_artifact_manifest_067.csv"
DELTA_THETA_JSON = REPORTS / "m4_delta_theta_075_frozen.json"

sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from derive_delta_theta_075 import load_interpolator  # noqa: E402
from orientbench.metrics.nrc_auc import nrc_auc  # noqa: E402
from orientbench.metrics.risk_coverage import aurc, risk_at_coverage  # noqa: E402


START = "2026-07-12 20:14:39 -0700"
DEADLINE = "2026-08-23 20:14:39 -0700"
PREREG = DOCS / "psc_phase1_preregistration.md"
PREREG_SHA256 = "c1f88a6a975d158e42e6c26ddd936a12d269ecbd05ac7999dc11980c45292f7f"
K_GRID = [0.25, 0.50, 0.75, 0.90, 1.00, 1.10, 1.25, 1.50, 2.00, 4.00]
ACTUAL_SUPPLEMENT_SCHEMA = "psc_phase1_actual_head_loss_network_space_v1"
ACTUAL_SUPPLEMENT_CSV = "actual_head_loss_network_space.csv"
ACTUAL_SUPPLEMENT_MANIFEST = "actual_head_loss_network_space_manifest.json"
NATIVE_ENDPOINT_SCHEMA = "psc_phase1_frozen_k2_native_endpoint_v1"
DATASETS = ("DIOR-R", "SODA-A")
SEEDS = (0, 1, 2)
AR_MAIN = 2.1
BOOTSTRAP_REPLICATES = 800
EXPECTED_IMAGES = {"DIOR-R": 11738, "SODA-A": 22994}
EXPECTED_GT = {"DIOR-R": 124445, "SODA-A": 449644}
EXPECTED_GT_PATHS = {
    "DIOR-R": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl",
    "SODA-A": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl",
}
CPU_BUDGET = 48
MIN_CPU_WORKERS = math.ceil(CPU_BUDGET * 0.80)

OUTPUTS = {
    "radial": REPORTS / "psc_phase1_radial_scaling.csv",
    "branch": REPORTS / "psc_phase1_branch_decision.csv",
    "dissection": REPORTS / "psc_phase1_dissection.csv",
    "scores": REPORTS / "psc_phase1_score_comparison.csv",
    "nontriviality": REPORTS / "psc_phase1_nontriviality_audit.csv",
    "gate": REPORTS / "psc_phase1_split_gate_decision.csv",
    "manifest": REPORTS / "psc_phase1_artifact_manifest.csv",
    "radial_doc": DOCS / "psc_phase1_radial_scaling_intervention.md",
    "gate_doc": DOCS / "psc_phase1_split_gate_report.md",
}

SCORE_FORMULAS = {
    "phase_mod": "phase_mod_primary",
    "negative_phase_mod": "-phase_mod_primary",
    "detection_score": "post-NMS detection score",
    "tta_phase_direction_consistency": "-theta->2theta circular variance over identity/hflip/vflip phase direction",
    "multi_frequency_consistency": "-multi_frequency_disagreement_deg",
    "unwrap_candidate_energy_gap": "abs(cos alignment candidate0 - candidate1)",
    "phase_direction_margin": "unwrap_candidate_energy_gap * secondary phase-vector norm",
}

MECHANISM_CANDIDATES = (
    "tta_phase_direction_consistency",
    "multi_frequency_consistency",
    "unwrap_candidate_energy_gap",
    "phase_direction_margin",
)

RADIAL_REQUIRED = {
    "dataset", "seed", "k", "n_images", "n_predictions", "n_matched", "AP50", "AP75",
    "mean_angle_error_deg", "median_angle_error_deg", "p95_angle_error_deg",
    "mean_phase_mod_primary", "mean_phase_mod_secondary", "mean_matched_phase_loss",
    "mean_abs_radial_gradient", "mean_tangential_gradient_norm", "mean_abs_dloss_dk",
    "controlled_base_mean_phase_mod_primary", "controlled_base_mean_phase_mod_secondary",
    "controlled_base_mean_phase_loss", "controlled_base_mean_abs_radial_gradient",
    "controlled_base_mean_tangential_gradient_norm", "controlled_base_mean_abs_dloss_dk",
    "actual_head_mean_angle_loss", "actual_head_mean_abs_radial_gradient",
    "actual_head_mean_tangential_gradient_norm", "actual_head_mean_abs_dloss_dk",
    "actual_head_mean_positive_anchors",
    "decoded_angle_median_diff_deg", "decoded_angle_p95_diff_deg",
    "post_nms_exact_image_proportion", "post_nms_score_label_count_equal_proportion",
}

ACTUAL_HEAD_FIELDS = {
    "actual_head_mean_angle_loss", "actual_head_mean_abs_radial_gradient",
    "actual_head_mean_tangential_gradient_norm",
    "actual_head_mean_abs_radial_gradient_wrt_base_z",
    "actual_head_mean_tangential_gradient_norm_wrt_base_z",
    "actual_head_mean_abs_dloss_dk", "actual_head_mean_positive_anchors",
}

MATCHED_REQUIRED = {
    "dataset", "seed", "image_id", "pred_id", "class", "score", "angle_error", "aspect_ratio",
    "size", "decoded_angle", "objectness", "boundary_distance_deg", "wrapping_condition",
    "phase_mod_primary", "phase_mod_secondary", "phase_angle_primary", "phase_angle_secondary",
    "multi_frequency_disagreement_deg", "unwrap_candidate_energy_gap", "phase_direction_margin",
    "angle_vector_norm", "reg_feature_norm", "tta_phase_direction_circular_variance", "n_tta_phase_angles",
}


class PendingInputs(RuntimeError):
    pass


class InvalidInput(RuntimeError):
    pass


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def stable_seed(*parts) -> int:
    text = "|".join(map(str, parts))
    return int(hashlib.sha256(text.encode("utf-8")).hexdigest()[:8], 16)


def finite_float(value, label):
    try:
        output = float(value)
    except (TypeError, ValueError) as exc:
        raise InvalidInput(f"{label} is not numeric: {value!r}") from exc
    if not math.isfinite(output):
        raise InvalidInput(f"{label} is nonfinite")
    return output


def atomic_csv(path: Path, rows, fieldnames=None):
    if not rows and not fieldnames:
        raise ValueError(f"cannot infer schema for empty CSV {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    fields = fieldnames or list(rows[0])
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def atomic_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    os.replace(temporary, path)


def log(message):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(f"[{time.strftime('%F %T')}] {message}\n")


def expected_paths(dataset, seed):
    cfg_name = "psc_dior_seed0.py" if dataset == "DIOR-R" else "psc_soda_seed0.py"
    work = REPO / f"work_dirs/k2/K2_final__PSC__{dataset}__seed{seed}"
    return work / cfg_name, work / "epoch_12.pth", FORWARD_ROOT / dataset / f"seed{seed}"


def resolve_project_artifact(path_text):
    path = Path(path_text)
    if not path.is_absolute():
        path = ROOT / path
    resolved = path.resolve()
    try:
        resolved.relative_to(ROOT.resolve())
    except ValueError as exc:
        raise InvalidInput(f"artifact escapes project root: {path_text}") from exc
    return resolved


def validate_preregistration():
    start = datetime.strptime(START, "%Y-%m-%d %H:%M:%S %z")
    deadline = datetime.strptime(DEADLINE, "%Y-%m-%d %H:%M:%S %z")
    if deadline != start + timedelta(days=42):
        raise InvalidInput("Phase-1 deadline is not exactly start+42 days")
    if not PREREG.is_file() or sha256(PREREG) != PREREG_SHA256:
        raise InvalidInput("frozen PSC Phase-1 preregistration hash changed")


def validate_risk_event():
    if not DELTA_THETA_JSON.is_file() or not DELTA_THETA_JSON.stat().st_size:
        raise PendingInputs(f"missing frozen geometry-risk threshold: {DELTA_THETA_JSON}")
    payload = json.loads(DELTA_THETA_JSON.read_text(encoding="utf-8"))
    expected = {
        "schema_version": "m4_delta_theta_075_v2",
        "frozen_at": START,
        "definition_changed": False,
        "tau_main": 0.75,
        "angle_convention": "le90_pi_periodic_long_axis",
        "geometry_model": "concentric_same_scale_congruent_rectangles",
        "stability_all_pass": True,
    }
    for key, value in expected.items():
        if payload.get(key) != value:
            raise InvalidInput(f"{DELTA_THETA_JSON}: frozen risk-event field {key} changed")
    if finite_float(payload.get("solve_tolerance_deg"), "solve_tolerance_deg") > 1e-3:
        raise InvalidInput(f"{DELTA_THETA_JSON}: solve tolerance exceeds 1e-3 degree")


def validate_summary(path, dataset, seed, n_images):
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        rows = list(reader)
    missing = RADIAL_REQUIRED.difference(fields)
    if missing:
        raise InvalidInput(f"{path}: missing radial fields {sorted(missing)}")
    if len(rows) != len(K_GRID):
        raise InvalidInput(f"{path}: expected {len(K_GRID)} k rows, got {len(rows)}")
    seen_k = []
    for index, row in enumerate(rows):
        if row["dataset"] != dataset or int(row["seed"]) != seed:
            raise InvalidInput(f"{path}: dataset/seed mismatch at row {index + 2}")
        if int(row["n_images"]) != n_images:
            raise InvalidInput(f"{path}: n_images mismatch")
        k = finite_float(row["k"], f"{path}:k")
        seen_k.append(k)
        for field in RADIAL_REQUIRED.difference({"dataset"}):
            finite_float(row[field], f"{path}:{field}")
        if int(row["n_predictions"]) <= 0 or int(row["n_matched"]) <= 0:
            raise InvalidInput(f"{path}: empty evaluator row at k={k}")
        if not all(0.0 <= float(row[field]) <= 1.0 for field in (
                "AP50", "AP75", "post_nms_exact_image_proportion",
                "post_nms_score_label_count_equal_proportion")):
            raise InvalidInput(f"{path}: probability/AP outside [0,1] at k={k}")
        if not all(0.0 <= float(row[field]) <= 90.0 for field in (
                "mean_angle_error_deg", "median_angle_error_deg", "p95_angle_error_deg",
                "decoded_angle_median_diff_deg", "decoded_angle_p95_diff_deg")):
            raise InvalidInput(f"{path}: angle statistic outside [0,90] at k={k}")
        nonnegative = RADIAL_REQUIRED.intersection({
            "mean_phase_mod_primary", "mean_phase_mod_secondary", "mean_matched_phase_loss",
            "mean_abs_radial_gradient", "mean_tangential_gradient_norm", "mean_abs_dloss_dk",
            "controlled_base_mean_phase_mod_primary", "controlled_base_mean_phase_mod_secondary",
            "controlled_base_mean_phase_loss", "controlled_base_mean_abs_radial_gradient",
            "controlled_base_mean_tangential_gradient_norm", "controlled_base_mean_abs_dloss_dk",
            "actual_head_mean_angle_loss", "actual_head_mean_abs_radial_gradient",
            "actual_head_mean_tangential_gradient_norm", "actual_head_mean_abs_dloss_dk",
            "actual_head_mean_positive_anchors",
        })
        if any(float(row[field]) < 0 for field in nonnegative):
            raise InvalidInput(f"{path}: negative loss/norm statistic at k={k}")
        if float(row["actual_head_mean_positive_anchors"]) <= 0:
            raise InvalidInput(f"{path}: actual head loss has no positive anchors at k={k}")
        if abs(k - 1.0) < 1e-12 and (
                float(row["decoded_angle_p95_diff_deg"]) > 1e-6
                or float(row["post_nms_exact_image_proportion"]) < 1.0
                or float(row["post_nms_score_label_count_equal_proportion"]) < 1.0):
            raise InvalidInput(f"{path}: k=1 identity check failed")
    if not np.allclose(seen_k, K_GRID, rtol=0, atol=1e-12):
        raise InvalidInput(f"{path}: k grid changed")
    return rows


def validate_actual_loss_supplement(
        out_dir, dataset, seed, expected_cfg, expected_checkpoint,
        k2_manifest_sha, expected_k2_eval, expected_gt):
    """Validate and load the network-coordinate actual-head supplement.

    The original radial forward's decode/AP/NMS artifacts remain authoritative,
    but its packed validation GT was in evaluator coordinates during its loss
    assignment.  This targeted supplement is therefore mandatory and replaces
    only the ``actual_head_*`` columns.
    """
    manifest_path = out_dir / ACTUAL_SUPPLEMENT_MANIFEST
    summary_path = out_dir / ACTUAL_SUPPLEMENT_CSV
    if not manifest_path.is_file() or not summary_path.is_file():
        raise PendingInputs(
            f"missing targeted PSC actual-loss supplement for {dataset}/seed{seed}: "
            f"{manifest_path}")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise InvalidInput(f"{manifest_path}: malformed JSON") from exc
    required = {
        "status", "schema_version", "run_id", "dataset", "seed", "k_grid",
        "n_images", "n_gt", "summary_path", "summary_sha256", "summary_bytes",
        "config_path", "config_sha256", "checkpoint_path", "checkpoint_sha256",
        "k2_artifact_manifest_path", "k2_artifact_manifest_sha256", "k2_eval_path",
        "k2_eval_sha256", "gt_path", "gt_sha256", "gt_coordinate_space",
        "only_actual_head_loss_statistics", "no_decode", "no_matching", "no_nms",
        "no_ap_evaluation", "no_training", "generation_command", "completed_at",
    }
    absent = required.difference(manifest)
    if absent:
        raise InvalidInput(f"{manifest_path}: missing fields {sorted(absent)}")
    run_id = f"K2_final__PSC__{dataset}__seed{seed}"
    if (manifest.get("status") != "complete"
            or manifest.get("schema_version") != ACTUAL_SUPPLEMENT_SCHEMA
            or manifest.get("run_id") != run_id
            or manifest.get("dataset") != dataset
            or int(manifest.get("seed", -1)) != seed
            or int(manifest.get("n_images", -1)) != EXPECTED_IMAGES[dataset]
            or int(manifest.get("n_gt", -1)) != EXPECTED_GT[dataset]
            or manifest.get("gt_coordinate_space") != "network_input_after_validation_scale_factor"):
        raise InvalidInput(f"{manifest_path}: identity/cardinality/coordinate-space mismatch")
    if not np.allclose(manifest.get("k_grid", []), K_GRID, rtol=0, atol=1e-12):
        raise InvalidInput(f"{manifest_path}: frozen k grid mismatch")
    if not all(manifest.get(field) is True for field in (
            "only_actual_head_loss_statistics", "no_decode", "no_matching", "no_nms",
            "no_ap_evaluation", "no_training")):
        raise InvalidInput(f"{manifest_path}: targeted/no-training declarations invalid")
    if "/dev/shm" in json.dumps(manifest):
        raise InvalidInput(f"{manifest_path}: /dev/shm dependency")
    expected_command = f"scripts/m069_psc_actual_loss_supplement.py {dataset} {seed}"
    if expected_command not in manifest["generation_command"] or not manifest["completed_at"]:
        raise InvalidInput(f"{manifest_path}: generation/completion record mismatch")

    recorded = {
        "summary": resolve_project_artifact(manifest["summary_path"]),
        "config": resolve_project_artifact(manifest["config_path"]),
        "checkpoint": resolve_project_artifact(manifest["checkpoint_path"]),
        "k2_manifest": resolve_project_artifact(manifest["k2_artifact_manifest_path"]),
        "k2_eval": resolve_project_artifact(manifest["k2_eval_path"]),
        "gt": resolve_project_artifact(manifest["gt_path"]),
    }
    expected_paths_map = {
        "summary": summary_path.resolve(),
        "config": expected_cfg.resolve(),
        "checkpoint": expected_checkpoint.resolve(),
        "k2_manifest": K2_ARTIFACT_MANIFEST.resolve(),
        "k2_eval": expected_k2_eval.resolve(),
        "gt": expected_gt.resolve(),
    }
    if recorded != expected_paths_map:
        raise InvalidInput(f"{manifest_path}: recorded supplement source path drift")
    expected_hashes = {
        "summary_sha256": sha256(summary_path),
        "config_sha256": sha256(expected_cfg),
        "checkpoint_sha256": sha256(expected_checkpoint),
        "k2_artifact_manifest_sha256": k2_manifest_sha,
        "k2_eval_sha256": sha256(expected_k2_eval),
        "gt_sha256": sha256(expected_gt),
    }
    if any(manifest.get(field) != value for field, value in expected_hashes.items()):
        raise InvalidInput(f"{manifest_path}: supplement source/output SHA mismatch")
    if summary_path.stat().st_size != int(manifest.get("summary_bytes", -1)):
        raise InvalidInput(f"{manifest_path}: supplement summary byte count mismatch")
    with summary_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        rows = list(reader)
    required_csv = {"dataset", "seed", "k", "n_images", "n_gt"}.union(ACTUAL_HEAD_FIELDS)
    if required_csv.difference(fields) or len(rows) != len(K_GRID):
        raise InvalidInput(f"{summary_path}: supplement schema/row count mismatch")
    if not np.allclose([finite_float(row["k"], f"{summary_path}:k") for row in rows],
                       K_GRID, rtol=0, atol=1e-12):
        raise InvalidInput(f"{summary_path}: supplement k grid mismatch")
    for row in rows:
        if (row["dataset"] != dataset or int(row["seed"]) != seed
                or int(row["n_images"]) != EXPECTED_IMAGES[dataset]
                or int(row["n_gt"]) != int(manifest["n_gt"])):
            raise InvalidInput(f"{summary_path}: supplement row identity mismatch")
        for field in ACTUAL_HEAD_FIELDS:
            if finite_float(row[field], f"{summary_path}:{field}") < 0:
                raise InvalidInput(f"{summary_path}: negative {field}")
        if float(row["actual_head_mean_positive_anchors"]) <= 0:
            raise InvalidInput(f"{summary_path}: no positive anchors")
    supplement_log = REPO / f"logs/m069/psc_phase1_actual_loss/{dataset}_seed{seed}.log"
    if (not supplement_log.is_file()
            or f"{dataset} seed={seed} DONE images={EXPECTED_IMAGES[dataset]}" not in supplement_log.read_text(errors="ignore")):
        raise InvalidInput(f"{supplement_log}: missing normal DONE record")
    if any(out_dir.glob(f"{ACTUAL_SUPPLEMENT_CSV}.tmp")) or any(
            out_dir.glob(f"{ACTUAL_SUPPLEMENT_MANIFEST}.tmp")):
        raise InvalidInput(f"{out_dir}: incomplete supplement temporary artifact")
    return {
        "manifest_path": manifest_path,
        "summary_path": summary_path,
        "log_path": supplement_log,
        "rows": rows,
    }


def validate_forward_inputs():
    if not K2_ARTIFACT_MANIFEST.is_file():
        raise PendingInputs(f"missing frozen K2 artifact manifest: {K2_ARTIFACT_MANIFEST}")
    k2_manifest_sha = sha256(K2_ARTIFACT_MANIFEST)
    with K2_ARTIFACT_MANIFEST.open(newline="", encoding="utf-8") as handle:
        k2_rows = {row["run_id"]: row for row in csv.DictReader(handle)}
    missing = []
    sources = []
    for dataset in DATASETS:
        for seed in SEEDS:
            expected_cfg, expected_checkpoint, out_dir = expected_paths(dataset, seed)
            manifest_path = out_dir / "manifest.json"
            for path in (expected_cfg, expected_checkpoint, manifest_path):
                if not path.is_file():
                    missing.append(str(path))
            if any(not path.is_file() for path in (expected_cfg, expected_checkpoint, manifest_path)):
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            required_manifest = {
                "status", "schema_version", "run_id", "dataset", "seed", "k_grid", "n_images",
                "config_path", "config_sha256", "checkpoint_path", "checkpoint_sha256",
                "k2_artifact_manifest_path", "k2_artifact_manifest_sha256", "k2_eval_path",
                "k2_eval_sha256", "summary_path", "summary_sha256", "summary_bytes",
                "matched_path", "matched_sha256", "matched_bytes", "matched_rows",
                "tta_phase_direction", "no_training", "generation_command", "completed_at",
            }
            absent = required_manifest.difference(manifest)
            if absent:
                raise InvalidInput(f"{manifest_path}: missing manifest fields {sorted(absent)}")
            if manifest.get("status") != "complete" or manifest.get("no_training") is not True:
                raise InvalidInput(f"{manifest_path}: status/no_training invalid")
            if manifest.get("schema_version") != "psc_phase1_radial_scaling_v2":
                raise InvalidInput(f"{manifest_path}: unsupported forward schema")
            if manifest.get("dataset") != dataset or int(manifest.get("seed", -1)) != seed:
                raise InvalidInput(f"{manifest_path}: dataset/seed mismatch")
            if manifest.get("tta_phase_direction") != (seed == 0):
                raise InvalidInput(f"{manifest_path}: seed-specific TTA declaration mismatch")
            expected_command = f"scripts/m069_psc_phase1_forward.py {dataset} {seed}"
            if expected_command not in manifest.get("generation_command", "") or not manifest.get("completed_at"):
                raise InvalidInput(f"{manifest_path}: generation/completion record mismatch")
            if not np.allclose(manifest.get("k_grid", []), K_GRID, rtol=0, atol=1e-12):
                raise InvalidInput(f"{manifest_path}: frozen k grid mismatch")
            if "/dev/shm" in json.dumps(manifest):
                raise InvalidInput(f"{manifest_path}: /dev/shm dependency")

            run_id = f"K2_final__PSC__{dataset}__seed{seed}"
            if manifest.get("run_id") != run_id or run_id not in k2_rows:
                raise InvalidInput(f"{manifest_path}: frozen K2 run identity mismatch")
            k2_manifest_path = resolve_project_artifact(manifest["k2_artifact_manifest_path"])
            if k2_manifest_path != K2_ARTIFACT_MANIFEST.resolve():
                raise InvalidInput(f"{manifest_path}: K2 artifact manifest path mismatch")
            if manifest.get("k2_artifact_manifest_sha256") != k2_manifest_sha:
                raise InvalidInput(f"{manifest_path}: K2 artifact manifest SHA mismatch")

            cfg = resolve_project_artifact(manifest["config_path"])
            checkpoint = resolve_project_artifact(manifest["checkpoint_path"])
            if cfg != expected_cfg.resolve() or checkpoint != expected_checkpoint.resolve():
                raise InvalidInput(f"{manifest_path}: not the expected frozen K2 config/checkpoint")
            if sha256(cfg) != manifest.get("config_sha256"):
                raise InvalidInput(f"{manifest_path}: config SHA mismatch")
            if sha256(checkpoint) != manifest.get("checkpoint_sha256"):
                raise InvalidInput(f"{manifest_path}: checkpoint SHA mismatch")
            k2_row = k2_rows[run_id]
            if Path(k2_row["checkpoint"]).resolve() != checkpoint:
                raise InvalidInput(f"{manifest_path}: checkpoint path differs from K2 artifact manifest")
            if not manifest["checkpoint_sha256"].startswith(k2_row["ckpt_sha"]):
                raise InvalidInput(f"{manifest_path}: checkpoint SHA differs from K2 artifact manifest")
            k2_eval = resolve_project_artifact(manifest["k2_eval_path"])
            if k2_eval != Path(k2_row["eval_json"]).resolve():
                raise InvalidInput(f"{manifest_path}: K2 evaluator path mismatch")
            if not k2_eval.is_file() or sha256(k2_eval) != manifest.get("k2_eval_sha256"):
                raise InvalidInput(f"{manifest_path}: K2 evaluator SHA mismatch")
            if not manifest["k2_eval_sha256"].startswith(k2_row["eval_sha"]):
                raise InvalidInput(f"{manifest_path}: K2 evaluator differs from artifact manifest")
            k2_payload = json.loads(k2_eval.read_text(encoding="utf-8"))
            if (k2_payload.get("run_id") != run_id or k2_payload.get("head") != "PSC"
                    or k2_payload.get("dataset") != dataset):
                raise InvalidInput(f"{manifest_path}: frozen K2 evaluator identity mismatch")

            summary = resolve_project_artifact(manifest["summary_path"])
            matched = resolve_project_artifact(manifest["matched_path"])
            if not summary.is_file() or not matched.is_file() or not summary.stat().st_size or not matched.stat().st_size:
                missing.extend(str(path) for path in (summary, matched) if not path.is_file() or not path.stat().st_size)
                continue
            if summary.stat().st_size != int(manifest.get("summary_bytes", -1)) or sha256(summary) != manifest.get("summary_sha256"):
                raise InvalidInput(f"{manifest_path}: radial summary bytes/SHA mismatch")
            if matched.stat().st_size != int(manifest.get("matched_bytes", -1)) or sha256(matched) != manifest.get("matched_sha256"):
                raise InvalidInput(f"{manifest_path}: matched artifact bytes/SHA mismatch")
            n_images = int(manifest.get("n_images", 0))
            matched_rows = int(manifest.get("matched_rows", 0))
            if n_images != EXPECTED_IMAGES[dataset] or matched_rows <= 0:
                raise InvalidInput(f"{manifest_path}: incomplete full-validation forward artifact")
            summary_rows = validate_summary(summary, dataset, seed, n_images)
            k1_row = next(row for row in summary_rows if abs(float(row["k"]) - 1.0) < 1e-12)
            if (matched_rows != int(k2_payload.get("n_matched", -1))
                    or abs(float(k1_row["AP50"]) - float(k2_payload["AP50"])) > 2e-4
                    or abs(float(k1_row["AP75"]) - float(k2_payload["AP75"])) > 2e-4):
                raise InvalidInput(
                    f"{manifest_path}: k=1 instrumented output differs from frozen K2 evaluator")
            supplement = validate_actual_loss_supplement(
                out_dir, dataset, seed, expected_cfg, expected_checkpoint,
                k2_manifest_sha, k2_eval, EXPECTED_GT_PATHS[dataset])
            supplement_by_k = {float(row["k"]): row for row in supplement["rows"]}
            merged_summary = []
            for row in summary_rows:
                merged = dict(row)
                replacement = supplement_by_k[float(row["k"])]
                for field in ACTUAL_HEAD_FIELDS:
                    merged[field] = replacement[field]
                merged["actual_head_statistics_source"] = "targeted_network_coordinate_supplement"
                merged["legacy_actual_head_fields_superseded"] = "True"
                merged_summary.append(merged)
            summary_rows = merged_summary
            forward_log = REPO / f"logs/m069/psc_phase1_forward/{dataset}_seed{seed}.log"
            if not forward_log.is_file() or " DONE " not in (" " + forward_log.read_text(errors="ignore") + " "):
                raise InvalidInput(f"{forward_log}: missing normal DONE record")
            sources.append({
                "dataset": dataset,
                "seed": seed,
                "manifest_path": manifest_path,
                "manifest": manifest,
                "summary_path": summary,
                "summary_rows": summary_rows,
                "matched_path": matched,
                "checkpoint_path": checkpoint,
                "checkpoint_sha256": manifest["checkpoint_sha256"],
                "forward_log": forward_log,
                "actual_supplement_manifest_path": supplement["manifest_path"],
                "actual_supplement_summary_path": supplement["summary_path"],
                "actual_supplement_log_path": supplement["log_path"],
            })
    if missing:
        raise PendingInputs("missing PSC forward inputs:\n" + "\n".join(sorted(set(missing))))
    if len(sources) != 6:
        raise PendingInputs(f"only {len(sources)}/6 PSC forward cells validated")
    return sources


def validate_native_endpoint_inputs():
    """Validate all 12 frozen DCL/CSL Phase-1 endpoint extractions."""
    if not K2_ARTIFACT_MANIFEST.is_file():
        raise PendingInputs(f"missing frozen K2 artifact manifest: {K2_ARTIFACT_MANIFEST}")
    k2_index_sha = sha256(K2_ARTIFACT_MANIFEST)
    with K2_ARTIFACT_MANIFEST.open(newline="", encoding="utf-8") as handle:
        k2_rows = {row["run_id"]: row for row in csv.DictReader(handle)}
    required_row = {
        "head", "dataset", "seed", "image_id", "pred_id", "gt_id", "class",
        "detection_score", "native_score", "native_signal", "angle_error",
        "aspect_ratio", "size", "pred_box", "gt_box", "match_iou", "post_nms",
    }
    expected_signal = {
        "DCL": "dcl_mean_sigmoid_bit_margin",
        "CSL": "csl_softmax_top1_top2_margin",
    }
    sources = []
    missing = []
    for head in ("DCL", "CSL"):
        for dataset in DATASETS:
            slug = "dior" if dataset == "DIOR-R" else "soda"
            for seed in SEEDS:
                run_id = f"K2_final__{head}__{dataset}__seed{seed}"
                work = REPO / f"work_dirs/k2/{run_id}"
                cfg = work / f"{head.lower()}_{slug}_seed0.py"
                checkpoint = work / "epoch_12.pth"
                out_dir = NATIVE_ROOT / head / dataset / f"seed{seed}"
                manifest_path = out_dir / "manifest.json"
                matched_path = out_dir / "matched_native.jsonl"
                for path in (cfg, checkpoint, manifest_path, matched_path):
                    if not path.is_file() or not path.stat().st_size:
                        missing.append(str(path))
                if any(not path.is_file() or not path.stat().st_size
                       for path in (cfg, checkpoint, manifest_path, matched_path)):
                    continue
                try:
                    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                except json.JSONDecodeError as exc:
                    raise InvalidInput(f"{manifest_path}: malformed JSON") from exc
                required_manifest = {
                    "status", "schema_version", "run_id", "head", "dataset", "seed",
                    "n_images", "n_gt", "n_predictions", "n_matched", "native_signal",
                    "matching", "matched_path", "matched_sha256", "matched_bytes",
                    "config_path", "config_sha256", "checkpoint_path", "checkpoint_sha256",
                    "k2_artifact_manifest_path", "k2_artifact_manifest_sha256",
                    "k2_eval_path", "k2_eval_sha256", "gt_path", "gt_sha256",
                    "identity_only", "post_nms_own_detector_matching", "no_tta",
                    "no_ap_evaluation", "no_training", "generation_command", "completed_at",
                }
                absent = required_manifest.difference(manifest)
                if absent:
                    raise InvalidInput(f"{manifest_path}: missing fields {sorted(absent)}")
                if (manifest.get("status") != "complete"
                        or manifest.get("schema_version") != NATIVE_ENDPOINT_SCHEMA
                        or manifest.get("run_id") != run_id or manifest.get("head") != head
                        or manifest.get("dataset") != dataset or int(manifest.get("seed", -1)) != seed
                        or int(manifest.get("n_images", -1)) != EXPECTED_IMAGES[dataset]
                        or int(manifest.get("n_gt", -1)) != EXPECTED_GT[dataset]
                        or int(manifest.get("n_predictions", 0)) <= 0
                        or int(manifest.get("n_matched", 0)) <= 0
                        or manifest.get("native_signal") != expected_signal[head]):
                    raise InvalidInput(f"{manifest_path}: identity/cardinality/native-signal mismatch")
                if not all(manifest.get(field) is True for field in (
                        "identity_only", "post_nms_own_detector_matching", "no_tta",
                        "no_ap_evaluation", "no_training")):
                    raise InvalidInput(f"{manifest_path}: extraction-scope declaration mismatch")
                if "/dev/shm" in json.dumps(manifest):
                    raise InvalidInput(f"{manifest_path}: /dev/shm dependency")
                expected_command = f"scripts/m069_psc_native_signal_dump.py {head} {dataset} {seed}"
                if expected_command not in manifest["generation_command"] or not manifest["completed_at"]:
                    raise InvalidInput(f"{manifest_path}: generation/completion record mismatch")

                k2_row = k2_rows.get(run_id)
                if k2_row is None:
                    raise InvalidInput(f"{K2_ARTIFACT_MANIFEST}: missing {run_id}")
                k2_eval = Path(k2_row["eval_json"]).resolve()
                gt_path = EXPECTED_GT_PATHS[dataset].resolve()
                recorded_paths = {
                    "matched": resolve_project_artifact(manifest["matched_path"]),
                    "config": resolve_project_artifact(manifest["config_path"]),
                    "checkpoint": resolve_project_artifact(manifest["checkpoint_path"]),
                    "k2_index": resolve_project_artifact(manifest["k2_artifact_manifest_path"]),
                    "k2_eval": resolve_project_artifact(manifest["k2_eval_path"]),
                    "gt": resolve_project_artifact(manifest["gt_path"]),
                }
                expected_paths_map = {
                    "matched": matched_path.resolve(), "config": cfg.resolve(),
                    "checkpoint": checkpoint.resolve(), "k2_index": K2_ARTIFACT_MANIFEST.resolve(),
                    "k2_eval": k2_eval, "gt": gt_path,
                }
                if recorded_paths != expected_paths_map or Path(k2_row["checkpoint"]).resolve() != checkpoint.resolve():
                    raise InvalidInput(f"{manifest_path}: frozen K2/GT source path drift")
                expected_hashes = {
                    "matched_sha256": sha256(matched_path), "config_sha256": sha256(cfg),
                    "checkpoint_sha256": sha256(checkpoint),
                    "k2_artifact_manifest_sha256": k2_index_sha,
                    "k2_eval_sha256": sha256(k2_eval), "gt_sha256": sha256(gt_path),
                }
                if any(manifest.get(field) != value for field, value in expected_hashes.items()):
                    raise InvalidInput(f"{manifest_path}: output/source SHA mismatch")
                if (not manifest["checkpoint_sha256"].startswith(k2_row["ckpt_sha"])
                        or not manifest["k2_eval_sha256"].startswith(k2_row["eval_sha"])
                        or str(k2_row.get("can_recompute", "")).strip().lower() not in {"yes", "true", "1"}):
                    raise InvalidInput(f"{manifest_path}: frozen K2 index mismatch")
                k2_payload = json.loads(k2_eval.read_text(encoding="utf-8"))
                if (k2_payload.get("run_id") != run_id or k2_payload.get("head") != head
                        or k2_payload.get("dataset") != dataset
                        or int(k2_payload.get("n_matched", -1)) != int(manifest["n_matched"])):
                    raise InvalidInput(f"{manifest_path}: K2 matched cardinality mismatch")
                if (matched_path.stat().st_size != int(manifest.get("matched_bytes", -1))
                        or sum(1 for line in matched_path.open(encoding="utf-8") if line.strip())
                        != int(manifest["n_matched"])):
                    raise InvalidInput(f"{manifest_path}: matched bytes/rows mismatch")
                with matched_path.open(encoding="utf-8") as handle:
                    first_line = next((line for line in handle if line.strip()), "")
                first = json.loads(first_line)
                if required_row.difference(first):
                    raise InvalidInput(f"{matched_path}: native endpoint row schema incomplete")
                if (first.get("head") != head or first.get("dataset") != dataset
                        or int(first.get("seed", -1)) != seed
                        or first.get("native_signal") != expected_signal[head]
                        or first.get("post_nms") is not True):
                    raise InvalidInput(f"{matched_path}: first row identity mismatch")
                completion_log = REPO / f"logs/m069/psc_phase1_native_signals/{head}_{dataset}_seed{seed}.log"
                done = f"{head} {dataset} seed={seed} DONE images={EXPECTED_IMAGES[dataset]} gt={EXPECTED_GT[dataset]}"
                if not completion_log.is_file() or done not in completion_log.read_text(errors="ignore"):
                    raise InvalidInput(f"{completion_log}: missing normal DONE record")
                if list(out_dir.glob("*.tmp")):
                    raise InvalidInput(f"{out_dir}: incomplete native endpoint temporary artifact")
                sources.append({
                    "head": head, "dataset": dataset, "seed": seed,
                    "manifest": manifest, "manifest_path": manifest_path,
                    "matched_path": matched_path, "checkpoint_path": checkpoint,
                    "k2_eval_path": k2_eval, "completion_log": completion_log,
                })
    if missing:
        raise PendingInputs("missing DCL/CSL native endpoint inputs:\n" + "\n".join(sorted(set(missing))))
    if len(sources) != 12:
        raise PendingInputs(f"only {len(sources)}/12 DCL/CSL native endpoint cells validated")
    return sources


def radial_analysis(sources):
    radial_rows = []
    branch_rows = []
    for source in sources:
        rows = source["summary_rows"]
        base = next(row for row in rows if abs(float(row["k"]) - 1.0) < 1e-12)
        base_loss = abs(float(base["actual_head_mean_angle_loss"]))
        base_mod = float(base["controlled_base_mean_phase_mod_primary"])
        cell_rows = []
        for row in rows:
            k = float(row["k"])
            loss_relative = abs(
                float(row["actual_head_mean_angle_loss"])
                - float(base["actual_head_mean_angle_loss"])
            ) / max(base_loss, 1e-12)
            mod_ratio = float(row["controlled_base_mean_phase_mod_primary"]) / max(base_mod, 1e-12)
            output = dict(row)
            output.update({
                "actual_head_loss_relative_change_vs_k1": round(loss_relative, 10),
                "controlled_phase_mod_ratio_vs_k1": round(mod_ratio, 8),
                "phase_mod_expected_k2": round(k * k, 8),
                "phase_mod_k2_abs_error": round(abs(mod_ratio - k * k), 8),
                "manifest_sha256": sha256(source["manifest_path"]),
                "actual_head_supplement_manifest_sha256": sha256(
                    source["actual_supplement_manifest_path"]),
                "checkpoint_sha256": source["checkpoint_sha256"],
                "mask_definition": (
                    "full evaluator radial intervention; matched diagnostics use frozen K2 val; "
                    "actual head loss uses network-coordinate targeted supplement"),
            })
            radial_rows.append(output)
            cell_rows.append(output)
        max_median = max(float(row["decoded_angle_median_diff_deg"]) for row in cell_rows)
        max_p95 = max(float(row["decoded_angle_p95_diff_deg"]) for row in cell_rows)
        max_loss_relative = max(float(row["actual_head_loss_relative_change_vs_k1"]) for row in cell_rows)
        min_set_equal = min(float(row["post_nms_score_label_count_equal_proportion"]) for row in cell_rows)
        decoded_gate = max_median < 0.5 and max_p95 < 1.0
        loss_gate = max_loss_relative < 1e-3
        cell_branch = "A" if decoded_gate and loss_gate else "B"
        if cell_branch == "A":
            structural_cause = "radial_magnitude_decode_irrelevant_and_loss_weak"
        elif not decoded_gate:
            structural_cause = "radial_decoder_sensitivity_including_modulation_threshold_or_wrapping"
        else:
            structural_cause = "radial_magnitude_semantics_in_configured_angle_loss"
        branch_rows.append({
            "scope": "dataset_seed",
            "dataset": source["dataset"],
            "seed": source["seed"],
            "branch": cell_branch,
            "decoded_median_max_deg": round(max_median, 8),
            "decoded_p95_max_deg": round(max_p95, 8),
            "loss_relative_change_max": round(max_loss_relative, 10),
            "post_nms_score_label_count_equal_min": round(min_set_equal, 8),
            "decoded_gate_lt_0.5median_lt_1p95": str(decoded_gate),
            "loss_gate_rel_lt_1e-3": str(loss_gate),
            "structural_cause": structural_cause,
            "structural_cause_intervention_verified": "True",
            "branch_consistent_all_six": "",
            "start": START,
            "deadline": DEADLINE,
            "note": "Loss gate uses the configured anchor-assigned PSC head loss L(kz); matched post-NMS L1 is diagnostic only.",
        })
    overall_a = all(row["branch"] == "A" for row in branch_rows)
    overall_b = all(row["branch"] == "B" for row in branch_rows)
    decoded_sensitivity_all = all(
        row["decoded_gate_lt_0.5median_lt_1p95"] == "False" for row in branch_rows)
    loss_semantics_all = all(row["loss_gate_rel_lt_1e-3"] == "False" for row in branch_rows)
    if overall_a:
        structural_cause = "radial_magnitude_decode_irrelevant_and_loss_weak"
        structural_verified = True
    elif overall_b and decoded_sensitivity_all:
        structural_cause = "stable_six_cell_radial_decoder_sensitivity_including_modulation_threshold_or_wrapping"
        structural_verified = True
    elif overall_b and loss_semantics_all:
        structural_cause = "stable_six_cell_radial_magnitude_semantics_in_configured_angle_loss"
        structural_verified = True
    else:
        structural_cause = "heterogeneous_radial_response_no_single_six_cell_structural_cause"
        structural_verified = False
    branch_rows.append({
        "scope": "overall",
        "dataset": "DIOR-R+SODA-A",
        "seed": "all_3_seeds",
        "branch": "A" if overall_a else "B",
        "decoded_median_max_deg": max(row["decoded_median_max_deg"] for row in branch_rows),
        "decoded_p95_max_deg": max(row["decoded_p95_max_deg"] for row in branch_rows),
        "loss_relative_change_max": max(row["loss_relative_change_max"] for row in branch_rows),
        "post_nms_score_label_count_equal_min": min(row["post_nms_score_label_count_equal_min"] for row in branch_rows),
        "decoded_gate_lt_0.5median_lt_1p95": str(all(row["decoded_gate_lt_0.5median_lt_1p95"] == "True" for row in branch_rows)),
        "loss_gate_rel_lt_1e-3": str(all(row["loss_gate_rel_lt_1e-3"] == "True" for row in branch_rows)),
        "structural_cause": structural_cause,
        "structural_cause_intervention_verified": str(structural_verified),
        "branch_consistent_all_six": str(overall_a or overall_b),
        "start": START,
        "deadline": DEADLINE,
        "note": "Overall A requires all six cells to pass decode invariance and configured anchor-loss relative-change gates.",
    })
    return radial_rows, branch_rows


def load_matched(source):
    columns = {name: [] for name in (
        "image_id", "pred_id", "class", "score", "angle_error", "aspect_ratio", "size", "decoded_angle",
        "objectness", "boundary_distance_deg", "wrapping_condition", "phase_mod_primary", "phase_mod_secondary",
        "phase_angle_primary", "phase_angle_secondary", "multi_frequency_disagreement_deg",
        "unwrap_candidate_energy_gap", "phase_direction_margin", "angle_vector_norm",
        "reg_feature_norm", "tta_phase_direction_circular_variance", "n_tta_phase_angles",
    )}
    row_count = 0
    with source["matched_path"].open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            missing = MATCHED_REQUIRED.difference(row)
            if missing:
                raise InvalidInput(f"{source['matched_path']}:{line_number}: missing {sorted(missing)}")
            if row["dataset"] != source["dataset"] or int(row["seed"]) != source["seed"]:
                raise InvalidInput(f"{source['matched_path']}:{line_number}: dataset/seed mismatch")
            for name in columns:
                value = row[name]
                columns[name].append(np.nan if value is None else value)
            row_count += 1
    if row_count != int(source["manifest"]["matched_rows"]):
        raise InvalidInput(f"{source['matched_path']}: matched_rows mismatch")
    object_fields = {"image_id", "pred_id", "class"}
    bool_fields = {"wrapping_condition"}
    output = {}
    for name, values in columns.items():
        if name in object_fields:
            output[name] = np.asarray(values, dtype=object)
        elif name in bool_fields:
            output[name] = np.asarray(values, dtype=bool)
        else:
            output[name] = np.asarray(values, dtype=float)
    finite_required = set(columns).difference({
        "image_id", "pred_id", "class", "wrapping_condition",
        "objectness", "tta_phase_direction_circular_variance",
    })
    for name in finite_required:
        if not np.isfinite(output[name]).all():
            raise InvalidInput(f"{source['matched_path']}: nonfinite {name}")
    if np.any(output["aspect_ratio"] < 1.0) or np.any(output["size"] <= 0.0):
        raise InvalidInput(f"{source['matched_path']}: invalid GT geometry")
    if np.any(output["angle_error"] < 0.0) or np.any(output["angle_error"] > 90.0):
        raise InvalidInput(f"{source['matched_path']}: angle_error outside le90 range")
    if np.any(output["score"] < 0.0) or np.any(output["score"] > 1.0):
        raise InvalidInput(f"{source['matched_path']}: detection score outside [0,1]")
    unique_keys = set(zip(output["image_id"].tolist(), output["pred_id"].tolist()))
    if len(unique_keys) != row_count:
        raise InvalidInput(f"{source['matched_path']}: duplicate image_id/pred_id rows")
    tta = output["tta_phase_direction_circular_variance"]
    if source["seed"] == 0:
        finite_tta = np.isfinite(tta)
        if not finite_tta.any() or np.any(tta[finite_tta] < 0.0) or np.any(tta[finite_tta] > 1.0):
            raise InvalidInput(f"{source['matched_path']}: invalid seed0 TTA variance")
    elif np.isfinite(tta).any():
        raise InvalidInput(f"{source['matched_path']}: unexpected non-seed0 TTA values")
    return output


def load_native_endpoint(source):
    columns = {name: [] for name in (
        "image_id", "pred_id", "class", "detection_score", "native_score",
        "angle_error", "aspect_ratio", "size",
    )}
    expected_signal = (
        "dcl_mean_sigmoid_bit_margin" if source["head"] == "DCL"
        else "csl_softmax_top1_top2_margin")
    count = 0
    with source["matched_path"].open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            row = json.loads(line)
            if (row.get("head") != source["head"] or row.get("dataset") != source["dataset"]
                    or int(row.get("seed", -1)) != source["seed"]
                    or row.get("native_signal") != expected_signal or row.get("post_nms") is not True):
                raise InvalidInput(f"{source['matched_path']}:{line_number}: identity/signal mismatch")
            for field in columns:
                columns[field].append(row[field])
            count += 1
    if count != int(source["manifest"]["n_matched"]):
        raise InvalidInput(f"{source['matched_path']}: native matched row count mismatch")
    output = {
        field: np.asarray(values, dtype=object if field in {"image_id", "pred_id", "class"} else float)
        for field, values in columns.items()
    }
    for field in ("detection_score", "native_score", "angle_error", "aspect_ratio", "size"):
        if not np.isfinite(output[field]).all():
            raise InvalidInput(f"{source['matched_path']}: nonfinite {field}")
    if (np.any(output["detection_score"] < 0) or np.any(output["detection_score"] > 1)
            or np.any(output["native_score"] < 0) or np.any(output["native_score"] > 1)
            or np.any(output["angle_error"] < 0) or np.any(output["angle_error"] > 90)
            or np.any(output["aspect_ratio"] < 1) or np.any(output["size"] <= 0)):
        raise InvalidInput(f"{source['matched_path']}: native endpoint value outside contract")
    if len(set(zip(output["image_id"].tolist(), output["pred_id"].tolist()))) != count:
        raise InvalidInput(f"{source['matched_path']}: duplicate image_id/pred_id")
    return output


def safe_spearman(left, right):
    mask = np.isfinite(left) & np.isfinite(right)
    if mask.sum() < 3 or np.unique(left[mask]).size < 2 or np.unique(right[mask]).size < 2:
        return float("nan")
    return float(spearmanr(left[mask], right[mask]).correlation)


def dissection_rows(source, data, severe, threshold, mask):
    rows = []

    def add(analysis_id, analysis_name, group_type, group_value, statistic, estimate, n, note="", evidence=None):
        rows.append({
            "analysis_id": analysis_id,
            "analysis_name": analysis_name,
            "dataset": source["dataset"],
            "seed": source["seed"],
            "mask_definition": "aspect_ratio>=2.1",
            "risk_event": "angle_error>delta_theta_0.75(aspect_ratio)",
            "group_type": group_type,
            "group_value": group_value,
            "statistic": statistic,
            "estimate": estimate,
            "n": int(n),
            "status": "COMPLETE" if n else "UNAVAILABLE",
            "note": note,
            "evidence_json": json.dumps(evidence, sort_keys=True, ensure_ascii=False) if evidence is not None else "",
        })

    idx = np.where(mask)[0]
    pm = data["phase_mod_primary"]
    error = data["angle_error"]
    # 1. phase_mod x angle error: rank association and frozen deciles.
    add(1, "phase_mod_x_angle_error", "all", "all", "spearman", safe_spearman(pm[idx], error[idx]), len(idx))
    if len(idx):
        edges = np.quantile(pm[idx], np.linspace(0, 1, 11))
        bins = np.clip(np.searchsorted(edges[1:-1], pm[idx], side="right"), 0, 9)
        for decile in range(10):
            take = idx[bins == decile]
            add(1, "phase_mod_x_angle_error", "phase_mod_decile", f"D{decile + 1}", "mean_angle_error_deg",
                round(float(error[take].mean()), 8) if len(take) else "", len(take))
            add(1, "phase_mod_x_angle_error", "phase_mod_decile", f"D{decile + 1}", "severe_event_rate",
                round(float(severe[take].mean()), 8) if len(take) else "", len(take))

    # 2. Phase-vector direction is circular; report its sine/cosine components.
    phase = data["phase_angle_primary"]
    add(2, "phase_mod_x_phase_angle", "all", "all", "spearman_cos_phase",
        safe_spearman(pm[idx], np.cos(phase[idx])), len(idx))
    add(2, "phase_mod_x_phase_angle", "all", "all", "spearman_sin_phase",
        safe_spearman(pm[idx], np.sin(phase[idx])), len(idx))
    # 3. RetinaNet has no independent objectness branch; do not relabel its
    # classification/detection score as objectness.
    add(3, "phase_mod_x_objectness", "all", "all", "availability", "", 0,
        note="UNAVAILABLE: frozen PSC RetinaNet has no separate objectness output; detection score is reported only in the registered score comparison.")
    # 4-5. Actual shared regression/angle-tower feature norm and GT size.
    for analysis_id, name, field, transform, note in (
        (4, "phase_mod_x_feature_norm", "reg_feature_norm", lambda x: x,
         "Feature norm is the actual shared regression/angle-tower feature at the post-NMS-selected FPN location."),
        (5, "phase_mod_x_size", "size", lambda x: np.log(np.maximum(x, 1e-12)),
         "Size statistic uses log(GT box area) for preregistered diagnostic conditioning only."),
    ):
        add(analysis_id, name, "all", "all", "spearman",
            safe_spearman(pm[idx], transform(data[field][idx])), len(idx), note=note)
    # 6. class-conditional phase magnitude and severe rate.
    for class_name in sorted(set(data["class"][idx])):
        take = idx[data["class"][idx] == class_name]
        add(6, "phase_mod_x_class", "class", class_name, "median_phase_mod",
            round(float(np.median(pm[take])), 8), len(take))
        add(6, "phase_mod_x_class", "class", class_name, "severe_event_rate",
            round(float(severe[take].mean()), 8), len(take))
    # 7. boundary/wrapping conditioning.
    boundary = data["boundary_distance_deg"]
    add(7, "phase_mod_x_boundary_wrapping", "all", "all", "spearman_boundary_distance",
        safe_spearman(pm[idx], boundary[idx]), len(idx))
    for wrapped in (False, True):
        take = idx[data["wrapping_condition"][idx] == wrapped]
        add(7, "phase_mod_x_boundary_wrapping", "wrapping_condition", str(wrapped), "severe_event_rate",
            round(float(severe[take].mean()), 8) if len(take) else "", len(take))
    # 8. Persist the preregistered high-phase/high-error instance board as long-form evidence rows.
    if len(idx):
        high_cut = float(np.quantile(pm[idx], 0.9))
        take = idx[(pm[idx] >= high_cut) & severe[idx].astype(bool)]
        take = take[np.argsort(-error[take], kind="stable")[:100]]
        for rank, pos in enumerate(take, 1):
            evidence = {
                "image_id": str(data["image_id"][pos]),
                "pred_id": str(data["pred_id"][pos]),
                "class": str(data["class"][pos]),
                "phase_mod": round(float(pm[pos]), 8),
                "angle_error_deg": round(float(error[pos]), 8),
                "delta_theta_075_deg": round(float(threshold[pos]), 8),
            }
            add(8, "high_phase_mod_large_error_board", "instance_rank", rank, "listed_instance", 1, 1,
                note="Top phase-mod decile and geometry-normalized severe event.", evidence=evidence)
    # 9-12. Registered mechanism diagnostics.
    for analysis_id, name, field in (
        (9, "multi_frequency_circular_disagreement", "multi_frequency_disagreement_deg"),
        (10, "unwrap_candidate_energy_gap", "unwrap_candidate_energy_gap"),
        (11, "phase_direction_margin", "phase_direction_margin"),
        (12, "tta_phase_direction_circular_variance", "tta_phase_direction_circular_variance"),
    ):
        valid = idx[np.isfinite(data[field][idx])]
        if not len(valid):
            add(analysis_id, name, "all", "all", "availability", "", 0,
                note="TTA was preregistered for seed0 only." if analysis_id == 12 else "No finite values.")
            continue
        add(analysis_id, name, "all", "all", "mean", round(float(data[field][valid].mean()), 8), len(valid))
        add(analysis_id, name, "all", "all", "p90", round(float(np.percentile(data[field][valid], 90)), 8), len(valid))
        add(analysis_id, name, "all", "all", "spearman_angle_error",
            safe_spearman(data[field][valid], error[valid]), len(valid))
    return rows


def metric_bundle(scores, risks):
    if len(scores) < 50:
        return {name: float("nan") for name in ("nrc", "aurc", "risk70", "risk90")}
    result = nrc_auc(scores, risks)
    return {
        "nrc": float(result["nrc_auc"]),
        "aurc": float(aurc(scores, risks)),
        "risk70": float(risk_at_coverage(scores, risks, 0.70)),
        "risk90": float(risk_at_coverage(scores, risks, 0.90)),
    }


def percentile_interval(values):
    finite = np.asarray([value for value in values if math.isfinite(value)], dtype=float)
    if not len(finite):
        return float("nan"), float("nan")
    return float(np.percentile(finite, 2.5)), float(np.percentile(finite, 97.5))


def weighted_metric_bundle(order, risks, weights, harmonic):
    """Exact selective metrics for an integer-weighted, pre-sorted sample."""
    sorted_risk = risks[order]
    sorted_weight = weights[order]
    keep = sorted_weight > 0
    sorted_risk = sorted_risk[keep]
    sorted_weight = sorted_weight[keep]
    cumulative_count = np.cumsum(sorted_weight, dtype=np.int64)
    total = int(cumulative_count[-1])
    cumulative_risk = np.cumsum(sorted_weight * sorted_risk, dtype=float)
    count_before = cumulative_count - sorted_weight
    risk_before = cumulative_risk - sorted_weight * sorted_risk
    harmonic_delta = harmonic[cumulative_count] - harmonic[count_before]
    aurc_value = float(np.sum(
        sorted_weight * sorted_risk
        + (risk_before - count_before * sorted_risk) * harmonic_delta
    ) / total)

    def risk_at(coverage):
        retained = int(math.ceil(coverage * total))
        position = int(np.searchsorted(cumulative_count, retained, side="left"))
        copies = retained - int(count_before[position])
        return float((risk_before[position] + copies * sorted_risk[position]) / retained)

    return aurc_value, risk_at(0.70), risk_at(0.90)


def cluster_bootstrap(scores, reference, risks, image_ids, replicates, workers, seed):
    image_ids = np.asarray(image_ids, dtype=object)
    _, image_inverse = np.unique(image_ids, return_inverse=True)
    n_images = int(image_inverse.max()) + 1
    if n_images < 2:
        return {}
    candidate_order = np.argsort(-scores, kind="stable")
    reference_order = np.argsort(-reference, kind="stable")
    oracle_order = np.argsort(risks, kind="stable")

    def one(rep):
        rng = np.random.RandomState((seed + rep * 104729) % (2**32 - 1))
        picked = rng.randint(0, n_images, size=n_images)
        image_weight = np.bincount(picked, minlength=n_images)
        weights = image_weight[image_inverse]
        total = int(weights.sum())
        harmonic = np.empty(total + 1, dtype=float)
        harmonic[0] = 0.0
        np.cumsum(1.0 / np.arange(1, total + 1, dtype=float), out=harmonic[1:])
        oracle_aurc, _, _ = weighted_metric_bundle(oracle_order, risks, weights, harmonic)
        random_aurc = float(np.dot(weights, risks) / total)
        denominator = random_aurc - oracle_aurc

        def evaluate(order):
            model_aurc, risk70, risk90 = weighted_metric_bundle(order, risks, weights, harmonic)
            nrc = float("nan") if abs(denominator) < 1e-12 else (model_aurc - oracle_aurc) / denominator
            return {"nrc": nrc, "aurc": model_aurc, "risk70": risk70, "risk90": risk90}

        candidate_metrics = evaluate(candidate_order)
        reference_metrics = evaluate(reference_order)
        return candidate_metrics, {key: candidate_metrics[key] - reference_metrics[key] for key in candidate_metrics}

    if workers == 1:
        samples = [one(rep) for rep in range(replicates)]
    else:
        with ThreadPoolExecutor(max_workers=workers) as executor:
            samples = list(executor.map(one, range(replicates)))
    output = {}
    for metric in ("nrc", "aurc", "risk70", "risk90"):
        output[f"{metric}_ci"] = percentile_interval([sample[0][metric] for sample in samples])
        output[f"delta_{metric}_ci"] = percentile_interval([sample[1][metric] for sample in samples])
    return output


def score_arrays(data):
    return {
        "phase_mod": data["phase_mod_primary"],
        "negative_phase_mod": -data["phase_mod_primary"],
        "detection_score": data["score"],
        "tta_phase_direction_consistency": -data["tta_phase_direction_circular_variance"],
        "multi_frequency_consistency": -data["multi_frequency_disagreement_deg"],
        "unwrap_candidate_energy_gap": data["unwrap_candidate_energy_gap"],
        "phase_direction_margin": data["phase_direction_margin"],
    }


def score_comparison_rows(source, data, severe, mask, replicates, workers):
    rows = []
    arrays = score_arrays(data)
    reference = arrays["negative_phase_mod"]
    for score_name, values in arrays.items():
        common = mask & np.isfinite(values) & np.isfinite(reference)
        if common.sum() < 50:
            rows.append({
                "dataset": source["dataset"], "seed": source["seed"], "score": score_name,
                "score_family": "registered_psc_phase1", "formula": SCORE_FORMULAS[score_name],
                "endpoint": "geometry_normalized_severe_event", "mask_definition": "aspect_ratio>=2.1",
                "risk_event": "angle_error>delta_theta_0.75(aspect_ratio)", "ar_threshold": AR_MAIN,
                "retained_count": int(common.sum()), "retained_ratio": round(float(common.mean()), 8),
                "n": int(common.sum()), "n_images": len(set(data["image_id"][common])),
                "nrc": "", "nrc_ci_lo": "", "nrc_ci_hi": "", "aurc": "", "aurc_ci_lo": "", "aurc_ci_hi": "",
                "risk70": "", "risk70_ci_lo": "", "risk70_ci_hi": "", "risk90": "", "risk90_ci_lo": "", "risk90_ci_hi": "",
                "reference_score": "negative_phase_mod", "delta_nrc": "", "delta_nrc_ci_lo": "", "delta_nrc_ci_hi": "",
                "delta_aurc": "", "delta_aurc_ci_lo": "", "delta_aurc_ci_hi": "", "delta_risk70": "",
                "delta_risk70_ci_lo": "", "delta_risk70_ci_hi": "", "delta_risk90": "", "delta_risk90_ci_lo": "", "delta_risk90_ci_hi": "",
                "bootstrap_unit": "image", "bootstrap_replicates": replicates, "comparison_status": "UNAVAILABLE",
                "source_file": str(source["matched_path"].relative_to(ROOT)), "source_sha256": source["manifest"]["matched_sha256"],
            })
            continue
        candidate = values[common]
        ref = reference[common]
        risk = severe[common]
        images = data["image_id"][common]
        metrics = metric_bundle(candidate, risk)
        reference_metrics = metric_bundle(ref, risk)
        boot = cluster_bootstrap(candidate, ref, risk, images, replicates, workers,
                                 stable_seed(source["dataset"], source["seed"], score_name))
        row = {
            "dataset": source["dataset"], "seed": source["seed"], "score": score_name,
            "score_family": "registered_psc_phase1", "formula": SCORE_FORMULAS[score_name],
            "endpoint": "geometry_normalized_severe_event", "mask_definition": "aspect_ratio>=2.1",
            "risk_event": "angle_error>delta_theta_0.75(aspect_ratio)", "ar_threshold": AR_MAIN,
            "retained_count": int(common.sum()), "retained_ratio": round(float(common.mean()), 8),
            "n": int(common.sum()), "n_images": len(set(images)),
            "reference_score": "negative_phase_mod", "bootstrap_unit": "image",
            "bootstrap_replicates": replicates, "comparison_status": "PAIRED_COMPARABLE",
            "source_file": str(source["matched_path"].relative_to(ROOT)), "source_sha256": source["manifest"]["matched_sha256"],
        }
        for metric in ("nrc", "aurc", "risk70", "risk90"):
            ci = boot.get(f"{metric}_ci", (float("nan"), float("nan")))
            delta_ci = boot.get(f"delta_{metric}_ci", (float("nan"), float("nan")))
            row[metric] = round(metrics[metric], 8)
            row[f"{metric}_ci_lo"] = round(ci[0], 8)
            row[f"{metric}_ci_hi"] = round(ci[1], 8)
            row[f"delta_{metric}"] = round(metrics[metric] - reference_metrics[metric], 8)
            row[f"delta_{metric}_ci_lo"] = round(delta_ci[0], 8)
            row[f"delta_{metric}_ci_hi"] = round(delta_ci[1], 8)
        rows.append(row)
    return rows


def native_endpoint_score_rows(source, data, delta_theta, replicates, workers):
    threshold = np.asarray([delta_theta(value) for value in data["aspect_ratio"]], dtype=float)
    severe = (data["angle_error"] > threshold).astype(float)
    base_mask = ((data["aspect_ratio"] >= AR_MAIN) & np.isfinite(threshold)
                 & np.isfinite(data["angle_error"]))
    reference = data["detection_score"]
    prefix = source["head"].lower()
    definitions = (
        (f"{prefix}_native", data["native_score"], source["manifest"]["native_signal"]),
        (f"{prefix}_detection_score", reference, "post-NMS detection score from the same frozen head"),
    )
    rows = []
    for score_name, values, formula in definitions:
        common = base_mask & np.isfinite(values) & np.isfinite(reference)
        if int(common.sum()) < 50:
            raise InvalidInput(
                f"{source['head']} {source['dataset']} seed{source['seed']}: fewer than 50 ar>=2.1 rows")
        candidate = values[common]
        ref = reference[common]
        risk = severe[common]
        images = data["image_id"][common]
        metrics = metric_bundle(candidate, risk)
        reference_metrics = metric_bundle(ref, risk)
        boot = cluster_bootstrap(
            candidate, ref, risk, images, replicates, workers,
            stable_seed(source["head"], source["dataset"], source["seed"], score_name))
        row = {
            "dataset": source["dataset"], "seed": source["seed"], "score": score_name,
            "score_family": "frozen_k2_native_phase1_endpoint", "formula": formula,
            "endpoint": "geometry_normalized_severe_event", "mask_definition": "aspect_ratio>=2.1",
            "risk_event": "angle_error>delta_theta_0.75(aspect_ratio)", "ar_threshold": AR_MAIN,
            "retained_count": int(common.sum()), "retained_ratio": round(float(common.mean()), 8),
            "n": int(common.sum()), "n_images": len(set(images)),
            "reference_score": f"{prefix}_detection_score", "bootstrap_unit": "image",
            "bootstrap_replicates": replicates,
            "comparison_status": "PAIRED_SAME_HEAD_DETECTION_BASELINE",
            "source_file": str(source["matched_path"].relative_to(ROOT)),
            "source_sha256": source["manifest"]["matched_sha256"],
        }
        for metric in ("nrc", "aurc", "risk70", "risk90"):
            ci = boot.get(f"{metric}_ci", (float("nan"), float("nan")))
            delta_ci = boot.get(f"delta_{metric}_ci", (float("nan"), float("nan")))
            row[metric] = round(metrics[metric], 8)
            row[f"{metric}_ci_lo"] = round(ci[0], 8)
            row[f"{metric}_ci_hi"] = round(ci[1], 8)
            row[f"delta_{metric}"] = round(metrics[metric] - reference_metrics[metric], 8)
            row[f"delta_{metric}_ci_lo"] = round(delta_ci[0], 8)
            row[f"delta_{metric}_ci_hi"] = round(delta_ci[1], 8)
        rows.append(row)
    return rows


def isotonic_r2(source, target, increasing):
    """Weighted pool-adjacent-violators R2, including tied-score grouping."""
    source = np.asarray(source, dtype=float)
    target = np.asarray(target, dtype=float)
    valid = np.isfinite(source) & np.isfinite(target)
    source, target = source[valid], target[valid]
    if len(source) < 3:
        return float("nan")
    _, inverse = np.unique(source, return_inverse=True)
    weights = np.bincount(inverse).astype(float)
    means = np.bincount(inverse, weights=target) / weights
    work = means if increasing else -means
    blocks = []
    for index, (value, weight) in enumerate(zip(work, weights)):
        blocks.append([index, index + 1, float(weight), float(value)])
        while len(blocks) >= 2 and blocks[-2][3] > blocks[-1][3]:
            right = blocks.pop()
            left = blocks.pop()
            total_weight = left[2] + right[2]
            level = (left[3] * left[2] + right[3] * right[2]) / total_weight
            blocks.append([left[0], right[1], total_weight, level])
    fitted_unique = np.empty(len(means), dtype=float)
    for start, end, _, level in blocks:
        fitted_unique[start:end] = level if increasing else -level
    prediction = fitted_unique[inverse]
    denominator = float(np.sum((target - target.mean()) ** 2))
    return (float("nan") if denominator <= 1e-12
            else 1.0 - float(np.sum((target - prediction) ** 2)) / denominator)


def nontriviality_rows(source, data, mask, score_rows):
    output = []
    arrays = score_arrays(data)
    reference = arrays["negative_phase_mod"]
    detection = arrays["detection_score"]
    score_lookup = {(row["dataset"], int(row["seed"]), row["score"]): row for row in score_rows
                    if row["score_family"] == "registered_psc_phase1"}
    for candidate_name in MECHANISM_CANDIDATES:
        candidate = arrays[candidate_name]
        valid = mask & np.isfinite(candidate) & np.isfinite(reference) & np.isfinite(detection)
        n = int(valid.sum())
        if n < 50:
            output.append({
                "dataset": source["dataset"], "seed": source["seed"], "candidate": candidate_name,
                "n": n, "formula": SCORE_FORMULAS[candidate_name], "spearman_vs_negative_phase_mod": "",
                "kendall_vs_negative_phase_mod": "", "rank_disagreement": "", "top10_overlap": "",
                "isotonic_r2_best_direction": "", "spearman_vs_detection_score": "", "unique_values": "",
                "depends_on_gt": "False", "inference_side": "True", "target_domain_fit": "False",
                "feature_ablation": "single registered raw mechanism signal; no fitted combination",
                "simple_monotone_transform": "", "nontrivial": "False", "beats_negative_phase_mod_nrc": "False",
                "beats_negative_phase_mod_all_metrics": "False", "paired_delta_nrc_ci_hi": "",
                "paired_delta_aurc_ci_hi": "", "paired_delta_risk70_ci_hi": "",
                "paired_delta_risk90_ci_hi": "", "status": "UNAVAILABLE",
            })
            continue
        cand = candidate[valid]
        ref = reference[valid]
        det = detection[valid]
        spearman = float(spearmanr(cand, ref).correlation)
        kendall = float(kendalltau(cand, ref).correlation)
        detection_spearman = float(spearmanr(cand, det).correlation)
        rank_c = np.argsort(np.argsort(cand, kind="stable"), kind="stable") / max(n - 1, 1)
        rank_r = np.argsort(np.argsort(ref, kind="stable"), kind="stable") / max(n - 1, 1)
        rank_disagreement = float(np.mean(np.abs(rank_c - rank_r)))
        top_n = max(1, int(math.ceil(0.1 * n)))
        top_c = set(np.argpartition(cand, -top_n)[-top_n:].tolist())
        top_r = set(np.argpartition(ref, -top_n)[-top_n:].tolist())
        overlap = len(top_c & top_r) / top_n
        iso = max(isotonic_r2(ref, cand, True), isotonic_r2(ref, cand, False))
        unique_values = int(np.unique(cand).size)
        simple = bool(abs(spearman) >= 0.95 or abs(detection_spearman) >= 0.95
                      or (math.isfinite(iso) and iso >= 0.95)
                      or overlap >= 0.90 or rank_disagreement <= 0.05 or unique_values < 20)
        metric_row = score_lookup.get((source["dataset"], source["seed"], candidate_name), {})
        ci_values = {
            metric: metric_row.get(f"delta_{metric}_ci_hi", float("nan"))
            for metric in ("nrc", "aurc", "risk70", "risk90")
        }
        beats_nrc = bool(isinstance(ci_values["nrc"], (int, float))
                         and math.isfinite(float(ci_values["nrc"]))
                         and float(ci_values["nrc"]) < 0)
        beats_all = all(isinstance(value, (int, float)) and math.isfinite(float(value))
                        and float(value) < 0 for value in ci_values.values())
        output.append({
            "dataset": source["dataset"], "seed": source["seed"], "candidate": candidate_name,
            "n": n, "formula": SCORE_FORMULAS[candidate_name],
            "spearman_vs_negative_phase_mod": round(spearman, 8),
            "kendall_vs_negative_phase_mod": round(kendall, 8),
            "rank_disagreement": round(rank_disagreement, 8), "top10_overlap": round(overlap, 8),
            "isotonic_r2_best_direction": round(iso, 8),
            "spearman_vs_detection_score": round(detection_spearman, 8),
            "unique_values": unique_values, "depends_on_gt": "False", "inference_side": "True",
            "target_domain_fit": "False",
            "feature_ablation": "single registered raw mechanism signal; no fitted combination",
            "simple_monotone_transform": str(simple), "nontrivial": str(not simple),
            "beats_negative_phase_mod_nrc": str(beats_nrc),
            "beats_negative_phase_mod_all_metrics": str(beats_all),
            "paired_delta_nrc_ci_hi": ci_values["nrc"],
            "paired_delta_aurc_ci_hi": ci_values["aurc"],
            "paired_delta_risk70_ci_hi": ci_values["risk70"],
            "paired_delta_risk90_ci_hi": ci_values["risk90"],
            "status": "COMPLETE",
        })
    return output


def verify_ranking_only_condition(sources, score_rows, nontriviality, winning):
    """Derive split-gate condition 4 for the proposed reliability scores.

    The preregistered condition applies to the new score, not to the radial
    intervention used to identify the mechanism.  A qualifying score must be a
    post-hoc, inference-side ranking over SHA-bound frozen predictions.  It may
    not train a detector, fit target-domain GT, or alter boxes/classes/AP.
    """
    failures = []
    source_by_key = {(source["dataset"], source["seed"]): source for source in sources}
    for source in sources:
        dataset, seed = source["dataset"], source["seed"]
        manifest = source["manifest"]
        if manifest.get("no_training") is not True:
            failures.append(f"{dataset}/seed{seed}:no_training_false")
    for row in nontriviality:
        if row["candidate"] not in winning:
            continue
        identity = (row["dataset"], int(row["seed"]))
        if identity not in source_by_key:
            failures.append(f"{identity[0]}/seed{identity[1]}:{row['candidate']}:unknown_source")
        if not (
            row["depends_on_gt"] == "False"
            and row["inference_side"] == "True"
            and row["target_domain_fit"] == "False"
        ):
            failures.append(f"{identity[0]}/seed{identity[1]}:{row['candidate']}:not_ranking_only")
    for row in score_rows:
        if row["score"] not in winning:
            continue
        identity = (row["dataset"], int(row["seed"]))
        source = source_by_key.get(identity)
        if source is None:
            continue
        if (
            row["source_file"] != str(source["matched_path"].relative_to(ROOT))
            or row["source_sha256"] != sha256(source["matched_path"])
        ):
            failures.append(f"{identity[0]}/seed{identity[1]}:{row['score']}:source_identity_changed")
    return not failures, failures


def split_gate(branch_rows, score_rows, nontriviality, sources):
    overall_branch = next(row for row in branch_rows if row["scope"] == "overall")
    condition1 = overall_branch["structural_cause_intervention_verified"] == "True"
    candidate_evidence = {}
    for candidate in MECHANISM_CANDIDATES:
        expected = ({(dataset, 0) for dataset in DATASETS}
                    if candidate == "tta_phase_direction_consistency"
                    else {(dataset, seed) for dataset in DATASETS for seed in SEEDS})
        nt = [row for row in nontriviality
              if row["candidate"] == candidate and (row["dataset"], int(row["seed"])) in expected]
        metrics = [row for row in score_rows
                   if row["score_family"] == "registered_psc_phase1" and row["score"] == candidate
                   and (row["dataset"], int(row["seed"])) in expected]
        observed_nt = {(row["dataset"], int(row["seed"])) for row in nt}
        observed_metrics = {(row["dataset"], int(row["seed"])) for row in metrics}
        complete_required = (observed_nt == expected and observed_metrics == expected
                             and all(row["status"] == "COMPLETE" for row in nt))
        nontrivial_all = complete_required and all(row["nontrivial"] == "True" for row in nt)
        beats_all = complete_required and all(
            row["comparison_status"] == "PAIRED_COMPARABLE"
            and all(float(row[f"delta_{metric}_ci_hi"]) < 0
                    for metric in ("nrc", "aurc", "risk70", "risk90"))
            for row in metrics
        )
        candidate_evidence[candidate] = {
            "required_cells": sorted(f"{dataset}/seed{seed}" for dataset, seed in expected),
            "complete_required_cells": complete_required,
            "nontrivial_all": nontrivial_all,
            "beats_negative_phase_mod_all": beats_all,
        }
    winning = [name for name, evidence in candidate_evidence.items()
               if evidence["nontrivial_all"] and evidence["beats_negative_phase_mod_all"]]
    condition2 = any(evidence["nontrivial_all"] for evidence in candidate_evidence.values())
    condition3 = bool(winning)
    condition4, condition4_failures = verify_ranking_only_condition(
        sources, score_rows, nontriviality, winning
    )
    decision = "PASS" if condition1 and condition2 and condition3 and condition4 else "FAIL"
    return [{
        "decision": decision,
        "start": START,
        "deadline": DEADLINE,
        "branch": overall_branch["branch"],
        "structural_cause": overall_branch["structural_cause"],
        "cond1_intervenable_structural_cause": str(condition1),
        "cond2_nontrivial_registered_score": str(condition2),
        "cond3_beats_negative_phase_mod_two_datasets_frozen_cells": str(condition3),
        "cond4_no_retrain_box_class_ap_unchanged": str(condition4),
        "cond4_evidence": (
            "six SHA-bound no-training manifests; winning scores are post-hoc "
            "inference-side rankings over unchanged source prediction identities; "
            "no target-domain GT fit and no box/class/AP modification"
        ),
        "cond4_failures": ";".join(condition4_failures),
        "winning_candidate": ";".join(winning),
        "candidate_evidence_json": json.dumps(candidate_evidence, sort_keys=True),
        "interpretation": "PASS only if all four frozen conditions hold; condition 3 requires all four metrics' paired image-bootstrap upper bounds below zero in every frozen available cell (TTA seed0 only; other candidates all seeds).",
    }]


def make_docs(branch_rows, gate_rows, score_rows):
    overall = next(row for row in branch_rows if row["scope"] == "overall")
    radial_doc = "\n".join([
        "# PSC Phase 1：相位向量径向缩放干预",
        "",
        f"- 原始开始时间：`{START}`；原始截止时间：`{DEADLINE}`，未重置。",
        f"- 预注册 SHA-256：`{PREREG_SHA256}`。",
        f"- 六个 K2 final PSC seed 单元均通过 manifest、config、checkpoint、输出 SHA 和正常结束日志校验。",
        "- actual-head loss/gradient 列来自只补该缺口的 network-coordinate supplement；原 forward 中 evaluator-coordinate anchor-assignment 列已 superseded，AP/NMS/matching/radial decode 未重跑。",
        f"- 冻结分支裁决：**{overall['branch']}**。",
        f"- 六单元一致的可干预结构性解释：`{overall['structural_cause']}`；verified={overall['structural_cause_intervention_verified']}。",
        f"- 六单元最大 decoded median/p95 差：{overall['decoded_median_max_deg']}° / {overall['decoded_p95_max_deg']}°。",
        f"- 六单元最大 loss 相对变化：{overall['loss_relative_change_max']}。",
        "- Branch A 仅在全部 k、两个数据集、三个 seed 同时满足 median<0.5°、p95<1.0°、configured anchor-assigned head loss relative change<1e-3 时成立。",
        "- Branch B 不自动判定结构原因成立；仅当六单元均为 B 且 decoder radial sensitivity 或 configured-loss magnitude semantics 在六单元一致复现时，条件1才通过。异质响应按未验证处理。",
        "- loss gate 使用实际配置的 anchor-assigned PSC angle loss；controlled matched L1 与 post-NMS matched L1 仅作诊断。",
        "- AP50/AP75、角误差、实际 head 径向/切向梯度、box/class/NMS 集合诊断见 `psc_phase1_radial_scaling.csv`；聚合脚本未训练或重新推理。",
        "",
    ])
    gate = gate_rows[0]
    comparable = [row for row in score_rows if row["score_family"] == "registered_psc_phase1"]
    gate_doc = "\n".join([
        "# PSC Phase 1 拆篇门控报告",
        "",
        f"- 时间冻结：`{START}` 至 `{DEADLINE}`。",
        f"- radial branch：**{gate['branch']}**。",
        f"- 条件1 可干预结构性原因：{gate['cond1_intervenable_structural_cause']}（`{gate['structural_cause']}`）。",
        f"- 条件2 非平凡预注册新分数：{gate['cond2_nontrivial_registered_score']}。",
        f"- 条件3 两数据集冻结可用单元稳定优于 negative phase_mod：{gate['cond3_beats_negative_phase_mod_two_datasets_frozen_cells']}。",
        f"- 条件4 不重训且 box/class/AP 不变：{gate['cond4_no_retrain_box_class_ap_unchanged']}。",
        f"- **拆篇裁决：{gate['decision']}**。",
        "",
        "所有正式比较（含冻结 K2 DCL/CSL native endpoint）使用 `ar>=2.1` 与 `angle_error > delta_theta_0.75(aspect_ratio)`；NRC/AURC/Risk@70/Risk@90 的区间按图像簇 bootstrap。DCL/CSL 与自身 detection score 配对，但不代替 PSC 新机制分数相对 negative phase_mod 的拆篇条件。",
        f"本次可配对 PSC score rows：{sum(row['comparison_status'] == 'PAIRED_COMPARABLE' for row in comparable)}。",
        "若 FAIL：不拆篇；有效机制证据并回主论文机制小节，停止 B 线继续搜索。",
        "",
    ])
    return radial_doc, gate_doc


def artifact_manifest_rows(sources, native_sources):
    rows = []
    roles = {
        "radial": "six-seed radial intervention",
        "branch": "frozen radial branch decision",
        "dissection": "twelve preregistered analyses",
        "scores": "ar>=2.1 geometry-event score comparison",
        "nontriviality": "registered candidate nontriviality audit",
        "gate": "four-condition split gate",
        "radial_doc": "radial intervention report",
        "gate_doc": "split gate report",
    }
    for name, path in OUTPUTS.items():
        if name == "manifest":
            continue
        rows.append({
            "artifact": str(path.relative_to(ROOT)), "role": roles[name], "status": "complete",
            "sha256": sha256(path), "bytes": path.stat().st_size, "source": "six frozen K2 PSC Phase1 forward manifests",
            "can_recompute": "yes: python scripts/psc_phase1.py",
        })
    rows.append({
        "artifact": str(PREREG.relative_to(ROOT)), "role": "frozen preregistration", "status": "frozen",
        "sha256": sha256(PREREG), "bytes": PREREG.stat().st_size, "source": "historical start anchor",
        "can_recompute": "no; immutable registration",
    })
    for path, role in (
        (K2_ARTIFACT_MANIFEST, "frozen K2 artifact index"),
        (DELTA_THETA_JSON, "frozen geometry-normalized risk threshold"),
        (Path(__file__).resolve(), "PSC Phase1 aggregation script"),
        (ROOT / "scripts/m069_psc_phase1_forward.py", "PSC radial forward source"),
        (ROOT / "scripts/m069_psc_actual_loss_supplement.py", "network-coordinate actual-head supplement source"),
        (ROOT / "scripts/m069_psc_native_signal_dump.py", "DCL/CSL native endpoint source"),
        (REPO / "orientbench_ext/instrumented_heads.py", "post-NMS encoded-angle instrumentation source"),
    ):
        rows.append({
            "artifact": str(path.relative_to(ROOT)), "role": role, "status": "validated_input",
            "sha256": sha256(path), "bytes": path.stat().st_size, "source": "frozen protocol chain",
            "can_recompute": "source code" if path.suffix == ".py" else "no",
        })
    for head in ("DCL", "CSL"):
        for dataset in DATASETS:
            for seed in SEEDS:
                path = K2_EVAL / f"K2_final__{head}__{dataset}__seed{seed}.json"
                rows.append({
                    "artifact": str(path.relative_to(ROOT)), "role": f"frozen {head} native-signal reference",
                    "status": "validated_input", "sha256": sha256(path), "bytes": path.stat().st_size,
                    "source": f"{dataset} seed{seed}", "can_recompute": "frozen K2 evaluator only",
                })
    for source in sources:
        for path, role in ((source["manifest_path"], "forward manifest"),
                           (source["summary_path"], "radial evaluator source"),
                           (source["matched_path"], "matched phase source"),
                           (source["checkpoint_path"], "frozen K2 checkpoint"),
                           (source["actual_supplement_manifest_path"],
                            "network-coordinate actual-head supplement manifest"),
                           (source["actual_supplement_summary_path"],
                            "network-coordinate actual-head supplement summary"),
                           (source["actual_supplement_log_path"],
                            "network-coordinate actual-head supplement completion log")):
            rows.append({
                "artifact": str(path.relative_to(ROOT)), "role": role, "status": "validated_input",
                "sha256": sha256(path), "bytes": path.stat().st_size,
                "source": f"{source['dataset']} seed{source['seed']}",
                "can_recompute": (
                    "targeted actual-head supplement only"
                    if "supplement" in role else "forward preregistration only"),
            })
    for source in native_sources:
        for path, role in (
                (source["manifest_path"], "frozen K2 native Phase1 endpoint manifest"),
                (source["matched_path"], "frozen K2 native Phase1 matched endpoint"),
                (source["completion_log"], "frozen K2 native Phase1 completion log")):
            rows.append({
                "artifact": str(path.relative_to(ROOT)), "role": role, "status": "validated_input",
                "sha256": sha256(path), "bytes": path.stat().st_size,
                "source": f"{source['head']} {source['dataset']} seed{source['seed']}",
                "can_recompute": "targeted identity-only native endpoint extraction",
            })
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--bootstrap-replicates", type=int, default=BOOTSTRAP_REPLICATES)
    parser.add_argument("--workers", type=int, default=MIN_CPU_WORKERS)
    args = parser.parse_args(argv)
    if args.bootstrap_replicates < 100:
        raise SystemExit("bootstrap-replicates must be >=100")
    if not MIN_CPU_WORKERS <= args.workers <= CPU_BUDGET:
        raise SystemExit(f"workers must be in [{MIN_CPU_WORKERS},{CPU_BUDGET}] for the frozen 48-core budget")
    validate_preregistration()
    try:
        validate_risk_event()
        sources = validate_forward_inputs()
        native_sources = validate_native_endpoint_inputs()
    except PendingInputs as exc:
        print(f"PSC_PHASE1_PENDING\n{exc}", file=sys.stderr)
        return 3

    log(f"PSC Phase1 FINAL AGGREGATION START prereg_sha={PREREG_SHA256} start={START} deadline={DEADLINE}")
    radial_rows, branch_rows = radial_analysis(sources)
    dissection = []
    scores = []
    nontriviality = []
    delta_theta = load_interpolator(str(DELTA_THETA_JSON))
    for source in sources:
        data = load_matched(source)
        threshold = np.asarray([delta_theta(value) for value in data["aspect_ratio"]], dtype=float)
        severe = (data["angle_error"] > threshold).astype(float)
        mask = ((data["aspect_ratio"] >= AR_MAIN) & np.isfinite(data["angle_error"])
                & np.isfinite(threshold))
        if mask.sum() < 50:
            raise InvalidInput(f"{source['dataset']} seed{source['seed']}: fewer than 50 ar>=2.1 rows")
        dissection.extend(dissection_rows(source, data, severe, threshold, mask))
        cell_scores = score_comparison_rows(source, data, severe, mask, args.bootstrap_replicates, args.workers)
        scores.extend(cell_scores)
        nontriviality.extend(nontriviality_rows(source, data, mask, cell_scores))
    for source in native_sources:
        data = load_native_endpoint(source)
        scores.extend(native_endpoint_score_rows(
            source, data, delta_theta, args.bootstrap_replicates, args.workers))
    gate_rows = split_gate(branch_rows, scores, nontriviality, sources)
    radial_doc, gate_doc = make_docs(branch_rows, gate_rows, scores)

    atomic_csv(OUTPUTS["radial"], radial_rows)
    atomic_csv(OUTPUTS["branch"], branch_rows)
    atomic_csv(OUTPUTS["dissection"], dissection)
    atomic_csv(OUTPUTS["scores"], scores)
    atomic_csv(OUTPUTS["nontriviality"], nontriviality)
    atomic_csv(OUTPUTS["gate"], gate_rows)
    atomic_text(OUTPUTS["radial_doc"], radial_doc)
    atomic_text(OUTPUTS["gate_doc"], gate_doc)
    atomic_csv(OUTPUTS["manifest"], artifact_manifest_rows(sources, native_sources))
    log(f"PSC Phase1 FINAL AGGREGATION DONE branch={gate_rows[0]['branch']} decision={gate_rows[0]['decision']}")
    print(f"PSC_PHASE1_DONE branch={gate_rows[0]['branch']} decision={gate_rows[0]['decision']}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except InvalidInput as exc:
        print(f"PSC_PHASE1_INVALID: {exc}", file=sys.stderr)
        sys.exit(2)
