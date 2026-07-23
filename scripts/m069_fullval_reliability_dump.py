#!/usr/bin/env python3
"""Persist lineage-clean full-validation matched reliability inputs for command 069.

The dump combines identity, horizontal-flip, and vertical-flip inference in one
streaming pass.  It writes only matched detections plus a complete image universe;
the latter is required for image-level losses where images with no retained match
must contribute zero.  Frozen checkpoints are loaded read-only and no training is
performed.
"""
from __future__ import annotations

import argparse
import copy
import csv
import fcntl
import hashlib
import json
import math
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import torch

ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
PTH = Path("/home/rspip/cqc/pro/study/pth_data")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "top_journal_v3_reaudit_055"))

import mmrotate  # noqa: E402,F401
import mmrotate.datasets  # noqa: E402,F401
import mmrotate.models  # noqa: E402,F401
import orientbench_ext.instrumented_heads  # noqa: E402,F401
from mmengine.config import Config  # noqa: E402
from mmengine.registry import init_default_scope  # noqa: E402
from mmengine.runner import load_checkpoint  # noqa: E402
from mmrotate.registry import DATASETS, MODELS, TASK_UTILS  # noqa: E402
from orientbench.core.geometry import canonical_longside_theta  # noqa: E402
from orientbench.data.splits import assign_split  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract  # noqa: E402

init_default_scope("mmrotate")

OUT_ROOT = ROOT / "outputs/persistent_artifacts/m069_fullval_reliability"
LOG_ROOT = ROOT / "top_journal_v3_reaudit_055/logs/m069/fullval_reliability"
GT_ROOT = ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt"
DIOR_PREP = ROOT / "top_journal_v3_reaudit_055/data_prep/DIOR"
FAIR_PREP = ROOT / "top_journal_v3_reaudit_055/data_prep/FAIR1M_val20"
IOU = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))

CELLS = {
    "A": dict(
        dataset="DIOR-R", detector="rotated_retinanet_psc", cell_id="DIOR-R/22", psc=True,
        cfg=PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/config.py",
        ckpt=PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/best_mAP_5368_epoch_12.pth",
        expected_images=11738, expected_gt=124445,
    ),
    "B": dict(
        dataset="DIOR-R", detector="oriented_rcnn", cell_id="DIOR-R/3", psc=False,
        cfg=PTH / "baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/cell03_orcnn_dior_sgd_lr020.py",
        ckpt=PTH / "baseline_oriented_rcnn_r50_fpn_1x_le90/DIOR_trainval_test/best_dota_mAP_epoch_11.pth",
        expected_images=11738, expected_gt=124445,
    ),
    "C": dict(
        dataset="DIOR-R", detector="rotated_rtmdet_s", cell_id="DIOR-R/61", psc=False,
        cfg=PTH / "baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/config.py",
        ckpt=PTH / "baseline_rotated_rtmdet_s_fpn_3x_le90/DIOR_trainval_test_taos_pad32/best_mAP_5489_epoch_32.pth",
        expected_images=11738, expected_gt=124445,
    ),
    "D": dict(
        dataset="FAIR1M-v1.0", detector="rotated_retinanet_psc", cell_id="FAIR1M-v1.0/24", psc=True,
        cfg=PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/FAIR1M_train_only_val/config.py",
        ckpt=PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/FAIR1M_train_only_val/best_mAP_3462_epoch_12.pth",
        expected_images=4362, expected_gt=78644,
    ),
    "E": dict(
        dataset="SODA-A", detector="rotated_retinanet_psc", cell_id="SODA-A/23", psc=True,
        cfg=PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/config.py",
        ckpt=PTH / "baseline_rotated_retinanet_psc_r50_fpn_1x_le90/SODA_train_val/best_mAP_5991_epoch_12.pth",
        expected_images=22994, expected_gt=449644,
    ),
    "F": dict(
        dataset="SODA-A", detector="oriented_rcnn", cell_id="SODA-A/4", psc=False,
        cfg=PTH / "baseline_oriented_rcnn_r50_fpn_1x_le90/SODA_train_val/config.py",
        ckpt=PTH / "baseline_oriented_rcnn_r50_fpn_1x_le90/SODA_train_val/best_mAP_7295_epoch_09.pth",
        expected_images=22994, expected_gt=449644,
    ),
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


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


def log(cell: str, message: str) -> None:
    LOG_ROOT.mkdir(parents=True, exist_ok=True)
    line = f"[{time.strftime('%F %T')}] {cell} {message}\n"
    with (LOG_ROOT / f"{cell}.log").open("a", encoding="utf-8") as f:
        f.write(line)
    print(line.rstrip(), flush=True)


def configure_dataset(cfg: Config, spec: dict) -> tuple[dict, dict[str, list[tuple[int, torch.Tensor]]] | None, Path]:
    vd = copy.deepcopy(cfg.val_dataloader["dataset"])
    external_gt = None
    if spec["dataset"] == "DIOR-R":
        vd["data_root"] = str(DIOR_PREP) + "/"
        vd["ann_file"] = "annfiles_dotaformat/test/"
        vd["data_prefix"] = dict(img_path="dotaformat_images/test/")
        vd["img_suffix"] = "jpg"
        gt_path = GT_ROOT / "DIOR-R_test_fullval_gt.jsonl"
    elif spec["dataset"] == "FAIR1M-v1.0":
        vd["data_root"] = str(FAIR_PREP) + "/"
        vd["ann_file"] = "annfiles_dotaformat/"
        vd["data_prefix"] = dict(img_path="images/")
        vd["img_suffix"] = "png"
        gt_path = GT_ROOT / "FAIR1M-v1.0_val20_fullval_gt.jsonl"
        classes = list(vd["metainfo"]["classes"])
        class_index = {name: i for i, name in enumerate(classes)}
        external_gt = {}
        with gt_path.open(encoding="utf-8") as f:
            for line in f:
                row = json.loads(line)
                label = class_index.get(row["class_name"])
                if label is None:
                    raise KeyError(f"FAIR class absent from config: {row['class_name']}")
                box = torch.tensor([row[k] for k in ("obb_cx", "obb_cy", "obb_w", "obb_h", "obb_theta")])
                external_gt.setdefault(str(row["image_id"]), []).append((label, box))
    else:
        gt_path = GT_ROOT / "SODA-A_val_tiled_fullval_gt.jsonl"
    return vd, external_gt, gt_path


def flip_dataset(vd: dict, direction: str):
    out = copy.deepcopy(vd)
    pipeline = list(out["pipeline"])
    pack_index = next(i for i, step in enumerate(pipeline) if str(step.get("type", "")).endswith("PackDetInputs"))
    pipeline.insert(pack_index, dict(type="mmdet.RandomFlip", prob=1.0, direction=direction))
    pack_index += 1
    meta = list(pipeline[pack_index].get("meta_keys", ("img_id", "img_path", "ori_shape", "img_shape", "scale_factor")))
    for key in ("flip", "flip_direction"):
        if key not in meta:
            meta.append(key)
    pipeline[pack_index]["meta_keys"] = tuple(meta)
    out["pipeline"] = pipeline
    return DATASETS.build(out)


def predict(model, item):
    sample = item["data_samples"]
    data = model.data_preprocessor(
        dict(inputs=[item["inputs"].cuda()], data_samples=[sample.cuda()]), training=False)
    return model.predict(data["inputs"], data["data_samples"])[0].pred_instances


def tensors(inst):
    boxes = (inst.bboxes.tensor if hasattr(inst.bboxes, "tensor") else inst.bboxes).detach().cpu().float()
    return boxes, inst.scores.detach().cpu().float(), inst.labels.detach().cpu().long()


def unflip(boxes: torch.Tensor, direction: str, height: float, width: float) -> torch.Tensor:
    out = boxes.clone()
    if direction == "horizontal":
        out[:, 0] = width - out[:, 0]
    else:
        out[:, 1] = height - out[:, 1]
    out[:, 4] = -out[:, 4]
    return out


def tta_matches(base_boxes, base_labels, aug_boxes, aug_labels, threshold=0.3):
    result: dict[int, int] = {}
    for label in torch.unique(base_labels).tolist():
        base_indices = (base_labels == int(label)).nonzero(as_tuple=True)[0]
        aug_indices = (aug_labels == int(label)).nonzero(as_tuple=True)[0]
        if base_indices.numel() == 0 or aug_indices.numel() == 0:
            continue
        matrix = IOU(base_boxes[base_indices].cuda(), aug_boxes[aug_indices].cuda()).cpu()
        used_local: set[int] = set()
        for local_base, base_index in enumerate(base_indices.tolist()):
            available = [j for j in range(len(aug_indices)) if j not in used_local]
            if not available:
                break
            pos = max(available, key=lambda j: float(matrix[local_base, j]))
            if float(matrix[local_base, pos]) >= threshold:
                result[int(base_index)] = int(aug_indices[pos])
                used_local.add(pos)
    return result


def circular_variance(boxes: list[torch.Tensor]) -> float:
    angles = [canonical_longside_theta(float(b[2]), float(b[3]), float(b[4])) for b in boxes]
    angles = [a for a in angles if math.isfinite(a)]
    if not angles:
        return float("nan")
    doubled = 2.0 * np.asarray(angles)
    return float(1.0 - math.hypot(float(np.cos(doubled).mean()), float(np.sin(doubled).mean())))


def phase_fields(inst, coder) -> tuple[np.ndarray | None, np.ndarray | None]:
    if not hasattr(inst, "angle_encoded"):
        return None, None
    encoded = inst.angle_encoded.detach().cpu().float()
    ns = int(coder.num_step)
    cc = coder.coef_cos.detach().cpu().float()
    ss = coder.coef_sin.detach().cpu().float()
    primary = encoded[:, :ns]
    phase_cos = (primary * cc).sum(-1)
    phase_sin = (primary * ss).sum(-1)
    mod = phase_cos.square() + phase_sin.square()
    return encoded.numpy(), mod.numpy()


def area_bin(area: float) -> str:
    if area < 32 * 32:
        return "small"
    if area < 96 * 96:
        return "medium"
    return "large"


def gt_for_item(item, external_gt):
    image_id = str(item["data_samples"].img_id)
    if external_gt is not None:
        rows = external_gt.get(image_id, [])
        if not rows:
            return torch.zeros((0, 5)), torch.zeros((0,), dtype=torch.long)
        return torch.stack([r[1] for r in rows]).float(), torch.tensor([r[0] for r in rows], dtype=torch.long)
    gt = item["data_samples"].gt_instances
    boxes = (gt.bboxes.tensor if hasattr(gt.bboxes, "tensor") else gt.bboxes).detach().cpu().float()
    return boxes, gt.labels.detach().cpu().long()


def match_identity(base_boxes, base_scores, base_labels, gt_boxes, gt_labels):
    matches = []
    for label in torch.unique(base_labels).tolist():
        pred_indices = (base_labels == int(label)).nonzero(as_tuple=True)[0]
        gt_indices = (gt_labels == int(label)).nonzero(as_tuple=True)[0]
        if pred_indices.numel() == 0 or gt_indices.numel() == 0:
            continue
        matrix = IOU(base_boxes[pred_indices].cuda(), gt_boxes[gt_indices].cuda()).cpu()
        local_by_pred = {int(index): local for local, index in enumerate(pred_indices.tolist())}
        order = pred_indices[torch.argsort(base_scores[pred_indices], descending=True)]
        used_local: set[int] = set()
        for pred_index in order.tolist():
            available = [j for j in range(len(gt_indices)) if j not in used_local]
            if not available:
                break
            local_pred = local_by_pred[int(pred_index)]
            pos = max(available, key=lambda j: float(matrix[local_pred, j]))
            if float(matrix[local_pred, pos]) >= 0.5:
                used_local.add(pos)
                matches.append((int(pred_index), int(gt_indices[pos]), float(matrix[local_pred, pos])))
    return matches


def prefetched_items(base_ds, h_ds, v_ds, workers: int):
    """Load aligned identity/hflip/vflip samples ahead of GPU inference."""
    if workers <= 1:
        for index in range(len(base_ds)):
            yield index, (base_ds[index], None if h_ds is None else h_ds[index],
                          None if v_ds is None else v_ds[index])
        return

    def load(index):
        return (base_ds[index], None if h_ds is None else h_ds[index],
                None if v_ds is None else v_ds[index])

    window = max(workers * 2, workers)
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="m069-data") as pool:
        pending = {index: pool.submit(load, index) for index in range(min(window, len(base_ds)))}
        for index in range(len(base_ds)):
            item = pending.pop(index).result()
            next_index = index + window
            if next_index < len(base_ds):
                pending[next_index] = pool.submit(load, next_index)
            yield index, item


def run(cell: str, skip_tta: bool = False, prefetch_workers: int = 10) -> None:
    spec = CELLS[cell]
    # Identity-only mode is diagnostic and must never overwrite the canonical
    # formal identity+hflip+vflip artifact namespace.
    out_dir = OUT_ROOT / ("identity_only_nonformal" if skip_tta else "") / cell
    out_dir.mkdir(parents=True, exist_ok=True)
    matched_final = out_dir / "matched_fullval.jsonl"
    universe_final = out_dir / "image_universe.csv"
    manifest_path = out_dir / "manifest.json"
    if manifest_path.is_file():
        manifest = load_json(manifest_path)
        if (manifest and manifest.get("status") == "complete" and matched_final.is_file() and universe_final.is_file()
                and manifest.get("matched_sha256") == sha256(matched_final)
                and manifest.get("universe_sha256") == sha256(universe_final)
                and manifest.get("matched_bytes") == matched_final.stat().st_size
                and manifest.get("universe_bytes") == universe_final.stat().st_size
                and manifest.get("n_images") == spec["expected_images"]
                and manifest.get("n_gt") == spec["expected_gt"]
                and manifest.get("n_matched", 0) > 0
                and manifest.get("tta_enabled") is (not skip_tta)
                and manifest.get("checkpoint_sha256") == sha256(spec["ckpt"])
                and manifest.get("config_sha256") == sha256(spec["cfg"])
                and not any("/dev/shm" in str(value) for value in manifest.values())):
            log(cell, "verified existing complete artifact; no inference repeated")
            return
    lock_handle = (out_dir / ".generation.lock").open("a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise RuntimeError(f"{cell}: another artifact generator holds the lock") from exc

    cfg = Config.fromfile(str(spec["cfg"]))
    if spec["psc"]:
        cfg.model.bbox_head.type = "InstrumentedAngleBranchRetinaHead"
    model = MODELS.build(cfg.model)
    load_checkpoint(model, str(spec["ckpt"]), map_location="cpu")
    model.eval().cuda()
    checkpoint_sha = sha256(spec["ckpt"])
    config_sha = sha256(spec["cfg"])
    coder = getattr(getattr(model, "bbox_head", None), "angle_coder", None)
    vd, external_gt, gt_path = configure_dataset(cfg, spec)
    base_ds = DATASETS.build(vd)
    h_ds = None if skip_tta else flip_dataset(vd, "horizontal")
    v_ds = None if skip_tta else flip_dataset(vd, "vertical")
    if len(base_ds) != spec["expected_images"]:
        raise RuntimeError(f"{cell}: expected {spec['expected_images']} images, got {len(base_ds)}")
    if h_ds is not None and (len(h_ds) != len(base_ds) or len(v_ds) != len(base_ds)):
        raise RuntimeError(f"{cell}: TTA dataset length mismatch")

    matched_tmp = matched_final.with_suffix(".jsonl.partial")
    universe_tmp = universe_final.with_suffix(".csv.partial")
    for path in (matched_tmp, universe_tmp):
        if path.exists():
            path.unlink()
    classes = list(vd["metainfo"]["classes"])
    n_gt = n_pred = n_matched = n_tta_2 = n_tta_3 = 0
    seen_image_ids: set[str] = set()
    started = time.time()
    with matched_tmp.open("w", encoding="utf-8") as matched_out, universe_tmp.open("w", newline="", encoding="utf-8") as universe_out:
        universe_writer = csv.DictWriter(
            universe_out,
            fieldnames=["cell", "dataset", "image_id", "image_path", "d_cal_daudit_split_flag", "n_gt", "n_predictions"])
        universe_writer.writeheader()
        with torch.no_grad():
            for index, (item, prefetched_h, prefetched_v) in prefetched_items(
                    base_ds, h_ds, v_ds, prefetch_workers):
                image_id = str(item["data_samples"].img_id)
                if image_id in seen_image_ids:
                    raise RuntimeError(f"{cell}: duplicate image id {image_id}")
                seen_image_ids.add(image_id)
                image_path = str(item["data_samples"].metainfo.get("img_path", ""))
                gt_boxes, gt_labels = gt_for_item(item, external_gt)
                n_gt += len(gt_boxes)
                base_inst = predict(model, item)
                base_boxes, base_scores, base_labels = tensors(base_inst)
                n_pred += len(base_boxes)
                encoded, phase_mod = phase_fields(base_inst, coder) if spec["psc"] else (None, None)
                h_boxes = v_boxes = torch.zeros((0, 5))
                h_labels = v_labels = torch.zeros((0,), dtype=torch.long)
                h_map: dict[int, int] = {}
                v_map: dict[int, int] = {}
                if not skip_tta:
                    hi, vi = prefetched_h, prefetched_v
                    if str(hi["data_samples"].img_id) != image_id or str(vi["data_samples"].img_id) != image_id:
                        raise RuntimeError(f"{cell}/{index}: TTA image id mismatch")
                    hb, _, h_labels = tensors(predict(model, hi))
                    vb, _, v_labels = tensors(predict(model, vi))
                    height, width = item["data_samples"].metainfo["ori_shape"][:2]
                    h_boxes = unflip(hb, "horizontal", float(height), float(width))
                    v_boxes = unflip(vb, "vertical", float(height), float(width))
                    h_map = tta_matches(base_boxes, base_labels, h_boxes, h_labels)
                    v_map = tta_matches(base_boxes, base_labels, v_boxes, v_labels)

                universe_writer.writerow(dict(
                    cell=cell, dataset=spec["dataset"], image_id=image_id, image_path=image_path,
                    d_cal_daudit_split_flag=assign_split(image_id), n_gt=len(gt_boxes), n_predictions=len(base_boxes)))
                for pred_index, gt_index, match_iou in match_identity(
                        base_boxes, base_scores, base_labels, gt_boxes, gt_labels):
                    pred = base_boxes[pred_index]
                    gt = gt_boxes[gt_index]
                    cc = angle_error_contract(*[float(x) for x in pred[2:5]], *[float(x) for x in gt[2:5]])
                    angle_error = float(cc["angle_error_canonical_longside"])
                    if not math.isfinite(angle_error):
                        continue
                    angles = [pred]
                    if pred_index in h_map:
                        angles.append(h_boxes[h_map[pred_index]])
                    if pred_index in v_map:
                        angles.append(v_boxes[v_map[pred_index]])
                    if len(angles) >= 2:
                        n_tta_2 += 1
                    if len(angles) == 3:
                        n_tta_3 += 1
                    gt_w, gt_h = float(gt[2]), float(gt[3])
                    area = gt_w * gt_h
                    aspect = max(gt_w, gt_h) / max(min(gt_w, gt_h), 1e-9)
                    label = int(base_labels[pred_index])
                    row = dict(
                        cell_id=spec["cell_id"], cell=cell, dataset=spec["dataset"], detector=spec["detector"],
                        image_id=image_id, image_path=image_path, pred_id=pred_index, gt_id=gt_index,
                        score=float(base_scores[pred_index]),
                        phase_mod=(float(phase_mod[pred_index]) if phase_mod is not None else ""),
                        phase_vector=(encoded[pred_index].tolist() if encoded is not None else []),
                        pred_obb=dict(obb_cx=float(pred[0]), obb_cy=float(pred[1]), obb_w=float(pred[2]),
                                      obb_h=float(pred[3]), obb_theta=float(pred[4])),
                        gt_obb=dict(obb_cx=float(gt[0]), obb_cy=float(gt[1]), obb_w=gt_w,
                                    obb_h=gt_h, obb_theta=float(gt[4])),
                        match_iou=round(match_iou, 6), angle_error=angle_error,
                        **{"class": classes[label] if label < len(classes) else str(label)},
                        size=area, aspect_ratio=aspect, near_square=bool(cc["near_square"]),
                        size_bin=area_bin(area), split="fullval",
                        d_cal_daudit_split_flag=assign_split(image_id),
                        tta_circular_variance=(circular_variance(angles) if len(angles) >= 2 else None),
                        n_tta_angles=len(angles), tta_stable_key="same-forward image/class/rotated-IoU>=0.3",
                        source_checkpoint=str(spec["ckpt"]), checkpoint_sha256=checkpoint_sha,
                        config_path=str(spec["cfg"]), is_real_detector_output=True,
                        is_synthetic_or_proxy=False, lineage="m069_fullval_reliability",
                    )
                    matched_out.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
                    n_matched += 1
                if (index + 1) % 1000 == 0:
                    log(cell, f"progress {index + 1}/{len(base_ds)} matched={n_matched} minutes={(time.time() - started) / 60:.1f}")

    if n_gt != spec["expected_gt"]:
        raise RuntimeError(f"{cell}: expected {spec['expected_gt']} GT, got {n_gt}")
    if len(seen_image_ids) != spec["expected_images"] or n_matched <= 0:
        raise RuntimeError(
            f"{cell}: incomplete output images={len(seen_image_ids)} matched={n_matched}")
    if not skip_tta and n_tta_2 <= 0:
        raise RuntimeError(f"{cell}: formal output has no stable TTA matches")
    os.replace(matched_tmp, matched_final)
    os.replace(universe_tmp, universe_final)
    manifest = dict(
        status="complete", cell=cell, cell_id=spec["cell_id"], dataset=spec["dataset"], detector=spec["detector"],
        split="full-validation", n_images=len(base_ds), n_gt=n_gt, n_predictions=n_pred, n_matched=n_matched,
        n_with_at_least_2_tta=n_tta_2, n_with_3_tta=n_tta_3, tta_enabled=not skip_tta,
        matched_path=str(matched_final.relative_to(ROOT)), matched_bytes=matched_final.stat().st_size,
        matched_sha256=sha256(matched_final), universe_path=str(universe_final.relative_to(ROOT)),
        universe_bytes=universe_final.stat().st_size, universe_sha256=sha256(universe_final),
        gt_path=str(gt_path.relative_to(ROOT)), gt_sha256=sha256(gt_path),
        checkpoint_path=str(spec["ckpt"]), checkpoint_sha256=checkpoint_sha,
        config_path=str(spec["cfg"]), config_sha256=config_sha,
        split_assignment="orientbench.data.splits.assign_split; frozen salt orientbench_v1",
        can_recompute=True, generation_command=f"CUDA_VISIBLE_DEVICES=<gpu> python scripts/m069_fullval_reliability_dump.py {cell}",
        completed_at=time.strftime("%F %T %z"), elapsed_seconds=round(time.time() - started, 3),
    )
    atomic_json(manifest_path, manifest)
    log(cell, f"DONE images={len(base_ds)} gt={n_gt} pred={n_pred} matched={n_matched} sha={manifest['matched_sha256']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("cell", choices=sorted(CELLS))
    parser.add_argument("--skip-tta", action="store_true", help="Identity-only emergency mode; not formal M1 output")
    parser.add_argument("--prefetch-workers", type=int, default=10)
    args = parser.parse_args()
    if args.prefetch_workers < 0:
        parser.error("--prefetch-workers must be nonnegative")
    run(args.cell, args.skip_tta, args.prefetch_workers)


if __name__ == "__main__":
    main()
