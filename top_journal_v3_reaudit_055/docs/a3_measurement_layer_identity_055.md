# A3 —— cliff 与测量层回归 + 论文身份决断 (055)

> 依据 A0（协议调和）、A2（约束扰动/cliff）、A1（conformal）。不新增训练。

## 1. cliff 回归测量层
aspect-ratio cliff **保留、升格为测量层核心发现**（非反校准附属）：
- 经验（A2 dose-response）：near-square 框在 IoU 上对角度几乎不可分辨（eps_max~68°，注入 68° 角扰动 mAP@0.5 仍不变），角度误差 p99 从 elongated ~10–26° 跳到 near-square ~88–90°。
- 理论（IoU(δ;ar) 曲线）：ar→1 时 IoU 在任意 δ 都 ≥0.707，角度对 IoU 病态；ar 增大后 IoU 对 δ 敏感。
- 意义：cliff = **masked 主协议（ar≥1.6）存在的根本理由**，也是 P2 分层 conformal（Mondrian by ar）的动机。
- 状态：**RETAINED（测量层核心）**，不静默删除；与反校准脱钩（反校准 headline 已 superseded，A0）。

## 2. 23-cell 测量层状态
- 原 23-cell matrix 的 **headline（PSC/NRC 跨 dataset 反校准）= SUPERSEDED**（A0：unmasked pooling artifact）。
- 本轮在冻结 masked 协议下 **严格重算的仅 7–9 个 cell**（052 权威 matched：DIOR#22/#3/#61, FAIR1M#24, SODA#23/#4, DOTA#20；+features_v2 的 DIOR#10/SODA#11 masked-only）。
- 其余 cell 未在冻结 masked 协议 + 052 provenance 下重算 → **不能继续自称 full 23-cell benchmark**。
- 状态：**测量层 = protocol + 有限重算 cell**，不是 full benchmark。

## 3. 论文身份决断
- **不是 full benchmark paper**：主分析经法证调和后只剩少量 provenance-clean cell，且 23-cell 反校准 headline 作废。
- **是 “orientation reliability measurement protocol + finite-sample risk control” paper**：
  - measure：masked NRC/AURC/risk-coverage 协议 + cliff（测量层核心）+ P1 约束扰动（mAP@0.5 无法刻画朝向，precise-pass 动机）。
  - control：P2 within-cell conformal（脊柱，A1 强化）+ score menu（geometry selector 最优）。
  - diagnose：intrinsic phase_mod 在 masked 下显著反校准（angle-coder 机制候选，A0-3）。
- 身份裁决：**Protocol + Risk Control**（遥感/可信度方向），benchmark 身份**收缩为“协议 + 有限 provenance-clean cell 的可靠性测量”**，不吹全面性。

## 4. 一句话
cliff 回归测量层核心；23-cell 反校准 headline 作废；论文从“benchmark”明确改写为“**orientation reliability measurement protocol + finite-sample conformal risk control**”。
