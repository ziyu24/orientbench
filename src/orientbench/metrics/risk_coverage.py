"""Risk-Coverage primitives (Bench-Core-0 skeleton).

Inputs (项目执行文件 §7.1):
    selection_score   : higher = more confident (kept first)
    orientation_risk  : lower  = better (e.g. angle error in rad/deg)

Selective prediction: order samples by selection_score DESCENDING. At coverage
c = k/n we keep the top-k most-confident samples; the selective risk is the
mean orientation_risk over those k samples.

    selective_risk(k) = mean(risk_sorted_by_score_desc[:k])
    AURC = mean_{k=1..n} selective_risk(k)            (area under risk-coverage)
    Risk@p = selective_risk at coverage p (k = ceil(p * n))

Lower AURC / Risk@p is better. NaN risks are dropped (with count reported).
Ties in score are broken deterministically (stable sort) so results are
reproducible.
"""
from __future__ import annotations

from typing import Dict, Sequence

import numpy as np


def _clean(scores: Sequence[float], risks: Sequence[float]):
    s = np.asarray(scores, dtype=float)
    r = np.asarray(risks, dtype=float)
    if s.shape != r.shape:
        raise ValueError(f"shape mismatch: scores{s.shape} risks{r.shape}")
    mask = np.isfinite(s) & np.isfinite(r)
    return s[mask], r[mask], int((~mask).sum())


def selective_risk_curve(scores: Sequence[float], risks: Sequence[float]):
    """Return (coverages, selective_risks) ordered by score descending.

    coverages = [1/n, 2/n, ..., 1.0]; selective_risks[k-1] = mean risk of the
    top-k most-confident samples.
    """
    s, r, _ = _clean(scores, risks)
    n = s.size
    if n == 0:
        return np.array([]), np.array([])
    # stable descending sort on score: negate then argsort(kind="stable")
    order = np.argsort(-s, kind="stable")
    r_sorted = r[order]
    csum = np.cumsum(r_sorted)
    ks = np.arange(1, n + 1)
    selective = csum / ks
    coverages = ks / n
    return coverages, selective


def aurc(scores: Sequence[float], risks: Sequence[float]) -> float:
    """Area under the risk-coverage curve (mean selective risk). NaN if empty."""
    _, sel = selective_risk_curve(scores, risks)
    if sel.size == 0:
        return float("nan")
    return float(np.mean(sel))


def risk_at_coverage(scores: Sequence[float], risks: Sequence[float],
                     coverage: float) -> float:
    """Selective risk at a target coverage in (0, 1]. NaN if empty/invalid."""
    if not (0.0 < coverage <= 1.0):
        raise ValueError(f"coverage must be in (0,1], got {coverage}")
    cov, sel = selective_risk_curve(scores, risks)
    n = sel.size
    if n == 0:
        return float("nan")
    k = int(np.ceil(coverage * n))
    k = max(1, min(k, n))
    return float(sel[k - 1])


def risk_coverage_summary(scores: Sequence[float], risks: Sequence[float]) -> Dict[str, float]:
    """Convenience bundle: AURC, Risk@70, Risk@90, n, n_dropped."""
    s, r, n_dropped = _clean(scores, risks)
    n = s.size
    return {
        "n": int(n),
        "n_dropped": n_dropped,
        "aurc": aurc(scores, risks),
        "risk_at_70": risk_at_coverage(scores, risks, 0.70) if n else float("nan"),
        "risk_at_90": risk_at_coverage(scores, risks, 0.90) if n else float("nan"),
    }
