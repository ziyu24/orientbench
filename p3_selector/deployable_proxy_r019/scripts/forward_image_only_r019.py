#!/usr/bin/env python3
"""Image-only DOTA inference worker; never initializes a labeled dataset."""
from __future__ import annotations

import argparse
import builtins
import json
import os
import pickle
import time
from pathlib import Path

import cv2
import torch


ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r019"
PROTECTED = ("/annfiles/", "dota_orcnn.jsonl", "dota_rtmdet.jsonl", "matched_fullval.jsonl")


def install_guard(log_path: Path):
    events = []
    original_open = builtins.open
    def guarded_open(file, *args, **kwargs):
        value = str(file).lower().replace("\\", "/")
        if any(token in value for token in PROTECTED):
            events.append({"operation": "open", "path": str(file), "time": time.time()})
            log_path.write_text(json.dumps(events, indent=2) + "\n")
            raise PermissionError(f"r019 prelabel label-access guard: {file}")
        return original_open(file, *args, **kwargs)
    builtins.open = guarded_open
    return events


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", choices=("orcnn", "rtmdet"), required=True)
    parser.add_argument("--gpu", type=int, required=True)
    parser.add_argument("--registry", required=True)
    parser.add_argument("--indices", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--guard-log", required=True)
    args = parser.parse_args()
    os.environ["CUDA_VISIBLE_DEVICES"] = str(args.gpu)
    guard_path = Path(args.guard_log); guard_path.parent.mkdir(parents=True, exist_ok=True)
    events = install_guard(guard_path)
    from mmdet.apis import inference_detector, init_detector
    import mmrotate.models  # noqa: F401

    protocol = json.loads((ROOT / "p3_selector/deployable_proxy_r019/protocol_r019.json").read_text())
    registry = json.loads(Path(args.registry).read_text())
    indices = [int(x) for x in Path(args.indices).read_text().splitlines() if x.strip()]
    spec = registry["units"][args.unit]
    model = init_detector(spec["config"], spec["checkpoint"], device="cuda:0")
    images = registry["tiles"]
    output = []
    started = time.time()
    with torch.no_grad():
        for ordinal, index in enumerate(indices):
            item = images[index]
            array = cv2.imread(item["path"], cv2.IMREAD_COLOR)
            if array is None:
                raise RuntimeError(f"unreadable image: {item['path']}")
            h, w = array.shape[:2]
            views = {
                "identity": array,
                "hflip": cv2.flip(array, 1),
                "vflip": cv2.flip(array, 0),
            }
            for view, value in views.items():
                sample = inference_detector(model, value)
                pred = sample.pred_instances
                boxes = pred.bboxes.tensor if hasattr(pred.bboxes, "tensor") else pred.bboxes
                output.append({
                    "img_id": item["stem"], "view": view, "ori_shape": (h, w), "img_shape": (h, w),
                    "pred_instances": {
                        "bboxes": boxes.detach().cpu(), "scores": pred.scores.detach().cpu(),
                        "labels": pred.labels.detach().cpu(),
                    },
                })
            if (ordinal + 1) % 100 == 0:
                print(f"{args.unit} gpu={args.gpu} {ordinal+1}/{len(indices)}", flush=True)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with Path(args.output).open("wb") as handle:
        pickle.dump(output, handle, protocol=4)
    guard_path.write_text(json.dumps({"events": events, "target_label_access_count": len(events)}, indent=2) + "\n")
    print(json.dumps({"unit": args.unit, "gpu": args.gpu, "images": len(indices), "records": len(output), "elapsed_seconds": time.time() - started, "target_label_access_count": len(events)}))
    if events:
        raise SystemExit(2)


if __name__ == "__main__": main()
