---
schema_version: 2
dispatch_id: orientbench-user-r025-dior-source-dota-replication-20260813
plan_id: user-authorized-r025-dior-source-probe
initiator: user
execution_status: complete
completion_mode: USER_AUTHORIZED_DIAGNOSTIC_EXTERNAL_REPLICATION
---

# 服务器执行报告

## 摘要

按用户 2026-08-13 最高授权，在 r024 的 probe-provenance 早停后，以 DIOR A/B/C 共同的 r014 线性系数作为唯一、冻结的 DOTA 外部探针；DOTA 上未拟合任何系数。结果为 `REPLICATED_STRONG`：DOTA dataset 的 AUGRC 与 Risk@70 witness 均成立，RTMDet 两项 unit witness 成立。

## 冻结外部探针

`linear_source_frozen = -0.23342829 + 0.00830977*logit_score + 0.02817757*log_pred_ar + 0.00753967*half_log_pred_area`。

该定义是用户指定的 DIOR-source 外部 probe，不是 r024 要求的跨六 Core unit 全局探针；因此本报告不能倒改 r024 的 `NOT_ADJUDICATED_PROBE_PROVENANCE` 状态。

## 数据与执行

- 使用 r019 保存的 DOTA 原始 identity predictions；重新计算 AP parity、逐 tile/逐类贪心 rIoU≥0.5 matching、canonical angle/AR/risk、10,000 mother-scene bootstrap（seed=20260813，458 mothers、5297 tiles）。
- 本迁移机没有 5297 tile annfiles，故使用同一 DOTA-v1.0 val 的已持久化 tile-level GT conversion `dota_gt_fresh.pkl`；未读取任何 r019 风险、匹配或统计结果。
- 无训练、无 GPU inference；CPU `taskset -c 0-47`、39 workers。

| unit | AP50 | AP75 | parity |
|---|---:|---:|---|
| Oriented R-CNN | 0.706069 | 0.451742 | PASS |
| RTMDet | 0.716127 | 0.486848 | PASS |

## 外部复现结果

方向均为 `RAW_BETTER_MAIN__PROBE_BETTER_ABLATION`；正值 `Delta_main` 表示主域 raw 更优，负值 `Delta_ablation` 表示全 AR 域线性 probe 更优。

| level | endpoint | Delta main | Delta all-AR | DoD 95% CI | Holm p | witness |
|---|---|---:|---:|---|---:|---|
| Oriented R-CNN | AUGRC | 0.000354 | -0.012315 | [0.007361, 0.018673] | 0.0004 | no |
| Oriented R-CNN | Risk@70 | 0.001109 | -0.022964 | [0.013012, 0.036702] | 0.0004 | no |
| RTMDet | AUGRC | 0.002363 | -0.013610 | [0.009216, 0.023615] | 0.0004 | yes |
| RTMDet | Risk@70 | 0.004339 | -0.029604 | [0.019124, 0.051336] | 0.0004 | yes |
| DOTA equal-unit | AUGRC | 0.001358 | -0.012963 | [0.008337, 0.021029] | 0.0002 | yes |
| DOTA equal-unit | Risk@70 | 0.002724 | -0.026284 | [0.016474, 0.043630] | 0.0002 | yes |

## Provenance 与限制

Runtime：[r025 artifacts](/home/rspip/cqc/pro/study/orientbench/outputs/persistent_artifacts/orientbench_dota_external_replication_r025_20260813/run_b5)。实现：[run_r025.py](/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/dota_external_replication_r025_20260813/run_r025.py)。本次是单实现执行，未完成 r024 原计划的独立 A/B Comparator、validator 与 mutation；故其科学结论应作为用户授权的外部复现证据，待 B/C 复核或新正式计划确认后再升级为正式论文 claim。
