#!/usr/bin/env python3
"""Official mmrotate DOTAMetric functional endpoint adapter for r011."""
import argparse
import json
import pickle
from pathlib import Path

import numpy as np
from mmrotate.evaluation.functional import eval_rbbox_map

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
        instances = record["pred_instances"]
        boxes = instances["bboxes"].detach().cpu().numpy()
        scores = instances["scores"].detach().cpu().numpy()
        labels = instances["labels"].detach().cpu().numpy()
        for box, score, label in zip(boxes, scores, labels):
            rows.append({"image_id": str(record["img_id"]), "class_name": SODA_CLASSES[int(label)],
                         "obb_cx": float(box[0]), "obb_cy": float(box[1]),
                         "obb_w": float(box[2]), "obb_h": float(box[3]),
                         "obb_theta": float(box[4]), "score": float(score)})
    return rows

def prepare(preds, gts):
    classes = sorted({row["class_name"] for row in preds + gts})
    class_index = {name: index for index, name in enumerate(classes)}
    images = sorted({str(row["image_id"]) for row in preds + gts})
    image_index = {name: index for index, name in enumerate(images)}
    dets = [[[] for _ in classes] for _ in images]
    gt_boxes = [[] for _ in images]
    gt_labels = [[] for _ in images]
    for row in preds:
        dets[image_index[str(row["image_id"])]][class_index[row["class_name"]]].append([
            row["obb_cx"], row["obb_cy"], row["obb_w"], row["obb_h"], row["obb_theta"], row["score"]])
    for row in gts:
        idx = image_index[str(row["image_id"])]
        gt_boxes[idx].append([row["obb_cx"], row["obb_cy"], row["obb_w"], row["obb_h"], row["obb_theta"]])
        gt_labels[idx].append(class_index[row["class_name"]])
    det_results = [[np.asarray(v, dtype=np.float32).reshape(-1, 6) for v in row] for row in dets]
    annotations = []
    for boxes, labels in zip(gt_boxes, gt_labels):
        annotations.append({
            "bboxes": np.asarray(boxes, dtype=np.float32).reshape(-1, 5),
            "labels": np.asarray(labels, dtype=np.int64),
            "bboxes_ignore": np.empty((0, 5), dtype=np.float32),
            "labels_ignore": np.empty((0,), dtype=np.int64),
        })
    return classes, images, det_results, annotations

def evaluate(cell, nproc):
    pred_path, gt_path = CELLS[cell]
    preds, gts = load(pred_path), load(gt_path)
    classes, images, dets, annotations = prepare(preds, gts)
    values = {}
    for threshold in (0.5, 0.75):
        mean_ap, _ = eval_rbbox_map(dets, annotations, iou_thr=threshold,
                                    use_07_metric=True, box_type="rbox",
                                    dataset=classes, logger="silent", nproc=nproc)
        values[f"AP{int(threshold * 100)}"] = float(mean_ap)
    return {"unit": cell, "endpoint": "mmrotate.evaluation.functional.eval_rbbox_map",
            "images": len(images), "predictions": len(preds), "ground_truth": len(gts), **values}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", choices=CELLS, required=True)
    parser.add_argument("--nproc", type=int, default=8)
    parser.add_argument("--output")
    args = parser.parse_args()
    result = evaluate(args.unit, args.nproc)
    text = json.dumps(result, sort_keys=True)
    if args.output:
        Path(args.output).write_text(text + "\n")
    print(text)

if __name__ == "__main__":
    main()
