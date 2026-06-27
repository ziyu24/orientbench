"""Focused sanity tests for Bench-Core-0 primitives.

Covers (003 task §6):
  - angle error pi-periodicity & range;
  - HBB conversion (axis-aligned & 45deg square);
  - GV near-square vs elongated/oblique cases + frozen identities;
  - risk-coverage ordering (oracle-vs-bad selection);
  - NRC-AUC boundary sanity (oracle=0, random=1, degenerate=NaN);
  - near-square bucket placeholder flagging.

Runnable via pytest or `python tests/test_bench_core0.py`.
"""
from __future__ import annotations

import math
import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.buckets.stress_buckets import near_square_bucket, padding_only_metadata
from orientbench.core.geometry import (
    angle_error_deg,
    angle_error_rad,
    hbb_area,
    hbb_dims,
    obb_area,
    obb_to_hbb,
)
from orientbench.metrics.gv import gv_obliquity
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import (
    aurc,
    risk_at_coverage,
    risk_coverage_summary,
    selective_risk_curve,
)

PI = math.pi
TOL = 1e-9


# --- angle error -----------------------------------------------------------
def test_angle_error_zero_and_period():
    assert abs(angle_error_rad(0.3, 0.3)) < TOL
    # pi-periodic: theta and theta+pi are the same orientation
    assert abs(angle_error_rad(0.3 + PI, 0.3)) < TOL
    assert abs(angle_error_rad(0.3 - PI, 0.3)) < TOL


def test_angle_error_range_and_symmetry():
    # 90deg apart -> max error pi/2
    assert abs(angle_error_rad(PI / 2, 0.0) - PI / 2) < TOL
    # never exceeds pi/2
    for d in [0.1, 1.0, 2.0, 3.0, 5.0, 100.0]:
        e = angle_error_rad(d, 0.0)
        assert 0.0 - TOL <= e <= PI / 2 + TOL
    # symmetric
    assert abs(angle_error_rad(0.0, 0.4) - angle_error_rad(0.4, 0.0)) < TOL


def test_angle_error_deg_and_nan():
    assert abs(angle_error_deg(90.0, 0.0) - 90.0) < 1e-6
    assert abs(angle_error_deg(190.0, 10.0) - 0.0) < 1e-6  # 180 period
    assert math.isnan(angle_error_rad(float("nan"), 0.0))


# --- HBB conversion --------------------------------------------------------
def test_hbb_axis_aligned():
    d = hbb_dims(4.0, 2.0, 0.0)
    assert abs(d["W"] - 4.0) < TOL and abs(d["H"] - 2.0) < TOL
    assert abs(hbb_area(4.0, 2.0, 0.0) - 8.0) < TOL
    assert abs(obb_area(4.0, 2.0) - 8.0) < TOL


def test_hbb_45deg_square():
    w = h = 2.0
    d = hbb_dims(w, h, PI / 4)
    expect = 2.0 * math.sqrt(2.0)  # w*(|cos|+|sin|) = 2*(√2/2+√2/2)=2√2
    assert abs(d["W"] - expect) < TOL and abs(d["H"] - expect) < TOL
    conv = obb_to_hbb(w, h, PI / 4)
    assert abs(conv["obb_area"] - 4.0) < TOL
    assert abs(conv["hbb_area"] - 8.0) < TOL  # (2√2)^2 = 8


def test_geometry_invalid():
    assert math.isnan(obb_area(0.0, 5.0))
    assert math.isnan(hbb_area(-1.0, 5.0, 0.3))
    assert math.isnan(hbb_dims(float("inf"), 2.0, 0.0)["W"])


# --- GV-obliquity ----------------------------------------------------------
def test_gv_axis_aligned_is_one():
    g = gv_obliquity(4.0, 2.0, 0.0)
    assert abs(g["gv_ratio"] - 1.0) < TOL
    assert abs(g["gv_hbb_safe"] - 1.0) < TOL
    assert abs(g["gv_obb_needed"] - 0.0) < TOL


def test_gv_45deg_square_is_half():
    g = gv_obliquity(2.0, 2.0, PI / 4)
    assert abs(g["gv_ratio"] - 0.5) < TOL
    assert abs(g["gv_obb_needed"] - 0.5) < TOL


def test_gv_elongated_oblique_lower_than_near_upright():
    # strongly elongated box at 45deg -> very low gv_ratio (OBB strongly needed)
    g_oblique = gv_obliquity(20.0, 1.0, PI / 4)
    g_upright = gv_obliquity(20.0, 1.0, 0.0)
    assert g_upright["gv_ratio"] > g_oblique["gv_ratio"]
    assert g_oblique["gv_obb_needed"] > g_upright["gv_obb_needed"]
    # frozen identity holds everywhere
    assert abs(g_oblique["gv_hbb_safe"] - g_oblique["gv_ratio"]) < TOL
    assert abs((g_oblique["gv_hbb_safe"] + g_oblique["gv_obb_needed"]) - 1.0) < TOL


def test_gv_invalid():
    g = gv_obliquity(0.0, 2.0, 0.3)
    assert math.isnan(g["gv_ratio"])


# --- risk-coverage ---------------------------------------------------------
def test_selective_risk_ordering():
    # score perfectly anti-correlated with risk -> oracle ordering
    scores = [0.9, 0.8, 0.7, 0.6]
    risks = [0.0, 1.0, 2.0, 3.0]
    cov, sel = selective_risk_curve(scores, risks)
    # selective risk monotonically non-decreasing as we add worse samples
    assert list(cov) == [0.25, 0.5, 0.75, 1.0]
    assert sel[0] == 0.0
    assert all(sel[i] <= sel[i + 1] + TOL for i in range(len(sel) - 1))
    # good selection has lower AURC than reversed (bad) selection
    aurc_good = aurc(scores, risks)
    aurc_bad = aurc(list(reversed(scores)), risks)
    assert aurc_good < aurc_bad


def test_risk_at_coverage_and_summary():
    scores = [4, 3, 2, 1, 0]
    risks = [0, 0, 0, 10, 10]
    # top 60% (k=3) all-zero risk
    assert abs(risk_at_coverage(scores, risks, 0.6) - 0.0) < TOL
    s = risk_coverage_summary(scores, risks)
    assert s["n"] == 5 and s["n_dropped"] == 0
    assert s["risk_at_70"] >= 0.0
    # full coverage selective risk == mean risk
    assert abs(risk_at_coverage(scores, risks, 1.0) - 4.0) < TOL


def test_risk_coverage_nan_dropped():
    s = risk_coverage_summary([1.0, 2.0, float("nan")], [0.5, 1.5, 9.9])
    assert s["n"] == 2 and s["n_dropped"] == 1


# --- NRC-AUC boundary sanity ----------------------------------------------
def test_nrc_auc_oracle_is_zero():
    # score == -risk -> model ordering equals oracle -> NRC-AUC == 0
    risks = [0.0, 1.0, 2.0, 3.0, 4.0]
    scores = [-r for r in risks]
    out = nrc_auc(scores, risks)
    assert abs(out["nrc_auc"] - 0.0) < 1e-9
    assert out["aurc_model"] <= out["aurc_random"] + TOL


def test_nrc_auc_worst_ordering_at_least_one():
    # score == +risk -> we keep worst first -> >= random (>=1)
    risks = [0.0, 1.0, 2.0, 3.0, 4.0]
    scores = list(risks)
    out = nrc_auc(scores, risks)
    assert out["nrc_auc"] >= 1.0 - 1e-9


def test_nrc_auc_degenerate():
    out = nrc_auc([3, 2, 1], [5.0, 5.0, 5.0])  # all equal risk
    assert out["degenerate"] is True
    assert math.isnan(out["nrc_auc"])


# --- near-square bucket placeholder ---------------------------------------
def test_near_square_bucket_placeholder():
    sq = near_square_bucket(2.0, 2.0)
    assert sq["is_member"] is True
    assert sq["pending_threshold_freeze"] is True
    el = near_square_bucket(20.0, 1.0)
    assert el["is_member"] is False
    pad = padding_only_metadata("img_001")
    assert pad["geometry_unchanged"] is True and pad["implemented"] is False


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
