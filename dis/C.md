---
round_id: orientbench-c-topjournal-feasibility-receipt-20260809
planning_base: 3a4e86cf435af8b29e63b1668af92a1add7c6dbf
control_base: bc27506f7d7c0e47c4d67b202b9157bd4016a87a
source_execution_commit: cdf764c5a974030739a9992079bedb8b970fb2a7
source_execution_status: ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809
source_numbers_status: DESCRIPTIVE_UNVERIFIED
source_reported_gate: FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED
scientific_data_cutoff: a9067fb16d2bbd747dfe69789ac33a5911eb15fe
protected_B_blob: c0c2571f3a5c828673b39e6458ceaed5f14c5a6a
review_mode: post_feasibility_abnormal_execution_receipt_authorization
evidence_cutoff: 2026-08-09
receipt_status: READY_FOR_SERVER_FEASIBILITY_RECEIPT
receipt_execution_status: NOT_STARTED
current_route: ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC
tgrs_status: CONDITIONAL_ON_FUTURE_METHOD_UPGRADE
cc_recommendation: 'no'
cc_status: COMPLETED_CLOSED
---

# OrientBench C：顶刊可行性源执行异常裁决与 receipt 交接

## 结论

源执行绑定提交 `cdf764c5a974030739a9992079bedb8b970fb2a7`。该提交已发布，但其证据链不能支持“完整且可复核”的执行声明；源完成状态永久固定为：

```text
ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809
```

这不是技术早停，也不是 efficacy early stop；更不能把它映射为正式科学 `FAIL`。源执行报告中的全部指标统一为 `DESCRIPTIVE_UNVERIFIED`。其所报 `FAIL_TO_MEASUREMENT_ONLY` 只是保守且安全的方向，机器状态固定写作 `FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED`，不能作为已验证科学裁决、论文数字或 venue gate 消费。

当前路线仍为 `ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC`。唯一下一步是服务器按 `dis/sug.md` 完成一次 receipt-only 独立验收；receipt 尚未开始，也未执行。

## 证据锁

- planning base：`3a4e86cf435af8b29e63b1668af92a1add7c6dbf`。
- receipt control base：`bc27506f7d7c0e47c4d67b202b9157bd4016a87a`。
- source execution：`cdf764c5a974030739a9992079bedb8b970fb2a7`。
- scientific data cutoff：`a9067fb16d2bbd747dfe69789ac33a5911eb15fe`。
- protected B blob：`c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`；C 只核验 Git blob/diff 元数据，不读取或触碰内容。
- active manuscript：`top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`；receipt 不改稿。
- active instruction：`dis/sug.md`。
- source runtime：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809`，严格只读。
- receipt code root：`top_journal_v3_reaudit_055/feasibility_receipt_20260809`。
- receipt runtime：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt_20260809`。
- 唯一未来报告：`dis/server_reports/orientbench-c-topjournal-feasibility-receipt-20260809.md`；当前不存在，不能冒充已开始或已回报。

## 源执行的恰好六个授权变更路径

`cdf764c5a974030739a9992079bedb8b970fb2a7` 的授权变更集合固定且只有：

1. `claude_code_and_supervisor.md`
2. `dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md`
3. `top_journal_v3_reaudit_055/feasibility_gate_20260809/finalize_evidence.py`
4. `top_journal_v3_reaudit_055/feasibility_gate_20260809/generate_feasibility.py`
5. `top_journal_v3_reaudit_055/feasibility_gate_20260809/protocol.json`
6. `top_journal_v3_reaudit_055/feasibility_gate_20260809/validate_feasibility.py`

不得把服务器 Git-ignored runtime、聊天自述或其它路径补入该提交的 tracked scope。

## 决定性缺陷

1. **伪 ledger：** execution ledger 用文件 mtime 代替真实命令起止时间，并以硬编码退出码和完成状态回填 provenance。
2. **Track D 自证：** 许可、角度合约、资产和候选状态由生成器布尔值给出；validator 没有从官方原始取证独立重建，prior-outcome 搜索也未证明覆盖 Git-ignored persistent artifacts。
3. **bootstrap 未独立全重算：** validator 没有从 raw rows、完整 cluster universe 和固定抽样算法逐一生成并比较 replicate `0..9999` 的全部字段。
4. **状态与联合 gate 不闭合：** joint gate 漏检共同至少三 family、至少一个新 family 和无需 target-label tuning 等硬条件，`SENSITIVITY_UNSTABLE` 分支亦未实现和验证。

这些缺陷攻击的是执行与验证闭环，因此源数字不能升格；本机又没有服务器 Git-ignored runtime，不能用报告叙述替代 manifest、mutation 和逐 replicate 实物核验。

## 当前科学与投稿边界

源报告的负向方向不改变既有保守路线：继续按 measurement/diagnostic 主线组织几何等价、角度特异、scene-aware 的 orientation reliability 证据。只有 receipt 从独立 raw/official/search evidence 完整闭合后，C 才能重新裁定 Track M、Track D 和 joint gate；服务器的执行完成状态与科学 outcome 必须分开。

即使 receipt 将来得到正向 gate，也只允许 C 起草未来新协议并再次请求用户批准，不自动授权方法实验。即使得到负向科学结果，只要 receipt 合约、validator、mutation、唯一提交、HTTPS 发布和 external receipt 全部闭合，也可以是正常执行。

## 唯一下一步与禁止项

唯一下一步是 `orientbench-c-topjournal-feasibility-receipt-20260809` 的 receipt-only validation。它只读源 runtime、sealed Core 资产、既有 manifest 与保存的官方取证，并写入新的 receipt code/runtime/报告范围。

receipt 期间一律禁止：

- 新实验、GPU、下载、训练、forward、推理或新 target outcome；
- 启用 `r020`、替换 gate、阈值、cluster、指标或状态 precedence；
- 用 DOTA、HRSC、Core、同数据集新 detector 或旧结果救场；
- 修改主稿，或把未验证数字写入论文；
- 重复调用 CC，或让 CC/B 执行服务器任务。

`cc_recommendation: no`。上轮 CC 保持 `COMPLETED_CLOSED`；用户未来明确重授权前不启动新轮次。

## 决策台账

| 项目 | 当前状态 | 下一项允许动作 |
|---|---|---|
| feasibility 源执行 | `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809` | 永久保留异常，不洗成正常执行 |
| feasibility 源数字 | `DESCRIPTIVE_UNVERIFIED` | receipt 独立重算前不得消费 |
| 源报告 gate | `FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED` | 仅保守方向，不是科学裁决 |
| 当前路线 | `ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC` | 仅执行 receipt-only validation |
| receipt | `READY_FOR_SERVER_FEASIBILITY_RECEIPT` / `NOT_STARTED` | 服务器按 active `dis/sug.md` 执行 |
| CC | `COMPLETED_CLOSED`；`cc_recommendation: no` | 用户明确重授权前保持关闭 |
