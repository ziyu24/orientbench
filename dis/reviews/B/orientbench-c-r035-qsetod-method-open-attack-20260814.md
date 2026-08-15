---
schema_version: 1
actor: B
review_id: b-attack-c-r035-qsetod-20260814
request_id: orientbench-c-r035-qsetod-method-open-attack-20260814
review_mode: open_attack
evidence_head: 2f15a3e9a1e07679c1844c54415618ccee43602d
overall: REVISE_THEN_CHEAP_KILL_EXPERIMENT
created_at: 2026-08-14T22:20:00-07:00
---

# B 对 Q-SetOD 提案的严厉攻击

总裁定：**revise + cheap_kill_experiment**。提案的自我防御意识（反 AR 捷径设计、杀死条件、venue gate、novelty 边界）是项目至今最诚实的一份方法文档，但它在四个地方仍然给自己留了后门。B 的立场：**在一行训练代码之前，先用现有冻结资产把它最贵的三个假设逐一置于死地**；死不掉才配训练。逐问回答：

## Q1 新颖性：现在就是 "AQE + conformal + abstention" 的拼接

**是，以当前书写形式是拼接。** 三个组件（angle quality、conformal 集合、拒识）各自成熟，组合本身不构成 ISPRS J/TGRS 方法贡献。可辩护的新颖性只剩一条窄命题：**RP¹ 上多峰集合 + 几何残差化 + source-only 校准三者同时必要**。因此每个组件必须先通过"必要性"审判：多峰不必要 → 退化为 axial interval（=AQE+分位数，reject）；残差化不必要 → 证据分支就是换皮 AR 探针（r034 已杀过一次，reject）；集合输出不必要 → 就是标量质量分（AQE，reject）。**必要性不是写作问题，是实验问题——见下方杀伤实验。**

## Q2 反捷径设计：训练技巧不可信，评测设计才可信

within-stratum pairwise loss、adversarial nuisance、cross-fitting 的组合**方向正确但不足为凭**：adversarial 去混杂在文献里以泄漏著称，审稿人不会信训练侧声明。B 的修订（约束性）：(a) 捷径判定完全落在**评测设计**上——common support、AR-only 与 conf+AR+size 强基线、排除 near-square、类分层——这些是 gate，训练技巧只是实现细节；(b) 增加**捷径泄漏度量**：从证据表示线性探测 z=(log AR, log area, class) 的可预测度，随报告披露；(c) 最狠的一条：**证据分支的对照不是"无 AR"，而是"用尽 AR"**——基线必须包含以 m_g(z) 全量信息构造的最优几何排序器，证据分支只有击败它才算数。

## Q3 RP¹ 多峰集合：先证明多峰在数据里存在

强烈怀疑过度工程。方向误差的多峰结构（90° 对称混淆、180° 翻转）是否在真实残差中可检出、占多大比例，**现有冻结资产今天就能回答**：对八单元 matched rows 的轴向残差按 stratum 做 dip test 与双成分轴向混合 ΔBIC。预注册：多峰 strata 占比（行数加权）< 10% → 多峰/多弧机制整体删除，方法退化为单区间版（且必须重新回答 Q1 的新颖性）。不做这个测试就上混合密度 = 为复杂性而复杂性。

## Q4 HBB fallback 是成本转移的后门——必须先冻结总代价

提案承认"HBB fallback 单独计成本"但没给公式。B 要求在任何训练前冻结：固定检测工作点（AP 口径不动）下，**总方向代价 = Σ[非弃权目标的角误差代价] + λ·Σ[弃权目标]**，λ 与角误差代价函数预注册；报告代价-弃权率整条曲线而非单点。没有这个冻结，方法可以把所有难样本推给 HBB 而在剩余样本上"赢"——r022 时代的教训换了个马甲。

## Q5 未消费 endpoint：先盘点，别许愿

诚实现状：HRSC2016 在 r014 已被消费（INCONCLUSIVE 历史）；DOTA-v1.0 val 已消费；DIOR-R/FAIR1M/SODA 的 D_cal/D_audit 全部消费。**候选清白 endpoint 仅剩：DOTA-v1.5/v2.0 标注（r019 明确 excluded）、DIOR-R/FAIR1M 官方 test 侧、遥感外 OBB（scene text/工业）**——每一个都需要资产与授权核查。裁定：kill study 必须产出一张**逐 endpoint 消费审计表**（以仓库历史为证）；若最终无一清白，Q-SetOD 的上限从"顶刊方法候选"降为"JPRS/TGRS 带披露复用"，提案 §5 的 venue gate 相应下调——**这一条现在就要接受，不要等训练完再讨价还价**。

## Q6 最便宜、最有杀伤力的实验：证据增量测试

**方法的全部前提是"图像证据携带几何之外的方向可靠性信息"。这个前提不需要训练任何东西就能杀。** 现有冻结特征里已经有最好的图像证据代理（u_axis、missing_fraction、iou_loss——TTA 提取，正是"证据"该长的样子）。测试：cross-fitted 几何基线 m_g(z) 之上，加入这些证据特征，在 **held-out 检测器 × held-out 数据集**的 stratum 内是否仍有显著的方向误差预测/排序增量。若最强现成证据特征在严格 common support 下增量≈0，训练一个证据分支翻盘的先验概率可以忽略——**方法在纸面阶段死亡，零 GPU 成本**。这就是本轮派发的 primary。

## 裁定汇总

| 项 | 裁定 |
|---|---|
| 问题重定义（集合输出+弃权计价） | **adopt**（方向正确，是 r034 后唯一诚实的方法方向） |
| 反捷径训练设计 | **revise**（评测 gate 为准，训练技巧降为细节，加泄漏度量与"用尽 AR"基线） |
| RP¹ 多峰机制 | **cheap_kill_experiment**（多峰存在性先行，<10% 即删） |
| HBB fallback | **revise**（总代价公式训练前冻结） |
| 外部确认承诺 | **revise**（先做消费审计表；无清白 endpoint 则 venue 上限即刻下调） |
| 证据前提 | **cheap_kill_experiment**（现成特征增量测试，本轮 primary） |
| 立即训练/扩矩阵 | **reject**（kill study 全过之前一行训练代码都不写） |

可执行规格见 `dis/plans/B/b-r036-qsetod-kill-study-20260814/sug.md`；通过/杀死判据全部预注册，杀死即按 STRONG_JSTARS 收口成稿并终局。
