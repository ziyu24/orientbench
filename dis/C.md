---
round_id: orientbench-c-r020-measurement-validity-20260811
planning_base: 594654a95d50b1f14b87252698911cc3fc583b03
protected_B_blob: c0c2571f3a5c828673b39e6458ceaed5f14c5a6a
evidence_cutoff: 2026-08-11
review_mode: jprs_measurement_validity_dispatch
current_route: ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC
learned_eqs_role: APPENDIX_FAILED_ONLY
receipt3_execution_commit: 594654a95d50b1f14b87252698911cc3fc583b03
receipt3_status: ABNORMAL_EXECUTABLE_AUDIT_FAILURE
receipt3_completion_mode: PROTOCOL_DRIFT
receipt3_scientific_gate: NOT_ADJUDICATED
receipt3_non_reusable: true
receipt3_report: dis/server_reports/orientbench-c-topjournal-feasibility-receipt3-20260811.md
receipt3_report_blob: 498dd8094f713a4a76339890ffd3a9ec45352344
receipt3_archive: dis/sug/orientbench-c-topjournal-feasibility-receipt3-20260811-abnormal-audit.md
receipt3_archive_blob: aeb79060e50aeaa615b365065fc087dc7b9e74cc
design_path: dis/jprs_measurement_validity_gate_design_20260811.md
plan_path: dis/jprs_measurement_validity_dispatch_plan_20260811.md
server_instruction: dis/sug.md
server_report: dis/server_reports/orientbench-c-r020-measurement-validity-20260811.md
code_root: top_journal_v3_reaudit_055/measurement_validity_r020_20260811
runtime_root: outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811
postseal_receipt_root: outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811_postseal_receipt
postseal_receipt_path: outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811_postseal_receipt/postseal_receipt.json
post_server_required_action: C_POSTPULL_ADJUDICATION
server_status: READY_FOR_SERVER_EXECUTION
execution_status: NOT_STARTED
existing_core_measurement_reanalysis_authorized: true
new_protocol_authorized: true
new_experiment_authorized: true
new_target_dataset_outcome_authorized: false
gpu_authorized: false
general_download_authorized: false
installation_authorized: false
training_authorized: false
forward_authorized: false
inference_authorized: false
annotation_root_authorized: false
manuscript_edit_authorized: false
method_experiment_authorized: false
cc_status: COMPLETED_CLOSED
cc_recommendation: 'no'
---

# OrientBench C：receipt3 异常审计闭环与 r020 交接

## 当前结论

receipt3 的 Git 发布机械闭合，但其 validator 在真实 access log、manifest 和 report 生成前只验证 planned tokens，scientific inputs 也未完整进入 frozen manifest。正式裁决因此是：

receipt3_execution: ABNORMAL_EXECUTABLE_AUDIT_FAILURE
completion_mode: PROTOCOL_DRIFT
scientific_gate: NOT_ADJUDICATED
track_m_formal: NOT_EMITTED
reported_track_m: METRIC_REVERSAL_DESCRIPTIVE_UNVERIFIED
reported_gate: FAIL_TO_MEASUREMENT_ONLY_DESCRIPTIVE_UNVERIFIED
non_reusable: true
scientific_failure: false

receipt3 的 round、code、runtime 和 report path 永久消费。其数字、rows、bootstrap、manifest、代码与 gate 不得作为 r020 科学输入；同一 receipt 不得再运行。旧合同已逐内容归档，filter-aware blob 为 aeb79060e50aeaa615b365065fc087dc7b9e74cc。

## r020 唯一 active 任务

r020 状态为 READY_FOR_SERVER_EXECUTION / NOT_STARTED。唯一目标是在 r014/m069 冻结 Core A-F 上执行 CPU-only、双独立实现的 measurement-validity 终门，判定 OBB 长边等价、几何归一化、AR domain 与 scene cluster 是否会实质改变可靠性结论。

正式四态是 PASS_TO_EXTERNAL_CONFIRMATION、FAIL_GENERIC_OR_NULL、INCONCLUSIVE_MIXED、NOT_ADJUDICATED。PASS 只进入未来独立确认，不等于 JPRS/TGRS ready；FAIL 关闭顶刊实验循环并按 JSTARS scope 收口；INCONCLUSIVE 不换 gate 续命。learned EQS 固定 APPENDIX_FAILED_ONLY，S0、r011 与 receipt3 均不能进入 formal gate。

本轮设计与执行合同：

- dis/jprs_measurement_validity_gate_design_20260811.md
- dis/jprs_measurement_validity_dispatch_plan_20260811.md
- dis/sug.md
- 唯一未来报告 dis/server_reports/orientbench-c-r020-measurement-validity-20260811.md
- 唯一 seal 外回执 outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811_postseal_receipt/postseal_receipt.json；它只驱动服务器阶段 normal/abnormal，跨电脑正式科学态必须等 C post-pull 独立复核后另行写入 dis

## 权限与证据边界

已授权 existing Core measurement reanalysis、新 protocol 与该 CPU-only r020 执行。未授权 GPU、一般下载、安装、训练、forward、inference、新 target outcome、annotation root、主稿或 method experiment。唯一网络例外是合同内精确 fd-shifts commit 的一次 HTTPS fetch。

protected B blob 保持 c0c2571f3a5c828673b39e6458ceaed5f14c5a6a；C 只核验 Git blob/diff 元数据，不读取或触碰内容。CC 上轮保持 COMPLETED_CLOSED，cc_recommendation: no；本轮不重复调用 CC。

## 唯一下一步

服务器 HTTPS fast-forward 到发布 r020 合同的提交，只执行 dis/sug.md。服务器最终聊天只允许项目 wrapper 加一句 正常执行完毕 或 异常结束；完整科学 PASS/FAIL/INCONCLUSIVE 都属于正常，技术、provenance、审计或 Git 闭包失败属于异常。

## 决策台账

| 项目 | 当前状态 | 后续 |
|---|---|---|
| receipt1 | ABNORMAL_PREFLIGHT_FAILURE / NOT_ADJUDICATED / non_reusable | 历史 |
| receipt2 | ABNORMAL_MANDATORY_REFERENCE_PROVENANCE_FAILURE / NOT_ADJUDICATED / non_reusable | 历史 |
| receipt3 | ABNORMAL_EXECUTABLE_AUDIT_FAILURE / PROTOCOL_DRIFT / NOT_ADJUDICATED / non_reusable | 只作描述动机 |
| learned EQS | APPENDIX_FAILED_ONLY | 永不复活为 gate |
| r020 | READY_FOR_SERVER_EXECUTION / NOT_STARTED | 服务器执行 active dis/sug.md |
| route | ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC | PASS 后另行外部确认 |
| CC | COMPLETED_CLOSED / no | 保持关闭 |
