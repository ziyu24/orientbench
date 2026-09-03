"""Pre-test canvas parity check for r006 phase zero inference."""
from __future__ import annotations

import argparse
import json
import math
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np

from orientbench.r005.matcher import global_match
from mmrotate.evaluation import eval_rbbox_map


def _array(value):
    return np.asarray(value.detach().cpu(), dtype=float)


def _read(path: Path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def _long_side_angle(box: np.ndarray) -> float:
    """Polygon construction then long-edge canonicalization in the RP1 quotient."""
    cx, cy, width, height, theta = map(float, box[:5])
    long_edge = theta if width >= height else theta + math.pi / 2
    return long_edge % math.pi


def _dpi(left: float, right: float) -> float:
    return min(abs((left - right) % math.pi), abs((right - left) % math.pi))


def _per_image_angle(gt: np.ndarray, boxes: np.ndarray) -> tuple[set[int], dict[int, float]]:
    pairs = global_match(gt, boxes)
    return {g for g, _ in pairs}, {g: _dpi(_long_side_angle(boxes[p]), _long_side_angle(gt[g])) for g, p in pairs}


def _load_canvas(path: Path) -> dict[str, dict]:
    payload = _read(path)
    # A full r006 sweep stores phase zero as a registered condition; the
    # trainval preflight stores it directly as records.  Both refer to the
    # same raw, pre-NMS-rescale coordinate contract.
    if "conditions" in payload:
        for condition in payload["conditions"]:
            if condition["axis"] == "x" and condition["shift"] == 0 and condition["repeat"] == 0:
                return {str(record["img_id"]): record for record in condition["records"]}
        raise RuntimeError(f"missing x/0/repeat-0 phase zero in {path}")
    return {str(record["img_id"]): record for record in payload["records"]}


def _ap75(standard: list[dict], canvas: dict[str, dict], use_07: bool) -> tuple[float, float]:
    standard_dets, canvas_dets, annotations = [], [], []
    for record in standard:
        image_id = str(record["img_id"])
        gt = _array(record["gt_instances"]["bboxes"])
        original_boxes = _array(record["pred_instances"]["bboxes"])
        original_scores = _array(record["pred_instances"]["scores"]).reshape(-1, 1)
        phase = canvas[image_id]
        phase_boxes = np.asarray(phase["bboxes"], dtype=float)
        phase_scores = np.asarray(phase["scores"], dtype=float).reshape(-1, 1)
        standard_dets.append([np.concatenate([original_boxes, original_scores], 1)])
        canvas_dets.append([np.concatenate([phase_boxes, phase_scores], 1)])
        annotations.append({"bboxes": gt, "labels": np.zeros(len(gt), dtype=np.int64),
                            "bboxes_ignore": np.zeros((0, 5)), "labels_ignore": np.zeros(0, dtype=np.int64)})
    base, _ = eval_rbbox_map(standard_dets, annotations, iou_thr=.75, use_07_metric=use_07,
                             box_type="rbox", logger="silent", nproc=4)
    shifted, _ = eval_rbbox_map(canvas_dets, annotations, iou_thr=.75, use_07_metric=use_07,
                                box_type="rbox", logger="silent", nproc=4)
    return float(base), float(shifted)


def _check(standard_path: Path, canvas_path: Path) -> dict:
    standard = _read(standard_path)
    canvas = _load_canvas(canvas_path)
    total_standard = retained = 0
    standard_error, canvas_error = [], []
    per_image = []
    for record in standard:
        image_id = str(record["img_id"])
        gt = _array(record["gt_instances"]["bboxes"])
        standard_boxes = _array(record["pred_instances"]["bboxes"])
        phase = canvas[image_id]
        canvas_boxes = np.asarray(phase["bboxes"], dtype=float)
        std_set, std_angle = _per_image_angle(gt, standard_boxes)
        canvas_set, canvas_angle = _per_image_angle(gt, canvas_boxes)
        overlap = std_set & canvas_set
        total_standard += len(std_set)
        retained += len(overlap)
        if std_set:
            standard_error.append(float(np.mean(list(std_angle.values()))))
        if overlap:
            canvas_error.append(float(np.mean([canvas_angle[index] for index in overlap])))
        per_image.append({"image_id": image_id, "standard_matched": len(std_set),
                          "canvas_matched": len(canvas_set), "retained_standard": len(overlap)})
    # The explicitly specified canvas criterion is evaluated on the same
    # standard-clean frozen matched objects; all angular errors are RP1 long-side values.
    use_07 = "rotated_rtmdet_m" in standard_path.as_posix()
    standard_ap75, canvas_ap75 = _ap75(standard, canvas, use_07)
    return {"standard_matched": total_standard, "retained_standard": retained,
            "retention": retained / total_standard if total_standard else 0.0,
            "standard_mean_le90_deg": math.degrees(float(np.mean(standard_error))),
            "canvas_mean_le90_deg": math.degrees(float(np.mean(canvas_error))),
            "mean_le90_abs_delta_deg": abs(math.degrees(float(np.mean(canvas_error))) -
                                            math.degrees(float(np.mean(standard_error)))),
            "standard_ap75": standard_ap75, "canvas_ap75": canvas_ap75,
            "ap75_abs_delta": abs(canvas_ap75 - standard_ap75),
            "per_image": per_image}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r004-root", type=Path, required=True)
    parser.add_argument("--orcnn", type=Path, required=True)
    parser.add_argument("--rtmdet", type=Path, required=True)
    parser.add_argument("--split", choices=("trainval", "test"), default="trainval")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    checks = {
        "oriented_rcnn_r50": _check(args.r004_root / f"inference/{args.split}/oriented_rcnn_r50/clean/predictions.pkl", args.orcnn),
        "rotated_rtmdet_m": _check(args.r004_root / f"inference/{args.split}/rotated_rtmdet_m/clean/predictions.pkl", args.rtmdet),
    }
    for check in checks.values():
        check["passes_canvas_parity"] = bool(check["retention"] >= .95 and check["mean_le90_abs_delta_deg"] <= .5
                                              and check["ap75_abs_delta"] <= .005)
    output = {"protocol": "r006-canvas-phase0-parity-v1", "checks": checks,
              "all_passes_canvas_parity": all(check["passes_canvas_parity"] for check in checks.values())}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
