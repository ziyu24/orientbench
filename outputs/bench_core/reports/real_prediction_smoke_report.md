# Real Prediction Smoke Report (D_cal scale)

> real predictions (D5/D7 授权)；3 detector archetypes；DOTA-v1.0 val 600-img 子集；**非正式 gate**；不训练。

- baselines OK: 3；failed/skipped: 3；GT objects: 21349；D_cal imgs=266 D_audit imgs=296
- angle convention: **RESOLVED_longside_canonical**（median orientation error ~1.6°，已解决 88° 二义性）

## 成功 baseline（真实指标，non-formal）
| baseline | archetype | dets | D_cal matched | med_err° | Risk@70 | Risk@90 | NRC | schema_issues |
|---|---|---|---|---|---|---|---|---|
| b1 oriented_rcnn_r50 | two_stage_regression | 29461 | 9820 | 1.564 | 2.2687 | 2.3864 | 0.9736 | none |
| b20 rotated_retinanet_psc_r50 | angle_coder_psc | 70137 | 7549 | 1.599 | 3.0532 | 2.9161 | 1.3113 | none |
| b32 rotated_rtmdet_s | one_stage_realtime | 49278 | 9926 | 1.596 | 2.2916 | 2.4482 | 0.7767 | none |

## 失败/跳过 baseline
| baseline | stage | reason |
|---|---|---|
| b7 oriented_rcnn_lsknet_s | inference | LSKNet backbone not registered in available mmrotate (needs LSKNet repo on path/install) |
| b14 arsdetr_r50 | inference | ARSDETR not registered (needs ARS-DETR fork mmrotate); DETR-like, NOT RHINO |
| b64 point2rbox_v2 | inference | weak/pseudo supervision; real inference semantics not standard test — skipped |

## angle-version 状态
- DOTA-v1.0：**RESOLVED**（mmrotate GT + long-side canonical，median ~1.6°）。HRSC mbox le90 仍 uncertain（未接 HRSC prediction）。
## 是否可进入 D_cal / 正式 gate
- D_cal calibration input: **available**（真实 Risk@90/NRC，见 calibration_candidate_report）。
- formal_gate_allowed=**False**（thresholds 未冻结 R8）；training_allowed=**False**。
## schema 校验
- 全部 is_synthetic=False, not_detector_output=False, score∈[0,1], 坐标范围正常, 0 异常；converter_version=mmrotate1x_v1+longside_canon。
## 下一批建议
1. 0.x/fork baseline（LSKNet/ARSDETR）需其自带 repo 注册模型才能推理（依赖安装，需裁示）。
2. 扩到完整 val (5297) 或更大 D_cal；接 HRSC/DIOR 等以解 HRSC angle。
3. 合作者批准 D1 阈值候选 + R8 冻结后方可正式 gate；D6 训练仍未批准。
