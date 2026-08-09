# OrientBench 最小跨机器协作协议

## 当前锚点

- state：`READY_FOR_SERVER_FEASIBILITY_RECEIPT`
- round：`orientbench-c-topjournal-feasibility-receipt-20260809`
- planning base：`3a4e86cf435af8b29e63b1668af92a1add7c6dbf`
- receipt control base：`bc27506f7d7c0e47c4d67b202b9157bd4016a87a`
- source execution：`cdf764c5a974030739a9992079bedb8b970fb2a7`
- source completion：`ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`
- source numbers：`DESCRIPTIVE_UNVERIFIED`
- source reported gate：`FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED`
- scientific data cutoff：`a9067fb16d2bbd747dfe69789ac33a5911eb15fe`
- protected B blob：`c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`
- active instruction：`dis/sug.md`
- source report：`dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md`
- future receipt report：`dis/server_reports/orientbench-c-topjournal-feasibility-receipt-20260809.md`
- source runtime：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809`
- receipt code root：`top_journal_v3_reaudit_055/feasibility_receipt_20260809`
- receipt runtime：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt_20260809`
- current route：`ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC`
- CC：`COMPLETED / CLOSED`；`cc_recommendation: no`

跨机器共享只通过 Git 仓库，不写账号、机器标识、凭据、本地绝对路径或 C 侧私有规则。planning base、receipt control base、source execution、scientific cutoff 与 protected B blob 各有独立职责，不得互换。未来 receipt report 当前必须不存在；`READY_FOR_SERVER_FEASIBILITY_RECEIPT` 只表示可以交给服务器，不表示 receipt 已开始、已执行或已发布。

## 源执行裁决

源执行的 tracked 提交只包含六个授权路径：

1. `claude_code_and_supervisor.md`
2. `dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md`
3. `top_journal_v3_reaudit_055/feasibility_gate_20260809/finalize_evidence.py`
4. `top_journal_v3_reaudit_055/feasibility_gate_20260809/generate_feasibility.py`
5. `top_journal_v3_reaudit_055/feasibility_gate_20260809/protocol.json`
6. `top_journal_v3_reaudit_055/feasibility_gate_20260809/validate_feasibility.py`

该源执行永久为 `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`：ledger 使用 mtime 与硬编码完成/退出状态；Track D 由生成器布尔值自证且 prior-outcome 搜索没有证明覆盖 Git-ignored persistent artifacts；bootstrap 没有从 raw rows 与完整 cluster universe 独立逐 replicate 全重算；joint gate 漏硬条件且未实现 `SENSITIVITY_UNSTABLE`。因此全部源数字只是 `DESCRIPTIVE_UNVERIFIED`；所报 measurement-only 方向是保守选择，但不是正式科学 `FAIL`。

## 角色、所有权与写入边界

### C

C 冻结科学问题、状态映射、joint gate 和服务器证据契约；维护 `dis/C.md`、`dis/review_state.json`、本协议与 `dis/B_START_PROMPT.md`。服务器回报后仍由 C 从 tracked report 与发布对象审计证据；C 不以聊天状态或源数字直接裁定科学结论。

### 服务器

服务器只执行 active `dis/sug.md`。receipt 的唯一写范围是：

1. `top_journal_v3_reaudit_055/feasibility_receipt_20260809/**`
2. `outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt_20260809/**`
3. `dis/server_reports/orientbench-c-topjournal-feasibility-receipt-20260809.md`
4. `claude_code_and_supervisor.md`，仅 append-only

源 feasibility code/runtime、sealed Core、既有 manifests、官方取证、C 状态文件、主稿和旧报告全部只读；不得删除、覆盖、重命名、patch、补写或 backfill。receipt 不使用 GPU，不下载、不安装依赖、不训练、不 forward/inference、不读取候选 annotation 内容、不产生新 target outcome、不用 target label 调参，也不改稿。

### B / CC

`dis/B.md` 由 B/CC 独占；C 与服务器不得创建、读取内容、修改、格式化、移动、删除、暂存、恢复或提交，只可核验普通/staged diff 为零和 Git blob 等于固定值。上轮 CC 已完成并关闭；本轮不是新邀请。用户未来明确重授权前，CC/B 不执行服务器 receipt、不追加或改写 `dis/B.md`，也不成为最终裁决者。

## Receipt-only 科学状态

服务器执行健康与科学 outcome 是两条独立轴。科学状态分三层，由 independent validator 从 raw/official/search evidence 重建，不得消费 generator 的状态布尔值：

1. **Track M：** `INSUFFICIENT_ASSETS`、`METRIC_REVERSAL`、`BASELINE_DOMINATED`、`SENSITIVITY_UNSTABLE`、`ROBUST_CANDIDATE`，按 active `dis/sug.md` 的固定 precedence 互斥求值；它是 deterministic point-estimate screen，paired bootstrap CI 必须完整重算与报告，但不驱动本次 feasibility state。资产齐全却因数学退化或 executable-audit failure 无法唯一取五态时，不增设科学状态，记录 `scientific_gate: NOT_ADJUDICATED` 并执行异常。
2. **Track D：** 每个候选在 `CONTAMINATED`、`LICENSE_BLOCKED`、`INCOMPATIBLE_ANGLE_CONTRACT`、`MISSING_ASSET`、`ELIGIBLE_CANDIDATE` 中取唯一状态；所有较低优先级事实仍须保留。
3. **Joint gate：** `FAIL_TO_MEASUREMENT_ONLY`、`INCONCLUSIVE_FEASIBILITY`、`PASS_TO_METHOD_DESIGN`。PASS 必须同时满足 Track M robust、两个独立遥感 OBB 候选、共同至少三 detector family、至少一个 old Core 外新 family，以及无需 target-label tuning；INCONCLUSIVE 只允许 Track M 缺资产且 Track D 没有独立负条件。

源执行所报 `FAIL_TO_MEASUREMENT_ONLY` 在 receipt 前固定为 `FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED`。receipt 的科学负结果、真实缺资产或 measurement-only gate 不自动等于执行异常；相反，科学正向也不能弥补执行证据缺项。即使将来为 `PASS_TO_METHOD_DESIGN`，也只允许 C 起草未来协议并再次请求用户批准。

## Receipt 执行完成与异常

`正常执行完毕` 当且仅当 active `dis/sug.md` genuinely exhausted、独立 validator 通过、四项真实 isolated mutation 均被拒绝、tracked 内容封存后恰好一个提交、HTTPS push 成功且仓库外 external receipt 闭合。科学结论为负仍可正常执行完毕。

任一必做 phase 缺失、source runtime 不可用、provenance gap 没有按合约落为可判定证据、validator 或 mutation 失败、越界写入、提交数不等于一、HTTPS 发布失败或 external receipt 缺失，均为 `异常结束`。tracked report、generator/validator 的 PASS 或 `PENDING_EXTERNAL_RECEIPT` 都不能单独决定聊天状态。

详细命令、证据、路径、SHA、科学状态、缺失项和异常只能写入唯一 tracked receipt report；聊天不得承载这些字段。

## 服务器聊天唯一格式

服务器最终聊天只能在以下两个完整模板中二选一。只能有一对 wrapper 和一个状态短语；不得添加路径、SHA、解释、列表、前后缀或其它字符。

```text
👇👇👇👇👇👇

正常执行完毕

👆👆👆👆👆👆
```

或：

```text
👇👇👇👇👇👇

异常结束

👆👆👆👆👆👆
```

## 当前唯一动作与禁区

当前唯一动作是 receipt-only validation。禁止新实验、`r020`、gate substitution、DOTA/HRSC/Core rescue、同数据集新 detector 救场、修改主稿或重复调用 CC。receipt 尚未开始；服务器必须先按 `dis/sug.md` 完成 preflight，再决定执行聊天状态。
