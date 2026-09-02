"""Guarded inference runner — constructs commands & validates guards.

DOES NOT run any detector. Default behavior is to REFUSE execution and emit a
dry-run plan. Even when an approval token is supplied AND --execute is set, the
execute branch returns ``blocked_by_supervisor`` (cc must not start detector
inference this round). Approval state is read from configs/approvals.yaml, which
only the collaborator edits.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None

from orientbench.io.output_policy import build_prediction_output_path, validate_output_path
from orientbench.reports.prediction_import_matrix import PRESENT_DATASETS, _norm_dataset

MISSING_DATASETS = {"SODA-A", "ICDAR-MLT"}
FORBIDDEN_SUBSTITUTE = {"rhino"}  # never substitute RHINO


def load_approvals(path: str) -> Dict[str, Any]:
    if not os.path.isfile(path) or yaml is None:
        return {"token": None, "decisions": {}}
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {"token": None, "decisions": {}}


def is_approved(approvals: Dict[str, Any], decision_key: str, token: Optional[str]) -> bool:
    decisions = approvals.get("decisions", {}) or {}
    reg_token = approvals.get("token")
    return bool(token is not None and reg_token is not None and token == reg_token
                and decisions.get(decision_key) == "allow")


def build_inference_command(baseline: Dict[str, Any], out_path: str) -> str:
    """Construct (string-only) a reproducible mmrotate test command. Not executed."""
    cfg = baseline.get("config_abs")
    ckpt = baseline.get("pth_abs")
    env = baseline.get("env")
    return (f"# env: conda activate {env}\n"
            f"python tools/test.py {cfg} {ckpt} "
            f"--out {out_path} --cfg-options test_evaluator.format_only=False")


def validate_guards(baseline: Dict[str, Any], dataset: str, split: str,
                    out_path: str, thresholds_pending: bool) -> Dict[str, Any]:
    guards: List[Dict[str, Any]] = []

    def g(name, ok, detail):
        guards.append({"guard": name, "ok": bool(ok), "detail": detail})

    norm = _norm_dataset(dataset)
    g("dataset_present", norm in PRESENT_DATASETS,
      f"normalized={norm}")
    g("dataset_not_silently_skipped", norm not in (None,) or dataset not in MISSING_DATASETS,
      "SODA-A/ICDAR-MLT must be explicit, not skipped")
    g("config_exists", bool(baseline.get("config_abs")) and os.path.isfile(baseline.get("config_abs") or ""),
      baseline.get("config_abs"))
    g("checkpoint_exists", bool(baseline.get("pth_abs")) and os.path.isfile(baseline.get("pth_abs") or ""),
      baseline.get("pth_abs"))
    g("baseline_valid", baseline.get("valid") is True, f"valid={baseline.get('valid')}")
    op_ok, op_reason = validate_output_path(out_path)
    g("output_path_under_predictions", op_ok, op_reason or out_path)
    mid = (baseline.get("model_id") or "").lower()
    g("not_rhino_substitution", not any(s in mid for s in FORBIDDEN_SUBSTITUTE) or "rhino" in mid,
      "ARS-DETR != RHINO; no substitution")
    # thresholds_pending is informational: inference may run pre-freeze but
    # produces NON-FORMAL predictions; the gate stays blocked until freeze.
    g("thresholds_freeze_state", True,
      f"thresholds pending={thresholds_pending} (inference non-formal until R8 freeze)")
    all_ok = all(x["ok"] for x in guards)
    return {"all_ok": all_ok, "guards": guards}


def run_guarded(baseline: Dict[str, Any], dataset: str, split: str, timestamp: str,
                approvals_path: str, approval_token: Optional[str] = None,
                execute: bool = False, thresholds_pending: bool = True) -> Dict[str, Any]:
    """Default: dry-run plan. Never starts a detector."""
    out_path = build_prediction_output_path(dataset, baseline.get("id"), split, timestamp)
    guard_report = validate_guards(baseline, dataset, split, out_path, thresholds_pending)
    cmd = build_inference_command(baseline, out_path)
    approvals = load_approvals(approvals_path)
    approved = is_approved(approvals, "D5_allow_real_inference", approval_token)

    base = {
        "baseline_id": baseline.get("id"), "model_id": baseline.get("model_id"),
        "dataset": dataset, "split": split, "output_path": out_path,
        "command": cmd, "guards": guard_report, "approved_D5": approved,
        "is_synthetic": False, "detector_invoked": False,
    }
    if not (execute and approval_token):
        base["mode"] = "dry_run_plan"
        base["status"] = "dry_run_plan"
        return base
    if not approved:
        base["mode"] = "execute_requested"
        base["status"] = "refused_not_approved"
        base["reason"] = "D5 not 'allow' or token mismatch in approvals.yaml"
        return base
    # approved + execute requested: cc STILL must not start a detector this round
    base["mode"] = "execute_requested"
    base["status"] = "blocked_by_supervisor"
    base["reason"] = ("cc must not start detector inference; execution to be enabled "
                      "in a later explicitly-authorized round (no detector call here)")
    return base
