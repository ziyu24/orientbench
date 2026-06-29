# PSC Orientation-Selection 反校准 — 机制候选分析

> v2，基于现有 23 cells，无新训练。数字来自 final_matrix_summary / tail_risk_analysis_v2。

## 1. 现象

PSC（rotated_retinanet + PSC angle-coder）在 4 个数据集的 orientation-reliability：

| dataset | PSC NRC-AUC | PSC mAP | median° | masked p90° | masked p95° | masked p99° |
|---|---|---|---|---|---|---|
| DIOR-R (#22) | 0.549 | 0.537 | 0.725 | 3.836 | 5.227 | 10.048 |
| DOTA-v1.0 (#20) | **1.057** | 0.556 | 1.004 | — | — | — |
| FAIR1M-v1.0 (#24) | **1.083** | 0.346 | 1.724 | 5.386 | 6.771 | 10.953 |
| SODA-A (#23) | **1.260** | 0.599 | 1.441 | 5.249 | 7.237 | 16.111 |

> NRC-AUC=1.0 表示 selection score 对 orientation risk 的排序与随机等价；>1 表示**反校准**（高分预测反而朝向更差）。

## 2. 与其它 detector 对比（NRC-AUC，同 dataset）

| dataset | orcnn | lsknet | rtmdet | strip | arsdetr | **PSC** |
|---|---|---|---|---|---|---|
| DIOR-R | 0.521 | 0.529 | 0.427 | 0.506 | 0.999 | **0.549** |
| DOTA-v1.0 | 0.570 | 0.714 | — | 0.717 | — | **1.057** |
| FAIR1M | 0.845 | 0.826 | — | — | — | **1.083** |
| SODA-A | 0.832 | 0.763 | — | — | — | **1.260** |

- PSC 在 **DOTA / FAIR1M / SODA 三处 NRC>1**（唯一系统性反校准的 detector family）。
- DIOR 是例外（PSC 0.549，与同数据集其它 detector 同量级）。

## 3. 是否 “mAP 不弱但 orientation selection 反校准”

- DOTA：mAP 0.556（中等，非崩溃）但 NRC 1.057 → **是**。
- SODA：mAP 0.599（不弱）但 NRC 1.260 → **是，最显著**。
- FAIR1M：mAP 0.346（偏低）+ NRC 1.083 → 部分（mAP 也弱）。
- DIOR：mAP 0.537 + NRC 0.549 → 否（不反校准）。

结论：PSC 在 **mAP 不弱的 DOTA/SODA 上 orientation selection 仍反校准** —— 这是 accuracy 指标看不到的可靠性缺陷，正是 NRC/benchmark 的价值点。

## 4. 机制候选（仅分析，不开实验）

- PSC（Phase-Shifting Coder）把角度编码为相位/周期表示；其 classification confidence（selection score 来源）可能**不随角度回归质量单调**——高置信不代表角度准。
- 反校准在 long-tail/small-object（SODA）更强，提示 angle-coder 在密集小目标的相位混叠。
- DIOR 例外可能与类别/尺度分布有关（需后续分析，非本轮）。

## 5. 建议

- **暂不启动大规模 “只换角度头” 训练**。
- 证据已支持：PSC orientation-selection 反校准是真实、跨数据集、accuracy 独立的现象。
- 建议回到合作者讨论是否启动 **angle-head control experiment**（固定 backbone/检测头，仅替换/对比 angle-coder：PSC vs 直接回归 vs DCL/CSL），以确认机制归因。这是 P1 benchmark 的一个有力 follow-up，但需明确批准与算力预算。
