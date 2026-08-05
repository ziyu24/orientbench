# OrientBench 服务器任务：A1 不可行性的功效—分数归因门

- round: `orientbench-c-r004-20260805`
- scientific snapshot: `cb0a259f81d9d0cd3af27f514a9e94c75ddf9cbd`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`
- previous server report: `dis/server_reports/orientbench-c-r003-20260805.md`
- 唯一服务器报告路径: `dis/server_reports/orientbench-c-r004-20260805.md`

## 1. 单一科学问题

主风险 `geometry_normalized_severe` 的 144 个 score-endpoint-budget rows 中有 142 个 infeasible。冻结现有协议和全部数据/阈值后，这些不可行中有多少是：

1. 当前 calibration scene 数下，即使零损失也不可能通过的结构性功效上限；
2. 理想 outcome oracle 在冻结 coverage grid 上仍不能通过的事件基率/网格上限；
3. oracle 可以通过、但实际 score 不能通过的排序限制；
4. 形式认证后仍达不到 practical coverage/count 的限制？

本轮只做既有证据的零 GPU 归因，不训练、不推理、不下载新资产、不改论文。它不新增或修改正式协议；只判断当前“现有分数导致多数不可认证”的归因能否保留。

## 2. 不可改写的边界

1. [`a1_protocol_frozen.json`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_protocol_frozen.json)、原 A1/A6 结果、主稿、split、score direction、coverage grid、absolute alpha、`delta=0.1`、practical thresholds 和 missing-TTA policy 均逐字节不变。
2. A=`A_MEASUREMENT_ONLY`；原 A6=`NO_ELIGIBLE_CONFIRMATORY_UNIT`；r003=`FAIL_NO_A6R_ASSET`，但带一项共享路径合规缺陷；B 永久退出主 claim。
3. primary estimand 是 conditional matched-orientation scene risk，不得把本轮结果改称 full-output deployment guarantee。
4. 主归因只使用冻结 `delta=0.1`；`delta=0.05`、`0.01` 只做功效敏感性，不能替代主门。
5. target-GT-free scores 固定为 `detection_score`、`tta_circular_consistency`、`source_supervised_leave_geometry`。`target_gt_nonlinear_geometry_upper_bound` 单独列为 diagnostic upper bound，不混入主多数门。

## 3. 开始与合规修复

1. 只允许 fast-forward 同步；记录实际完整 HEAD 并证明 ancestry 包含 scientific snapshot。tracked/index 不洁净、远端/所有权冲突或不能 fast-forward 时停止。
2. 先完整读取仓库规则、A1 冻结协议、`run_a1_a3.py`、A1 reproduction status、现有 frontier/schema、r003 gate/manifest/report 和迁移交接。
3. 在任何分析前，对 `audit_a6r_assets_r003.py` 做唯一允许的历史源代码修复：删除硬编码的服务器绝对 dataset 路径及账号段，改为未解析值不会写入共享产物的 CLI 参数或环境变量逻辑别名；不得在日志、manifest、报告或异常中持久化解析后的绝对路径。旧 r003 CSV/JSON/报告不得重写或重跑。
4. 把 `protocol_drift=False` 的硬编码改为由可观测前置条件与共享输出 sanitizer 派生；训练/推理/风险/下载计数若仍无法 instrumentation，明确标为 `STATIC_CONTROL_FLOW_AUDIT`，不得伪称运行时计数器证明。
5. 对本轮所有新增文件、被整体修改的文件及 append-only 文件的新增 diff hunks 扫描账号模式、机器名、Unix/Windows 绝对路径和凭据；不得因历史文件中未触碰的既有文本误报。新增内容命中即 `PROTOCOL_DRIFT` 并停止提交。

## 4. 权威输入与复算前置门

至少登记并验证以下输入的 bytes、SHA-256 与 Git blob/既有 reproduction hash；服务器侧大型原物仅用仓库相对路径或逻辑别名：

- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_protocol_frozen.json`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/run_a1_a3.py`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_a3_reproduction_status.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_guaranteed_frontier_all_alpha.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a2_scene_level_ltt_frontier.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a2_scene_event_frontier.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a2_eligible_scene_universe.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_trivial_infeasible_summary.csv`
- `scripts/m069_common.py`、`orientbench/data/splits.py` 及 `M.verify_fullval_lineage()` / `M.load_cell()` 实际读取的六单元原物

先独立重建 576 行的 identity key：`evaluation_unit|score|risk_endpoint|alpha_label`，并逐字段比较现有表的 alpha、trivial、feasible、practical、calibration/audit scene count、selected coverage/count 与 UCB。行集合、主字段或 lineage 任一不一致时输出 `INCONCLUSIVE_POWER_DECOMPOSITION`，不得继续给出 headline 归因。

## 5. 冻结的功效与 oracle 定义

### 5.1 Zero-loss optimistic envelope

对每个 evaluation-unit × endpoint × alpha：

- 使用该角色中**全部 eligible calibration scenes** 作为可获得的最大 exchangeable `n`；
- 计算 `HB_UCB(mean=0,n,delta)`；scene-event 另算 `CP_UCB(k=0,n,delta)`；
- 这是对任何 score 最有利的结构性下界，不是经验结果；
- 若在 `delta=0.1` 下该 optimistic HB UCB 仍大于 alpha，则该行标记 `STRUCTURAL_POWER_LIMIT`。不得把它归因于 score。

同时对 `delta=0.05` 与 `0.01` 重算 sensitivity，但不改变主分类。

### 5.2 Outcome-oracle envelope

只作 diagnostic upper bound：使用真实 endpoint event 构造 larger-is-better 的完美 instance oracle。对每个完整 cell 的持久化行号 `i=0..N-1`，固定 `oracle_score=(1-event)+1e-6*(1-i/max(N-1,1))`；因此所有低风险实例严格排在高风险实例之前，同风险时只按全 cell 的持久化行号稳定排序，且同一数值定义跨 fit/calib/audit 应用。阈值仍只从 D_fit 与冻结 coverage grid 产生；calibration 仍按 fixed-sequence 从低覆盖到高覆盖，首失败即关闭；audit 不参与阈值或门选择。

oracle 不得覆盖或混写到四个原 score，不得形成 deployable claim。若 zero-loss 结构上可行但该 oracle 在冻结 grid/经验事件下仍不可行，标记 `ORACLE_DATA_OR_GRID_LIMIT`。

### 5.3 互斥归因顺序

对 576 行按以下顺序给出一个且仅一个 attribution：

1. `TRIVIAL_BUDGET`：`alpha >= r_fit`；
2. `STRUCTURAL_POWER_LIMIT`：nontrivial 且 optimistic zero-loss HB UCB `> alpha`；
3. `ORACLE_DATA_OR_GRID_LIMIT`：结构上可行，但 outcome oracle 无 fixed-sequence certified candidate；
4. `SCORE_RANKING_LIMIT`：oracle 可认证，实际 score 不可认证；
5. `PRACTICAL_COVERAGE_LIMIT`：实际 score 形式非平凡认证，但 audit nonempty rate、instance coverage 或 selected count 未同时达到冻结 practical gate；
6. `CERTIFIED_PRACTICAL`：实际 score 非平凡且 practical；
7. `FORMAL_OTHER`：只用于捕获实际表中未被以上状态覆盖的形式结果；出现时必须解释并把主 gate 置为 inconclusive，不能静默吞掉。

分类必须分别汇总：全部 576 行、主风险 144 行、主风险 target-GT-free 108 行、diagnostic upper bound 36 行；并按 unit、score、alpha 类型与 alpha 值交叉报告。

## 6. 预注册主 gate

主分母固定为：`geometry_normalized_severe`、target-GT-free 三类 score、nontrivial、现有表 `feasible=False` 的行。

- `PASS_SCORE_LIMIT_DOMINANT`：其中严格超过 50% 被归为 `SCORE_RANKING_LIMIT`，且 576 行 parity、lineage、互斥/完备性全部通过。
- `FAIL_SCORE_LIMIT_DOMINANT`：parity 与归因有效，但 `SCORE_RANKING_LIMIT` 占比不超过 50%。论文必须删除“现有可部署分数是多数不可认证的主因”，改成实际占多数的 power/data/grid boundary；这不是删负结果。
- `INCONCLUSIVE_POWER_DECOMPOSITION`：主分母为 0，或原物/lineage/identity/parity 缺失，oracle 次序或 UCB 不能按冻结定义复算，或出现未解释的 `FORMAL_OTHER`。
- `PROTOCOL_DRIFT`：修改冻结文件/split/threshold/score direction/coverage grid，读取或写入未授权资产，执行训练/推理/下载，或共享产物泄露账号、机器、凭据、绝对路径。

无论 PASS 或 FAIL，都必须报告 numerator、denominator、精确比例及全部 attribution counts；不得只给标签。

## 7. 早停与资源

1. Git/所有权/ancestry/共享路径 sanitizer 失败：立即 `PROTOCOL_DRIFT` 停止。
2. 六单元 lineage 或 576 行 parity 失败：立即 `INCONCLUSIVE_POWER_DECOMPOSITION` 停止，不运行 oracle。
3. 归因不互斥、不完备或出现未解释 `FORMAL_OTHER`：inconclusive。
4. 本轮 GPU 使用必须为 0；训练、推理、风险资产下载和 RSAR 下载均为 0。
5. 原物装载与大表计算属于 CPU 密集任务时，按仓库规则使用不少于 80% 可用 CPU；若受 I/O 或实现串行限制，报告实测利用率与理由，不得伪造并行。
6. 不读取或下载 D7/PCP-OBB、pcbobb、pcbobb_beyond、pcbobb_score_study。它们不能改变本门。

## 8. 授权写入范围

只允许：

- 修改 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a6r_assets_r003.py`（仅第 3 节合规修复）；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a1_power_decomposition_r004.py`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_power_envelope_r004.csv`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_oracle_feasibility_r004.csv`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_failure_attribution_r004.csv`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_power_sensitivity_r004.csv`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_power_gate_r004.json`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_power_manifest_r004.json`；
- append-only 修改 `claude_code_and_supervisor.md`，只记录 r004 的逻辑路径、gate 和停止状态，不写服务器路径/账号/机器；
- 新增唯一报告 `dis/server_reports/orientbench-c-r004-20260805.md`。

不得修改旧 A1/A6 表、主稿、协议、配置、checkpoint、数据、`dis/B.md`、`dis/C.md`、`dis/sug.md`、`dis/review_state.json` 或任何旧服务器报告。需要其它写入时标记 `PROPOSED_DEVIATION` 并停止。

## 9. 必须报告的证据

1. 576 行 parity 比较与不一致计数；六单元 raw lineage/hash。
2. 每行 `n_max`、zero-loss HB/CP UCB、主 delta 与 sensitivity delta。
3. oracle 的 fit threshold、calibration fixed-sequence 过程、chosen coverage 或第一个失败点；audit 仅作描述。
4. 互斥 attribution、四类汇总和主 gate 的精确分子/分母。
5. 对当前 `142/144` 的正确改写建议：哪些是 trivial、structural、oracle/data/grid、score、practical；不把重叠计数写成互斥证据。
6. manifest：scientific snapshot、execution HEAD、实际命令、输入/输出 bytes、SHA-256、Git blob、逻辑路径、CPU/GPU、训练/推理/下载计数和合规 sanitizer 结果。manifest 自身以提交 Git blob 固定，不做伪自哈希。
7. 最弱环节、置信度、反证条件及下一步。r004 不授权获取 RSAR；只有 C 裁决后才进入独立 acquisition round。

## 10. Git 与最终回复

运行 JSON/CSV/schema/row-count 检查、`git diff --check`、普通与 staged diff。确认仅授权路径变化且 `dis/B.md` blob 未变。只显式暂存授权文件，以中文 commit message提交并普通 push；禁止 merge/rebase/reset/clean/force。

最终回复必须恰好两行，不加代码围栏、项目符号或第三行：

第一行只能是 `执行完毕` 或 `未执行完毕`。

第二行只能是 `dis/server_reports/orientbench-c-r004-20260805.md`。
