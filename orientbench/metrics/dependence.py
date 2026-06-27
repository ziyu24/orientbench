"""Dependence statistics for A4 source attribution: partial correlation + HSIC.

partial_correlation(x, y | Z): Pearson corr of residuals after regressing x and y
on covariates Z (e.g. GV + class dummies). HSIC: kernel dependence with an RBF
kernel and a permutation p-value (controlled sampling for cost). Pure numpy.
Mechanism primitives, NOT formal A4 conclusions.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

import numpy as np


def _residualize(v: np.ndarray, Z: np.ndarray) -> np.ndarray:
    # least-squares residual of v on [1, Z]
    X = np.column_stack([np.ones(len(v)), Z]) if Z.ndim and Z.size else np.ones((len(v), 1))
    beta, *_ = np.linalg.lstsq(X, v, rcond=None)
    return v - X @ beta


def partial_correlation(x, y, Z=None) -> float:
    """Partial Pearson correlation of x,y controlling for covariates Z."""
    x = np.asarray(x, float); y = np.asarray(y, float)
    if len(x) < 3:
        return float("nan")
    if Z is None:
        rx, ry = x - x.mean(), y - y.mean()
    else:
        Z = np.asarray(Z, float)
        if Z.ndim == 1:
            Z = Z[:, None]
        rx, ry = _residualize(x, Z), _residualize(y, Z)
    d = np.sqrt((rx ** 2).sum() * (ry ** 2).sum())
    return float((rx * ry).sum() / d) if d > 0 else float("nan")


def _rbf(a: np.ndarray, sigma: Optional[float] = None) -> np.ndarray:
    a = a.reshape(-1, 1)
    d2 = (a - a.T) ** 2
    if sigma is None:
        med = np.median(d2[d2 > 0]) if np.any(d2 > 0) else 1.0
        sigma = np.sqrt(med / 2) if med > 0 else 1.0
    return np.exp(-d2 / (2 * sigma ** 2 + 1e-12))


def hsic(x, y, max_samples: int = 800, n_perm: int = 200, seed: int = 0) -> Dict[str, Any]:
    """Biased HSIC statistic + permutation p-value. Controlled sampling if large."""
    rng = np.random.RandomState(seed)
    x = np.asarray(x, float); y = np.asarray(y, float)
    n = len(x)
    truncated = False
    if n > max_samples:
        idx = rng.choice(n, max_samples, replace=False)
        x, y = x[idx], y[idx]
        n = max_samples
        truncated = True
    if n < 5:
        return {"hsic": float("nan"), "p_value": float("nan"), "n": n, "truncated": truncated}
    K = _rbf(x); L = _rbf(y)
    H = np.eye(n) - np.ones((n, n)) / n
    Kc = H @ K @ H
    stat = float(np.sum(Kc * (H @ L @ H)) / (n - 1) ** 2)
    # permutation null
    ge = 0
    Lc0 = H @ L @ H
    for _ in range(n_perm):
        p = rng.permutation(n)
        Lp = Lc0[np.ix_(p, p)]
        s = np.sum(Kc * Lp) / (n - 1) ** 2
        if s >= stat:
            ge += 1
    pval = (ge + 1) / (n_perm + 1)
    return {"hsic": stat, "p_value": float(pval), "n": n, "n_perm": n_perm,
            "max_samples": max_samples, "seed": seed, "truncated": truncated}


def bootstrap_ci(values, stat_fn=np.mean, n_boot: int = 500, seed: int = 0,
                 alpha: float = 0.05) -> Dict[str, float]:
    rng = np.random.RandomState(seed)
    v = np.asarray(values, float)
    v = v[np.isfinite(v)]
    if len(v) < 3:
        return {"point": float("nan"), "lo": float("nan"), "hi": float("nan"), "n": len(v)}
    boots = [stat_fn(v[rng.randint(0, len(v), len(v))]) for _ in range(n_boot)]
    return {"point": float(stat_fn(v)), "lo": float(np.percentile(boots, 100 * alpha / 2)),
            "hi": float(np.percentile(boots, 100 * (1 - alpha / 2))), "n": len(v)}
