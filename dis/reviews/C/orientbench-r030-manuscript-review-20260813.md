---
schema_version: 1
actor: C
review_id: orientbench-r030-manuscript-review-20260813
dispatch_id: orientbench-b-r030-jprs-manuscript-20260813
review_mode: open_attack
evidence_head: 657950ac455d4e98e31240a77de8f223b55e2a5f
execution_verdict: PROTOCOL_DRIFT_R030
scientific_verdict: JPRS_NOT_READY
external_review_recommendation: no
---

# C 对 r030 主稿包的严厉验收

## 执行裁决

r030 生成了可审阅的完整 Markdown 稿件包，但不能验收为冻结合同下的正常完成：`STARTED.json` 缺少 plan/dispatch/starting-commit 等冻结身份字段；报告使用未冻结的 `COMPLETE_JPRS_MANUSCRIPT_PACKAGE_PENDING_BC_REVIEW` completion token，并把 `ending_commit` 写成自引用占位。正式执行裁决为 `PROTOCOL_DRIFT_R030`。

`claim_check.json` 的 1,709/1,709 PASS 不能视为语义证据闭包。生成器在没有 SOURCE block 时可从异质数字池选择最近值，并对标题、引用和部分格式 token 直接标一致；它没有固定 claim-id、源文件、行/字段/key、变换和容差。包的字节完整性可用，科学主张仍需独立核验。

## 科学裁决

当前稿件是 measurement/diagnostic paper。外部审稿指出的首要反证成立：当前几何归一风险显式依赖 GT aspect ratio，而线性 probe 显式含 predicted aspect ratio；现有消融没有覆盖 `ALL_AR + unnormalized canonical angle risk`，因此尚未排除定义诱导的循环性。类别—AR 组成混杂与 FAIR1M/SODA-A/ORCNN mixed 结果也未得到正式归因。

当前真实级别为 `STRONG_JSTARS_OR_REMOTE_SENSING`；`ISPRS_JPRS` 仅是有条件目标，状态 `JPRS_NOT_READY`；TGRS 需要额外机制或可用修复。不得扩大为盲目全矩阵、重启 learned EQS，或用新数据集替换失败 gate。

## 唯一下一步

先执行只读资产预检，确认八个既有单元能否支持冻结的 2×2 循环性审计和类别标准化：必须有 predicted AR、GT AR、class id、confidence、size、canonical angle error、稳定 row key、image/mother cluster、split role 与官方标注 provenance。预检不得拟合、计算新风险、生成效果量或改稿。
