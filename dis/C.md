# OrientBench C 侧 r002 裁决与 A6R 前瞻复现基线

- round: `orientbench-c-r003-20260805`
- scientific snapshot: `e3ca1ad94d64d202a47b6635490fde439df76868`
- evidence cutoff: `2026-08-05`
- active manuscript: [`orientation_reliability_paper_A_zh_v077.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md)
- 当前科学状态: A=`A_MEASUREMENT_ONLY`；原 A6=`NO_ELIGIBLE_CONFIRMATORY_UNIT`；B=`RETIRED_FAIL_CANDIDATE_GATE`；B6/B7=`STOPPED_NOT_RUN`；submission=`NOT_READY`。
- 投稿上限: 强 JSTARS / TGRS borderline。一个真正前瞻、完整、未看风险结果的 A6R 复现单元会使 TGRS 更可信；现有证据不支持 TGRS+。
- `cc_recommendation: no`

CC 已完成 r001，新的服务器证据和可复算反例已经足以裁决 B；当前再次调用不会改变 gate。A6R 出现新科学证据后或投稿前再评估 CC。

## 1. r002 服务器回执裁决

服务器提交 `e3ca1ad94d64d202a47b6635490fde439df76868` 与唯一报告 [`orientbench-c-r002-20260805.md`](server_reports/orientbench-c-r002-20260805.md) 的核心失败门有效：

| 事项 | C 裁决 | 证据与含义 |
|---|---|---|
| 333 个直接输入、9/9 raw→cache lineage、275 文件 inventory | adopt | 两项先前漏记输入哈希精确匹配；九个 cache 的 108 个数组逐元素一致；旧 r001 文件未变 |
| `FAIL_EVIDENCE_DRIFT` | adopt | DIOR-R seed0 TTA 排除 `298/48282=0.617%`，SODA-A seed0 排除 `2104/193045=1.090%`；四个 TTA×endpoint 行的共同有限宇宙改变，最大统计差 `0.024593006944616247` |
| `FAIL_CANDIDATE_GATE / STOP_B6` | adopt | B4 全部原始行仍不支持候选；common-mask 修复没有产生外部成功 |
| `redundant_comparisons=0` | reject | 实现只比较原始 score 哈希，漏掉 stable-ranking 等价候选和 baseline 自比较；对应测试是同一数组与自身比较的恒真测试 |
| “r002 是 publication-grade 全闭环” | reject | 预注册 PASS 未满足，且冗余报告口径错误；只能把它作为失败发现和 B 停止证据 |

独立重算后的正确描述口径是：

- B3 的 58 个原始行包含 18 个 `multi_frequency_consistency` / `unwrap_candidate_energy_gap` rank-equivalent 重复增量；折叠后为 40 个 unique-result groups，支持为 `15/40`，而不是把相关重复项当成 `27/58` 个独立证据。
- B4 的 24 个原始行包含 6 个 detection-score 对自身的恒等比较；其余又有 6 个 rank-equivalent 重复增量。实质外部门是 `0/12` 个 unique non-baseline comparisons，结论仍为 FAIL。
- r002 修正后的四个 TTA 行可用于披露 common-mask 漂移；r001 的对应四行不再作为权威统计。r002 的“重复数为 0”和未经折叠的支持计数不得进入论文 headline、摘要或独立证据计数。

置信度：B 统计失败与 `STOP_B6` 为 `0.99`；provenance 包内部一致性为 `0.96`；本机缺少服务器 14.58 GB 原物，无法在本机端到端重放全部 lineage，因此对完整跨机 replay 的置信度为 `0.82`。

## 2. 对主论文 A 的影响

r002 没有直接推翻 A。A 的冻结协议 [`a1_protocol_frozen.json`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_protocol_frozen.json) 对缺失 TTA 的定义是保持 eligible universe、把非有限 TTA 排在全部有限值之后；实现 [`run_a1_a3.py`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/run_a1_a3.py) 与该定义一致。B 为候选与两条 baseline 的公平配对比较采用 common finite mask，两者是不同 estimand，不能混表。

主稿后续必须披露上述 `0.617%` 和 `1.090%` 缺失率，并明确：A 是 worst-rank imputation / full eligible universe；B 是 candidate-specific complete-case paired comparison。该事实修订不改变 A 当前“可部署分数没有 nontrivial practical certification”的负结论。

原 A6 冻结协议 [`a6_confirmatory_protocol_frozen.json`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a6_confirmatory_protocol_frozen.json) 与结论 `NO_ELIGIBLE_CONFIRMATORY_UNIT` 永久保留。下一步 A6R 是在当前全部既有结果之后新注册的 prospective replication；它不能被追溯描述为原 A6 的 confirmatory success。

## 3. 为什么不再修 B，而转 A6R

B 的最强外部结果即使按最有利口径也为零支持，冗余折叠后只会减少独立证据数。继续修 B 的脚本只能让一个已死亡的候选包更整齐，不能提高主论文的科学上限。C 因此把 B 路线永久退出主 claim；保留其失败机制和审计教训，但不再投入服务器训练、推理或统计重跑。

当前最致命问题是 A 没有一个满足 full-universe、provenance-clean、未参与协议设计且未看过风险结果的前瞻复现单元。下一服务器任务 [`sug.md`](sug.md) 只做 A6R 资产门控，不计算 NRC、风险或认证结果。

## 4. 可证伪候选

| 候选 | 实质差异 | 最低判别 gate | 杀死条件 |
|---|---|---|---|
| C1：五层统一 OBB 朝向可靠性审计协议 | 把 le90/AR 风险、完整 evaluator、ranking、母景认证和人工分歧统一为可复算 measurement protocol，而不是新 detector/selector | A6R 先冻结一个未看 outcome 的完整 detector×head×dataset×split 单元；之后只运行一次冻结推理与复算 | 没有合格资产；或前瞻单元使核心 AP/几何/认证边界方向消失 |
| C2：母景有效样本量与人工角度分歧共同限制认证 | 区别于实例级 calibration，明确 scene dependence 与 human ambiguity 的共同边界 | 在 A6R 中完整保留 image/tile/mother-scene 身份和 empty scenes；投稿前统一人工证据事实状态 | 正确母景划分后边界反转；人工锚点不可复现；或普通实例级方法即可得到同等保证 |

## 5. A6R 选择边界

A6R 优先新 dataset + 新 detector/head；若只能使用既有 dataset，则必须是从未参与任何 alpha、AR、score direction、endpoint、coverage grid 或候选设计的精确新 unit，并降级标为 unit-level replication。资产门不查看 target NRC/risk/certification outcome，只按 provenance 完整度和预先声明的中性规则选一个候选。

用户的其它个人项目均未投稿，因而没有公开优先权冲突；其思想可以重新验证后吸收到 OrientBench。但 D7/PCP-OBB、pcbobb、pcbobb_beyond、pcbobb_score_study 的旧资产/结果不能创造 A6R 独立性。本轮不下载这些仓库；只有明确缺少一个最小实现函数时，才按冻结 SHA 提取源码且不得导入结果。

## 6. 决策台账

| 决策 | 状态 | 理由 | 下一步 |
|---|---|---|---|
| r002 evidence closure PASS | reject | gate 明确为 `FAIL_EVIDENCE_DRIFT`，且冗余检测失效 | 不伪装成 PASS |
| B 候选继续实验 | reject | 折叠后外部仍 `0/12`，没有可挽救信号 | 永久停止 B6/B7 |
| 再跑一轮 B 只修报表 | reject | 不改变主论文或候选结论 | 在 C 中冻结正确独立口径 |
| 进入 A6R 资产门 | experiment | 这是唯一能明显提高 TGRS 可辩护性的最小新证据 | 执行 r003 `sug.md` |
| 下载四个旧项目 | reject-now | 旧选择/结果暴露，不能充当前瞻复现 | A6R 本轮禁止 |
| 再次调用 CC | reject-now | 当前争议已由代码、CSV 和 gate 裁决 | A6R 后或投稿前再评估 |
