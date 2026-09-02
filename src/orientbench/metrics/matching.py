"""GT <-> prediction matching skeleton (Bench-Core).

Greedy, score-sorted, same-image / same-class matching with rotated-IoU.
IoU uses shapely polygon intersection when available (method 'shapely_polygon');
otherwise an axis-aligned-bbox approximation (method 'approx_aabb', flagged with
an ``approximate_iou`` warning). The IoU threshold is a PLACEHOLDER
(pending_threshold_freeze) — matching here is a skeleton, NOT a formal gate.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple

from orientbench.core.geometry import obb_to_corners

try:
    from shapely.geometry import Polygon  # type: ignore
    _HAS_SHAPELY = True
except Exception:  # pragma: no cover
    _HAS_SHAPELY = False

IOU_THRESHOLD_PLACEHOLDER = 0.5  # PENDING_THRESHOLD_FREEZE


def _corners(rec) -> Optional[list]:
    return obb_to_corners(rec["obb_cx"], rec["obb_cy"], rec["obb_w"], rec["obb_h"], rec["obb_theta"])


def obb_iou(a: Dict[str, Any], b: Dict[str, Any]) -> Tuple[float, str, List[str]]:
    """Return (iou, method, warnings) for two OBB records."""
    ca, cb = _corners(a), _corners(b)
    if ca is None or cb is None:
        return 0.0, "invalid", ["invalid geometry"]
    if _HAS_SHAPELY:
        pa, pb = Polygon(ca), Polygon(cb)
        if not pa.is_valid or not pb.is_valid:
            return 0.0, "invalid_polygon", ["non-simple polygon"]
        inter = pa.intersection(pb).area
        union = pa.area + pb.area - inter
        return (inter / union if union > 0 else 0.0), "shapely_polygon", []
    # fallback: axis-aligned bbox IoU (approximate)
    def aabb(c):
        xs = [p[0] for p in c]; ys = [p[1] for p in c]
        return min(xs), min(ys), max(xs), max(ys)
    ax0, ay0, ax1, ay1 = aabb(ca)
    bx0, by0, bx1, by1 = aabb(cb)
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0.0, ix1 - ix0), max(0.0, iy1 - iy0)
    inter = iw * ih
    union = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return (inter / union if union > 0 else 0.0), "approx_aabb", ["approximate_iou"]


def _aabb(rec):
    c = _corners(rec)
    if c is None:
        return None
    xs = [p[0] for p in c]; ys = [p[1] for p in c]
    return (min(xs), min(ys), max(xs), max(ys))


def _aabb_overlap(a, b):
    if a is None or b is None:
        return False
    return not (a[2] < b[0] or b[2] < a[0] or a[3] < b[1] or b[3] < a[1])


def match_image(
    preds: List[Dict[str, Any]], gts: List[Dict[str, Any]],
    iou_threshold: float = IOU_THRESHOLD_PLACEHOLDER,
) -> List[Dict[str, Any]]:
    """Greedy match predictions to GTs within one image (same class, score desc).

    Returns one row per prediction with matched_gt_id / match_status / iou /
    iou_method. Uses an AABB pre-filter to skip non-overlapping pairs (speed).
    """
    order = sorted(range(len(preds)), key=lambda i: -float(preds[i].get("score", 0.0)))
    used = set()
    rows = []
    approximate = False
    gt_aabb = [_aabb(g) for g in gts]
    for pi in order:
        p = preds[pi]
        p_aabb = _aabb(p)
        best_iou, best_gt, best_method = 0.0, None, "none"
        for gi, g in enumerate(gts):
            if gi in used:
                continue
            if g.get("class_name") != p.get("class_name"):
                continue
            if not _aabb_overlap(p_aabb, gt_aabb[gi]):
                continue
            iou, method, w = obb_iou(p, g)
            if "approximate_iou" in w:
                approximate = True
            if iou > best_iou:
                best_iou, best_gt, best_method = iou, gi, method
        status = "matched" if (best_gt is not None and best_iou >= iou_threshold) else "unmatched"
        if status == "matched":
            used.add(best_gt)
        rows.append({
            "pred_index": pi, "matched_gt_id": best_gt if status == "matched" else None,
            "match_status": status, "iou": round(best_iou, 4), "iou_method": best_method,
            "approximate_iou": approximate, "iou_threshold_placeholder": iou_threshold,
            "pending_threshold_freeze": True,
        })
    return rows


def match_dataset(
    preds: List[Dict[str, Any]], gts: List[Dict[str, Any]],
    iou_threshold: float = IOU_THRESHOLD_PLACEHOLDER,
) -> Dict[str, Any]:
    """Match across a dataset by grouping on image_id. Returns matches + stats."""
    by_img_p: Dict[str, List[int]] = {}
    by_img_g: Dict[str, List[int]] = {}
    for i, p in enumerate(preds):
        by_img_p.setdefault(p["image_id"], []).append(i)
    for j, g in enumerate(gts):
        by_img_g.setdefault(g["image_id"], []).append(j)

    matched_pairs = []  # (pred_global_idx, gt_global_idx, iou)
    n_matched = 0
    approximate = False
    for img, p_idxs in by_img_p.items():
        g_idxs = by_img_g.get(img, [])
        local_p = [preds[i] for i in p_idxs]
        local_g = [gts[j] for j in g_idxs]
        rows = match_image(local_p, local_g, iou_threshold)
        for r in rows:
            if r["approximate_iou"]:
                approximate = True
            if r["match_status"] == "matched":
                n_matched += 1
                matched_pairs.append((p_idxs[r["pred_index"]],
                                      g_idxs[r["matched_gt_id"]], r["iou"]))
    return {
        "n_preds": len(preds), "n_gts": len(gts), "n_matched": n_matched,
        "matched_pairs": matched_pairs, "approximate_iou": approximate,
        "iou_method": "shapely_polygon" if _HAS_SHAPELY else "approx_aabb",
        "iou_threshold_placeholder": iou_threshold,
    }
