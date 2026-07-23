#!/usr/bin/env python3
"""Instrumented PSC Phase-1 forward on frozen K2 final checkpoints.

Backbone/head tensors are computed once per image.  The preregistered radial k
grid is decoded and NMS-evaluated from the shared head output, avoiding ten
redundant detector forwards.  Seed 0 also records h/v TTA phase direction.
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
import pickle
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import torch

ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
REPO = ROOT / "top_journal_v3_reaudit_055"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(REPO))

import mmrotate  # noqa: E402,F401
import mmrotate.datasets  # noqa: E402,F401
import mmrotate.models  # noqa: E402,F401
import orientbench_ext.instrumented_heads  # noqa: E402,F401
from mmengine.config import Config  # noqa: E402
from mmengine.registry import init_default_scope  # noqa: E402
from mmengine.runner import load_checkpoint  # noqa: E402
from mmrotate.registry import DATASETS, MODELS, TASK_UTILS  # noqa: E402
from orientbench.core.geometry import canonical_longside_theta  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract  # noqa: E402

init_default_scope("mmrotate")
IOU = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))
OUT = ROOT / "outputs/persistent_artifacts/m069_psc_phase1"
LOG = REPO / "logs/m069/psc_phase1_forward"
K_GRID = [0.25, 0.50, 0.75, 0.90, 1.00, 1.10, 1.25, 1.50, 2.00, 4.00]
K2_ARTIFACT_MANIFEST = REPO / "reports/k2_artifact_manifest_067.csv"
EXPECTED_IMAGES = {"DIOR-R": 11738, "SODA-A": 22994}
EXPECTED_GT = {"DIOR-R": 124445, "SODA-A": 449644}
GT_PATHS = {
    "DIOR-R": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl",
    "SODA-A": ROOT / "outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl",
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


def atomic_csv(path: Path, rows: list[dict]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def log(dataset, seed, message):
    LOG.mkdir(parents=True, exist_ok=True)
    line = f"[{time.strftime('%F %T')}] {dataset} seed={seed} {message}\n"
    with (LOG / f"{dataset}_seed{seed}.log").open("a", encoding="utf-8") as f:
        f.write(line)
    print(line.rstrip(), flush=True)


def paths(dataset, seed):
    slug = "DIOR-R" if dataset == "DIOR-R" else "SODA-A"
    work = REPO / f"work_dirs/k2/K2_final__PSC__{slug}__seed{seed}"
    cfg_name = "psc_dior_seed0.py" if dataset == "DIOR-R" else "psc_soda_seed0.py"
    return work / cfg_name, work / "epoch_12.pth", OUT / slug / f"seed{seed}"


def verify_k2_checkpoint(dataset, seed, checkpoint):
    run_id = f"K2_final__PSC__{dataset}__seed{seed}"
    rows = {row["run_id"]: row for row in csv.DictReader(K2_ARTIFACT_MANIFEST.open())}
    if run_id not in rows:
        raise RuntimeError(f"frozen K2 artifact manifest lacks {run_id}")
    row = rows[run_id]
    if str(row.get("can_recompute", "")).strip().lower() not in {"yes", "true", "1"}:
        raise RuntimeError(f"K2 artifact is not marked recomputable for {run_id}")
    if Path(row["checkpoint"]).resolve() != checkpoint.resolve():
        raise RuntimeError(f"K2 checkpoint path drift for {run_id}")
    actual = sha256(checkpoint)
    if not actual.startswith(row["ckpt_sha"]):
        raise RuntimeError(f"K2 checkpoint SHA drift for {run_id}")
    eval_path = Path(row["eval_json"])
    if not eval_path.is_file() or not sha256(eval_path).startswith(row["eval_sha"]):
        raise RuntimeError(f"K2 frozen evaluator artifact drift for {run_id}")
    log_path = Path(row["log"])
    if not log_path.is_file() or not sha256(log_path).startswith(row["log_sha"]):
        raise RuntimeError(f"K2 frozen training log artifact drift for {run_id}")
    evaluator = load_json(eval_path)
    if (not evaluator or evaluator.get("run_id") != run_id
            or evaluator.get("head") != "PSC" or evaluator.get("dataset") != dataset):
        raise RuntimeError(f"K2 frozen evaluator identity drift for {run_id}")
    return run_id, row, actual, eval_path


def flip_dataset(vd, direction):
    out = copy.deepcopy(vd)
    pipeline = list(out["pipeline"])
    pack = next(i for i, step in enumerate(pipeline) if str(step.get("type", "")).endswith("PackDetInputs"))
    pipeline.insert(pack, dict(type="mmdet.RandomFlip", prob=1.0, direction=direction))
    pack += 1
    keys = list(pipeline[pack].get("meta_keys", ("img_id", "img_path", "ori_shape", "img_shape", "scale_factor")))
    for key in ("flip", "flip_direction"):
        if key not in keys:
            keys.append(key)
    pipeline[pack]["meta_keys"] = tuple(keys)
    out["pipeline"] = pipeline
    return DATASETS.build(out)


def preprocess(model, item):
    sample = item["data_samples"]
    return model.data_preprocessor(
        dict(inputs=[item["inputs"].cuda()], data_samples=[sample.cuda()]), training=False)


def predict_from_outs(model, outs, samples, k, feature_norms=None):
    cls_scores, bbox_preds, angle_preds = outs
    scaled = [pred * float(k) for pred in angle_preds]
    metas = [sample.metainfo for sample in samples]
    model.bbox_head._phase1_feature_norms = feature_norms
    return model.bbox_head.predict_by_feat(
        cls_scores, bbox_preds, scaled, batch_img_metas=metas, rescale=True, with_nms=True)[0]


def forward_once(model, item):
    data = preprocess(model, item)
    features = model.extract_feat(data["inputs"])
    return model.bbox_head(features), data["data_samples"], features


def regression_feature_norms(head, features):
    """Actual angle/regression-tower feature norm at every FPN location."""
    norms = []
    with torch.no_grad():
        for feature in features:
            reg_feature = feature
            for convolution in head.reg_convs:
                reg_feature = convolution(reg_feature)
            norms.append(torch.linalg.vector_norm(reg_feature.float(), dim=1))
    return norms


def tensors(inst):
    boxes = (inst.bboxes.tensor if hasattr(inst.bboxes, "tensor") else inst.bboxes).detach().cpu().float()
    scores = inst.scores.detach().cpu().float()
    labels = inst.labels.detach().cpu().long()
    encoded = inst.angle_encoded.detach().cpu().float()
    feature_norm = (inst.phase1_reg_feature_norm.detach().cpu().float()
                    if hasattr(inst, "phase1_reg_feature_norm")
                    else torch.full((len(boxes),), float("nan")))
    return boxes, scores, labels, encoded, feature_norm


def gt(item):
    instances = item["data_samples"].gt_instances
    boxes = (instances.bboxes.tensor if hasattr(instances.bboxes, "tensor") else instances.bboxes).detach().cpu().float()
    return boxes, instances.labels.detach().cpu().long()


def match(boxes, scores, labels, gt_boxes, gt_labels):
    rows = []
    for label in torch.unique(labels).tolist():
        pred_indices = (labels == int(label)).nonzero(as_tuple=True)[0]
        gt_indices = (gt_labels == int(label)).nonzero(as_tuple=True)[0]
        if pred_indices.numel() == 0 or gt_indices.numel() == 0:
            continue
        matrix = IOU(boxes[pred_indices].cuda(), gt_boxes[gt_indices].cuda()).cpu()
        order = pred_indices[torch.argsort(scores[pred_indices], descending=True)]
        local = {int(pred): idx for idx, pred in enumerate(pred_indices.tolist())}
        used = set()
        for pred_index in order.tolist():
            ious = matrix[local[pred_index]]
            available = [j for j in range(len(gt_indices)) if j not in used]
            if not available:
                break
            best_local = max(available, key=lambda j: float(ious[j]))
            if float(ious[best_local]) >= 0.5:
                used.add(best_local)
                rows.append((pred_index, int(gt_indices[best_local]), float(ious[best_local])))
    return rows


def unflip(boxes, direction, height, width):
    boxes = boxes.clone()
    if direction == "horizontal":
        boxes[:, 0] = width - boxes[:, 0]
    else:
        boxes[:, 1] = height - boxes[:, 1]
    boxes[:, 4] = -boxes[:, 4]
    return boxes


def cross_view_map(base_boxes, base_labels, aug_boxes, aug_labels, threshold=0.3):
    mapping = {}
    for label in torch.unique(base_labels).tolist():
        base_indices = (base_labels == int(label)).nonzero(as_tuple=True)[0]
        aug_indices = (aug_labels == int(label)).nonzero(as_tuple=True)[0]
        if base_indices.numel() == 0 or aug_indices.numel() == 0:
            continue
        matrix = IOU(base_boxes[base_indices].cuda(), aug_boxes[aug_indices].cuda()).cpu()
        used_local = set()
        for local_base, base_index in enumerate(base_indices.tolist()):
            available = [j for j in range(len(aug_indices)) if j not in used_local]
            if not available:
                break
            pos = max(available, key=lambda j: float(matrix[local_base, j]))
            if float(matrix[local_base, pos]) >= threshold:
                mapping[int(base_index)] = int(aug_indices[pos])
                used_local.add(pos)
    return mapping


def angle_periodic_diff(a, b):
    delta = abs(float(a) - float(b)) % math.pi
    return min(delta, math.pi - delta)


def phase_stats(vector, coder):
    ns = int(coder.num_step)
    coef_sin = coder.coef_sin.detach().cpu().float()
    coef_cos = coder.coef_cos.detach().cpu().float()
    first, second = vector[:ns], vector[ns:2 * ns]
    p1s, p1c = float((first * coef_sin).sum()), float((first * coef_cos).sum())
    p2s, p2c = float((second * coef_sin).sum()), float((second * coef_cos).sum())
    phase1 = -math.atan2(p1s, p1c)
    phase2 = -math.atan2(p2s, p2c) / 2.0
    cand0 = phase2
    cand1 = ((phase2 + math.pi + math.pi) % (2 * math.pi)) - math.pi
    align0 = math.cos(phase1 - cand0)
    align1 = math.cos(phase1 - cand1)
    chosen = cand1 if align1 > align0 else cand0
    return dict(
        phase_mod_primary=p1c * p1c + p1s * p1s,
        phase_mod_secondary=p2c * p2c + p2s * p2s,
        phase_angle_primary=phase1,
        phase_angle_secondary=phase2,
        multi_frequency_disagreement_deg=math.degrees(angle_periodic_diff(phase1 / 2.0, chosen / 2.0)),
        unwrap_candidate_energy_gap=abs(align0 - align1),
        phase_direction_margin=abs(align0 - align1) * math.sqrt(max(p2c * p2c + p2s * p2s, 0.0)),
        angle_vector_norm=float(torch.linalg.vector_norm(vector)),
    )


def loss_gradient(vector, target, k, weight=0.2):
    """Matched post-NMS L1 diagnostic; not the trained anchor-assigned loss."""
    value = vector * float(k)
    delta = value - target
    loss = float(delta.abs().mean() * weight)
    grad = torch.sign(delta) * (weight / max(1, delta.numel()))
    dloss_dk = abs(float(torch.dot(grad, vector)))
    norm = torch.linalg.vector_norm(value)
    if float(norm) <= 1e-12:
        grad_norm = float(torch.linalg.vector_norm(grad))
        return loss, grad_norm, grad_norm, dloss_dk
    radial_unit = value / norm
    radial_signed = torch.dot(grad, radial_unit)
    tangential = grad - radial_signed * radial_unit
    return loss, abs(float(radial_signed)), float(torch.linalg.vector_norm(tangential)), dloss_dk


def prepare_angle_loss_context(head, outs, samples):
    """Freeze the trained head's anchor assignment in network coordinates.

    The validation pipelines load annotations after ``Resize`` so their packed
    GT boxes deliberately remain in original-image coordinates for evaluation.
    Head priors, however, live in resized input coordinates.  Recreate the
    training-time coordinate system before assigning anchors; otherwise the
    reported configured loss is evaluated on the wrong positive anchors.
    """
    cls_scores, _, _ = outs
    featmap_sizes = [feature.size()[-2:] for feature in cls_scores]
    metas = [sample.metainfo for sample in samples]
    gt_instances = []
    for sample in samples:
        instance = sample.gt_instances.clone()
        scale_factor = tuple(float(value) for value in sample.metainfo.get("scale_factor", (1.0, 1.0)))
        if len(scale_factor) != 2 or not all(math.isfinite(value) and value > 0 for value in scale_factor):
            raise RuntimeError(f"invalid validation scale_factor for PSC loss audit: {scale_factor}")
        instance.bboxes.rescale_(scale_factor)
        gt_instances.append(instance)
    anchor_list, valid_flag_list = head.get_anchors(
        featmap_sizes, metas, device=cls_scores[0].device)
    targets = head.get_targets(
        anchor_list, valid_flag_list, gt_instances, metas,
        batch_gt_instances_ignore=None)
    if targets is None or len(targets) != 7:
        raise RuntimeError("PSC head did not return the expected anchor-assigned angle targets")
    _, _, _, _, avg_factor, angle_targets, angle_weights = targets
    positive_base = []
    positive_targets = []
    positive_weights = []
    for base, target, weight in zip(outs[2], angle_targets, angle_weights):
        base_flat = base.detach().permute(0, 2, 3, 1).reshape(-1, head.encode_size)
        target_flat = target.reshape(-1, head.encode_size)
        weight_flat = weight.reshape(-1, 1)
        mask = weight_flat[:, 0] > 0
        if bool(mask.any()):
            positive_base.append(base_flat[mask])
            positive_targets.append(target_flat[mask])
            positive_weights.append(weight_flat[mask])
    return {
        "base": torch.cat(positive_base) if positive_base else None,
        "target": torch.cat(positive_targets) if positive_targets else None,
        "weight": torch.cat(positive_weights) if positive_weights else None,
        "avg_factor": avg_factor,
    }


def actual_angle_loss_gradient(head, base_angle_preds, context, k):
    """Evaluate the configured anchor-assigned loss L(kz) and its radial geometry.

    Gradients are with respect to z'=kz. ``dL/dk`` applies the chain rule using
    the original z. Only positive/weighted anchors define the vector geometry.
    """
    if isinstance(context, dict):
        base_positive = context["base"]
        target_positive = context["target"]
        weight_positive = context["weight"]
        avg_factor = context["avg_factor"]
    else:
        angle_targets, angle_weights, avg_factor = context
        positive_base = []
        positive_targets = []
        positive_weights = []
        for base, target, weight in zip(base_angle_preds, angle_targets, angle_weights):
            base_flat = base.detach().permute(0, 2, 3, 1).reshape(-1, head.encode_size)
            target_flat = target.reshape(-1, head.encode_size)
            weight_flat = weight.reshape(-1, 1)
            mask = weight_flat[:, 0] > 0
            if bool(mask.any()):
                positive_base.append(base_flat[mask])
                positive_targets.append(target_flat[mask])
                positive_weights.append(weight_flat[mask])
        base_positive = torch.cat(positive_base) if positive_base else None
        target_positive = torch.cat(positive_targets) if positive_targets else None
        weight_positive = torch.cat(positive_weights) if positive_weights else None
    if base_positive is None:
        return 0.0, 0.0, 0.0, 0.0, 0
    with torch.enable_grad():
        scaled_positive = (base_positive * float(k)).requires_grad_(True)
        total = head.loss_angle(
            scaled_positive, target_positive, weight=weight_positive, avg_factor=avg_factor)
        gradient_positive, = torch.autograd.grad(
            total, scaled_positive, retain_graph=False, create_graph=False)

    dot_g_scaled = float((gradient_positive.detach() * scaled_positive.detach()).sum())
    dot_g_base = float((gradient_positive.detach() * base_positive).sum())
    scaled_norm_sq = float(scaled_positive.detach().square().sum())
    gradient_norm_sq = float(gradient_positive.detach().square().sum())
    positive_anchors = len(base_positive)
    if positive_anchors <= 0 or scaled_norm_sq <= 0:
        radial = math.sqrt(max(gradient_norm_sq, 0.0))
        tangential = radial
    else:
        radial = abs(dot_g_scaled) / math.sqrt(scaled_norm_sq)
        tangential = math.sqrt(max(gradient_norm_sq - radial * radial, 0.0))
    return float(total.detach()), radial, tangential, abs(dot_g_base), positive_anchors


def set_signature(boxes, scores, labels):
    if not len(boxes):
        return hashlib.sha256(b"empty").hexdigest()
    data = np.column_stack([
        np.round(boxes.numpy(), 5), np.round(scores.numpy(), 6), labels.numpy(),
    ])
    return hashlib.sha256(data.tobytes()).hexdigest()


def voc_ap(tp, scores, n_gt):
    if n_gt == 0:
        return float("nan")
    order = np.argsort(-scores, kind="stable")
    tp = tp[order]
    cumulative_tp = np.cumsum(tp)
    cumulative_fp = np.cumsum(1 - tp)
    recall = cumulative_tp / n_gt
    precision = cumulative_tp / np.maximum(cumulative_tp + cumulative_fp, 1e-9)
    return float(sum((precision[recall >= threshold].max() if (recall >= threshold).any() else 0.0) / 11
                     for threshold in np.linspace(0, 1, 11)))


def evaluate_stream(path, gts_by_class, thresholds=(0.5, 0.75)):
    detections = {}
    with path.open("rb") as f:
        while True:
            try:
                image_id, boxes, scores, labels = pickle.load(f)
            except EOFError:
                break
            for i in range(len(boxes)):
                detections.setdefault(int(labels[i]), []).append((float(scores[i]), image_id, boxes[i]))
    aps = {float(threshold): {} for threshold in thresholds}
    for label, by_image in gts_by_class.items():
        n_gt = sum(len(rows) for rows in by_image.values())
        rows = sorted(detections.get(label, []), key=lambda row: -row[0])
        score = np.asarray([row[0] for row in rows], dtype=float)
        positions_by_image = {}
        for position, (_, image_id, _) in enumerate(rows):
            positions_by_image.setdefault(image_id, []).append(position)
        matrices = {}
        for image_id, positions in positions_by_image.items():
            candidates = by_image.get(image_id, [])
            if not candidates:
                continue
            pred_tensor = torch.stack([rows[position][2] for position in positions])
            gt_tensor = torch.stack(candidates)
            matrix = IOU(pred_tensor.cuda(), gt_tensor.cuda()).cpu().numpy()
            matrices[image_id] = {position: matrix[local] for local, position in enumerate(positions)}
        for threshold in thresholds:
            tp = np.zeros(len(rows))
            used = set()
            for index, (_, image_id, _) in enumerate(rows):
                if image_id not in matrices:
                    continue
                values = matrices[image_id][index]
                best = int(np.argmax(values))
                if (float(values[best]) >= threshold
                        and (image_id, best) not in used):
                    tp[index] = 1
                    used.add((image_id, best))
            aps[float(threshold)][label] = voc_ap(tp, score, n_gt)
    output = {}
    for threshold, per_class in aps.items():
        values = [value for value in per_class.values() if np.isfinite(value)]
        output[threshold] = float(np.mean(values)) if values else float("nan")
    return output


def prefetched_items(data, h_data, v_data, workers):
    if workers <= 1:
        for index in range(len(data)):
            yield index, (data[index], None if h_data is None else h_data[index],
                          None if v_data is None else v_data[index])
        return

    def load(index):
        return (data[index], None if h_data is None else h_data[index],
                None if v_data is None else v_data[index])

    window = max(workers * 2, workers)
    with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="psc-phase1-data") as pool:
        pending = {index: pool.submit(load, index) for index in range(min(window, len(data)))}
        for index in range(len(data)):
            item = pending.pop(index).result()
            next_index = index + window
            if next_index < len(data):
                pending[next_index] = pool.submit(load, next_index)
            yield index, item


def run(dataset, seed, prefetch_workers=10):
    cfg_path, checkpoint, out_dir = paths(dataset, seed)
    run_id, k2_artifact, checkpoint_sha, k2_eval_path = verify_k2_checkpoint(
        dataset, seed, checkpoint)
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = out_dir / "manifest.json"
    summary_path = out_dir / "radial_full_evaluator.csv"
    matched_path = out_dir / "matched_phase.jsonl"
    if manifest_path.is_file():
        meta = load_json(manifest_path)
        post_items = meta.get("postnms_artifacts", []) if meta else []
        postnms_valid = (len(post_items) == len(K_GRID)
            and np.allclose([float(item.get("k", float("nan"))) for item in post_items],
                            K_GRID, rtol=0, atol=1e-12)
            and all(
            (ROOT / item["path"]).is_file()
            and sha256(ROOT / item["path"]) == item.get("sha256")
            and (ROOT / item["path"]).stat().st_size == int(item.get("bytes", -1))
            for item in post_items))
        if (meta and meta.get("status") == "complete"
                and meta.get("schema_version") == "psc_phase1_radial_scaling_v2"
                and meta.get("run_id") == run_id and meta.get("n_images") == EXPECTED_IMAGES[dataset]
                and meta.get("n_gt") == EXPECTED_GT[dataset]
                and meta.get("k_grid") == K_GRID and meta.get("checkpoint_sha256") == checkpoint_sha
                and meta.get("k2_artifact_manifest_sha256") == sha256(K2_ARTIFACT_MANIFEST)
                and meta.get("k2_eval_sha256") == sha256(k2_eval_path)
                and meta.get("gt_sha256") == sha256(GT_PATHS[dataset])
                and meta.get("config_sha256") == sha256(cfg_path)
                and meta.get("objectness_available") is False
                and meta.get("no_training") is True
                and summary_path.is_file() and matched_path.is_file()
                and meta.get("summary_sha256") == sha256(summary_path)
                and meta.get("matched_sha256") == sha256(matched_path)
                and postnms_valid
                and not any("/dev/shm" in str(value) for value in meta.values())):
            log(dataset, seed, "verified existing complete artifact; no forward repeated")
            return
    lock_handle = (out_dir / ".generation.lock").open("a+")
    try:
        fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise RuntimeError(f"{run_id}: another Phase-1 generator holds the lock") from exc

    cfg = Config.fromfile(str(cfg_path))
    cfg.model.bbox_head.type = "InstrumentedAngleBranchRetinaHead"
    model = MODELS.build(cfg.model)
    load_checkpoint(model, str(checkpoint), map_location="cpu")
    model.eval().cuda()
    coder = model.bbox_head.angle_coder
    data = DATASETS.build(cfg.val_dataloader["dataset"])
    if len(data) != EXPECTED_IMAGES[dataset]:
        raise RuntimeError(
            f"{run_id}: expected {EXPECTED_IMAGES[dataset]} full-validation images, got {len(data)}")
    h_data = flip_dataset(cfg.val_dataloader["dataset"], "horizontal") if seed == 0 else None
    v_data = flip_dataset(cfg.val_dataloader["dataset"], "vertical") if seed == 0 else None
    classes = list(cfg.val_dataloader["dataset"]["metainfo"]["classes"])
    postnms_paths = {k: out_dir / f"postnms_k{k:.2f}.pklstream" for k in K_GRID}
    temp_paths = {k: path.with_suffix(path.suffix + ".tmp") for k, path in postnms_paths.items()}
    for path in temp_paths.values():
        if path.exists():
            path.unlink()
    streams = {k: path.open("wb") for k, path in temp_paths.items()}
    matched_tmp = matched_path.with_suffix(".jsonl.tmp")
    gts_by_class = {}
    seen_image_ids = []
    aggregates = {k: dict(
        loss=[], radial=[], tangential=[], dloss_dk=[], angle_error=[], phase_mod_primary=[],
        phase_mod_secondary=[], controlled_loss=[], controlled_radial=[], controlled_tangential=[],
        controlled_dloss_dk=[], controlled_phase_mod_primary=[], controlled_phase_mod_secondary=[],
        actual_head_loss=[], actual_head_radial=[], actual_head_tangential=[],
        actual_head_dloss_dk=[], actual_head_positive_anchors=[],
        n_pred=0, n_match=0, exact_set=0, box_class_set_equal=0, decoded_diff=[])
        for k in K_GRID}
    started = time.time()
    with matched_tmp.open("w", encoding="utf-8") as matched_out, torch.no_grad():
        for index, (item, prefetched_h, prefetched_v) in prefetched_items(
                data, h_data, v_data, prefetch_workers):
            image_id = str(item["data_samples"].img_id)
            seen_image_ids.append(image_id)
            gt_boxes, gt_labels = gt(item)
            for gt_index in range(len(gt_boxes)):
                gts_by_class.setdefault(int(gt_labels[gt_index]), {}).setdefault(image_id, []).append(gt_boxes[gt_index])
            outs, samples, features = forward_once(model, item)
            feature_norms = regression_feature_norms(model.bbox_head, features)
            angle_loss_context = prepare_angle_loss_context(model.bbox_head, outs, samples)
            results = {k: predict_from_outs(model, outs, samples, k, feature_norms) for k in K_GRID}
            unpacked = {k: tensors(inst) for k, inst in results.items()}
            base_boxes, base_scores, base_labels, base_encoded, base_feature_norm = unpacked[1.0]
            base_sig = set_signature(base_boxes, base_scores, base_labels)

            h_boxes = v_boxes = torch.zeros((0, 5))
            h_labels = v_labels = torch.zeros((0,), dtype=torch.long)
            h_encoded = v_encoded = torch.zeros((0, coder.encode_size))
            h_map = v_map = {}
            if seed == 0:
                h_item, v_item = prefetched_h, prefetched_v
                if (str(h_item["data_samples"].img_id) != image_id
                        or str(v_item["data_samples"].img_id) != image_id):
                    raise RuntimeError(f"PSC TTA image-id mismatch at index={index}: {image_id}")
                h_out, h_samples, _ = forward_once(model, h_item)
                v_out, v_samples, _ = forward_once(model, v_item)
                h_boxes, _, h_labels, h_encoded, _ = tensors(
                    predict_from_outs(model, h_out, h_samples, 1.0, None))
                v_boxes, _, v_labels, v_encoded, _ = tensors(
                    predict_from_outs(model, v_out, v_samples, 1.0, None))
                height, width = item["data_samples"].metainfo["ori_shape"][:2]
                h_boxes = unflip(h_boxes, "horizontal", height, width)
                v_boxes = unflip(v_boxes, "vertical", height, width)
                h_map = cross_view_map(base_boxes, base_labels, h_boxes, h_labels)
                v_map = cross_view_map(base_boxes, base_labels, v_boxes, v_labels)

            base_matches = match(base_boxes, base_scores, base_labels, gt_boxes, gt_labels)
            base_match_map = {pred_index: (gt_index, iou) for pred_index, gt_index, iou in base_matches}
            for pred_index, (gt_index, match_iou) in base_match_map.items():
                vector = base_encoded[pred_index]
                target = coder.encode(gt_boxes[gt_index, 4:5].reshape(1, 1)).detach().cpu().float()[0]
                stats = phase_stats(vector, coder)
                decoded = float(coder.decode(vector.reshape(1, -1).cuda()).cpu()[0])
                gt_theta = float(gt_boxes[gt_index, 4])
                cc = angle_error_contract(*[float(x) for x in base_boxes[pred_index, 2:5]],
                                          *[float(x) for x in gt_boxes[gt_index, 2:5]])
                decoded_longside = canonical_longside_theta(
                    float(base_boxes[pred_index, 2]), float(base_boxes[pred_index, 3]), decoded)
                tta_angles = [decoded_longside]
                if pred_index in h_map:
                    h_index = h_map[pred_index]
                    h_decoded = -float(coder.decode(
                        h_encoded[h_index].reshape(1, -1).cuda()).cpu()[0])
                    tta_angles.append(canonical_longside_theta(
                        float(h_boxes[h_index, 2]), float(h_boxes[h_index, 3]), h_decoded))
                if pred_index in v_map:
                    v_index = v_map[pred_index]
                    v_decoded = -float(coder.decode(
                        v_encoded[v_index].reshape(1, -1).cuda()).cpu()[0])
                    tta_angles.append(canonical_longside_theta(
                        float(v_boxes[v_index, 2]), float(v_boxes[v_index, 3]), v_decoded))
                doubled = 2.0 * np.asarray(tta_angles)
                tta_var = (float(1.0 - math.hypot(float(np.cos(doubled).mean()), float(np.sin(doubled).mean())))
                           if len(tta_angles) >= 2 else None)
                long_theta = canonical_longside_theta(float(base_boxes[pred_index, 2]),
                                                      float(base_boxes[pred_index, 3]), decoded)
                boundary_distance = math.degrees(min(abs(long_theta + math.pi / 2), abs(math.pi / 2 - long_theta)))
                row = dict(
                    dataset=dataset, seed=seed, image_id=image_id, pred_id=pred_index, gt_id=gt_index,
                    **{"class": classes[int(base_labels[pred_index])]}, score=float(base_scores[pred_index]),
                    pred_box=[float(x) for x in base_boxes[pred_index]], gt_box=[float(x) for x in gt_boxes[gt_index]],
                    match_iou=match_iou, angle_error=float(cc["angle_error_canonical_longside"]),
                    aspect_ratio=max(float(gt_boxes[gt_index, 2]), float(gt_boxes[gt_index, 3])) /
                                 max(min(float(gt_boxes[gt_index, 2]), float(gt_boxes[gt_index, 3])), 1e-9),
                    size=float(gt_boxes[gt_index, 2] * gt_boxes[gt_index, 3]), encoded_vector=vector.tolist(),
                    encoded_target=target.tolist(), decoded_angle=decoded,
                    decoded_longside_angle=decoded_longside,
                    detection_score=float(base_scores[pred_index]), objectness=None,
                    objectness_available=False,
                    objectness_note="RetinaNet has no separate objectness branch; detection score is reported separately",
                    reg_feature_norm=float(base_feature_norm[pred_index]),
                    feature_norm_definition="L2 norm of the actual shared regression/angle-tower feature at the selected FPN location",
                    boundary_distance_deg=boundary_distance,
                    wrapping_condition=bool(boundary_distance < 10.0),
                    tta_phase_direction_circular_variance=tta_var, n_tta_phase_angles=len(tta_angles), **stats,
                )
                matched_out.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")

                for k in K_GRID:
                    scaled_vector = vector * k
                    decoded_k = float(coder.decode(scaled_vector.reshape(1, -1).cuda()).cpu()[0])
                    aggregates[k]["decoded_diff"].append(math.degrees(angle_periodic_diff(decoded, decoded_k)))
                    controlled_loss, controlled_radial, controlled_tangential, controlled_dloss_dk = \
                        loss_gradient(vector, target, k)
                    controlled_stats = phase_stats(scaled_vector, coder)
                    aggregates[k]["controlled_loss"].append(controlled_loss)
                    aggregates[k]["controlled_radial"].append(controlled_radial)
                    aggregates[k]["controlled_tangential"].append(controlled_tangential)
                    aggregates[k]["controlled_dloss_dk"].append(controlled_dloss_dk)
                    aggregates[k]["controlled_phase_mod_primary"].append(
                        controlled_stats["phase_mod_primary"])
                    aggregates[k]["controlled_phase_mod_secondary"].append(
                        controlled_stats["phase_mod_secondary"])

            for k in K_GRID:
                actual_loss, actual_radial, actual_tangential, actual_dloss_dk, actual_positive = \
                    actual_angle_loss_gradient(model.bbox_head, outs[2], angle_loss_context, k)
                aggregates[k]["actual_head_loss"].append(actual_loss)
                aggregates[k]["actual_head_radial"].append(actual_radial)
                aggregates[k]["actual_head_tangential"].append(actual_tangential)
                aggregates[k]["actual_head_dloss_dk"].append(actual_dloss_dk)
                aggregates[k]["actual_head_positive_anchors"].append(actual_positive)
                boxes, scores, labels, encoded, _ = unpacked[k]
                pickle.dump((image_id, boxes, scores, labels), streams[k], protocol=pickle.HIGHEST_PROTOCOL)
                aggregates[k]["n_pred"] += len(boxes)
                if set_signature(boxes, scores, labels) == base_sig:
                    aggregates[k]["exact_set"] += 1
                if len(boxes) == len(base_boxes) and torch.equal(labels, base_labels) and torch.allclose(scores, base_scores):
                    aggregates[k]["box_class_set_equal"] += 1
                for pred_index, gt_index, _ in match(boxes, scores, labels, gt_boxes, gt_labels):
                    target = coder.encode(gt_boxes[gt_index, 4:5].reshape(1, 1)).detach().cpu().float()[0]
                    loss, radial, tangential, dloss_dk = loss_gradient(encoded[pred_index], target, 1.0)
                    cc = angle_error_contract(*[float(x) for x in boxes[pred_index, 2:5]],
                                              *[float(x) for x in gt_boxes[gt_index, 2:5]])
                    stats = phase_stats(encoded[pred_index], coder)
                    aggregates[k]["loss"].append(loss)
                    aggregates[k]["radial"].append(radial)
                    aggregates[k]["tangential"].append(tangential)
                    aggregates[k]["dloss_dk"].append(dloss_dk)
                    aggregates[k]["angle_error"].append(float(cc["angle_error_canonical_longside"]))
                    aggregates[k]["phase_mod_primary"].append(stats["phase_mod_primary"])
                    aggregates[k]["phase_mod_secondary"].append(stats["phase_mod_secondary"])
                    aggregates[k]["n_match"] += 1
            if (index + 1) % 1000 == 0:
                log(dataset, seed, f"progress {index + 1}/{len(data)} minutes={(time.time() - started) / 60:.1f}")

    for stream in streams.values():
        stream.close()
    if len(set(seen_image_ids)) != len(data):
        raise RuntimeError(f"{run_id}: duplicate/missing image IDs in full-validation stream")
    n_gt = sum(len(rows) for by_image in gts_by_class.values() for rows in by_image.values())
    if n_gt != EXPECTED_GT[dataset]:
        raise RuntimeError(f"{run_id}: expected {EXPECTED_GT[dataset]} GT, got {n_gt}")
    os.replace(matched_tmp, matched_path)
    summary = []
    for k in K_GRID:
        ap = evaluate_stream(temp_paths[k], gts_by_class)
        ap50, ap75 = ap[0.5], ap[0.75]
        agg = aggregates[k]
        summary.append(dict(
            dataset=dataset, seed=seed, k=k, n_images=len(data), n_predictions=agg["n_pred"],
            n_matched=agg["n_match"], AP50=round(ap50, 6), AP75=round(ap75, 6),
            mean_angle_error_deg=round(float(np.mean(agg["angle_error"])), 8),
            median_angle_error_deg=round(float(np.median(agg["angle_error"])), 8),
            p95_angle_error_deg=round(float(np.percentile(agg["angle_error"], 95)), 8),
            mean_phase_mod_primary=round(float(np.mean(agg["phase_mod_primary"])), 8),
            mean_phase_mod_secondary=round(float(np.mean(agg["phase_mod_secondary"])), 8),
            mean_matched_phase_loss=round(float(np.mean(agg["loss"])), 8),
            mean_abs_radial_gradient=round(float(np.mean(agg["radial"])), 8),
            mean_tangential_gradient_norm=round(float(np.mean(agg["tangential"])), 8),
            mean_abs_dloss_dk=round(float(np.mean(agg["dloss_dk"])), 8),
            controlled_base_mean_phase_mod_primary=round(
                float(np.mean(agg["controlled_phase_mod_primary"])), 8),
            controlled_base_mean_phase_mod_secondary=round(
                float(np.mean(agg["controlled_phase_mod_secondary"])), 8),
            controlled_base_mean_phase_loss=round(float(np.mean(agg["controlled_loss"])), 8),
            controlled_base_mean_abs_radial_gradient=round(
                float(np.mean(agg["controlled_radial"])), 8),
            controlled_base_mean_tangential_gradient_norm=round(
                float(np.mean(agg["controlled_tangential"])), 8),
            controlled_base_mean_abs_dloss_dk=round(
                float(np.mean(agg["controlled_dloss_dk"])), 8),
            actual_head_mean_angle_loss=round(float(np.mean(agg["actual_head_loss"])), 8),
            actual_head_mean_abs_radial_gradient=round(
                float(np.mean(agg["actual_head_radial"])), 8),
            actual_head_mean_tangential_gradient_norm=round(
                float(np.mean(agg["actual_head_tangential"])), 8),
            actual_head_mean_abs_radial_gradient_wrt_base_z=round(
                float(k * np.mean(agg["actual_head_radial"])), 8),
            actual_head_mean_tangential_gradient_norm_wrt_base_z=round(
                float(k * np.mean(agg["actual_head_tangential"])), 8),
            actual_head_mean_abs_dloss_dk=round(
                float(np.mean(agg["actual_head_dloss_dk"])), 8),
            actual_head_mean_positive_anchors=round(
                float(np.mean(agg["actual_head_positive_anchors"])), 4),
            decoded_angle_median_diff_deg=round(float(np.median(agg["decoded_diff"])), 8),
            decoded_angle_p95_diff_deg=round(float(np.percentile(agg["decoded_diff"], 95)), 8),
            post_nms_exact_image_proportion=round(agg["exact_set"] / len(data), 8),
            post_nms_score_label_count_equal_proportion=round(agg["box_class_set_equal"] / len(data), 8),
        ))
        os.replace(temp_paths[k], postnms_paths[k])
    atomic_csv(summary_path, summary)

    postnms_artifacts = [dict(
        k=k, path=str(postnms_paths[k].relative_to(ROOT)),
        sha256=sha256(postnms_paths[k]), bytes=postnms_paths[k].stat().st_size,
        schema="pickle stream of (image_id, post-NMS boxes[N,5], scores[N], labels[N])")
        for k in K_GRID]
    manifest = dict(
        status="complete", schema_version="psc_phase1_radial_scaling_v2",
        run_id=run_id, dataset=dataset, seed=seed, k_grid=K_GRID, n_images=len(data), n_gt=n_gt,
        image_id_sha256=hashlib.sha256(
            "\n".join(sorted(seen_image_ids)).encode("utf-8")).hexdigest(),
        gt_path=str(GT_PATHS[dataset].relative_to(ROOT)), gt_sha256=sha256(GT_PATHS[dataset]),
        config_path=str(cfg_path), config_sha256=sha256(cfg_path), checkpoint_path=str(checkpoint),
        checkpoint_sha256=checkpoint_sha,
        k2_artifact_manifest_path=str(K2_ARTIFACT_MANIFEST.relative_to(ROOT)),
        k2_artifact_manifest_sha256=sha256(K2_ARTIFACT_MANIFEST),
        k2_eval_path=str(k2_eval_path.relative_to(ROOT)), k2_eval_sha256=sha256(k2_eval_path),
        summary_path=str(summary_path.relative_to(ROOT)),
        summary_sha256=sha256(summary_path), summary_bytes=summary_path.stat().st_size,
        matched_path=str(matched_path.relative_to(ROOT)), matched_sha256=sha256(matched_path),
        matched_bytes=matched_path.stat().st_size, matched_rows=sum(1 for _ in matched_path.open()),
        postnms_artifacts=postnms_artifacts,
        coder=dict(type=type(coder).__name__, dual_freq=bool(coder.dual_freq),
                   num_step=int(coder.num_step), threshold_mod=float(coder.thr_mod),
                   encode_size=int(coder.encode_size), angle_version=str(coder.angle_version)),
        loss_intervention=(
            "configured anchor-assigned bbox_head.loss_angle with frozen assignment; "
            "autograd dL/dz_prime and chain-rule dL/dk; post-NMS matched L1 separately labelled diagnostic"),
        actual_head_loss_gt_coordinate_space="network_input_after_validation_scale_factor",
        actual_head_fields_authoritative=True,
        objectness_available=False,
        feature_norm_definition=(
            "L2 norm of actual shared regression/angle-tower feature aligned through post-NMS"),
        tta_phase_direction=(seed == 0), no_training=True,
        generation_command=f"CUDA_VISIBLE_DEVICES=<gpu> python scripts/m069_psc_phase1_forward.py {dataset} {seed}",
        completed_at=time.strftime("%F %T %z"), elapsed_seconds=round(time.time() - started, 3),
    )
    atomic_json(manifest_path, manifest)
    log(dataset, seed, f"DONE images={len(data)} matched={manifest['matched_rows']} summary_sha={manifest['summary_sha256']}")


def main():
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
