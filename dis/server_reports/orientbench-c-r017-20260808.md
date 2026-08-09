instruction_fulfillment: ALL_REQUIRED_PHASES_COMPLETED
execution_completion: FULL_COMPLETION
round_verdict: PASS_STATIC_RECEIPT_R017
r016_historical_acceptance: PROTOCOL_DRIFT_R016
r016_underlying_failure: FAIL_AUDIT_IMPLEMENTATION_R016
numeric_acceptance: EXPLORATORY_CORE_SUPPORT_R015
last_completed_phase: C_manifest_validator_commit_push
executed_required_phases: [A_static_numeric_gate_receipt, B_schema_implementation_manuscript_index, C_exact_input_manifest_resource_declaration]
early_stop_trigger: NONE
early_stop_scientific_meaning: NOT_APPLICABLE
unrun_required_phases: []
all_required_work_completed: true
push_status: PUSHED

# r017 静态收据与证据索引闭合报告

## 结果

r017 完成全部静态阶段，validator token 为 `VALID_STATIC_RECEIPT_R017`。本轮没有重跑 bootstrap，没有训练、推理、selector refit、新 target score 或 runtime 输出。r016 的历史验收保持 `PROTOCOL_DRIFT_R016 / FAIL_AUDIT_IMPLEMENTATION_R016`；r015 数值可接受为高置信探索性证据 `EXPLORATORY_CORE_SUPPORT_R015`，不能升级为 confirmatory/deployable 结论。

## 静态数值和 gate 收据

r015 bootstrap 表恰好 9,000 行，合法域为六个 unit 加三个 dataset；每个 `(level,key)` 完整覆盖 replicate 0--999，无重复、缺失、额外 key 或 NaN/Inf。r016 summary 与 r015 point、CI、centered p、Holm、support 逐字段一致。独立按冻结规则重算 gate：unit 6/6，覆盖三数据集与至少两 detector families，FAIR unit D 支持，dataset 3/3；`gate_r015.json` 的 status、counts、`synchronized=true` 和 `soda_primary=mother_scene` 一致。

zero-eligible cluster 不是恒真占位：DIOR-R A/B/C 分别为 2403/2257/2203，FAIR1M D 为 920，SODA-A E/F 为 161/159，并保存每个 sorted zero-set SHA。完整 universe count/SHA 与 r015 一致。同一数据集 universe 相同。

## 集合、schema 与稿件索引

r015 set audit 的 SHA256 80/20 role 与 canonical `m069_common.split_role` 的 MD5 parity 不同，固定记为 `R015_SET_AUDIT_ROLE_DRIFT`。r017 按 canonical split 重建 source/target 集合，禁止交集为零。六个 feature/score Parquet 的完整 schema 不含 GT、angle error、risk、GT_AR、split/role 字段；prelabel/final seal hash 一致。

源码 witness 保留三项实现偏差：doubled-angle axial dispersion、association margin 单/零候选契约、sentinel。其它 witness 按源码行登记。新 claim ledger 仅修正 C03/C05 heading，八条 exact claim 与 SHA 不变且正文存在。novelty matrix 将 O2-DFINE、Fourier Angle Alignment 及其它不能闭合身份的根页/占位页统一标为 `UNKNOWN_EXCLUDED`。正文 exploratory、HRSC 跨零、leave-dataset 0/6 和 fixed-dose descriptive-only 边界成立，旧三组 dataset CI 与失效 UCB 未被消费。

## 完成语义

本轮 actual input manifest 与统一 access log 精确一致，`runtime_outputs=[]`；资源声明为 `cpu_intensive_phases=[]`、`bootstrap_recomputed=false`、`telemetry_required=false`。r014-r016、活动稿件、数据、runtime、split、threshold、selector、checkpoint 与 `dis/B.md` 均未修改。
