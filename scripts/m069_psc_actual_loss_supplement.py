#!/usr/bin/env python3
"""Targeted PSC Phase-1 actual-head loss supplement.

This fills only the configured anchor-assigned ``L(kz)`` statistics.  It does
one frozen head forward per validation image and deliberately does not decode,
match, run NMS, evaluate AP, or repeat any other Phase-1 measurement.  Packed
validation GT is rescaled from evaluator/original coordinates to network-input
coordinates before the frozen training assigner is invoked.
"""
from __future__ import annotations

import argparse
import csv
import fcntl
import json
import math
import os
import time
from pathlib import Path

import numpy as np
import torch
from mmengine.config import Config
from mmengine.runner import load_checkpoint
from mmrotate.registry import DATASETS, MODELS

from m069_psc_phase1_forward import (
    EXPECTED_GT,
    EXPECTED_IMAGES,
    GT_PATHS,
    K2_ARTIFACT_MANIFEST,
    K_GRID,
    ROOT,
    actual_angle_loss_gradient,
    forward_once,
    paths,
    prefetched_items,
    prepare_angle_loss_context,
    sha256,
    verify_k2_checkpoint,
)

REPO = ROOT / "top_journal_v3_reaudit_055"
LOG_ROOT = REPO / "logs/m069/psc_phase1_actual_loss"
SCHEMA = "psc_phase1_actual_head_loss_network_space_v1"
CSV_NAME = "actual_head_loss_network_space.csv"
MANIFEST_NAME = "actual_head_loss_network_space_manifest.json"
ACTUAL_FIELDS = (
    "actual_head_mean_angle_loss",
    "actual_head_mean_abs_radial_gradient",
    "actual_head_mean_tangential_gradient_norm",
    "actual_head_mean_abs_radial_gradient_wrt_base_z",
    "actual_head_mean_tangential_gradient_norm_wrt_base_z",
    "actual_head_mean_abs_dloss_dk",
    "actual_head_mean_positive_anchors",
)


def log(dataset: str, seed: int, message: str) -> None:
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    line = f"[{time.strftime('%F %T')}] {dataset} seed={seed} {message}\n"
    with (LOG_ROOT / f"{dataset}_seed{seed}.log").open("a", encoding="utf-8") as handle:
        handle.write(line)
    print(line.rstrip(), flush=True)


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None


def atomic_json(path: Path, payload: dict) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def atomic_csv(path: Path, rows: list[dict]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def validate_csv(path: Path, dataset: str, seed: int) -> bool:
    try:
        rows = list(csv.DictReader(path.open(newline="", encoding="utf-8")))
        if len(rows) != len(K_GRID):
            return False
        if not np.allclose([float(row["k"]) for row in rows], K_GRID, rtol=0, atol=1e-12):
            return False
        for row in rows:
            if row["dataset"] != dataset or int(row["seed"]) != seed:
                return False
            if int(row["n_images"]) != EXPECTED_IMAGES[dataset] or int(row["n_gt"]) != EXPECTED_GT[dataset]:
                return False
            values = [float(row[field]) for field in ACTUAL_FIELDS]
            if not all(math.isfinite(value) and value >= 0 for value in values):
                return False
            if float(row["actual_head_mean_positive_anchors"]) <= 0:
                return False
        return True
    except (OSError, KeyError, TypeError, ValueError):
        return False


def verified_existing(
        manifest_path: Path, csv_path: Path, dataset: str, seed: int,
        run_id: str, checkpoint_sha: str, k2_eval_path: Path, cfg_path: Path) -> bool:
    manifest = load_json(manifest_path)
    if not manifest or not csv_path.is_file() or not validate_csv(csv_path, dataset, seed):
        return False
    return (
        manifest.get("status") == "complete"
        and manifest.get("schema_version") == SCHEMA
        and manifest.get("run_id") == run_id
        and manifest.get("dataset") == dataset
        and int(manifest.get("seed", -1)) == seed
        and manifest.get("k_grid") == K_GRID
        and int(manifest.get("n_images", -1)) == EXPECTED_IMAGES[dataset]
        and int(manifest.get("n_gt", -1)) == EXPECTED_GT[dataset]
        and manifest.get("gt_coordinate_space") == "network_input_after_validation_scale_factor"
        and manifest.get("checkpoint_sha256") == checkpoint_sha
        and manifest.get("config_sha256") == sha256(cfg_path)
        and manifest.get("k2_artifact_manifest_sha256") == sha256(K2_ARTIFACT_MANIFEST)
        and manifest.get("k2_eval_sha256") == sha256(k2_eval_path)
        and manifest.get("gt_sha256") == sha256(GT_PATHS[dataset])
        and manifest.get("summary_sha256") == sha256(csv_path)
        and int(manifest.get("summary_bytes", -1)) == csv_path.stat().st_size
        and manifest.get("no_training") is True
        and manifest.get("only_actual_head_loss_statistics") is True
        and "/dev/shm" not in json.dumps(manifest)
    )


def run(dataset: str, seed: int, prefetch_workers: int = 10) -> None:
    cfg_path, checkpoint, out_dir = paths(dataset, seed)
    run_id, _, checkpoint_sha, k2_eval_path = verify_k2_checkpoint(dataset, seed, checkpoint)
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / CSV_NAME
    manifest_path = out_dir / MANIFEST_NAME
    if verified_existing(
            manifest_path, summary_path, dataset, seed, run_id,
            checkpoint_sha, k2_eval_path, cfg_path):
        log(dataset, seed, "verified existing actual-loss supplement; no forward repeated")
        return

    lock_handle = (out_dir / ".actual_loss_supplement.lock").open("a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise RuntimeError(f"{run_id}: another actual-loss supplement holds the lock") from exc

    cfg = Config.fromfile(str(cfg_path))
    model = MODELS.build(cfg.model)
    load_checkpoint(model, str(checkpoint), map_location="cpu")
    model.eval().cuda()
    loss_module = model.bbox_head.loss_angle
    if (type(loss_module).__name__ != "L1Loss" or loss_module.reduction != "mean"
            or not math.isclose(float(loss_module.loss_weight), 0.2, rel_tol=0, abs_tol=1e-12)):
        raise RuntimeError(
            f"{run_id}: frozen PSC loss drifted from preregistered L1(mean, weight=0.2)")
    data = DATASETS.build(cfg.val_dataloader["dataset"])
    if len(data) != EXPECTED_IMAGES[dataset]:
        raise RuntimeError(f"{run_id}: expected {EXPECTED_IMAGES[dataset]} images, got {len(data)}")

    totals = {k: {field: 0.0 for field in ACTUAL_FIELDS} for k in K_GRID}
    seen_image_ids: set[str] = set()
    n_gt = 0
    started = time.time()
    with torch.no_grad():
        for index, (item, _, _) in prefetched_items(data, None, None, prefetch_workers):
            image_id = str(item["data_samples"].img_id)
            if image_id in seen_image_ids:
                raise RuntimeError(f"{run_id}: duplicate image ID {image_id}")
            seen_image_ids.add(image_id)
            n_gt += len(item["data_samples"].gt_instances)
            outs, samples, _ = forward_once(model, item)
            context = prepare_angle_loss_context(model.bbox_head, outs, samples)
            for k in K_GRID:
                loss, radial, tangential, dloss_dk, positives = actual_angle_loss_gradient(
                    model.bbox_head, outs[2], context, k)
                values = {
                    "actual_head_mean_angle_loss": loss,
                    "actual_head_mean_abs_radial_gradient": radial,
                    "actual_head_mean_tangential_gradient_norm": tangential,
                    "actual_head_mean_abs_radial_gradient_wrt_base_z": k * radial,
                    "actual_head_mean_tangential_gradient_norm_wrt_base_z": k * tangential,
                    "actual_head_mean_abs_dloss_dk": dloss_dk,
                    "actual_head_mean_positive_anchors": positives,
                }
                if not all(math.isfinite(float(value)) and float(value) >= 0 for value in values.values()):
                    raise RuntimeError(f"{run_id}/{image_id}/k={k}: nonfinite actual-loss statistic")
                for field, value in values.items():
                    totals[k][field] += float(value)
            if (index + 1) % 1000 == 0:
                log(dataset, seed, f"progress {index + 1}/{len(data)} minutes={(time.time() - started) / 60:.1f}")

    if len(seen_image_ids) != EXPECTED_IMAGES[dataset] or n_gt != EXPECTED_GT[dataset]:
        raise RuntimeError(
            f"{run_id}: full-validation cardinality mismatch images={len(seen_image_ids)} gt={n_gt}")
    rows = []
    for k in K_GRID:
        row = {
            "dataset": dataset,
            "seed": seed,
            "k": k,
            "n_images": len(data),
            "n_gt": n_gt,
        }
        row.update({field: round(totals[k][field] / len(data), 10) for field in ACTUAL_FIELDS})
        rows.append(row)
    atomic_csv(summary_path, rows)
    if not validate_csv(summary_path, dataset, seed):
        raise RuntimeError(f"{run_id}: written actual-loss supplement failed schema validation")
    manifest = {
        "status": "complete",
        "schema_version": SCHEMA,
        "run_id": run_id,
        "dataset": dataset,
        "seed": seed,
        "k_grid": K_GRID,
        "n_images": len(data),
        "n_gt": n_gt,
        "summary_path": str(summary_path.relative_to(ROOT)),
        "summary_sha256": sha256(summary_path),
        "summary_bytes": summary_path.stat().st_size,
        "config_path": str(cfg_path),
        "config_sha256": sha256(cfg_path),
        "checkpoint_path": str(checkpoint),
        "checkpoint_sha256": checkpoint_sha,
        "k2_artifact_manifest_path": str(K2_ARTIFACT_MANIFEST.relative_to(ROOT)),
        "k2_artifact_manifest_sha256": sha256(K2_ARTIFACT_MANIFEST),
        "k2_eval_path": str(k2_eval_path.relative_to(ROOT)),
        "k2_eval_sha256": sha256(k2_eval_path),
        "gt_path": str(GT_PATHS[dataset].relative_to(ROOT)),
        "gt_sha256": sha256(GT_PATHS[dataset]),
        "gt_coordinate_space": "network_input_after_validation_scale_factor",
        "assignment": "frozen configured MaxIoU anchor assignment",
        "loss": "configured L1(mean, loss_weight=0.2) bbox_head.loss_angle on positive/weighted anchors",
        "only_actual_head_loss_statistics": True,
        "no_decode": True,
        "no_matching": True,
        "no_nms": True,
        "no_ap_evaluation": True,
        "no_training": True,
        "generation_command": (
            f"CUDA_VISIBLE_DEVICES=<gpu> python scripts/m069_psc_actual_loss_supplement.py "
            f"{dataset} {seed}"),
        "completed_at": time.strftime("%F %T %z"),
        "elapsed_seconds": round(time.time() - started, 3),
    }
    atomic_json(manifest_path, manifest)
    log(dataset, seed, f"DONE images={len(data)} gt={n_gt} summary_sha={manifest['summary_sha256']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", choices=["DIOR-R", "SODA-A"])
    parser.add_argument("seed", type=int, choices=[0, 1, 2])
    parser.add_argument("--prefetch-workers", type=int, default=10)
    args = parser.parse_args()
    if args.prefetch_workers < 0:
        parser.error("--prefetch-workers must be nonnegative")
    run(args.dataset, args.seed, args.prefetch_workers)


if __name__ == "__main__":
    main()
