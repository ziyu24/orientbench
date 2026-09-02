"""angle_version EVIDENCE audit — resolve le90 with computed evidence where possible.

Evidence sources (no guessing):
  - poly datasets (DOTA/DIOR/FAIR1M): round-trip IoU of original polygon vs the
    polygon reconstructed from poly8_to_obb (cv2.minAreaRect le90), plus theta
    range ⊆ [-pi/2, pi/2). High round-trip IoU + in-range == the GT le90 parsing
    is lossless & in canonical range -> resolved_with_evidence (for GT parsing).
  - HRSC: mbox_ang range + cross-check of predicted OBB-HBB extent vs the
    annotated box_* extent. The annotated HBB is loose (independent annotation),
    so the cross-check is inconclusive -> stays uncertain (no fabrication).

Detector-side sign equivalence (prediction theta) cannot be proven without a
real prediction and remains a separate uncertain item.
"""
from __future__ import annotations

import math
import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from orientbench.core.geometry import hbb_dims, obb_to_corners
from orientbench.data.dior import parse_dior_obb_xml
from orientbench.data.dota import parse_dota_txt
from orientbench.data.gt_index import (
    DATASET_ROOT_DEFAULT,
    DATASETS,
    parse_fair1m_xml,
    poly8_to_obb,
    resolve_dataset_key,
)

HALF_PI = math.pi / 2.0

try:
    from shapely.geometry import Polygon  # type: ignore
    _HAS_SHAPELY = True
except Exception:  # pragma: no cover
    _HAS_SHAPELY = False

_POLY_PARSERS = {"dota10": parse_dota_txt, "dota15": parse_dota_txt,
                 "dior": parse_dior_obb_xml, "fair1m": parse_fair1m_xml}


def _poly_iou(p_orig, p_obb) -> Optional[float]:
    if not _HAS_SHAPELY:
        return None
    a, b = Polygon(p_orig), Polygon(p_obb)
    if not a.is_valid or not b.is_valid:
        return None
    inter = a.intersection(b).area
    union = a.area + b.area - inter
    return inter / union if union > 0 else None


def evidence_for_poly_dataset(key: str, data_root: str, split: str,
                              max_files: int = 40) -> Dict[str, Any]:
    spec = DATASETS[key]
    loc = spec["resolve"](data_root, split)
    parser = _POLY_PARSERS[key]
    ann_dir = loc["ann_dir"]
    ext = loc["ann_ext"]
    if not os.path.isdir(ann_dir):
        return {"status": "no_data", "detail": f"ann dir missing: {ann_dir}"}
    if loc.get("split_list") and os.path.isfile(loc["split_list"]):
        with open(loc["split_list"]) as fh:
            ids = [l.strip() for l in fh if l.strip()][:max_files]
    else:
        ids = sorted(f[:-len(ext)] for f in os.listdir(ann_dir) if f.endswith(ext))[:max_files]

    ious: List[float] = []
    thetas: List[float] = []
    n_obj = 0
    for image_id in ids:
        p = os.path.join(ann_dir, image_id + ext)
        if not os.path.isfile(p):
            continue
        objs, _ = parser(p)
        for o in objs:
            poly = o.get("poly")
            if not poly or len(poly) != 8:
                continue
            obb, _w = poly8_to_obb([float(x) for x in poly])
            if obb is None:
                continue
            cx, cy, w, h, th = obb
            thetas.append(th)
            corners = obb_to_corners(cx, cy, w, h, th)
            if corners is not None:
                pts_orig = [(poly[i], poly[i + 1]) for i in range(0, 8, 2)]
                iou = _poly_iou(pts_orig, corners)
                if iou is not None:
                    ious.append(iou)
            n_obj += 1
    in_range = all(-HALF_PI - 1e-6 <= t < HALF_PI + 1e-6 for t in thetas) if thetas else False
    mean_iou = sum(ious) / len(ious) if ious else float("nan")
    frac_hi = (sum(1 for i in ious if i >= 0.99) / len(ious)) if ious else 0.0
    # Resolution claim (GT-side, narrow): theta is in canonical le90 range AND the
    # (cx,cy,w,h,theta) OBB is the faithful minimum-area fit of the GT polygon.
    # Residual below 1.0 IoU reflects GT polygon non-rectangularity (annotation),
    # not an angle-convention error. Detector-side sign equivalence is separate.
    resolved = bool(ious and mean_iou >= 0.88 and in_range)
    return {
        "n_objects": n_obj, "n_iou": len(ious),
        "mean_roundtrip_iou": round(mean_iou, 5) if ious else None,
        "frac_iou_ge_0.99": round(frac_hi, 4),
        "theta_min": round(min(thetas), 4) if thetas else None,
        "theta_max": round(max(thetas), 4) if thetas else None,
        "in_le90_range": in_range,
        "status": "resolved_with_evidence" if resolved else "uncertain",
        "resolution_scope": "GT le90-range parsing fidelity (NOT detector sign equivalence)",
        "evidence": "poly->obb->poly round-trip IoU + theta range [-pi/2,pi/2)",
    }


def evidence_for_hrsc(data_root: str, split: str, max_files: int = 60) -> Dict[str, Any]:
    ann_dir = os.path.join(data_root, "HRSC2016/annfiles")
    split_list = os.path.join(data_root, "HRSC2016/splits", f"{split}.txt")
    if not os.path.isdir(ann_dir):
        return {"status": "no_data", "detail": f"ann dir missing: {ann_dir}"}
    if os.path.isfile(split_list):
        with open(split_list) as fh:
            ids = [l.strip() for l in fh if l.strip()][:max_files]
    else:
        ids = sorted(f[:-4] for f in os.listdir(ann_dir) if f.endswith(".xml"))[:max_files]

    angs: List[float] = []
    w_err: List[float] = []
    h_err: List[float] = []
    for image_id in ids:
        p = os.path.join(ann_dir, image_id + ".xml")
        if not os.path.isfile(p):
            continue
        try:
            root = ET.parse(p).getroot()
        except Exception:  # noqa: BLE001
            continue
        cont = root.find("HRSC_Objects")
        if cont is None:
            continue
        for o in cont.findall("HRSC_Object"):
            try:
                w = float(o.find("mbox_w").text); h = float(o.find("mbox_h").text)
                ang = float(o.find("mbox_ang").text)
                xmin = float(o.find("box_xmin").text); xmax = float(o.find("box_xmax").text)
                ymin = float(o.find("box_ymin").text); ymax = float(o.find("box_ymax").text)
            except (AttributeError, ValueError, TypeError):
                continue
            angs.append(ang)
            d = hbb_dims(w, h, ang)
            aw, ah = (xmax - xmin), (ymax - ymin)
            if aw > 0 and ah > 0 and math.isfinite(d["W"]):
                w_err.append(abs(d["W"] - aw) / aw)
                h_err.append(abs(d["H"] - ah) / ah)
    in_range = all(-HALF_PI - 1e-6 <= a < HALF_PI + 1e-6 for a in angs) if angs else False
    mean_w_err = sum(w_err) / len(w_err) if w_err else float("nan")
    mean_h_err = sum(h_err) / len(h_err) if h_err else float("nan")
    # annotated HBB is loose -> cross-check inconclusive -> remain uncertain
    hbb_consistent = bool(w_err and mean_w_err < 0.05 and mean_h_err < 0.05)
    status = "resolved_with_evidence" if (in_range and hbb_consistent) else "uncertain"
    return {
        "n_objects": len(angs), "ang_in_le90_range": in_range,
        "mean_hbb_W_relerr": round(mean_w_err, 4) if w_err else None,
        "mean_hbb_H_relerr": round(mean_h_err, 4) if h_err else None,
        "hbb_crosscheck_consistent": hbb_consistent,
        "status": status,
        "evidence": "mbox_ang range + OBB-HBB extent vs annotated box_* (loose -> inconclusive)",
    }


def build_angle_evidence_audit(data_root: str = DATASET_ROOT_DEFAULT,
                               max_files: int = 40) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    for key, split in [("dota10", "train"), ("dota15", "train"),
                       ("dior", "trainval"), ("fair1m", "train")]:
        ev = evidence_for_poly_dataset(key, data_root, split, max_files)
        rows.append({"dataset": DATASETS[key]["name"], "split": split, **ev})
    hrsc = evidence_for_hrsc(data_root, "trainval", max_files=max(max_files, 60))
    rows.append({"dataset": "HRSC2016", "split": "trainval", **hrsc})

    # minAreaRect normalization: resolved if all poly datasets round-tripped
    poly_resolved = all(r["status"] == "resolved_with_evidence"
                        for r in rows if r["dataset"].startswith(("DOTA", "DIOR", "FAIR1M")))
    rows.append({
        "dataset": "Bench-Core minAreaRect", "split": "n/a",
        "status": "resolved_with_evidence" if poly_resolved else "uncertain",
        "evidence": "le90 [-pi/2,pi/2) normalization round-trips on poly datasets",
    })
    # prediction theta unit: no real prediction -> uncertain
    rows.append({"dataset": "prediction theta unit", "split": "n/a", "status": "uncertain",
                 "evidence": "no real detector prediction ingested yet"})

    n_resolved = sum(1 for r in rows if r["status"] == "resolved_with_evidence")
    n_uncertain = sum(1 for r in rows if r["status"] == "uncertain")
    return {"n_items": len(rows), "n_resolved": n_resolved, "n_uncertain": n_uncertain,
            "hrsc_status": hrsc["status"], "rows": rows}
