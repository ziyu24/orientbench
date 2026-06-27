"""Focused tests for 009: angle evidence / import matrix / inference plan /
threshold review / approval form / training_allowed."""
from __future__ import annotations

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.reports.angle_evidence import evidence_for_hrsc, evidence_for_poly_dataset
from orientbench.reports.inference_plan import build_inference_plan
from orientbench.reports.prediction_import_matrix import _norm_dataset, build_import_matrix
from orientbench.reports.readiness import build_collaborator_form
from orientbench.reports.threshold_proposal import build_threshold_review
from orientbench.reports.training_readiness import build_training_readiness

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
CONFIGS = os.path.join(_PROJECT_ROOT, "configs")
DATA_ROOT = "/home/rspip/cqc/data/dataset"


def test_angle_evidence_poly_resolved_with_evidence():
    ev = evidence_for_poly_dataset("dior", DATA_ROOT, "trainval", max_files=15)
    # DIOR robndbox is exactly rectangular -> high round-trip IoU + in range -> resolved
    assert ev["in_le90_range"] is True
    assert ev["mean_roundtrip_iou"] is None or ev["mean_roundtrip_iou"] >= 0.88
    assert ev["status"] == "resolved_with_evidence"
    assert "NOT detector sign" in ev["resolution_scope"]


def test_angle_evidence_hrsc_stays_uncertain():
    ev = evidence_for_hrsc(DATA_ROOT, "trainval", max_files=30)
    # HRSC annotated HBB is loose -> cross-check inconclusive -> uncertain (no fabrication)
    assert ev["status"] == "uncertain"
    assert ev["ang_in_le90_range"] in (True, False)


def test_norm_dataset_missing():
    assert _norm_dataset("SODA-A") is None
    assert _norm_dataset("ICDAR-MLT 2019") is None
    assert _norm_dataset("DOTA-v1.5 MS") == "DOTA-v1.5"
    assert _norm_dataset("DIOR-R") == "DIOR-R"


def test_import_matrix_status_classification():
    res = build_import_matrix(OUT)
    statuses = {r["status"] for r in res["rows"]}
    assert "needs_inference" in statuses          # present-dataset valid baselines
    assert "blocked_missing_dataset" in statuses  # SODA-A / ICDAR-MLT baselines
    assert "blocked_missing_detector" in statuses  # RHINO / A4 explicit rows
    # no real ready_schema (no real predictions imported)
    assert res["n_ready_schema"] == 0


def test_inference_plan_not_executable():
    res = build_inference_plan(OUT, os.path.join(OUT, "predictions", "real"))
    assert res["any_executable_now"] is False
    assert all(r["executable_now"] is False for r in res["rows"])
    # RHINO / A4 blocked rows present
    assert any("blocked_missing_detector" in r["blocked_reason"] for r in res["rows"])


def test_threshold_review_does_not_modify_thresholds():
    import yaml
    before = open(os.path.join(CONFIGS, "thresholds.yaml"), "r", encoding="utf-8").read()
    rows = build_threshold_review()
    after = open(os.path.join(CONFIGS, "thresholds.yaml"), "r", encoding="utf-8").read()
    assert before == after  # building review must not touch the live file
    assert all(r["approval_status"] == "pending" for r in rows)
    live = yaml.safe_load(after)
    assert str(live.get("freeze_status")).startswith("partial_frozen_dota_d2")  # 012+014
    assert len(rows) >= 8


def test_collaborator_form_all_pending():
    md = build_collaborator_form("TS")
    assert md.count("**pending**") >= 6
    # no pre-filled choices
    assert "____" in md
    assert "RHINO" in md


def test_training_allowed_still_false():
    res = build_training_readiness(OUT, CONFIGS)
    assert res["training_allowed"] == "true_for_approved_host_scope"  # 013 D6
    assert res["formal_gate_allowed"] is False


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
