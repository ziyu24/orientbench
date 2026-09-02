"""Optimal-transport matching with a dustbin (C1 mechanism primitive).

Matches two object sets (e.g. predictions across two views) by entropic OT with
an explicit dustbin column/row that absorbs unmatched mass. Returns the
transport plan, dustbin mass, and matched responsibility. Pure numpy (no extra
deps). This is a mechanism primitive, NOT a formal C1 conclusion.
"""
from __future__ import annotations

from typing import Any, Dict

import numpy as np


def sinkhorn_dustbin(cost: np.ndarray, dustbin_cost: float = 1.0,
                     reg: float = 0.1, n_iter: int = 200) -> Dict[str, Any]:
    """Entropic OT between n sources and m targets with a dustbin on both sides.

    cost: (n, m) matching cost (lower=better). Augment with a dustbin row+col at
    `dustbin_cost`. Uniform marginals with an extra dustbin unit each side.
    Returns plan (n+1, m+1), dustbin_mass (mass routed to dustbins), and
    matched_mass (mass on the real n x m block).
    """
    n, m = cost.shape
    if n == 0 or m == 0:
        return {"plan": np.zeros((n + 1, m + 1)), "dustbin_mass": float(max(n, m)),
                "matched_mass": 0.0, "n": n, "m": m}
    C = np.full((n + 1, m + 1), dustbin_cost, dtype=float)
    C[:n, :m] = cost
    C[n, m] = 0.0  # dustbin-to-dustbin free (absorbs leftover balancing mass)
    # SuperGlue-style marginals: each real point mass 1; dustbins absorb the
    # other side's count so totals match (n+m both sides).
    a = np.ones(n + 1); a[n] = m
    b = np.ones(m + 1); b[m] = n
    a /= a.sum(); b /= b.sum()
    K = np.exp(-C / reg)
    u = np.ones(n + 1)
    v = np.ones(m + 1)
    for _ in range(n_iter):
        u = a / (K @ v + 1e-12)
        v = b / (K.T @ u + 1e-12)
    plan = u[:, None] * K * v[None, :]
    matched = float(plan[:n, :m].sum())
    dust = float(plan[n, :m].sum() + plan[:n, m].sum())
    return {"plan": plan, "dustbin_mass": dust, "matched_mass": matched, "n": n, "m": m}


def obb_match_cost(src, tgt, w_center: float = 1.0, w_angle: float = 1.0) -> np.ndarray:
    """Cost matrix between two OBB sets by normalized center distance + angle error."""
    from orientbench.core.geometry import canonical_longside_theta
    n, m = len(src), len(tgt)
    C = np.zeros((n, m))
    for i, s in enumerate(src):
        for j, t in enumerate(tgt):
            dc = np.hypot(s["obb_cx"] - t["obb_cx"], s["obb_cy"] - t["obb_cy"])
            scale = max(1.0, (max(s["obb_w"], s["obb_h"]) + max(t["obb_w"], t["obb_h"])) / 2.0)
            a1 = canonical_longside_theta(s["obb_w"], s["obb_h"], s["obb_theta"])
            a2 = canonical_longside_theta(t["obb_w"], t["obb_h"], t["obb_theta"])
            ang = abs(((a1 - a2 + np.pi / 2) % np.pi) - np.pi / 2) / (np.pi / 2)
            C[i, j] = w_center * (dc / scale) + w_angle * ang
    return C
