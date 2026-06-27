# D_cal Calibration Plan

> 生成时间: 2026-06-26 09:11:25 CST
> 标定准备；不冻结；不写回 thresholds.yaml。

- have_real_predictions: False; have_splits: True
- fields: 10; **blocked: 9**; ready_to_estimate: 1

| module | field | input_needed | status |
|---|---|---|---|
| B_C1 | drop_rate_max | real detector predictions on D_cal | **blocked_needs_real_prediction** |
| B_C1 | cycle_err_max | real detector predictions on D_cal | **blocked_needs_real_prediction** |
| B_C1 | ot_vs_gt_identity.min_delta | real detector predictions on D_cal | **blocked_needs_real_prediction** |
| B_C1 | padding_only_tie.max_delta_abs | real detector predictions on D_cal | **blocked_needs_real_prediction** |
| A_A4 | partial_corr_max_abs | real detector predictions on D_cal | **blocked_needs_real_prediction** |
| A_A4 | hsic_p_min_after_correction | real detector predictions on D_cal | **blocked_needs_real_prediction** |
| A_A4 | all_source_vs_best_single_delta_min | real detector predictions on D_cal | **blocked_needs_real_prediction** |
| D2 | spearman_mAP_NRC_max | real detector predictions on D_cal | **blocked_needs_real_prediction** |
| D2 | effect_size_min.background_phase_spearman | real detector predictions on D_cal | **blocked_needs_real_prediction** |
| D2 | fdr_method | GT/bucket/source dry-run on D_cal | **ready_to_estimate** |

说明：blocked_needs_real_prediction 项必须先接入真实 detector predictions（D5/D7 批准后），在 D_cal 上估计、在 D_audit 上审计（不得在 D_audit 上调阈值）。冻结由责任角色在批准后执行。
