"""Prediction output path policy.

All future prediction outputs MUST live under
outputs/predictions/{dataset}/{baseline_id}/ inside the project. Writing to
pth_data, third_party, or the project root is forbidden. Filenames embed
baseline_id / dataset / split / timestamp.
"""
from __future__ import annotations

import os
import re
from typing import Optional, Tuple

PROJECT_ROOT = "/home/rspip/cqc/pro/study/orientbench"
PREDICTIONS_ROOT = os.path.join(PROJECT_ROOT, "outputs", "predictions")
FORBIDDEN_PREFIXES = [
    "/home/rspip/cqc/pro/study/pth_data",
    "/home/rspip/cqc/pro/study/third_party",
    "/home/rspip/cqc/data/dataset",
]


def _sanitize(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", str(s)).strip("_") or "unknown"


def build_prediction_output_path(dataset: str, baseline_id, split: str,
                                 timestamp: str, ext: str = "jsonl") -> str:
    ds = _sanitize(dataset)
    bid = _sanitize(str(baseline_id))
    sp = _sanitize(split)
    ts = _sanitize(timestamp)
    fname = f"pred_b{bid}_{ds}_{sp}_{ts}.{ext}"
    return os.path.join(PREDICTIONS_ROOT, ds, bid, fname)


def validate_output_path(path: str) -> Tuple[bool, Optional[str]]:
    """Return (ok, reason). ok only if path is under PREDICTIONS_ROOT."""
    ap = os.path.abspath(path)
    for bad in FORBIDDEN_PREFIXES:
        if ap.startswith(os.path.abspath(bad) + os.sep) or ap == os.path.abspath(bad):
            return False, f"forbidden location (under {bad})"
    # project root but not predictions -> reject (no root clutter)
    if not ap.startswith(os.path.abspath(PREDICTIONS_ROOT) + os.sep):
        if ap.startswith(os.path.abspath(PROJECT_ROOT) + os.sep):
            return False, "inside project but not under outputs/predictions"
        return False, "outside outputs/predictions"
    return True, None
