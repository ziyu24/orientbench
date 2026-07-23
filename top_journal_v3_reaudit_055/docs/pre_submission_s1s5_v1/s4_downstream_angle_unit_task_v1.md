# S4 —— 角度单位下游任务 (v1)

> 数据：`reports/pre_submission_s1s5_v1/s4_downstream_angle_unit_v1.csv`。masked ar≥1.6，risk = 角度误差（度）。selector 在 D_fit 上训练。只报 OBB long-axis 几何朝向，非 semantic heading。

## 数据来源说明
HRSC 本地仅有 **synthetic proxy 预测**（is_synthetic=true / not_detector_output=true），不可作 detector evidence。故改用真实 052 匹配表中的 **方向类**（ship / harbor / large-vehicle / small-vehicle / plane / warship 等）做角度单位选择性预测。替换旧 ΔrIoU（被中心/尺度主导、且收益仅 ~0.3% IoU）。

## 结果（角度误差为度，越低越好）
| cell (方向类) | base mean° | R@70 detection | R@70 size-linear | R@70 geometry |
|---|---|---|---|---|
| SODA#4 (plane/large-veh/ship/small-veh, n=140k) | 2.78 | 2.51 | 2.38 | **2.35** |
| DIOR#3 (plane/harbor/ship, n=7.6k) | 1.91 | 1.64 | 1.62 | 1.64 |
| FAIR1M#24 (A220/A321/Motorboat/Warship, n=714) | 2.80 | 2.92 | 2.50 | **2.51** |
| DIOR#22 (plane/harbor/ship, n=6.9k) | 1.81 | 1.63 | 1.59 | 1.60 |

## 裁决
- **角度单位下游收益真实但 modest 且 cell-dependent**：
  - SODA#4（大车/船，大样本）geometry 在 70% 覆盖把角度误差从 2.51°降到 2.35°（~6%）。
  - FAIR1M#24（detection 弱）size-linear/geometry 明显优于 detection（2.5 vs 2.92）。
  - DIOR 两 cell 几乎无改善（detection 已强）。
- 相比 ΔrIoU（~0.3% IoU，不可解释）**改善在于可解释（度）**，但绝对幅度仍小（0.1–0.4°）。
- **P5 留附录/边界**：角度可靠性选择在方向类上带来真实但小的角度收益；**不写下游 utility proven**，不影响 P1/P2 主线。
- 局限：无真实 HRSC detector 预测；方向类仅用 OBB long-axis 几何朝向，不涉 semantic heading。
