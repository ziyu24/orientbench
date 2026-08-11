#!/usr/bin/env python3
"""Attempt the pinned package's normal import without installation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np


VECTORS = {
    "tie": ([0.9, 0.8, 0.8, 0.1], [0.0, 1.0, 0.0, 1.0]),
    "binary": ([0.95, 0.6, 0.4, 0.2], [0.0, 1.0, 1.0, 0.0]),
    "continuous": ([0.91, 0.73, 0.41, 0.19], [0.1, 0.4, 0.8, 0.2]),
    "boundary": ([1.0, 0.0], [0.0, 1.0]),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkout", type=Path, required=True)
    args = parser.parse_args()
    def deny_network(event, _arguments):
        if event in {"socket.connect", "socket.bind", "socket.getaddrinfo"}:
            raise RuntimeError(f"network disabled during pinned reference import: {event}")
    sys.addaudithook(deny_network)
    sys.path.insert(0, str(args.checkout.resolve()))
    from fd_shifts.analysis.rc_stats import RiskCoverageStats

    output = {}
    for name, (score, residual) in VECTORS.items():
        stats = RiskCoverageStats(
            confids=np.asarray(score, dtype=np.float64),
            residuals=np.asarray(residual, dtype=np.float64),
        )
        curve = stats.curve_stats_generalized_risk
        output[name] = {
            "coverages": np.asarray(curve["coverages"], dtype=float).tolist(),
            "risks": np.asarray(curve["risks"], dtype=float).tolist(),
            "augrc_display": float(stats.augrc),
            "auc_display_scale": int(stats.AUC_DISPLAY_SCALE),
        }
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__":
    main()
