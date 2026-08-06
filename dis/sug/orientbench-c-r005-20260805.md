# OrientBench 服务器任务：A1 scene-functional oracle 支配性修复门

- round: `orientbench-c-r005-20260805`
- scientific snapshot: `6955bbc49094a09696c1025e3034f74b74910857`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`
- previous server report: `dis/server_reports/orientbench-c-r004-20260805.md`
- 唯一服务器报告路径: `dis/server_reports/orientbench-c-r005-20260805.md`

## 1. 单一科学问题

r004 的程序输出为 `SCORE_RANKING_LIMIT=0/90`，但其 instance oracle 并不支配实际 score selection：144 个独立 oracle 单元全部在 1% coverage 首点失败，而现有表中存在 `actual_feasible=True`、`oracle_primary_feasible=False` 的行。冻结原 A1 与 r004 历史产物不变，本轮回答：

> 对 conditional matched-orientation scene risk，能否构造一个对任意实际 selected subset 都不劣、可证明支配的 target-outcome relaxed attainable envelope；在该 envelope 下，主分母 90 行中有多少是结构性功效界、经验 scene-support 界、selection/protocol gap，以及“score 排序占多数”还能否由上下界裁决？

本轮只做已有六单元原物的零 GPU 统计审计，不训练或推理 detector，不拟合或预测诊断回归器，不下载新资产，不改论文，不读取 RSAR 或其它个人项目。它不覆盖 A1/r004；只把 r004 literal gate 与因果解释分开。

## 2. 冻结边界

1. `a1_protocol_frozen.json`、split、main mask、mother-scene 规则、四个 endpoint、四个原 score、score direction、coverage grid、absolute/relative alpha、`delta=0.1`、practical thresholds、原 A1/A6/r003/r004 输出与主稿逐字节不变。
2. primary estimand 仍是 conditional matched-orientation scene risk；不得改称 full-output deployment guarantee。
3. r004 的 `FAIL_SCORE_LIMIT_DOMINANT` 只保留为 frozen 1%-entry fixed-sequence literal gate；不得重命名、覆盖或回写旧 JSON/CSV/报告。
4. target-GT-free scores固定为 `detection_score`、`tta_circular_consistency`、`source_supervised_leave_geometry`；`target_gt_nonlinear_geometry_upper_bound` 只作 diagnostic witness。
5. 主分母固定为 `geometry_normalized_severe`、三个 target-GT-free score、nontrivial、原表 `feasible=False`，预期 90 行；计数不符即 inconclusive。
6. r005 relaxed envelope 可使用 calibration endpoint outcome 与 scene ID，仅用于可达性证明；它不是 inference-available score，不是新正式协议，也不得参与 audit 选择。

## 3. 开始、Git 与前置门

1. 只允许 fast-forward 同步；记录完整实际 HEAD，证明 ancestry 包含 scientific snapshot。tracked/index 不洁净、远端/所有权冲突或不能 fast-forward 时停止。
2. 完整读取仓库规则、本任务、A1 冻结协议、`run_a1_a3.py`、r004 script/gate/manifest/四张 CSV/报告、A1 frontier 与六单元 lineage 原物。
3. 核验 r004 结果提交相对 parent 的路径集合、旧 A1/A6/r003 blob 不变、r004 九个非自引用输出的 bytes/SHA-256/Git blob、36 个输入身份和六单元 lineage。任一不一致：`INCONCLUSIVE_SCENE_ENVELOPE`，不得继续归因。
4. 从原 `a1_guaranteed_frontier_all_alpha.csv` 与 r004 产物独立复算 576 identity、实际状态、结构功效标签和 r004 oracle 标签；行数、唯一键或字段不符即 inconclusive。
5. 不运行 r004 的 geometry regressor parity 重建。本轮模型操作预算严格为：detector fit/predict=`0/0`，diagnostic regressor fit/predict=`0/0`。只允许直接的数组、分组、阈值和 UCB 计算。

## 4. 先把 r004 反例机器化

生成一行一个实际 identity 的支配性反例表，至少记录：identity、unit、score、endpoint、alpha、trivial、actual feasible/practical/coverage/count/UCB、r004 oracle feasible/first failure/chosen coverage、r004 attribution。

同时按唯一 `unit × endpoint × alpha × coverage` 重建 r004 persistent-row outcome oracle 的完整 coverage trace，共 `6 × 4 × 6 × 13 = 1872` 行：

- `oracle_score=(1-event)+1e-6*(1-i/max(N-1,1))`，阈值只从 D_fit 相同 coverage quantile 得到，再把同一数值阈值用于 calibration；
- 每个 coverage 必须保存 fit threshold、selected instances、nonempty calibration scenes、conditional scene risk、HB UCB、pointwise pass、fixed-sequence prefix 是否仍 open；
- audit 不用于阈值或 gate；本 trace 不需读取 audit outcome。

必须报告并交叉核对：

- `actual_feasible=True && r004_oracle=False` 的总数、其中 practical 数，以及 primary 反例；
- 144 个独立 oracle 单元的 1% 首败数；首败后任一更高 coverage pointwise 通过数；
- primary 36 单元的 later-pass 数；
- 主分母中原 `ORACLE_DATA_OR_GRID_LIMIT` 行的 later-pass 数。

这些是 r004 的诊断复算，不是新主门。若复算与 r004 CSV/原 frontier 不能闭环，置 `INCONCLUSIVE_SCENE_ENVELOPE`。

## 5. 严格支配的 scene-functional attainable envelope

### 5.1 定义

对每个 `evaluation unit × endpoint`，只在冻结 main mask 与 calibration role 中计算。设 eligible calibration scenes 为 `s=1..N`，二元 endpoint event 为 `e_i∈{0,1}`。对每个 scene 定义：

`m_s = min{e_i : i 是该 scene 的 eligible calibration instance}`。

这等价于在该 scene 中只选一个风险最小的实例；若 scene 至少有一个 non-event，则 `m_s=0`，否则为 1。把 `(m_s, stable_scene_id)` 升序排序。对每个 `n=1..N`：

- 取前 n 个 scene，每个只取实现 `m_s` 的一个实例；
- `mean_n = sum(m_s)/n`；
- 用与 A1 完全相同的 `M.hb_ucb(mean_n,n,delta)` 计算 `ucb_n`；
- primary 使用 `delta=0.1`，`0.05/0.01` 只作 sensitivity。

在每个 `unit × endpoint × alpha` 下，从全部 n 中选择最小 `ucb_n`；并列时依次选择更小 mean、更大 n、稳定 scene 顺序。保存 chosen n、zero-risk scene 数、all-event scene 数、mean、UCB、alpha 与 feasibility。

### 5.2 为什么它必须支配实际 selection

对任一实际 selected subset，设其 nonempty calibration scene 数为 n。每个实际 scene 的 selected-event mean 不小于该 scene 的 `m_s`；在同样 n 下，选择全体 scene 中最小的 n 个 `m_s` 又不劣于实际 scene 集合。HB UCB 对固定 n 的 empirical mean 单调。因此本 envelope 在全部 n 上取最小值后，UCB 必不大于任一实际候选的 UCB。

程序必须用两种方式验证该证明：

1. 状态支配：全部原表 `actual_feasible=True` 的行，其对应 envelope 必须 `feasible=True`；
2. 数值支配：对可得的实际 chosen candidate，`envelope_min_ucb <= actual_certified_risk_ucb + 2e-6`。

出现任何状态支配反例即 `FAIL_SCENE_ENVELOPE_DOMINANCE` 并早停，不得给新的 failure attribution。数值支配不一致必须列出全部行；若不是纯六位小数舍入可解释，亦 fail。

### 5.3 解释边界

该 envelope 是使用 calibration outcome、放松 score/fit-threshold/coverage-grid/fixed-sequence/practical-coverage 约束后的可达性下界。它能证明“即使任意 target-aware scene selection 也不可能通过”，或证明“形式上存在可通过的 scene subset”；它不能把后者单独归因于 score，也不能作为部署方法。

## 6. 状态优先的互斥归因与 score 上下界

对 576 行按下列顺序给唯一标签；成功状态必须先于 failure cause，不能再被 oracle precedence 吞掉：

1. `TRIVIAL_FORMAL_CERTIFIED`: trivial 且 actual feasible；
2. `TRIVIAL_BUDGET_INFEASIBLE`: trivial 且 actual infeasible；
3. `CERTIFIED_PRACTICAL`: nontrivial、actual feasible 且 practical；
4. `PRACTICAL_COVERAGE_LIMIT`: nontrivial、actual feasible 但不 practical；
5. `STRUCTURAL_POWER_LIMIT`: nontrivial、actual infeasible，且 r004 zero-loss structural limit 为真；
6. `EMPIRICAL_SCENE_SUPPORT_LIMIT`: nontrivial、actual infeasible、非 structural，且 dominating envelope infeasible；
7. `SELECTION_PROTOCOL_GAP`: nontrivial、actual infeasible、非 structural，且 dominating envelope feasible；
8. `FORMAL_OTHER`: 只捕获未覆盖状态；出现即主结论 inconclusive。

其中 `SELECTION_PROTOCOL_GAP` 只表示 relaxed scene selection 可达、当前 formal score sequence 不可达，混合 score ranking、D_fit→calibration transfer、coverage grid、1% entry、fixed-sequence order 和 policy class，禁止简写为 `SCORE_RANKING_LIMIT`。

对主分母 90 行另给 score-cause bounds：

- conservative lower witness：同一 `unit × endpoint × alpha` 下，另一个 target-GT-free score 在原 frozen protocol 中 actual feasible；
- diagnostic witness：仅 target-GT diagnostic score feasible，单独报告，不并入 conservative lower；
- upper bound：所有 `SELECTION_PROTOCOL_GAP` 行都暂视为可能由 score 造成；
- 输出 conservative lower/90、加 diagnostic witness 的 sensitivity lower/90、upper/90。

只有 conservative lower 严格大于 50% 才能给 `PASS_SCORE_LIMIT_DOMINANT_LOWER_BOUND`；只有 upper 不大于 50% 才能给 `FAIL_SCORE_LIMIT_DOMINANT_UPPER_BOUND`；否则给 `INCONCLUSIVE_SCORE_CAUSAL_ATTRIBUTION`。这一 score-cause gate 是 r005 的科学结论；不得用 r004 的 0/90 或 any-grid 57/90 替代。

## 7. r005 最终 gate

结构 gate 只能为：

- `PASS_SCENE_ENVELOPE_VALID`: 输入、lineage、r004 复算、互斥分类和支配证明全部通过；
- `FAIL_SCENE_ENVELOPE_DOMINANCE`: 新 envelope 对任一实际 feasible 行不支配；
- `INCONCLUSIVE_SCENE_ENVELOPE`: 输入/hash/schema/identity/trace/分类不闭环、主分母非 90、出现 `FORMAL_OTHER` 或关键字段不可复算；
- `PROTOCOL_DRIFT`: 修改冻结/历史文件、越权读写、执行模型 fit/predict、训练/推理 detector、下载、GPU、RSAR/其它个人项目读取，或共享产物泄漏私有信息。

必须同时给出独立的 score-cause gate，以及 formal r004、pointwise any-grid 和 relaxed attainable envelope 三层结果；三层口径不得混写。

## 8. 早停、资源与共享安全

1. Git/所有权/ancestry/授权路径失败：立即停止。
2. r004 身份、576 行、主分母 90 或 1872 trace 不闭环：inconclusive，停止归因。
3. 新 envelope 有任何 dominance violation：fail，停止 attribution，不得调参修补。
4. GPU、下载、detector fit/predict、diagnostic regressor fit/predict、RSAR 读取均必须为 0；直接统计循环不算模型操作。
5. CPU 密集步骤按仓库规则使用不少于 80% 可用 CPU；若实现/I/O 串行，报告线程预算和限制，不伪报实际利用率。
6. 对全部新增文件和 append diff 执行 bounded sanitizer，至少覆盖 Windows drive/UNC 与 Unix `/home`、`/Users`、`/root`、`/srv`、`/opt`、`/scratch`、`/workspace`、`/tmp`、`/var`、`/mnt`、`/data` 绝对路径，常见 token/password/Bearer/私钥/连接串，以及运行时账号和机器名。sanitizer 是有界检查，不得称为完整泄漏证明；命中即 protocol drift。

## 9. 授权写入范围

只允许：

- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a1_scene_oracle_r005.py`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_r004_dominance_violations_r005.csv`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_coverage_trace_r005.csv`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_scene_attainable_envelope_r005.csv`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_failure_bounds_r005.csv`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_scene_oracle_gate_r005.json`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_scene_oracle_manifest_r005.json`；
- append-only 修改 `claude_code_and_supervisor.md`，只记录 r005 逻辑路径、结构 gate、score-cause gate 与停止状态；
- 新增唯一报告 `dis/server_reports/orientbench-c-r005-20260805.md`。

不得修改任何旧脚本、旧报告、旧 CSV/JSON、主稿、协议、配置、checkpoint、数据、`dis/B.md`、`dis/C.md`、`dis/sug.md`、`dis/review_state.json` 或旧服务器报告。需要其它写入时标记 `PROPOSED_DEVIATION` 并停止。

## 10. 必须持久化和报告的证据

1. r004 输入/输出身份、576 identity、22 类支配反例的完整机器表与 primary 反例；若独立复算得到不同数量，以实际证据为准并置 inconclusive，不得迎合预期。
2. 1872 行 coverage trace；至少汇总 1% 首败、later-pass 的 105/144、25/36、主分母 57/57 是否成立。
3. 每个 `unit × endpoint × alpha` 的 N、zero/all-event scene 数、全部 n 搜索、chosen n/mean/UCB/feasible；可把逐 n 轨迹压缩为机器可复算的充分统计，但脚本必须能确定性重建。
4. 新 envelope 的状态和数值 dominance 检查；全部违反行而非只给计数。
5. 576 行状态优先归因、全部/primary/target-GT-free/diagnostic 分区和主分母 90 的精确计数。
6. score lower/diagnostic/upper bounds、精确比例、最终 score-cause gate；不得把 `SELECTION_PROTOCOL_GAP` 改称 score failure。
7. detector fit/predict、diagnostic regressor fit/predict、下载、GPU、RSAR read 分开的计数与证据来源。静态审计必须标成 `STATIC_CONTROL_FLOW_AUDIT`。
8. manifest：scientific snapshot、execution HEAD、实际命令、输入/输出 bytes、SHA-256、Git blob、逻辑路径、资源/操作计数、bounded sanitizer、授权路径；manifest 自身以结果提交 Git blob 固定，不做伪自哈希。
9. 最弱环节、置信度、反证条件与下一步。即使 envelope valid，本轮也不授权 RSAR acquisition 或推理。

## 11. 校验、提交与最终回复

运行 JSON/CSV/schema/row-count/identity/path/link 检查、`git diff --check`、普通与 staged diff。确认只含授权路径，所有旧 r004 blob 与 `dis/B.md` blob 不变。只显式暂存授权文件，以中文 commit message提交并正常 push；禁止 merge/rebase/reset/clean/force。

最终回复必须恰好两行，不加代码围栏、项目符号或第三行：

第一行只能是 `执行完毕` 或 `未执行完毕`。

第二行只能是 `dis/server_reports/orientbench-c-r005-20260805.md`。
