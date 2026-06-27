"""OBB angle-representation contract (normalization layer).

This formalizes the le90 representation-equivalence discovered with real
predictions: (w,h,theta) and (h,w,theta+pi/2) describe the SAME rectangle. It is
a NORMALIZATION layer on top of the unchanged pi-periodic angle-error definition
(orientbench.core.geometry.angle_error_rad) — it does NOT redefine angle error.

For every comparison two audit fields are kept:
  - angle_error_raw_le90        : pi-periodic error of raw thetas (diagnostic)
  - angle_error_canonical_longside : pi-periodic error after long-side
                                   canonicalization (the OFFICIAL orientation risk)

Near-square boxes have an unstable long-axis; they are flagged so a gate can mask
them rather than trust an ill-defined orientation. Degenerate / non-finite boxes
yield NaN. Results carry metric_version + normalization_version; never overwrite
historical results across versions.
"""
from __future__ import annotations

import math
from typing import Any, Dict

from orientbench.core.geometry import angle_error_deg, angle_error_rad, canonical_longside_theta

NORMALIZATION_VERSION = "longside_v1"
METRIC_VERSION = "orientation_risk_v1"

# aspect ratio (long/short) below which orientation is treated as unstable.
NEAR_SQUARE_RATIO_MAX = 1.10


def is_near_square(w: float, h: float, ratio_max: float = NEAR_SQUARE_RATIO_MAX) -> bool:
    if not (math.isfinite(w) and math.isfinite(h)) or min(w, h) <= 0:
        return False
    return (max(w, h) / min(w, h)) <= ratio_max


def normalize_orientation(w: float, h: float, theta: float) -> Dict[str, Any]:
    """Return raw + canonical long-side orientation and the near-square flag."""
    return {
        "raw_theta": theta,
        "canonical_theta": canonical_longside_theta(w, h, theta),
        "near_square": is_near_square(w, h),
        "normalization_version": NORMALIZATION_VERSION,
    }


def angle_error_contract(wp, hp, tp, wg, hg, tg) -> Dict[str, Any]:
    """Compute both raw and canonical angle errors (deg) with audit metadata.

    The OFFICIAL orientation risk is ``angle_error_canonical_longside``.
    ``near_square`` is True if either box is near-square (orientation unstable).
    """
    raw = angle_error_deg(math.degrees(tp), math.degrees(tg))
    cp = canonical_longside_theta(wp, hp, tp)
    cg = canonical_longside_theta(wg, hg, tg)
    canon = angle_error_deg(math.degrees(cp), math.degrees(cg)) if (
        math.isfinite(cp) and math.isfinite(cg)) else float("nan")
    return {
        "angle_error_raw_le90": raw,
        "angle_error_canonical_longside": canon,
        "near_square": bool(is_near_square(wp, hp) or is_near_square(wg, hg)),
        "metric_version": METRIC_VERSION,
        "normalization_version": NORMALIZATION_VERSION,
    }


def orientation_risk_deg(wp, hp, tp, wg, hg, tg) -> float:
    """Official orientation risk = canonical long-side angle error (deg)."""
    return angle_error_contract(wp, hp, tp, wg, hg, tg)["angle_error_canonical_longside"]
