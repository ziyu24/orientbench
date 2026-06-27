"""Focused tests for 011 real-inference conversion (mmrotate-1.x pkl -> schema)."""
from __future__ import annotations

import math
import os
import pickle
import sys

import numpy as np

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.prediction_converters import DOTA10_CLASSES, convert_mmrotate1x_pkl
from orientbench.io.predictions import validate_prediction
from orientbench.core.geometry import angle_error_deg


def _mini_pkl(tmp_path):
    rec = {"img_id": "P0001__1024__0___0",
           "pred_instances": {
               "bboxes": np.array([[100.0, 100.0, 40.0, 20.0, 0.30],
                                   [200.0, 200.0, 30.0, 30.0, -0.10]], dtype=np.float32),
               "scores": np.array([0.95, 0.80], dtype=np.float32),
               "labels": np.array([4, 6], dtype=np.int64)}}
    p = os.path.join(str(tmp_path), "mini.pkl")
    with open(p, "wb") as fh:
        pickle.dump([rec], fh)
    return p


def test_convert_mmrotate1x_schema(tmp_path):
    p = _mini_pkl(tmp_path)
    preds, stats = convert_mmrotate1x_pkl(p, "DOTA-v1.0", "val", "orcnn", "1")
    assert stats["n_images"] == 1 and stats["n_detections"] == 2
    assert stats["is_synthetic"] is False
    r0 = preds[0]
    # full schema + real-prediction flags
    ok, _w = validate_prediction(r0)
    assert ok is True
    assert r0["is_synthetic"] is False
    assert r0["not_formal_gate"] is True
    assert r0["angle_version"] == "le90"
    assert r0["class_name"] == DOTA10_CLASSES[4]  # small-vehicle
    assert preds[1]["class_name"] == DOTA10_CLASSES[6]  # ship
    assert abs(r0["obb_theta"] - 0.30) < 1e-5


def test_swap_aware_angle_error_identity():
    # a +90deg representation difference -> naive ~90, swap-aware ~0
    naive = angle_error_deg(45.0, 45.0 + 90.0)
    swap = min(angle_error_deg(45.0, 45.0 + 90.0), angle_error_deg(45.0, 45.0 + 90.0 + 90.0))
    assert naive > 80.0
    assert swap < 1e-6


if __name__ == "__main__":
    import tempfile, pathlib
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                if fn.__code__.co_argcount:
                    with tempfile.TemporaryDirectory() as d:
                        fn(pathlib.Path(d))
                else:
                    fn()
                passed += 1
                print(f"PASS {name}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(1 if failed else 0)
