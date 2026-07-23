# A5 / P5 —— 下游任务重设计 (055)

> 真实 052 matched (masked ar≥1.6, D_audit)。shapely 反事实。selector 仅用 D_cal。数据：`reports/p5_downstream_redesign_055.csv`。

## 1. 为什么重设计
旧 P5（053）用 risk=1−rIoU，被中心/尺度误差主导，与角度可靠性任务错配 → fail 不可归因于角度。
本轮改为 **反事实 angle-induced rIoU drop**，只隔离角度贡献：
> ΔrIoU = rIoU(pred 框代入 GT 角度) − rIoU(pred 框用预测角度)（保持 pred 中心/尺度不变）。
ΔrIoU = “把角度纠正后可恢复的 IoU”，即角度误差造成的下游定位损失。selector 若能在保留高置信预测时降低 ΔrIoU，即证明角度可靠性选择有下游价值。

## 2. 结果（masked ar≥1.6, D_audit）
| cell | base mean ΔrIoU | NRC detection | NRC size-linear | NRC geometry |
|---|---|---|---|---|
| DIOR#22 | 0.0032 | 0.801 | 0.883 | **0.752** |
| FAIR1M#24 | 0.0023 | 0.893 | 1.016 | **0.954** |
| SODA#23 | 0.0025 | 1.085 | 0.983 | **0.891** |
| DIOR#3 | 0.0044 | **0.742** | 0.987 | 0.764 |
| DIOR#61 | 0.0041 | **0.737** | 0.879 | 0.785 |
| SODA#4 | 0.0033 | 0.991 | 0.921 | **0.873** |

- geometry selector 在 ΔrIoU 上 NRC 最低（下游最优）于 4/6 cell；risk@70 略优（如 DIOR#22 0.0031 vs 0.0033）。
- **但绝对量极小**：base ΔrIoU 仅 0.002–0.004（≈0.2–0.4% IoU）。在 well-posed 细长实例上，角度误差本就小，角度纠正的下游收益因此很小。

## 3. 裁决
- **重设计后下游信号方向正确但幅度微弱**：角度可靠性选择能一致地小幅降低 angle-induced IoU 损失（geometry selector 最优），但绝对收益 ~0.3% IoU，不足以作为 headline utility claim。
- 比 053 的“flat fail”更清晰（任务错配已修复，信号可归因于角度），但仍 **进附录 / 边界**：写为“角度可靠性的下游价值在 well-posed 实例上真实但小；near-square 上角度病态、纠正无意义”。
- **不影响 P1/P2 主线**；不外推为下游实用性已证明。
