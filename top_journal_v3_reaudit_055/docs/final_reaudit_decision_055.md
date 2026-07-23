# 最终综合裁决 (055 re-audit)

> 基于 A0（协议法证）、A1（P2 强化）、A2（P1 约束扰动）、A3（测量层身份）、A4（P4）、A5（P5）、Task0（Codex 049–054 审计图）。全部数字来自真实 052 provenance-clean artifacts，冻结 masked 协议 ar≥1.6，未训练/未推理/未改 thresholds/split。

## 逐问裁决

**1. Codex 049–054 是否存在执行错误？** 是（3 处实质错误）：
- 053/054 headline NRC 用 unmasked full table（丢失 masked 主协议）→ near-square pooling artifact 伪反校准。
- DOTA#20 用 19-图 D_cal-subset dump 混入 P1 主表并算 mAP（0.0132 无意义）。
- 053 P1 用均匀 30° 扰动（破坏 rIoU>0.5，mAP 同步动，非有效解耦）。
（另：049–052 多轮 NRC 均未 masked；phase_mod DOTA#20 dump 与 matched 486 scope 冲突未被察觉——见 Task0 异常项。）

**2. 哪些错误导致 B 的问题？**
- B-A0 协议漂移 = 错误①。B-A0(DOTA#20) = 错误②。B-A2(约束扰动) = 错误③。B-A1(空洞保证) = alpha 选取过松（设计问题，非纯执行错误）。

**3. 哪些 B 问题不是执行错误而是证据本身不足？**
- 下游实用性（P5）：良态实例上角度纠正的下游收益本就微弱（~0.3% IoU），非协议可修。
- PSC 机制“证明”：需受控 angle-coder 重训实验，超本轮范围（只能给候选）。
- 跨域严格保证：conformal 在 shift 下的退化是方法本质，非执行错误。

**4. P1 是否 partial → precise-pass？** **是**。约束扰动下 mAP@0.5 各 ar-bin Δ=0，orientation risk +15~+64°、AP75 崩 → precise-pass（受 ar/IoU 阈值门控的精确解耦）。

**5. P2 是否 空洞 → 有效贡献？** **是（有边界）**。在“优于平均可靠性”strict 区，within-cell conformal 提供带弃权的尾部保证（干净 Hoeffding 界）；score menu 证明 conformal+几何选择器为默认。边界：均值版为近似保证；跨数据集无严格保证（如实报告退化，Mondrian 部分缓解）。

**6. P3 是否保留为 case study / mechanism candidate？** P3 重定位：几何选择器成为 **P2 score-menu 的最优 score**（方法一部分，source-supervised + target GT-free = deployable **candidate**，非 validated method）；机制候选 = intrinsic phase_mod 反校准。

**7. P4 推荐路线？** **几何感知选择器**（masked 下 NRC 6/6 显著优于检测置信度、5/6 优于 TTA）；TTA+conformal 作 GT-free 后备（不稳定）；phase_mod 不作 selector（反校准）。checkpoint-ensemble 因无多 epoch 权重 = unavailable（不编造）。

**8. P5 是否有合理下游收益？** 方向正确但**微弱**（几何选择器一致小幅降低 angle-induced IoU 损失，绝对 ~0.3%）→ 附录/边界，不作 utility headline。

**9. 论文身份？** **Orientation Reliability Measurement Protocol + Finite-Sample Conformal Risk Control**（非 full benchmark；测量层核心 = cliff；脊柱 = P2）。

**10. 是否可回到遥感顶刊强候选？** **有条件的‘是’**。修正后的科学内核是自洽且非假象的：P1 precise-pass（动机）+ cliff（测量层）+ P2 有限样本风险控制（脊柱，含 score menu）+ intrinsic phase_mod 机制候选 + 诚实边界。这构成一个可信的 **遥感 / 可信度期刊（如 TGRS / ISPRS 方向）强候选**。**明确不是 CVPR/ICCV/TPAMI ready，不保证录用，不宣称 top venue ready。**

**11. 若不能（进一步上探/稳录），还缺什么？**
- 在冻结 masked 协议 + 052 provenance 下重算更多 cell（当前仅 7–9），恢复可辩护的多 detector×dataset 覆盖。
- 受控 angle-coder 实验以把 phase_mod 从“机制候选”升为机制证据（需监督批准，涉及训练）。
- 一个角度真正主导的下游任务（如舰船 heading 选择性预测）以支撑 utility。
- 更紧的有限样本 / 分布迁移保证（CRC 变体、Mondrian 理论）。
- DOTA cell 的 full-val provenance dump（对齐其它 cell scope）。

## 一句话
Codex 在 049–054 因协议漂移把 near-square pooling 伪反校准当成 headline；本轮法证调和后，检测置信度反校准作废，P1 升为 precise-pass、P2 升为有效有限样本风险控制、几何选择器为推荐默认、intrinsic phase_mod 反校准成为幸存机制候选；论文改写为 **protocol + risk control**，是遥感/可信度期刊的**有条件强候选**，非顶会 ready。
