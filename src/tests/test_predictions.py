"""Focused tests for prediction contract / matching / angle audit (006 §8)."""
from __future__ import annotations

import json
import math
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

import orientbench.metrics.matching as matching
from orientbench.data.gt_index import build_gt_index, resolve_dataset_key
from orientbench.io.predictions import (
    PREDICTION_SCHEMA,
    detect_format,
    generate_synthetic_predictions,
    load_predictions,
    make_synthetic_prediction,
    validate_prediction,
)
from orientbench.metrics.matching import match_dataset, obb_iou
from orientbench.reports.angle_audit import _scan_config, audit_angle_versions

GT = {"dataset": "DOTA-v1.0", "split": "train", "image_id": "P0", "class_name": "ship",
      "obb_cx": 100.0, "obb_cy": 100.0, "obb_w": 40.0, "obb_h": 20.0, "obb_theta": 0.3,
      "angle_version": "le90_derived_from_poly", "valid_geometry": True}


def test_prediction_schema_validation():
    p = make_synthetic_prediction(GT, __import__("numpy").random.RandomState(0))
    for f in PREDICTION_SCHEMA:
        assert f in p
    ok, warns = validate_prediction(p)
    assert ok is True
    # break a field
    bad = dict(p); bad["obb_w"] = -1.0
    ok2, warns2 = validate_prediction(bad)
    assert any("non-positive" in w for w in warns2)


def test_synthetic_fixture_flags():
    p = make_synthetic_prediction(GT, __import__("numpy").random.RandomState(1))
    assert p["is_synthetic"] is True
    assert p["not_detector_output"] is True
    assert p["source_path"] == "SYNTHETIC"
    assert 0.0 <= p["score"] <= 1.0
    # derived from GT geometry (center/size preserved, only theta perturbed)
    assert p["obb_cx"] == GT["obb_cx"] and p["obb_w"] == GT["obb_w"]


def test_generate_skips_invalid():
    gts = [GT, dict(GT, valid_geometry=False)]
    preds = generate_synthetic_predictions(gts, seed=0)
    assert len(preds) == 1


def test_missing_prediction_file():
    out = load_predictions("/no/such/pred.jsonl")
    assert out["status"] == "no_prediction_available"
    out2 = load_predictions(None)
    assert out2["status"] == "no_prediction_available"


def test_format_auto_detection(tmp_path):
    assert detect_format("a.jsonl") == "jsonl"
    assert detect_format("a.json") == "json"
    assert detect_format("a.csv") == "csv"
    assert detect_format("a.pkl") == "pickle_placeholder"
    assert detect_format("model_mmrotate.pth") == "mmrotate_placeholder"
    # real jsonl load
    p = tmp_path / "p.jsonl"
    p.write_text(json.dumps({"a": 1}) + "\n", encoding="utf-8")
    out = load_predictions(str(p))
    assert out["status"] == "loaded" and out["format"] == "jsonl" and len(out["records"]) == 1


def test_gt_pred_matching_skeleton():
    preds = generate_synthetic_predictions([GT, dict(GT, image_id="P0", obb_cx=300.0)], seed=0)
    gts = [GT, dict(GT, obb_cx=300.0)]
    m = match_dataset(preds, gts)
    assert m["n_preds"] == 2
    # synthetic preds (only angle perturbed) overlap their GT strongly -> matched
    assert m["n_matched"] >= 1
    assert m["iou_method"] in ("shapely_polygon", "approx_aabb")


def test_identical_obb_iou_is_one():
    iou, method, warns = obb_iou(GT, GT)
    assert iou > 0.99


def test_approximate_iou_warning(monkeypatch):
    # force the shapely-absent fallback -> approximate_iou flagged
    monkeypatch.setattr(matching, "_HAS_SHAPELY", False)
    iou, method, warns = matching.obb_iou(GT, GT)
    assert method == "approx_aabb"
    assert "approximate_iou" in warns


def test_angle_version_config_scan(tmp_path):
    cfg = tmp_path / "config.py"
    cfg.write_text("angle_version = 'le90'\npredict_box_type='rbox'\n", encoding="utf-8")
    res = _scan_config(str(cfg))
    assert res["angle_version"] == "le90"
    assert res["box_type"] == "rbox"
    assert res["theta_unit"] == "rad_inferred"
    assert res["source"] == "config_scan"


def test_angle_version_unknown_and_model_id_fallback(tmp_path):
    cfg = tmp_path / "config.py"
    cfg.write_text("# no angle token here\nfoo = 1\n", encoding="utf-8")
    inv = tmp_path / "inv.json"
    inv.write_text(json.dumps({"records": [
        {"id": 1, "model_id": "oriented_rcnn_r50_fpn_1x_le90", "dataset": "DOTA",
         "config_abs": str(cfg)},
        {"id": 2, "model_id": "mystery_model", "dataset": "DOTA", "config_abs": None},
    ]}), encoding="utf-8")
    rows = audit_angle_versions(str(inv))
    # config has no token -> fall back to model_id suffix le90
    assert rows[0]["angle_version"] == "le90"
    assert rows[0]["source"] == "model_id_suffix"
    # no config + no suffix -> unknown
    assert rows[1]["angle_version"] == "unknown"


def test_dota15_gt_sanity_path():
    assert resolve_dataset_key("DOTA-v1.5") == "dota15"
    # build on missing root is tolerated (records warning, supported True)
    res = build_gt_index("dota15", data_root="/no/such", split="train", max_files=3)
    assert res["supported"] is True


def test_report_contains_dryrun_labels():
    from orientbench.reports.bench_core import build_report
    md = build_report(os.path.join(_PROJECT_ROOT, "outputs", "bench_core"),
                      "TS", stage="core1")
    assert "DRY-RUN" in md or "dry-run" in md
    assert "SYNTHETIC" in md or "synthetic" in md


if __name__ == "__main__":
    passed = failed = 0
    import numpy as np  # noqa
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                argc = fn.__code__.co_argcount
                if argc == 0:
                    fn()
                else:
                    import tempfile, pathlib
                    with tempfile.TemporaryDirectory() as d:
                        fn(pathlib.Path(d))
                passed += 1
                print(f"PASS {name}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(1 if failed else 0)
