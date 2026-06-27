# Threshold Freeze Proposal (DRAFT)

> 生成时间: 2026-06-25 18:21:48 CST
> proposed_by=claude_draft approval_status=pending freeze_status=draft_not_frozen
> 草案；不修改 thresholds.yaml；不冻结；待合作者审批。

## B_C1 (draft)
- status: draft
- drop_rate_max: 0.5
- cycle_err_max: 0.3
- transport_entropy_min: 0.2
- transport_entropy_max: 0.9
- ot_vs_gt_identity: {'metric': 'NRC-AUC', 'min_delta': 0.03, 'test': 'paired_bootstrap'}
- padding_only_tie: {'metric': 'NRC-AUC', 'max_delta_abs': 0.01}
- ota_kl_tie: {'metric': 'NRC-AUC', 'max_delta_abs': 0.01}

## A_A4 (draft)
- status: draft
- partial_corr_max_abs: 0.2
- hsic_p_min_after_correction: 0.05
- gv_baseline_delta_min: 0.03
- entropy_baseline_delta_min: 0.03
- all_source_vs_best_single_delta_min: 0.02

## D2 (draft)
- status: draft
- spearman_mAP_NRC_max: 0.95
- fdr_method: benjamini_hochberg
- bonferroni_alpha: 0.05
- effect_size_min: {'background_phase_spearman': 0.2, 'layout_mask_angle_collapse': 0.15, 'domain_shift_survival_min': 0.5}

## Rationale
- D2.spearman_mAP_NRC_max: 项目执行文件 §12.2 停止条件上界，照搬
- B_C1.ot_vs_gt_identity.min_delta: draft: NRC-AUC 改善需 >0.03 才算非 GT-identity 副产物
- A_A4.partial_corr_max_abs: draft: source attribution 偏相关上界，待 HSIC 联合校准
- general: 其余数值为占位草案，需各责任角色用 D_cal 数据标定后替换

## 审批流程
1. 各责任角色用 D_cal 数据标定占位数值；2. 填入 thresholds.yaml 并设 freeze_time + responsible_role；3. 设 freeze_status=frozen 后方可做正式 gate（本脚本不执行此步）。
