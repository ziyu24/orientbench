#!/usr/bin/env python3
"""Independent HRSC2016 confirmation for the frozen r014 EQS protocol."""
from __future__ import annotations

import csv
import hashlib
import importlib.util
import json
import math
import pickle
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from mmcv.ops import box_iou_rotated
from mmrotate.evaluation import eval_rbbox_map


ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r014"
REPORT = ROOT / "p3_selector/deployable_proxy_r014/reports/hrsc_results_r014.csv"
HRSC = Path("/home/rspip/cqc/data/dataset/HRSC2016")
CORE_SCRIPT = Path(__file__).with_name("evaluate_eqs_r014.py")


def load_core():
    spec = importlib.util.spec_from_file_location("r014_core", CORE_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_gt(image_id: str) -> np.ndarray:
    root = ET.parse(HRSC / "annfiles" / f"{image_id}.xml").getroot()
    rows = []
    for obj in root.findall("HRSC_Objects/HRSC_Object"):
        rows.append([float(obj.find(key).text) for key in
                     ("mbox_cx", "mbox_cy", "mbox_w", "mbox_h", "mbox_ang")])
    return np.asarray(rows, dtype=np.float32).reshape(-1, 5)


def le90_deg(a: float, b: float) -> float:
    delta = abs((a - b) * 180.0 / math.pi) % 180.0
    return min(delta, 180.0 - delta)


def official_ap(records: list[dict]) -> tuple[float, float, int]:
    detections, annotations = [], []
    gt_total = 0
    for record in records:
        pred = record["pred_instances"]
        boxes = pred["bboxes"].detach().cpu().numpy().astype(np.float32)
        scores = pred["scores"].detach().cpu().numpy().astype(np.float32)
        labels = pred["labels"].detach().cpu().numpy()
        detections.append([np.concatenate((boxes[labels == 0], scores[labels == 0, None]), axis=1)])
        gt = parse_gt(str(record["img_id"]))
        gt_total += len(gt)
        annotations.append({
            "bboxes": gt, "labels": np.zeros(len(gt), dtype=np.int64),
            "bboxes_ignore": np.empty((0, 5), dtype=np.float32),
            "labels_ignore": np.empty((0,), dtype=np.int64),
        })
    ap50, _ = eval_rbbox_map(detections, annotations, iou_thr=0.5,
                             use_07_metric=True, nproc=1, logger="silent")
    ap75, _ = eval_rbbox_map(detections, annotations, iou_thr=0.75,
                             use_07_metric=True, nproc=1, logger="silent")
    return float(ap50), float(ap75), gt_total


def attach_labels(core, records: list[dict]) -> pd.DataFrame:
    rows = []
    for record in records:
        image_id = str(record["img_id"])
        pred = record["pred_instances"]
        boxes = pred["bboxes"].detach().cpu().float()
        scores = pred["scores"].detach().cpu().numpy()
        labels = pred["labels"].detach().cpu().numpy()
        gt = parse_gt(image_id)
        if len(boxes) == 0 or len(gt) == 0:
            continue
        overlap = box_iou_rotated(boxes, torch.from_numpy(gt)).cpu().numpy()
        used = set()
        for pred_id in np.argsort(-scores):
            if labels[pred_id] != 0:
                continue
            candidates = np.argsort(-overlap[pred_id])
            gt_id = next((int(index) for index in candidates
                          if index not in used and overlap[pred_id, index] >= 0.5), None)
            if gt_id is None:
                continue
            used.add(gt_id)
            width, height = float(gt[gt_id, 2]), float(gt[gt_id, 3])
            aspect_ratio = max(width, height) / max(min(width, height), 1e-6)
            if aspect_ratio < 2.1:
                continue
            angle = le90_deg(float(boxes[pred_id, 4]), float(gt[gt_id, 4]))
            risk = min(angle / max(float(core._DTH(aspect_ratio)), 1.0), 3.0)
            rows.append({"image_id": image_id, "pred_id": int(pred_id),
                         "cluster": image_id, "angle_error": angle,
                         "gt_ar": aspect_ratio, "risk": risk})
    return pd.DataFrame(rows)


def main() -> None:
    core = load_core()
    raw = RUNTIME / "raw/hrsc_lsknet/identity.pkl"
    feature_path = RUNTIME / "features/H.parquet"
    registry_path = RUNTIME / "hrsc_forward_registry.json"
    if not all(path.is_file() for path in (raw, feature_path, registry_path)):
        raise FileNotFoundError("HRSC identity/features/registry are incomplete")
    with raw.open("rb") as handle:
        records = sorted(pickle.load(handle), key=lambda row: str(row["img_id"]))
    if len(records) != 453 or len({str(row["img_id"]) for row in records}) != 453:
        raise RuntimeError("HRSC frozen test universe is not 453 unique images")

    # Fit once using all Core source D_cal-fit labels.  HRSC labels are not read
    # until model, scores, and their hashes have been sealed below.
    source_parts = []
    for dataset in core.DATASETS:
        frame = core.source_data(dataset, "D_cal-fit").copy()
        source_parts.append(frame)
    source = pd.concat(source_parts, ignore_index=True)
    models = core.fit_models(source)
    features = pd.read_parquet(feature_path)
    scores = core.score_frame(features, models)
    score_path = RUNTIME / "scores/hrsc_lsknet.parquet"
    score_path.parent.mkdir(parents=True, exist_ok=True)
    scores.to_parquet(score_path, compression="zstd", index=False)
    seal = {
        "schema": "r014_hrsc_prelabel_seal_v1",
        "source_datasets": list(core.DATASETS), "source_role": "D_cal-fit",
        "source_dataset_weight": "equal_1_over_3",
        "feature_sha256": sha256(feature_path), "score_sha256": sha256(score_path),
        "raw_sha256": sha256(raw), "hrsc_labels_accessed_before_seal": False,
    }
    seal_path = RUNTIME / "hrsc_prelabel_seal.json"
    seal_path.write_text(json.dumps(seal, indent=2) + "\n", encoding="utf-8")

    labels = attach_labels(core, records)
    frame = labels.merge(scores, on=["image_id", "pred_id"], validate="one_to_one")
    if len(frame) < 2:
        raise RuntimeError("HRSC has too few eligible matched predictions")
    risk = frame["risk"].to_numpy()
    linear = frame["score_ar_size_linear"].to_numpy()
    eqs = frame["EQS"].to_numpy()
    standalone = frame["standalone_equivariance"].to_numpy()
    point = core.nrc(linear, risk) - core.nrc(eqs, risk)
    standalone_point = core.nrc(standalone, risk) - core.nrc(eqs, risk)
    boot = core.cluster_bootstrap_delta(frame, linear, eqs, 20260808, 1000)
    standalone_boot = core.cluster_bootstrap_delta(frame, standalone, eqs, 20260809, 1000)
    ap50, ap75, gt_total = official_ap(records)
    ci_low, ci_high = np.percentile(boot, [2.5, 97.5])
    standalone_low, standalone_high = np.percentile(standalone_boot, [2.5, 97.5])
    if point >= 0.02 and ci_low > 0 and standalone_point >= 0:
        verdict = "PASS_INDEPENDENT_HRSC_R014"
    elif ci_high <= 0:
        verdict = "FAIL_INDEPENDENT_HRSC_R014"
    else:
        verdict = "INCONCLUSIVE_INDEPENDENT_HRSC_R014"
    row = {
        "unit": "HRSC2016/LSKNet", "images": 453, "gt_instances": gt_total,
        "predictions": sum(len(record["pred_instances"]["scores"]) for record in records),
        "eligible_matched_ar21": len(frame), "clusters": frame["cluster"].nunique(),
        "ap50": ap50, "ap75": ap75, "nrc_linear": core.nrc(linear, risk),
        "nrc_eqs": core.nrc(eqs, risk), "nrc_standalone": core.nrc(standalone, risk),
        "delta_linear_minus_eqs": point, "ci_low": ci_low, "ci_high": ci_high,
        "delta_standalone_minus_eqs": standalone_point,
        "standalone_ci_low": standalone_low, "standalone_ci_high": standalone_high,
        "bootstrap_reps": 1000, "seal_sha256": sha256(seal_path),
        "target_angle_labels_used_for_fit": False, "status": verdict,
    }
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    with REPORT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row), lineterminator="\n")
        writer.writeheader(); writer.writerow(row)
    print(json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
