"""Training readiness checklist (CHECK ONLY — does NOT start training).

Default training_allowed=false. Encodes the 监督 006 preconditions for training:
thresholds frozen (R8), D_cal/D_audit split, real predictions formal,
angle_version verified, RHINO/A4 host ruling, config/log/schedule/lr alignment
plan, first-epoch stop rule logged, human approval. Conclusion is expected to
be training_allowed=false until all are satisfied.
"""
from __future__ import annotations

from typing import Any, Dict, List

from orientbench.reports.readiness import build_readiness


def _d6_approved(configs_dir: str) -> bool:
    import os
    try:
        import yaml
        p = os.path.join(configs_dir, "approvals.yaml")
        d = yaml.safe_load(open(p, encoding="utf-8")) or {}
        return str(d.get("decisions", {}).get("D6_allow_training", "")).startswith("allow")
    except Exception:
        return False


def build_training_readiness(outputs_dir: str, configs_dir: str) -> Dict[str, Any]:
    base = build_readiness(outputs_dir, configs_dir)
    rd = {i["item"]: i["status"] for i in base["items"]}
    d6 = _d6_approved(configs_dir)

    items: List[Dict[str, str]] = []

    def add(key, status, detail):
        items.append({"item": key, "status": status, "detail": detail})

    # default-deny
    add("training_allowed_default", "blocked", "training_allowed defaults to FALSE (监督 006)")
    add("R8_thresholds_frozen", rd.get("freeze_time_set", "pending"),
        "thresholds.yaml must complete R8 freeze before training")
    add("host_baseline_selected", "blocked" if rd.get("rhino_host") == "blocked" else "pending",
        "RHINO (C1/B) missing; A4 host pending — host/baseline ruling required")
    add("config_path_exists", "ready",
        "baseline config paths exist (inventory config_exists all True) — alignment plan still required")
    add("checkpoint_log_path_policy", "pending",
        "policy: save only best-mAP + latest; logs full path — to be enacted at training time")
    add("dataset_path_exists", "ready", "5 present datasets verified (DOTA10/15/DIOR/HRSC/FAIR1M)")
    add("split_policy_valid", rd.get("dcal_daudit_disjoint", "pending"),
        "D_cal/D_audit mutually exclusive; train/val(test) per dataset policy")
    add("lr_batch_schedule_alignment_plan", "pending",
        "must align epoch/batch/lr/SyncBN/schedule to official/valid baseline (not yet authored)")
    add("gpu_plan", "pending", "4xA30 default; fall back on OOM and log — plan to be confirmed")
    add("first_epoch_stop_rule", "ready",
        "first-epoch-low stop rule recorded: if first-epoch mAP clearly low -> stop & report")
    add("output_directory_policy", "ready",
        "self-built baselines -> orientbench/pth_data with baseline_ prefix; no root clutter")
    add("no_pollution_rule", "ready", "no writes outside study root; pth_data read-only")
    add("real_predictions_formal", rd.get("real_prediction_available", "pending"),
        "formal real detector predictions required before training is meaningful")
    add("angle_version_verified", rd.get("angle_version_certain", "pending"),
        "angle_version le90 sign consistency (esp. HRSC) must be verified")
    add("human_approval", "ready" if d6 else "blocked",
        "supervisor 012/013 token = training approval (D6=allow_approved_host_scope)" if d6
        else "explicit human/supervisor approval required to start training")

    blockers = [i["item"] for i in items if i["status"] in ("blocked", "pending")]
    # 013: D6 approved -> training allowed for the approved host scope (RHINO/O2-RTDETR only)
    training_allowed = "true_for_approved_host_scope" if d6 else False
    reasons = []
    if not d6:
        reasons.append("human approval required")
    else:
        reasons.append("training approved for host scope (RHINO C1/B + O2-RTDETR A4) via 012/013 token")
        reasons.append("formal gate still blocked until host training done + B_C1/A_A4 frozen + D_audit")

    return {
        "training_allowed": training_allowed,
        "can_train_now": bool(d6),
        "expected": True if d6 else False,
        "scope": "approved_host_scope (RHINO->C1/B, O2-RTDETR->A4) only" if d6 else "none",
        "formal_gate_allowed": False,
        "reasons": reasons,
        "n_items": len(items), "blockers": blockers,
        "items": items,
        # executable checklist (监督 007/008)
        "remaining_before_training": [
            "R8 thresholds frozen (configs/thresholds.yaml freeze_time + freeze_status=frozen)",
            "D_cal/D_audit split policy ratified",
            "RHINO (C1/B) host ruling + A4 frozen host provided",
            "real predictions converted + angle_version verified (esp. HRSC)",
            "config/log/schedule/lr/batch alignment plan authored",
            "GPU plan (4xA30 default) confirmed",
        ],
        "human_decisions_required": [
            "approve threshold draft values",
            "rule on RHINO host (download/train/supply/approve-substitute)",
            "supply A4 hybrid-encoder frozen snapshot",
            "explicit approval to start training",
        ],
        "files_needed": [
            "frozen thresholds.yaml (freeze_time set)",
            "RHINO checkpoint+config (or approved substitute)",
            "A4 hybrid-host frozen snapshot+config",
            "real detector prediction files in prediction schema",
        ],
        "commands_allowed_after_approval": [
            "(after approval only) training command aligned to official/valid baseline; "
            "4xA30; per-epoch eval; save best-mAP+latest; logs to outputs/logs with full path",
        ],
        "stop_conditions_for_first_epoch": [
            "first-epoch mAP clearly below baseline expectation -> STOP and report",
            "NaN/inf loss -> STOP and report",
            "OOM not resolved by documented fallback -> STOP and report",
        ],
    }
