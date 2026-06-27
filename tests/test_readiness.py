"""Focused tests for readiness packet (007 §7)."""
from __future__ import annotations

import json
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.data.splits import assign_split, build_audit_split, hash_bucket
from orientbench.io.prediction_discovery import _keys_to_schema_status, discover_predictions
from orientbench.io.predictions import load_predictions
from orientbench.reports.readiness import STATUSES, build_readiness
from orientbench.reports.training_readiness import build_training_readiness

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
CONFIGS = os.path.join(_PROJECT_ROOT, "configs")


def _gt(img, n, ds="DOTA-v1.0", sp="train"):
    return [{"dataset": ds, "split": sp, "image_id": img, "obb_cx": 1.0, "obb_cy": 1.0,
             "obb_w": 2.0, "obb_h": 1.0, "obb_theta": 0.0, "valid_geometry": True}
            for _ in range(n)]


# --- prediction discovery --------------------------------------------------
def test_discovery_schema_classification():
    ss, nc = _keys_to_schema_status({"score", "obb_cx", "obb_cy", "obb_w", "obb_h", "obb_theta"})
    assert ss == "matches_prediction_schema" and nc is False
    ss2, nc2 = _keys_to_schema_status({"image_id", "bbox", "score", "category_id"})
    assert ss2 == "coco_style_needs_conversion" and nc2 is True
    ss3, nc3 = _keys_to_schema_status({"lr", "loss", "epoch"})
    assert ss3 == "training_log_not_prediction"


def test_discovery_schema_fields(tmp_path):
    res = discover_predictions(roots=[str(tmp_path)], inventory_json=None)
    req = {"baseline_id", "model_id", "dataset", "candidate_path", "file_type",
           "exists", "size_bytes", "parse_status", "schema_status",
           "needs_conversion", "warnings"}
    # empty dir -> no candidate rows, but result keys exist
    assert "no_real_prediction_found" in res
    assert res["no_real_prediction_found"] is True
    # create a coco-style json -> discovered, needs conversion
    p = tmp_path / "result.bbox.json"
    p.write_text(json.dumps([{"image_id": 1, "bbox": [1, 2, 3, 4], "score": 0.9, "category_id": 1}]),
                 encoding="utf-8")
    res2 = discover_predictions(roots=[str(tmp_path)], inventory_json=None)
    rec = [r for r in res2["records"] if r["candidate_path"].endswith("result.bbox.json")]
    assert rec and req <= set(rec[0].keys())
    assert rec[0]["needs_conversion"] is True


def test_missing_real_prediction():
    out = load_predictions("/no/such/real.jsonl")
    assert out["status"] == "no_prediction_available"


# --- splits ----------------------------------------------------------------
def test_hash_split_reproducible():
    a = hash_bucket("img_001")
    b = hash_bucket("img_001")
    assert a == b  # deterministic
    assert assign_split("img_001") == assign_split("img_001")


def test_dcal_daudit_mutually_exclusive():
    gts = []
    for i in range(200):
        gts += _gt(f"img_{i:03d}", 1)
    res = build_audit_split(gts, cal_fraction=0.5)
    cal = {r["image_id"] for r in res["cal_rows"]}
    aud = {r["image_id"] for r in res["audit_rows"]}
    assert cal & aud == set()
    assert res["meta"]["mutually_exclusive"] is True
    assert res["meta"]["intersection_size"] == 0
    assert res["meta"]["n_cal"] + res["meta"]["n_audit"] == res["meta"]["n_images"]


# --- readiness -------------------------------------------------------------
def test_readiness_pending_and_blocked():
    res = build_readiness(OUT, CONFIGS)
    assert res["overall_readiness"] in STATUSES
    # thresholds.yaml is pending -> not ready overall
    assert res["overall_readiness"] != "ready"
    assert res["formal_gate_allowed"] is False
    items = {i["item"]: i["status"] for i in res["items"]}
    # thresholds pending detection
    assert items["B_C1_thresholds"] == "ready"  # B_C1 frozen by 017
    assert items["D2_thresholds"] == "ready"  # D2 frozen by 012
    assert items["freeze_time_set"] == "ready"  # freeze_time set by 012
    # RHINO missing detection
    assert items["rhino_host"] == "blocked"


def test_training_allowed_false():
    # 013: D6 approved -> training_allowed becomes host-scope value; formal gate still false
    res = build_training_readiness(OUT, CONFIGS)
    assert res["training_allowed"] == "true_for_approved_host_scope"
    assert res["formal_gate_allowed"] is False


def test_no_formal_gate_claim_in_report():
    from orientbench.reports.bench_core import build_report
    md = build_report(OUT, "TS", stage="core1").lower()
    # must not claim a formal gate pass
    assert "gate passed" not in md and "正式 gate 通过" not in md
    assert "dry-run" in md or "dry_run" in md


if __name__ == "__main__":
    passed = failed = 0
    import tempfile, pathlib
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                if fn.__code__.co_argcount and "tmp_path" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
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
