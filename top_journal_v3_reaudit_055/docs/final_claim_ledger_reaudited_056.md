# Final Claim Ledger（reaudited）

> 冻结 masked 口径 ar≥1.6，provenance-clean 真实匹配表。分：allowed / qualified / forbidden / superseded / future work。

## allowed（有真实证据支撑）
| claim | 证据 |
|---|---|
| 朝向可靠性测量协议（canonical 角度误差 + masked 口径 + NRC/AURC/风险覆盖） | 第 3–4 节 |
| P1 precise-pass：mAP@0.5 对朝向的（不）敏感性受 ar 与 IoU 阈值门控 | 表 3/3b，约束扰动 mAP@0.5 Δ=0、朝向误差 +~30° |
| finite-sample conformal orientation risk control（严格预算下带弃权、带 Hoeffding 界的尾部保证） | 表 4–6 |
| aspect-ratio cliff（测量层核心，保留） | 表 3b + 理论 IoU(δθ;ar) 曲线 |
| phase_mod mechanism candidate（masked 下 3/3 PSC cell 显著反校准） | 表 8，CI 下界>1 |
| 打分菜单：几何选择器在固定保证下一致最高覆盖，含 θ→2θ 圆统计 TTA 基线 | 表 7/7b，配对 bootstrap geo 6/6 优于 det、5/6 优于 TTA |

## qualified（须限定表述）
| claim | 限定 |
|---|---|
| 几何感知选择器 | reliability-aware selector **candidate**（source-supervised 训练 + target GT-free 推理），非 validated deployable method |
| NRC 提供 mAP 之外信号 | 仅“在可比设置内提供 reliability signal”，**不严格独立于 mAP** |
| TTA circular variance | GT-free 后备打分，不稳定（5/6 弱于几何选择器） |
| within-cell 均值保形 | 近似保证（无界损失）；尾部版才有干净有限样本界 |
| 跨数据集迁移 | 无严格迁移保证；ar 分层部分缓解 |

## forbidden（禁止主张）
- NRC 严格独立于 mAP。
- full benchmark complete / all datasets covered / 9-detector matrix complete。
- P3 final method success / deployable method complete。
- PSC angle head proven broken（只可写 mechanism candidate）。
- DOTA #20 validation（invalid_pending）。
- downstream utility proven。
- detection-score PSC 反校准（unmasked headline，作废）。
- CVPR / ICCV / TPAMI ready / top venue ready。
- full project complete。
- DOTA SOTA / 追公开 mAP。

## superseded（作废，附原因）
| 旧 claim | 原因 |
|---|---|
| unmasked score-only NRC 1.1265/1.5061/1.6733 → 反校准 | near-square pooling artifact；masked ar≥1.6 → 0.542/0.885/0.914 显著校准 |
| FAIR1M 1.083 / SODA 1.260「masked 反校准」 | 弱 mask（≤1.10）；ar≥1.6 下降到 0.885/0.914 |
| 均匀 30° 扰动“解耦” | 破坏 rIoU>0.5，mAP 同步变动；由约束扰动替代 |
| DOTA#20 P1 结果 / mAP 0.013 | 19 图 D_cal 子集 scope |

## future work
- 冻结 masked 口径 + provenance-clean 下重算更多 cell。
- 受控 angle-coder 实验（phase_mod 机制候选 → 机制证据）。
- 角度主导的下游任务（heading 选择性预测）。
- 更紧的有限样本 / 分布迁移保证（CRC 变体、Mondrian 理论）。
- DOTA full-val provenance dump。
