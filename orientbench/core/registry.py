"""Detector taxonomy & registry (D2, 项目执行文件 §0/§7.2, R6).

Defines the 9-detector archetype taxonomy used by the probe prediction matrix
and the default-selection-score mapping. Availability is recorded honestly:
RHINO-style rotated DETR is MISSING (not substituted by ARS-DETR); the A4
hybrid-encoder host is a pending frozen snapshot.

angle head type -> Bench-Core default selection score (§7.2, FROZEN definition):
    angle_distribution_head : negative normalized angle entropy
    pure_regression_head    : calibrated GV-obliquity proxy
    native_quality_head     : native score + Bench-Core default (comparison)
"""
from __future__ import annotations

from typing import Any, Dict, List

# head type -> default selection score (frozen definition names)
HEAD_DEFAULT_SCORE = {
    "angle_distribution_head": "negative_normalized_angle_entropy",
    "pure_regression_head": "calibrated_gv_obliquity_proxy",
    "native_quality_head": "native_plus_benchcore_default_comparison",
}

# 9-detector archetype taxonomy. `example_families` map to readme baseline ids.
DETECTOR_TAXONOMY: List[Dict[str, Any]] = [
    {"archetype": "two_stage_regression", "head_type": "pure_regression_head",
     "example_families": ["oriented_rcnn_r50"], "available": True,
     "notes": "Oriented R-CNN R50 two-stage angle regression"},
    {"archetype": "two_stage_regression_strong_backbone", "head_type": "pure_regression_head",
     "example_families": ["oriented_rcnn_lsknet_s", "strip_rcnn_s"], "available": True,
     "notes": "LSKNet / Strip R-CNN strong-backbone two-stage"},
    {"archetype": "one_stage_regression", "head_type": "pure_regression_head",
     "example_families": ["rotated_retinanet_r50"], "available": True,
     "notes": "Rotated RetinaNet vanilla regression"},
    {"archetype": "one_stage_dense_realtime", "head_type": "pure_regression_head",
     "example_families": ["rotated_rtmdet_s", "rotated_rtmdet_m"], "available": True,
     "notes": "Rotated RTMDet real-time dense"},
    {"archetype": "angle_coder_psc", "head_type": "angle_distribution_head",
     "example_families": ["rotated_retinanet_psc_r50"], "available": True,
     "notes": "PSC angle-coder -> phase distribution"},
    {"archetype": "detr_angle_distribution", "head_type": "angle_distribution_head",
     "example_families": ["arsdetr_r50"], "available": True,
     "notes": "ARS-DETR ARCSL angle distribution (NOT a RHINO substitute)"},
    {"archetype": "rotated_detr_rhino", "head_type": "angle_distribution_head",
     "example_families": ["rhino"], "available": False,
     "notes": "RHINO-style rotated DETR — MISSING in pth_data/readme.md (C1/B host, R6)"},
    {"archetype": "weakly_supervised", "head_type": "pure_regression_head",
     "example_families": ["h2rbox_v2_r50", "point2rbox_v2_r50"], "available": True,
     "notes": "weak-supervision OBB (H2RBox-v2 / Point2RBox-v2)"},
    {"archetype": "pseudo_label", "head_type": "pure_regression_head",
     "example_families": ["rotated_fcos_r50_pseudo"], "available": True,
     "notes": "Rotated FCOS pseudo-label baseline"},
]

# A4 host is tracked separately (frozen hybrid-encoder oriented DETR, R3/R6).
A4_HOST = {
    "name": "hybrid_encoder_oriented_detr",
    "role": "A4 source-attribution host",
    "available": False,
    "status": "frozen_snapshot_pending",
    "notes": "A-gate-1 must run on this frozen host; not yet provided",
}


def default_score_for_head(head_type: str) -> str:
    return HEAD_DEFAULT_SCORE.get(head_type, "unknown")


def taxonomy_availability() -> Dict[str, int]:
    avail = sum(1 for d in DETECTOR_TAXONOMY if d["available"])
    return {"n_archetypes": len(DETECTOR_TAXONOMY), "n_available": avail,
            "n_missing": len(DETECTOR_TAXONOMY) - avail}
