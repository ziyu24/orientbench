"""Actual r015 renderer plus backbone forward/backward qualification before fits."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).parents[2]))
from orientbench.r015.data import Windows, collate, render
from orientbench.r015.model import Heads, initialize


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--windows", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.out.exists():
        raise RuntimeError("r015 model preflight output exists")
    preflight = json.loads(args.preflight.read_text())
    if not preflight["render_pass"]:
        raise RuntimeError("renderer gate")
    manifest = json.loads((args.windows / "manifest.json").read_text())["objects"]
    rows = []
    for row in preflight["records"]["train"][:2]:
        row = dict(row)
        row["window"] = manifest[str(row["object_id"])]["window"]
        rows.append(row)
    windows, rows = collate([Windows(rows, args.windows)[i] for i in range(len(rows))])
    if not torch.cuda.is_available():
        raise RuntimeError("CUDA required")
    device = torch.device("cuda:0")
    windows = windows.to(device)
    # The actual training operator must be invariant to harmless batch padding.
    batched = render(windows, rows, "I", 96, 1501, 0, False)
    padding_error = 0.0
    for index, row in enumerate(rows):
        one_window, one_rows = collate([Windows([row], args.windows)[0]])
        one = render(one_window.to(device), one_rows, "I", 96, 1501, 0, False)
        padding_error = max(padding_error, float((batched[index:index + 1] - one).abs().max()))
    # A collated image is normalized to a larger grid than its unpadded twin;
    # grid_sample maps both back to the same source pixel coordinates.  The
    # remaining float32 inverse-normalization rounding is bounded well below
    # the independent RGB renderer's 1e-4 acceptance tolerance.
    if padding_error > 3e-5:
        raise RuntimeError(("batch-padding-render", padding_error))
    outcomes = []
    for kind in ("resnet50", "vit_b16"):
        for size in (96, 224):
            torch.manual_seed(1501)
            model = Heads(kind, size).to(device)
            weights = initialize(model)
            x = render(windows, rows, "I", size, 1501, 0, False)
            logits = model(x)
            loss = logits.square().mean()
            loss.backward()
            if not torch.isfinite(loss):
                raise RuntimeError((kind, size, "nonfinite"))
            outcomes.append({"architecture": kind, "size": size, "input_shape": list(x.shape),
                             "logit_shape": list(logits.shape), "loss": float(loss),
                             "initialization": str(weights)})
            del model, x, logits, loss
            torch.cuda.empty_cache()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps({"protocol": "r015-model-preflight-v1", "outcome_blind": True,
                                    "test_opened": False, "padding_max_abs": padding_error,
                                    "checks": outcomes}, sort_keys=True, indent=2) + "\n")


if __name__ == "__main__":
    main()
