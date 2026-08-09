# OrientBench 顶刊可行性纠偏验收与简洁回报设计

```yaml
document_status: AWAITING_USER_WRITTEN_SPEC_APPROVAL
date: 2026-08-09
review_base: cdf764c5a974030739a9992079bedb8b970fb2a7
dispatch_commit: cb84b950ec5b94d89d0b13327a529e5712885111
scientific_data_cutoff: a9067fb16d2bbd747dfe69789ac33a5911eb15fe
protected_B_blob: c0c2571f3a5c828673b39e6458ceaed5f14c5a6a
user_conceptual_approval: true
user_written_spec_approval: false
server_execution_authorized: false
cc_recommendation: no
```

## 1. 已核定问题

服务器提交 `cdf764c5a974030739a9992079bedb8b970fb2a7` 的 Git 发布正常，但其 `FULL_COMPLETION` 不予接受，当前执行状态固定为 `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`：

- execution ledger 用文件 mtime 代替真实命令起止时间，并硬编码部分退出码与完成状态；
- Track D 的许可、角度合约和资产状态由生成器布尔值直接给出，validator 未从官方取证和真实搜索结果独立重建；
- prior-outcome 搜索不能证明覆盖 Git-ignored persistent artifacts；
- joint gate 实现遗漏共同三-family、新 family 和 target-label tuning 等硬条件；
- validator 未从 raw rows、完整 cluster universe 和固定抽样算法逐 replicate 重算 10,000 次 bootstrap；
- `SENSITIVITY_UNSTABLE` 分支未在实现中闭合；本机没有服务器 Git-ignored runtime，不能独立核验 manifest 与 mutation 实物。

因此本轮报告中的 Track M/Track D 数字只可标为 `DESCRIPTIVE_UNVERIFIED`。`FAIL_TO_MEASUREMENT_ONLY` 的方向是保守安全的，但不能把本轮写成已验证科学证据。

## 2. 选定方案

采用一次 **receipt-only 纠偏验收**。不重跑 detector、训练、推理或新科学实验；只读取现有 feasibility runtime、既有 sealed Core 源资产、既有 manifest 和官方取证，补齐独立验证。

未采用的方案：

- 直接接受原 `FULL_COMPLETION`：证据不闭合，拒绝；
- 全量重跑实验或更换 gate：没有必要且会扩大选择空间，拒绝。

## 3. 固定身份与权限

```yaml
round_id: orientbench-c-topjournal-feasibility-receipt-20260809
source_execution_commit: cdf764c5a974030739a9992079bedb8b970fb2a7
source_runtime: outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809
receipt_runtime: outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt_20260809
receipt_code_root: top_journal_v3_reaudit_055/feasibility_receipt_20260809
report_path: dis/server_reports/orientbench-c-topjournal-feasibility-receipt-20260809.md
gpu_authorized: false
download_authorized: false
training_authorized: false
inference_authorized: false
new_target_outcome_authorized: false
manuscript_edit_authorized: false
```

源 runtime 和旧科学资产全部只读，禁止删除、覆盖、重命名或补写。receipt 只能写入新的 code/runtime/report 路径及 `claude_code_and_supervisor.md` 的 append-only 记录。

## 4. 最小补验内容

### 4.1 Track M

1. 将 A–F 每个输入文件的 bytes/SHA256/schema/row keys/cluster universe 与 r014、m069 的既有 sealed manifest 独立比对；不得只与本轮自生成 inventory 比对。
2. 从 raw sealed rows 重算 risk、五个非 learned score、AUGRC、AURC/NRC、Risk@70/90 和 unit-equal dataset aggregate。
3. 动态核验 pinned AUGRC 参考实现及 commit 身份，禁止仅用同源硬编码 toy expected 自证。
4. 按 seed `20260809`、完整 cluster universe 和同步 multiplicity 逐一重算 replicate `0..9999`，逐字段比较全部 replicate、CI 和 worker/cluster witness。
5. 实现并验证 `INSUFFICIENT_ASSETS`、`METRIC_REVERSAL`、`BASELINE_DOMINATED`、`SENSITIVITY_UNSTABLE`、`ROBUST_CANDIDATE` 五个互斥分支；已触发高优先级负状态时仍如实记录低优先级检查是否执行。

### 4.2 Track D

1. 从已保存的官方 body/header/meta 独立重建 URL、HTTP 状态、bytes/SHA256、许可、版本、split、OBB/angle/ignore 语义；不信任原 candidate inventory 的布尔字段。
2. 对 Git tracked、Git-ignored persistent artifacts、项目 manifests/reports、`pth_data/readme.md` 和 dataset filename/stat-only 视图执行真实搜索；命令必须显式覆盖 ignored 文件，且不得打开候选 annotation 内容。
3. 独立重建每个候选的全部失败事实、precedence 和最终状态；资产存在性必须来自实际 stat/hash 证据，不能硬编码 `ABSENT`。

### 4.3 Joint gate 与 provenance

validator 必须逐项实现完整 gate：Track M 状态、两个独立遥感候选、共同至少三个 family、至少一个新 family、无需 target-label tuning，以及 `INCONCLUSIVE` 的精确条件。禁止仅检查 eligible 数量。

新 receipt 的命令、cwd、真实起止时间、退出码、stdout/stderr 哈希必须在执行时记录。旧 run 无法恢复的字段标记为 `SOURCE_FIELD_ABSENT`，不得用 mtime 或常量回填。validator 从 raw/official/search evidence 重建结论，不读取生成端 gate token。

## 5. 完成语义

- `正常执行完毕`：receipt 合约全部完成，独立 validator、必要 mutation、唯一 commit、HTTPS push 和远端回执均闭合。科学结论为负也仍可正常完成。
- `异常结束`：任何必做验收缺失、validator 不通过、runtime 不可用、provenance 仍不闭合，或 Git 发布未闭合。

详细字段、证据、结论和错误只写入唯一服务器报告。服务器最终对话必须使用中文，且只能是下列两种之一；不得追加报告路径、SHA、阶段列表或解释：

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

## 6. 验收后决策

- 若纠偏验收确认 Track M 的负状态或 Track D 不足，停止服务器方法实验并进入 measurement-only 主稿重写。
- 若纠偏验收意外得到正向 gate，也只允许 C 起草未来协议并再次请求用户批准，不直接授权实验。
- 不重复调用 CC，不使用 DOTA/HRSC/Core 续命，不换 gate。

## 7. 成功标准

- 原 feasibility round 永久保留为异常执行，不被覆盖；
- receipt 不产生新 target outcome；
- 所有关键判断均能从独立证据重建；
- 服务器对话只有一行中文状态，详细信息全部进入仓库唯一报告。
