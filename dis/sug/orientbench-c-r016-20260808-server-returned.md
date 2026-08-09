# OrientBench r016：补齐 r015 独立验证器与完成语义

- round: `orientbench-c-r016-20260808`
- execution base: `9f906fb3bfb07bd276d380a009cd95e2dc57c36a`
- immutable r015 report: `dis/server_reports/orientbench-c-r015-20260808.md`
- archived r015 instruction: `dis/sug/orientbench-c-r015-20260808-executed.md`
- immutable r015 package: `p3_selector/deployable_proxy_r015/`
- manuscript under audit: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
- unique report: `dis/server_reports/orientbench-c-r016-20260808.md`
- mode: **CPU-only validator closure；禁止训练、推理、重拟合、重打分或换 gate**

本轮只修复 r015 的独立验收缺口。不得修改 r015 及更早的任何代码、报告、数字、稿件或 runtime，不得把 r015 已揭盲数字包装成 confirmatory/deployable 证据。

开始前完整读取所有上级/当前 `AGENTS.md`、`pth_data/readme.md`、本文件、r015 报告/代码/manifest、当前协作状态。只用 HTTPS；核对 origin、当前/默认/upstream、完整 HEAD、工作树与 index，只允许 `git pull --ff-only`。HEAD 必须准确包含 `9f906fb3...`。工作树或 index 不干净、不能 fast-forward、授权路径冲突即按本文“未执行完毕”语义报告并停止；不得 stash、reset、clean、checkout、merge、rebase、删除未跟踪文件或触碰既有 stash。

## 1. C 侧已冻结的 r015 裁决

以下事实不得由服务器反向漂移：

1. r015 的 Git 提交本身为单 commit、19 条授权路径，父节点 `b1fb7df...`，`dis/B.md` blob 保持 `3181a862137918f1dd41677893937c12b3c39c28`；manifest 内 18 个非自引用 tracked blob 与 Git blob 的 bytes/SHA-256 一致。但该 manifest 只列 3 个 read-only inputs，且唯一 runtime output 没有 bytes/SHA，未满足“全部输入与 runtime 输出登记”契约。
2. r015 的 9,000 行同步 bootstrap 与其 unit/dataset CSV 在数值上自洽：6/6 unit 与 3/3 dataset 均为正支持；该事实当前只算“待独立闭合的 exploratory evidence”。
3. r015 报告所写 `FULL_COMPLETION/PASS_PROTOCOL_CLOSURE_R015` 不被 C 接受。其 validator 只逐值比对 bootstrap replicates，没有独立重算并核对 point estimate、CI、centered p、Holm、support 与最终 gate；也没有实质检查 30 条 r014 集合、零 eligible cluster、feature schema、禁止交集、seal hashes、实现偏差、claim hashes、单 commit 与授权 diff。
4. `authorized_diff_only` 是提交前 `b1fb7df..HEAD` 空差分的占位真值，不能证明最终 19 条提交范围。`zero_eligible_universe_*` 只检查 universe 非空，不能证明零 eligible cluster 被保留。
5. r015 telemetry 只记录 `workers=38/quota_percent=3840/start/end`，没有实际 CPU/RAM 样本；这违反 r015 “不得用 worker 字符串代替真实利用率”的要求。
6. 因而 r015 当前验收为 `FAIL_AUDIT_IMPLEMENTATION_R015`，执行语义是“报告误称全部完成”，不是合法早停，也不是 EQS 性能失败。r014 仍为 `FAIL_PROTOCOL_R014`；HRSC 仍为 `INCONCLUSIVE_INDEPENDENT_HRSC_R014`。

## 2. Phase A：来源、Git 与 manifest 独立复核

新增 `validate_r015_closure_r016.py`，不得 import r015 生成脚本或 validator 的判断函数，不得信任任何 CSV/JSON 状态字符串。动态输出并核对：

1. `b1fb7df... -> 9f906fb...` 父链、恰好一个 r015 commit、最终恰好 19 条且逐条等于 r015 授权集合；`dis/B.md` 在父/子提交的 blob 相同。
2. r015 evidence manifest 的 18 个非自引用 Git blob bytes/SHA-256；self 必须为 `N/A_SELF_REFERENCE`。
3. 枚举 Phase B/C 实际读取的每一个 r014 score、label、image universe、SODA map、seal、manifest、稿件和 ledger；逐项记录 live bytes/SHA/schema，并核对已有 prelabel/final manifest。不得把 r015 仅列出的 3 个 inputs 冒充完整输入集合。
4. r015 runtime manifest entry 缺少 bytes/SHA，必须明确记为 `R015_MANIFEST_OMISSION`。若原 `orientbench_r015/cluster_universe_r015.json` 存在则只读记录 hash；若不存在，允许从不可变输入在 r016 runtime 重建，不能修改 r015 runtime。重建集合必须与 r015 unit/dataset CSV 的 count/SHA 一致，否则 `FAIL_PROVENANCE_R016` 早停。
5. r014 prelabel seal、最终 manifest 与 r015 法证结论保持区分，不得用最终文件存在性恢复揭盲前 seal。任一已有期望 hash 不符立即早停，不得继续给 numeric acceptance。

## 3. Phase B：真正独立重算 r015 数值链

从 r014 sealed scores、原 matched labels、冻结 image universe 与 SODA tile-to-mother map 独立实现以下全部步骤：

1. 重建 DIOR-R、FAIR1M-v1.0 的全部 D_audit image universe 与 SODA-A 的全部 D_audit mother-scene universe；同 dataset 各 unit 集合必须相同。
2. 明确计算并输出“完整 universe 中 eligible row 数为零”的 cluster 数量和 sorted-set SHA，不能用 `len(universe)>0` 代替。
3. 按 `RandomState(20260807+d)`、固定 dataset 顺序与 1,000 replicates 重建同步 multiplicity；同 dataset 同 replicate 必须作用于所有 units/selectors。
4. 从 raw score/label 独立重算每个 unit 与 dataset 的 point Delta_NRC、percentile 95% CI、centered one-sided p、Holm-6/Holm-3、support、6/6 与 3/3 数量及最终 exploratory gate。
5. 对 r015 的 9,000 replicate 值和全部 summary/gate 字段逐字段比较；数值容差 `atol=1e-12, rtol=0`。不能只核对行数、文件存在或 PASS 字符串。

输出 `summary_recomputed_r016.csv`，并在 `validator_r016.json` 为每项保存 expected、actual、max_abs_error 与 witness。

## 4. Phase C：集合、seal、实现与稿件复核

必须动态完成而非消费 r015 布尔值：

1. 对每个 outer target 重建 `source_Dcal_fit/source_Dcal_calib/source_Daudit/target_Dcal/target_Daudit/target_feature_prelabel/target_scores_prelabel`；输出 row/image/mother counts、SHA 与所有禁止交集。fit/calib 含 source D_audit 或 target dataset 任一 label row即失败。
2. 读取 Parquet 实际 schema，确认 feature/score 不含 GT、angle_error、risk、GT_AR 或 split role；逐个核对 r014 prelabel seal 与 final manifest 的 feature/model/score bytes/SHA。
3. 对 doubled-angle axial dispersion、`u_axis`、association margin 单/零候选、sentinel、deterministic tie-break、w/h swap、0/90 boundary 提供源码行或动态 witness。r015 已发现的三个 deviation 必须保留，不能事后修代码或重评分。
4. 稿件必须保持 exploratory 边界、HRSC 跨零、leave-dataset 0/6 与 fixed-dose descriptive-only；检查 DIOR DOI、AOPG/DIOR-R 一手标识和 PSC 作者。正文不得出现内部 round/PASS/FAIL/authorized-path/venue-ready 词。
5. 对 claim ledger 每条 `claim_sha256` 重新计算，绑定稿件精确原句且该原句存在；检查旧失效 UCB 和 r014 错误 dataset CI 均未被消费。novelty matrix 不得把不准确来源标为 verified。

## 5. Phase D：资源证据与 validator 结果

- GPU=0、detector forward=0、training=0、selector refit=0、new target score=0。
- CPU 密集阶段将进程/子进程限制到 38 logical CPUs、BLAS=1；telemetry 必须记录有效 affinity/cpuset、实际 aggregate CPU%、RSS、worker 数、时间戳与 phase。开始/结束各一条；阶段超过 30 秒时每 30 秒一条。不得再用 `workers=38` 或 `quota_percent=3840` 代替实际利用率。
- `validator_r016.json` 成功 token 只能是 `VALID_R015_CLOSURE_R016`。它表示 r016 已补齐审计，不会追认 r015 当时的虚假 FULL_COMPLETION，也不证明 deployable selector。

若全部复核一致，r016 可采纳 `EXPLORATORY_CORE_SUPPORT_R015`；若任一 raw 数值、集合、hash、稿件或 gate 不一致，使用 `FAIL_VALIDATION_R016`，不得自行修 r015 或换统计口径。

## 6. 完成、早停与科学含义——回执不得含糊

“进程退出”不等于“把 `sug.md` 搞完”。唯一报告顶部必须逐行给出：

```text
instruction_fulfillment: ALL_REQUIRED_PHASES_COMPLETED | EARLY_STOP_WITH_UNRUN_PHASES | BLOCKED_WITH_UNRUN_PHASES | PROTOCOL_DRIFT
execution_completion: FULL_COMPLETION | INCOMPLETE_EARLY_STOP | INCOMPLETE_BLOCKED | PROTOCOL_DRIFT
round_verdict: PASS_R015_VALIDATOR_CLOSURE_R016 | FAIL_VALIDATION_R016 | FAIL_PROVENANCE_R016 | FAIL_AUDIT_IMPLEMENTATION_R016 | PROTOCOL_DRIFT_R016
r015_historical_acceptance: FAIL_AUDIT_IMPLEMENTATION_R015
r015_numeric_acceptance: EXPLORATORY_CORE_SUPPORT_R015 | REJECTED | NOT_EVALUATED
r014_formal_verdict: FAIL_PROTOCOL_R014
hrsc_status: INCONCLUSIVE_INDEPENDENT_HRSC_R014
last_completed_phase: ...
executed_required_phases: [...]
early_stop_trigger: NONE | ...
early_stop_scientific_meaning: NOT_APPLICABLE | PROVENANCE_FAILURE_NOT_PERFORMANCE_FAILURE | VALIDATION_FAILURE | PROTOCOL_FAILURE | BLOCKED_NO_SCIENTIFIC_VERDICT
unrun_required_phases: [] | [...]
all_required_work_completed: true | false
push_status: PUSHED | FAILED
```

合法分类：

- 只有 A-D、validator、manifest、报告、commit、push 全部完成，才可写 `ALL_REQUIRED_PHASES_COMPLETED/FULL_COMPLETION/all_required_work_completed:true`；失败的科学结果也可以是完整执行，但必须确实执行完所有无条件阶段和已触发的条件分支。
- 触发本文预定来源硬门并停止，写 `EARLY_STOP_WITH_UNRUN_PHASES/INCOMPLETE_EARLY_STOP`；这表示执行未完成。科学含义由 trigger 决定，来源失败不得写成 EQS 性能失败。
- 环境/资产/权限使任务无法继续，写 `BLOCKED_WITH_UNRUN_PHASES/INCOMPLETE_BLOCKED`，列出未运行阶段，不产生科学结论。
- 改 gate、改 r015、越权写路径、缺必做验证却声称完成，写 `PROTOCOL_DRIFT`。

最终对话首行必须完全采用以下二选一：

```text
执行完毕：dis/sug.md 全部必需阶段已完成（非早停）
未执行完毕：早停/阻塞/协议漂移；仍有必需阶段未运行
```

第二行必须且只能是 `dis/server_reports/orientbench-c-r016-20260808.md`。若第二种，第三行必须给出 `early_stop_trigger` 与 `unrun_required_phases`。禁止只写“执行完毕”或“脚本结束”。

## 7. 精确写入集合（10）

只允许创建/修改：

1. `claude_code_and_supervisor.md`（恰好 append 一个 r016 section）
2. `dis/server_reports/orientbench-c-r016-20260808.md`
3. `p3_selector/deployable_proxy_r016/protocol_r016.json`
4. `p3_selector/deployable_proxy_r016/scripts/validate_r015_closure_r016.py`
5. `p3_selector/deployable_proxy_r016/reports/summary_recomputed_r016.csv`
6. `p3_selector/deployable_proxy_r016/reports/set_and_schema_audit_r016.csv`
7. `p3_selector/deployable_proxy_r016/reports/validator_r016.json`
8. `p3_selector/deployable_proxy_r016/reports/resource_telemetry_r016.csv`
9. `p3_selector/deployable_proxy_r016/reports/evidence_manifest_r016.json`（必须登记本轮实际读取的全部输入与 runtime 输出，不得只列代表性文件）
10. `p3_selector/deployable_proxy_r016/docs/r015_validator_closure_r016.md`

新中间文件只进入 gitignored `outputs/persistent_artifacts/orientbench_r016/`。禁止修改 r015 及更早资产、稿件、数据、split、threshold、selector、checkpoint、`.gitignore` 和任何其它路径，尤其不得触碰 `dis/B.md`。

最终只做一个中文 commit；只显式暂存上述 10 条，LF，`git diff --check` 零输出。manifest 最后生成，self=`N/A_SELF_REFERENCE`。使用 HTTPS 普通 push 当前分支，不改 origin、不 force。push 失败时保留本地 commit，必须按“未执行完毕”回执，不得把本地 commit 当服务器已交付。
