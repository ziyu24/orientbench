"""Independent synthetic falsification fixtures for the r004 observables."""
from __future__ import annotations

import json
from pathlib import Path

import cv2
import numpy as np

from .observability import circular_crop, corrupt, fixed_noise_scale, measure


def _radial(n: int = 161) -> np.ndarray:
    y, x = np.mgrid[:n, :n].astype(float); r = np.hypot(x-(n-1)/2, y-(n-1)/2)
    return np.exp(-(r/26)**2).astype(np.float32)


def _ellipse(n: int = 161) -> np.ndarray:
    y, x = np.mgrid[:n, :n].astype(float); x -= (n-1)/2; y -= (n-1)/2
    return np.exp(-((x/34)**2+(y/10)**2)).astype(np.float32)


def _fourfold(n: int = 161) -> np.ndarray:
    y, x = np.mgrid[:n, :n].astype(float); x -= (n-1)/2; y -= (n-1)/2
    return (np.cos(4*np.arctan2(y, x))*np.exp(-np.hypot(x,y)/36)).astype(np.float32)


def _textured_ellipse(n: int = 161) -> np.ndarray:
    """A direction-bearing lobe with native-frequency content for resampling."""
    y, x = np.mgrid[:n, :n].astype(float); x -= (n-1)/2; y -= (n-1)/2
    envelope = np.exp(-((x/34)**2+(y/10)**2))
    return (envelope * (1 + .35*np.cos(1.1*x))).astype(np.float32)


def _m(a: np.ndarray):
    p, w = circular_crop(a, (a.shape[1]-1)/2, (a.shape[0]-1)/2, 80)
    return measure(p, w, fixed_noise_scale(p))


def run(output: str | Path) -> dict:
    """Run the independently specified fixture properties and persist their values."""
    const = np.zeros((161, 161), np.float32)
    radial, ellipse, four, textured = _radial(), _ellipse(), _fourfold(), _textured_ellipse()
    rotated = cv2.rotate(ellipse, cv2.ROTATE_90_CLOCKWISE)
    sequence = [_m(corrupt(ellipse, "blur", d)).j_eff for d in (.5, 1., 1.5)]
    down = [_m(corrupt(textured, "downsample", d)).j_eff for d in (1.25, 1.5, 2.)]
    values = {"constant": _m(const).__dict__, "radial": _m(radial).__dict__, "ellipse": _m(ellipse).__dict__, "fourfold": _m(four).__dict__, "rotated_ellipse": _m(rotated).__dict__, "blur_j": sequence, "downsample_j": down}
    checks = {
        "constant_zero": values["constant"]["j_eff"] < 1e-8 and values["constant"]["m15"] < 1e-8,
        "radial_zero": values["radial"]["j_eff"] < values["ellipse"]["j_eff"] * 1e-4,
        "ellipse_nonzero": values["ellipse"]["j_eff"] > values["radial"]["j_eff"] + 1e-3,
        "fourfold_local_global_alias": values["fourfold"]["j_eff"] > 1e-4 and values["fourfold"]["m15"] < values["ellipse"]["m15"],
        "rotation_invariant": abs(values["ellipse"]["j_eff"] - values["rotated_ellipse"]["j_eff"]) / max(values["ellipse"]["j_eff"], 1e-8) < .05,
        "blur_monotone": sequence[0] >= sequence[1] >= sequence[2],
        "downsample_monotone": down[0] >= down[1] >= down[2],
    }
    result = {"checks": checks, "values": values, "passed": all(checks.values())}
    Path(output).parent.mkdir(parents=True, exist_ok=True)
    Path(output).write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(); parser.add_argument("--output", required=True)
    args = parser.parse_args(); result = run(args.output)
    raise SystemExit(0 if result["passed"] else 1)
