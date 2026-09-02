"""Probe prediction matrix TEMPLATE (D2, 项目执行文件 §0 item 6).

Emits a detector × probe template with pre-registered expectation placeholders.
This is a TEMPLATE, not measured results. Missing detectors/datasets are marked
explicitly; ARS-DETR is NOT presented as RHINO.
"""
from __future__ import annotations

from typing import Any, Dict, List

from orientbench.core.registry import A4_HOST, DETECTOR_TAXONOMY, default_score_for_head

PROBES = ["background_phase", "layout_masking", "domain_survival"]

MISSING_NOTES = [
    "RHINO-style rotated DETR missing",
    "A4 hybrid-host frozen snapshot pending",
    "SODA-A dataset missing",
    "ICDAR-MLT dataset missing",
]


def build_probe_matrix_template() -> List[Dict[str, Any]]:
    """One row per (detector archetype × probe), all cells pending/expected-only."""
    rows: List[Dict[str, Any]] = []
    for det in DETECTOR_TAXONOMY:
        for probe in PROBES:
            rows.append({
                "archetype": det["archetype"],
                "head_type": det["head_type"],
                "default_score": default_score_for_head(det["head_type"]),
                "available": det["available"],
                "probe": probe,
                "expected_effect": "PENDING_PREREGISTRATION",
                "measured_effect": "PENDING_MEASUREMENT",
                "is_template": True,
                "notes": det["notes"],
            })
    # A4 host as a separate informational row
    for probe in PROBES:
        rows.append({
            "archetype": A4_HOST["name"],
            "head_type": "native_quality_head",
            "default_score": default_score_for_head("native_quality_head"),
            "available": A4_HOST["available"],
            "probe": probe,
            "expected_effect": "PENDING_PREREGISTRATION",
            "measured_effect": "PENDING_MEASUREMENT",
            "is_template": True,
            "notes": A4_HOST["notes"],
        })
    return rows
