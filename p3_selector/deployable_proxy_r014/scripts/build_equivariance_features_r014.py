#!/usr/bin/env python3
"""Build the sealed, prediction-only r014 equivariance feature registry."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import multiprocessing as mp
import os
import pickle
import sys
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import torch
from mmcv.ops import box_iou_rotated
from mmrotate.structures.bbox import RotatedBoxes
from shapely.geometry import Polygon


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))
from derive_delta_theta_075 import load_interpolator

RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r014"
OLD_TTA = ROOT / "outputs/persistent_artifacts/orientbench_v2_047/tta_preds"
SODA4_ID = ROOT / "outputs/persistent_artifacts/orientbench_v2/SODA-A/4/raw/result_b4.pkl"
UNITS = {
    "A": ("DIOR-R/22", "DIOR-R", RUNTIME / "raw/dior22"),
    "B": ("DIOR-R/3", "DIOR-R", RUNTIME / "raw/dior3"),
    "C": ("DIOR-R/61", "DIOR-R", RUNTIME / "raw/dior61"),
    "D": ("FAIR1M-v1.0/24", "FAIR1M-v1.0", RUNTIME / "raw/fair24"),
    "E": ("SODA-A/23", "SODA-A", OLD_TTA / "SODA-A_23"),
    "F": ("SODA-A/4", "SODA-A", OLD_TTA / "SODA-A_4"),
    "H": ("HRSC2016/LSKNet", "HRSC2016", RUNTIME / "raw/hrsc_lsknet"),
}
_DTH = load_interpolator()
_RECORDS = None


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_csv(path: Path, rows: list[dict]) -> None:
    fields = []
    for row in rows:
        for key in row:
            if key not in fields:
                fields.append(key)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def raw_paths(unit: str) -> tuple[Path, Path, Path]:
    directory = UNITS[unit][2]
    identity = SODA4_ID if unit == "F" else directory / "identity.pkl"
    return identity, directory / "hflip.pkl", directory / "vflip.pkl"


def tensors(record: dict) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    pred = record["pred_instances"]
    boxes = pred["bboxes"].tensor if hasattr(pred["bboxes"], "tensor") else pred["bboxes"]
    return boxes.detach().cpu().float(), pred["scores"].detach().cpu().float(), pred["labels"].detach().cpu().long()


def inverse_boxes(record: dict, direction: str) -> torch.Tensor:
    boxes, _, _ = tensors(record)
    if boxes.numel() == 0:
        return boxes
    shape = record.get("ori_shape", record.get("img_shape"))
    restored = RotatedBoxes(boxes.clone())
    restored.flip_((int(shape[0]), int(shape[1])), direction)
    return restored.tensor


def le90_deg(a: float, b: float) -> float:
    delta = abs((a - b) * 180.0 / math.pi) % 180.0
    return min(delta, 180.0 - delta)


def association(identity_boxes: torch.Tensor, identity_labels: torch.Tensor,
                view_boxes: torch.Tensor, view_scores: torch.Tensor,
                view_labels: torch.Tensor) -> tuple[dict[int, tuple[int, float]], dict[int, float]]:
    matches: dict[int, tuple[int, float]] = {}
    margins: dict[int, float] = {}
    for label in sorted(set(identity_labels.tolist())):
        ii = torch.where(identity_labels == label)[0]
        vv = torch.where(view_labels == label)[0]
        if not len(ii) or not len(vv):
            continue
        matrix = box_iou_rotated(identity_boxes[ii], view_boxes[vv]).cpu().numpy()
        candidates = []
        for local_i, global_i in enumerate(ii.tolist()):
            values = np.sort(matrix[local_i])[::-1]
            margins[global_i] = float(np.clip(values[0] - (values[1] if len(values) > 1 else 0.0), 0.0, 1.0))
            for local_v, global_v in enumerate(vv.tolist()):
                iou = float(matrix[local_i, local_v])
                if iou >= 0.3:
                    candidates.append((-iou, -float(view_scores[global_v]), global_i, global_v))
        used_i: set[int] = set()
        used_v: set[int] = set()
        for neg_iou, _, global_i, global_v in sorted(candidates):
            if global_i in used_i or global_v in used_v:
                continue
            used_i.add(global_i)
            used_v.add(global_v)
            matches[global_i] = (global_v, -neg_iou)
    return matches, margins


def process_image(index: int) -> list[dict]:
    identity, hrecord, vrecord = (_RECORDS[0][index], _RECORDS[1][index], _RECORDS[2][index])
    image_id = str(identity["img_id"])
    if str(hrecord["img_id"]) != image_id or str(vrecord["img_id"]) != image_id:
        raise RuntimeError(f"unaligned view image identity at {index}: {image_id}")
    ib, score, labels = tensors(identity)
    hb, hs, hl = tensors(hrecord)
    vb, vs, vl = tensors(vrecord)
    hb = inverse_boxes(hrecord, "horizontal")
    vb = inverse_boxes(vrecord, "vertical")
    hm, hmargin = association(ib, labels, hb, hs, hl)
    vm, vmargin = association(ib, labels, vb, vs, vl)
    rows = []
    for pred_id in range(len(ib)):
        base = ib[pred_id]
        width, height = float(base[2]), float(base[3])
        pred_ar = max(width, height) / max(min(width, height), 1e-6)
        area = max(width * height, 1e-6)
        score_clip = float(np.clip(float(score[pred_id]), 1e-6, 1 - 1e-6))
        logit = float(np.clip(math.log(score_clip / (1 - score_clip)), -13.815511, 13.815511))
        matches = []
        for match, boxes, scores, margins in ((hm, hb, hs, hmargin), (vm, vb, vs, vmargin)):
            if pred_id not in match:
                continue
            view_id, iou = match[pred_id]
            other = boxes[view_id]
            other_score = float(np.clip(float(scores[view_id]), 1e-6, 1 - 1e-6))
            other_logit = float(np.clip(math.log(other_score / (1 - other_score)), -13.815511, 13.815511))
            matches.append({
                "angle": le90_deg(float(base[4]), float(other[4])),
                "iou_loss": 1.0 - iou,
                "center": math.hypot(float(base[0] - other[0]), float(base[1] - other[1])) / math.sqrt(area),
                "wdisp": abs(math.log(max(float(other[2]), 1e-6) / max(width, 1e-6))),
                "hdisp": abs(math.log(max(float(other[3]), 1e-6) / max(height, 1e-6))),
                "score_disp": abs(logit - other_logit),
                "margin": margins.get(pred_id, 0.0),
            })
        support = len(matches) / 2.0
        if matches:
            med = lambda key: float(np.median([row[key] for row in matches]))
            dth = max(float(_DTH(pred_ar)), 1.0)
            u_axis = float(np.clip(med("angle") / dth, 0.0, 3.0))
            iou_loss = float(np.clip(med("iou_loss"), 0.0, 1.0))
            center = float(np.clip(med("center"), 0.0, 3.0))
            wdisp = float(np.clip(med("wdisp"), 0.0, 3.0))
            hdisp = float(np.clip(med("hdisp"), 0.0, 3.0))
            score_disp = float(np.clip(med("score_disp"), 0.0, 10.0))
            margin = float(np.clip(med("margin"), 0.0, 1.0))
        else:
            u_axis, iou_loss, center, wdisp, hdisp, score_disp, margin = 3.0, 1.0, 3.0, 3.0, 3.0, 10.0, 0.0
        rows.append({
            "image_id": image_id,
            "pred_id": pred_id,
            "class_id": int(labels[pred_id]),
            "detection_score": float(score[pred_id]),
            "logit_score": logit,
            "log_pred_ar": float(np.clip(math.log(max(pred_ar, 1 + 1e-6)), 0.0, 4.605170)),
            "half_log_pred_area": float(np.clip(0.5 * math.log(area), -6.907755, 9.210340)),
            "support_fraction": support,
            "missing_fraction": 1.0 - support,
            "u_axis": u_axis,
            "iou_loss": iou_loss,
            "center_dispersion": center,
            "width_dispersion": wdisp,
            "height_dispersion": hdisp,
            "score_dispersion": score_disp,
            "association_margin": margin,
        })
    return rows


def build(unit: str, workers: int) -> dict:
    global _RECORDS
    paths = raw_paths(unit)
    if not all(path.is_file() for path in paths):
        raise FileNotFoundError(f"missing raw views for {unit}: {paths}")
    loaded = []
    for path in paths:
        with path.open("rb") as handle:
            records = pickle.load(handle)
        loaded.append(sorted(records, key=lambda row: str(row["img_id"])))
    ids = [[str(row["img_id"]) for row in records] for records in loaded]
    if not (ids[0] == ids[1] == ids[2]) or len(ids[0]) != len(set(ids[0])):
        raise RuntimeError(f"view universe mismatch for {unit}")
    _RECORDS = loaded
    out_dir = RUNTIME / "features"
    out_dir.mkdir(parents=True, exist_ok=True)
    final = out_dir / f"{unit}.parquet"
    partial = final.with_suffix(".parquet.partial")
    if partial.exists():
        partial.unlink()
    writer = None
    rows_total = 0
    started = time.time()
    context = mp.get_context("fork")
    with context.Pool(processes=workers) as pool:
        for rows in pool.imap(process_image, range(len(ids[0])), chunksize=4):
            if not rows:
                continue
            table = pa.Table.from_pylist(rows)
            if writer is None:
                writer = pq.ParquetWriter(partial, table.schema, compression="zstd")
            writer.write_table(table)
            rows_total += len(rows)
    if writer is None:
        raise RuntimeError(f"empty feature registry for {unit}")
    writer.close()
    partial.replace(final)
    result = {
        "unit": UNITS[unit][0], "dataset": UNITS[unit][1],
        "images": len(ids[0]), "rows": rows_total,
        "path": str(final), "bytes": final.stat().st_size, "sha256": sha256(final),
        "schema": "r014_prediction_only_equivariance_v1", "workers": workers,
        "elapsed_seconds": round(time.time() - started, 3), "gt_fields": [],
    }
    (out_dir / f"{unit}.manifest.json").write_text(json.dumps(result, indent=2) + "\n")
    return result


def sanity() -> dict:
    rng = np.random.RandomState(20260807)
    # Binary-exact centers/sizes isolate transform algebra from the known
    # near-identical-polygon numerical instability in box_iou_rotated.
    samples = torch.tensor(np.column_stack([
        rng.randint(10, 111, 50), rng.randint(10, 91, 50),
        rng.randint(4, 31, 50), rng.randint(2, 21, 50),
        rng.randint(-128, 129, 50) / 128.0,
    ]), dtype=torch.float32)
    results = []
    def polygon(box):
        cx, cy, width, height, theta = map(float, box)
        c, s = math.cos(theta), math.sin(theta)
        return Polygon([(cx + c*x - s*y, cy + s*x + c*y)
                        for x, y in ((-width/2, -height/2), (width/2, -height/2),
                                     (width/2, height/2), (-width/2, height/2))])
    for direction in ("horizontal", "vertical"):
        transformed = RotatedBoxes(samples.clone())
        transformed.flip_((100, 120), direction)
        transformed.flip_((100, 120), direction)
        iou = np.asarray([polygon(a).intersection(polygon(b)).area / polygon(a).union(polygon(b)).area
                          for a, b in zip(samples, transformed.tensor)])
        angle = [le90_deg(float(a), float(b)) for a, b in zip(samples[:, 4], transformed.tensor[:, 4])]
        results.append({"direction": direction, "min_iou": float(iou.min()), "max_angle_deg": max(angle)})
    return {"status": "PASS" if all(r["min_iou"] >= 1 - 1e-7 and r["max_angle_deg"] <= 1e-7 for r in results) else "FAIL", "rows": results}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", choices=tuple(UNITS), required=True)
    parser.add_argument("--workers", type=int, default=38)
    args = parser.parse_args()
    if not 1 <= args.workers <= 38:
        raise SystemExit("workers must be in [1,38]")
    check = sanity()
    if check["status"] != "PASS":
        raise RuntimeError(check)
    result = build(args.unit, args.workers)
    report_dir = ROOT / "p3_selector/deployable_proxy_r014/reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    write_csv(report_dir / "transform_sanity_r014.csv", [
        {"test": f"synthetic_50_{row['direction']}", "samples": 50, **row,
         "status": "PASS" if row["min_iou"] >= 1 - 1e-7 and row["max_angle_deg"] <= 1e-7 else "FAIL"}
        for row in check["rows"]
    ])
    manifests = []
    for unit in UNITS:
        path = RUNTIME / f"features/{unit}.manifest.json"
        if path.is_file():
            manifests.append(json.loads(path.read_text()))
    write_csv(report_dir / "feature_summary_r014.csv", manifests)
    print(json.dumps({"sanity": check, "feature": result}))


if __name__ == "__main__":
    main()
