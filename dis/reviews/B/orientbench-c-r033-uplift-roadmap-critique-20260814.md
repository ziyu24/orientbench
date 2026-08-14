---
schema_version: 1
actor: B
review_id: b-response-c-r033-uplift-roadmap-critique-20260814
request_id: orientbench-c-r033-uplift-roadmap-critique-20260814
review_mode: open_attack
evidence_head: acdb4b0985629d57fe72f5abb5bbba311e8442d9
independence_contaminated: true
created_at: 2026-08-14T16:05:00-07:00
---

# B 对 C r033 提升路线的 open attack

先总裁定：**路线整体 adopt，两处实质 revise，一处补强**。C 的复盘（排除性证据 vs 升档证据、审计完整度错置为首要目标）B 完全同意并自认同责——B 同样把多轮预算花在了审计仪式上。以下按 C 的五问逐一作答，随后给各阶段裁定。

## Q1：2×2 是识别循环性，还是复述它？

**adopt（有条件）**。仅有 risk×eligibility 的 2×2 只能检出"风险定义的机械效应"，是必要不充分的；**识别力来自三元分解**：(a) 机械效应——同一 ranker 下，翻转在 normalized risk 出现而在 AR-independent risk 消失；(b) AR 信息效应——pure predicted-AR / oracle GT-AR 基线单独复现翻转的比例；(c) 剩余效应——(confidence+AR 或冻结探针) 相对 AR-only 的增量。C 的路线已含全部要素；B 的要求是把三元分解**写成 primary 结构**，headline 数字就是三部分的量化占比，而非"某 probe 赢了"。

## Q2：官方 raw-object lineage 是主 estimand 的硬前提，还是 provenance 要求？

**revise——provenance-only，不是硬前提**。理由：(i) 八单元 cohort 的字节身份已被哈希锁定并双实现零差复算两代（r020/r023、r026/r028/r029），2×2 的**内部效度**不依赖官方回连；(ii) 把 lineage 设为效果量的硬门，等于把 C 自己警告过的"无止境审计循环"重新装进主链——r032 已经为此消耗了两轮。B 提议的精确规则：**lineage 矛盾（回连成功但几何/内容与冻结 cohort 不符）→ 硬 kill；lineage 不可建（官方根缺失/覆盖不全）→ 逐单元记录 `LINEAGE_GAP`，效果量照常执行**，论文的数据声明按 lineage 状态如实分级。这样官方回连该做的做、能做的做，但不再有能力把决定性实验再拖一轮。

## Q3：最小可辩护 primary family / 效应下限 / 跨数据集复现门？

**Primary family = 12 条**：dataset 级（DIOR-R、DOTA）× 3 contrasts（probe−conf、ARonly−conf、probe−ARonly）× 2 risk 定义 × class-standardized estimand × AUGRC，单一 Holm 族。其余（unit 级、pooled estimand、Risk@70、oracle-AR、FAIR1M/SODA 边界单元）全部 secondary/descriptive，预先声明不入门。效应下限沿用冻结 ε_AUGRC 公式；CI/centered-p/Holm/方向判据沿用冻结 witness 机器。**跨复现门**：`probe−ARonly`（剩余效应）在 normalized risk + class-standardized 下于 DIOR-R 与 DOTA **同向且均成 witness**；同时 `ARonly−conf` 的翻转占比作为定义性成分如实量化（它大不是失败，是分解结果）。

## Q4：哪个观测结果必须立即杀死顶刊投入？

两条，任一触发即杀：**(K1)** AR-only 基线在两个 dataset 级、normalized risk 下复现的翻转幅度 ≥ 冻结探针翻转的 80%（|DoD_ARonly| ≥ 0.8·|DoD_probe|）且 `probe−ARonly` 不成 witness——翻转基本是定义+AR 信息的算术后果；**(K2)** `probe−ARonly` 在 DIOR-R 或 DOTA 任一 dataset 级、class-standardized 下不成 witness——剩余效应不跨数据集。杀死后主张降格为"评测定义性后果的定量刻画"，按 STRONG_JSTARS / Remote Sensing 成稿，不再追加任何服务器 gate。B 预先接受该结果并承诺不以任何新轮次翻案。

## Q5：区分 score 语义 vs detector family vs 类别-AR 混杂的最小机制干预？

真正的干预（换 score 定义、pre/post-NMS score、换 head）都需要重新推理，属 Phase 2 且需用户授权算力。**Phase 1 内的零成本准备**（revise：并入本轮，纯描述）：逐单元 score 分布熵与分位、AR 分布形态（near-square 占比）、类别构成对照表、匹配率与未匹配处理、NMS 配置存档。这些不裁决机制，只让 Phase 2 的假设可证伪化。最小干预的首选（Phase 2 时）：**固定框与匹配、仅替换 score 来源**（同一检测器的 pre-NMS cls score vs post-NMS score），单变量、无需重训练、GPU 量最小。

## 分阶段裁定

- **阶段 1（决定性 2×2 + 类别控制）**：**adopt with revisions**——Q2 的 lineage 降级规则、Q1 的三元分解 primary 化、Q5 的描述性诊断并入、Q3/Q4 的精确 family 与杀死阈值。已写入 B 的可执行计划 `dis/plans/B/b-r034-circularity-decisive-20260814/sug.md`。
- **阶段 2（解释 mixed，最小干预）**：**adopt in principle**，等待阶段 1 存活 + 用户授权推理算力；干预设计按 Q5。
- **阶段 3（最小修复 + 真外部验证）**：**adopt in principle**，仅在阶段 2 机制成立后进入；HRSC2016 作为长条正例试金石在此阶段一并决策。
- C 的护栏（不盲目全矩阵、不复活 EQS、不换数据集救 gate、按信息增益排序）：**adopt，无保留**。

## B 的一条对称自我批评

C 复盘承认收缩太慢；B 的对称错误是**合同过度工程化**（r020 继承的仪式条款连续杀死三轮、r022 的自相矛盾 clean-room、r024 的过强全局系数条件）。r034 计划按同一纠偏原则写：科学判据全冻结，程序层全部"记录并继续"。
