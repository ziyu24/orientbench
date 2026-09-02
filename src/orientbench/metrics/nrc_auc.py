"""NRC-AUC — Normalized Risk-Coverage AUC (Bench-Core-0 skeleton).

Definition is FROZEN per 项目执行文件.md §7.4 — do not change:

    NRC-AUC = (AURC_model - AURC_oracle) / (AURC_random - AURC_oracle)

    0 = oracle (optimal selective ordering)
    1 = random baseline
    lower is better.

Deterministic skeleton baselines:
    AURC_oracle  : order samples by orientation_risk ASCENDING (best possible
                   selection ordering), then mean selective risk.
    AURC_random  : expected selective risk under a uniformly random ordering is
                   the global mean risk at every coverage, so
                   AURC_random = mean(orientation_risk).

If the denominator (AURC_random - AURC_oracle) is ~0 (degenerate: all risks
equal, no separability), NRC-AUC is undefined and returned as NaN with a flag.
"""
from __future__ import annotations

from typing import Dict, Sequence

import numpy as np

from orientbench.metrics.risk_coverage import _clean, aurc, selective_risk_curve

_DEGENERATE_EPS = 1e-12


def aurc_oracle(risks: Sequence[float]) -> float:
    """AURC under the optimal ordering (risk ascending)."""
    r = np.asarray(risks, dtype=float)
    r = r[np.isfinite(r)]
    if r.size == 0:
        return float("nan")
    # oracle = sort risk ascending; selective risk = cumulative mean
    r_sorted = np.sort(r, kind="stable")
    csum = np.cumsum(r_sorted)
    ks = np.arange(1, r.size + 1)
    return float(np.mean(csum / ks))


def aurc_random(risks: Sequence[float]) -> float:
    """Expected AURC under a uniformly random ordering = global mean risk."""
    r = np.asarray(risks, dtype=float)
    r = r[np.isfinite(r)]
    if r.size == 0:
        return float("nan")
    return float(np.mean(r))


def nrc_auc(scores: Sequence[float], risks: Sequence[float]) -> Dict[str, float]:
    """Compute NRC-AUC and its components.

    Returns a dict with aurc_model / aurc_oracle / aurc_random / nrc_auc /
    n / n_dropped / degenerate.
    """
    s, r, n_dropped = _clean(scores, risks)
    n = s.size
    if n == 0:
        return {
            "n": 0, "n_dropped": n_dropped,
            "aurc_model": float("nan"), "aurc_oracle": float("nan"),
            "aurc_random": float("nan"), "nrc_auc": float("nan"),
            "degenerate": True,
        }
    a_model = aurc(s, r)
    a_oracle = aurc_oracle(r)
    a_random = aurc_random(r)
    denom = a_random - a_oracle
    degenerate = abs(denom) < _DEGENERATE_EPS
    value = float("nan") if degenerate else (a_model - a_oracle) / denom
    return {
        "n": int(n),
        "n_dropped": n_dropped,
        "aurc_model": a_model,
        "aurc_oracle": a_oracle,
        "aurc_random": a_random,
        "nrc_auc": value,
        "degenerate": bool(degenerate),
    }
