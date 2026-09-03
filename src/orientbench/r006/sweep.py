"""Frozen r006 full integer-shift sweep, with repeated phase zero."""
from __future__ import annotations

import argparse
import pickle
from pathlib import Path

import cv2

from .inference import _load_model, _predict, _resize_and_canvas, SourceTrace
from .preflight import MODELS as MODEL_SPECS


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MODEL_SPECS, required=True)
    parser.add_argument("--pth-root", type=Path, required=True)
    parser.add_argument("--images", type=Path, required=True)
    parser.add_argument("--ids", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--axes", nargs="+", choices=("x", "y"), required=True)
    parser.add_argument("--max-shift", type=int, required=True, help="exclusive; frozen as two full periods")
    parser.add_argument("--phase0-repeats", type=int, default=3)
    parser.add_argument("--device", default="cuda:0")
    args = parser.parse_args()
    if not 1 <= args.max_shift <= 64 or args.phase0_repeats != 3:
        raise ValueError("r006 requires max_shift in [1,64] and exactly three phase-zero repeats")
    ids = [line.strip() for line in args.ids.read_text().splitlines() if line.strip()]
    model, cfg = _load_model(args.model, args.pth_root, args.device)
    scale = tuple(cfg.test_dataloader.dataset.pipeline[1]["scale"])
    trace = SourceTrace(model, args.model)
    conditions = []
    try:
        for axis in args.axes:
            for shift in range(args.max_shift):
                # x/y phase-zero tensors are identical.  Preserve exactly the
                # registered three independent repeats rather than spending an
                # additional outcome-dependent repeat on the second axis.
                repeats = args.phase0_repeats if shift == 0 and axis == args.axes[0] else 1
                for repeat in range(repeats):
                    records = []
                    for image_id in ids:
                        image = cv2.imread(str(args.images / f"{image_id}.bmp"), cv2.IMREAD_COLOR)
                        if image is None:
                            raise FileNotFoundError(image_id)
                        canvas = _resize_and_canvas(image, scale, axis, shift)
                        records.append(_predict(model, trace, canvas, image_id, args.device))
                    conditions.append({"axis": axis, "shift": shift, "repeat": repeat, "records": records})
    finally:
        trace.close()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("wb") as handle:
        pickle.dump({"protocol": "r006-frozen-biaxial-sweep-v1", "model": args.model,
                     "max_shift_exclusive": args.max_shift, "phase0_repeats": args.phase0_repeats,
                     "conditions": conditions}, handle)


if __name__ == "__main__":
    main()
