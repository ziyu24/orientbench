# A0 —— Supersedes Memo (055)

> 权威重算源：052 matched_17field（checkpoint sha256 provenance）。冻结主协议：masked ar≥1.6。
> 数据：`reports/a0_nrc_masked_unmasked_recompute_055.csv`、`reports/a0_masked_nrc_bootstrap_ci_055.csv`、`reports/a0_evidence_lineage_reconciliation_055.csv`。

## 1. RETAINED（保留）
- **DIOR#22 detection-score masked NRC ≈ 0.55**（0.542 [0.529,0.556]，复现 measure_fix 0.549）。
- **intrinsic phase_mod 反校准（masked 幸存）**：DIOR#22 1.129 [1.098,1.160]、FAIR1M#24 1.101 [1.077,1.121]、SODA#23 1.090 [1.081,1.100]，3/3 full-val PSC cell CI 下界>1 → 显著。这是本项目**唯一在冻结 masked 协议下幸存的反校准信号**，作为 Track A angle-coder 机制候选（非“已证明反校准”）。
- **near-square 病态性 / aspect-ratio cliff**：真实，回归测量层（A3）。
- **053/054 unmasked pooled NRC 数值本身**（1.13/1.51/1.67）：作为“pooling artifact 演示”保留，但改标注为 unmasked，非反校准证据。

## 2. SUPERSEDED（作废，附原因）
| 旧 claim / 数字 | 作废原因 | 是否 Codex 执行错误 |
|---|---|---|
| 053/054：score-only NRC 1.1265/1.5061/1.6733 → PSC「反校准」 | unmasked full table，near-square pooling artifact；masked ar≥1.6 得 0.542/0.885/0.914（<1 显著校准） | **是**（协议漂移） |
| measure_fix：FAIR1M#24=1.083、SODA#23=1.260「masked 反校准显著」 | “masked”实为 ≤1.10 弱剔除，仍含 moderate 病态；ar≥1.6 下降到 0.885/0.914 | 部分（历史口径不统一） |
| “PSC detection-score 系统性反校准” | detection-score 在 masked 下 4/4 cell 显著校准 | 是 |
| DOTA#20 P1 结果（486 matched, mAP 0.0132） | 19-图 D_cal subset scope，见 a0_dota20 | 是 |
| 053 P1 均匀 30° 扰动“解耦” | 破坏 rIoU>0.5，mAP 同步变动，非有效解耦；见 A2 | 是（实验设计错误） |

## 3. PENDING_RECOMPUTE / OUT_OF_SCOPE
- non-PSC leave-* deployable 8/9（047）、deployable hardening 12/12（040）、Route-C TTA：均为 selector-gain 分析，不是 NRC-protocol 结论，A0 不直接推翻，但须统一采用 masked 协议标签，且 deployable 一律降为 candidate（A4/A6 处理）。

## 4. 一句话
detection-score 的“PSC 反校准”在两个时代都被 near-square 病态实例污染，冻结 masked 协议下不成立并作废；真正幸存并被本轮强化的，是 **intrinsic phase_mod 在 well-posed 实例上仍显著反校准** 的 angle-coder 机制候选。
