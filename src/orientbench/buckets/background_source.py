"""Background source per image (A4) — annulus gradient-orientation evidence.

Thin orchestrator over orientbench.buckets.sources: loads a raster image,
precomputes gradients once, and computes V_bg/A_bg/E_bg/bg_valid_ratio for every
GT OBB in that image (annulus outside the box, excluding other GTs / image
border / padding). Per-image image-missing -> bg_unavailable (not guessed).
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

import numpy as np

from orientbench.buckets.sources import (
    compute_background_for_object,
    precompute_gradients,
)
from orientbench.core.geometry import obb_to_corners

try:
    import cv2  # type: ignore
except Exception:  # pragma: no cover
    cv2 = None


def background_for_image(image_path: str, objs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return a bg dict per object (aligned to objs). Image missing -> unavailable."""
    if cv2 is None or not os.path.isfile(image_path):
        return [{"bg_status": "unavailable", "V_bg": 0, "A_bg": float("nan"),
                 "E_bg": float("nan"), "bg_valid_ratio": float("nan"),
                 "bg_warnings": ["image missing or cv2 unavailable"]} for _ in objs]
    gray = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if gray is None:
        return [{"bg_status": "unavailable", "V_bg": 0, "A_bg": float("nan"),
                 "E_bg": float("nan"), "bg_valid_ratio": float("nan"),
                 "bg_warnings": ["cv2 failed to read"]} for _ in objs]
    mag, tcos, tsin = precompute_gradients(gray.astype(np.float64))
    corners = [obb_to_corners(o["obb_cx"], o["obb_cy"], o["obb_w"], o["obb_h"], o["obb_theta"])
               for o in objs]
    out = []
    for k, o in enumerate(objs):
        others = [corners[j] for j in range(len(objs)) if j != k]
        out.append(compute_background_for_object(mag, tcos, tsin, o, others))
    return out
