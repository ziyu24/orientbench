# Threshold Freeze Record

> freeze_time: 2026-06-26 09:51:38 CST
> approval_token: SUPERVISOR_APPROVED_012_D1_R8_D6_HOST_TRAINING

- freeze_status: **partial_frozen_dota_d2** (B_C1/A_A4 pending hosts)
- calibration_split: D_cal (D_audit NOT consulted)
- metric_version: orientation_risk_v1 / normalization_version: longside_v1
- data_fingerprint: `b49a350d5600b720`  code_fingerprint: `f5ef709cfb7b3935`
- **frozen thresholds.yaml sha256: `4a8e0202679f60945c4776a1596001dfaa92397e059d6006918cfe82eece7593`**

## Frozen DOTA D2 gate
- per_detector_nrc_auc_pass_max = 1.0 (detector passes if NRC_AUC<=1.0, beats random)
- spearman_mAP_NRC_max = 0.95 (D2 independence stop condition, project §12.2)
- orientation_risk_metric = angle_error_canonical_longside (deg); near_square masked
- D_cal reference: baseline_1:NRC=0.9736/R@90=2.3864deg, baseline_20:NRC=1.3113/R@90=2.9161deg, baseline_32:NRC=0.7767/R@90=2.4482deg

此后不得因 D_audit 修改阈值；定义级错误只能另起版本并保留旧版本。
