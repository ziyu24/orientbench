# OrientBench C 侧首轮证据基线

- round: `orientbench-c-r001-20260805`
- scientific snapshot: `9d9cdae1847f9c82e841f6f8b2692389cf9d9d79`
- 核查日期: `2026-08-05`
- active manuscript: [`top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md)
- 当前科学状态: A=`A_MEASUREMENT_ONLY`；B5=`PASS_MECHANISM_BOUNDED`（但其候选 bootstrap 与可执行 gate 需重审）；B6/B7 未执行。
- 投稿上限: 当前不应投稿。若统计修复、主稿事实修订、独立确认与 novelty 边界均通过，可按 TGRS 及以上标准重评；在此之前不能把 A 写成可部署认证方法，也不能把 B 写成已验证修复方法。
- `cc_recommendation: recommended_now`

## 1. 可复算证据入口

| 证据层 | 权威入口 | 当前解释 |
|---|---|---|
| A 主稿 | [`orientation_reliability_paper_A_zh_v077.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md) | 主动稿；measurement-only，不含已证实的通用选择器 |
| 完整评测器 AP/角度扰动 | [`table1_fullval_final_065.csv`](../top_journal_v3_reaudit_055/reports/table1_fullval_final_065.csv)，生成端 [`recompute_table1_fullval_k1_065.py`](../top_journal_v3_reaudit_055/scripts/recompute_table1_fullval_k1_065.py) | 6 个主单元中 AP50 基本不变，AP75 大幅下降 |
| `ar>=2.1` 实例排序 | [`m1_all_main_results_ar21.csv`](../top_journal_v3_reaudit_055/reports/m1_all_main_results_ar21.csv)，生成端 [`m1_ar21_unify.py`](../scripts/m1_ar21_unify.py) | 六个主单元 detection-score NRC 为 0.4653--0.9379；这是 informative ranking，不是 calibration |
| A1--A3 严格前沿 | [`a1_guaranteed_frontier_all_alpha.csv`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_guaranteed_frontier_all_alpha.csv)，生成端 [`run_a1_a3.py`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/run_a1_a3.py) | `alpha<=0.01` 无可部署 nontrivial practical point；唯一 practical 点是 target-GT 诊断上界 |
| 人工标注 | [`m4_human_annotation_primary_summary_073.csv`](../reports/m4_human_annotation_primary_summary_073.csv)，生成端 [`integrate_m4_human_073.py`](../scripts/integrate_m4_human_073.py) | 450 个数值双标目标；第三标注者 150 目标尚无真人结果 |
| 共享 G0 取证 | [`g0_phase_score_forensics.md`](../top_journal_v3_reaudit_055/shared_forensics/g0/docs/g0_phase_score_forensics.md)，[`g0_final_decision.csv`](../top_journal_v3_reaudit_055/shared_forensics/g0/reports/g0_final_decision.csv) | `PASS_RISK_FUNCTIONAL_DEPENDENT`；连续角误差与 severe-event 必须分开表述 |
| B1--B3 | [`b1_b3_final_decision.csv`](../top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b1_b3_final_decision.csv)，生成端 [`run_b3_real_interventions.py`](../top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/run_b3_real_interventions.py) | H1/H3 有边界内机制证据；H2/H4 部分支持；不能继承为候选优越性 |
| B4--B5 | [`b5_mechanism_gate_decision.csv`](../top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b5_mechanism_gate_decision.csv)，生成端 [`run_b4_b5_analysis.py`](../top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/run_b4_b5_analysis.py) | 外部 RotatedFCOS-PSCD 三 seed 健康，但候选未外部确认；现有 gate 生成方式需修复 |
| 冻结阈值 | [`configs/thresholds.yaml`](../configs/thresholds.yaml) | 服务器迁移清单给出的 raw SHA-256 为 `b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae`；文本换行转换会改变工作树原始字节哈希 |

本 Git 快照不包含服务器上的数据集、模型权重和大体量持久化预测。它足以审计论证、协议、代码和小型结果表，但不足以在本地重跑 detector、恢复 10 份 split CSV、核对全部 275 个迁移资产或执行 B6。

## 2. 严格审查：三种互补失败模式

### 2.1 旋转检测与部署

建设候选：把贡献限定为 OBB 朝向可靠性的测量协议，组合 le90 周期误差、`ar>=2.1` 几何适用域、geometry-normalized severe event、完整评测器扰动和 scene/tile 统计单位审计。

最强攻击：近期工作已分别覆盖角度质量/方差、面向角度的 NMS、旋转不确定性和 aspect-ratio-sensitive 指标。A 不能声称“首次角度质量”“首次旋转不确定性”或“首次指出 AP50 对角度不敏感”。此外，ranking-only 操作保持 boxes/classes/NMS 不变；机制干预是在 post-NMS 角度上改写，未重跑 NMS，不能宣称 AP 不变或可部署修复。

综合：A 的可守 novelty 是“系统测量与审计协议及其负结果”，而不是新 detector 或成功的风险控制器。置信度：中高。最弱环节：尚无满足 full-universe、provenance-clean、持久化完整且未参与协议设计的独立确认单元。

### 2.2 统计与协议

建设候选：A 的外层 `D_cal/D_audit` 与 LTT/Hoeffding--Bentkus、图像/切片/母景审计形成清楚的有限样本框架；G0 的 cluster bootstrap 通过把重采样 cluster multiplicity 提升为实例权重，保持了实例级 estimand。

最强攻击（当前最致命问题）：

1. B3 的 `bootstrap_delta` 先把 candidate score、phase score 和 risk 各自在 image 内取均值，再对 image means 计算 NRC；B4 的 `boot` 对 mother scene 做相同处理。报告中的点估计却是在全部 matched instances 上计算的 NRC。区间与点估计不是同一 estimand。
2. 直接审计结果：B3 有区间的 58 个候选比较中，39 个实例级点差落在所报区间之外；B4 为 24 个中的 4 个。区间不必机械包含点估计，但代码与这种系统性偏离共同证明了 estimand mismatch。
3. [`run_b4_b5_analysis.py`](../top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/run_b4_b5_analysis.py) 直接写入 H1--H4 状态及 `PASS_MECHANISM_BOUNDED`，没有从冻结阈值、健康检查和统计结果计算 verdict。当前 CSV 是叙述性结论的生成器，不是可执行 gate。
4. 主稿 DOTA NRC 仍写 0.6912/0.6458；这是旧宽掩码结果。统一 `ar>=2.1` 权威表 [`m1_all_main_results_ar21.csv`](../top_journal_v3_reaudit_055/reports/m1_all_main_results_ar21.csv) 为 0.7544/0.7113，且 [`074_orientation_reliability_AB_split_full_report.md`](../docs/074_orientation_reliability_AB_split_full_report.md) 明确禁止混用。

综合：A 的主要负结论暂不依赖 B3/B4 候选区间，因而未被直接推翻；B 的候选比较、外部确认和 B6 放行条件不能沿用。置信度：高。最弱环节：本地缺少服务器大资产，无法在本轮直接生成修正区间。反证条件：服务器按实例权重重算后证明旧区间逐行与同一 estimand 数值等价，并给出可复算证据；若成立，撤销该问题。

### 2.3 对抗性 novelty / TGRS+ 审稿

截至 `2026-08-05` 核查的一手来源：

- [SeqCRC: Sequential Conformal Risk Control for Post-Processed Object Detection (arXiv:2505.24038v2)](https://arxiv.org/abs/2505.24038)，[官方实现](https://github.com/leoandeol/cods)：已经对 post-NMS 检测器顺序调 confidence、localization、classification 参数并给出有限样本风险控制，是最接近的通用方法框架。
- [Angle Quality Estimation for Oriented Object Detection (Scientific Reports, DOI 10.1038/s41598-025-31034-w)](https://www.nature.com/articles/s41598-025-31034-w)：显式学习 angle-quality distribution 的均值/方差，提出 NMS-AQ 与 aspect-ratio-aware loss。
- [O2: Real-time Open-world Object Detection in Remote Sensing Images (TGRS 2026, arXiv:2603.15497)](https://arxiv.org/abs/2603.15497)，[IEEE DOI](https://doi.org/10.1109/TGRS.2026.3671683)：angle distribution refinement 明确用于捕捉旋转不确定性。
- [ARS-DETR (arXiv:2303.04989；TGRS 2024)](https://arxiv.org/abs/2303.04989)：已明确批评 AP50 的大角度容忍并提出 aspect-ratio-sensitive 检测评价。
- [Phase-Shifting Coder (CVPR 2023)](https://openaccess.thecvf.com/content/CVPR2023/html/Yu_Phase-Shifting_Coder_Predicting_Accurate_Orientation_in_Oriented_Object_Detection_CVPR_2023_paper.html)，[官方 MMRotate 配置](https://github.com/open-mmlab/mmrotate/tree/1.x/configs/psc)：PSC 原始作者为 Yi Yu、Feipeng Da；主稿当前作者表述需更正。
- [Rethinking Boundary Discontinuity Problem for Oriented Object Detection (CVPR 2024)](https://openaccess.thecvf.com/content/CVPR2024/html/Xu_Rethinking_Boundary_Discontinuity_Problem_for_Oriented_Object_Detection_CVPR_2024_paper.html)：直接讨论旋转框边界不连续与 PSC 机制边界。
- [OSKDet (CVPR 2022)](https://openaccess.thecvf.com/content/CVPR2022/html/Lu_OSKDet_Orientation-Sensitive_Keypoint_Localization_for_Rotated_Object_Detection_CVPR_2022_paper.html)：已有 orientation-sensitive localization quality 建模。
- [Adaptive Bounding Box Uncertainties via Two-Step Conformal Prediction (ECCV 2024)](https://eccv.ecva.net/virtual/2024/poster/138)，[Multivariate Confidence Calibration for Object Detection (CVPRW 2020)](https://openaccess.thecvf.com/content_CVPRW_2020/html/w20/Kuppers_Multivariate_Confidence_Calibration_for_Object_Detection_CVPRW_2020_paper.html)，[MCCL (CVPR 2023)](https://openaccess.thecvf.com/content/CVPR2023/html/Pathiraja_Multiclass_Confidence_and_Localization_Calibration_for_Object_Detection_CVPR_2023_paper.html)，[Beyond Classification (WACV 2024)](https://openaccess.thecvf.com/content/WACV2024/html/Popordanoska_Beyond_Classification_Definition_and_Density-Based_Estimation_of_Calibration_in_Object_WACV_2024_paper.html)：限定 calibration / localization uncertainty 的既有边界。
- [AOPG / DIOR-R (arXiv:2110.01931)](https://arxiv.org/abs/2110.01931)，[官方实现](https://github.com/jbwang1997/AOPG)：主稿把 DIOR-R 关联到 2016 rotation-invariant CNN 文献，数据集出处需更正为 AOPG/DIOR-R 来源。

综合：现有 related work 不足以支持高位 novelty 表述，且至少有 PSC 作者、DIOR-R 来源和 DOTA NRC 三处可直接核验的事实问题。置信度：高。AI4IM 2026 的 “Uncertainty-Aware Rotation Estimation” 仅能从官方会议信息确认题目/DOI，全文证据未取得，本轮只列 watchlist，不独立支撑判断：[DOI 10.1109/AI4IM69129.2026.11558216](https://doi.org/10.1109/AI4IM69129.2026.11558216)。

## 3. 可证伪候选与最低判别实验

| 候选 | 与最近一手工作的实质差异 | 最低判别实验 / gate | 杀死条件 |
|---|---|---|---|
| C1：OBB 朝向可靠性测量与认证可行性审计 | 相对 SeqCRC，主张 OBB 特有的周期角、AR 适用域、几何归一化严重事件、完整评测器扰动、母景统计单位与人工角度分歧；不主张新通用 CRC 算法 | 在一个未参与协议设计、full-universe、provenance-clean、持久化完整的 detector-head-dataset 单元上，冻结后一次性复算 AP、NRC、scene risk 和前沿；并以 SeqCRC 风格通用 post-NMS 风险控制作为直接基线 | 新单元无法复算；关键负/几何结论在母景正确划分后消失；或所有增量都可由通用 SeqCRC 加普通 angle uncertainty 无损替代 |
| C2：endpoint/host-qualified 的 PSC 排序修复 | 相对 PSC、边界不连续和 AQE，不主张首次角质量；只主张从双频相位机制得到、在固定 endpoint/host 上可验证的 ranking-only score | 先用 cluster multiplicity 实例权重重算 B3/B4 800 次配对 bootstrap，并把 B5 改为数据驱动 gate；通过后才在 RetinaNet 与外部 RotatedFCOS 三 seed 上运行冻结 B6，要求同时对 phase_mod 与 detection score 报告 | 任一端点/host 不能稳定优于 detection score；CI 不支持预注册最小效应；改变 boxes/classes/NMS/AP；或收益只存在于开发 seed/事后选参 |
| C3：母景与标注噪声决定“可认证性”的边界 | 相对常规 detection calibration，主张实例数量不能替代独立场景数，且 degree-level 风险需由人工分歧界定 | 修复 SODA 母景角色交叉，给出 mother-scene-clean 外层 split；完成第三标注员 150 目标并冻结仲裁；重跑严格前沿与敏感性 | 母景清洁重分后结论方向反转或不稳定；第三人结果与现有人类锚点不可复现；或无需 scene/human 处理即可得到相同认证结论 |

## 4. 决策台账

| 决策 | 状态 | 证据/理由 | 下一步 |
|---|---|---|---|
| A 保持 measurement-only | adopt | 严格主风险无跨单元可部署 practical success；唯一 practical 点依赖 target-GT | 不扩张为成功方法论文 |
| B5 机制存在但范围受限 | revise | 外部三 seed 与 endpoint/host 差异支持 bounded mechanism；现有统计区间和 gate 生成不合格 | 先执行 [`sug.md`](sug.md) 的统计重审 |
| 立即执行 B6 | reject | B5 不是可信的可执行放行门，候选 CI estimand 不一致 | 统计 gate 通过后重新决策 |
| 主稿当前数字与引用可投稿 | reject | DOTA NRC 主口径混用；PSC 作者、DIOR-R 来源错误；遗漏 2024--2026 最近工作 | 单独建立 manuscript correction 清单，不在本轮改主稿 |
| 独立 CC 盲审 | experiment | 当前问题同时横跨统计实现、旋转检测机制和 novelty，独立盲审可暴露同源偏差；CC 不作裁决 | 用户决定是否从 [`B_START_PROMPT.md`](B_START_PROMPT.md) 启动 |

## 5. CC 建议

`cc_recommendation: recommended_now`

理由：本轮发现会改变 B5/B6 决策的实现级统计问题，以及会直接触发审稿质疑的事实与 novelty 缺口。适合让 CC 在不知道本轮 C 判断的条件下先独立盲审，再逐条对抗复核。CC 不是裁决者；收到 `dis/B.md` 后，C 将对每项给出 `adopt | revise | reject | experiment`，需要新证据时转最小实验。
