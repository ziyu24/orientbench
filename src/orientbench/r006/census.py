"""Freeze active source strides from trainval before test is opened."""
from __future__ import annotations

import argparse
import json
import pickle
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

from orientbench.r005.matcher import global_match


def _array(value):
    return np.asarray(value.detach().cpu(), dtype=float)


def _read(path: Path):
    with path.open("rb") as handle:
        return pickle.load(handle)


def _ground_truth(path: Path) -> dict[str, np.ndarray]:
    answer = {}
    for record in _read(path):
        answer[str(record["img_id"])] = _array(record["gt_instances"]["bboxes"])
    return answer


def _census(prediction_path: Path, gt: dict[str, np.ndarray]) -> dict:
    payload = _read(prediction_path)
    counts, images = Counter(), defaultdict(set)
    matched = 0
    for record in payload["records"]:
        image_id = str(record["img_id"])
        boxes = np.asarray(record["bboxes"], dtype=float)
        for _, pred_index in global_match(gt[image_id], boxes):
            stride = int(record["source_stride"][pred_index])
            counts[stride] += 1
            images[stride].add(image_id)
            matched += 1
    rows = []
    for stride in sorted(counts):
        fraction = counts[stride] / matched if matched else 0.0
        rows.append({"stride": stride, "objects": counts[stride], "images": len(images[stride]),
                     "fraction": fraction,
                     "eligible": bool(fraction >= .15 and counts[stride] >= 200 and len(images[stride]) >= 100)})
    return {"matched_objects": matched, "strides": rows,
            "eligible_strides": [row["stride"] for row in rows if row["eligible"]],
            "phase0_file": str(prediction_path)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--r004-root", type=Path, required=True)
    parser.add_argument("--orcnn", type=Path, required=True)
    parser.add_argument("--rtmdet", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    roots = args.r004_root / "inference/trainval"
    output = {
        "protocol": "r006-trainval-active-stride-census-v1",
        "oriented_rcnn_r50": _census(args.orcnn, _ground_truth(roots / "oriented_rcnn_r50/clean/predictions.pkl")),
        "rotated_rtmdet_m": _census(args.rtmdet, _ground_truth(roots / "rotated_rtmdet_m/clean/predictions.pkl")),
    }
    output["all_models_have_eligible_stride"] = all(output[name]["eligible_strides"] for name in
                                                     ("oriented_rcnn_r50", "rotated_rtmdet_m"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
