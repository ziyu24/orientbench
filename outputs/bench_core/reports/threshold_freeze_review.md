# Threshold Freeze Review

> 生成时间: 2026-06-25 23:34:10 CST
> 基于 thresholds.draft.yaml；不修改 thresholds.yaml（仍 pending）；approval_status 全 pending。

| module | field | draft_value | needs_D_cal | affects_D_audit | risk_if_changed_after_run |
|---|---|---|---|---|---|
| B_C1 | drop_rate_max | 0.5 | True | True | changing post-run invalidates DropRate stop decision |
| B_C1 | cycle_err_max | 0.3 | True | True | invalidates cycle-consistency gate |
| B_C1 | ot_vs_gt_identity.min_delta | 0.03 | True | True | changing alters whether OT beats GT-identity (R1) |
| B_C1 | padding_only_tie.max_delta_abs | 0.01 | True | True | alters padding-only tie ruling |
| A_A4 | partial_corr_max_abs | 0.2 | True | True | alters source-attribution significance |
| A_A4 | hsic_p_min_after_correction | 0.05 | True | True | alters HSIC independence ruling |
| A_A4 | all_source_vs_best_single_delta_min | 0.02 | True | True | alters multi-source benefit claim |
| D2 | spearman_mAP_NRC_max | 0.95 | False | True | raising hides NRC-mAP redundancy (stop condition) |
| D2 | effect_size_min.background_phase_spearman | 0.2 | True | True | alters probe-cell significance |
| D2 | fdr_method | benjamini_hochberg | False | True | changing multiple-comparison control after run is p-hacking risk |

- live thresholds.yaml freeze_status: **pending**（未改）
- 审批后由责任角色用 D_cal 标定数值，填 thresholds.yaml + freeze_time，再设 freeze_status=frozen。
