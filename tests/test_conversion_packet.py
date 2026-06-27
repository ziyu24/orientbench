"""Focused tests for conversion / ingestion plan / host packet / drafts (008 §7)."""
from __future__ import annotations

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.prediction_converters import (
    convert_coco_record,
    convert_coco_records,
    detect_bbox_kind,
)
from orientbench.io.prediction_discovery import classify_ingestion
from orientbench.io.predictions import validate_prediction
from orientbench.reports.angle_version_plan import build_angle_version_plan
from orientbench.reports.readiness import build_host_decision_packet
from orientbench.reports.threshold_proposal import build_threshold_draft
from orientbench.reports.training_readiness import build_training_readiness

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
CONFIGS = os.path.join(_PROJECT_ROOT, "configs")


def test_detect_bbox_kind():
    assert detect_bbox_kind([1, 2, 3, 4]) == "hbb_xywh"
    assert detect_bbox_kind([1, 2, 3, 4, 0.5]) == "obb_cxcywha"
    assert detect_bbox_kind([1, 2, 3, 4, 5, 6, 7, 8]) == "poly8"


def test_bbox_only_converter_not_formal_obb_gate():
    rec = {"image_id": "x", "bbox": [10, 20, 40, 20], "score": 0.9, "category_id": 3}
    c = convert_coco_record(rec, "DOTA-v1.0", "train", "det", "1", "src.json")
    assert c["source_bbox_kind"] == "hbb_xywh"
    assert c["bbox_only"] is True
    assert c["obb_unavailable"] is True
    assert c["not_orientation_prediction"] is True
    assert c["not_formal_gate"] is True
    assert c["obb_theta"] == 0.0  # placeholder, not a real orientation


def test_obb5_converter_carries_orientation_but_not_formal():
    rec = {"image_id": "x", "bbox": [100, 100, 40, 20, 1.2], "score": 1.0, "category_id": 6}
    c = convert_coco_record(rec, "DOTA-v1.0", "train", "det", "1", "src.json")
    assert c["source_bbox_kind"] == "obb_cxcywha"
    assert c["bbox_only"] is False
    assert c["obb_theta"] == 1.2
    assert c["not_formal_gate"] is True       # pseudo-label / unverified
    assert c["needs_category_mapping"] is True


def test_converted_prediction_schema_valid():
    rec = {"image_id": "x", "bbox": [100, 100, 40, 20, 1.2], "score": 1.0, "category_id": 6}
    c = convert_coco_record(rec, "DOTA-v1.0", "train", "det", "1", "src.json")
    ok, warns = validate_prediction(c)
    assert ok is True  # full 17-field schema present + finite numerics


def test_convert_records_stats_no_formal_gate():
    recs = [{"image_id": "a", "bbox": [1, 2, 3, 4], "score": 0.5, "category_id": 1},
            {"image_id": "a", "bbox": [1, 2, 3, 4, 0.3], "score": 0.9, "category_id": 2}]
    out, stats = convert_coco_records(recs, "DOTA-v1.0", "train", "det", "1", "src.json")
    assert stats["any_can_enter_formal_angle_gate"] is False
    assert stats["all_not_formal_gate"] is True
    assert stats["n_bbox_only"] == 1


def test_ingestion_status_classification():
    # bbox-only coco -> convertible_bbox_only, cannot enter formal
    r = {"origin": "external", "parse_status": "parseable_json",
         "schema_status": "coco_style_needs_conversion", "bbox_dim": 4}
    st, formal = classify_ingestion(r)
    assert st == "convertible_bbox_only" and formal is False
    # obb-5 coco -> convertible_needs_mapping, still not formal
    r2 = dict(r, bbox_dim=5)
    st2, f2 = classify_ingestion(r2)
    assert st2 == "convertible_needs_mapping" and f2 is False
    # synthetic internal
    r3 = {"origin": "orientbench_synthetic"}
    assert classify_ingestion(r3)[0] == "synthetic_internal"


def test_angle_version_plan_keeps_uncertain():
    plan = build_angle_version_plan()
    assert plan["all_resolved"] is False
    assert plan["n_uncertain"] >= 1
    hrsc = [c for c in plan["checks"] if c["check_id"] == "hrsc_mbox_le90_equiv"]
    assert hrsc and hrsc[0]["current_status"].startswith("uncertain")


def test_threshold_draft_does_not_freeze():
    d = build_threshold_draft()
    assert d["approval_status"] == "pending"
    assert d["proposed_by"] == "claude_draft"
    assert d["freeze_status"] != "frozen"
    assert d["freeze_time"] is None
    # live thresholds.yaml must still be pending (unchanged by drafting)
    import yaml
    with open(os.path.join(CONFIGS, "thresholds.yaml"), "r", encoding="utf-8") as fh:
        live = yaml.safe_load(fh)
    assert str(live.get("freeze_status")).startswith("partial_frozen_dota_d2")  # 012+014 host gates


def test_host_packet_forbids_arsdetr_substitution():
    md = build_host_decision_packet("TS")
    assert "不可替代 RHINO" in md
    assert "ARS-DETR" in md
    assert "MISSING" in md


def test_training_readiness_still_false_with_checklist():
    res = build_training_readiness(OUT, CONFIGS)
    assert res["training_allowed"] == "true_for_approved_host_scope"  # 013 D6
    assert res["can_train_now"] is True
    assert len(res["remaining_before_training"]) >= 4
    assert len(res["stop_conditions_for_first_epoch"]) >= 1
    assert any("host scope" in r.lower() for r in res["reasons"])  # 013 D6 approved


def test_report_no_formal_gate_claim():
    from orientbench.reports.bench_core import build_report
    md = build_report(OUT, "TS").lower()
    assert "gate passed" not in md and "正式 gate 通过" not in md


if __name__ == "__main__":
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                passed += 1
                print(f"PASS {name}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(1 if failed else 0)
