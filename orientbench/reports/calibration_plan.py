"""D_cal calibration plan (no freeze).

For each draft threshold field, states what input it needs, how D_cal estimates
it, how D_audit audits it, and whether it is blocked pending real predictions.
Does NOT write thresholds.yaml.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

from orientbench.reports.threshold_proposal import build_threshold_review

# which fields fundamentally require real detector predictions to calibrate
_NEEDS_REAL_PRED = {
    "ot_vs_gt_identity.min_delta", "padding_only_tie.max_delta_abs", "drop_rate_max",
    "cycle_err_max", "partial_corr_max_abs", "hsic_p_min_after_correction",
    "all_source_vs_best_single_delta_min", "spearman_mAP_NRC_max",
    "effect_size_min.background_phase_spearman",
}


def _real_predictions_available(outputs_dir: str) -> bool:
    p = os.path.join(outputs_dir, "reports", "prediction_discovery.csv")
    if not os.path.isfile(p):
        return False
    import csv
    with open(p, "r", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            if r.get("schema_status") == "matches_prediction_schema" and r.get("origin") == "external":
                return True
    return False


def _real_prediction_smoke(outputs_dir: str):
    p = os.path.join(outputs_dir, "reports", "real_prediction_smoke_summary.json")
    if not os.path.isfile(p):
        return 0, False
    import json
    with open(p, "r", encoding="utf-8") as fh:
        d = json.load(fh)
    n_ok = d.get("n_ok", 0)
    # angle convention mismatch blocks angle-dependent calibration on smoke data
    angle_blocked = any(r.get("smoke_risk_validity") == "INVALID_angle_convention_mismatch"
                        for r in d.get("rows", []) if r.get("status") == "ok")
    return n_ok, angle_blocked


def build_calibration_plan(outputs_dir: str) -> Dict[str, Any]:
    review = build_threshold_review()
    have_pred = _real_predictions_available(outputs_dir)
    n_smoke, angle_blocked = _real_prediction_smoke(outputs_dir)
    # splits present?
    splits_meta = os.path.join(outputs_dir, "splits", "splits_summary.json")
    have_splits = os.path.isfile(splits_meta)
    rows: List[Dict[str, Any]] = []
    for r in review:
        needs_pred = r["field"] in _NEEDS_REAL_PRED
        blocked = needs_pred and not have_pred
        rows.append({
            "module": r["module"], "field": r["field"], "draft_value": r["draft_value"],
            "input_needed": ("real detector predictions on D_cal" if needs_pred
                             else "GT/bucket/source dry-run on D_cal"),
            "dcal_estimation": ("estimate metric distribution on D_cal, pick threshold at target "
                                "coverage/FDR" if needs_pred else "compute directly from D_cal GT-derived stats"),
            "daudit_audit": "re-evaluate on disjoint D_audit; no threshold tuning on D_audit",
            "status": "blocked_needs_real_prediction" if blocked else
                      ("ready_to_estimate" if have_splits else "blocked_needs_splits"),
        })
    n_blocked = sum(1 for r in rows if r["status"].startswith("blocked"))
    return {
        "have_real_predictions": have_pred, "have_splits": have_splits,
        "have_real_prediction_smoke": n_smoke > 0,
        "n_real_prediction_smoke": n_smoke,
        "smoke_angle_convention_blocked": angle_blocked,
        "smoke_note": ("real_prediction_smoke available但 angle convention mismatch(~88deg)未解决，"
                       "angle-error 相关阈值仍不能用 smoke 数据标定；score/coverage 类可先非正式探索"
                       if n_smoke else "no real prediction smoke yet"),
        "n_fields": len(rows), "n_blocked": n_blocked,
        "n_ready_to_estimate": sum(1 for r in rows if r["status"] == "ready_to_estimate"),
        "rows": rows,
    }
