# OrientBench C 侧证据裁决与下一轮基线

- round: `orientbench-c-r002-20260805`
- scientific snapshot: `8466602330a942c9bb8beff284aa8fc5b952a3b0`
- 核查日期: `2026-08-05`
- active manuscript: [`top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md)
- 当前科学状态: A=`A_MEASUREMENT_ONLY`；B=`FAIL_CANDIDATE_GATE`；B6/B7=`STOPPED_NOT_RUN`；submission=`NOT_READY`。
- 投稿上限: 当前是强 JSTARS / TGRS borderline。完成事实修订、证据链收口和一个真正未见的完整确认单元后，才适合按 TGRS 重新评估；现有证据不支持 TGRS+。
- `cc_recommendation: no`

CC 已完成 r001 的盲审和对抗复核；服务器的新证据已经裁决其关键统计分歧。当前再启动 CC 不会增加新证据，除非用户以后明确要求在 A6R 结果或投稿前做新一轮复核。

## 1. 本轮结论

服务器报告 [`orientbench-c-r001-20260805.md`](server_reports/orientbench-c-r001-20260805.md) 及本地独立复核支持以下裁决：

- 38/38 完整性检查与 14/14 同估计量测试通过；本地四项正式测试也通过。
- 旧实现中 B3 `39/58`、B4 `4/24` 个实例级点差落在所报旧区间外；修正为 cluster multiplicity 提升到实例权重后，新点差全部落在对应新区间内。
- B3 开发证据中 `27/58` 行同时优于 phase_mod 和 detection score；B4 的外部 DOTA/RotatedFCOS 三 seed 为 `0/24`。因此没有任何冻结 candidate×endpoint 在外部单元的三个 seed 上同时击败两条基线。
- 最终裁决为 `FAIL_CANDIDATE_GATE`，并永久停止 B6 以及事后增加 score、seed、阈值或 endpoint 的候选挽救。H1/H3 只保留为 bounded mechanism 证据，不能继承成 ranking repair。
- A 的 measurement-only 结论不依赖 B 候选成功，因此负结果没有推翻主项目；它反而限定了论文应写成“系统测量与可认证性审计”，而不是一个成功的新 detector 或可部署 selector。

置信度：统计实现核心 `0.98`，`STOP_B6` 裁决 `0.97`，当前证据包达到 publication-grade 全链复现的置信度 `0.72`。

## 2. 最致命问题与证据缺口

当前最致命问题不再是 weighted NRC 数学实现，而是“主稿事实仍未修订 + 缺少真正独立的确认单元”。在此之前不能把负结果包装成普适定理或可部署认证结论。

r001 证据包还需一次不改变科学结果的 provenance 收口：

1. 两个实际参与计算/完整性判断的直接输入未进入 manifest：
   - `top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json`，canonical SHA-256 `80d86a5f72e70405fe4a49db87aad61e6aea20a26af0ad1c5745bfd646d1e5cb`；
   - `top_journal_v3_reaudit_055/shared_forensics/g0/reports/g0_comparison_manifest.csv`，canonical SHA-256 `e038aed06b3aff86818c8663657f074798e90de867ab48ac9d2821c61c191a86`。
2. 九个 B3 cache 只核对行数，尚未用 raw→cache 的确定性内容 lineage 证明来源。
3. 点估计会删除非有限 score，但 bootstrap 没有显式使用同一 common mask；本轮已报告单元看来均为有限值，所以不影响当前数字，但实现必须封死漂移入口。
4. `bootstrap_nrc()` 隐式循环固定的 800 次，而不是传入 multiplicity 数量；生产结果不受影响，测试覆盖不足。
5. 现有 development gate 允许 FAIR1M 混入 DIOR-R/SODA-A 的开发数据集计数，且没有预注册多 seed 和多重比较成功规则。由于外部支持是空集，本轮 FAIL 不受影响；未来任何 PASS 都不能沿用该口径。
6. 生成物嵌入运行时 HEAD，导致在新提交上复跑时字节改变；需要把固定科学快照、执行源码哈希和 Git 结果提交的职责分开，不宣称自引用提交可 bitwise 稳定。

下一台服务器只执行 [`sug.md`](sug.md) 的 r002 evidence-only 收口；不训练、不推理、不恢复 B6。

## 3. 论文主张与可发表性

本文主要研究：在遥感旋转目标检测中，常规 AP 尤其 AP50 是否掩盖方向错误，检测分数能否可靠排序方向风险，以及在图像/切片/母景相关性和人工角度分歧存在时，有限样本认证是否真的可行。论文的贡献应是把以下五层放入同一个可复算审计协议：

1. le90 周期角误差与 `ar>=2.1` 几何适用域；
2. geometry-normalized severe event 与连续角误差的分离；
3. 完整 evaluator 下的角度扰动及 AP50/AP75 盲区；
4. 实例 ranking 与母景级有限样本认证边界；
5. 人工方向标注分歧作为可认证性的经验下限。

负结果仍有论文价值，因为它不是“方法没涨点”，而是由多数据集、多 seed、完整 evaluator、母景统计单位和人工证据共同界定：现有分数有一定 ranking 信息，但冻结修复候选不能外部确认，严格 practical certification 也没有跨单元成功。可发表性来自可复现的边界、失败机制和防止错误部署结论的协议；前提是不过度声称成功 selector。

截至 `2026-08-05`，可守的外部表述是：

> To our knowledge, this is the first systematic remote-sensing OBB study to unify le90/AR-normalized orientation risk, reliability ranking, mother-scene finite-sample certification feasibility, full-evaluator angular perturbation, and human angular disagreement in one reproducible audit protocol.

这仍需在投稿前用完整 related-work 表格逐项核对。不能声称“首个 angle uncertainty”“首个 AR-aware metric”“首个 OBB calibration/conformal”“首个指出 AP50 角度盲区”或“首个通用风险控制/可部署 selector”。主要一手边界包括 [SeqCRC](https://arxiv.org/abs/2505.24038)、[Angle Quality Estimation](https://www.nature.com/articles/s41598-025-31034-w)、[ARS-DETR](https://arxiv.org/abs/2303.04989)、[PSC](https://openaccess.thecvf.com/content/CVPR2023/html/Yu_Phase-Shifting_Coder_Predicting_Accurate_Orientation_in_Oriented_Object_Detection_CVPR_2023_paper.html) 和 [CVPR 2024 boundary-discontinuity study](https://openaccess.thecvf.com/content/CVPR2024/html/Xu_Rethinking_Boundary_Discontinuity_Problem_for_Oriented_Object_Detection_CVPR_2024_paper.html)。

## 4. 可证伪候选与 gates

| 候选 | 实质差异 | 最低判别 gate | 杀死条件 |
|---|---|---|---|
| C1：五层统一的 OBB 朝向可靠性审计协议 | 不发明通用 CRC 或新 detector，而是把 OBB 特有几何、完整 evaluator、母景单位与人类分歧统一到可复算协议 | 先通过 r002 provenance 收口；再在一个未参与协议设计的 full-universe、provenance-clean detector×head×dataset 单元上冻结后一次性复算 | 新单元无法复算；核心结论在母景正确划分后消失；或五层增量可被既有单一协议无损覆盖 |
| C2：母景有效样本量与人工角度噪声共同限制可认证性 | 区别于只做实例级 calibration 的工作，主张 scene dependence 和 human ambiguity 都会收紧可认证边界 | 修复 SODA 母景角色交叉，完成缺失第三标注者证据，并报告冻结敏感性分析 | 母景重分后方向反转；人工锚点不可复现；或实例级处理即可得到相同结论 |
| C3：独立确认单元上的 measurement-only 泛化 | 不追求挽救 B，而检验 A 的负/几何结论能否跨新 host/head/dataset 保持 | A6R asset/provenance gate 先确认资产真正未见、含 empty images/tiles、完整 GT/prediction/NMS/母景 ID；通过后才允许一次推理或重分析 | 与现有 OrientBench/PCP 资产或选择过程重叠；只有 matched cache/非完整 universe；或新单元推翻关键方向 |

## 5. 其它个人项目的关系

用户已确认 D7/PCP-OBB、pcbobb、pcbobb_beyond、pcbobb_score_study 均为未投稿的个人内部项目，因此不存在公开发表优先权或自我竞争问题；OrientBench 是当前主项目。其有效思想可以在本项目重新验证后吸收，也可以对外提出首创表述，但外部 novelty 仍必须相对于公开一手文献成立，不能把未公开草稿当成引用依据。

当前不下载这些旧仓库到服务器：D7 和 pcbobb_beyond 的已跟踪大型结果约为 0.53 GB 和 0.93 GB，主要是与现有 checkpoint/数据/选择流程重叠的 matched/operator 资产；换一台服务器不会创造科学独立性，旧缓存也不能充当 A6R 确认。以后若确需借用一个 replayer/bootstrap 函数，只按冻结 commit 提取最小源码并单独记录 provenance，不导入旧结果作为确认性证据。

## 6. 决策台账

| 决策 | 裁决 | 证据与理由 | 下一步 |
|---|---|---|---|
| 接受服务器 `FAIL_CANDIDATE_GATE` | adopt | B4 外部支持 `0/24`，结论不依赖边缘 gate 写法 | 永久 `STOP_B6` |
| 保留 H1/H3 bounded mechanism | revise | 外部机制方向可复现，但不能证明候选排序修复 | 只作机制/附录证据 |
| r001 已完全 publication-grade 闭环 | revise | 统计核心正确，但 direct-input manifest 和 cache lineage 有缺口 | 执行 r002 evidence-only 收口 |
| 立即进入 A6R 新单元 | experiment-after-r002 | 是提高 TGRS 可辩护性的最小新证据，但应先封闭廉价 provenance 缺口 | r002 PASS 后发布 A6R asset gate |
| 下载四个旧项目到服务器 | reject-now | 体量大、资产/选择重叠且不能制造独立确认 | 仅在明确最小代码依赖时提取 |
| 再次调用 CC | reject-now | CC r001 已完成，新服务器证据已裁决主要分歧 | A6R 后或投稿前再评估 |
