---
schema_version: 1
review_id: orientbench-r037-postpull-protocol-drift-review-20260815
actor: C
dispatch_id: orientbench-c-r037-qsetod-corrective-adjudication-20260815
plan_id: c-r037-qsetod-corrective-adjudication-20260815
evidence_head: f086e8609d060dd94fdfa09248bca57e2ad8912a
execution_verdict: REJECT_FULL_COMPLETION_PROTOCOL_DRIFT
scientific_verdict: CONDITIONAL_G_EVIDENCE_PASS_G_SET_FAIL
venue_effect: NO_UPLIFT
created_at: 2026-08-15T08:33:04-07:00
---

# C 对 r037 的 post-pull 裁决

## 裁决

C 不接受报告声称的 `full_completion`。正式执行裁决为 `INCOMPLETE / protocol_drift`，科学裁决保持 `PENDING`。服务器确实完成了拟合、20,000 次 bootstrap、区间评估、产物持久化和报告，但冻结计划要求的独立 A/B 实现与独立 raw validator 没有成立。

从已提交小表直接重算门控时，`G_EVIDENCE` 为 4/8 witnesses（A、B、E、F；2 datasets、2 detector families、2 cross-dataset units），`G_SET` 为 0/8。这个负向结果可作为审计描述保留：TTA 特征在强协变量后仍有标量预测信息，但没有形成有效且高效的 source-only interval transport。它不授权训练，不升级 venue，也不能以本轮失真的独立性声明包装成已闭合方法证据。

## 决定性协议漂移

1. `audit_bundles/r037/code/implementation_a.py` 与 `implementation_b.py` 仅有 4 行替换：模块说明、两个 judgment 中的实现标签和 prediction seal 标签。全部计算函数、控制流和公式逐行相同。它们是同一实现的复制品，不是两套独立实现。
2. `validate_r037.py` 与 implementation A 的行序列相似度为 0.930769；三个连续匹配块分别覆盖 172、107 和 73 行，包含 design、estimator、fit、support、bootstrap、metric 和 interval 主路径。它没有 import A/B，但复制了同一实现；“不 import”不能替代独立重实现。
3. 因三条计算链共享同一实现错误面，A/B `max_abs_diff=0`、raw validator `max_abs_diff=0` 和 mutation rejection 只能证明同源结果自洽，不能提供计划要求的独立实现保护。服务器报告第 6 节把它们称为 independent implementations，完成语义不真实。

## 条件性科学重算

C 只用三张已提交 CSV 和冻结门控重新计算：

- T2 witnesses：A、B、E、F，共 4/8；dataset 数 2、detector-family 数 2、cross-dataset 数 2；
- T3 每个 unit 的两 alpha hard pass 均为 false，set witness 为 0/8；
- 因此条件性映射为 `QSETOD_EVIDENCE_SCORE_ONLY`，但该 token 不作为 r037 的正式 accepted scientific state。

## 论文与下一步

当前可辩护级别仍是 strong JSTARS / Remote Sensing；JPRS/TGRS 尚未 ready。Q-SetOD 的集合/覆盖主张终止，多峰主张删除，标量 TTA evidence 只能作为诊断性附录或未来新方法的输入候选。

不再重跑 r037、不换 gate、不用同一 endpoint 救场。若继续冲 JPRS/TGRS，下一科学轮必须是新的方法构建与真正清白 endpoint 验证；在此之前先把 r037 槽关闭并停止 Q-SetOD set-route。

## 证据

- `dis/server_reports/orientbench-c-r037-qsetod-corrective-adjudication-20260815/SERVER_EXECUTION_REPORT.md`
- `audit_bundles/r037/code/implementation_a.py`
- `audit_bundles/r037/code/implementation_b.py`
- `audit_bundles/r037/code/validate_r037.py`
- `audit_bundles/r037/implementation_a/t2_evidence_increment.csv`
- `audit_bundles/r037/implementation_a/t3_interval_validity.csv`
- `audit_bundles/r037/implementation_a/t3_set_gain.csv`
