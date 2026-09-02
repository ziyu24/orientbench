"""Prediction ingestion contract (schema + validator + synthetic + format detect).

This module defines the prediction record schema, a validator, a DRY-RUN
SYNTHETIC generator (predictions derived ONLY from GT + controlled score/angle
perturbation), and a format auto-detector. It does NOT run any detector.

Synthetic predictions are always flagged:
    is_synthetic = True
    not_detector_output = True
"""
from __future__ import annotations

import json
import math
import os
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from orientbench.core.geometry import angle_error_rad

PREDICTION_SCHEMA: List[str] = [
    "dataset", "split", "image_id", "detector_id", "baseline_id", "class_name",
    "score", "obb_cx", "obb_cy", "obb_w", "obb_h", "obb_theta",
    "angle_unit", "angle_version", "source_path", "is_synthetic", "warnings",
]

_VALID_ANGLE_UNITS = {"rad", "deg"}


def validate_prediction(rec: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate one prediction record against the schema. Returns (ok, warnings)."""
    warns: List[str] = []
    for f in PREDICTION_SCHEMA:
        if f not in rec:
            warns.append(f"missing field: {f}")
    # numeric checks
    for f in ("score", "obb_cx", "obb_cy", "obb_w", "obb_h", "obb_theta"):
        v = rec.get(f)
        if not isinstance(v, (int, float)) or not math.isfinite(v):
            warns.append(f"non-finite numeric field: {f}={v!r}")
    if rec.get("obb_w", 0) <= 0 or rec.get("obb_h", 0) <= 0:
        warns.append("non-positive box side")
    if rec.get("angle_unit") not in _VALID_ANGLE_UNITS:
        warns.append(f"angle_unit not in {_VALID_ANGLE_UNITS}: {rec.get('angle_unit')!r}")
    ok = not any(w.startswith("missing field") or w.startswith("non-finite") for w in warns)
    return ok, warns


def validate_predictions(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    n_ok = 0
    all_warn: List[str] = []
    for r in records:
        ok, w = validate_prediction(r)
        n_ok += int(ok)
        all_warn.extend(w[:3])
    return {"n_total": len(records), "n_ok": n_ok,
            "n_bad": len(records) - n_ok, "warnings_sample": all_warn[:20]}


# --- synthetic generation --------------------------------------------------
def make_synthetic_prediction(
    gt: Dict[str, Any], rng: np.random.RandomState,
    detector_id: str = "synthetic_gv_proxy", baseline_id: str = "synthetic",
) -> Dict[str, Any]:
    """Build ONE synthetic prediction from a GT record.

    Angle is perturbed with a magnitude that grows with GV-obliquity (oblique
    boxes are 'harder'); score anti-correlates with the realized angle error
    plus controlled noise. Everything derives from GT — NOT a detector output.
    """
    from orientbench.metrics.gv import gv_obliquity
    g = gv_obliquity(gt["obb_w"], gt["obb_h"], gt["obb_theta"])
    obb_needed = g["gv_obb_needed"] if math.isfinite(g["gv_obb_needed"]) else 0.5
    # controlled angle perturbation (radians), harder for oblique boxes
    scale = 0.05 + 0.5 * max(0.0, obb_needed)
    err = abs(rng.randn()) * scale
    err = min(err, math.pi / 2)
    sign = 1.0 if rng.rand() > 0.5 else -1.0
    pred_theta = gt["obb_theta"] + sign * err
    # controlled score: high when (realized) error low, with noise
    realized = angle_error_rad(pred_theta, gt["obb_theta"])
    score = float(np.clip(math.exp(-3.0 * realized) + rng.randn() * 0.05, 0.0, 1.0))
    return {
        "dataset": gt["dataset"], "split": gt["split"], "image_id": gt["image_id"],
        "detector_id": detector_id, "baseline_id": baseline_id,
        "class_name": gt.get("class_name", "unknown"), "score": score,
        "obb_cx": gt["obb_cx"], "obb_cy": gt["obb_cy"],
        "obb_w": gt["obb_w"], "obb_h": gt["obb_h"], "obb_theta": pred_theta,
        "angle_unit": "rad", "angle_version": gt.get("angle_version", "unknown"),
        "source_path": "SYNTHETIC", "is_synthetic": True,
        "not_detector_output": True, "warnings": [],
    }


def generate_synthetic_predictions(
    gt_records: List[Dict[str, Any]], seed: int = 0,
    detector_id: str = "synthetic_gv_proxy",
) -> List[Dict[str, Any]]:
    rng = np.random.RandomState(seed)
    out = []
    for gt in gt_records:
        if not gt.get("valid_geometry", False):
            continue
        out.append(make_synthetic_prediction(gt, rng, detector_id=detector_id))
    return out


# --- format detection / loading -------------------------------------------
def detect_format(path: str) -> str:
    """Return a format label for a prediction file path."""
    ext = os.path.splitext(path)[1].lower()
    if ext == ".jsonl":
        return "jsonl"
    if ext == ".json":
        return "json"
    if ext == ".csv":
        return "csv"
    if ext in (".pkl", ".pickle"):
        return "pickle_placeholder"
    if ext in (".pth", ".bin") or "mmrotate" in path.lower():
        return "mmrotate_placeholder"
    return "unknown"


def load_predictions(path: Optional[str]) -> Dict[str, Any]:
    """Load real predictions if available; never raises.

    Returns {"status": ..., "format": ..., "records": [...], "warnings": [...]}.
    status is 'loaded' | 'no_prediction_available' | 'unsupported_format'.
    """
    if not path or not os.path.isfile(path):
        return {"status": "no_prediction_available", "format": None,
                "records": [], "warnings": [f"prediction file not found: {path}"]}
    fmt = detect_format(path)
    warns: List[str] = []
    records: List[Dict[str, Any]] = []
    try:
        if fmt == "jsonl":
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        records.append(json.loads(line))
        elif fmt == "json":
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            records = data if isinstance(data, list) else data.get("records", [])
        elif fmt == "csv":
            import csv
            with open(path, "r", encoding="utf-8") as fh:
                records = list(csv.DictReader(fh))
        else:
            return {"status": "unsupported_format", "format": fmt, "records": [],
                    "warnings": [f"format '{fmt}' not yet implemented (placeholder)"]}
    except Exception as e:  # noqa: BLE001
        return {"status": "unsupported_format", "format": fmt, "records": [],
                "warnings": [f"failed to parse {path}: {e}"]}
    return {"status": "loaded", "format": fmt, "records": records, "warnings": warns}
