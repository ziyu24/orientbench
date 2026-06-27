"""Bench-Core constants & placeholder thresholds.

IMPORTANT (R8 / 项目执行文件 §6, §9):
All gate / bucket thresholds must be FROZEN before any real experiment, via
configs/thresholds.yaml and a responsible role. The values here are
PLACEHOLDERS for skeleton/sanity wiring only and MUST NOT be used to launch
formal experiments. Every placeholder carries the marker
``PENDING_THRESHOLD_FREEZE``.
"""
from __future__ import annotations

import math

# Frozen geometric constants (not thresholds — definitional).
PI = math.pi
HALF_PI = math.pi / 2.0
ANGLE_ERROR_RANGE_RAD = (0.0, HALF_PI)

# Marker string stamped onto any value that is not yet frozen.
PENDING_THRESHOLD_FREEZE = "PENDING_THRESHOLD_FREEZE"

# Bench-Core-1 measurement constants (项目执行文件 §6.2). Definitional, not
# gate thresholds, but kept here for single-source reuse (R7).
BETA = 1.5          # sigma_i = beta * max(w_i, h_i)
N_MIN = 3           # layout availability minimum same-class neighbors
TAU_BG = 0.5        # background availability minimum valid annulus ratio
NEIGHBOR_DIST_FACTOR = 3.0  # neighbors within <= 3 * sigma_i

# ---------------------------------------------------------------------------
# PLACEHOLDER bucket thresholds — NOT FROZEN.
# Real values come from configs/thresholds.yaml after R8 freeze.
# ---------------------------------------------------------------------------
PLACEHOLDER_THRESHOLDS = {
    "status": PENDING_THRESHOLD_FREEZE,
    # near-square: aspect ratio max(w,h)/min(w,h) below this is "near square".
    "near_square_aspect_ratio_max": 1.15,
    # minimal box side (px) to treat geometry as numerically reliable.
    "min_box_side_px": 2.0,
}


def is_placeholder(threshold_block: dict) -> bool:
    """True if a threshold block is still an unfrozen placeholder."""
    return threshold_block.get("status") == PENDING_THRESHOLD_FREEZE


# ---------------------------------------------------------------------------
# Source-measurement DRY-RUN constants (项目执行文件 §6.4/§6.5).
# beta / n_min / tau_bg above are definitional (from the project file). The
# constants below (gamma, eps, annulus width, histogram bins) are NOT given a
# numeric value in the project file; they are documented DRY-RUN measurement
# constants, NOT frozen gate thresholds. They affect the magnitude of source
# scores but not the frozen definitions of GV / NRC-AUC / selection score.
# ---------------------------------------------------------------------------
EPS = 1e-9
GAMMA_ELONG = 1.0          # a(b_j) = tanh^2(gamma * |log(w_j/h_j)|) — dry-run
BG_ANNULUS_WIDTH_FACTOR = 0.5   # annulus width = factor * max(w_i,h_i) — dry-run
BG_HIST_BINS = 18          # K orientation bins over [0, pi) for P_bg — dry-run
SOURCE_DRYRUN_NOTE = "dry-run source constants (gamma/annulus/bins) not frozen"
