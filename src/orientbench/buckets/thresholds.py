"""Class-conditional bucket thresholds (DRY-RUN).

Computes per-class percentiles of source measures (D_nbr, R_nbr, E_bg, ...)
used to assign stress buckets. While thresholds.yaml is unfrozen these are
DRY-RUN percentiles, every emitted threshold block carries
``pending_threshold_freeze=True`` (R8).
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List

from orientbench.core.constants import PENDING_THRESHOLD_FREEZE
from orientbench.metrics.statistics import class_conditional_percentiles

# percentile points referenced by bucket definitions (项目执行文件 §6.6)
BUCKET_PERCENTILES = (10, 30, 70, 80, 90)

# value keys whose class-conditional percentiles drive the buckets
BUCKET_SOURCE_KEYS = ("D_nbr", "R_nbr", "E_bg", "gv_ratio", "aspect_ratio")


def compute_bucket_thresholds(records: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    """Compute class-conditional percentile tables for the bucket source keys.

    Returns {"status": pending, "percentiles": {key: {class: {pXX: val}}}}.
    """
    recs = list(records)
    table: Dict[str, Dict[str, Dict[str, float]]] = {}
    for key in BUCKET_SOURCE_KEYS:
        table[key] = class_conditional_percentiles(
            recs, value_key=key, p_list=BUCKET_PERCENTILES
        )
    return {
        "status": PENDING_THRESHOLD_FREEZE,
        "pending_threshold_freeze": True,
        "percentiles": table,
        "percentile_points": list(BUCKET_PERCENTILES),
    }
