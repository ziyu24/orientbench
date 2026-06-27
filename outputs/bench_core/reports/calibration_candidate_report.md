# Calibration Candidate Report (real prediction D_cal)

> 生成时间: 2026-06-26 09:07:45 CST
> 真实 prediction（D5/D7 授权）；angle convention RESOLVED (long-side)；**非正式 gate**；approval_status=pending；thresholds.yaml 未冻结。

- D_cal images: 266；D_audit images: 296（互斥 hash split）

| baseline | archetype | D_cal matched | D_cal med_err° | D_cal Risk@90 | D_cal NRC | D_audit Risk@90 | D_audit NRC |
|---|---|---|---|---|---|---|---|
| b1 | two_stage_regression | 9820 | 1.564 | 2.3864 | 0.9736 | 2.4543 | 0.8138 |
| b20 | angle_coder_psc | 7549 | 1.599 | 2.9161 | 1.3113 | 2.7927 | 1.0059 |
| b32 | one_stage_realtime | 9926 | 1.596 | 2.4482 | 0.7767 | 2.464 | 0.7523 |

说明：orientation error 用 long-side canonical（解决 le90 (w,h,θ) 二义性），median ~1° 表示真实prediction 朝向精确。Risk@90/NRC 为真实非正式度量，可作 D_cal 标定输入；冻结仍需合作者批准(D1)+R8。
D_audit 指标仅用于审计对照，**不得在 D_audit 上调阈值**。
