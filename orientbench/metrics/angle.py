"""Angle-error metrics (Bench-Core-0).

Thin metric-layer wrappers around orientbench.core.geometry plus vectorized
helpers for batches of predictions. Definitions are pi-periodic per
项目执行文件.md §5.3; do not change the period.
"""
from __future__ import annotations

import math
from typing import List, Sequence

from orientbench.core.geometry import (
    angle_error_deg,
    angle_error_rad,
    canonical_longside_theta,
)

__all__ = ["angle_error_rad", "angle_error_deg", "angle_error_rad_batch",
           "orientation_angle_error_rad", "orientation_angle_error_deg"]


def orientation_angle_error_rad(wp, hp, tp, wg, hg, tg) -> float:
    """Convention-independent OBB orientation error (rad), via long-side canonicalization.

    Canonicalizes both boxes to their long-side orientation, then takes the
    pi-periodic angle error. This is the valid orientation risk for OBB,
    immune to the (w,h)<->(h,w) labeling difference between detector and GT.
    """
    return angle_error_rad(canonical_longside_theta(wp, hp, tp),
                           canonical_longside_theta(wg, hg, tg))


def orientation_angle_error_deg(wp, hp, tp, wg, hg, tg) -> float:
    return math.degrees(orientation_angle_error_rad(wp, hp, tp, wg, hg, tg))


def angle_error_rad_batch(
    theta_pred: Sequence[float], theta_gt: Sequence[float]
) -> List[float]:
    """Element-wise pi-periodic angle error (radians) over two sequences."""
    if len(theta_pred) != len(theta_gt):
        raise ValueError(
            f"length mismatch: pred={len(theta_pred)} gt={len(theta_gt)}"
        )
    return [angle_error_rad(p, g) for p, g in zip(theta_pred, theta_gt)]


def mean_angle_error_rad(
    theta_pred: Sequence[float], theta_gt: Sequence[float]
) -> float:
    """Mean angle error ignoring NaN (invalid) pairs. NaN if none valid."""
    errs = [e for e in angle_error_rad_batch(theta_pred, theta_gt) if math.isfinite(e)]
    if not errs:
        return float("nan")
    return sum(errs) / len(errs)
