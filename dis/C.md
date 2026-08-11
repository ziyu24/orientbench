---
round_id: orientbench-c-topjournal-feasibility-receipt3-20260811
retry_of: orientbench-c-topjournal-feasibility-receipt2-20260810
planning_base: 3a4e86cf435af8b29e63b1668af92a1add7c6dbf
control_base: bc27506f7d7c0e47c4d67b202b9157bd4016a87a
housekeeping_commit: 2a70303e9d74313a15b71e1767b0b6ecdc05d2cc
receipt2_report_publication_commit: a2da27559dc6eb005f02efb9b3b34584ebed57b8
dispatch_base: 35358b5fef838b178aff0e16470ebe0117cab687
source_execution_commit: cdf764c5a974030739a9992079bedb8b970fb2a7
source_execution_status: ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809
source_numbers_status: DESCRIPTIVE_UNVERIFIED
source_reported_gate: FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED
scientific_data_cutoff: a9067fb16d2bbd747dfe69789ac33a5911eb15fe
protected_B_blob: c0c2571f3a5c828673b39e6458ceaed5f14c5a6a
receipt1_status: ABNORMAL_PREFLIGHT_FAILURE
receipt1_scientific_gate: NOT_ADJUDICATED
receipt1_reusable: false
receipt2_status: ABNORMAL_MANDATORY_REFERENCE_PROVENANCE_FAILURE
receipt2_scientific_gate: NOT_ADJUDICATED
receipt2_reusable: false
review_mode: receipt3_pinned_reference_retry
evidence_cutoff: 2026-08-11
receipt_status: READY_FOR_SERVER_FEASIBILITY_RECEIPT
receipt_execution_status: NOT_STARTED
receipt_only: true
receipt_only_retry: true
pinned_reference_fetch_authorized: true
pinned_reference_fetch_max_attempts: 3
pinned_reference_remote: https://github.com/IML-DKFZ/fd-shifts.git
pinned_reference_commit: c4467aec134e99691359da209f811d91283fc1e3
reference_root: outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt3_20260811/references/fd-shifts
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
method_experiment_authorized: false
new_experiment_authorized: false
new_protocol_authorized: false
cc_recommendation: 'no'
cc_status: COMPLETED_CLOSED
---

# OrientBench C：receipt2 reference 异常闭环与 receipt3 交接

## 结论

receipt1 保持 `ABNORMAL_PREFLIGHT_FAILURE / NOT_ADJUDICATED / non_reusable`；Track M、Track D 均未运行。receipt2 已正式终止为：

```text
receipt_execution: ABNORMAL_MANDATORY_REFERENCE_PROVENANCE_FAILURE
scientific_gate: NOT_ADJUDICATED
track_m_state: NOT_EMITTED_NOT_RUN
track_d_state: NOT_RUN
non_reusable: true
```

receipt2 的强制 preflight 已通过，但允许根内没有 pinned `IML-DKFZ/fd-shifts@c4467aec134e99691359da209f811d91283fc1e3` Git object/checkout；当轮下载权限为 false，因此 mandatory reference provenance 无法闭合并异常停止。这不是科学失败，也不是 `INSUFFICIENT_ASSETS`；Track M 为 `NOT_EMITTED_NOT_RUN`，Track D 与 joint gate 均未运行。

receipt2 唯一报告为 `dis/server_reports/orientbench-c-topjournal-feasibility-receipt2-20260810.md`，blob `8e1407d90f5a7247816c457eddcb60a704291951`，由 `a2da27559dc6eb005f02efb9b3b34584ebed57b8` 发布；该 SHA 是 report publication commit，不是 receipt2 正常执行提交。receipt2 active 合同已归档为 `dis/sug/orientbench-c-topjournal-feasibility-receipt2-20260810-abnormal-reference.md`，filter-aware blob `25ee36ec83db92364134a66bb44b349ac5f34cf9`。

当前 active 状态为 receipt3 `orientbench-c-topjournal-feasibility-receipt3-20260811`：`READY_FOR_SERVER_FEASIBILITY_RECEIPT / NOT_STARTED`。它是 receipt-only retry，唯一新增权限是最多三次从精确 HTTPS remote 获取精确 pinned commit 到新 runtime reference 目录。一般 download 与全部实验、安装、推理和改稿权限仍为 false。

## 证据锁

- dispatch base：`35358b5fef838b178aff0e16470ebe0117cab687`。
- receipt2 report publication commit：`a2da27559dc6eb005f02efb9b3b34584ebed57b8`。
- receipt control base：`bc27506f7d7c0e47c4d67b202b9157bd4016a87a`。
- source execution：`cdf764c5a974030739a9992079bedb8b970fb2a7`。
- scientific data cutoff：`a9067fb16d2bbd747dfe69789ac33a5911eb15fe`。
- protected B blob：`c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`；C 只核验 Git blob/diff 元数据，不读取或触碰内容。
- receipt1 report/archive：`4fe331a6a683313150a4fb21cbabd432ffde0f6b` / `11553a92b05b692a14bf9c4f21898a5c9e10d144`。
- receipt2 report/archive：`8e1407d90f5a7247816c457eddcb60a704291951` / `25ee36ec83db92364134a66bb44b349ac5f34cf9`。
- source runtime：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809`，全树严格只读，aggregate SHA-256 `2e9f7eb60b7de427b24faa8c91b0ef2017864d99cbc923b04bfe70b500085b43`。
- receipt3 code root：`top_journal_v3_reaudit_055/feasibility_receipt3_20260811`。
- receipt3 runtime：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt3_20260811`。
- receipt3 reference root：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt3_20260811/references/fd-shifts`。
- receipt3 唯一未来报告：`dis/server_reports/orientbench-c-topjournal-feasibility-receipt3-20260811.md`；当前不存在。

## 科学状态与新增权限边界

源执行仍永久为 `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`；源数字仍为 `DESCRIPTIVE_UNVERIFIED`；reported gate 仍为 `FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED`。当前路线保持 `ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC`。

receipt3 的 §5.1/§5.2/§5.4-§8、Track M 五态、Track D 谓词与 precedence、joint gate、cohort、公式、seed `20260809`、replicate `0..9999`、CI report-only、validator 和四项 mutation 与 receipt2 归档逐字节一致。仅 §5.3 增加精确 pinned reference 的窄获取与无安装 AST adapter 规则。

`pinned_reference_fetch_authorized: true` 只允许 HTTPS `git clone/fetch` 精确 remote、精确 commit、最多三次、精确新 reference root。禁止镜像、替代 commit、submodule、LFS、hooks、setup、pip/conda、依赖安装或其它下载。失败必须异常结束且科学 gate 不裁定，不得换源或把它写成缺资产科学状态。

## 唯一下一步与禁止项

唯一下一步是服务器执行 receipt3。除窄 pinned reference fetch 外，一律禁止新实验、`r020`、rescue、gate substitution、GPU、一般下载、安装、训练、forward、推理、新 target outcome、annotation 内容读取、target-label tuning 与改稿。不得调用 CC；上轮 CC 保持 `COMPLETED_CLOSED`。

## 决策台账

| 项目 | 当前状态 | 下一项允许动作 |
|---|---|---|
| source execution/numbers | `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809` / `DESCRIPTIVE_UNVERIFIED` | 永久保守 |
| receipt1 | `ABNORMAL_PREFLIGHT_FAILURE / NOT_ADJUDICATED / non_reusable` | 历史证据 |
| receipt2 | `ABNORMAL_MANDATORY_REFERENCE_PROVENANCE_FAILURE / NOT_ADJUDICATED / non_reusable` | 历史证据，不复用路径 |
| receipt3 | `READY_FOR_SERVER_FEASIBILITY_RECEIPT / NOT_STARTED` | 执行 active `dis/sug.md` |
| reference fetch | 精确 remote/commit/root，最多三次 | 仅 §5.3 窄授权 |
| route | `ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC` | 不新增科学权限 |
| CC | `COMPLETED_CLOSED`；`cc_recommendation: no` | 用户重授权前保持关闭 |
