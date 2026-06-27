"""GT index builder (Bench-Core-0 data layer).

Produces a flat per-instance GT index with a fixed schema, shared across
datasets so geometry/GV/angle primitives have one input contract (R7).

Geometry conversion: a quadrilateral (DOTA poly8 / DIOR robndbox corners /
FAIR1M points) is converted to an OBB via cv2.minAreaRect, then theta is
normalized to [-pi/2, pi/2) (le90-style range). HRSC supplies (cx,cy,w,h,ang)
directly. GV-obliquity and aspect ratio are sign-invariant, so the exact le90
sign convention does not affect this sanity layer; the derived nature of the
angle is recorded honestly in ``angle_version`` (not asserted as ground-truth
le90).

Schema (one row per GT instance):
    dataset, split, image_id, image_path, annotation_path, class_name,
    obb_cx, obb_cy, obb_w, obb_h, obb_theta, angle_unit, angle_version,
    source_format, valid_geometry, warnings
"""
from __future__ import annotations

import math
import os
import xml.etree.ElementTree as ET
from typing import Any, Dict, Iterable, List, Optional, Tuple

import numpy as np

try:
    import cv2  # type: ignore
    _HAS_CV2 = True
except Exception:  # pragma: no cover
    _HAS_CV2 = False

from orientbench.data.dior import parse_dior_obb_xml
from orientbench.data.dota import parse_dota_txt

DATASET_ROOT_DEFAULT = "/home/rspip/cqc/data/dataset"
HALF_PI = math.pi / 2.0

GT_SCHEMA: List[str] = [
    "dataset", "split", "image_id", "image_path", "annotation_path",
    "class_name", "obb_cx", "obb_cy", "obb_w", "obb_h", "obb_theta",
    "angle_unit", "angle_version", "source_format", "valid_geometry", "warnings",
]


def _normalize_le90(theta: float) -> float:
    """Map an angle (rad) into [-pi/2, pi/2)."""
    return ((theta + HALF_PI) % math.pi) - HALF_PI


def poly8_to_obb(poly: List[float]) -> Tuple[Optional[Tuple[float, float, float, float, float]], Optional[str]]:
    """Convert an 8-value quadrilateral to (cx,cy,w,h,theta_rad).

    Returns ((cx,cy,w,h,theta), None) or (None, warning) on failure.
    Uses cv2.minAreaRect when available; falls back to an edge-based estimate.
    """
    if len(poly) != 8:
        return None, f"poly has {len(poly)} values (need 8)"
    pts = np.array(poly, dtype=np.float64).reshape(4, 2)
    if not np.all(np.isfinite(pts)):
        return None, "poly has non-finite coords"

    if _HAS_CV2:
        rect = cv2.minAreaRect(pts.astype(np.float32))
        (cx, cy), (w, h), ang_deg = rect
        theta = _normalize_le90(math.radians(ang_deg))
        return (float(cx), float(cy), float(w), float(h), float(theta)), None

    # fallback: assume ordered rectangle corners p1,p2,p3,p4
    p1, p2, p3 = pts[0], pts[1], pts[2]
    cx, cy = pts.mean(axis=0)
    w = float(np.linalg.norm(p2 - p1))
    h = float(np.linalg.norm(p3 - p2))
    theta = _normalize_le90(math.atan2(p2[1] - p1[1], p2[0] - p1[0]))
    return (float(cx), float(cy), w, h, theta), "obb via edge-fallback (cv2 unavailable)"


# --- HRSC + FAIR1M parsers (formats are clear; kept here, not separate files) -
def parse_hrsc_xml(path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """HRSC2016: <HRSC_Object> with mbox_cx/cy/w/h/ang (ang in radians)."""
    objs: List[Dict[str, Any]] = []
    warnings: List[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as e:
        return [], [f"could not parse HRSC XML {path}: {e}"]
    root = tree.getroot()
    container = root.find("HRSC_Objects")
    if container is None:
        return [], [f"{path}: no HRSC_Objects"]
    for obj in container.findall("HRSC_Object"):
        try:
            cx = float(obj.find("mbox_cx").text)
            cy = float(obj.find("mbox_cy").text)
            w = float(obj.find("mbox_w").text)
            h = float(obj.find("mbox_h").text)
            ang = float(obj.find("mbox_ang").text)
        except (AttributeError, ValueError, TypeError):
            warnings.append(f"{path}: HRSC_Object missing/!numeric mbox, skipped")
            continue
        cls_el = obj.find("Class_ID")
        class_name = cls_el.text.strip() if (cls_el is not None and cls_el.text) else "ship"
        objs.append({"obb": (cx, cy, w, h, ang), "class_name": class_name, "difficult": None})
    return objs, warnings


def parse_fair1m_xml(path: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """FAIR1M v1.0: <object> with <points> (5 pts, closing) + possibleresult/name."""
    objs: List[Dict[str, Any]] = []
    warnings: List[str] = []
    try:
        tree = ET.parse(path)
    except (ET.ParseError, OSError) as e:
        return [], [f"could not parse FAIR1M XML {path}: {e}"]
    root = tree.getroot()
    objects_el = root.find("objects")
    if objects_el is None:
        return [], [f"{path}: no <objects>"]
    for obj in objects_el.findall("object"):
        name_el = obj.find("possibleresult/name")
        class_name = name_el.text.strip() if (name_el is not None and name_el.text) else "unknown"
        pts_el = obj.find("points")
        if pts_el is None:
            warnings.append(f"{path}: object '{class_name}' has no points, skipped")
            continue
        coords: List[float] = []
        for p in pts_el.findall("point"):
            if not p.text:
                continue
            try:
                x, y = p.text.split(",")
                coords.extend([float(x), float(y)])
            except ValueError:
                continue
        # FAIR1M closes the polygon (first==last); take first 4 unique points
        if len(coords) >= 8:
            poly = coords[:8]
        else:
            warnings.append(f"{path}: object '{class_name}' has <4 points, skipped")
            continue
        objs.append({"poly": poly, "class_name": class_name, "difficult": None})
    return objs, warnings


# --- dataset registry --------------------------------------------------------
def _dior_split(data_root, split):
    img_sub = "test" if split == "test" else "trainval"
    return {
        "ann_dir": os.path.join(data_root, "DIOR/annfiles/obb"),
        "img_dir": os.path.join(data_root, "DIOR/images", img_sub),
        "split_list": os.path.join(data_root, "DIOR/splits", f"{split}.txt"),
        "ann_ext": ".xml", "img_ext": ".jpg",
    }


def _hrsc_split(data_root, split):
    return {
        "ann_dir": os.path.join(data_root, "HRSC2016/annfiles"),
        "img_dir": os.path.join(data_root, "HRSC2016/images"),
        "split_list": os.path.join(data_root, "HRSC2016/splits", f"{split}.txt"),
        "ann_ext": ".xml", "img_ext": ".bmp",
    }


def _dota_split(data_root, version, split):
    base = f"dota/dota{version}/split_ss_dota{version.replace('.', '')}"
    return {
        "ann_dir": os.path.join(data_root, base, split, "annfiles"),
        "img_dir": os.path.join(data_root, base, split, "images"),
        "split_list": None, "ann_ext": ".txt", "img_ext": ".png",
    }


def _fair1m_split(data_root, split):
    sub = "train_80" if split in ("train", "trainval") else "val_20"
    return {
        "ann_dir": os.path.join(data_root, "fair1m1.0/split", sub, "annfiles"),
        "img_dir": os.path.join(data_root, "fair1m1.0/split", sub, "images"),
        "split_list": None, "ann_ext": ".xml", "img_ext": ".png",
    }


# dataset key -> (canonical name, source_format, angle_version, parser, geom-mode, split-resolver)
DATASETS: Dict[str, Dict[str, Any]] = {
    "dota10": {
        "name": "DOTA-v1.0", "source_format": "dota_txt_poly8",
        "angle_version": "le90_derived_from_poly(cv2.minAreaRect)",
        "parser": parse_dota_txt, "geom": "poly",
        "resolve": lambda dr, sp: _dota_split(dr, "1.0", sp),
    },
    "dota15": {
        "name": "DOTA-v1.5", "source_format": "dota_txt_poly8",
        "angle_version": "le90_derived_from_poly(cv2.minAreaRect)",
        "parser": parse_dota_txt, "geom": "poly",
        "resolve": lambda dr, sp: _dota_split(dr, "1.5", sp),
    },
    "dior": {
        "name": "DIOR-R", "source_format": "dior_obb_xml_robndbox",
        "angle_version": "le90_derived_from_corners(cv2.minAreaRect); raw <angle> retained",
        "parser": parse_dior_obb_xml, "geom": "poly", "resolve": _dior_split,
    },
    "hrsc": {
        "name": "HRSC2016", "source_format": "hrsc_xml_mbox",
        "angle_version": "mbox_ang_rad(opencv-like, UNVERIFIED le90 equivalence)",
        "parser": parse_hrsc_xml, "geom": "obb", "resolve": _hrsc_split,
    },
    "fair1m": {
        "name": "FAIR1M-v1.0", "source_format": "fair1m_xml_points",
        "angle_version": "le90_derived_from_poly(cv2.minAreaRect)",
        "parser": parse_fair1m_xml, "geom": "poly", "resolve": _fair1m_split,
    },
}

DATASET_ALIASES = {
    "dota-v1.0": "dota10", "dota1.0": "dota10", "dota10": "dota10",
    "dota-v1.5": "dota15", "dota1.5": "dota15", "dota15": "dota15",
    "dior-r": "dior", "dior": "dior",
    "hrsc2016": "hrsc", "hrsc": "hrsc",
    "fair1m-v1.0": "fair1m", "fair1m1.0": "fair1m", "fair1m": "fair1m",
}


def resolve_dataset_key(dataset: str) -> Optional[str]:
    return DATASET_ALIASES.get(dataset.strip().lower())


def _list_ann_ids(loc: Dict[str, Any]) -> Tuple[List[str], List[str]]:
    """Return (image_ids, warnings) honoring a split list if present."""
    warnings: List[str] = []
    ann_dir = loc["ann_dir"]
    ext = loc["ann_ext"]
    if not os.path.isdir(ann_dir):
        return [], [f"annotation dir missing: {ann_dir}"]
    if loc.get("split_list") and os.path.isfile(loc["split_list"]):
        with open(loc["split_list"], "r", encoding="utf-8") as fh:
            ids = [ln.strip() for ln in fh if ln.strip()]
        return ids, warnings
    if loc.get("split_list"):
        warnings.append(f"split list missing ({loc['split_list']}); scanning ann dir")
    ids = sorted(
        os.path.splitext(f)[0] for f in os.listdir(ann_dir) if f.endswith(ext)
    )
    return ids, warnings


def build_gt_index(
    dataset: str,
    data_root: str = DATASET_ROOT_DEFAULT,
    split: str = "train",
    max_files: Optional[int] = 50,
    strict: bool = False,
) -> Dict[str, Any]:
    """Build a GT index for one (dataset, split). Returns a result dict with
    ``records`` (schema rows), ``warnings``, and ``stats``. Never raises on
    missing files unless ``strict`` is set."""
    key = resolve_dataset_key(dataset)
    result: Dict[str, Any] = {
        "dataset": dataset, "dataset_key": key, "split": split,
        "records": [], "warnings": [], "stats": {},
        "supported": key is not None,
    }
    if key is None:
        msg = f"unsupported/unknown dataset: {dataset!r}"
        if strict:
            raise ValueError(msg)
        result["warnings"].append(msg)
        return result

    spec = DATASETS[key]
    loc = spec["resolve"](data_root, split)
    ids, warns = _list_ann_ids(loc)
    result["warnings"].extend(warns)
    if not ids:
        if strict:
            raise FileNotFoundError(f"no annotations for {dataset}/{split} at {loc['ann_dir']}")
        result["warnings"].append(f"no annotation ids found for {dataset}/{split}")
        return result

    if max_files is not None:
        ids = ids[:max_files]

    parser = spec["parser"]
    n_obj = n_valid = n_invalid = n_files_ok = n_files_missing = 0
    records: List[Dict[str, Any]] = []

    for image_id in ids:
        ann_path = os.path.join(loc["ann_dir"], image_id + loc["ann_ext"])
        img_path = os.path.join(loc["img_dir"], image_id + loc["img_ext"])
        if not os.path.isfile(ann_path):
            n_files_missing += 1
            result["warnings"].append(f"missing annotation file: {ann_path}")
            continue
        objs, pwarn = parser(ann_path)
        if pwarn:
            result["warnings"].extend(pwarn[:5])  # cap noise
        n_files_ok += 1
        for o in objs:
            n_obj += 1
            rec_warn: List[str] = []
            if spec["geom"] == "obb":
                cx, cy, w, h, theta = o["obb"]
                theta = _normalize_le90(float(theta))
                conv_w = None
            else:
                obb, w_msg = poly8_to_obb(o["poly"])
                if w_msg:
                    rec_warn.append(w_msg)
                if obb is None:
                    cx = cy = w = h = theta = float("nan")
                else:
                    cx, cy, w, h, theta = obb
            valid_geom = bool(
                all(math.isfinite(v) for v in (cx, cy, w, h, theta)) and w > 0 and h > 0
            )
            if valid_geom:
                n_valid += 1
            else:
                n_invalid += 1
            records.append({
                "dataset": spec["name"], "split": split, "image_id": image_id,
                "image_path": img_path, "annotation_path": ann_path,
                "class_name": o.get("class_name", "unknown"),
                "obb_cx": cx, "obb_cy": cy, "obb_w": w, "obb_h": h, "obb_theta": theta,
                "angle_unit": "rad", "angle_version": spec["angle_version"],
                "source_format": spec["source_format"],
                "valid_geometry": valid_geom,
                "warnings": rec_warn,
            })

    result["records"] = records
    result["stats"] = {
        "n_ids_considered": len(ids),
        "n_files_ok": n_files_ok,
        "n_files_missing": n_files_missing,
        "n_objects": n_obj,
        "n_valid_geometry": n_valid,
        "n_invalid_geometry": n_invalid,
    }
    return result
