"""Default selection score — Bench-Core (项目执行文件 §7.2).

The FROZEN default-score *definitions* per detector head type live in
orientbench.core.registry. This module produces DRY-RUN demo scores from GT/GV
when no detector predictions exist yet.

DRY-RUN scores are explicitly:
    - NOT detector predictions,
    - NOT formal calibration (monotonic direction frozen on D_cal later),
    - NOT official results.

Convention: higher selection_score = more confident = expected lower
orientation risk (kept first in risk-coverage). For the GV-obliquity proxy a
higher gv_hbb_safe (closer to upright/HBB-safe) is treated as lower orientation
risk in this DRY-RUN demo only.
"""
from __future__ import annotations

import math
from typing import Any, Dict

from orientbench.core.registry import default_score_for_head
from orientbench.metrics.gv import gv_obliquity

DRYRUN_FLAGS = {
    "not_detector_prediction": True,
    "not_formal_calibration": True,
    "not_official_result": True,
}


def dryrun_gv_proxy_score(record: Dict[str, Any]) -> float:
    """DRY-RUN selection score = gv_hbb_safe (calibrated direction NOT frozen).

    Returns NaN for invalid geometry.
    """
    g = gv_obliquity(record.get("obb_w", float("nan")),
                     record.get("obb_h", float("nan")),
                     record.get("obb_theta", float("nan")))
    return g["gv_hbb_safe"]


def dryrun_scores_for_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Produce the dry-run default score + provenance flags for one record."""
    score = dryrun_gv_proxy_score(record)
    return {
        "default_selection_score": score,
        "score_definition": "calibrated_gv_obliquity_proxy",
        "score_mode": "dry_run",
        **DRYRUN_FLAGS,
    }


def head_type_definitions() -> Dict[str, str]:
    """Return the frozen default-score definition per head type (for reports)."""
    return {
        "angle_distribution_head": default_score_for_head("angle_distribution_head"),
        "pure_regression_head": default_score_for_head("pure_regression_head"),
        "native_quality_head": default_score_for_head("native_quality_head"),
    }
