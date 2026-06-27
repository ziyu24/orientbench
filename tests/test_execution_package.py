"""Focused tests for 010 approval-gated execution package."""
from __future__ import annotations

import os
import sys

_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.output_policy import build_prediction_output_path, validate_output_path
from orientbench.reports.baseline_shortlist import build_shortlist
from orientbench.reports.calibration_plan import build_calibration_plan
from orientbench.reports.training_readiness import build_training_readiness
from orientbench.runners.inference_runner import is_approved, run_guarded

OUT = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")
CONFIGS = os.path.join(_PROJECT_ROOT, "configs")
APPROVALS = os.path.join(CONFIGS, "approvals.yaml")

BASELINE = {"id": 1, "model_id": "oriented_rcnn_r50_fpn_1x_le90", "dataset": "DOTA-v1.0",
            "valid": True, "config_abs": __file__, "pth_abs": __file__, "env": "pcp-obb"}


def test_output_path_under_predictions():
    p = build_prediction_output_path("DOTA-v1.0", 1, "train", "2026-06-25_000000")
    ok, reason = validate_output_path(p)
    assert ok is True
    assert "outputs/predictions" in p


def test_output_path_rejects_forbidden():
    ok, _ = validate_output_path("/home/rspip/cqc/pro/study/pth_data/x.jsonl")
    assert ok is False
    ok2, _ = validate_output_path("/home/rspip/cqc/pro/study/orientbench/root_clutter.jsonl")
    assert ok2 is False
    ok3, _ = validate_output_path("/home/rspip/cqc/data/dataset/x.jsonl")
    assert ok3 is False


def test_runner_default_refuses_execution():
    res = run_guarded(BASELINE, "DOTA-v1.0", "train", "ts", APPROVALS)
    assert res["mode"] == "dry_run_plan"
    assert res["detector_invoked"] is False
    assert "command" in res


def test_runner_execute_without_approval_refused():
    # execute requested but no token / not approved -> refused, no detector
    res = run_guarded(BASELINE, "DOTA-v1.0", "train", "ts", APPROVALS,
                      approval_token="anything", execute=True)
    assert res["status"] in ("refused_not_approved", "blocked_by_supervisor")
    assert res["detector_invoked"] is False


def test_runner_execute_branch_never_calls_detector(monkeypatch):
    # even simulating an approved decision, cc must NOT start a detector
    import orientbench.runners.inference_runner as ir
    monkeypatch.setattr(ir, "load_approvals",
                        lambda p: {"token": "T", "decisions": {"D5_allow_real_inference": "allow"}})
    res = run_guarded(BASELINE, "DOTA-v1.0", "train", "ts", APPROVALS,
                      approval_token="T", execute=True)
    assert res["status"] == "blocked_by_supervisor"
    assert res["detector_invoked"] is False


def test_is_approved_logic():
    appr = {"token": "T", "decisions": {"D5_allow_real_inference": "allow"}}
    assert is_approved(appr, "D5_allow_real_inference", "T") is True
    assert is_approved(appr, "D5_allow_real_inference", "wrong") is False
    assert is_approved({"token": None, "decisions": {"D5_allow_real_inference": "allow"}},
                       "D5_allow_real_inference", "T") is False
    assert is_approved({"token": "T", "decisions": {"D5_allow_real_inference": "pending"}},
                       "D5_allow_real_inference", "T") is False


def test_shortlist_arsdetr_is_detr_like_not_rhino():
    res = build_shortlist(OUT)
    detr = [r for r in res["rows"] if r["archetype"] == "detr_like"]
    assert detr and "arsdetr" in (detr[0].get("model_id") or "").lower()
    assert "NOT a RHINO" in detr[0]["why_selected"]
    rhino = [r for r in res["rows"] if r["archetype"] == "rotated_detr_rhino"]
    assert rhino and rhino[0]["status"] == "blocked_missing"
    assert "NOT be substituted" in rhino[0]["risks"]


def test_calibration_plan_blocked_without_real_prediction():
    res = build_calibration_plan(OUT)
    # no real predictions imported -> the pred-dependent fields are blocked
    assert res["have_real_predictions"] is False
    assert res["n_blocked"] >= 1
    assert any(r["status"] == "blocked_needs_real_prediction" for r in res["rows"])


def test_training_allowed_still_false():
    res = build_training_readiness(OUT, CONFIGS)
    assert res["training_allowed"] == "true_for_approved_host_scope"  # 013 D6
    assert res["formal_gate_allowed"] is False


if __name__ == "__main__":
    import tempfile, pathlib
    passed = failed = 0
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                if "monkeypatch" in fn.__code__.co_varnames[:fn.__code__.co_argcount]:
                    print(f"SKIP {name} (needs pytest monkeypatch)")
                    continue
                fn()
                passed += 1
                print(f"PASS {name}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {e}")
    print(f"\n{passed} passed, {failed} failed")
    raise SystemExit(1 if failed else 0)
