"""Focused tests for Bench-Core-1 sources / buckets / score / matrix (005 §9)."""
from __future__ import annotations

import math
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.buckets.sources import compute_layout_for_image
from orientbench.buckets.stress_buckets import ALL_BUCKETS, assign_buckets
from orientbench.buckets.thresholds import compute_bucket_thresholds
from orientbench.core.registry import DETECTOR_TAXONOMY, default_score_for_head, taxonomy_availability
from orientbench.metrics.selection_score import dryrun_scores_for_record, head_type_definitions
from orientbench.metrics.statistics import class_conditional_percentiles, normalized_entropy, saturate
from orientbench.reports.prediction_matrix import build_probe_matrix_template


def _obj(cx, cy, w, h, theta, cls="ship"):
    return {"obb_cx": cx, "obb_cy": cy, "obb_w": w, "obb_h": h, "obb_theta": theta,
            "class_name": cls, "valid_geometry": True}


# --- layout source ---------------------------------------------------------
def test_layout_coherent_cluster():
    # 4 aligned same-class boxes close together
    objs = [_obj(0, 0, 20, 10, 0.0), _obj(15, 0, 20, 10, 0.0),
            _obj(30, 0, 20, 10, 0.0), _obj(45, 0, 20, 10, 0.0)]
    lay = compute_layout_for_image(objs)
    # central boxes have >=3 neighbors -> V_layout=1
    assert lay[1]["V_layout"] == 1
    assert lay[1]["n_neighbors"] >= 3
    # aligned neighbors -> R_nbr ~1, A_align ~1
    assert lay[1]["R_nbr"] > 0.95
    assert lay[1]["A_align"] > 0.95
    assert 0.0 <= lay[1]["D_nbr"] <= 1.0
    assert lay[1]["E_layout"] > 0.5


def test_layout_incoherent_lower_R():
    # same positions but scattered orientations -> lower R_nbr than coherent
    coh = compute_layout_for_image(
        [_obj(0, 0, 20, 10, 0.0), _obj(15, 0, 20, 10, 0.0),
         _obj(30, 0, 20, 10, 0.0), _obj(45, 0, 20, 10, 0.0)])
    inc = compute_layout_for_image(
        [_obj(0, 0, 20, 10, 0.0), _obj(15, 0, 20, 10, math.pi / 2),
         _obj(30, 0, 20, 10, math.pi / 4), _obj(45, 0, 20, 10, -math.pi / 4)])
    assert inc[0]["R_nbr"] < coh[1]["R_nbr"]


def test_layout_isolated_box():
    # single box far from others -> no neighbors -> V_layout 0, E_layout 0
    objs = [_obj(0, 0, 10, 10, 0.0), _obj(10000, 0, 10, 10, 0.0)]
    lay = compute_layout_for_image(objs)
    assert lay[0]["n_neighbors"] == 0
    assert lay[0]["V_layout"] == 0
    assert lay[0]["E_layout"] == 0.0


# --- statistics ------------------------------------------------------------
def test_class_conditional_percentiles():
    recs = [{"class_name": "a", "v": float(i)} for i in range(10)]
    recs += [{"class_name": "b", "v": 100.0}]
    out = class_conditional_percentiles(recs, "v", p_list=(30, 80))
    assert out["a"]["n"] == 10
    assert out["a"]["p80"] > out["a"]["p30"]
    assert out["b"]["n"] == 1


def test_saturate_and_entropy():
    assert saturate(2.0) == 1.0 and saturate(-1.0) == 0.0
    # uniform histogram -> normalized entropy ~1
    assert abs(normalized_entropy([1, 1, 1, 1]) - 1.0) < 1e-9
    # delta histogram -> entropy 0
    assert abs(normalized_entropy([0, 5, 0, 0]) - 0.0) < 1e-9


# --- buckets ---------------------------------------------------------------
def _bucket_records():
    # one class with a spread of D_nbr/R_nbr/E_bg so percentiles are meaningful
    recs = []
    for i in range(10):
        recs.append({"class_name": "ship", "obb_w": 20.0, "obb_h": 10.0, "obb_theta": 0.0,
                     "D_nbr": i / 10.0, "R_nbr": i / 10.0, "E_bg": i / 10.0,
                     "n_neighbors": 5, "V_bg": 0, "V_layout": 1})
    return recs


def test_bucket_dense_coherent_and_incoherent():
    recs = _bucket_records()
    thr = compute_bucket_thresholds(recs)
    # high D + high R -> dense_coherent
    hi = {"class_name": "ship", "obb_w": 20.0, "obb_h": 10.0, "obb_theta": 0.0,
          "D_nbr": 0.99, "R_nbr": 0.99, "E_bg": 0.1, "n_neighbors": 5, "V_bg": 0, "V_layout": 1}
    res = assign_buckets(hi, thr)
    assert res["buckets"]["dense_coherent"] is True
    assert res["pending_threshold_freeze"] is True
    # high D + low R -> dense_incoherent
    lo = dict(hi, R_nbr=0.0)
    res2 = assign_buckets(lo, thr)
    assert res2["buckets"]["dense_incoherent"] is True


def test_bucket_evidence_weak_and_sparse_bg_strong():
    recs = _bucket_records()
    thr = compute_bucket_thresholds(recs)
    ew = {"class_name": "ship", "obb_w": 20.0, "obb_h": 10.0, "obb_theta": 0.0,
          "D_nbr": float("nan"), "R_nbr": float("nan"), "E_bg": float("nan"),
          "n_neighbors": 0, "V_bg": 0, "V_layout": 0}
    assert assign_buckets(ew, thr)["buckets"]["evidence_weak"] is True
    sb = {"class_name": "ship", "obb_w": 20.0, "obb_h": 10.0, "obb_theta": 0.0,
          "D_nbr": 0.1, "R_nbr": 0.1, "E_bg": 0.99, "n_neighbors": 1, "V_bg": 1, "V_layout": 0}
    assert assign_buckets(sb, thr)["buckets"]["sparse_bg_strong"] is True


def test_all_buckets_present():
    res = assign_buckets({"class_name": "x", "obb_w": 5, "obb_h": 5, "obb_theta": 0},
                         {"percentiles": {}})
    for b in ALL_BUCKETS:
        assert b in res["buckets"]


# --- selection score / registry -------------------------------------------
def test_head_type_definitions_frozen():
    d = head_type_definitions()
    assert d["angle_distribution_head"] == "negative_normalized_angle_entropy"
    assert d["pure_regression_head"] == "calibrated_gv_obliquity_proxy"
    assert default_score_for_head("native_quality_head").startswith("native")


def test_dryrun_score_flags():
    sc = dryrun_scores_for_record({"obb_w": 20, "obb_h": 10, "obb_theta": 0.0})
    assert sc["score_mode"] == "dry_run"
    assert sc["not_detector_prediction"] is True
    assert sc["not_formal_calibration"] is True
    assert sc["not_official_result"] is True
    assert 0.0 <= sc["default_selection_score"] <= 1.0


# --- probe matrix template -------------------------------------------------
def test_probe_matrix_template_schema_and_missing():
    rows = build_probe_matrix_template()
    assert len(rows) > 0
    req = {"archetype", "head_type", "default_score", "available", "probe",
           "expected_effect", "measured_effect", "is_template", "notes"}
    for r in rows:
        assert req <= set(r.keys())
        assert r["is_template"] is True
        assert r["expected_effect"] == "PENDING_PREREGISTRATION"
    # RHINO archetype must be present and marked unavailable (not substituted)
    rhino = [r for r in rows if r["archetype"] == "rotated_detr_rhino"]
    assert rhino and all(r["available"] is False for r in rhino)
    av = taxonomy_availability()
    assert av["n_missing"] >= 1


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
