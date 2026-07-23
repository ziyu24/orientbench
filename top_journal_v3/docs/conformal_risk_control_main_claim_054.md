# Conformal Risk Control 主贡献说明 054

## 核心定位

Conformal orientation risk control 是收缩版论文的主贡献。它不是新的 selection score，也不与 score-only、geometry-aware selector、TTA variance 并列为同类打分器。它是套在任意 score 上的阈值与保证层：先由 score 给出排序或候选集合，再由 D_cal 上的 conformal / CRC 规则确定阈值，最后在 D_audit 上报告 empirical risk、coverage 和 violation。

## Within-cell 保证

在 within-cell 设置中，D_cal 与 D_audit 来自同一 cell，且 frozen split 互斥。053 使用 052 full real matched tables 得到七个关键 cell 的结果：

| cell | alpha(deg) | confidence | empirical risk | coverage | violation rate | audit n |
|---|---:|---:|---:|---:|---:|---:|
| DOTA-v1.0/20 | 15.0 | 0.90 | 1.3941 | 0.9321 | 0.0000 | 280 |
| DIOR-R/22 | 15.0 | 0.90 | 4.6681 | 0.9437 | 0.0000 | 15466 |
| FAIR1M-v1.0/24 | 15.0 | 0.90 | 4.6945 | 0.9496 | 0.0000 | 26108 |
| SODA-A/23 | 15.0 | 0.90 | 5.0777 | 0.9475 | 0.0000 | 157586 |
| DIOR-R/3 | 15.0 | 0.90 | 4.4872 | 0.9445 | 0.0000 | 16743 |
| DIOR-R/61 | 15.0 | 0.90 | 4.1538 | 0.9412 | 0.0000 | 17033 |
| SODA-A/4 | 15.0 | 0.90 | 5.0303 | 0.9493 | 0.0000 | 192250 |

该结果可以正式表述为：在预注册 frozen D_cal / D_audit 的 within-cell 设置下，conformal threshold layer 将 selected orientation risk 控制在 alpha=15 degrees 以内，并在 audit split 上观察到 0 violation rate。finite-sample guarantee 的有效性依赖 exchangeability / 同分布假设。

## Shift audit 能说什么

Shift audit 可以说：当阈值从 source cell 迁移到 target cell 时，coverage、empirical risk 和 violation rate 如何变化。它是 detector/dataset shift 下的压力测试和退化审计。

Shift audit 不能说：分布移位下仍有与 within-cell 相同的严格 conformal guarantee。论文中必须写明 `strict_shift_guarantee_claimed=False`，并把 shift 部分作为 audit，而不是理论保证。

## 如何作为收缩版论文主贡献

P2 使论文不止是 benchmark：它把 orientation reliability 从事后诊断推进到风险可控的选择性预测语法。即使 P1 仅 partial、P3/P4 不足以支撑方法成功、P5 没有下游收益，P2 仍给出一个可执行且可验证的正贡献：在真实 detector matched predictions 上，对朝向预测进行 risk-controlled selection。

## 建议主文表述

推荐表述：

> We use conformal risk control as a thresholding and guarantee layer over orientation reliability scores. In within-cell calibration/audit splits, the selected predictions satisfy the target angle-risk level empirically with finite-sample conformal semantics under exchangeability. Under detector or dataset shift, we report degradation as an audit and do not claim strict conformal validity.

禁止表述：

- conformal selector 打败其他 score。
- conformal 是新的 selection score。
- shift setting 下仍有严格 guarantee。
- conformal 证明 detector 本身可靠。
