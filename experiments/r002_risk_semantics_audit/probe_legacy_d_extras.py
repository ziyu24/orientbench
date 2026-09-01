#!/usr/bin/env python3
"""Locate legacy-only D matches in the recovered FAIR1M annotation tree."""
from __future__ import annotations

import argparse
import importlib.util
import json
import pickle
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from mmcv.ops import box_iou_rotated

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--annotations", required=True, type=Path)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("source_attach_labels", args.source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with (args.runtime / "raw/fair24/identity.pkl").open("rb") as stream:
        records = {str(record["img_id"]): record for record in pickle.load(stream)}
    names = module.class_names("D")
    replay = []
    for image_id, record in records.items():
        replay.extend(module.match_one(record, args.annotations / f"{image_id}.txt", names, "FAIR1M-v1.0"))
    keys = ["image_id", "pred_id", "class_id"]
    replay_keys = set(map(tuple, pd.DataFrame(replay)[keys].to_numpy()))
    legacy = pd.read_parquet(args.runtime / "labels/D.parquet")
    extra = legacy[~legacy[keys].apply(tuple, axis=1).isin(replay_keys)]
    counts: list[int] = []
    for row in extra.itertuples(index=False):
        record = records[str(row.image_id)]
        inst = record["pred_instances"]
        boxes = inst["bboxes"].tensor if hasattr(inst["bboxes"], "tensor") else inst["bboxes"]
        boxes = boxes.detach().cpu().float()
        pred = boxes[int(row.pred_id)].reshape(1, 5)
        gt, names_in_file = module.parse_gt(args.annotations / f"{row.image_id}.txt")
        target_name = names[int(row.class_id)]
        candidates = np.flatnonzero(names_in_file == target_name)
        if len(candidates):
            iou = box_iou_rotated(pred, gt[candidates]).cpu().numpy()[0]
            ar = np.maximum(gt[candidates, 2].numpy(), gt[candidates, 3].numpy()) / np.maximum(np.minimum(gt[candidates, 2].numpy(), gt[candidates, 3].numpy()), 1e-6)
            angles = np.asarray([module.le90(float(pred[0, 4]), float(gt[index, 4])) for index in candidates])
            mask = (np.abs(iou - float(row.iou)) < 1e-5) & (np.abs(ar - float(row.gt_ar)) < 1e-5) & (np.abs(angles - float(row.angle_error)) < 1e-4)
            counts.append(int(mask.sum()))
        else:
            counts.append(0)
    payload = {"legacy_only": len(extra), "candidate_count_histogram": {str(k): counts.count(k) for k in sorted(set(counts))}, "all_unique": all(count == 1 for count in counts)}
    print(json.dumps(payload, sort_keys=True))
    if not payload["all_unique"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
