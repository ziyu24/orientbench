---
schema_version: 2
dispatch_id: orientbench-b-r024-dota-external-replication-20260813
plan_id: b-r024-dota-external-replication-20260813
initiator: B
plan_path: dis/plans/B/b-r024-dota-external-replication-20260813/sug.md
plan_commit_sha: 57e4f808f0344a2b6d9dc204196d4c9c3eb7c234
plan_blob_oid: PENDING_DISCLOSED
plan_sha256: PENDING_DISCLOSED
dispatch_commit_sha: 57e4f808f0344a2b6d9dc204196d4c9c3eb7c234
server_report_path: dis/server_reports/orientbench-b-r024-dota-external-replication-20260813/SERVER_EXECUTION_REPORT.md
execution_status: incomplete
completion_mode: NOT_ADJUDICATED_PROBE_PROVENANCE
starting_commit: 9cbe1037151e8bc90b01832cabb1fd7544a6f036
ending_commit: PENDING_RESULT_COMMIT
---

# 服务器执行报告

## 摘要

r024 在预注册的探针 P 阶段触发硬性 kill：不存在可跨六个 Core unit 使用的唯一 `linear_source_frozen` 函数。依计划停止为 `NOT_ADJUDICATED_PROBE_PROVENANCE`；未读取 DOTA GT、未做匹配、未做 AP parity、未启动 inference/GPU 或训练，未产生 DOTA 科学数字。

## Dispatch、授权与资源

- 用户交付 dispatch/path/commit 与当前 checkout `57e4f808f0344a2b6d9dc204196d4c9c3eb7c234` 一致。
- `pth_data/readme.md` 已按项目规则先行读取；本地 valid DOTA baseline 清单包含 Oriented R-CNN 的 0.7061 和 RTMDet 条目。
- STARTED 单文件 commit：`9cbe1037151e8bc90b01832cabb1fd7544a6f036`，已 HTTPS push。
- 实际资源仅 CPU 的 Core r014 features/scores 读取及最小二乘核验；GPU=0、训练=0、DOTA 标注读取=0。

## 探针 P 预注册核验

P1：在 r014 protocol/source 中只找到模型训练语义（`StandardScaler + LinearRegression`），未找到可直接应用于新 DOTA raw predictions 的单一显式全局系数工件，因此转入 P2。

P2：对每个 unit 的全表 `score_ar_size_linear` 用预注册候选矩阵 `[1, logit_score, log_pred_ar, half_log_pred_area]` 最小二乘重构。每 unit 的最大绝对残差均 ≤ `5.6e-16`，证明该候选在各自 unit 内可精确复构；但系数不一致，违反计划的跨六 unit 成对差 ≤`1e-6` 条件。

| units | intercept | logit_score | log_pred_ar | half_log_pred_area |
|---|---:|---:|---:|---:|
| A/B/C (DIOR-R) | -0.23342829 | 0.00830977 | 0.02817757 | 0.00753967 |
| D (FAIR1M) | -0.26525345 | 0.01355104 | 0.00337013 | 0.02027136 |
| E/F (SODA-A) | -0.21289442 | 0.01466760 | -0.01161673 | 0.00892121 |

该差异远超 `1e-6`，所以不能选择任一组、平均系数或重新拟合来构造 DOTA probe；这些均为计划禁止的替代探针。

## Gate、停止与后续

触发 kill condition：`线性探针恢复失败（P 步骤两分支均不成立）`。完成映射为 `execution_status=incomplete`。本报告不产生 REPLICATED / NOT_REPLICATED / INCONCLUSIVE_EXTERNAL 任何 DOTA 科学态。

要继续 DOTA 外部研究，需要 B/监督端发布新的预注册计划，明确允许的、可跨域定义的线性探针；服务器不会自行改写该定义。
