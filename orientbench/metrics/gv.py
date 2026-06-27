"""GV-obliquity (Bench-Core-0).

Definition is FROZEN per 项目执行文件.md §5.3 — do not change:

    gv_ratio     = area(OBB) / area(HBB)
    gv_hbb_safe  = gv_ratio
    gv_obb_needed = 1 - gv_ratio

Interpretation:
    gv_ratio  -> 1 : OBB ~ its axis-aligned box (HBB is "safe"; near upright)
    gv_ratio  -> low : strongly oblique elongated box (HBB wastes area;
                       orientation matters, "OBB needed")

The actual monotonic direction of the *default selection score* is frozen on
the calibration split elsewhere; this module only emits the raw measurement.
"""
from __future__ import annotations

import math
from typing import Dict

from orientbench.core.geometry import obb_area, hbb_area


def gv_obliquity(w: float, h: float, theta: float) -> Dict[str, float]:
    """Return gv_ratio / gv_hbb_safe / gv_obb_needed for one OBB.

    Returns NaN fields for invalid geometry (non-finite / non-positive sides /
    degenerate HBB), never raises.
    """
    a_obb = obb_area(w, h)
    a_hbb = hbb_area(w, h, theta)
    if not (math.isfinite(a_obb) and math.isfinite(a_hbb)) or a_hbb <= 0:
        nan = float("nan")
        return {"gv_ratio": nan, "gv_hbb_safe": nan, "gv_obb_needed": nan}
    gv_ratio = a_obb / a_hbb
    return {
        "gv_ratio": gv_ratio,
        "gv_hbb_safe": gv_ratio,
        "gv_obb_needed": 1.0 - gv_ratio,
    }
