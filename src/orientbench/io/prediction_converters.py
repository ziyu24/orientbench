"""COCO-style / pseudo-label -> prediction schema converters.

Detects the bbox representation per record and converts to the 17-field
prediction schema. HONEST flagging:
  - 4-value [x,y,w,h]  -> HBB: bbox_only=True, obb_unavailable=True,
                          not_orientation_prediction=True (theta=0 placeholder).
  - 5-value [cx,cy,w,h,theta] -> rotated OBB: carries orientation, but angle
                          version/unit unverified and class mapping unknown.
  - 8-value poly       -> minAreaRect -> OBB.
HBB bbox is NEVER presented as an OBB prediction. Everything carries
not_formal_gate=True (pseudo-label / unverified provenance) — usable only to
exercise ingestion/matching, NOT for a formal angle-error gate.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from orientbench.data.gt_index import poly8_to_obb


def detect_bbox_kind(bbox: List[float]) -> str:
    n = len(bbox) if isinstance(bbox, (list, tuple)) else -1
    if n == 4:
        return "hbb_xywh"
    if n == 5:
        return "obb_cxcywha"
    if n == 8:
        return "poly8"
    return "unknown"


def convert_coco_record(
    rec: Dict[str, Any], dataset: str, split: str,
    detector_id: str, baseline_id: Optional[str], source_path: str,
) -> Dict[str, Any]:
    bbox = rec.get("bbox", [])
    kind = detect_bbox_kind(bbox)
    warns: List[str] = ["needs_category_mapping: category_id->class_name unknown"]
    bbox_only = False
    obb_unavailable = False
    not_orientation = False
    cx = cy = w = h = theta = float("nan")
    angle_unit = "rad"
    angle_version = "uncertain"

    if kind == "obb_cxcywha":
        cx, cy, w, h, theta = (float(bbox[0]), float(bbox[1]), float(bbox[2]),
                               float(bbox[3]), float(bbox[4]))
        angle_version = "uncertain_pseudo_label(le90?)"
    elif kind == "poly8":
        obb, w_msg = poly8_to_obb([float(x) for x in bbox])
        if obb is not None:
            cx, cy, w, h, theta = obb
            angle_version = "le90_derived_from_poly(cv2.minAreaRect)"
        if w_msg:
            warns.append(w_msg)
    elif kind == "hbb_xywh":
        x, y, bw, bh = (float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
        cx, cy, w, h, theta = x + bw / 2.0, y + bh / 2.0, bw, bh, 0.0
        bbox_only = True
        obb_unavailable = True
        not_orientation = True
        angle_version = "n/a_hbb"
        warns.append("HBB bbox; theta=0 placeholder; NOT an orientation prediction")
    else:
        warns.append(f"unknown bbox kind (len={len(bbox) if isinstance(bbox, list) else '?'})")

    return {
        "dataset": dataset, "split": split,
        "image_id": str(rec.get("image_id")),
        "detector_id": detector_id, "baseline_id": baseline_id,
        "class_name": f"category_{rec.get('category_id')}",
        "score": float(rec.get("score", 0.0)),
        "obb_cx": cx, "obb_cy": cy, "obb_w": w, "obb_h": h, "obb_theta": theta,
        "angle_unit": angle_unit, "angle_version": angle_version,
        "source_path": source_path, "is_synthetic": False,
        # honest provenance flags
        "source_bbox_kind": kind,
        "bbox_only": bbox_only, "obb_unavailable": obb_unavailable,
        "not_orientation_prediction": not_orientation,
        "not_formal_gate": True, "needs_category_mapping": True,
        "warnings": warns,
    }


def convert_coco_records(
    records: List[Dict[str, Any]], dataset: str, split: str,
    detector_id: str, baseline_id: Optional[str], source_path: str,
    max_records: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    kinds: Dict[str, int] = {}
    truncated = False
    for i, rec in enumerate(records):
        if max_records is not None and max_records >= 0 and i >= max_records:
            truncated = True
            break
        c = convert_coco_record(rec, dataset, split, detector_id, baseline_id, source_path)
        kinds[c["source_bbox_kind"]] = kinds.get(c["source_bbox_kind"], 0) + 1
        out.append(c)
    n_bbox_only = sum(1 for c in out if c["bbox_only"])
    n_oriented = sum(1 for c in out if not c["bbox_only"] and math.isfinite(c["obb_theta"]))
    stats = {
        "n_source_records": len(records), "n_converted": len(out),
        "truncated": truncated, "bbox_kind_counts": kinds,
        "n_bbox_only": n_bbox_only, "n_oriented": n_oriented,
        "all_not_formal_gate": True,
        "any_can_enter_formal_angle_gate": False,  # pseudo-label / unverified
    }
    return out, stats


# DOTA class name orderings (label index -> class_name)
DOTA10_CLASSES = ["plane", "baseball-diamond", "bridge", "ground-track-field",
                  "small-vehicle", "large-vehicle", "ship", "tennis-court",
                  "basketball-court", "storage-tank", "soccer-ball-field",
                  "roundabout", "harbor", "swimming-pool", "helicopter"]
DOTA15_CLASSES = DOTA10_CLASSES + ["container-crane"]

_DATASET_CLASSES = {"DOTA-v1.0": DOTA10_CLASSES, "DOTA-v1.5": DOTA15_CLASSES}


def convert_mmrotate1x_pkl(pkl_path, dataset, split, detector_id, baseline_id,
                           angle_version="le90", max_records=None):
    """Convert an mmrotate-1.x test --out pkl to the prediction schema.

    pkl = list of per-image dicts with img_id + pred_instances{bboxes(N,5
    [cx,cy,w,h,theta-rad]), labels, scores}. angle is le90 radians (config).
    Returns (records, stats). is_synthetic=False; not_formal_gate=True (smoke).
    """
    import pickle
    import numpy as np
    with open(pkl_path, "rb") as fh:
        data = pickle.load(fh)
    classes = _DATASET_CLASSES.get(dataset)
    out = []
    n_img = 0
    for rec in data:
        n_img += 1
        if isinstance(rec, dict):
            img_id = rec.get("img_id") or rec.get("img_path", "")
            pi = rec.get("pred_instances", {})
            getf = pi.get
        else:  # DetDataSample (DumpDetResults) — attribute access
            img_id = getattr(rec, "img_id", None) or rec.metainfo.get("img_id") or \
                rec.metainfo.get("img_path", "")
            pi = rec.pred_instances
            getf = lambda k, _pi=pi: getattr(_pi, k)
        bb = getf("bboxes")
        sc = getf("scores")
        lb = getf("labels")
        bb = bb.numpy() if hasattr(bb, "numpy") else np.asarray(bb)
        sc = sc.numpy() if hasattr(sc, "numpy") else np.asarray(sc)
        lb = lb.numpy() if hasattr(lb, "numpy") else np.asarray(lb)
        for i in range(len(bb)):
            if max_records is not None and len(out) >= max_records:
                break
            cx, cy, w, h, th = [float(x) for x in bb[i][:5]]
            lab = int(lb[i])
            cname = classes[lab] if (classes and 0 <= lab < len(classes)) else f"label_{lab}"
            out.append({
                "dataset": dataset, "split": split, "image_id": str(img_id),
                "detector_id": detector_id, "baseline_id": baseline_id,
                "class_name": cname, "score": float(sc[i]),
                "obb_cx": cx, "obb_cy": cy, "obb_w": w, "obb_h": h, "obb_theta": th,
                "angle_unit": "rad", "angle_version": angle_version,
                "source_path": pkl_path, "is_synthetic": False,
                "not_formal_gate": True, "source_bbox_kind": "mmrotate1x_rbox",
                "warnings": [],
            })
    stats = {"n_images": n_img, "n_detections": len(out), "is_synthetic": False,
             "angle_version": angle_version, "all_not_formal_gate": True}
    return out, stats
