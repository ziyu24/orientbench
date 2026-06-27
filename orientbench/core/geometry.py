"""OBB geometry utilities for Bench-Core-0.

All definitions follow 项目执行文件.md §5.3. Angles are in radians, le90
convention assumed by callers; the angle-error primitive itself is pi-periodic
and convention-agnostic.

Numeric tolerance: invalid inputs (non-finite, non-positive box sides) return
``float('nan')`` rather than raising, so downstream aggregation can mask them.
"""
from __future__ import annotations

import math
from typing import Dict

HALF_PI = math.pi / 2.0


def _finite(*vals: float) -> bool:
    return all(isinstance(v, (int, float)) and math.isfinite(v) for v in vals)


def angle_error_rad(theta_pred: float, theta_gt: float) -> float:
    """Pi-periodic absolute angle error in radians, range [0, pi/2].

    delta = abs(((theta_pred - theta_gt + pi/2) % pi) - pi/2)   (项目执行文件 §5.3)
    """
    if not _finite(theta_pred, theta_gt):
        return float("nan")
    return abs(((theta_pred - theta_gt + HALF_PI) % math.pi) - HALF_PI)


def angle_error_deg(theta_pred_deg: float, theta_gt_deg: float) -> float:
    """Pi-periodic absolute angle error in degrees, range [0, 90]."""
    if not _finite(theta_pred_deg, theta_gt_deg):
        return float("nan")
    rad = angle_error_rad(math.radians(theta_pred_deg), math.radians(theta_gt_deg))
    return math.degrees(rad)


def obb_area(w: float, h: float) -> float:
    """Area of an oriented box = w * h (rotation-invariant)."""
    if not _finite(w, h) or w <= 0 or h <= 0:
        return float("nan")
    return w * h


def hbb_dims(w: float, h: float, theta: float) -> Dict[str, float]:
    """Axis-aligned bounding-box dimensions of an OBB (项目执行文件 §5.3).

    W = w*|cos t| + h*|sin t|
    H = w*|sin t| + h*|cos t|
    """
    if not _finite(w, h, theta) or w <= 0 or h <= 0:
        return {"W": float("nan"), "H": float("nan")}
    c = abs(math.cos(theta))
    s = abs(math.sin(theta))
    return {"W": w * c + h * s, "H": w * s + h * c}


def hbb_area(w: float, h: float, theta: float) -> float:
    d = hbb_dims(w, h, theta)
    if not _finite(d["W"], d["H"]):
        return float("nan")
    return d["W"] * d["H"]


def canonical_longside_theta(w: float, h: float, theta: float) -> float:
    """Canonical orientation = angle of the LONG side, in [-pi/2, pi/2).

    Resolves the OBB (w,h,theta) <-> (h,w,theta+pi/2) representation symmetry so
    angle comparison between two boxes is convention-independent. Does NOT change
    the pi-periodic angle-error definition; it only canonicalizes the box's
    orientation before comparison. GV/area are swap-invariant and unaffected.
    """
    if not _finite(w, h, theta) or w <= 0 or h <= 0:
        return float("nan")
    if w < h:
        theta = theta + HALF_PI
    return ((theta + HALF_PI) % math.pi) - HALF_PI


def obb_to_corners(cx: float, cy: float, w: float, h: float, theta: float):
    """Return the 4 corner points (4x2 list) of an OBB. NaN-safe-ish.

    Corners are ordered; caller may pass to cv2.fillPoly. Returns None if
    geometry is invalid.
    """
    if not _finite(cx, cy, w, h, theta) or w <= 0 or h <= 0:
        return None
    c, s = math.cos(theta), math.sin(theta)
    dx, dy = w / 2.0, h / 2.0
    # local corners (clockwise)
    local = [(-dx, -dy), (dx, -dy), (dx, dy), (-dx, dy)]
    return [(cx + lx * c - ly * s, cy + lx * s + ly * c) for lx, ly in local]


def obb_to_hbb(w: float, h: float, theta: float) -> Dict[str, float]:
    """Convert an OBB to its enclosing HBB: returns W, H, obb_area, hbb_area."""
    d = hbb_dims(w, h, theta)
    return {
        "W": d["W"],
        "H": d["H"],
        "obb_area": obb_area(w, h),
        "hbb_area": (d["W"] * d["H"]) if _finite(d["W"], d["H"]) else float("nan"),
    }
