"""Theta-hidden crop observables frozen for r004.

The functions in this module intentionally accept only pixels, a centre and a
direction-free scale.  No ground-truth angle or detector box is an input.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import cv2
import numpy as np


@dataclass(frozen=True)
class Observable:
    j_eff: float
    m15: float
    rotation_energy: float
    coherence: float
    gradient_energy: float
    edge_energy: float
    contrast: float
    footprint: float


def circular_crop(image: np.ndarray, cx: float, cy: float, scale: float) -> tuple[np.ndarray, np.ndarray]:
    """Extract the fixed, theta-hidden circular G/P/N crop and radial window."""
    radius = max(48.0, 0.9 * float(scale))
    size = int(2 * math.ceil(radius) + 1)
    patch = cv2.getRectSubPix(image.astype(np.float32), (size, size), (float(cx), float(cy)))
    yy, xx = np.mgrid[:size, :size].astype(np.float32)
    rr = np.hypot(xx - (size - 1) / 2, yy - (size - 1) / 2) / radius
    # Tukey-like radial support; it is invariant to theta and used everywhere.
    w = np.where(rr <= .8, 1.0, np.where(rr < 1.0, .5 * (1 + np.cos(np.pi * (rr - .8) / .2)), 0.0))
    return patch, w.astype(np.float64)


def fixed_noise_scale(clean_patch: np.ndarray) -> float:
    med = cv2.medianBlur(clean_patch.astype(np.float32), 3)
    high = clean_patch.astype(np.float64) - med.astype(np.float64)
    return max(1e-4, float(np.median(np.abs(high - np.median(high))) / .67448975))


def _weighted_residual(v: np.ndarray, nuisance: np.ndarray, weight: np.ndarray) -> np.ndarray:
    good = weight.ravel() > 0
    a = nuisance.reshape(-1, nuisance.shape[-1])[good]
    y = v.ravel()[good]
    sw = np.sqrt(weight.ravel()[good])
    coef, *_ = np.linalg.lstsq(a * sw[:, None], y * sw, rcond=None)
    out = v.copy().ravel()
    out[good] = y - a @ coef
    out[~good] = 0.0
    return out.reshape(v.shape)


def _alias_margin(patch: np.ndarray, weight: np.ndarray, sigma0: float, grid_step: int = 5) -> float:
    """M15 with translation/scale/positive-gain/offset nuisance minimised per phi."""
    h, w = patch.shape
    center = ((w - 1) / 2, (h - 1) / 2)
    support = weight > 0
    ref = patch.astype(np.float64)
    denom = sigma0 * sigma0 * float(weight.sum())
    errors: list[float] = []
    for deg in range(15, 180, grid_step):
        mat = cv2.getRotationMatrix2D(center, float(deg), 1.0)
        rotated = cv2.warpAffine(ref.astype(np.float32), mat, (w, h), flags=cv2.INTER_LINEAR,
                                 borderMode=cv2.BORDER_REFLECT_101).astype(np.float64)
        # Linearised translation/scale columns plus positive gain and offset.
        gx = cv2.Sobel(rotated, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(rotated, cv2.CV_64F, 0, 1, ksize=3)
        yy, xx = np.mgrid[:h, :w].astype(np.float64)
        cols = np.stack([gx, gy, (xx-center[0])*gx + (yy-center[1])*gy, rotated, np.ones_like(rotated)], -1)
        good = support.ravel()
        a = cols.reshape(-1, 5)[good]
        y = ref.ravel()[good]
        sw = np.sqrt(weight.ravel()[good])
        coef, *_ = np.linalg.lstsq(a * sw[:, None], y * sw, rcond=None)
        # Positive photometric gain is frozen by the protocol.
        coef[3] = max(0.0, coef[3])
        residual = y - a @ coef
        errors.append(float(np.sum(weight.ravel()[good] * residual**2) / denom))
    return max(0.0, min(errors) if errors else 0.0)


def measure(patch: np.ndarray, weight: np.ndarray, sigma0: float) -> Observable:
    """Compute the two r004 primary quantities plus frozen classical baselines."""
    image = patch.astype(np.float64)
    gx = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    gy = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)
    h, w = image.shape
    yy, xx = np.mgrid[:h, :w].astype(np.float64)
    x, y = xx - (w - 1)/2, yy - (h - 1)/2
    gtheta = -y * gx + x * gy
    nuisance = np.stack([gx, gy, x*gx + y*gy, image, np.ones_like(image)], -1)
    residual = _weighted_residual(gtheta, nuisance, weight)
    j = float(np.sum(weight * residual**2) / (sigma0*sigma0*weight.sum()))
    a = float(np.sum(weight * gx*gx)); b = float(np.sum(weight * gx*gy)); c = float(np.sum(weight * gy*gy))
    coherence = ((a-c)**2 + 4*b*b) / max((a+c)**2, 1e-12)
    grad = (a+c) / max(weight.sum(), 1.0)
    edge = float(np.sum(weight * (np.hypot(gx, gy) > np.percentile(np.hypot(gx, gy)[weight > 0], 75))) / weight.sum())
    return Observable(j, _alias_margin(image, weight, sigma0), float(np.sum(weight*gtheta*gtheta)/(sigma0*sigma0*weight.sum())),
                      float(coherence), float(grad), edge, float(np.sqrt(np.average((image-np.average(image, weights=weight))**2, weights=weight))), float(weight.sum()))


def corrupt(image: np.ndarray, kind: str, dose: float) -> np.ndarray:
    """Frozen r004 full-image intervention; output has original geometry."""
    if kind == "blur":
        return cv2.GaussianBlur(image, (0, 0), sigmaX=float(dose), sigmaY=float(dose), borderType=cv2.BORDER_REFLECT_101)
    if kind == "downsample":
        h, w = image.shape[:2]
        small = cv2.resize(image, (round(w/float(dose)), round(h/float(dose))), interpolation=cv2.INTER_AREA)
        return cv2.resize(small, (w, h), interpolation=cv2.INTER_CUBIC)
    raise ValueError(f"unknown corruption {kind}")
