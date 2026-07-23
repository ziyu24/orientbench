#!/usr/bin/env python3
"""Extract missing Phase-1 DCL/CSL native signals from frozen K2 heads.

This is an identity-only endpoint extraction, not a K2 rerun: it performs one
frozen forward, post-NMS own-detector TP matching, and writes only the rows
needed for the preregistered geometry-risk ranking comparison.  It does not
train, evaluate AP, run TTA, or alter any detector output.
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

import torch
from mmengine.config import Config
from mmengine.runner import load_checkpoint
from mmrotate.registry import DATASETS, MODELS

from m069_psc_phase1_forward import (
    EXPECTED_GT,
    EXPECTED_IMAGES,
    GT_PATHS,
    K2_ARTIFACT_MANIFEST,
    ROOT,
    match,
    prefetched_items,
    preprocess,
    sha256,
)
from orientbench.metrics.angle_contract import angle_error_contract

REPO = ROOT / "top_journal_v3_reaudit_055"
OUT_ROOT = ROOT / "outputs/persistent_artifacts/m069_psc_phase1/native_signals"
LOG_ROOT = REPO / "logs/m069/psc_phase1_native_signals"
SCHEMA = "psc_phase1_frozen_k2_native_endpoint_v1"
HEADS = ("DCL", "CSL")
DATASETS_SUPPORTED = ("DIOR-R", "SODA-A")


def log(head: str, dataset: str, seed: int, message: str) -> None:
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    line = f"[{time.strftime('%F %T')}] {head} {dataset} seed={seed} {message}\n"
    path = LOG_ROOT / f"{head}_{dataset}_seed{seed}.log"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
    print(line.rstrip(), flush=True)


def paths(head: str, dataset: str, seed: int):
    slug = "dior" if dataset == "DIOR-R" else "soda"
    work = REPO / f"work_dirs/k2/K2_final__{head}__{dataset}__seed{seed}"
    cfg = work / f"{head.lower()}_{slug}_seed0.py"
    checkpoint = work / "epoch_12.pth"
    out_dir = OUT_ROOT / head / dataset / f"seed{seed}"
    return cfg, checkpoint, out_dir


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


def verify_k2(head: str, dataset: str, seed: int, checkpoint: Path):
    run_id = f"K2_final__{head}__{dataset}__seed{seed}"
    with K2_ARTIFACT_MANIFEST.open(newline="", encoding="utf-8") as handle:
        rows = {row["run_id"]: row for row in csv.DictReader(handle)}
    if run_id not in rows:
        raise RuntimeError(f"frozen K2 index lacks {run_id}")
    row = rows[run_id]
    if Path(row["checkpoint"]).resolve() != checkpoint.resolve():
        raise RuntimeError(f"{run_id}: checkpoint path drift")
    checkpoint_sha = sha256(checkpoint)
    if not checkpoint_sha.startswith(row["ckpt_sha"]):
        raise RuntimeError(f"{run_id}: checkpoint SHA drift")
    if str(row.get("can_recompute", "")).strip().lower() not in {"yes", "true", "1"}:
        raise RuntimeError(f"{run_id}: frozen artifact not marked recomputable")
    eval_path = Path(row["eval_json"])
    train_log = Path(row["log"])
    if (not eval_path.is_file() or not sha256(eval_path).startswith(row["eval_sha"])
            or not train_log.is_file() or not sha256(train_log).startswith(row["log_sha"])):
        raise RuntimeError(f"{run_id}: frozen evaluator/training-log SHA drift")
    evaluator = load_json(eval_path)
    if (not evaluator or evaluator.get("run_id") != run_id or evaluator.get("head") != head
            or evaluator.get("dataset") != dataset or int(evaluator.get("n_matched", 0)) <= 0):
        raise RuntimeError(f"{run_id}: frozen evaluator identity/cardinality drift")
    return run_id, row, checkpoint_sha, eval_path, evaluator


def native_score(head: str, encoded: torch.Tensor) -> torch.Tensor:
    if head == "CSL":
        probabilities = encoded.float().softmax(dim=-1)
        top2 = probabilities.topk(2, dim=-1).values
        return top2[:, 0] - top2[:, 1]
    probabilities = encoded.float().sigmoid()
    return (2.0 * probabilities - 1.0).abs().mean(dim=-1)


def verified_existing(
        manifest_path: Path, matched_path: Path, head: str, dataset: str, seed: int,
        run_id: str, cfg_path: Path, checkpoint: Path, checkpoint_sha: str,
        eval_path: Path, expected_matched: int) -> bool:
    manifest = load_json(manifest_path)
    if not manifest or not matched_path.is_file():
        return False
    return (
        manifest.get("status") == "complete"
        and manifest.get("schema_version") == SCHEMA
        and manifest.get("run_id") == run_id
        and manifest.get("head") == head
        and manifest.get("dataset") == dataset
        and int(manifest.get("seed", -1)) == seed
        and int(manifest.get("n_images", -1)) == EXPECTED_IMAGES[dataset]
        and int(manifest.get("n_gt", -1)) == EXPECTED_GT[dataset]
        and int(manifest.get("n_matched", -1)) == expected_matched
        and manifest.get("config_sha256") == sha256(cfg_path)
        and manifest.get("checkpoint_sha256") == checkpoint_sha
        and Path(manifest.get("checkpoint_path", "")).resolve() == checkpoint.resolve()
        and manifest.get("k2_artifact_manifest_sha256") == sha256(K2_ARTIFACT_MANIFEST)
        and manifest.get("k2_eval_sha256") == sha256(eval_path)
        and manifest.get("gt_sha256") == sha256(GT_PATHS[dataset])
        and manifest.get("matched_sha256") == sha256(matched_path)
        and int(manifest.get("matched_bytes", -1)) == matched_path.stat().st_size
        and manifest.get("identity_only") is True
        and manifest.get("no_ap_evaluation") is True
        and manifest.get("no_training") is True
        and "/dev/shm" not in json.dumps(manifest)
    )


def run(head: str, dataset: str, seed: int, prefetch_workers: int = 10) -> None:
    cfg_path, checkpoint, out_dir = paths(head, dataset, seed)
    run_id, _, checkpoint_sha, eval_path, evaluator = verify_k2(
        head, dataset, seed, checkpoint)
    expected_matched = int(evaluator["n_matched"])
    out_dir.mkdir(parents=True, exist_ok=True)
    matched_path = out_dir / "matched_native.jsonl"
    manifest_path = out_dir / "manifest.json"
    if verified_existing(
            manifest_path, matched_path, head, dataset, seed, run_id, cfg_path,
            checkpoint, checkpoint_sha, eval_path, expected_matched):
        log(head, dataset, seed, "verified existing native endpoint; no forward repeated")
        return

    lock_handle = (out_dir / ".generation.lock").open("a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise RuntimeError(f"{run_id}: another native endpoint generator holds the lock") from exc

    cfg = Config.fromfile(str(cfg_path))
    cfg.model.bbox_head.type = "InstrumentedAngleBranchRetinaHead"
    model = MODELS.build(cfg.model)
    load_checkpoint(model, str(checkpoint), map_location="cpu")
    model.eval().cuda()
    data = DATASETS.build(cfg.val_dataloader["dataset"])
    if len(data) != EXPECTED_IMAGES[dataset]:
        raise RuntimeError(f"{run_id}: expected {EXPECTED_IMAGES[dataset]} images, got {len(data)}")
    classes = list(cfg.val_dataloader["dataset"]["metainfo"]["classes"])

    temporary = matched_path.with_suffix(".jsonl.tmp")
    if temporary.exists():
        temporary.unlink()
    seen_image_ids: set[str] = set()
    n_gt = n_predictions = n_matched = 0
    started = time.time()
    with temporary.open("w", encoding="utf-8") as output, torch.no_grad():
        for index, (item, _, _) in prefetched_items(data, None, None, prefetch_workers):
            image_id = str(item["data_samples"].img_id)
            if image_id in seen_image_ids:
                raise RuntimeError(f"{run_id}: duplicate image ID {image_id}")
            seen_image_ids.add(image_id)
            gt_instances = item["data_samples"].gt_instances
            gt_boxes = (gt_instances.bboxes.tensor if hasattr(gt_instances.bboxes, "tensor")
                        else gt_instances.bboxes).detach().cpu().float()
            gt_labels = gt_instances.labels.detach().cpu().long()
            n_gt += len(gt_boxes)

            processed = preprocess(model, item)
            prediction = model.predict(
                processed["inputs"], processed["data_samples"])[0].pred_instances
            boxes = (prediction.bboxes.tensor if hasattr(prediction.bboxes, "tensor")
                     else prediction.bboxes).detach().cpu().float()
            scores = prediction.scores.detach().cpu().float()
            labels = prediction.labels.detach().cpu().long()
            encoded = prediction.angle_encoded.detach().cpu().float()
            native = native_score(head, encoded)
            if len(native) != len(boxes) or not bool(torch.isfinite(native).all()):
                raise RuntimeError(f"{run_id}/{image_id}: invalid native-score alignment")
            n_predictions += len(boxes)
            for pred_index, gt_index, match_iou in match(
                    boxes, scores, labels, gt_boxes, gt_labels):
                pred = boxes[pred_index]
                target = gt_boxes[gt_index]
                contract = angle_error_contract(
                    *[float(value) for value in pred[2:5]],
                    *[float(value) for value in target[2:5]])
                angle_error = float(contract["angle_error_canonical_longside"])
                gt_w, gt_h = float(target[2]), float(target[3])
                row = {
                    "head": head,
                    "dataset": dataset,
                    "seed": seed,
                    "image_id": image_id,
                    "pred_id": pred_index,
                    "gt_id": gt_index,
                    "class": classes[int(labels[pred_index])],
                    "detection_score": float(scores[pred_index]),
                    "native_score": float(native[pred_index]),
                    "native_signal": "csl_softmax_top1_top2_margin" if head == "CSL" else "dcl_mean_sigmoid_bit_margin",
                    "angle_error": angle_error,
                    "aspect_ratio": max(gt_w, gt_h) / max(min(gt_w, gt_h), 1e-9),
                    "size": gt_w * gt_h,
                    "pred_box": [float(value) for value in pred],
                    "gt_box": [float(value) for value in target],
                    "match_iou": float(match_iou),
                    "post_nms": True,
                }
                if not all(math.isfinite(float(row[field])) for field in (
                        "detection_score", "native_score", "angle_error", "aspect_ratio",
                        "size", "match_iou")):
                    raise RuntimeError(f"{run_id}/{image_id}: nonfinite matched endpoint")
                output.write(json.dumps(row, separators=(",", ":")) + "\n")
                n_matched += 1
            if (index + 1) % 1000 == 0:
                log(head, dataset, seed,
                    f"progress {index + 1}/{len(data)} matched={n_matched} minutes={(time.time() - started) / 60:.1f}")
        output.flush()
        os.fsync(output.fileno())

    if (len(seen_image_ids) != EXPECTED_IMAGES[dataset] or n_gt != EXPECTED_GT[dataset]
            or n_matched != expected_matched or n_predictions <= 0):
        raise RuntimeError(
            f"{run_id}: cardinality mismatch images={len(seen_image_ids)} gt={n_gt} "
            f"pred={n_predictions} matched={n_matched} expected_matched={expected_matched}")
    os.replace(temporary, matched_path)
    manifest = {
        "status": "complete",
        "schema_version": SCHEMA,
        "run_id": run_id,
        "head": head,
        "dataset": dataset,
        "seed": seed,
        "n_images": len(data),
        "n_gt": n_gt,
        "n_predictions": n_predictions,
        "n_matched": n_matched,
        "native_signal": "csl_softmax_top1_top2_margin" if head == "CSL" else "dcl_mean_sigmoid_bit_margin",
        "matching": "own-detector post-NMS class-aware score-greedy rotated-IoU>=0.5",
        "matched_path": str(matched_path.relative_to(ROOT)),
        "matched_sha256": sha256(matched_path),
        "matched_bytes": matched_path.stat().st_size,
        "config_path": str(cfg_path),
        "config_sha256": sha256(cfg_path),
        "checkpoint_path": str(checkpoint),
        "checkpoint_sha256": checkpoint_sha,
        "k2_artifact_manifest_path": str(K2_ARTIFACT_MANIFEST.relative_to(ROOT)),
        "k2_artifact_manifest_sha256": sha256(K2_ARTIFACT_MANIFEST),
        "k2_eval_path": str(eval_path.relative_to(ROOT)),
        "k2_eval_sha256": sha256(eval_path),
        "gt_path": str(GT_PATHS[dataset].relative_to(ROOT)),
        "gt_sha256": sha256(GT_PATHS[dataset]),
        "identity_only": True,
        "post_nms_own_detector_matching": True,
        "no_tta": True,
        "no_ap_evaluation": True,
        "no_training": True,
        "generation_command": (
            f"CUDA_VISIBLE_DEVICES=<gpu> python scripts/m069_psc_native_signal_dump.py "
            f"{head} {dataset} {seed}"),
        "completed_at": time.strftime("%F %T %z"),
        "elapsed_seconds": round(time.time() - started, 3),
    }
    atomic_json(manifest_path, manifest)
    log(head, dataset, seed,
        f"DONE images={len(data)} gt={n_gt} matched={n_matched} sha={manifest['matched_sha256']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("head", choices=HEADS)
    parser.add_argument("dataset", choices=DATASETS_SUPPORTED)
    parser.add_argument("seed", type=int, choices=[0, 1, 2])
    parser.add_argument("--prefetch-workers", type=int, default=10)
    args = parser.parse_args()
    if args.prefetch_workers < 0:
        parser.error("--prefetch-workers must be nonnegative")
    run(args.head, args.dataset, args.seed, args.prefetch_workers)


if __name__ == "__main__":
    main()
