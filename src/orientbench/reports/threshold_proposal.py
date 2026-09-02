"""Threshold-freeze PROPOSAL (draft only — does NOT freeze).

Produces a draft set of gate thresholds for collaborator approval. Values are
proposed_by=claude_draft, approval_status=pending. The live configs/thresholds.yaml
freeze_status is NOT modified; the draft is written to a separate file.
"""
from __future__ import annotations

from typing import Any, Dict

# Draft proposed values (starting points for discussion — NOT approved).
DRAFT = {
    "project": "orientbench",
    "version": "v1.0-draft",
    "proposed_by": "claude_draft",
    "approval_status": "pending",
    "freeze_status": "draft_not_frozen",     # NEVER 'frozen' here
    "freeze_time": None,
    "note": "草案待合作者审批；数值为讨论起点，非批准值；不得据此冻结或做正式 gate。",
    "B_C1": {
        "status": "draft",
        "drop_rate_max": 0.50,
        "cycle_err_max": 0.30,
        "transport_entropy_min": 0.20,
        "transport_entropy_max": 0.90,
        "ot_vs_gt_identity": {"metric": "NRC-AUC", "min_delta": 0.03, "test": "paired_bootstrap"},
        "padding_only_tie": {"metric": "NRC-AUC", "max_delta_abs": 0.01},
        "ota_kl_tie": {"metric": "NRC-AUC", "max_delta_abs": 0.01},
    },
    "A_A4": {
        "status": "draft",
        "partial_corr_max_abs": 0.20,
        "hsic_p_min_after_correction": 0.05,
        "gv_baseline_delta_min": 0.03,
        "entropy_baseline_delta_min": 0.03,
        "all_source_vs_best_single_delta_min": 0.02,
    },
    "D2": {
        "status": "draft",
        "spearman_mAP_NRC_max": 0.95,
        "fdr_method": "benjamini_hochberg",
        "bonferroni_alpha": 0.05,
        "effect_size_min": {
            "background_phase_spearman": 0.20,
            "layout_mask_angle_collapse": 0.15,
            "domain_shift_survival_min": 0.50,
        },
    },
    "rationale": {
        "D2.spearman_mAP_NRC_max": "项目执行文件 §12.2 停止条件上界，照搬",
        "B_C1.ot_vs_gt_identity.min_delta": "draft: NRC-AUC 改善需 >0.03 才算非 GT-identity 副产物",
        "A_A4.partial_corr_max_abs": "draft: source attribution 偏相关上界，待 HSIC 联合校准",
        "general": "其余数值为占位草案，需各责任角色用 D_cal 数据标定后替换",
    },
}


def build_threshold_draft() -> Dict[str, Any]:
    return dict(DRAFT)


def build_threshold_review() -> list:
    """Flatten the draft into a review packet (one row per threshold field)."""
    d = build_threshold_draft()
    rows = []

    def add(module, field, value, needs_dcal, affects_daudit, risk):
        rows.append({
            "module": module, "field": field, "draft_value": value,
            "rationale": d["rationale"].get(f"{module}.{field}",
                         d["rationale"].get("general", "draft placeholder")),
            "needs_D_cal": needs_dcal, "affects_D_audit": affects_daudit,
            "approval_status": "pending",
            "risk_if_changed_after_run": risk,
        })

    add("B_C1", "drop_rate_max", d["B_C1"]["drop_rate_max"], True, True,
        "changing post-run invalidates DropRate stop decision")
    add("B_C1", "cycle_err_max", d["B_C1"]["cycle_err_max"], True, True, "invalidates cycle-consistency gate")
    add("B_C1", "ot_vs_gt_identity.min_delta", d["B_C1"]["ot_vs_gt_identity"]["min_delta"], True, True,
        "changing alters whether OT beats GT-identity (R1)")
    add("B_C1", "padding_only_tie.max_delta_abs", d["B_C1"]["padding_only_tie"]["max_delta_abs"], True, True,
        "alters padding-only tie ruling")
    add("A_A4", "partial_corr_max_abs", d["A_A4"]["partial_corr_max_abs"], True, True,
        "alters source-attribution significance")
    add("A_A4", "hsic_p_min_after_correction", d["A_A4"]["hsic_p_min_after_correction"], True, True,
        "alters HSIC independence ruling")
    add("A_A4", "all_source_vs_best_single_delta_min", d["A_A4"]["all_source_vs_best_single_delta_min"],
        True, True, "alters multi-source benefit claim")
    add("D2", "spearman_mAP_NRC_max", d["D2"]["spearman_mAP_NRC_max"], False, True,
        "raising hides NRC-mAP redundancy (stop condition)")
    add("D2", "effect_size_min.background_phase_spearman",
        d["D2"]["effect_size_min"]["background_phase_spearman"], True, True,
        "alters probe-cell significance")
    add("D2", "fdr_method", d["D2"]["fdr_method"], False, True,
        "changing multiple-comparison control after run is p-hacking risk")
    return rows
