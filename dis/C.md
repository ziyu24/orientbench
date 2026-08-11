---
round_id: orientbench-c-topjournal-feasibility-receipt2-20260810
retry_of: orientbench-c-topjournal-feasibility-receipt-20260809
planning_base: 3a4e86cf435af8b29e63b1668af92a1add7c6dbf
control_base: bc27506f7d7c0e47c4d67b202b9157bd4016a87a
housekeeping_commit: 2a70303e9d74313a15b71e1767b0b6ecdc05d2cc
dispatch_base: 2a70303e9d74313a15b71e1767b0b6ecdc05d2cc
source_execution_commit: cdf764c5a974030739a9992079bedb8b970fb2a7
source_execution_status: ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809
source_numbers_status: DESCRIPTIVE_UNVERIFIED
source_reported_gate: FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED
scientific_data_cutoff: a9067fb16d2bbd747dfe69789ac33a5911eb15fe
protected_B_blob: c0c2571f3a5c828673b39e6458ceaed5f14c5a6a
previous_receipt_status: ABNORMAL_PREFLIGHT_FAILURE
previous_receipt_scientific_gate: NOT_ADJUDICATED
previous_receipt_reusable: false
review_mode: receipt2_mechanical_retry_after_abnormal_preflight
evidence_cutoff: 2026-08-10
receipt_status: READY_FOR_SERVER_FEASIBILITY_RECEIPT
receipt_execution_status: NOT_STARTED
receipt_only_retry: true
current_route: ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC
tgrs_status: CONDITIONAL_ON_FUTURE_METHOD_UPGRADE
gpu_authorized: false
download_authorized: false
installation_authorized: false
training_authorized: false
forward_authorized: false
inference_authorized: false
new_target_outcome_authorized: false
annotation_content_authorized: false
manuscript_edit_authorized: false
cc_recommendation: 'no'
cc_status: COMPLETED_CLOSED
---

# OrientBench C：receipt1 异常闭环与 receipt2 机械重试交接

## 结论

receipt1 `orientbench-c-topjournal-feasibility-receipt-20260809` 已终止为：

```text
receipt_execution: ABNORMAL_PREFLIGHT_FAILURE
scientific_gate: NOT_ADJUDICATED
track_m_state: NOT_EMITTED / NOT_RUN
track_d_state: NOT_RUN
non_reusable: true
```

它不是科学失败，也不改变源 feasibility 执行的科学状态。失败原因仅是启动前既有 dirty tree 与 source runtime 对执行用户可写；Track M、Track D、bootstrap、validator、mutation 和 joint gate 均未运行。旧 round、code/runtime/report 路径已永久消费，不能清理后复用。

用户随后在 receipt 外单独授权 housekeeping。提交 `2a70303e9d74313a15b71e1767b0b6ecdc05d2cc` 已发布旧异常报告和迁移记录，并把 source runtime 改为只读；内容树聚合 SHA-256 前后均为 `2e9f7eb60b7de427b24faa8c91b0ef2017864d99cbc923b04bfe70b500085b43`。housekeeping 不追溯修复 receipt1，不产生科学结果，也不增加权限。

当前 active 状态是 receipt2 `orientbench-c-topjournal-feasibility-receipt2-20260810`：`READY_FOR_SERVER_FEASIBILITY_RECEIPT / NOT_STARTED`。它只是相同科学规格的机械重试，唯一下一步是服务器按 active `dis/sug.md` 执行 receipt2。

## 证据锁

- dispatch/housekeeping base：`2a70303e9d74313a15b71e1767b0b6ecdc05d2cc`。
- receipt control base：`bc27506f7d7c0e47c4d67b202b9157bd4016a87a`。
- source execution：`cdf764c5a974030739a9992079bedb8b970fb2a7`。
- scientific data cutoff：`a9067fb16d2bbd747dfe69789ac33a5911eb15fe`。
- protected B blob：`c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`；C 只核验 Git blob/diff 元数据，不读取或触碰内容。
- receipt1 report：`dis/server_reports/orientbench-c-topjournal-feasibility-receipt-20260809.md`，blob `4fe331a6a683313150a4fb21cbabd432ffde0f6b`。
- receipt1 canonical contract archive：`dis/sug/orientbench-c-topjournal-feasibility-receipt-20260809-abnormal-preflight.md`，filter-aware blob `11553a92b05b692a14bf9c4f21898a5c9e10d144`。
- active manuscript：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`；receipt2 不改稿。
- source runtime：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809`，全树严格只读。
- receipt2 code root：`top_journal_v3_reaudit_055/feasibility_receipt2_20260810`。
- receipt2 runtime：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt2_20260810`。
- receipt2 唯一未来报告：`dis/server_reports/orientbench-c-topjournal-feasibility-receipt2-20260810.md`；当前不存在。

## 科学状态不变

源执行仍永久为 `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`；源数字仍为 `DESCRIPTIVE_UNVERIFIED`；其所报 gate 仍为 `FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED`，不得当作已验证科学裁决或论文数字。当前路线保持 `ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC`，TGRS 仍只可能取决于未来另行批准的方法升级。

receipt2 的 Track M 五态、Track D 谓词与 precedence、joint gate、cohort、公式、seed `20260809`、replicate `0..9999`、validator 和四项 mutation 与 receipt1 归档逐字节一致。科学负结果可正常完成 receipt；preflight 或审计闭环失败则执行异常，两条轴不得混写。

## 唯一下一步与禁止项

唯一下一步是 receipt2 receipt-only validation。服务器必须先完成 HTTPS/clean-tree/housekeeping ancestry、receipt1 report/archive、source-runtime 全树只读与聚合 SHA、新路径不存在等 preflight，再执行不变的科学 receipt。

一律禁止新实验、`r020`、rescue、gate substitution、GPU、下载、安装、训练、forward、推理、新 target outcome、候选 annotation 内容读取、用 target label 调参和改稿。不得重复调用 CC；上轮 CC 保持 `COMPLETED_CLOSED`，不是 receipt2 的执行者或最终裁决者。

## 决策台账

| 项目 | 当前状态 | 下一项允许动作 |
|---|---|---|
| source feasibility execution | `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809` | 永久保留异常 |
| source numbers / gate | `DESCRIPTIVE_UNVERIFIED` / `FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED` | receipt2 独立重算前不得消费 |
| receipt1 | `ABNORMAL_PREFLIGHT_FAILURE` / `NOT_ADJUDICATED` / `non_reusable` | 只作历史证据，不重跑 |
| receipt2 | `READY_FOR_SERVER_FEASIBILITY_RECEIPT` / `NOT_STARTED` | 服务器执行 active `dis/sug.md` |
| route | `ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC` | 不新增实验或改稿 |
| CC | `COMPLETED_CLOSED`；`cc_recommendation: no` | 用户明确重授权前保持关闭 |
