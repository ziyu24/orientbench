"""Independent, deliberately small synthetic implementation for r004 checks.

It does not import the production observable implementation.  Its purpose is
to catch coordinate, periodicity, and interpolation regressions before any
official-test outcome is accessed.
"""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np


def _window(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    y, x = np.mgrid[:n, :n].astype(float); x -= (n-1)/2; y -= (n-1)/2
    w = (x*x+y*y <= 70*70).astype(float)
    return x, y, w


def _energy(image: np.ndarray) -> float:
    x, y, w = _window(image.shape[0])
    gy, gx = np.gradient(image.astype(float))
    tangent = -y*gx + x*gy
    # Independently remove only translation and photometric nuisance.
    cols = np.stack([gx, gy, image, np.ones_like(image)], -1).reshape(-1, 4)
    good = w.ravel() > 0
    coef, *_ = np.linalg.lstsq(cols[good], tangent.ravel()[good], rcond=None)
    r = tangent.ravel()[good] - cols[good] @ coef
    return float(np.mean(r*r))


def _margin(image: np.ndarray) -> float:
    n = image.shape[0]; c = ((n-1)/2, (n-1)/2); _, _, w = _window(n)
    values = []
    for degree in range(15, 180, 5):
        rot = cv2.warpAffine(image, cv2.getRotationMatrix2D(c, degree, 1), (n, n), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT_101)
        values.append(float(np.average((image-rot)**2, weights=w)))
    return min(values)


def _blur(x: np.ndarray, d: float) -> np.ndarray:
    return cv2.GaussianBlur(x, (0, 0), d, borderType=cv2.BORDER_REFLECT_101)


def _down(x: np.ndarray, d: float) -> np.ndarray:
    n = x.shape[0]; small = cv2.resize(x, (round(n/d), round(n/d)), interpolation=cv2.INTER_AREA)
    return cv2.resize(small, (n, n), interpolation=cv2.INTER_CUBIC)


def run(output: str | Path) -> dict:
    n = 161; y, x = np.mgrid[:n, :n].astype(float); x -= 80; y -= 80
    radial = np.exp(-(np.hypot(x, y)/26)**2).astype(np.float32)
    ellipse = np.exp(-((x/34)**2+(y/10)**2)).astype(np.float32)
    four = (np.cos(4*np.arctan2(y,x))*np.exp(-np.hypot(x,y)/36)).astype(np.float32)
    textured = (ellipse*(1+.35*np.cos(1.1*x))).astype(np.float32)
    e = {"constant": _energy(np.zeros((n,n),np.float32)), "radial": _energy(radial), "ellipse": _energy(ellipse), "fourfold": _energy(four), "ellipse_rotated": _energy(cv2.rotate(ellipse, cv2.ROTATE_90_CLOCKWISE))}
    m = {"ellipse": _margin(ellipse), "fourfold": _margin(four)}
    blur = [_energy(_blur(ellipse,d)) for d in (.5,1.,1.5)]
    down = [_energy(_down(textured,d)) for d in (1.25,1.5,2.)]
    checks = {"constant_zero": e["constant"] < 1e-12, "radial_low": e["radial"] < e["ellipse"]*.01,
              "ellipse_nonzero": e["ellipse"] > e["radial"]*100, "fourfold_alias": e["fourfold"] > e["radial"]*10 and m["fourfold"] < m["ellipse"],
              "rotation_invariant": abs(e["ellipse"]-e["ellipse_rotated"])/e["ellipse"] < .08,
              "blur_monotone": blur[0] >= blur[1] >= blur[2], "downsample_monotone": down[0] >= down[1] >= down[2]}
    result = {"checks": checks, "values": {"energy": e, "margin": m, "blur": blur, "downsample": down}, "passed": all(checks.values())}
    Path(output).parent.mkdir(parents=True, exist_ok=True); Path(output).write_text(json.dumps(result, indent=2, sort_keys=True)+"\n")
    return result


if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser(); p.add_argument("--output", required=True); a=p.parse_args()
    raise SystemExit(0 if run(a.output)["passed"] else 1)
