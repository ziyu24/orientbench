#!/usr/bin/env python3
"""Full FAIR1M evaluation for the frozen Command-070 PSC/CSL/DCL extension."""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "top_journal_v3_reaudit_055")]

import orientbench_ext.instrumented_heads  # noqa: F401,E402
from mmengine.config import Config  # noqa: E402
from mmengine.registry import init_default_scope  # noqa: E402
from mmengine.runner import load_checkpoint  # noqa: E402
from mmrotate.registry import DATASETS, MODELS, TASK_UTILS  # noqa: E402

from m069_common import boot_nrc_ci, delta_theta_075  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract  # noqa: E402
from orientbench.metrics.nrc_auc import nrc_auc  # noqa: E402
from orientbench.metrics.risk_coverage import aurc, risk_at_coverage  # noqa: E402

init_default_scope("mmrotate")
IOU = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))
OUT = ROOT / "outputs/persistent_artifacts/m4_third_dataset_070/eval"
OUT.mkdir(parents=True, exist_ok=True)


def native_score(head: str, encoded: torch.Tensor, coder) -> torch.Tensor:
    encoded = encoded.float()
    if head == "PSC":
        ns = coder.num_step
        cs = coder.coef_sin.to(encoded)
        cc = coder.coef_cos.to(encoded)
        return (encoded[:, :ns] * cc).sum(-1).square() + (encoded[:, :ns] * cs).sum(-1).square()
    if head == "CSL":
        prob = encoded.softmax(-1)
        top2 = prob.topk(2, dim=-1).values
        return top2[:, 0] - top2[:, 1]
    if head == "DCL":
        prob = encoded.sigmoid()
        return (2.0 * prob - 1.0).abs().mean(-1)
    raise ValueError(head)


def voc11(scores: np.ndarray, tp: np.ndarray, n_gt: int) -> float:
    if n_gt <= 0:
        return float("nan")
    order = np.argsort(-scores, kind="stable")
    tp = tp[order].astype(float)
    ctp = np.cumsum(tp)
    cfp = np.cumsum(1.0 - tp)
    rec = ctp / n_gt
    precision = ctp / np.maximum(ctp + cfp, 1e-12)
    return float(np.mean([precision[rec >= level].max() if np.any(rec >= level) else 0.0
                          for level in np.linspace(0.0, 1.0, 11)]))


def greedy_matches(pb: torch.Tensor, ps: torch.Tensor, pl: torch.Tensor,
                   gb: torch.Tensor, gl: torch.Tensor, threshold: float) -> dict[int, int]:
    matches: dict[int, int] = {}
    for cls in torch.unique(torch.cat([pl, gl]) if pl.numel() and gl.numel()
                            else (pl if pl.numel() else gl)).tolist():
        pidx = torch.where(pl == int(cls))[0]
        gidx = torch.where(gl == int(cls))[0]
        if not pidx.numel() or not gidx.numel():
            continue
        overlaps = IOU(pb[pidx].cuda(), gb[gidx].cuda()).cpu()
        used: set[int] = set()
        for local_p in torch.argsort(ps[pidx], descending=True).tolist():
            candidates = [(float(overlaps[local_p, j]), j) for j in range(gidx.numel()) if j not in used]
            if not candidates:
                continue
            best_iou, local_g = max(candidates)
            if best_iou >= threshold:
                used.add(local_g)
                matches[int(pidx[local_p])] = int(gidx[local_g])
    return matches


def finite(value: float) -> float | None:
    return float(value) if math.isfinite(float(value)) else None


def metric_block(score: np.ndarray, error: np.ndarray, severe: np.ndarray,
                 image_index: np.ndarray, mask: np.ndarray, bootstrap: bool) -> dict:
    score = score[mask]
    error = error[mask]
    severe = severe[mask]
    image_index = image_index[mask]
    if len(score) < 50:
        return {"n": int(len(score)), "status": "INSUFFICIENT"}
    angle_nrc = nrc_auc(score, error)["nrc_auc"]
    severe_nrc = nrc_auc(score, severe)["nrc_auc"]
    block = {
        "n": int(len(score)),
        "NRC_native": finite(angle_nrc),
        "geometry_severe_NRC_native": finite(severe_nrc),
        "AURC_native": finite(aurc(score, error)),
        "Risk70_native": finite(risk_at_coverage(score, error, 0.70)),
        "Risk90_native": finite(risk_at_coverage(score, error, 0.90)),
        "mean_angle_error": finite(np.mean(error)),
        "geometry_severe_rate": finite(np.mean(severe)),
        "status": "COMPLETE",
    }
    if bootstrap:
        block["NRC_native_image_cluster_CI"] = list(boot_nrc_ci(image_index, score, error, n=800))
        block["geometry_NRC_image_cluster_CI"] = list(boot_nrc_ci(image_index, score, severe, n=800))
        block["bootstrap_unit"] = "complete_evaluation_image"
        block["bootstrap_replicates"] = 800
    return block


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--head", choices=["PSC", "CSL", "DCL"], required=True)
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--max-images", type=int, default=0)
    args = parser.parse_args()

    cfg = Config.fromfile(args.config)
    cfg.model.bbox_head.type = "InstrumentedAngleBranchRetinaHead"
    model = MODELS.build(cfg.model)
    load_checkpoint(model, args.checkpoint, map_location="cpu")
    model.eval().cuda()
    coder = model.bbox_head.angle_coder
    dataset = DATASETS.build(cfg.val_dataloader.dataset)
    n_images = min(len(dataset), args.max_images) if args.max_images else len(dataset)

    ap_scores: dict[int, list[float]] = {}
    ap_tp50: dict[int, list[int]] = {}
    ap_tp75: dict[int, list[int]] = {}
    gt_count: dict[int, int] = {}
    matched = {key: [] for key in ("score", "native", "error", "ar", "size", "class_id",
                                    "image_index", "severe")}
    total_predictions = 0

    with torch.no_grad():
        for image_index in range(n_images):
            item = dataset[image_index]
            sample = item["data_samples"]
            gt = sample.gt_instances
            gb = (gt.bboxes.tensor if hasattr(gt.bboxes, "tensor") else gt.bboxes).cpu()
            gl = gt.labels.cpu()
            prepared = model.data_preprocessor(
                dict(inputs=[item["inputs"].cuda()], data_samples=[sample.cuda()]), False)
            prediction = model.predict(prepared["inputs"], prepared["data_samples"])[0].pred_instances
            pb = (prediction.bboxes.tensor if hasattr(prediction.bboxes, "tensor") else prediction.bboxes).cpu()
            ps = prediction.scores.detach().cpu()
            pl = prediction.labels.detach().cpu()
            if not hasattr(prediction, "angle_encoded"):
                raise RuntimeError(f"{args.run_id}: instrumented native encoding missing")
            native = native_score(args.head, prediction.angle_encoded.detach(), coder).cpu()
            if native.numel() != ps.numel() or not torch.isfinite(native).all():
                raise RuntimeError(f"{args.run_id}: invalid native signal")
            total_predictions += int(ps.numel())
            for cls in gl.tolist():
                gt_count[int(cls)] = gt_count.get(int(cls), 0) + 1
            m50 = greedy_matches(pb, ps, pl, gb, gl, 0.50)
            m75 = greedy_matches(pb, ps, pl, gb, gl, 0.75)
            for pred_idx in range(ps.numel()):
                cls = int(pl[pred_idx])
                ap_scores.setdefault(cls, []).append(float(ps[pred_idx]))
                ap_tp50.setdefault(cls, []).append(int(pred_idx in m50))
                ap_tp75.setdefault(cls, []).append(int(pred_idx in m75))
            for pred_idx, gt_idx in m50.items():
                wp, hp, tp = (float(x) for x in pb[pred_idx, 2:5])
                wg, hg, tg = (float(x) for x in gb[gt_idx, 2:5])
                contract = angle_error_contract(wp, hp, tp, wg, hg, tg)
                error = float(contract["angle_error_canonical_longside"])
                if not math.isfinite(error):
                    continue
                aspect_ratio = max(wg, hg) / max(min(wg, hg), 1e-9)
                severe = float(error > delta_theta_075(aspect_ratio))
                matched["score"].append(float(ps[pred_idx]))
                matched["native"].append(float(native[pred_idx]))
                matched["error"].append(error)
                matched["ar"].append(aspect_ratio)
                matched["size"].append(wg * hg)
                matched["class_id"].append(int(gl[gt_idx]))
                matched["image_index"].append(image_index)
                matched["severe"].append(severe)
            if (image_index + 1) % 250 == 0:
                print(f"EVAL_PROGRESS {args.run_id} {image_index + 1}/{n_images}", flush=True)

    if total_predictions == 0 or not matched["error"]:
        raise RuntimeError(f"{args.run_id}: empty predictions or matches")
    ap50 = []
    ap75 = []
    for cls, n_gt in gt_count.items():
        scores = np.asarray(ap_scores.get(cls, []), dtype=float)
        tp50 = np.asarray(ap_tp50.get(cls, []), dtype=np.uint8)
        tp75 = np.asarray(ap_tp75.get(cls, []), dtype=np.uint8)
        ap50.append(voc11(scores, tp50, n_gt))
        ap75.append(voc11(scores, tp75, n_gt))

    arrays = {key: np.asarray(value) for key, value in matched.items()}
    valid = np.isfinite(arrays["native"]) & np.isfinite(arrays["error"])
    result = {
        "run_id": args.run_id,
        "head": args.head,
        "dataset": "FAIR1M-v1.0",
        "split": "train_80->val_20",
        "images": n_images,
        "gt_instances": int(sum(gt_count.values())),
        "predictions": total_predictions,
        "matched_instances": int(valid.sum()),
        "AP50": finite(np.nanmean(ap50)),
        "AP75": finite(np.nanmean(ap75)),
        "mean_angle_error_all_matched": finite(np.mean(arrays["error"][valid])),
        "native_signal": {"PSC": "phase_mod", "CSL": "softmax_margin", "DCL": "bit_margin"}[args.head],
        "evaluation_status": "COMPLETE",
    }
    for label, threshold in (("main_ar2.1", 2.1), ("sensitivity_ar1.6", 1.6),
                             ("sensitivity_ar1.3", 1.3)):
        mask = valid & (arrays["ar"] >= threshold)
        block = metric_block(arrays["native"], arrays["error"], arrays["severe"],
                             arrays["image_index"], mask, bootstrap=(not args.pilot))
        block["retained_count"] = int(mask.sum())
        block["retained_ratio"] = float(mask.sum() / max(int(valid.sum()), 1))
        result[label] = block

    json_path = OUT / f"{args.run_id}.json"
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.pilot:
        np.savez_compressed(OUT / f"{args.run_id}_matched.npz", **arrays)
    print(f"M4_070_EVAL_DONE {args.run_id} AP50={result['AP50']:.4f} AP75={result['AP75']:.4f} "
          f"NRC={result['main_ar2.1'].get('NRC_native')}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
