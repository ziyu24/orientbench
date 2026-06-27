"""Stress buckets — Bench-Core-0 skeleton.

Only the primitives needed for v0.0 sanity are implemented here:
  - basic valid flag (geometry numerically usable);
  - near-square bucket (placeholder aspect-ratio threshold, NOT frozen);
  - padding-only view metadata placeholder.

The full bucket family (dense-coherent / dense-incoherent / sparse-bg-strong /
evidence-weak / domain-fragile / rotated-valid-mismatch) and class-conditional
percentile thresholds are deferred to Bench-Core-1 and frozen via
configs/thresholds.yaml (R8). All thresholds used here are placeholders and are
returned with a ``pending_threshold_freeze`` flag so no caller mistakes them
for approved values.
"""
from __future__ import annotations

import math
from typing import Any, Dict, Optional

from orientbench.core.constants import (
    N_MIN,
    PENDING_THRESHOLD_FREEZE,
    PLACEHOLDER_THRESHOLDS,
)


def basic_valid_flag(w: float, h: float, theta: float,
                     min_side: Optional[float] = None) -> bool:
    """Geometry is numerically usable: finite, positive, sides >= min_side."""
    if min_side is None:
        min_side = PLACEHOLDER_THRESHOLDS["min_box_side_px"]
    for v in (w, h, theta):
        if not (isinstance(v, (int, float)) and math.isfinite(v)):
            return False
    return w >= min_side and h >= min_side


def aspect_ratio(w: float, h: float) -> float:
    """max(w,h)/min(w,h); NaN if degenerate."""
    if not (math.isfinite(w) and math.isfinite(h)) or min(w, h) <= 0:
        return float("nan")
    return max(w, h) / min(w, h)


def near_square_bucket(w: float, h: float,
                       ratio_max: Optional[float] = None) -> Dict[str, Any]:
    """Near-square membership (placeholder threshold).

    Returns membership plus the placeholder marker so the caller knows the
    threshold is not frozen.
    """
    if ratio_max is None:
        ratio_max = PLACEHOLDER_THRESHOLDS["near_square_aspect_ratio_max"]
    r = aspect_ratio(w, h)
    member = bool(math.isfinite(r) and r <= ratio_max)
    return {
        "bucket": "near_square",
        "is_member": member,
        "aspect_ratio": r,
        "ratio_max_used": ratio_max,
        "pending_threshold_freeze": True,
        "threshold_status": PENDING_THRESHOLD_FREEZE,
    }


ALL_BUCKETS = [
    "near_square",
    "dense_coherent",
    "dense_incoherent",
    "sparse_bg_strong",
    "evidence_weak",
    "domain_fragile",          # placeholder (needs domain corruption probe)
    "rotated_valid_mismatch",  # placeholder (needs rotated-view valid mask)
]


def _pct(thr, key, cls, p):
    try:
        return thr["percentiles"][key][cls][f"p{p}"]
    except (KeyError, TypeError):
        return float("nan")


def assign_buckets(record: Dict[str, Any], thresholds: Dict[str, Any]) -> Dict[str, Any]:
    """Assign stress-bucket membership for one record given dry-run thresholds.

    Definitions (项目执行文件 §6.6), class-conditional percentiles:
        near_square      = aspect_ratio <= near_square_ratio_max (placeholder)
        dense_coherent   = D_nbr > class_p80 and R_nbr > class_p70
        dense_incoherent = D_nbr > class_p80 and R_nbr < class_p30
        sparse_bg_strong = n_neighbors < n_min and V_bg==1 and E_bg >= class_p70
        evidence_weak    = V_bg==0 and V_layout==0
        domain_fragile / rotated_valid_mismatch -> placeholder (needs probes)

    All membership is DRY-RUN (thresholds unfrozen); returns
    ``pending_threshold_freeze=True``.
    """
    cls = record.get("class_name", "unknown")
    members: Dict[str, bool] = {b: False for b in ALL_BUCKETS}

    # near-square (geometry placeholder threshold)
    ar = record.get("aspect_ratio")
    if ar is None:
        ar = aspect_ratio(record.get("obb_w", float("nan")), record.get("obb_h", float("nan")))
    ns = near_square_bucket(record.get("obb_w", float("nan")), record.get("obb_h", float("nan")))
    members["near_square"] = ns["is_member"]

    D = record.get("D_nbr", float("nan"))
    R = record.get("R_nbr", float("nan"))
    d_p80 = _pct(thresholds, "D_nbr", cls, 80)
    r_p70 = _pct(thresholds, "R_nbr", cls, 70)
    r_p30 = _pct(thresholds, "R_nbr", cls, 30)
    ebg_p70 = _pct(thresholds, "E_bg", cls, 70)

    if math.isfinite(D) and math.isfinite(R):
        if math.isfinite(d_p80) and math.isfinite(r_p70) and D > d_p80 and R > r_p70:
            members["dense_coherent"] = True
        if math.isfinite(d_p80) and math.isfinite(r_p30) and D > d_p80 and R < r_p30:
            members["dense_incoherent"] = True

    n_nbr = record.get("n_neighbors", 0)
    V_bg = record.get("V_bg", 0)
    E_bg = record.get("E_bg", float("nan"))
    V_layout = record.get("V_layout", 0)
    if (n_nbr is not None and n_nbr < N_MIN and V_bg == 1
            and math.isfinite(E_bg) and math.isfinite(ebg_p70) and E_bg >= ebg_p70):
        members["sparse_bg_strong"] = True
    if V_bg == 0 and V_layout == 0:
        members["evidence_weak"] = True

    return {
        "buckets": members,
        "aspect_ratio": ar,
        "pending_threshold_freeze": True,
        "threshold_status": PENDING_THRESHOLD_FREEZE,
    }


def padding_only_metadata(image_id: Optional[str] = None) -> Dict[str, Any]:
    """Placeholder metadata for the padding-only control view (§8.1).

    The padding-only view keeps target geometry unchanged and only simulates
    the padding / black border a rotated view would introduce. This is a
    metadata stub; actual view synthesis is implemented in
    orientbench/probes/padding_only.py later.
    """
    return {
        "view": "padding_only",
        "image_id": image_id,
        "rotation_applied": False,
        "geometry_unchanged": True,
        "padding_simulated": True,
        "implemented": False,
        "status": "placeholder",
    }
