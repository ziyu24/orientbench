# OrientBench r017：r016 静态收据修正与投稿证据索引闭合

- round: `orientbench-c-r017-20260808`
- execution base: `097f5829abd0159e38dd3312dae84833ca36ade1`
- immutable r016 report: `dis/server_reports/orientbench-c-r016-20260808.md`
- archived r016 instruction: `dis/sug/orientbench-c-r016-20260808-server-returned.md`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
- unique report: `dis/server_reports/orientbench-c-r017-20260808.md`
- mode: **static/low-CPU receipt closure；禁止重跑 9,000 bootstrap、训练、推理、重拟合或重打分**

本轮只修正 r016 的验收器与投稿索引缺口。r014-r016 全部只读，不得覆盖历史报告、代码、数字、稿件或 runtime。不得把探索性 Core 数字升级为 confirmatory/deployable 证据。

开始前完整读取所有上级/当前 `AGENTS.md`、`pth_data/readme.md`、本文件、r015/r016 报告与产物、当前协作状态。只用 HTTPS，核对 origin、当前/默认/upstream、完整 HEAD、工作树和 index；只允许 `git pull --ff-only`。HEAD 必须包含 `097f5829...`。脏树、不能 fast-forward、输入缺失/hash 不符、授权冲突即首行 `未执行完毕` 并早停；不得 stash、reset、clean、checkout、merge、rebase、删除未跟踪文件或触碰既有 stash。

## 1. 冻结裁决与科学边界

以下事实不得反向漂移：

1. r016 Git 为单 commit、精确 10 条授权路径，`dis/B.md` blob 未变；9 个非自引用 tracked blobs 与 Git blob bytes/SHA 一致。
2. r016 确实从 raw labels、完整 universe 与 sealed scores 重算 6,000 unit + 3,000 dataset replicates，seed、同步 multiplicity、SODA mother scene、point/CI/p/Holm 与 r015 数字一致。因此 C 采纳 `EXPLORATORY_CORE_SUPPORT_R015` 作为高置信探索性数值，不要求 r017 再跑 bootstrap。
3. r016 的 `FULL_COMPLETION/PASS_R015_VALIDATOR_CLOSURE_R016` 被拒绝，历史验收固定为 `PROTOCOL_DRIFT_R016 / FAIL_AUDIT_IMPLEMENTATION_R016`。它不是合法早停，也不是 EQS 性能失败。
4. 决定性缺口：r016 未读取/语义核对 `gate_r015.json`，只硬编码 6/6 与 3/3；zero-eligible 条件是恒真 `>=0` 且未输出 zero-set SHA；未验证 9,000 key/replicate 全集、summary metadata 和最终 gate 全字段。
5. r016 manifest 漏实际读取文件，却列入未读取的 gate/runtime；telemetry 使用全机 CPU、父进程 RSS 与硬编码 worker=38，不能称进程树实测。该历史 telemetry 不可事后修复，也不影响已复算的数值本身。
6. r015 稿正文与 claim hashes 基本合格，但 novelty matrix 仍把 O2-DFINE 的 `https://arxiv.org/` 根页和 Fourier Angle Alignment 的 `https://openaccess.thecvf.com/CVPR2026` 占位页放入 `verified_source`；r016 漏检。claim ledger 的 C03/C05 section heading 也与正文不完全一致。

## 2. Phase A：静态数值与 gate 收据

新增 `validate_r016_receipt_r017.py`，不得 import r015/r016 validator 或其 PASS 函数，不得重新执行 bootstrap。它必须从 committed r015/r016 CSV/JSON 独立完成：

1. 验证 bootstrap 表恰好 9,000 行；合法 key 域为六个 unit 加三个 dataset；每个 `(level,key)` 恰好覆盖 replicate `0..999`，无重复、缺失、额外 key、NaN/Inf。
2. 逐字段比较 r016 summary 与 r015 unit/dataset：point、CI、p、Holm、support、audit rows、完整 cluster count/SHA、bootstrap reps、unit/dataset 身份和 detector family；每项输出 expected/actual/error/witness。
3. 从 summaries 独立复算冻结 gate：unit support 至少 4/6、覆盖三数据集和至少两 detector families、FAIR unit D support、dataset 3/3；核对 `gate_r015.json` 的 numeric status、unit/dataset counts、`synchronized=true`、`soda_primary=mother_scene`。禁止硬编码“6/6即通过”代替 gate。
4. 从原 image universe、matched labels 和 SODA map 重建每个 unit 的 zero-eligible cluster **集合本身**；输出 count 与 sorted zero-set SHA，并确认 count>0、完整 universe count/SHA 与 r015/r016 一致。
5. 记录 r015 leakage audit 使用 SHA256 80/20 role 而 r014 实际 `m069_common.split_role` 为 MD5 parity 的差异为 `R015_SET_AUDIT_ROLE_DRIFT`；使用 r014 实际 canonical split 重建禁止交集，不得改 split。

输出 `gate_and_zero_receipt_r017.json` 与 `zero_eligible_sets_r017.csv`。数值一致时保留 `EXPLORATORY_CORE_SUPPORT_R015`；任一数字/gate/集合不一致则 `FAIL_VALIDATION_R017`，不得修改历史数字。

## 3. Phase B：schema、实现 witness 与稿件索引修正

1. 对六个 feature/score Parquet 保存完整列名/schema witness，以大小写无关和前缀/包含规则检查 GT、angle error、risk、GT_AR、split/role 等禁用字段；逐项核对 prelabel/final seal hashes。
2. 对 doubled-angle axial dispersion、`u_axis`、association margin 单/零候选、sentinel、deterministic tie-break、w/h swap、0/90 boundary，输出源码 path、行号、精确短 witness 与 bool。不能只做模糊 token 搜索后保存 bool。
3. 新建 `claim_ledger_r017.csv`，保持 8 条 exact claim 与 SHA 不变；将 C03 heading 精确改为 ``6.3 `ar>=2.1` 连续角风险排序``，将 C05 heading 精确改为 `6.6 跨数据集预测等变性选择的探索性审计`；其余 heading 逐条与正文核对。
4. 新建 `novelty_matrix_r017.csv`：O2-DFINE 与 Fourier Angle Alignment 的 `verified_source` 必须改为 `UNKNOWN_EXCLUDED`；所有仅根页、会议首页、期刊首页或无法闭合身份的来源均同样标记，不能靠 `novelty_action=exclude` 抵消错误的 verified_source。
5. 动态检查正文 exploratory/HRSC 跨零/leave-dataset 0/6/fixed-dose descriptive-only；排除全部三组 r014 错误 dataset CI、旧失效 UCB 数字、内部 round ID、standalone `PASS/FAIL`、validator、authorized path 和 venue-ready 用语；核对 DIOR DOI、AOPG/DIOR-R 与 PSC 作者。

输出 `schema_feature_manuscript_audit_r017.json`。不得修改 r015 稿正文；若发现正文实质错误，只在报告列 `PROPOSED_CORRECTION`，本轮不擅自改稿。

## 4. Phase C：真实 input manifest 与低资源声明

- 本轮禁止 ProcessPool/ThreadPool 和 CPU 密集复算。`resource_declaration_r017.json` 必须写 `cpu_intensive_phases: []`、`bootstrap_recomputed: false`、`telemetry_required: false`，不得再制造 CPU% 或 worker 数。
- 脚本内所有文件读取必须经过统一 access wrapper 记录实际访问路径；Python import 间接读取的 `scripts/m069_common.py`、`scripts/derive_delta_theta_075.py` 与 frozen delta-theta JSON须显式登记。
- `evidence_manifest_r017.json` 的 `actual_read_only_inputs` 必须与 access log 精确相等；每项含 bytes/SHA/schema。未读取文件不得冒充 input，已读取文件不得遗漏。`runtime_outputs: []`，因为本轮不产生 gitignored runtime。
- validator 必须核对 r017 产物结构、JSON/CSV、唯一报告、受保护 B blob和授权集合；成功 token 只能为 `VALID_STATIC_RECEIPT_R017`。

## 5. Gate、早停与完成语义

报告顶部必须逐行给出：

```text
instruction_fulfillment: ALL_REQUIRED_PHASES_COMPLETED | EARLY_STOP_WITH_UNRUN_PHASES | BLOCKED_WITH_UNRUN_PHASES | PROTOCOL_DRIFT
execution_completion: FULL_COMPLETION | INCOMPLETE_EARLY_STOP | INCOMPLETE_BLOCKED | PROTOCOL_DRIFT
round_verdict: PASS_STATIC_RECEIPT_R017 | FAIL_VALIDATION_R017 | FAIL_PROVENANCE_R017 | FAIL_AUDIT_IMPLEMENTATION_R017 | PROTOCOL_DRIFT_R017
r016_historical_acceptance: PROTOCOL_DRIFT_R016
r016_underlying_failure: FAIL_AUDIT_IMPLEMENTATION_R016
numeric_acceptance: EXPLORATORY_CORE_SUPPORT_R015 | REJECTED | NOT_EVALUATED
last_completed_phase: ...
executed_required_phases: [...]
early_stop_trigger: NONE | ...
early_stop_scientific_meaning: NOT_APPLICABLE | PROVENANCE_FAILURE_NOT_PERFORMANCE_FAILURE | VALIDATION_FAILURE | PROTOCOL_FAILURE | BLOCKED_NO_SCIENTIFIC_VERDICT
unrun_required_phases: [] | [...]
all_required_work_completed: true | false
push_status: PUSHED | FAILED
```

- 只有 A-C、validator、manifest、报告、commit、push 全部完成，才能写 `ALL_REQUIRED_PHASES_COMPLETED/FULL_COMPLETION/true`。
- 若静态检查得到负结果但所有无条件阶段、产物、报告和 push 均完成，可写 `执行完毕`，同时 `round_verdict=FAIL_VALIDATION_R017`；“完整执行”和“科学/验证通过”必须分开。
- 输入/hash/provenance 硬门触发后停止，写 `INCOMPLETE_EARLY_STOP`，列出未运行阶段；来源早停不是性能失败。
- 环境阻塞写 `INCOMPLETE_BLOCKED`；越权、改 gate、缺必做验证却声称完成写 `PROTOCOL_DRIFT`。

最终对话格式固定：

```text
执行完毕
dis/server_reports/orientbench-c-r017-20260808.md
instruction_fulfillment: ALL_REQUIRED_PHASES_COMPLETED
```

或：

```text
未执行完毕
dis/server_reports/orientbench-c-r017-20260808.md
instruction_fulfillment: EARLY_STOP_WITH_UNRUN_PHASES | BLOCKED_WITH_UNRUN_PHASES | PROTOCOL_DRIFT
early_stop_trigger: ...
unrun_required_phases: [...]
```

禁止只写“脚本结束”或把本地 commit 当作已推送交付。

## 6. 精确写入集合（13）

只允许创建/修改：

1. `claude_code_and_supervisor.md`（恰好 append 一个 r017 section）
2. `dis/server_reports/orientbench-c-r017-20260808.md`
3. `p3_selector/static_receipt_r017/protocol_r017.json`
4. `p3_selector/static_receipt_r017/scripts/validate_r016_receipt_r017.py`
5. `p3_selector/static_receipt_r017/reports/gate_and_zero_receipt_r017.json`
6. `p3_selector/static_receipt_r017/reports/zero_eligible_sets_r017.csv`
7. `p3_selector/static_receipt_r017/reports/schema_feature_manuscript_audit_r017.json`
8. `p3_selector/static_receipt_r017/reports/validator_r017.json`
9. `p3_selector/static_receipt_r017/reports/resource_declaration_r017.json`
10. `p3_selector/static_receipt_r017/reports/evidence_manifest_r017.json`
11. `p3_selector/static_receipt_r017/docs/static_receipt_r017.md`
12. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r017.csv`
13. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/novelty_matrix_r017.csv`

禁止修改 r016 及更早任何文件、当前 r015 稿、数据、runtime、split、seed、threshold、selector、checkpoint、`.gitignore` 和任何其它路径，尤其不得触碰 `dis/B.md`。

最终只做一个中文 commit，只显式暂存上述 13 条；LF，`git diff --check` 零输出。manifest 最后生成，self=`N/A_SELF_REFERENCE`。使用 HTTPS 普通 push 当前分支，不改 origin、不 force。push 失败保留本地 commit并按 `未执行完毕` 回执。
