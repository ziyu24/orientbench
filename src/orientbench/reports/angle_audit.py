"""angle_version audit — scan baseline configs (read-only) for angle convention.

Extracts/infers angle_version (le90/le135/oc/r360/unknown), box_type, and theta
unit from each baseline's config file (path from baseline_inventory.json). Does
NOT fabricate certainty: when the config has no clear token it falls back to the
model_id suffix and marks the source; otherwise 'unknown'. HRSC mbox dataset
angle equivalence remains 'uncertain'.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

_KNOWN_VERSIONS = ["le90", "le135", "oc", "r360"]
_VER_RE = re.compile(r"(?:angle_version|version|angle_range)\s*=\s*['\"](le90|le135|oc|r360)['\"]")
_RBOX_RE = re.compile(r"predict_box_type\s*=\s*['\"]rbox['\"]|box_type_mapping|gt_bboxes\s*=\s*['\"]rbox['\"]")


def _scan_config(path: Optional[str]) -> Dict[str, Any]:
    res = {"angle_version": "unknown", "box_type": "unknown",
           "theta_unit": "unknown", "source": "unknown", "warnings": []}
    if not path or not os.path.isfile(path):
        res["warnings"].append(f"config not found: {path}")
        return res
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            text = fh.read()
    except OSError as e:
        res["warnings"].append(f"cannot read config: {e}")
        return res
    versions = set(_VER_RE.findall(text))
    if len(versions) == 1:
        res["angle_version"] = next(iter(versions))
        res["source"] = "config_scan"
        # mmrotate stores theta in radians for le90/le135/oc internally
        res["theta_unit"] = "rad_inferred"
    elif len(versions) > 1:
        res["angle_version"] = "mixed:" + ",".join(sorted(versions))
        res["source"] = "config_scan"
        res["warnings"].append(f"multiple angle_version tokens: {sorted(versions)}")
    if _RBOX_RE.search(text):
        res["box_type"] = "rbox"
    return res


def _infer_from_model_id(model_id: str) -> Optional[str]:
    m = model_id.lower()
    for v in _KNOWN_VERSIONS:
        if m.endswith("_" + v) or ("_" + v + "_") in m or m.endswith(v):
            return v
    return None


def audit_angle_versions(inventory_json: str) -> List[Dict[str, Any]]:
    """Audit every baseline in baseline_inventory.json. Returns rows."""
    with open(inventory_json, "r", encoding="utf-8") as fh:
        inv = json.load(fh)
    rows: List[Dict[str, Any]] = []
    for r in inv["records"]:
        scan = _scan_config(r.get("config_abs"))
        angle_version = scan["angle_version"]
        source = scan["source"]
        warnings = list(scan["warnings"])
        if angle_version == "unknown":
            guess = _infer_from_model_id(r.get("model_id", ""))
            if guess:
                angle_version = guess
                source = "model_id_suffix"
                warnings.append("angle_version from model_id suffix (config token absent)")
        rows.append({
            "baseline_id": r.get("id"),
            "model_id": r.get("model_id"),
            "dataset": r.get("dataset"),
            "box_type": scan["box_type"],
            "angle_version": angle_version,
            "theta_unit": scan["theta_unit"],
            "source": source,
            "config_path": r.get("config_abs"),
            "warnings": warnings,
        })
    return rows


# dataset-level GT angle conventions (separate from baseline configs)
DATASET_ANGLE_NOTES = [
    {"dataset": "DOTA-v1.0/v1.5", "gt_angle": "le90_derived_from_poly(cv2.minAreaRect)",
     "certainty": "derived", "note": "poly8 -> minAreaRect; sign convention not asserted le90"},
    {"dataset": "DIOR-R", "gt_angle": "le90_derived_from_corners(cv2.minAreaRect)",
     "certainty": "derived", "note": "robndbox corners -> minAreaRect; raw <angle> retained"},
    {"dataset": "FAIR1M-v1.0", "gt_angle": "le90_derived_from_poly(cv2.minAreaRect)",
     "certainty": "derived", "note": "points polygon -> minAreaRect"},
    {"dataset": "HRSC2016", "gt_angle": "mbox_ang_rad",
     "certainty": "uncertain", "note": "opencv-like radians; le90 equivalence UNVERIFIED"},
]


def summarize_audit(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    counts: Dict[str, int] = {}
    src_counts: Dict[str, int] = {}
    for r in rows:
        counts[r["angle_version"]] = counts.get(r["angle_version"], 0) + 1
        src_counts[r["source"]] = src_counts.get(r["source"], 0) + 1
    return {"n_baselines": len(rows), "angle_version_counts": counts,
            "source_counts": src_counts}
