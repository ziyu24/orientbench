"""Standalone r005 recomputation; deliberately does not import the production matcher."""
from __future__ import annotations
import argparse, json, math, pickle
from pathlib import Path
import numpy as np


def _array(x):
    return np.asarray(x.detach().cpu(), dtype=float)


def _read(path):
    with open(path, "rb") as handle:
        return pickle.load(handle)


def _pairs(gt, pred):
    """Independent exhaustive theta-free candidate construction and greedy resolution."""
    candidates = []
    for gix, g in enumerate(gt):
        garea = max(float(g[2] * g[3]), 1e-9)
        for pix, p in enumerate(pred):
            distance = math.hypot(float(g[0] - p[0]), float(g[1] - p[1])) / max(math.sqrt(garea), 1.0)
            area_ratio = float(p[2] * p[3]) / garea
            sides = sorted((float(g[2]), float(g[3])))
            psides = sorted((float(p[2]), float(p[3])))
            side_cost = abs(math.log(max(sides[0], 1e-9) / max(psides[0], 1e-9))) + abs(math.log(max(sides[1], 1e-9) / max(psides[1], 1e-9)))
            if distance <= 0.5 and 0.25 <= area_ratio <= 4.0 and side_cost <= math.log(4.0):
                candidates.append((distance + side_cost, gix, pix))
    claimed_gt, claimed_pred, answer = set(), set(), []
    for _, gix, pix in sorted(candidates, key=lambda row: (row[0], row[1], row[2])):
        if gix not in claimed_gt and pix not in claimed_pred:
            claimed_gt.add(gix)
            claimed_pred.add(pix)
            answer.append((gix, pix))
    return answer


def _canonical(box):
    w, h, theta = map(float, box[2:5])
    if h > w:
        w, h, theta = h, w, theta + math.pi / 2
    theta = theta % math.pi
    return theta


def _le90(pred, gt):
    delta = abs(_canonical(pred) - _canonical(gt)) % math.pi
    return min(delta, math.pi - delta)


def _rows(root, split, model, condition):
    base = root / "inference" / split / model
    clean = _read(base / "clean" / "predictions.pkl")
    changed = {record["img_id"]: record for record in _read(base / condition / "predictions.pkl")}
    output = []
    for record in clean:
        image_id = record["img_id"]
        gt = _array(record["gt_instances"]["bboxes"])
        p0 = _array(record["pred_instances"]["bboxes"])
        p1 = _array(changed[image_id]["pred_instances"]["bboxes"])
        after = dict(_pairs(gt, p1))
        for gt_index, clean_pred_index in _pairs(gt, p0):
            e0 = _le90(p0[clean_pred_index], gt[gt_index])
            y0 = e0 / (math.pi / 2)
            after_pred_index = after.get(gt_index)
            if after_pred_index is None:
                retained, e1, miss, angle = 0, None, 1.0 - y0, 0.0
            else:
                e1 = _le90(p1[after_pred_index], gt[gt_index])
                retained, miss, angle = 1, 0.0, (e1 - e0) / (math.pi / 2)
            output.append({"image_id": image_id, "gt_index": gt_index,
                           "clean_pred_index": clean_pred_index, "after_pred_index": after_pred_index,
                           "e0_rad": e0, "e1_rad": e1, "retained": retained, "Y0": y0,
                           "C_miss": miss, "C_ang": angle, "DeltaY": miss + angle})
    return output


def _summary(rows):
    per_image = {}
    for row in rows:
        per_image.setdefault(row["image_id"], []).append(row)
    return {"objects": len(rows), "images": len(per_image), "retained": sum(row["retained"] for row in rows),
            "means": {field: float(np.mean([np.mean([row[field] for row in image_rows]) for image_rows in per_image.values()]))
                      for field in ("C_miss", "C_ang", "DeltaY")}, "rows": rows}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    answer = {"implementation": "independent_loss_audit_v1", "models": {}}
    for model in ("oriented_rcnn_r50", "rotated_rtmdet_m"):
        answer["models"][model] = {}
        for split in ("trainval", "test"):
            answer["models"][model][split] = {condition: _summary(_rows(args.root, split, model, condition))
                                                for condition in ("blur_1.5", "blur_1.25", "downsample_2", "downsample_1.75")}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(answer, indent=2) + "\n")


if __name__ == "__main__":
    main()
