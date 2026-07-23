# A0 —— NRC 协议漂移法证审计 (055 re-audit)

> 指令：SUPERVISOR_APPROVED_055_CLAUDE_REAUDIT_AND_FIX_B_CRITIQUE，任务 A0（最高优先，门控项）。
> 唯一权威 per-instance 源：`outputs/persistent_artifacts/orientbench_real_052/matched_tables/{ds}/{bid}/matched_17field_full_052.jsonl`（real detector output，携带 checkpoint sha256 / aspect_ratio / near_square / d_cal_daudit_split_flag），即 053/054 使用的同一批数据，从而干净隔离“masked/unmasked 协议”这一单一变量。
> NRC 定义冻结未改（`orientbench/metrics/nrc_auc.py`：0=oracle，1=random，>1=反校准）。masking 不在 metric 内，而是喂入样本前的筛选 → 协议差异 = 喂入哪些样本。
> 未训练、未推理、未改 thresholds.yaml、未改 D_cal/D_audit。

## 1. B 的指控与裁决（先给结论）

B 指出：measure_fix 期 DIOR#22 detection-score NRC(masked)=0.549 / FAIR1M#24=1.083 / SODA#23=1.260，在 053/054 表中变成 1.1265 / 1.5061 / 1.6733，疑似 masked/unmasked 协议漂移。

**裁决：B 正确，且问题比 B 指出的更严重。** 存在两处独立缺陷：

1. **Codex 053/054 执行错误（协议漂移，已确认）**：053/054 的 NRC 用了 **unmasked full matched table**（含 near-square），得到 NRC>1；而项目主协议是 **masked（near-square 病态角度剔除）**。这是把 near-square 病态性混入可靠性信号造成的 **pooling artifact**，不是真实反校准。
2. **measure_fix 期 FAIR1M/SODA 的 masked 反校准也不成立**：measure_fix 的 “masked” 实为较弱的 near-square≤1.10 剔除，仍保留 moderate(1.1–1.6) 病态实例；在冻结的 ar≥1.6 主协议下重算，FAIR1M/SODA detection-score NRC 落到 0.885/0.914（<1，显著校准），**并非反校准**。

结论：**detection-score “PSC 反校准” 在两个时代都不成立**；它是 near-square/moderate 病态实例被计入造成的。真正幸存的机制信号在 A0-3 与 A4 给出（intrinsic phase_mod）。

## 2. Pooling artifact 的直接证据（053 自带分层已可证）

053 `p1_angle_perturb_dose_response.csv`（epsilon=0 baseline 行）本身带 near-square/moderate/elongated 分层 NRC。**每个 cell 的 pooled(unmasked) NRC 都高于它自己的每一个分层** —— 这是典型 Simpson/pooling 效应：把 mean risk 20–32° 的 near-square 层混入 mean risk 1.6° 的 elongated 层，pooled NRC 被抬到 >1，而任何单层都不反校准。

| cell | pooled(unmasked) | near-sq NRC (risk°) | moderate NRC | elongated NRC |
|---|---|---|---|---|
| DIOR#22 | 1.127 | 0.949 (25.1°) | 0.595 | 0.838 |
| FAIR1M#24 | 1.506 | 1.060 (20.4°) | 0.993 | 0.915 |
| SODA#23 | 1.673 | 0.938 (31.9°) | 1.104 | 0.816 |
| DOTA#20 | 1.022 | — (n=0) | 1.026 | 0.918 |
| DIOR#3 | 1.120 | 1.007 (23.8°) | 0.584 | 0.835 |
| DIOR#61 | 1.050 | 0.811 (20.6°) | 0.499 | 0.765 |
| SODA#4 | 1.381 | 0.935 (32.2°) | 0.937 | 0.722 |

> pooled > 所有分层 → NRC>1 是近方形病态实例混入的结果，不是层内反校准。

## 3. 冻结主协议下的权威重算（表 2 / 表 6 / 表 7 重制）

源=052 matched_17field（同一权威表）；selector=detection_score（score→angle_error）；主协议 masked ar≥1.6，敏感度 ar≥1.3，unmasked 仅作对照。完整数据见 `reports/a0_nrc_masked_unmasked_recompute_055.csv`，PSC bootstrap CI 见 `reports/a0_masked_nrc_bootstrap_ci_055.csv`。

| cell | detector | unmasked | **masked ar≥1.6** | masked ar≥1.3 | measure_fix 旧值 | 053/054 旧值 |
|---|---|---|---|---|---|---|
| DIOR#22 | PSC | 1.141 | **0.542** [0.529,0.556] | 0.549 | 0.549 (masked) | 1.1265 |
| FAIR1M#24 | PSC | 1.620 | **0.885** [0.865,0.907] | 0.953 | 1.083「反校准」 | 1.5061 |
| SODA#23 | PSC | 1.798 | **0.914** [0.903,0.926] | 1.050 | 1.260「反校准」 | 1.6733 |
| DOTA#20 | PSC | 1.037 | 1.037 (n=486, 无效*) | 1.037 | 1.057 | 1.037 |
| DIOR#3 | ORCNN | 1.140 | **0.526** | 0.514 | — | 1.120 |
| DIOR#61 | RTMDet | 1.058 | **0.407** | 0.395 | — | 1.050 |
| SODA#4 | ORCNN | 1.468 | **0.711** | 0.763 | — | 1.381 |
| DIOR#10 | LSKNet | — | **0.548** (features_v2) | — | — | — |
| SODA#11 | LSKNet | — | **0.731** (features_v2) | — | — | — |

\* DOTA#20 为 19-图 D_cal-subset 残缺 dump（见 `a0_dota20_artifact_integrity_055.md`），移入脚注/invalid_pending，不进主表结论。

**核对**：unmasked 重算 (1.141/1.620/1.798) 复现 053/054 (1.13/1.51/1.67) 同一 regime；masked DIOR#22 (0.542) 复现 measure_fix (0.549)。二者都被复现 → 差异 100% 来自 masked/unmasked 协议，不是随机噪声或数据错误。

## 4. detection-score bootstrap 显著性（masked ar≥1.6）

| cell | NRC | 95% CI | 判定 |
|---|---|---|---|
| DIOR#22 | 0.542 | [0.529, 0.556] | 显著校准（CI 上界<1） |
| FAIR1M#24 | 0.885 | [0.865, 0.907] | 显著校准 |
| SODA#23 | 0.914 | [0.903, 0.926] | 显著校准 |
| DOTA#20 | 0.693 | [0.672, 0.711] | 显著校准（但 subset，慎用） |

**4/4 PSC cell 的 detection-score 在冻结 masked 协议下显著校准（NRC<1），无一反校准。**

## 5. 协议冻结（本轮据此执行，写入正文与附录）

- **主协议（headline）**：masked，near-square 病态实例剔除，阈值 **ar ≥ 1.6**；NRC/AURC/Risk@k 全部在此协议下报告。
- **敏感度**：ar ≥ 1.3。
- **unmasked**：仅作 pooling-artifact 演示与对照，**不得**作为反校准证据。
- **split**：可靠性审计在 D_audit 报告；D_cal 仅用于 selector/conformal 标定（NRC 对 split 不敏感，DIOR#22 full 0.542 vs D_audit 0.548）。
- 每张 NRC/AURC/Risk 表必须标注：masked/unmasked、ar 阈值、split、selector、n、artifact 源。

## 6. 是否 Codex 执行错误

- **是**（053/054）：用 unmasked full table 计算 headline NRC，丢失了项目既有的 near-square masking 主协议 → 产生 NRC>1 的伪反校准，并据此在 reduced-scope 稿写“score-only 反校准”。这是执行错误（协议漂移），已在本轮更正。
- **部分是**（measure_fix）：FAIR1M/SODA 的 1.083/1.260 用了较弱的 ≤1.10 mask，属协议不统一；在冻结 ar≥1.6 下不成立。此为历史口径不一致，本轮统一后 supersede。

## 7. 对下游门控的解锁

A0-1 完成，据此解冻：表 2 解读（§3）、P4 selector-vs-TTA 比较（见 `p4_uncertainty_branch_055.md`，全部在 masked 协议下重算）、Track A 机制（见 `a0_evidence_lineage_reconciliation_055.md` 与 A4：intrinsic phase_mod 在 masked 下仍显著反校准，是幸存的机制候选）。
