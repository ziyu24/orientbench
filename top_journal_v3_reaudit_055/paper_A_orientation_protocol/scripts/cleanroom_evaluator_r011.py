#!/usr/bin/env python3
"""Independent Shapely-based rotated-box evaluator for r011 parity checks."""
import argparse
import json
import math
import pickle
from collections import defaultdict
from pathlib import Path

import numpy as np
import shapely

ROOT = Path(__file__).resolve().parents[3]
CELLS = {
    "DIOR-R/22": ("outputs/persistent_artifacts/orientbench_v2/DIOR-R/22/schema/pred_b22_fullval.jsonl", "outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl"),
    "DIOR-R/3": ("outputs/persistent_artifacts/orientbench_v2/DIOR-R/3/schema/pred_b3_fullval.jsonl", "outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl"),
    "DIOR-R/61": ("outputs/persistent_artifacts/orientbench_v2/DIOR-R/61/schema/pred_b61_fullval.jsonl", "outputs/persistent_artifacts/k1_table1_fullval_065/gt/DIOR-R_test_fullval_gt.jsonl"),
    "FAIR1M-v1.0/24": ("outputs/persistent_artifacts/orientbench_v2/FAIR1M-v1.0/24/schema/pred_b24_fullval.jsonl", "outputs/persistent_artifacts/k1_table1_fullval_065/gt/FAIR1M-v1.0_val20_fullval_gt.jsonl"),
    "SODA-A/23": ("outputs/persistent_artifacts/orientbench_v2_047/tta_preds/SODA-A_23/identity.pkl", "outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl"),
    "SODA-A/4": ("outputs/persistent_artifacts/orientbench_v2/SODA-A/4/schema/pred_b4_fullval.jsonl", "outputs/persistent_artifacts/k1_table1_fullval_065/gt/SODA-A_val_tiled_fullval_gt.jsonl"),
}
SODA_CLASSES = ("airplane", "helicopter", "small-vehicle", "large-vehicle",
                "ship", "container", "storage-tank", "swimming-pool", "windmill")

def load(path):
    source = ROOT / path
    if source.suffix != ".pkl":
        return [json.loads(line) for line in source.open()]
    records = pickle.load(source.open("rb"))
    rows = []
    for record in records:
        inst = record["pred_instances"]
        boxes = inst["bboxes"].detach().cpu().numpy()
        scores = inst["scores"].detach().cpu().numpy()
        labels = inst["labels"].detach().cpu().numpy()
        for box, score, label in zip(boxes, scores, labels):
            rows.append({"image_id": str(record["img_id"]), "class_name": SODA_CLASSES[int(label)],
                         "obb_cx": float(box[0]), "obb_cy": float(box[1]),
                         "obb_w": float(box[2]), "obb_h": float(box[3]),
                         "obb_theta": float(box[4]), "score": float(score)})
    return rows

def polygons(rows):
    if not rows:
        return np.empty((0,), dtype=object)
    vertices = []
    for row in rows:
        cx, cy = float(row["obb_cx"]), float(row["obb_cy"])
        w, h, theta = float(row["obb_w"]), float(row["obb_h"]), float(row["obb_theta"])
        c, s = math.cos(theta), math.sin(theta)
        points = []
        for x, y in ((-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)):
            points.append((cx + c*x - s*y, cy + s*x + c*y))
        vertices.append(points)
    return shapely.polygons(np.asarray(vertices, dtype=np.float64))

def match_group(preds, gts, threshold):
    if not preds:
        return []
    order = sorted(range(len(preds)), key=lambda i: (-float(preds[i]["score"]), i))
    if not gts:
        return [(preds[i], 0) for i in order]
    pp, gg = polygons(preds), polygons(gts)
    intersections = shapely.area(shapely.intersection(pp[:, None], gg[None, :]))
    unions = shapely.area(pp)[:, None] + shapely.area(gg)[None, :] - intersections
    iou = np.divide(intersections, unions, out=np.zeros_like(intersections), where=unions > 0)
    used = np.zeros(len(gts), dtype=bool)
    result = []
    for i in order:
        j = int(np.argmax(iou[i]))
        hit = bool(iou[i, j] >= threshold and not used[j])
        if hit: used[j] = True
        result.append((preds[i], int(hit)))
    return result

def ap11(tp, scores, n_gt):
    if n_gt == 0: return float("nan")
    order = sorted(range(len(scores)), key=lambda i: (-scores[i], i))
    t = np.asarray([tp[i] for i in order], dtype=np.float64)
    f = 1.0 - t
    recall = np.cumsum(t) / n_gt
    precision = np.cumsum(t) / np.maximum(np.cumsum(t) + np.cumsum(f), 1.0)
    return float(np.mean([precision[recall >= level].max() if np.any(recall >= level) else 0.0
                          for level in np.linspace(0, 1, 11)]))

def evaluate(cell):
    pred_path, gt_path = CELLS[cell]
    preds, gts = load(pred_path), load(gt_path)
    grouped_pred, grouped_gt = defaultdict(list), defaultdict(list)
    for index, row in enumerate(preds):
        row = dict(row); row["_index"] = index
        grouped_pred[(str(row["image_id"]), row["class_name"])].append(row)
    for row in gts: grouped_gt[(str(row["image_id"]), row["class_name"])].append(row)
    classes = sorted({row["class_name"] for row in preds + gts})
    output = {"unit": cell, "endpoint": "cleanroom_shapely_polygon_iou_v1",
              "images": len({str(row["image_id"]) for row in preds + gts}),
              "predictions": len(preds), "ground_truth": len(gts)}
    for threshold in (0.5, 0.75):
        class_ap = []
        for cls in classes:
            keys = sorted({k for k in grouped_pred if k[1] == cls} | {k for k in grouped_gt if k[1] == cls})
            matched = []
            for key in keys: matched.extend(match_group(grouped_pred.get(key, []), grouped_gt.get(key, []), threshold))
            matched.sort(key=lambda pair: (-float(pair[0]["score"]), str(pair[0]["image_id"]), int(pair[0]["_index"])))
            n_gt = sum(len(grouped_gt.get(key, [])) for key in keys)
            class_ap.append(ap11([v for _, v in matched], [float(r["score"]) for r, _ in matched], n_gt))
        output[f"AP{int(threshold*100)}"] = float(np.nanmean(class_ap))
    return output

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", choices=CELLS, required=True)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = evaluate(args.unit)
    text = json.dumps(result, sort_keys=True)
    if args.output: Path(args.output).write_text(text + "\n")
    print(text)

if __name__ == "__main__": main()
