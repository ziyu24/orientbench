# OrientBench 服务器任务：标准 split-FST 的有效性与发展广度门

- round: `orientbench-c-r006-20260805`
- scientific snapshot: `60142448ff1f461531ad1eb2cd0c17785e782350`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`
- previous server report: `dis/server_reports/orientbench-c-r005-20260805.md`
- 唯一服务器报告路径: `dis/server_reports/orientbench-c-r006-20260805.md`

## 1. 单一科学问题

r005 已证明主分母 90 行中 33 行受 structural scene-count power 限制，57 行在完全 target-aware、放松 grid/sequence/practical 后存在 selection/protocol headroom；但 score 因果区间仍为 `0/90–57/90`。本轮回答：

> 使用文献已有的 split fixed-sequence testing，而不是 calibration-outcome any-grid 挑点，能否在保持 finite-sample FWER control 的前提下，把 r005 的形式 headroom 转化为有广度的 nontrivial target-GT-free certified-practical development evidence？

本轮是 A–F 已暴露数据上的 retrospective protocol development，不是 confirmatory 结果。split-FST、Holm、Bonferroni/LTT 均为已有统计工具，不得申报 OrientBench 方法首创。通过只允许冻结下一版 protocol 并进入独立 RSAR acquisition；不允许宣称 TGRS ready。

## 2. 不可改写的边界

1. `a1_protocol_frozen.json`、原 split、main mask、scene/tile unit、endpoint、四个 score 定义与方向、coverage grid、absolute/relative alpha、`delta=0.1`、tie-break、missing-TTA policy、practical thresholds、A1/A6/r003/r004/r005 产物和主稿逐字节不变。
2. r004 literal gate、r005 relaxed envelope 与 r006 split-FST 必须分层报告；r006 不覆盖历史正式结果。
3. target-GT-free score 固定为 `detection_score`、`tta_circular_consistency`、`source_supervised_leave_geometry`。`target_gt_nonlinear_geometry_upper_bound` 只作 diagnostic，不进入 primary breadth gate。
4. A–F 已经暴露，全部 r006 结果标记 `RETROSPECTIVE_DEVELOPMENT_ONLY`；不得改称前瞻、独立确认或 prevalence。
5. RSAR、D7/PCP-OBB、pcbobb、pcbobb_beyond、pcbobb_score_study 均不得读取或下载。
6. primary estimand 仍是 conditional matched-orientation scene/tile risk；不得称 full-output deployment guarantee。

## 3. 开始、Git 与 provenance 前置门

1. 只允许 fast-forward 同步；记录完整实际 HEAD，证明 ancestry 包含 scientific snapshot。远端/所有权冲突、tracked/index 不洁净或不能 fast-forward 时停止。
2. 完整读取仓库规则、本任务、A1 frozen protocol/implementation、r004 与 r005 script/gate/manifest/CSV/report、原 frontier、六单元 raw lineage 与迁移交接。
3. 核验 r005 结果提交的 9 个授权路径、8 个非自身输出 bytes/SHA-256/Git blob、46 个登记输入、旧 r004 blob 与六单元 lineage。任一身份不闭环：`INCONCLUSIVE_SPLIT_FST`。
4. 重建原 576 frontier 并逐字段 parity；必须与 r004 的 576 行和冻结字段一致。允许且必须显式报告 score-regressor reproduction：六单元各 target/source 两个固定 HistGradientBoostingRegressor，共 fit/predict=`12/12`；detector fit/predict=`0/0`。不得把两类操作混写。
5. r005 历史脚本不修改。新实现的 Bernoulli/scene-event HB 路径直接保留累计整数 `k`，不得用 `ceil(n*float_mean)` 恢复事件数；用 scalar/exact-integer 两条实现验证全部候选，而非只抽 probes。

## 4. 三个预注册比较臂

所有臂都使用冻结的 13 个 coverage threshold、相同 score 和相同 scene risk。每个 family 固定为：

`evaluation unit × score × endpoint × alpha`。

不同 score family 分别控制，不在 D_cal 后选择“最好 score”。论文必须同时报告 row 数与唯一 `unit × endpoint × alpha` 情境数。

### 4.1 Primary：D_fit-learned split fixed-sequence

对每个 family 的每个 coverage candidate：

1. threshold 只从 D_fit 该 score 的冻结 quantile 产生；
2. 只在 D_fit selected nonempty scenes 上计算 bounded scene loss、`n_fit`、`Rhat_fit` 与冻结 HB p-value `p_fit=hb_pvalue(Rhat_fit, alpha, n_fit)`；`n_fit=0` 时 p-value 固定为 1；
3. 在查看/使用 D_cal outcome 前，把候选顺序确定为以下稳定 tuple 升序：

`(p_fit, -n_fit, -target_coverage, original_coverage_grid_index)`。

顺序完全由 D_fit 决定。必须保存全 13 行 order、threshold、D_fit sufficient statistics、排序 tuple 和 order-file SHA-256。做 outcome-taint 单元检查：任意置换 D_cal/D_audit endpoint outcome，序列化 order bytes 必须不变；失败即 `FAIL_SPLIT_FST_VALIDITY`。

在 D_cal 中只按已冻结顺序执行：

- 计算 candidate 的 scene-risk HB p-value；`p_cal <= delta=0.1` 为拒绝不安全 null，即 certified pass；
- 从 order 第一个开始，遇到第一个 fail/accept-null 后永久关闭后续 sequence；
- 在关闭前的 passed prefix 中选择 target coverage 最大者；若无通过候选则 infeasible；
- audit 不参与 order、threshold、calibration pass 或 candidate 选择。

relative alpha 仍由 D_fit unselected base risk产生；给定 D_fit 后视为固定。不得从 D_cal 重新估计 alpha。

### 4.2 Historical baseline

按原 A1 的 coverage 从 1% 到 100% ascending fixed-sequence 重算；必须与冻结 frontier parity。它只作历史 baseline，不允许改变其 gate。

### 4.3 Pre-registered sensitivity：Holm

对同一 score family 的 13 个 D_cal HB p-values做标准 Holm step-down，family-wise `delta=0.1`；在 Holm 拒绝集中选最大 coverage。Holm 是 sensitivity，不得在看到结果后替换 primary；若 primary fail、Holm pass，只能记为下轮候选，不改变 r006 gate。

any-grid pointwise pass 继续只作无多重控制的 diagnostic，不得称 certified。

## 5. Practical 与 audit 口径

对 primary split-FST 和两个比较臂都记录：

- calibration chosen coverage、threshold、nonempty scenes、risk、UCB/p-value；
- audit conditional risk、risk UCB、nonempty scene rate、selected instance coverage、selected count；
- 原 practical gate：nonempty scene rate `>=0.1`、selected instance coverage `>=0.1`、selected count `>=100`、alpha nontrivial；
- `audit_direction_consistent = audit conditional empirical risk <= alpha`，作为 r006 breadth 的额外发展一致性门，不改写原 formal guarantee。

另生成 target-aware `zero-event practical witness`：同一 outcome score `1-event` 在 calibration/audit 均选择所有 event=0 的 eligible instances，报告 calibration UCB 与两角色的 scene rate/coverage/count。它只证明是否存在 zero-risk、高覆盖的 outcome-aware witness；不是 deployable score、不是完整 constrained optimum，失败也不能单独证明无 headroom。

## 6. FWER 证明与模拟 sanity gate

### 6.1 必须写出的证明前提

报告必须明确：D_fit 与 D_cal 在冻结 exchangeable unit 下不重叠；order、threshold、alpha 在给定 D_fit 后固定；D_cal 只用于合法 p-value；fixed-sequence 在首个未拒绝 null 处停止。条件于 D_fit，任何第一个 true null 被错误拒绝的概率不超过 `delta`，故 strong FWER 不超过 `delta`。这属于已有 LTT/split-FST 论证，不得写成新定理。

若 scene/tile split overlap、D_cal outcome 进入 order、p-value 不是 super-uniform，或代码选择与上述证明不一致，置 `FAIL_SPLIT_FST_VALIDITY`。

### 6.2 冻结模拟

- seed: `20260805`
- replicates: 每场景 `50000`
- scenarios: 六 evaluation units × 三 target-GT-free scores × 六 alpha labels，共 108；endpoint 固定 primary；每个 candidate 使用实际 D_fit/D_cal nonempty-scene n profile；
- global-null risk 固定为该 family alpha；fit 与 calibration 的 Bernoulli scene losses独立生成，candidate 间允许本 sanity 使用独立 draws；
- 用模拟 fit losses生成 primary order，再在独立 calibration losses执行 split-FST；Holm 同时模拟；
- 每个 scenario 报 empirical FWER、false-rejection count 与 95% Clopper-Pearson upper bound；分块向量化，不改变随机流。

validity simulation pass：全部 108 个 split-FST scenario 的 95% CP upper `<=0.105`；Holm 单列同一标准。若 primary 任一 scenario 超标，`FAIL_SPLIT_FST_VALIDITY`。模拟只是 implementation sanity；理论前提失败时不能靠模拟补救。

## 7. 预注册 gate

### 7.1 Structure/validity gate

- `PASS_SPLIT_FST_VALIDITY`: provenance/parity/lineage、D_fit-only order taint test、exact-integer HB、理论前提和全部 primary FWER simulation 通过；
- `FAIL_SPLIT_FST_VALIDITY`: order 使用 D_cal/audit outcome、split/FWER/p-value/taint 任一失败；
- `INCONCLUSIVE_SPLIT_FST`: 输入/hash/schema/identity/parity、模拟或关键字段不能闭环；
- `PROTOCOL_DRIFT`: 修改冻结/历史文件、越权读写、detector 训练/推理、下载、GPU、RSAR/其它个人项目读取，或共享产物泄漏私有信息。

### 7.2 Scientific development gate

先在 primary endpoint、三个 target-GT-free scores、nontrivial alpha 中按 evaluation unit 去重。一个 unit 只有在至少一个 score/alpha 同时满足以下条件才算 qualifying：

1. primary split-FST calibration certified；
2. 原 audit practical gate 全部通过；
3. `audit_direction_consistent=True`。

- `PASS_BROAD_TARGET_FREE_DEVELOPMENT`: validity pass，qualifying units `>=3/6`，且覆盖 `>=2/3` datasets；
- `FAIL_NO_BROAD_TARGET_FREE_DEVELOPMENT`: validity pass，但 unit 或 dataset breadth 未达门；
- `INCONCLUSIVE_DEVELOPMENT`: validity 非 pass 或 breadth 所需数据不完整。

只由 target-GT diagnostic、trivial alpha、Holm sensitivity、any-grid 或重复 score rows 取得的成功不计入 breadth。无论 pass/fail，都报告 qualifying unit/dataset/score/alpha 的精确集合、全部失败原因和 unique-context 计数。

## 8. 早停与解释纪律

1. Git/所有权/ancestry/授权路径失败：停止。
2. r005 身份、六单元 lineage 或 576 parity 失败：inconclusive，不运行新 protocol。
3. D_fit-only order taint test 或 exact-integer HB 对照失败：validity fail，停止发展 gate。
4. FWER simulation primary 任一 scenario 超标：validity fail，不得用 Holm 或挑场景续命。
5. breadth fail：C2-R 不进入 RSAR acquisition；不得降低 3 units/2 datasets、换 endpoint 或把 diagnostic 混入。
6. breadth pass：只建议冻结 protocol/code/seed/schema，再由 C 另开 RSAR acquisition；本轮不下载或推理。
7. A–F outcome 已暴露是不可恢复的最弱环节；所有正结果必须标记 retrospective development。

## 9. 资源与操作计数

- detector fit/predict=`0/0`；GPU、下载、RSAR read、其它个人项目 read=`0`。
- 允许固定 score-regressor reproduction fit/predict=`12/12`；必须与 detector 操作分开记录，且参数与 r004 完全一致。
- CPU 密集模拟使用不少于 80% 可用 CPU，线程/进程预算、实际并行方式和串行限制入报告；不得只设置环境变量就声称真实利用率。
- 全部新增文件和 append diff 做 bounded sanitizer，覆盖合同已有 Unix/Windows 路径、账号/机器、常见凭据/私钥/连接串；sanitizer 是有界检查，不称完整证明。

## 10. 授权写入范围

只允许：

- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a1_split_fst_r006.py`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_split_fst_order_r006.csv`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_split_fst_frontier_r006.csv`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_zero_event_practical_witness_r006.csv`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_split_fst_fwer_simulation_r006.csv`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_split_fst_gate_r006.json`；
- 新增 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_split_fst_manifest_r006.json`；
- append-only 修改 `claude_code_and_supervisor.md`，只记录 r006 逻辑路径、validity gate、development gate、停止状态和分离操作计数；
- 新增唯一报告 `dis/server_reports/orientbench-c-r006-20260805.md`。

不得修改任何旧 script/report/CSV/JSON、主稿、协议、配置、数据、checkpoint、`dis/B.md`、`dis/C.md`、`dis/sug.md`、`dis/review_state.json` 或旧服务器报告。需要其它写入时标记 `PROPOSED_DEVIATION` 并停止。

## 11. 必须持久化和报告的证据

1. 起止 SHA、授权路径、r005 输入/输出身份、六单元 lineage、576 parity 与 operation counts。
2. 7488=`576×13` 级候选 order/trace 表的唯一键、D_fit tuple、D_cal sequence 状态、historical/Holm/any-grid 标签；若 schema 合并行数不同，必须能无歧义重建同一候选全集。
3. 576 family 的 primary/historical/Holm selected result、formal/trivial/practical/audit consistency 和失败原因。
4. zero-event practical witness 的 row 与 unique-context 汇总，明确非 deployable/非完整 upper envelope。
5. exact-integer HB 全候选对照、r005 浮点 hardening 影响计数；历史 r005 gate 必须保持不变。
6. 108 个 FWER scenario、50000 replicates、seed、false count、empirical rate、CP upper、模拟代码路径与证明前提。
7. primary development breadth 的 qualifying units、datasets、score/alpha；行数与 unique context 分开。
8. manifest：scientific snapshot、execution HEAD、实际命令、输入/输出 bytes/SHA-256/Git blob、资源/操作计数、sanitizer、授权路径；manifest 自身由结果提交 Git blob 固定，不做伪自哈希。
9. 最弱环节、置信度、反证条件和下一步；不得把标准 split-FST 写成 novelty。

## 12. 校验、提交与最终回复

运行 JSON/CSV/schema/row-count/identity/path/link 检查、`git diff --check`、普通与 staged diff。确认只含授权路径，所有旧 r005 blob 与 `dis/B.md` blob 不变。只显式暂存授权文件，中文 commit message，正常 push；禁止 merge/rebase/reset/clean/force。

最终回复必须恰好两行，不加代码围栏、项目符号或第三行：

第一行只能是 `执行完毕` 或 `未执行完毕`。

第二行只能是 `dis/server_reports/orientbench-c-r006-20260805.md`。
