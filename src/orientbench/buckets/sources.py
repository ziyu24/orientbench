"""Source measurement — Bench-Core-1 (项目执行文件 §6.4 / §6.5).

Layout source (geometry-only, always available):
    sigma_i = beta * max(w_i, h_i);   neighbors j (same class) with
    ||c_i - c_j|| <= 3*sigma_i.
    V_layout = 1[|N_i| >= n_min]
    omega_ij = exp(-||c_i-c_j||^2 / sigma_i^2) * a(b_j),
               a(b_j) = tanh^2(gamma * |log(w_j/h_j)|)
    v_nbr = sum_j omega_ij * (cos 2θ_j, sin 2θ_j)
    R_nbr = ||v_nbr|| / (sum_j omega_ij + eps)
    u_nbr = v_nbr / (||v_nbr|| + eps);  u_box = (cos 2θ_i, sin 2θ_i)
    A_align = |dot(u_nbr, u_box)|
    D_nbr = saturate(max(w_i,h_i) / (min_j ||c_i-c_j|| + eps))
    E_layout = V_layout * D_nbr * R_nbr * A_align

Background source (needs raster image; per-sample 'unavailable' if image not
loadable — layout is unaffected):
    annulus outside the OBB; grayscale gradient orientation distribution over
    valid annulus pixels (excluding other instances / out-of-image / padding).
    V_bg = 1[bg_valid_ratio >= tau_bg];  A_bg = 1 - H(P_bg)/log(K)
    E_bg = V_bg * A_bg * |dot(u_bg, u_box)|

DEFINITIONS are not changed; the unspecified measurement constants
(gamma/annulus/bins) are dry-run and documented in core.constants.
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Optional

import numpy as np

from orientbench.core.constants import (
    BETA,
    BG_ANNULUS_WIDTH_FACTOR,
    BG_HIST_BINS,
    EPS,
    GAMMA_ELONG,
    N_MIN,
    NEIGHBOR_DIST_FACTOR,
    TAU_BG,
)
from orientbench.core.geometry import obb_to_corners
from orientbench.metrics.statistics import normalized_entropy, saturate

try:
    import cv2  # type: ignore
    _HAS_CV2 = True
except Exception:  # pragma: no cover
    _HAS_CV2 = False


def _elong_salience(w: float, h: float) -> float:
    if w <= 0 or h <= 0:
        return 0.0
    return math.tanh(GAMMA_ELONG * abs(math.log(w / h))) ** 2


def compute_layout_for_image(objects: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute layout sources for every object in one image.

    Each input object needs: obb_cx, obb_cy, obb_w, obb_h, obb_theta,
    class_name, valid_geometry. Returns a list (aligned) of layout dicts.
    """
    n = len(objects)
    cx = np.array([o["obb_cx"] for o in objects], dtype=float)
    cy = np.array([o["obb_cy"] for o in objects], dtype=float)
    w = np.array([o["obb_w"] for o in objects], dtype=float)
    h = np.array([o["obb_h"] for o in objects], dtype=float)
    th = np.array([o["obb_theta"] for o in objects], dtype=float)
    cls = [o.get("class_name", "unknown") for o in objects]
    valid = np.array([bool(o.get("valid_geometry", True)) for o in objects])

    out: List[Dict[str, Any]] = []
    for i in range(n):
        res = {
            "n_neighbors": 0, "V_layout": 0, "D_nbr": float("nan"),
            "R_nbr": float("nan"), "A_align": float("nan"), "E_layout": float("nan"),
        }
        if not valid[i] or not math.isfinite(w[i]) or not math.isfinite(h[i]):
            out.append(res)
            continue
        max_side = max(w[i], h[i])
        sigma = BETA * max_side
        radius = NEIGHBOR_DIST_FACTOR * sigma
        # same-class neighbors within radius
        dx = cx - cx[i]
        dy = cy - cy[i]
        dist = np.sqrt(dx * dx + dy * dy)
        nbr = np.array([
            (j != i) and valid[j] and (cls[j] == cls[i]) and (dist[j] <= radius)
            for j in range(n)
        ])
        idx = np.where(nbr)[0]
        res["n_neighbors"] = int(idx.size)
        res["V_layout"] = int(idx.size >= N_MIN)
        if idx.size == 0:
            res["D_nbr"] = 0.0
            res["R_nbr"] = 0.0
            res["A_align"] = 0.0
            res["E_layout"] = 0.0
            out.append(res)
            continue

        # omega weights
        sal = np.array([_elong_salience(w[j], h[j]) for j in idx])
        omega = np.exp(-(dist[idx] ** 2) / (sigma ** 2 + EPS)) * sal
        sum_omega = float(omega.sum())
        # neighbor orientation concentration in 2theta space
        v_cos = float(np.sum(omega * np.cos(2 * th[idx])))
        v_sin = float(np.sum(omega * np.sin(2 * th[idx])))
        v_norm = math.hypot(v_cos, v_sin)
        R_nbr = v_norm / (sum_omega + EPS)
        if v_norm > EPS:
            u_cos, u_sin = v_cos / v_norm, v_sin / v_norm
        else:
            u_cos, u_sin = 0.0, 0.0
        b_cos, b_sin = math.cos(2 * th[i]), math.sin(2 * th[i])
        A_align = abs(u_cos * b_cos + u_sin * b_sin)
        min_dist = float(np.min(dist[idx]))
        D_nbr = saturate(max_side / (min_dist + EPS))
        res["D_nbr"] = D_nbr
        res["R_nbr"] = R_nbr
        res["A_align"] = A_align
        res["E_layout"] = res["V_layout"] * D_nbr * R_nbr * A_align
        out.append(res)
    return out


# --- background ------------------------------------------------------------
def _fill_obb_mask(shape, corners, value=1):
    mask = np.zeros(shape, dtype=np.uint8)
    if corners is None or not _HAS_CV2:
        return mask
    pts = np.round(np.array(corners, dtype=np.float32)).astype(np.int32)
    cv2.fillPoly(mask, [pts], value)
    return mask


def compute_background_for_object(
    grad_mag: np.ndarray,
    tan2_cos: np.ndarray,
    tan2_sin: np.ndarray,
    obj: Dict[str, Any],
    other_corners: List[Any],
) -> Dict[str, Any]:
    """Background source for one object given precomputed gradient fields.

    grad_mag: HxW magnitude; tan2_cos/tan2_sin: HxW (cos/sin of 2*tangent_angle).
    Returns dict with V_bg, A_bg, E_bg, bg_valid_ratio, bg_status, bg_warnings.
    """
    res = {
        "V_bg": 0, "A_bg": float("nan"), "E_bg": float("nan"),
        "bg_valid_ratio": float("nan"), "bg_status": "unavailable", "bg_warnings": [],
    }
    if not _HAS_CV2:
        res["bg_warnings"].append("cv2 unavailable")
        return res
    shape = grad_mag.shape
    inner = obb_to_corners(obj["obb_cx"], obj["obb_cy"], obj["obb_w"], obj["obb_h"], obj["obb_theta"])
    if inner is None:
        res["bg_warnings"].append("invalid obb")
        return res
    annulus_w = BG_ANNULUS_WIDTH_FACTOR * max(obj["obb_w"], obj["obb_h"])
    outer = obb_to_corners(
        obj["obb_cx"], obj["obb_cy"],
        obj["obb_w"] + 2 * annulus_w, obj["obb_h"] + 2 * annulus_w, obj["obb_theta"],
    )
    inner_mask = _fill_obb_mask(shape, inner)
    outer_mask = _fill_obb_mask(shape, outer)
    annulus = (outer_mask > 0) & (inner_mask == 0)
    annulus_total = int(annulus.sum())
    if annulus_total == 0:
        res["bg_status"] = "empty_annulus"
        res["bg_valid_ratio"] = 0.0
        return res
    # exclude other instances
    excl = np.zeros(shape, dtype=bool)
    for c in other_corners:
        if c is not None:
            excl |= _fill_obb_mask(shape, c) > 0
    valid = annulus & (~excl)
    n_valid = int(valid.sum())
    bg_valid_ratio = n_valid / annulus_total
    res["bg_valid_ratio"] = bg_valid_ratio
    res["bg_status"] = "ok"
    res["V_bg"] = int(bg_valid_ratio >= TAU_BG)
    if n_valid == 0:
        res["A_bg"] = float("nan")
        res["E_bg"] = 0.0
        return res
    # orientation histogram over valid annulus pixels weighted by gradient mag
    mags = grad_mag[valid]
    tcos = tan2_cos[valid]
    tsin = tan2_sin[valid]
    ang2 = np.arctan2(tsin, tcos)  # in [-pi, pi) == 2*phi
    phi = (ang2 / 2.0) % math.pi      # tangent orientation in [0, pi)
    bins = BG_HIST_BINS
    hist, _ = np.histogram(phi, bins=bins, range=(0, math.pi), weights=mags)
    A_bg = 1.0 - normalized_entropy(hist)
    if not math.isfinite(A_bg):
        A_bg = 0.0
    # dominant orientation (mag-weighted circular mean in 2phi)
    u_cos = float(np.sum(mags * tcos))
    u_sin = float(np.sum(mags * tsin))
    nrm = math.hypot(u_cos, u_sin)
    if nrm > EPS:
        u_cos, u_sin = u_cos / nrm, u_sin / nrm
    else:
        u_cos, u_sin = 0.0, 0.0
    b_cos, b_sin = math.cos(2 * obj["obb_theta"]), math.sin(2 * obj["obb_theta"])
    align = abs(u_cos * b_cos + u_sin * b_sin)
    res["A_bg"] = A_bg
    res["E_bg"] = res["V_bg"] * A_bg * align
    return res


def precompute_gradients(gray: np.ndarray):
    """Return (grad_mag, tan2_cos, tan2_sin) for a grayscale image."""
    gx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    mag = np.hypot(gx, gy)
    grad_ang = np.arctan2(gy, gx)        # gradient direction
    tangent = grad_ang + math.pi / 2.0   # edge tangent perpendicular to gradient
    return mag, np.cos(2 * tangent), np.sin(2 * tangent)
