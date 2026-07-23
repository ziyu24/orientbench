#!/usr/bin/env python3
"""Recover FAIR1M frozen PSC post-NMS phase vectors and verify M4 identity."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
BROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts"), str(ROOT / "top_journal_v3_reaudit_055")]

import orientbench_ext.instrumented_heads  # noqa: F401,E402
from mmengine.config import Config  # noqa: E402
from mmengine.registry import init_default_scope  # noqa: E402
from mmengine.runner import load_checkpoint  # noqa: E402
from mmrotate.registry import DATASETS, MODELS, TASK_UTILS  # noqa: E402
from orientbench.metrics.angle_contract import angle_error_contract  # noqa: E402

init_default_scope("mmrotate")
IOU = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def greedy_matches(pb, ps, pl, gb, gl, threshold=0.5):
    matches = {}
    labels = torch.unique(torch.cat([pl, gl]) if pl.numel() and gl.numel() else (pl if pl.numel() else gl))
    for cls in labels.tolist():
        pidx = torch.where(pl == int(cls))[0]; gidx = torch.where(gl == int(cls))[0]
        if not pidx.numel() or not gidx.numel():
            continue
        overlaps = IOU(pb[pidx].cuda(), gb[gidx].cuda()).cpu()
        used = set()
        for local_p in torch.argsort(ps[pidx], descending=True).tolist():
            candidates = [(float(overlaps[local_p, j]), j) for j in range(gidx.numel()) if j not in used]
            if not candidates:
                continue
            best_iou, local_g = max(candidates)
            if best_iou >= threshold:
                used.add(local_g); matches[int(pidx[local_p])] = int(gidx[local_g])
    return matches


def periodic_diff(a, b):
    d = abs(float(a) - float(b)) % math.pi
    return min(d, math.pi - d)


def phase_stats(vector, coder):
    ns = int(coder.num_step)
    cs = coder.coef_sin.detach().cpu().numpy().astype(float)
    cc = coder.coef_cos.detach().cpu().numpy().astype(float)
    first, second = vector[:ns], vector[ns:2 * ns]
    p1s, p1c = float(first @ cs), float(first @ cc)
    p2s, p2c = float(second @ cs), float(second @ cc)
    phase1 = -math.atan2(p1s, p1c); phase2 = -math.atan2(p2s, p2c) / 2.0
    c0 = phase2; c1 = ((phase2 + math.pi + math.pi) % (2 * math.pi)) - math.pi
    a0, a1 = math.cos(phase1 - c0), math.cos(phase1 - c1)
    chosen = c1 if a1 > a0 else c0
    return {
        "phase_mod_primary": p1c * p1c + p1s * p1s,
        "phase_mod_secondary": p2c * p2c + p2s * p2s,
        "phase_angle_primary": phase1,
        "phase_angle_secondary": phase2,
        "multi_frequency_disagreement_deg": math.degrees(periodic_diff(phase1 / 2.0, chosen / 2.0)),
        "unwrap_candidate_energy_gap": abs(a0 - a1),
        "phase_direction_margin": abs(a0 - a1) * math.sqrt(max(p2c * p2c + p2s * p2s, 0.0)),
        "angle_vector_norm": float(np.linalg.norm(vector)),
        "candidate_index": int(a1 > a0),
    }


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--seed", type=int, choices=(0, 1, 2), required=True)
    args = ap.parse_args(); seed = args.seed
    cfg_path = ROOT / "configs/m4_third_dataset_070/fair1m_psc.py"
    checkpoint = ROOT / f"outputs/persistent_artifacts/m4_third_dataset_070/checkpoints/M4_070_final__PSC__FAIR1M__seed{seed}.pth"
    reference_npz = ROOT / f"outputs/persistent_artifacts/m4_third_dataset_070/eval/M4_070_final__PSC__FAIR1M__seed{seed}_matched.npz"
    reference_json = ROOT / f"outputs/persistent_artifacts/m4_third_dataset_070/eval/M4_070_final__PSC__FAIR1M__seed{seed}.json"
    out_dir = BROOT / f"artifacts/b3_fair1m/seed{seed}"; out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "matched_phase.jsonl.gz"; manifest_path = out_dir / "manifest.json"
    if out.is_file() and manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("status") == "complete" and manifest.get("output_sha256") == sha256(out):
            return 0
    cfg = Config.fromfile(str(cfg_path)); cfg.model.bbox_head.type = "InstrumentedAngleBranchRetinaHead"
    model = MODELS.build(cfg.model); load_checkpoint(model, str(checkpoint), map_location="cpu")
    model.eval().cuda(); coder = model.bbox_head.angle_coder
    dataset = DATASETS.build(cfg.val_dataloader.dataset); ref = np.load(reference_npz)
    collected = {k: [] for k in ref.files}; tmp = out.with_suffix(out.suffix + ".tmp")
    rows = 0; started = time.time()
    with gzip.open(tmp, "wt", encoding="utf-8", compresslevel=5) as f, torch.no_grad():
        for image_index in range(len(dataset)):
            item = dataset[image_index]; sample = item["data_samples"]; gt = sample.gt_instances
            gb = (gt.bboxes.tensor if hasattr(gt.bboxes, "tensor") else gt.bboxes).cpu(); gl = gt.labels.cpu()
            prepared = model.data_preprocessor(dict(inputs=[item["inputs"].cuda()], data_samples=[sample.cuda()]), False)
            pred = model.predict(prepared["inputs"], prepared["data_samples"])[0].pred_instances
            pb = (pred.bboxes.tensor if hasattr(pred.bboxes, "tensor") else pred.bboxes).detach().cpu()
            ps = pred.scores.detach().cpu(); pl = pred.labels.detach().cpu(); enc = pred.angle_encoded.detach().cpu().float().numpy()
            matches = greedy_matches(pb, ps, pl, gb, gl)
            for pred_idx, gt_idx in matches.items():
                wp, hp, tp = map(float, pb[pred_idx, 2:5]); wg, hg, tg = map(float, gb[gt_idx, 2:5])
                contract = angle_error_contract(wp, hp, tp, wg, hg, tg); error = float(contract["angle_error_canonical_longside"])
                if not math.isfinite(error):
                    continue
                ar = max(wg, hg) / max(min(wg, hg), 1e-9); size = wg * hg
                vec = enc[pred_idx].astype(float); stats = phase_stats(vec, coder)
                native = stats["phase_mod_primary"]
                severe = float(ref["severe"][rows]) if rows < len(ref["severe"]) else float("nan")
                values = {"score": float(ps[pred_idx]), "native": native, "error": error, "ar": ar,
                          "size": size, "class_id": int(gl[gt_idx]), "image_index": image_index, "severe": severe}
                for k, v in values.items(): collected[k].append(v)
                row = {
                    "dataset": "FAIR1M-v1.0", "seed": seed, "image_id": str(sample.img_id),
                    "image_index": image_index, "pred_id": pred_idx, "gt_id": gt_idx,
                    "class": int(gl[gt_idx]), "score": float(ps[pred_idx]),
                    "pred_box": [float(x) for x in pb[pred_idx]], "gt_box": [float(x) for x in gb[gt_idx]],
                    "angle_error": error, "aspect_ratio": ar, "size": size,
                    "encoded_vector": vec.tolist(), "decoded_angle": tp,
                    "detection_score": float(ps[pred_idx]), "objectness": None,
                    "objectness_available": False, "objectness_note": "RetinaNet has no separate objectness branch",
                    "reg_feature_norm": None, "feature_norm_definition": "unavailable in frozen FAIR1M dump",
                    "boundary_distance_deg": min(abs(((math.degrees(tp) + 90.0) % 180.0) - 90.0 + 90.0),
                                                 abs(90.0 - (((math.degrees(tp) + 90.0) % 180.0) - 90.0))),
                    "wrapping_condition": bool(abs(abs(((math.degrees(tp) + 90.0) % 180.0) - 90.0) - 90.0) < 10.0),
                    **stats,
                }
                f.write(json.dumps(row, separators=(",", ":")) + "\n"); rows += 1
            if (image_index + 1) % 250 == 0:
                print(f"FAIR1M_PHASE_DUMP seed={seed} {image_index + 1}/{len(dataset)}", flush=True)
    if rows != len(ref["error"]):
        tmp.unlink(missing_ok=True); raise RuntimeError(f"row mismatch {rows} != {len(ref['error'])}")
    checks = {}
    for k in ref.files:
        got = np.asarray(collected[k], dtype=ref[k].dtype)
        checks[k] = bool(np.array_equal(got, ref[k]) if np.issubdtype(ref[k].dtype, np.integer)
                         else np.allclose(got, ref[k], rtol=1e-6, atol=1e-6, equal_nan=True))
    if not all(checks.values()):
        tmp.unlink(missing_ok=True); raise RuntimeError(f"reference identity mismatch: {checks}")
    os.replace(tmp, out)
    payload = {
        "status": "complete", "schema_version": "b3_fair1m_phase_dump_v1", "dataset": "FAIR1M-v1.0",
        "seed": seed, "images": len(dataset), "matched_rows": rows, "checkpoint": str(checkpoint.relative_to(ROOT)),
        "checkpoint_sha256": sha256(checkpoint), "config": str(cfg_path.relative_to(ROOT)), "config_sha256": sha256(cfg_path),
        "reference_npz": str(reference_npz.relative_to(ROOT)), "reference_npz_sha256": sha256(reference_npz),
        "reference_eval_json": str(reference_json.relative_to(ROOT)), "reference_eval_json_sha256": sha256(reference_json),
        "identity_checks": checks, "output": str(out.relative_to(ROOT)), "output_sha256": sha256(out),
        "no_training": True, "formula_tuning": False, "completed_at": time.strftime("%F %T %z"),
        "elapsed_seconds": round(time.time() - started, 3),
    }
    manifest_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
