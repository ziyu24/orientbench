# OrientBench 服务器任务：r008 主稿 claim 隔离与证据对账

- round: `orientbench-c-r008-20260806`
- scientific snapshot: `426d47855eb91d5af947e8bdf9e06d035a95ebf0`
- active source manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`
- output manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v078.md`
- unique server report: `dis/server_reports/orientbench-c-r008-20260806.md`

## 1. 唯一科学问题

移除或隔离 r006/r007 中无效的 formal certification/FWER 结论后，OrientBench 的 orientation-specific measurement 主线是否仍有一套逐项可追溯、没有新增数字或首创包装的完整 claim 集？本轮不恢复 C2-R，不判断标准 LTT/fixed-sequence/Holm 为 novelty，不下载 RSAR，不增加数据、训练、推理或统计重算。

## 2. 固定事实与解释边界

- r007 服务器提交的 formal gate 保持 `FAIL_SPLIT_FST_VALIDITY_R007`，原因是实现未满足预注册契约；它不是 split-FST 理论或科学假设的反例。
- r007 的 108/108 FWER fail、96/1152 taint mismatch、2866 parity mismatch 均不得作为科学结果引用。
- 14 qualifying rows / 12 contexts / A–C / DIOR-R-only 只允许标为描述性、探索性线索，不得称 formal certification、prevalence、跨数据集广度或 deployment guarantee。
- r004 的 literal gate 只允许作为历史协议结果；r006 的 reported structure pass 已撤回。
- matched-only estimand 不覆盖 FP、FN、真空场景或完整部署输出。
- 标准 LTT、fixed-sequence 与 Holm 只能作为既有统计组件，不得作为 OrientBench 首创。

## 3. 执行任务

1. 从 v077 逐字节复制生成 v078；只在 v078 修改，不触碰 v077。
2. 建立 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_claim_reconciliation_r008.csv`，每行至少包含：`claim_id,manuscript_section,claim_text_or_anchor,claim_class,evidence_path,evidence_status,action,reason`。覆盖摘要、贡献、方法、结果、讨论、局限和结论中的 headline/novelty/certification/deployment claim。
3. 对每一项标为 `retain | qualify | quarantine | remove`：
   - 只有生成端与口径闭合的 orientation measurement 结论可以 retain；
   - matched-only、单数据集、探索性或 retrospective 结果必须 qualify；
   - 依赖 r006/r007 formal pass、FWER、taint、parity 或 certification 的内容必须 quarantine/remove；
   - 找不到数字事实源时不得猜测，标为 unresolved 并移除 headline 用法。
4. 编辑 v078，使摘要、贡献、正文、表图说明、局限和结论口径一致。不得新增实验数字、引用、数据集、算法、首创声明或统计保证；不得把实现失败包装成负结果。
5. 生成 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_claim_reconciliation_gate_r008.json`，包含 ledger 总数、各 action/status 计数、未解决 claim 列表、禁止短语扫描结果、v077/v078 SHA-256、变更行统计和最终 gate。
6. 生成 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_claim_reconciliation_manifest_r008.json`，登记全部输入/输出的路径、bytes、SHA-256、Git blob（提交后可得者）、命令与 schema。报告不得伪造服务器原始资产可在 C 侧复哈希。
7. 写唯一报告并 append-only 向 `claude_code_and_supervisor.md` 追加恰好一条本轮记录。

## 4. Gate

- `PASS_CLAIM_QUARANTINE_R008`：ledger 覆盖所有 headline/novelty/certification/deployment claim；无效 formal claim 全部隔离；保留 claim 均有仓库证据路径和明确口径；v078 没有新数字/引用/数据集/方法；摘要、贡献、局限、结论一致；所有产物与授权路径闭合。
- `FAIL_CLAIM_QUARANTINE_R008`：任何无效 certification/FWER/taint/parity claim 仍作为当前结论；任何 headline 无事实源；任何标准统计工具被包装为首创；或 v078 新增未授权科学内容。
- `INCONCLUSIVE_CLAIM_QUARANTINE_R008`：主稿、证据路径、schema 或哈希无法闭合，且无法在不猜测的前提下裁决。

即使 PASS，也只说明 claim 隔离完成，不代表论文达到 TGRS，不代表实验充分。若删除 certification 后不足以形成完整 orientation-specific 论证，在报告中明确记录 `MEASUREMENT_CORE_INSUFFICIENT_AFTER_QUARANTINE`，不得补写结论救场。

## 5. 早停与资源

- 本轮禁止训练、检测器推理、score-regressor fit/predict、GPU、下载和外部数据访问；对应 operation counts 必须全部为 0。
- 不修改现有脚本、CSV/JSON、v077、r004–r007 报告或历史记录。
- 发现事实冲突时保留 v078 的保守表述，在 ledger 中标 unresolved；不要自行扩实验。
- 若不能在固定证据内完成，输出 inconclusive 报告并停止。

## 6. 唯一授权写入范围

只允许新增：

- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v078.md`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_claim_reconciliation_r008.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_claim_reconciliation_gate_r008.json`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_claim_reconciliation_manifest_r008.json`
- `dis/server_reports/orientbench-c-r008-20260806.md`

并允许 append-only 修改 `claude_code_and_supervisor.md` 恰好一条。其它路径全部禁止，尤其不得触碰 `dis/B.md`、`dis/C.md`、`dis/sug.md`、`dis/review_state.json` 和 v077。需要偏离时写 `PROPOSED_DEVIATION` 并停止。

## 7. Git 与最终回复

起始工作树/index 必须干净且包含精确 snapshot；仅 fast-forward。显式暂存上述授权文件，普通中文 commit，SSH push，禁止 force。提交路径必须与 manifest 授权集合完全一致。

服务器最终回复首行只能是：

`执行完毕`

或：

`未执行完毕`

第二行必须且只能给出：`dis/server_reports/orientbench-c-r008-20260806.md`
