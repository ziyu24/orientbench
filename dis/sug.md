# OrientBench 服务器任务：r008 主稿 claim 隔离与证据对账（preflight-v2）

- round: `orientbench-c-r008-20260806`
- scientific evidence snapshot: `426d47855eb91d5af947e8bdf9e06d035a95ebf0`
- minimum instruction baseline: `4613142ba411c25f6a6ad06723538e877bce9403`
- active source manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`
- output manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v078.md`
- unique server report: `dis/server_reports/orientbench-c-r008-20260806.md`

服务器先 `git pull --ff-only` 当前分支。实际 execution HEAD 可以晚于 minimum instruction baseline，但必须包含该提交，且其 `dis/sug.md` 必须仍是本 round 的 preflight-v2；记录实际完整 HEAD。不得 checkout scientific snapshot，因为它是证据冻结点，不是执行指令提交。

## 1. 科学问题与两个独立状态

移除或隔离 r006/r007 中无效的 formal certification/FWER 结论后，OrientBench 的 orientation-specific measurement 主线是否仍有逐项可追溯、没有新增数字或首创包装的完整 claim 集？本轮只做 claim quarantine，不裁决期刊等级，不恢复 C2-R，不扩实验。

必须分别输出：

1. `hygiene_gate = PASS_CLAIM_QUARANTINE_R008 | FAIL_CLAIM_QUARANTINE_R008 | INCONCLUSIVE_CLAIM_QUARANTINE_R008`；
2. `measurement_core_status = SUFFICIENT_FOR_MEASUREMENT_REVISION | INSUFFICIENT_AFTER_QUARANTINE | INCONCLUSIVE_CORE_EVIDENCE`。

二者不得合并。hygiene pass 不代表科学核心充分，core sufficient 也不代表达到任何期刊。

## 2. 固定解释边界与证据规则

- r007 formal gate 保持 `FAIL_SPLIT_FST_VALIDITY_R007`，原因是实现未满足契约；它不是 split-FST 理论或科学假设反例。
- r007 的 108/108 FWER fail、96/1152 taint mismatch、2866 parity mismatch，及 r006 reported structure pass，禁止作为当前科学 claim 的支持证据。
- 14 rows / 12 contexts / A–C / DIOR-R-only 只允许标为描述性、探索性线索，不得称 formal certification、prevalence、跨数据集广度或 deployment guarantee。
- r004 literal gate 只允许作为历史协议结果。matched-only estimand 不覆盖 FP、FN、真空场景或完整部署输出。
- 标准 LTT、fixed-sequence、Holm 只能作为既有组件，不得算 OrientBench 首创或独立贡献。
- `dis/C.md`、`dis/B.md`、`dis/server_reports/**`、主稿叙述和 gate JSON 都不能作为 headline 数字的唯一事实源。
- 一个 claim 只有在 ledger 同时给出仓库内生成端/配置、消费端结果、适用数据集/单元、estimand 和证据状态时，才可标 `VALID`；缺一项只能 `QUALIFIED` 或 `UNRESOLVED`。

## 3. 两阶段执行；先清单后改稿

### 3.1 阶段 A：冻结 claim inventory 与 validator

先读取 v077，不改稿。枚举摘要、贡献、方法、结果、讨论、局限、结论中满足任一条件的句子：

- 含数字、百分比、比较级或显著性/保证用语；
- 含“首次、首个、系统、证明、保证、认证、部署、普适、稳健、显著、优于”或其英文对应词；
- 含 `LTT`、`fixed-sequence`、`Holm`、`FWER`、`certif*`、`guarantee*`、`deploy*`。

每个 v077 claim 生成稳定 `claim_id`，记录原 section heading、原文、规范化文本 SHA-256 和源行号。CSV 使用 UTF-8、RFC 4180，固定列：

`claim_id,source_section,source_line,source_text,source_text_sha256,claim_class,datasets,units,estimand,evidence_paths,evidence_status,action,target_section,target_text,target_text_sha256,reason`

固定枚举：

- `evidence_status = VALID | QUALIFIED | INVALID | UNRESOLVED`
- `action = RETAIN | QUALIFY | QUARANTINE | REMOVE`

`evidence_paths` 是 JSON array 字符串；每个路径必须存在于 execution HEAD，并标明生成端或消费端角色。先完成 inventory，再编写 deterministic validator：

`top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/validate_a1_claim_reconciliation_r008.py`

validator 只实现本文件规定的集合、schema、hash、覆盖率、路径和禁词检查，不自行判断创新。记录 validator 在编辑 v078 前的 SHA-256；之后不得修改它。若 inventory 无法闭合或 validator 无法运行，停止并输出 inconclusive，不进入阶段 B。

### 3.2 阶段 B：生成保守 v078

以 v077 的字节副本初始化 v078，先记录 v077 SHA-256，再只编辑 v078。逐项执行 ledger action：

- `RETAIN` 仅用于 `VALID` 的 orientation-specific measurement claim；
- matched-only、单数据集、探索性、retrospective 或边界不完整者必须 `QUALIFY`；
- 依赖禁用证据者必须 `QUARANTINE` 或 `REMOVE`；
- `UNRESOLVED` 不得保留为 headline，只能移除或在局限中明确写成未解决。

所有 v077→v078 修改 hunk 必须映射至少一个 `claim_id`；所有 v078 中满足阶段 A 抽取规则的句子也必须反向映射 ledger。任何未映射 hunk 或未映射 target claim 都是 hygiene fail。

## 4. 必须机器执行的检查

validator 和 gate JSON 至少报告：

1. v077 hash 未变；v078、ledger、validator 的 bytes/SHA-256/Git blob；
2. ledger schema、枚举、唯一 claim_id、路径存在性和 source/target text hash；
3. v077 抽取集合→ledger 与 v078 抽取集合→ledger 的双向覆盖，均须 100%；
4. v078 numeric token set、citation key/URL set、dataset name set、method/entity set 相对 v077 的差集；正文差集必须为空；
5. 每个修改 hunk→claim_id 覆盖率 100%；
6. 禁止肯定式表述命中：`正式认证|认证通过|保证控制|部署保证|formal certification|certified guarantee|FWER controlled|PASS_SPLIT_FST|PASS_BROAD_TARGET_FREE`。允许在历史/局限中出现，但同一句必须含 `历史|撤回|无效|未闭环|探索性|不构成|history|withdrawn|invalid|inconclusive|exploratory|not`，并逐条输出句子与裁决，不能只给计数；
7. v078 不得新增引用条目、数据集、算法、实验数字或首创声明；
8. operation counts：训练、检测器推理、score-regressor fit/predict、GPU、下载、外部数据访问全部为 0。

## 5. Gate

`PASS_CLAIM_QUARANTINE_R008` 当且仅当：阶段 A/B 均完成；双向覆盖、hunk 映射、schema、路径、hash、禁词和新增实体检查全过；无 `INVALID/UNRESOLVED` headline；无效 formal claim 全部隔离；授权路径与提交路径闭合。

`FAIL_CLAIM_QUARANTINE_R008`：上述任一可执行检查失败，或服务器擅自新增科学内容、把标准统计工具包装成首创、把实现错误包装成科学负结果。

`INCONCLUSIVE_CLAIM_QUARANTINE_R008`：必需输入、inventory、schema、hash 或证据路径无法闭合，且不能在不猜测的前提下判定。不得用主观补写变成 pass。

`SUFFICIENT_FOR_MEASUREMENT_REVISION` 当且仅当：隔离后至少保留 3 个不同 `claim_class` 的实质 OBB-specific measurement claims；全部为 `VALID/QUALIFIED`；合计覆盖至少 2 个数据集和 2 个检测器单元；形成“测量定义/机制或混杂—可复算观察—边界/反证”的闭环；不依赖禁用 formal 证据或标准 LTT novelty。否则为 `INSUFFICIENT_AFTER_QUARANTINE`；必要证据不可得时为 `INCONCLUSIVE_CORE_EVIDENCE`。

## 6. provenance、幂等性与早停

- 首次运行前，v078、ledger、gate、manifest、validator、server report 必须均不存在，且根记录不得已有本 round marker；否则停止并报告，不覆盖、不重复 append。
- 根记录只 append 一条，包含唯一 round marker、两个状态及 operation counts。运行结束验证本轮 marker 恰好出现一次。
- manifest 的 `authorized_changes` 必须精确等于第 7 节 7 个路径；登记全部输入和除自身外全部输出的 bytes/SHA-256/Git blob。manifest 自身固定写 `sha256 = N/A_SELF_REFERENCE`、`git_blob = N/A_SELF_REFERENCE`，不得伪造自哈希。
- 先完成 v078、ledger、validator、gate 和 server report，再 append 根记录一次；核对根记录最终 bytes/blob 后，最后生成 manifest。manifest 登记这些最终产物，唯独自身身份写 `N/A_SELF_REFERENCE`；manifest 生成后不得再修改任何输出。
- 不训练、不推理、不拟合 score regressor、不下载、不访问外部数据、不修改历史资产。任何必需输入缺失即早停。

## 7. 唯一授权写入与精确提交集合

精确 7 个 commit 路径：

- `claude_code_and_supervisor.md`（append-only 一条）
- `dis/server_reports/orientbench-c-r008-20260806.md`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v078.md`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_claim_reconciliation_r008.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_claim_reconciliation_gate_r008.json`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_claim_reconciliation_manifest_r008.json`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/validate_a1_claim_reconciliation_r008.py`

不得触碰其它路径，尤其 `dis/B.md`、`dis/C.md`、`dis/sug.md`、`dis/review_state.json`、v077 和 r004–r007 资产。需要偏离时写 `PROPOSED_DEVIATION` 并停止。

## 8. Git 与最终回复

起始工作树/index 必须干净；仅 fast-forward。只显式暂存上述 7 个路径，普通中文 commit，SSH push，禁止 force。提交前运行 validator、JSON 解析、`git diff --check`、普通/staged diff，并确认 `dis/B.md` 与 v077 blob 未变。

服务器最终回复首行只能是 `执行完毕` 或 `未执行完毕`。

第二行必须且只能给出：`dis/server_reports/orientbench-c-r008-20260806.md`
