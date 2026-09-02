"""DropRate + view-consistency risk (C1 mechanism primitives)."""
from __future__ import annotations

from typing import Any, Dict, List

import numpy as np

from orientbench.metrics.angle import orientation_angle_error_deg


def drop_rate(n_objects: int, n_responsible: int) -> float:
    """Fraction of objects that lost responsibility (dropped) across views."""
    if n_objects <= 0:
        return float("nan")
    return float(max(0, n_objects - n_responsible) / n_objects)


def view_consistency_risk(pairs: List[Dict[str, Any]]) -> Dict[str, float]:
    """Orientation risk delta across matched cross-view pairs.

    pairs: list of {a:{obb...}, b:{obb...}} matched across views. Returns mean/
    median canonical orientation error (deg) between the two views.
    """
    errs = []
    for p in pairs:
        a, b = p["a"], p["b"]
        e = orientation_angle_error_deg(a["obb_w"], a["obb_h"], a["obb_theta"],
                                        b["obb_w"], b["obb_h"], b["obb_theta"])
        if np.isfinite(e):
            errs.append(e)
    if not errs:
        return {"mean": float("nan"), "median": float("nan"), "n": 0}
    return {"mean": float(np.mean(errs)), "median": float(np.median(errs)),
            "p90": float(np.percentile(errs, 90)), "n": len(errs)}
