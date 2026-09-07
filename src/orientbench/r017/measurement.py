"""Frozen probability fusion and actual supervised loss for the r017 pilot."""
import numpy as np


def weighted_log_loss(probability, target, valid, foreground_fraction):
    if not 0 < foreground_fraction < 1:
        raise ValueError("training foreground fraction must be strictly between zero and one")
    p = np.asarray(probability, dtype=np.float64)
    y = np.asarray(target, dtype=np.float64)
    mask = np.asarray(valid, dtype=bool)
    if p.shape != y.shape or mask.shape != y.shape or not mask.any():
        raise ValueError("matching arrays and nonempty common mask required")
    if not np.isfinite(p[mask]).all() or not np.isin(y[mask], [0, 1]).all():
        raise ValueError("finite probabilities and binary labels required")
    if ((p[mask] < 0) | (p[mask] > 1)).any():
        raise ValueError("probabilities must lie in [0,1]")
    p, y = np.clip(p[mask], 1e-6, 1 - 1e-6), y[mask]
    weights = np.where(y == 1, 1 / (2 * foreground_fraction), 1 / (2 * (1 - foreground_fraction)))
    return float(np.mean(weights * (-y * np.log(p) - (1 - y) * np.log1p(-p))))


def crossed_comparison(a, b, u, v, target, valid, foreground_fraction):
    arrays = [np.asarray(p, dtype=np.float64) for p in (a, b, u, v)]
    if any(p.shape != np.shape(target) for p in arrays):
        raise ValueError("all four views must share the target grid")
    mask = np.asarray(valid, dtype=bool)
    if mask.shape != np.shape(target):
        raise ValueError("common mask must share the target grid")
    for p in arrays:
        if not np.isfinite(p[mask]).all() or ((p[mask] < 0) | (p[mask] > 1)).any():
            raise ValueError("each view must contain finite probabilities in [0,1]")
    a, b, u, v = arrays
    loss = lambda p: weighted_log_loss(p, target, valid, foreground_fraction)
    au, av, bv, bu = [loss((x + z) / 2) for x, z in ((a, u), (a, v), (b, v), (b, u))]
    return {"loss_au": au, "loss_av": av, "loss_bv": bv, "loss_bu": bu,
            "delta_a": au - av, "delta_b": bv - bu,
            "primary": ((au - av) + (bv - bu)) / 2}
