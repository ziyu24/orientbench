# OrientBench r018：r017 静态验收器终结裁决

- round: `orientbench-c-r018-20260808`
- execution base: `b349dcbd44685eae66bdabbdf7a795493ccdc08e`
- immutable r017 report: `dis/server_reports/orientbench-c-r017-20260808.md`
- archived r017 instruction: `dis/sug/orientbench-c-r017-20260808-server-returned.md`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
- unique report: `dis/server_reports/orientbench-c-r018-20260808.md`
- mode: **static/low-CPU final adjudication；禁止重跑 bootstrap、训练、推理、重拟合、重打分或改稿**

本轮不是为了把 r017 重新包装成 PASS，而是用一次可审计的静态收据终结机械验收循环。允许最终裁决为负；只要所有无条件阶段、产物、报告、commit 和 push 真实完成，就应如实写“执行完毕 + 负裁决”。不得为了得到正 token 改 gate、补造不存在的 source metadata、硬编码 bool，或覆盖 r014-r017 资产。

开始前完整读取所有上级/当前 `AGENTS.md`、`pth_data/readme.md`、本文件、r015-r017 报告与产物、当前协作状态。只用 HTTPS，核对 origin、当前/默认/upstream、完整 HEAD、工作树和 index；只允许 `git pull --ff-only`。HEAD 必须包含 `b349dcbd44685eae66bdabbdf7a795493ccdc08e`。脏树、不能 fast-forward、输入缺失/hash 不符、授权冲突即首行 `未执行完毕` 并早停；不得 stash、reset、clean、checkout、merge、rebase、删除未跟踪文件或触碰既有 stash。

## 1. 冻结裁决

以下事实不得反向漂移：

1. r017 确实运行、commit 并 push；它不是合法早停，也不是 EQS 性能失败。但其 `FULL_COMPLETION/PASS_STATIC_RECEIPT_R017` 被 C 拒绝，历史状态固定为 `PROTOCOL_DRIFT_R017 / FAIL_AUDIT_IMPLEMENTATION_R017`。
2. r017 Git 范围本身合格：单 commit、精确 13 条授权路径、`dis/B.md` blob 未变；12 个非自引用 tracked outputs 的 bytes/SHA 与 Git blob 一致。
3. 数值事实保留为 `EXPLORATORY_CORE_SUPPORT_R015`：当前表内按 `Delta_NRC>=0.02`、CI lower>0、Holm<0.05 独立判定为 unit 6/6、dataset 3/3，覆盖三数据集、至少两 detector families，FAIR unit D 支持。它仍非 confirmatory/deployable PASS；r014 正式 `FAIL_PROTOCOL_R014`、HRSC 跨零、leave-dataset 0/6、fixed-dose descriptive-only 均不变。
4. r017 的 claim 8/8 SHA/标题绑定、novelty `UNKNOWN_EXCLUDED` 修正、稿件边界与引用扫描可采纳；不得改正文、claim 文本、科学数字或 novelty 结论。
5. r017 必做实现缺口：
   - bootstrap 只验 `(level,key)`，没有验 `(level,key,dataset)`；summary 的 audit rows、cluster count/SHA、bootstrap reps、身份和 detector family 未逐字段比较；gate 直接信任旧 `supported` 列。
   - canonical split 只做源码 token 搜索，未保存 canonical/forbidden/intersection 集合的 count 与 sorted SHA witness。
   - frozen sentinel 源码实际实现 `(3,1,3,3,3,10,0)`，r017 却将其硬编码为 `false/IMPLEMENTATION_DEVIATION`；w/h swap、0/90 boundary 和 schema prefix/contains 也未由可执行微测试与逐文件 witness 证明。
   - validator 直接 `manifest_path.read_text()` 绕过 wrapper，随后只比较 path set，未比较 bytes/SHA/schema，却签发 `manifest_access_exact=true`。

## 2. Phase A：三元 key、support/gate 与 source metadata

新增独立 `validate_static_adjudication_r018.py`。不得 import 或调用 r015-r017 validator/PASS 函数，不得重跑 9,000 bootstrap。它必须从既有 committed/runtime 只读资产完成：

1. 验证 bootstrap 恰好 9,000 行，合法域为六个 unit 与三个 dataset 的明确 `(level,key,dataset)` 三元组；每个三元组恰好覆盖 replicate `0..999`，无重复、缺失、额外 key、dataset 错配或 NaN/Inf。validator 必须有一个故意错配 dataset 的内置负例，证明该检查会失败。
2. 从 point、CI lower、Holm p **重新计算**每个 unit/dataset 的 support；逐项保存 expected formula inputs、computed support、旧 `supported`、witness。禁止先筛旧 `supported` 再数 gate。
3. 仅用重新计算的 support 复算冻结 gate：unit 至少 4/6、覆盖三数据集、至少两 detector families、FAIR unit D 支持、dataset 3/3；再核对 `gate_r015.json` 的 numeric status、counts、`synchronized=true` 与 `soda_primary=mother_scene`。
4. 对 r016 summary 与 r015 表逐字段检查 point/CI/p/Holm/support。对 audit rows、cluster count/SHA、bootstrap reps、unit/dataset 身份和 detector family：若 r016 summary 本身没有字段，必须逐字段写 `SOURCE_FIELD_ABSENT`，不得以 r015 常量或硬编码映射冒充“summary 比较”；可另建带明确来源的 supplemental receipt，但状态只能是 `RECONSTRUCTED_NOT_SUMMARY_COMPARED`。
5. 保存 canonical MD5 parity split 的 source path/line witness；对每个 target 输出 canonical source set、forbidden target set、intersection 的 count 与 sorted SHA，并核对 intersection=0。明确保留 `R015_SET_AUDIT_ROLE_DRIFT`，不得改 split。

输出 `gate_and_metadata_receipt_r018.json`。若三元 key、support/gate 或可比较数值不一致，记录真实 numeric/gate mismatch；若仅 r016 summary metadata 字段缺失，则如实记录 source limitation，不得制造 PASS_R017。只要审计完整且没有 r018 验收器自身错误，`SOURCE_FIELD_ABSENT/RECONSTRUCTED_NOT_SUMMARY_COMPARED` 必须映射为 `r018_receipt_verdict=VALID_STATIC_ADJUDICATION_R018`、`task_execution=FULL_COMPLETION`：这是 r017 source limitation，不是 `FAIL_VALIDATION_R018`，也不是早停。

## 3. Phase B：feature contract 与稿件索引复核

输出 `feature_contract_audit_r018.json`，必须做到：

1. 对六个单元的 12 个 feature/score Parquet 保存逐文件完整 Arrow schema、大小写无关 prefix/contains 禁字段扫描结果、prelabel/final seal 的 expected/actual bytes+SHA。禁字段至少覆盖 `GT`/`ground_truth`、`angle_error`、`risk`、`GT_AR`、`split`、`role` 及其大小写/前缀/包含变体；缺任一文件或 seal witness 即失败。
2. 对 doubled-angle、`u_axis`、association-margin 单/零候选、sentinel、deterministic tie-break、w/h+90° 等价与 0/90 boundary，既保存源码 path/line/短 witness，也运行最小合成微测试并保存 input、expected、actual、tolerance、pass。所有微测试必须动态调用 r014 实际 production function/code path；禁止在 r018 validator 中复制或重实现公式后自测，也禁止用源码 token 存在或硬编码 bool 代替行为验证。
3. sentinel 的冻结期望精确为 `(u_axis,IoU_loss,center,wdisp,hdisp,score_disp,margin)=(3,1,3,3,3,10,0)`；源码和微测试一致时必须判 true，不得再标 implementation deviation。
4. 重新核对 r017 claim ledger 8/8 hash、唯一正文命中和最近标题；重新核对 novelty 中弱根页/会议或期刊首页均为 `UNKNOWN_EXCLUDED`；动态扫描正文 exploratory、HRSC 跨零、leave-dataset 0/6、fixed-dose descriptive-only、三组旧 CI、旧 UCB、内部 round/PASS/FAIL/validator/authorized-path/venue-ready 以及 DIOR/AOPG/PSC 引用。不得修改正文或 r017 ledger/matrix。

若 production 微测试发现真实 feature implementation deviation，必须保留负结果；在所有审计阶段完整执行时，它可与 `VALID_STATIC_ADJUDICATION_R018/FULL_COMPLETION` 并存。禁止为了拿 VALID receipt token 强行把行为微测试改成 PASS。

## 4. Phase C：无自欺的 provenance closure

输出 `provenance_receipt_r018.json`、`evidence_manifest_r018.json` 与 `validator_r018.json`：

1. 将 r017 manifest 作为普通只读输入，必须经统一 wrapper 读取；逐条全字段比较 r017 manifest 与 r017 validator 的 `actual_read_only_inputs`：path、bytes、SHA256、schema、read_only，保存缺失、额外和字段差异。
2. 从 Git commit `b349dcbd...` 的 blob，而非仅从工作树，核验 r017 单 commit/父节点/13 路径/唯一报告；逐个核验 12 个非自引用输出 bytes/SHA。每条 `git_blob_reads` 保存 commit/path/blob OID/bytes/SHA。`dis/B.md` 只比较 parent/head blob OID 相等，禁止 `cat-file` 读取其内容。r017 manifest 的 self 项只能按 `N/A_SELF_REFERENCE` 明确例外，不能伪造自哈希。
3. r018 wrapper 的每次读取必须且只能归入 `actual_read_only_inputs`、`executed_code`、`git_blob_reads`、`output_hash_reads` 四类之一：科学/审计输入只进第一类；解释器执行脚本与显式 imports 的模块源码进第二类；Git blob 读取进第三类；为 r018 tracked outputs 计算 bytes/SHA 的回读进第四类，均不得混淆或漏记。动态导入 production 模块时读取的 frozen delta-theta 等数据资产仍属于 `actual_read_only_inputs`，不能冒充 executed code。冻结最后一次 input 后生成 canonical input-record snapshot 及其 SHA；validator 与 manifest 都嵌入同一 snapshot SHA，并由该 in-memory snapshot 生成。validator 字段必须命名 `manifest_generated_from_frozen_snapshot`，不得声称 on-disk manifest 已独立验证。
4. r018 manifest 的 `tracked_outputs` 必须精确为第 6 节 10 条路径；manifest 自身 bytes/SHA 固定为 `N/A_SELF_REFERENCE`。manifest 最后一次写出，写后不得由同一 validator 重新读取；`actual_read_only_inputs` 与 frozen snapshot 逐条全字段一致。
5. `runtime_outputs: []`。`resource_declaration` 内嵌于 provenance receipt：`cpu_intensive_phases: []`、`bootstrap_recomputed:false`、`telemetry_required:false`、无 pool/GPU；禁止制造 CPU%、RSS 或 worker telemetry。
6. validator 必须显式区分：r018 执行是否完整、r017 历史裁决、数值采纳级别和每个失败项。成功 token 仅表示本轮**裁决收据有效**：`VALID_STATIC_ADJUDICATION_R018`，绝不表示 r017/deployable/venue PASS。

## 5. 报告、早停与完成语义

报告顶部必须逐行给出：

```text
task_execution: FULL_COMPLETION | INCOMPLETE_EARLY_STOP | INCOMPLETE_BLOCKED | PROTOCOL_DRIFT
r018_receipt_verdict: VALID_STATIC_ADJUDICATION_R018 | FAIL_VALIDATION_R018 | FAIL_PROVENANCE_R018 | FAIL_AUDIT_IMPLEMENTATION_R018 | PROTOCOL_DRIFT_R018
r017_historical_verdict: PROTOCOL_DRIFT_R017
r017_underlying_failure: FAIL_AUDIT_IMPLEMENTATION_R017
numeric_acceptance: EXPLORATORY_CORE_SUPPORT_R015 | REJECTED | NOT_EVALUATED
numeric_gate_result: CONSISTENT_EXPLORATORY | NUMERIC_OR_GATE_MISMATCH | NOT_EVALUATED
source_metadata_result: FULLY_COMPARED | SOURCE_FIELD_ABSENT | NOT_EVALUATED
feature_contract_result: PASS | IMPLEMENTATION_DEVIATION | NOT_EVALUATED
last_completed_phase: ...
executed_required_phases: [...]
early_stop_trigger: NONE | ...
early_stop_meaning: NOT_APPLICABLE | PROVENANCE_FAILURE_NOT_PERFORMANCE_FAILURE | VALIDATION_FAILURE_NOT_PERFORMANCE_FAILURE | BLOCKED_NO_SCIENTIFIC_VERDICT | PROTOCOL_FAILURE
unrun_required_phases: [] | [...]
all_required_work_completed: true | false
push_status: PUSHED | FAILED
```

- 首行只有两种：全部无条件阶段、产物、报告、commit 与 push 完成时写 `执行完毕`；任何早停、阻塞、协议漂移或 push 失败写 `未执行完毕`。
- `执行完毕` 可以伴随负科学/验证裁决；这表示任务完整运行，不表示 PASS。若 source metadata 缺失但已按本任务完整审计并给出负/受限裁决，仍可 `FULL_COMPLETION`。
- `VALID_STATIC_ADJUDICATION_R018` 只评价 r018 收据是否忠实、完整、可复核；被审计对象的 `NUMERIC_OR_GATE_MISMATCH`、`SOURCE_FIELD_ABSENT` 或 `IMPLEMENTATION_DEVIATION` 应进入各自 result 字段，不能反过来伪装成收据实现失败。`FAIL_VALIDATION_R018/FAIL_AUDIT_IMPLEMENTATION_R018` 仅用于 r018 自身未正确完成规定验证或生成了错误收据。
- 早停必须列出真实 trigger、未执行阶段及意义。来源/验证早停不是 EQS 性能失败；不得只写“脚本结束”。
- 本轮用于终结静态循环；不得自行创建 r019、训练任务、机制扩展或新 gate。

最终对话固定为：

```text
执行完毕
dis/server_reports/orientbench-c-r018-20260808.md
task_execution: FULL_COMPLETION
r018_receipt_verdict: ...
```

或：

```text
未执行完毕
dis/server_reports/orientbench-c-r018-20260808.md
task_execution: INCOMPLETE_EARLY_STOP | INCOMPLETE_BLOCKED | PROTOCOL_DRIFT
early_stop_trigger: ...
unrun_required_phases: [...]
```

## 6. 精确写入集合（10）

只允许创建/修改：

1. `claude_code_and_supervisor.md`（恰好 append 一个 r018 section）
2. `dis/server_reports/orientbench-c-r018-20260808.md`
3. `p3_selector/static_adjudication_r018/protocol_r018.json`
4. `p3_selector/static_adjudication_r018/scripts/validate_static_adjudication_r018.py`
5. `p3_selector/static_adjudication_r018/reports/gate_and_metadata_receipt_r018.json`
6. `p3_selector/static_adjudication_r018/reports/feature_contract_audit_r018.json`
7. `p3_selector/static_adjudication_r018/reports/provenance_receipt_r018.json`
8. `p3_selector/static_adjudication_r018/reports/validator_r018.json`
9. `p3_selector/static_adjudication_r018/reports/evidence_manifest_r018.json`
10. `p3_selector/static_adjudication_r018/docs/static_adjudication_r018.md`

禁止修改 r017 及更早任何文件、当前稿件、claim ledger、novelty matrix、数据、runtime、split、seed、threshold、selector、checkpoint、`.gitignore` 和其它路径，尤其不得触碰 `dis/B.md`。

最终只做一个中文 commit，只显式暂存上述 10 条；LF，`git diff --check` 零输出。使用 HTTPS 普通 push 当前分支，不改 origin、不 force。push 失败保留本地 commit，并按 `未执行完毕` 回执。
