task_execution: FULL_COMPLETION
r018_receipt_verdict: VALID_STATIC_ADJUDICATION_R018
r017_historical_verdict: PROTOCOL_DRIFT_R017
r017_underlying_failure: FAIL_AUDIT_IMPLEMENTATION_R017
numeric_acceptance: EXPLORATORY_CORE_SUPPORT_R015
numeric_gate_result: CONSISTENT_EXPLORATORY
source_metadata_result: SOURCE_FIELD_ABSENT
feature_contract_result: IMPLEMENTATION_DEVIATION
last_completed_phase: Phase C provenance closure
executed_required_phases: [Phase A, Phase B, Phase C]
early_stop_trigger: NONE
early_stop_meaning: NOT_APPLICABLE
unrun_required_phases: []
all_required_work_completed: true
push_status: PUSHED

# OrientBench r018 静态验收器终结裁决

## 决策结论

r018 的静态裁决收据有效。该结果终结本轮机械验收循环，但不把 r017 重新包装成通过：r017 固定为 `PROTOCOL_DRIFT_R017 / FAIL_AUDIT_IMPLEMENTATION_R017`，r014 固定为 `FAIL_PROTOCOL_R014`，数值证据仅保留为 `EXPLORATORY_CORE_SUPPORT_R015`。

既有 bootstrap 9,000 行的三元 key、replicate 完整性和有限值核验通过，故意错配 dataset 的负例可被检测。support 由 point、CI lower 与 Holm p 直接重算，unit 6/6、dataset 3/3；冻结 gate 一致。r016 summary 可比较数值全部一致，但 audit rows、cluster count/SHA、bootstrap reps 和 detector metadata 在来源表中缺失，状态为 `SOURCE_FIELD_ABSENT`，未用 r015 常量伪装成 summary 比较。

canonical MD5 parity 的源码和六个 target 的集合 count/sorted SHA 均已保存，禁止交集为零；`R015_SET_AUDIT_ROLE_DRIFT` 不变。

## Feature 与稿件法证

12 个 feature/score Parquet 的完整 Arrow schema、禁字段 contains/prefix 扫描、prelabel/final seal 均通过。production 微测试纠正了 r017 的 sentinel 误判：冻结 sentinel 与实际输出完全一致。两个真实偏差仍保留：单候选 association margin 为 1.0 而非冻结期望 0.0；doubled-angle axial dispersion 未在 production feature 中实现。因此 feature contract 为 `IMPLEMENTATION_DEVIATION`，可与有效的 r018 收据并存。

claim ledger 8/8、正文唯一命中与标题绑定通过；novelty 弱来源保持 `UNKNOWN_EXCLUDED`；探索性、HRSC 跨零、leave-dataset 0/6、fixed-dose descriptive-only、旧数值、内部术语和引用扫描通过。未修改稿件。

## Provenance 与范围

r017 manifest/validator 的 47 条输入完成 path、bytes、SHA、schema、read_only 全字段比较；r017 Git 单 commit、父节点、13 路径、唯一报告和 12 个非自引用 blob 全部闭合。`dis/B.md` 仅核对 blob OID 相等，未读取内容。输入快照、四类互斥读取记录与最后生成的 self-exempt manifest 已闭合。

本轮未重跑 bootstrap、训练、推理、重拟合或重打分，未修改 r014-r017、threshold、split、D_cal/D_audit、活动稿或 `dis/B.md`。
