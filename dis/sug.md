# OrientBench 服务器任务：r006 有效性实现修复与 r007 最小复核

- round: `orientbench-c-r007-20260805`
- scientific snapshot: `8e93291b75b34ddfb7b74a7592e1573407603f88`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`
- previous server report: `dis/server_reports/orientbench-c-r006-20260805.md`
- 唯一服务器报告路径: `dis/server_reports/orientbench-c-r007-20260805.md`

## 1. 单一科学问题

r006 的来源链、主 frontier 与“14 个合格行只覆盖 DIOR-R 的 A/B/C”可以复核，但其 `PASS_SPLIT_FST_VALIDITY` 不可采纳：

1. `hb_p_exact` 与 `pvec_exact` 缺少单侧安全检验必须的 `k/n >= alpha => p=1`；错误 exact 路径被用于 108 个 FWER 模拟。
2. outcome-taint 检查比较同一 `serial` 的哈希与自身，恒真，没有实际置换 D_cal/D_audit outcome。
3. 7,488 个 exact 对照有 6,762 个不一致，却没有进入 `valid` 条件。

本轮只回答：修正上述实现后，split-FST validity 是否真正通过；若通过，冻结口径下的发展广度是否仍不足 3/6 units 与 2/3 datasets。不得把修复称为新方法、确认性证据或 TGRS 就绪。

## 2. 固定边界

- 不修改 r006 及更早的任何 script、CSV、JSON、report、manifest、协议、split、threshold、score、endpoint、alpha、coverage grid、matching、tile/NMS、主稿或旧日志内容。
- primary 仍使用 bounded conditional scene loss 的冻结 `M.hb_pvalue`；exact-integer Bernoulli 路径仅用于正确的独立实现核验与 FWER simulation，不得偷换 primary estimand。
- family 固定为 `unit × score × endpoint × alpha`；target-GT-free score 固定为 `detection_score`、`tta_circular_consistency`、`source_supervised_leave_geometry`。
- A–F 结果均为 `RETROSPECTIVE_DEVELOPMENT_ONLY`。RSAR 与其它个人项目不得读取或下载。
- detector fit/predict、训练、推理、GPU、下载均为 0；允许复现固定 score regressor 12/12。

## 3. 必做修复与证据

### 3.1 单侧 exact-integer HB

实现相互独立的 scalar 与 vector 版本。对 `n<=0`、非法 alpha 或 `k/n >= alpha` 必须返回 1；仅在 `k/n < alpha` 时计算 Hoeffding–Bentkus lower-tail p-value。直接使用整数 `k`，禁止 `ceil(n*float_mean)` 恢复计数。

对 r006 全部 7,488 个 Bernoulli scene-event 候选保存 `k,n,alpha,scalar_p,vector_p,match`；scalar/vector mismatch 必须为 0。另设定至少包含 `k/n<alpha`、`=alpha`、`>alpha`、`k=0`、`k=n`、`n=0` 的边界单元测试；任一失败即 validity fail。

### 3.2 真实 outcome-taint 测试

将 order builder 写成只接受 D_fit threshold 与 sufficient statistics 的纯函数。对每个 576 family：

1. 生成 baseline order 的规范序列化字节；
2. 用固定 seed 分别置换 D_cal 与 D_audit endpoint outcome，并做一次确定性反转/极端扰动；
3. 验证扰动确实改变了至少一个 calibration/audit outcome 或 statistic；
4. 重新走完整候选装配路径，比较 baseline 与每种 perturbed order bytes。

禁止同一对象、自身哈希或未改变 outcome 的伪测试。保存 family、扰动类型、changed count、baseline/perturbed SHA-256 与 match；全部 family×扰动必须 match。

### 3.3 split 与 FWER

- 对 A–F 显式报告 D_fit、D_cal、D_audit scene/tile ID 集合大小及三组两两交集；交集必须为 0。
- 按 r006 冻结的 108 scenarios、seed `20260805`、每场景 50,000 replicates 重跑模拟，但必须调用修正后的单侧 vector exact-integer p-value。
- 每场景报告 false rejection、empirical FWER、95% Clopper–Pearson upper；全部 split-FST upper `<=0.105`。Holm 仍仅是 sensitivity。
- 模拟只验证实现；不能替代理论前提。

### 3.4 frontier 与广度

用正确的 bounded-loss primary 路径重建 2,304-row frontier，并与 r006 primary/historical/Holm/any-grid 字段比较。任何变化必须逐行解释；不得为了保留 14 行而改规则。

结构通过后才计算 development gate。合格条件保持：primary endpoint、nontrivial alpha、target-GT-free、split-FST certified、原 audit practical 全过、audit empirical risk `<=alpha`。同时报告行数和唯一 `unit×endpoint×alpha` context。

## 4. 预注册 gate

- `PASS_SPLIT_FST_VALIDITY_R007`: provenance/parity/lineage、split disjoint、全部 exact scalar/vector 与边界测试、真实 outcome-taint、理论前提和 108 个 primary FWER simulation 全部通过。
- `FAIL_SPLIT_FST_VALIDITY_R007`: 任一实现、单侧 p-value、taint、split、FWER 或理论前提失败。
- `INCONCLUSIVE_SPLIT_FST_R007`: 必需输入、身份、schema、hash 或重算无法闭环。
- development 仅在 validity pass 后判定：达到 3/6 units 且 2/3 datasets 为 `PASS_BROAD_TARGET_FREE_DEVELOPMENT_R007`，否则为 `FAIL_NO_BROAD_TARGET_FREE_DEVELOPMENT_R007`；validity 非 pass 时为 `INCONCLUSIVE_DEVELOPMENT_R007`。

若 validity pass 但仍只有 DIOR-R，明确停止 C2-R/RSAR acquisition，不得降门、换 endpoint、混入 diagnostic 或把 nominal/trivial pass 算入广度。

## 5. 授权写入范围

只允许新增：

- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a1_split_fst_r007.py`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_split_fst_exact_hb_r007.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_split_fst_order_taint_r007.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_split_fst_split_disjoint_r007.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_split_fst_fwer_simulation_r007.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_split_fst_frontier_r007.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_split_fst_gate_r007.json`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_split_fst_manifest_r007.json`
- `dis/server_reports/orientbench-c-r007-20260805.md`

并允许 append-only 修改 `claude_code_and_supervisor.md` 一条。其它路径全部禁止；尤其不得触碰 `dis/B.md`、`dis/C.md`、`dis/sug.md`、`dis/review_state.json`、主稿及 r006 文件。需要偏离时写 `PROPOSED_DEVIATION` 并停止，不得先做后报。

## 6. provenance、资源与早停

- 起始 HEAD 必须包含 scientific snapshot；工作树/index 必须干净；只允许 fast-forward。
- manifest 登记全部输入、输出 bytes/SHA-256/Git blob、命令、seed、schema、行数和 operation counts。提交路径必须与授权集合完全相同。
- CPU 密集模拟使用至少 80% 可用 CPU 的 worker budget，并如实区分预算与实际利用率。
- exact、taint、split 或 FWER 任一失败时立即停止广度解释；不得用 Holm 或挑场景续命。
- 即便全通过，本轮也不下载 RSAR、不修改主稿，只返回证据供 C 裁决。

## 7. 最终回复格式

服务器最终回复首行只能是：

`执行完毕`

或：

`未执行完毕`

第二行必须且只能给出：`dis/server_reports/orientbench-c-r007-20260805.md`。
