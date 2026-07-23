# A0-3 —— 前版证据去向审计 (055)

> 数据表：`reports/a0_evidence_lineage_reconciliation_055.csv`。每条证据标 retained / superseded / out_of_scope / invalid / pending_recompute。cliff 回归测量层，不静默删除。

## 逐条

| 证据 | 状态 | 说明 |
|---|---|---|
| detection-score PSC 反校准（1.083/1.260；1.1265/1.5061/1.6733） | **SUPERSEDED** | pooling artifact；masked ar≥1.6 → 0.885/0.914 显著校准 |
| DIOR#22 detection-score masked NRC=0.549 | **RETAINED** | 复现 0.542 [0.529,0.556] |
| intrinsic phase_mod 反校准（1.156/1.117/1.121） | **RETAINED_RECOMPUTED** | masked 幸存：1.129/1.101/1.090，CI 全>1 → 机制候选 |
| aspect-ratio cliff（masked p99 10–26° vs unmasked 88–90°） | **RETAINED（测量层）** | near-square 病态性即 masked 协议要形式化的对象，回归测量层（A3），不删 |
| non-PSC leave-* deployable 8/9（047） | **OUT_OF_SCOPE / PENDING** | selector-gain 分析，非 NRC-protocol；deployable 降为 candidate |
| deployable hardening 12/12 retained 0.645（040） | **OUT_OF_SCOPE / PENDING** | 同上；须采用 masked 标签 |
| Route-C real TTA（042/044/046） | **RETAINED（并入 P2 score menu）** | TTA circular variance 作为 conformal guarantee layer 的一个 score（A1-3），非独立 deployable claim |
| DOTA#20 P3 negative control / mAP 0.0132 | **INVALID_PENDING** | 19-图 subset scope；见 a0_dota20 |
| 053/054 P1 均匀 30° 扰动解耦 | **SUPERSEDED** | 破坏 rIoU>0.5；由 A2 约束扰动替代 |

## cliff 的显式去向
aspect-ratio cliff **不作废、不删除**，从“反校准证据的附属”升级为 **测量层核心发现**：随 aspect ratio → 1，角度估计病态、误差 p99 从 ~10–26°（elongated）跳到 ~88–90°（near-square）。这正是 masked 主协议存在的理由，也是 P2 分层 conformal（A1-4，Mondrian by ar）的动机。详见 `a3_measurement_layer_identity_055.md`。

## 机制信号的“搬家”
反校准信号从 **detection-score（Track B）搬到 intrinsic phase_mod（Track A）**：masked 下 detection-score 校准、phase_mod 反校准。故正文的诊断故事应写成“**PSC angle-coder 的内在置信度对角度误差反序**”，而非“detection-score 反校准”。这是本轮相对 049–054 的实质修正。
