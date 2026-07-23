#!/usr/bin/env python3
"""Dump post-NMS PSC vectors and full-evaluator inputs for the frozen B4 host."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import torch
from mmengine.config import Config
from mmengine.registry import init_default_scope
from mmengine.runner import Runner, load_checkpoint
from mmrotate.evaluation.metrics import DOTAMetric
from mmrotate.registry import MODELS, TASK_UTILS

ROOT = Path(__file__).resolve().parents[3]
BROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BROOT / "scripts"))
import b4_instrumented_fcos  # noqa: E402,F401

from orientbench.metrics.angle_contract import angle_error_contract  # noqa: E402

init_default_scope("mmrotate")
IOU = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def periodic_diff(a: float, b: float) -> float:
    delta = abs(a - b) % math.pi
    return min(delta, math.pi - delta)


def phase_stats(vector: np.ndarray, coder) -> dict:
    ns = int(coder.num_step)
    cs = coder.coef_sin.detach().cpu().numpy().astype(float)
    cc = coder.coef_cos.detach().cpu().numpy().astype(float)
    first, second = vector[:ns], vector[ns:2 * ns]
    p1s, p1c = float(first @ cs), float(first @ cc)
    p2s, p2c = float(second @ cs), float(second @ cc)
    p1 = -math.atan2(p1s, p1c)
    p2 = -math.atan2(p2s, p2c) / 2.0
    c0, c1 = p2, p2 % (2 * math.pi) - math.pi
    a0, a1 = math.cos(p1 - c0), math.cos(p1 - c1)
    chosen = c1 if a1 > a0 else c0
    mod1, mod2 = p1c * p1c + p1s * p1s, p2c * p2c + p2s * p2s
    switch_distance = abs(math.degrees(math.acos(max(-1.0, min(1.0, math.cos(p1 - p2))))) - 90.0)
    return {
        "phase_mod_primary": mod1,
        "phase_mod_secondary": mod2,
        "phase_angle_primary": p1,
        "phase_angle_secondary": p2,
        "multi_frequency_disagreement_deg": math.degrees(
            periodic_diff(p1 / 2.0, chosen / 2.0)),
        "unwrap_candidate_energy_gap": abs(a0 - a1),
        "phase_direction_margin": abs(a0 - a1) * math.sqrt(max(mod2, 0.0)),
        "candidate_index": int(a1 > a0),
        "boundary_distance_deg": switch_distance,
    }


def greedy_matches(pb, ps, pl, gb, gl, threshold=0.5):
    matches = {}
    labels = torch.unique(torch.cat([pl, gl]))
    for cls in labels.tolist():
        pi, gi = torch.where(pl == cls)[0], torch.where(gl == cls)[0]
        if not pi.numel() or not gi.numel():
            continue
        overlaps = IOU(pb[pi].cuda(), gb[gi].cuda()).cpu()
        used = set()
        for lp in torch.argsort(ps[pi], descending=True).tolist():
            candidates = [
                (float(overlaps[lp, j]), j)
                for j in range(gi.numel()) if j not in used]
            if candidates:
                iou, lg = max(candidates)
                if iou >= threshold:
                    used.add(lg)
                    matches[int(pi[lp])] = int(gi[lg])
    return matches


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, choices=(0, 1, 2), required=True)
    parser.add_argument("--checkpoint", required=True)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    seed = args.seed
    cfg_path = BROOT / f"configs/b4_external_variant/seed{seed}.py"
    checkpoint = Path(args.checkpoint).resolve()
    out_dir = BROOT / f"artifacts/b4_external/seed{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_path = out_dir / "matched_phase.jsonl.gz"
    eval_path = out_dir / "full_evaluator_inputs.pkl.gz"
    manifest_path = out_dir / "manifest.json"

    cfg = Config.fromfile(str(cfg_path))
    cfg.model.bbox_head.type = "B4InstrumentedRotatedFCOSHead"
    model = MODELS.build(cfg.model)
    load_checkpoint(model, str(checkpoint), map_location="cpu")
    model.eval().to(args.device)
    coder = model.bbox_head.angle_coder
    dataloader = Runner.build_dataloader(cfg.test_dataloader)
    metric = DOTAMetric(iou_thrs=[0.5, 0.75], metric="mAP")
    metric.dataset_meta = dataloader.dataset.metainfo

    tmp_rows = rows_path.with_suffix(rows_path.suffix + ".tmp")
    prediction_count = matched_count = 0
    intervention_inputs = []
    class_ids = set()
    started = time.time()
    with gzip.open(tmp_rows, "wt", encoding="utf-8", compresslevel=5) as stream:
        with torch.no_grad():
            for index, batch in enumerate(dataloader):
                results = model.test_step(batch)
                metric.process(batch, [sample.to_dict() for sample in results])
                for sample in results:
                    pred, gt = sample.pred_instances, sample.gt_instances
                    pb = (pred.bboxes.tensor if hasattr(pred.bboxes, "tensor") else pred.bboxes).detach().cpu()
                    ps, pl = pred.scores.detach().cpu(), pred.labels.detach().cpu()
                    encoded = pred.angle_encoded.detach().cpu().float().numpy()
                    gb = (gt.bboxes.tensor if hasattr(gt.bboxes, "tensor") else gt.bboxes).detach().cpu()
                    gl = gt.labels.detach().cpu()
                    prediction_count += len(pb)
                    class_ids.update(map(int, pl.tolist()))
                    intervention_inputs.append({
                        "image_id": str(sample.img_id),
                        "boxes": pb.numpy(),
                        "scores": ps.numpy(),
                        "labels": pl.numpy(),
                        "encoded": encoded,
                    })
                    matches = greedy_matches(pb, ps, pl, gb, gl)
                    image_id = str(sample.img_id)
                    mother_scene = image_id.split("__", 1)[0]
                    for pred_idx, gt_idx in matches.items():
                        wp, hp, tp = map(float, pb[pred_idx, 2:5])
                        wg, hg, tg = map(float, gb[gt_idx, 2:5])
                        contract = angle_error_contract(wp, hp, tp, wg, hg, tg)
                        error = float(contract["angle_error_canonical_longside"])
                        ar = max(wg, hg) / max(min(wg, hg), 1e-9)
                        if not math.isfinite(error) or ar < 2.1:
                            continue
                        vector = encoded[pred_idx].astype(float)
                        stats = phase_stats(vector, coder)
                        row = {
                            "dataset": "DOTA-v1.0",
                            "host": "RotatedFCOS",
                            "seed": seed,
                            "image_id": image_id,
                            "mother_scene_id": mother_scene,
                            "pred_id": pred_idx,
                            "gt_id": gt_idx,
                            "class": int(gl[gt_idx]),
                            "detection_score": float(ps[pred_idx]),
                            "pred_box": [float(v) for v in pb[pred_idx]],
                            "gt_box": [float(v) for v in gb[gt_idx]],
                            "angle_error": error,
                            "aspect_ratio": ar,
                            "size": wg * hg,
                            "encoded_vector": vector.tolist(),
                            "decoded_angle": tp,
                            "objectness": float(pred.score_factors[pred_idx])
                            if "score_factors" in pred else None,
                            "feature_norm": None,
                            "tta_phase_direction_circular_variance": None,
                            **stats,
                        }
                        stream.write(json.dumps(row, separators=(",", ":")) + "\n")
                        matched_count += 1
                if (index + 1) % 250 == 0:
                    print(f"B4_DUMP seed={seed} {index + 1}/{len(dataloader)}", flush=True)
    os.replace(tmp_rows, rows_path)

    metrics = metric.compute_metrics(metric.results)
    with gzip.open(eval_path, "wb", compresslevel=3) as handle:
        pickle.dump(
            {"metric_results": metric.results,
             "intervention_inputs": intervention_inputs},
            handle, protocol=pickle.HIGHEST_PROTOCOL)
    manifest = {
        "schema_version": "b4_external_variant_dump_v1",
        "status": "complete",
        "dataset": "DOTA-v1.0",
        "host": "RotatedFCOS",
        "seed": seed,
        "checkpoint": str(checkpoint),
        "checkpoint_sha256": sha256(checkpoint),
        "config": str(cfg_path.relative_to(ROOT)),
        "config_sha256": sha256(cfg_path),
        "images": len(dataloader.dataset),
        "prediction_count": prediction_count,
        "matched_ar21_count": matched_count,
        "class_coverage": len(class_ids),
        "AP50": float(metrics["AP50"]),
        "AP75": float(metrics["AP75"]),
        "rows": str(rows_path.relative_to(ROOT)),
        "rows_sha256": sha256(rows_path),
        "full_evaluator_inputs": str(eval_path.relative_to(ROOT)),
        "full_evaluator_inputs_sha256": sha256(eval_path),
        "mother_scene_source": "tile ID prefix before '__'",
        "formula_tuning": False,
        "elapsed_seconds": round(time.time() - started, 3),
        "completed_at": time.strftime("%F %T %z"),
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
