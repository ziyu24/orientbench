"""Statistics helpers for Bench-Core (percentiles, saturation, entropy).

Shared so buckets / sources / reports use one definition (R7).
"""
from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional, Sequence

import numpy as np


def saturate(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clip x into [lo, hi]; NaN passes through as NaN."""
    if not math.isfinite(x):
        return float("nan")
    return max(lo, min(hi, x))


def nan_percentile(values: Sequence[float], p: float) -> float:
    """p-th percentile (p in [0,100]) ignoring NaN. NaN if empty."""
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        return float("nan")
    return float(np.percentile(arr, p))


def class_conditional_percentiles(
    records: Iterable[Dict[str, Any]],
    value_key: str,
    class_key: str = "class_name",
    p_list: Sequence[float] = (10, 30, 70, 80, 90),
) -> Dict[str, Dict[str, float]]:
    """Compute per-class percentiles of ``value_key``.

    Returns {class_name: {"p10": .., "p30": .., ..., "n": int}}.
    Records with non-finite value are ignored for that class.
    """
    buckets: Dict[str, List[float]] = {}
    for r in records:
        v = r.get(value_key)
        if isinstance(v, (int, float)) and math.isfinite(v):
            buckets.setdefault(r.get(class_key, "unknown"), []).append(float(v))
    out: Dict[str, Dict[str, float]] = {}
    for cls, vals in buckets.items():
        entry = {f"p{int(p)}": nan_percentile(vals, p) for p in p_list}
        entry["n"] = len(vals)
        out[cls] = entry
    return out


def normalized_entropy(hist: Sequence[float]) -> float:
    """H(p)/log(K) for a histogram, in [0,1]. NaN if empty/zero-mass."""
    arr = np.asarray(hist, dtype=float)
    arr = arr[np.isfinite(arr)]
    total = arr.sum()
    if arr.size <= 1 or total <= 0:
        return float("nan")
    p = arr / total
    p = p[p > 0]
    h = -np.sum(p * np.log(p))
    return float(h / math.log(arr.size))


def summarize(values: Sequence[float]) -> Dict[str, float]:
    """mean/median/p10/p90/min/max/n ignoring NaN."""
    arr = np.asarray(values, dtype=float)
    arr = arr[np.isfinite(arr)]
    if arr.size == 0:
        out = {k: float("nan") for k in ("mean", "median", "p10", "p90", "min", "max")}
        out["n"] = 0
        return out
    return {
        "mean": float(np.mean(arr)),
        "median": float(np.median(arr)),
        "p10": float(np.percentile(arr, 10)),
        "p90": float(np.percentile(arr, 90)),
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "n": int(arr.size),
    }
