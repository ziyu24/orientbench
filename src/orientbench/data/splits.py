"""D_cal / D_audit split builder (R4, 项目执行文件 §1.4 / R4).

Deterministic, reproducible image-level hash split so D_cal ∩ D_audit = ∅.
No randomness — assignment is a pure function of (image_id, salt). D_cal is for
threshold/temperature/coverage calibration; D_audit for MVE / source-sanity /
risk-coverage audit. The two are mutually exclusive by construction.
"""
from __future__ import annotations

import hashlib
from collections import defaultdict
from typing import Any, Dict, List, Optional

DEFAULT_SALT = "orientbench_v1"
DEFAULT_CAL_FRACTION = 0.5


def hash_bucket(image_id: str, salt: str = DEFAULT_SALT, mod: int = 1000) -> int:
    """Deterministic hash bucket in [0, mod) for an image_id."""
    h = hashlib.md5(f"{salt}:{image_id}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) % mod


def assign_split(image_id: str, cal_fraction: float = DEFAULT_CAL_FRACTION,
                 salt: str = DEFAULT_SALT) -> str:
    """Return 'D_cal' or 'D_audit' deterministically."""
    return "D_cal" if hash_bucket(image_id, salt) < int(cal_fraction * 1000) else "D_audit"


def build_audit_split(
    gt_records: List[Dict[str, Any]],
    cal_fraction: float = DEFAULT_CAL_FRACTION,
    salt: str = DEFAULT_SALT,
    bucket_assignments: Optional[Dict[str, Dict[str, int]]] = None,
) -> Dict[str, Any]:
    """Split GT records' images into D_cal / D_audit by deterministic hash.

    Returns rows (one per image) + meta with disjointness verification.
    bucket_assignments: optional {image_id: {bucket: count}} for a summary col.
    """
    per_image: Dict[str, Dict[str, Any]] = {}
    for r in gt_records:
        img = r["image_id"]
        e = per_image.setdefault(img, {"dataset": r.get("dataset"), "split": r.get("split"),
                                       "object_count": 0})
        e["object_count"] += 1

    rows: List[Dict[str, Any]] = []
    cal_imgs, audit_imgs = set(), set()
    for img, e in sorted(per_image.items()):
        hb = hash_bucket(img, salt)
        assigned = "D_cal" if hb < int(cal_fraction * 1000) else "D_audit"
        (cal_imgs if assigned == "D_cal" else audit_imgs).add(img)
        bsum = ""
        if bucket_assignments and img in bucket_assignments:
            bsum = ";".join(f"{k}={v}" for k, v in bucket_assignments[img].items() if v)
        rows.append({
            "dataset": e["dataset"], "split": e["split"], "image_id": img,
            "object_count": e["object_count"], "bucket_summary_if_available": bsum,
            "assigned_split": assigned, "hash_key": hb,
        })

    intersection = cal_imgs & audit_imgs
    meta = {
        "salt": salt, "cal_fraction": cal_fraction, "n_images": len(per_image),
        "n_cal": len(cal_imgs), "n_audit": len(audit_imgs),
        "intersection_size": len(intersection),
        "mutually_exclusive": len(intersection) == 0,
        "deterministic": True, "method": "md5_hash_image_id",
    }
    return {"rows": rows, "meta": meta,
            "cal_rows": [r for r in rows if r["assigned_split"] == "D_cal"],
            "audit_rows": [r for r in rows if r["assigned_split"] == "D_audit"]}
