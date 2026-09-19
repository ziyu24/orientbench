"""Label-free sampling and queried-label-only AP estimation (NumPy only)."""
from __future__ import annotations

import numpy as np


def strata(image_ids, prediction_counts):
    """High quarter by both models' prediction counts, then numeric image ID."""
    order = sorted(range(len(image_ids)), key=lambda i: (-prediction_counts[i], int(image_ids[i])))
    cut = (len(order) + 3) // 4
    return np.asarray(order[:cut]), np.asarray(order[cut:])


def sample_plans(image_ids, prediction_counts, budgets, replicates, seed):
    """All choices fixed without any label, matching outcome or full AP input."""
    n = len(image_ids)
    high, low = strata(image_ids, prediction_counts)
    rng = np.random.Generator(np.random.PCG64(seed))
    for repetition in range(replicates):
        uniform = rng.permutation(n)
        hp, lp = rng.permutation(high), rng.permutation(low)
        for budget in budgets:
            if not 2 <= budget <= n:
                raise ValueError("budget outside population")
            picked = np.sort(uniform[:budget])
            yield repetition, budget, "srs", picked, np.full(budget, n / budget)
            nh = min(len(high), budget // 2)
            nl = budget - nh
            if nl > len(low):
                nl = len(low)
                nh = budget - nl
            picked = np.r_[hp[:nh], lp[:nl]]
            weights = np.r_[np.full(nh, len(high) / nh), np.full(nl, len(low) / nl)]
            order = np.argsort(picked)
            picked, weights = picked[order], weights[order]
            yield repetition, budget, "stratified_ht", picked, weights
            yield repetition, budget, "stratified_unweighted", picked, np.ones(budget)


def ap11(tp, fp, gt_total):
    """Weighted VOC07 plug-in AP; no unbiasedness or interval guarantee."""
    if gt_total <= 0:
        return 0.0
    tp, fp = np.cumsum(tp, dtype=np.float64), np.cumsum(fp, dtype=np.float64)
    recall = tp / gt_total
    precision = tp / np.maximum(tp + fp, np.finfo(np.float32).eps)
    return float(sum(np.max(precision[recall >= t], initial=0.0)
                     for t in np.arange(0, 1.1, .1)) / 11)


def estimate(queried, weights):
    """Only selected images enter: (global ranks, TP, FP, effective GT count).

    Query vectors keep each model's full-population prediction total order.
    Unqueried GT counts or TP/FP are not accepted by this interface.
    """
    if len(queried) != len(weights) or not len(queried):
        raise ValueError("one weight per queried image required")
    weights = np.asarray(weights, dtype=float)
    if not np.all(np.isfinite(weights) & (weights > 0)):
        raise ValueError("weights must be positive and finite")
    ranks = np.concatenate([x[0] for x in queried])
    if len(np.unique(ranks)) != len(ranks):
        raise ValueError("duplicated queried prediction positions")
    order = np.argsort(ranks)
    tp = np.concatenate([x[1] * w for x, w in zip(queried, weights)])[order]
    fp = np.concatenate([x[2] * w for x, w in zip(queried, weights)])[order]
    gt = float(sum(x[3] * w for x, w in zip(queried, weights)))
    return ap11(tp, fp, gt), gt
