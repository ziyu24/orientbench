# B（CC）审查报告 — OrientBench

```yaml
reviewer: B (Claude Code / CC)
round_id: orientbench-c-r001-20260805
scientific_snapshot_sha: 9d9cdae1847f9c82e841f6f8b2692389cf9d9d79
review_commit_sha: e2d1414c75f42f62b881a299a79e0de2a758b04d   # 工作树 HEAD；与快照的差异仅为 dis/ 下 5 个协作文件（git diff --name-status 核验）
paper_entry: top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md
review_time: 2026-08-05 (UTC+0 会话内完成)
independent_review_completed_before_reading_C: true
```

过程声明：

- 阶段一全程未读取本轮 `dis/C.md`、`dis/sug.md`、`dis/sug/**`；`dis/review_state.json` 阶段一整体未读（无法预判哪些字段泄漏 C 判断，宁可全跳过）。未通过 Git 历史、diff 或搜索间接接触上述内容（仓库级检索均显式排除 `dis/`）。独立性自评：**未受损**。
- 协议偏差披露：本机无 SSH 私钥，用户明确指示以 HTTPS 拉取（https://github.com/ziyu24/orientbench.git，Windows 凭据库有既存 GitHub 凭据）。克隆与推送均走 HTTPS 普通 push，禁 force 不变。这偏离启动 prompt 的"必须使用 SSH origin"，如实记录。
- 审查机器无 Python 环境，且 `outputs/persistent_artifacts/`（服务器侧 14.58 GB、275 文件，见 `docs/server_migration_handoff_20260727.md`）不在 Git 内，故本轮为**一致性/生成端/逻辑审查**，未做任何本地数值复算。凡"已核验"均指论文数字与仓库内持久化 CSV/JSON 的精确比对及其生成脚本的静态审查。

---

# STAGE_1_BLIND_REVIEW

## 0. 审查视角与覆盖

选取三个视角做一轮"建设候选—最强攻击—证据综合"：

1. 数字法证：headline 数字逐一追到生成端文件与脚本；
2. 统计方法学：统计单位、条件人群、LTT/UCB 参数、split 边界；
3. novelty：一手论文与官方实现核查（核查日期 2026-08-05）。

已核对的生成端（论文表 → 仓库文件）：

| 论文位置 | 生成端 | 核对结果 |
|---|---|---|
| 表 2（扰动 AP） | `top_journal_v3_reaudit_055/reports/table1_fullval_final_065.csv` + `reports/k1_table1/*.json` | 6/6 行精确一致 |
| 表 3（经验容忍角） | `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_empirical_tolerance_distribution.csv` | 抽查行精确一致 |
| 表 4（NRC/AURC） | `top_journal_v3_reaudit_055/reports/m1_all_main_results_ar21.csv` | 主 6 行精确一致；DOTA 两句有口径问题（见 F1） |
| 表 5（尺寸分箱） | `top_journal_v3_reaudit_055/reports/m2_g2doubleprime_ar21.csv` | 15 行、11 显著，逐行一致 |
| 表 6（认证前沿） | `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a1_guaranteed_frontier_all_alpha.csv` | 576 行聚合计数精确一致（含非互斥说明）；唯一 practical 点各字段一致 |
| 表 7（双标分歧） | `reports/m4_human_annotation_primary_summary_073.csv` | 精确一致（含分数据集行） |
| 表 8（标注者 vs GT） | `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a5_annotator_gt_metrics.csv` | 精确一致 |
| 表 1（统计单位示例） | `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a2_instance_tile_scene_comparison.csv` | 数值可全部溯源，但条件未披露（见 F5） |
| §4.1 `a=2.1` 推导 | `paper_A_orientation_protocol/reports/a4_ideal_delta_lookup.csv`、`figures/iou_delta_theta_aspect_ratio.csv` | δ₀.₇₅(2.1)=15.4°；15° 精确交叉在 ar≈2.15，"约为 2.1"成立但略松 |
| §8.5 score menu 分项 | 同表 6 文件按 score 聚合 | detection 0 / TTA 1 trivial / leave-* 0 / target-GT 1 practical，精确一致 |

裁决文件（`a1_a3_final_decision.csv`、`a4_a6_final_decision.csv`、`shared_forensics/g0/reports/g0_final_decision.csv`、`b5_mechanism_gate_decision.csv`）与论文的 measurement-only 定位一致；v077 未出现 PSC 机制或修复结论，A/B 边界合规。

## 1. 发现（按严重度排序）

### F1｜主口径章节混用 legacy 掩码的 DOTA NRC（事实性不一致，必须修复）

- 论文 v077 第 286 行（§8.3）："DOTA clean units 的 detection-score NRC 分别为 0.6912（Oriented R-CNN）和 0.6458（Rotated RTMDet-M）"。
- 权威 `ar>=2.1` 统一口径值是 **0.7544 / 0.7113**：`top_journal_v3_reaudit_055/reports/m1_all_main_results_ar21.csv` 第 26–27 行（G_dota_orcnn、H_dota_rtmdet）。
- 0.6912/0.6458 来自 legacy 宽掩码：`top_journal_v3_reaudit_055/reports/k4b_dota_full_val_metrics.csv` 第 2–3 行（retained 39,566/41,650，掩码与 m1 的 33,029/34,383 不同）。
- 项目自己的报告已明令禁止混用：`docs/074_orientation_reliability_AB_split_full_report.md` 第 353 行"历史表在较宽掩码下给出的 NRC 为 0.6912/0.6458；上表采用统一 `ar>=2.1` 后的权威主口径，**不能混用**"。方向审计 `reports/m1_old_vs_ar21_direction_audit.csv` 第 98–105 行同样记录了新旧值。
- 影响：定性结论（informative、远非 oracle）不变，但这是主口径章节里的口径混用，且与自家 authority 文件冲突；TGRS 审稿人比对仓库即可发现。
- 修复：改为 0.7544/0.7113，或显式标注"legacy 宽掩码值，仅供与历史表对照"。
- 置信度：高。反证条件：若存在一个我未见的、以 ar2.1 掩码复算出 0.6912/0.6458 的生成端文件，则本发现不成立（检索 `0.6912|0.6458` 未见此类文件）。

### F2｜表 4/表 5 的估计人群是 D_audit 子集，论文未披露且与 §7.1 措辞冲突（透明性，必须修复）

- `m1_all_main_results_ar21.csv` 所有主行 `evaluation_scope=D_audit`；`m2_g2doubleprime_ar21.csv` 明确 `evaluation_split=D_audit`、`selector_fit_split=D_cal-fit`。
- 论文 §7.1 却写"可靠性分析基于 provenance-clean **full-validation** matched predictions"（v077 第 223 行），全篇未出现"表 4/5 在审计子集上计算"的说明。
- 直接后果是同口径数字互相矛盾且无解释：unit A（DIOR-R/PSC）表 3 n=49,502（全验证 ar≥2.1，`a2_eligible_scene_universe.csv` eligible_instances=49,502），表 4 retained n=25,065（D_audit 子集 + near-square 排除；audit 场景 3,494/6,961）。普通读者无法调和 49,502 vs 25,065。
- G0 门控已提出同类要求：`shared_forensics/g0/reports/g0_final_decision.csv` "A 8.2/8.5 universe … do not describe 8.2 and 8.5 as same estimand … clarify in next A edit"——v077 尚未落实。
- 修复：§7.1/§8.3/§8.4 写明估计对象（D_audit 场景上的 matched、ar≥2.1、排除 near-square），并在表 3/表 4 注明两者人群差异；或补一份全验证口径的表 4 作对照。
- 置信度：高。反证条件：若 m1/m2 的 `D_audit` 字段实际覆盖全验证（即 audit=全集），则不成立——但 `a1_guaranteed_frontier_all_alpha.csv` unit A `calibration_scene_count=1794, audit_scene_count=3494`，与 universe 6,961 相加自洽，反证不成立。

### F3｜认证声明缺失置信参数 δ（统计完备性，必须修复、一句话即可）

- 冻结协议 `paper_A_orientation_protocol/reports/a1_protocol_frozen.json` 明确 `"delta": 0.1`（单侧 90% 置信）。
- 论文全文（含 §6.3、§8.5、表 1、表 6）未给出任何置信水平；"非平凡认证"、"UCB" 等语句在缺 δ 时是不完整的统计声明。grep `置信水平|90%|delta` 无命中（§4.1 的 δ 是角度符号）。
- 修复：在 §6.3 补一句"所有单侧上界在 1−δ=0.9 下计算，δ 在读取结果前冻结"。
- 置信度：高。

### F4｜FAIR1M 使用本地 train_80/val_20 冻结划分，§7.1 "既有 trainval/test 协议"表述不准确（必须修复措辞；无泄漏证据）

- GT manifest `reports/k1_table1_gt_manifest_065.csv`：官方 `split_ss_fair1m1.0/val/annfiles` 为空目录（n_images=0，sha256=e3b0c442…即空文件哈希）；实际单元使用 `split/val_20`（4,362 图 / 78,644 GT / 37 类，`build_fair1m_val20_gt_065.py` 生成）。
- `docs/m4_optional_third_dataset_extension.md` 第 4 行："frozen local train_80 -> val_20 (18505/4362 complete images)"；训练配置 `configs/m4_third_dataset_070/fair1m_psc.py` 第 35/49 行确认 train_80 训练、val_20 评测，整图级切分。
- 泄漏判断：切分在完整图像级、冻结、训练只用 train_80——未发现泄漏证据。问题仅在论文措辞：这不是"既有 trainval/test 协议"，是自建 80/20 划分，审稿人若比对 FAIR1M 官方协议（官方 test 无公开 GT）会质疑。
- 修复：§7.1 改写为"FAIR1M-v1.0 official validation 标注不可用，采用冻结的本地 train_80/val_20 整图划分（18,505/4,362 图）"。
- 置信度：高（对"表述不准确"）；对"无泄漏"为中高（依据 config 与 manifest 静态证据，未复算图像集合交集——最小补充证据：对 train_80/val_20 图像 ID 集合做一次交集为空校验并落盘）。

### F5｜表 1 两行取自前沿仅有的两个 certified 工作点，条件未标注（展示口径，必须修复）

- DIOR-R 行（19,207 / 2,882 / 2,882 / 0.0040 / 0.0188 / 0.0188）＝ unit C、`target_gt_nonlinear_geometry_upper_bound`、`relative_0.5_r_fit` 的唯一 practical 点：`a2_instance_tile_scene_comparison.csv` 第 212–214 行（instance ucb 0.003987；tile/mother ucb 0.018797；selected 19,207；nonempty 2,882/3,690）。即：**该行的分数是不可部署的 target-GT 诊断上界**。
- SODA-A 行（120,925 / 4,120 / 417 / 0.0061 / 0.0090 / 0.0180）＝ unit F、`tta_circular_consistency`、`absolute_0.01`、覆盖率 1.0 的唯一 **trivial** 点（α=0.01 ≥ 基础风险 0.003627，见 `a3_score_menu_certified_coverage.csv` F 行）：同文件 unit F 三行（ucb 0.006095/0.008967/0.018026）。
- 论文把两行呈现为中性"统计单位影响示例"，未写明 unit/score/α/审计范围；且"mother-scene 数 417"（unit F 审计范围非空母景）与 §6.2"可恢复 576 个母景"（全集）并置，读者易误读。
- 修复：表 1 加脚注标注两行的 (unit, score, α, split, selection 状态)，并注明 SODA-A 行来自 trivial 预算、DIOR-R 行来自不可部署上界分数。数字本身全部可溯源、无造假迹象。
- 置信度：高。

### F6｜可复算边界与 provenance 不对称（如实披露即可，部分需服务器补证）

- 本 Git 快照不含 `outputs/persistent_artifacts/`；`docs/server_migration_handoff_20260727.md` 第 32–34 行自认"仅从 Git clone 不能恢复完整项目"。因此论文所有主表在本快照下**不可复算**，只能做一致性审查——与"可复算 measurement protocol"的宣传（§摘要、§10）之间存在一个依赖服务器资产的前提，建议论文/README 明示复算所需资产清单。
- 表 2 六行来自两条不同生成路径：3 行（DIOR-R/22、DIOR-R/3、SODA-A/23）用持久化预测（`top_journal_v3_reaudit_055/scripts/recompute_table1_fullval_k1_065.py`，CELLS 仅含这 3 单元，结果 JSON 带 gt/pred sha256）；另 3 行（DIOR-R/61、FAIR1M/24、SODA-A/4）用重推理路径（`scripts/recompute_table1_by_inference_065.py`），其结果 JSON（`reports/k1_table1/DIOR-R_61.json` 等）只记录 ckpt 文件名、**无 GT/pred sha256**。后 3 单元 provenance 弱于前 3。修复：为重推理单元补 sha256 与 ckpt 哈希。
- 预注册顺序（预算/网格先于结果冻结）在 Git 上不可独立验证：`a1_protocol_frozen.json`、前沿 CSV、论文 v077 同在单一 squash 提交 da18ce6（2026-07-23）入库，先后顺序仅有 JSON 内自述 `frozen_at: 2026-07-22`。此项记为 `unknown`；如服务器端有原始细粒度提交或文件 mtime 日志，建议归档一份时间线证据。
- DIOR-R/61 checkpoint 名（best_mAP_5489）与 AP50 0.6462 的表面矛盾已由 `reports/k1_dior61_taos_pad32_residual_audit_066.csv` 解决（0.5489 是 multi-threshold dota/mAP 非 AP50；log AP50=0.6440 vs 复算 0.6462，差 0.0022）——建议论文附录引用该审计，防审稿人从 ckpt 名起疑。
- 工具箱测试：`toolbox_test_status.json` 记录 unit/synthetic/regression 全 PASS；本机无 Python 未能复跑，记为依赖仓库报告。

### F7｜表 2 的 AP75 下降部分是构造使然（表述级修改建议）

- 扰动定义是"沿远离 GT 方向推进到 IoU>0.5 边界内最大角"（`recompute_table1_fullval_k1_065.py` eps_max，1° 网格取连续前缀），推到 0.5 壳边界后 IoU≥0.75 几乎必然丢失——AP75 从 0.35–0.45 掉到 0.03–0.07 在很大程度上是**必然结果**，不是独立发现。
- 真正的信息量是：(a) 重匹配后 ΔAP50 恰为 0（六单元全部成立，非平凡，因为贪心重匹配与竞争可能改变配对）；(b) 壳内平均角剂量 8.9°→34.4–40.5°，即 IoU0.5 评测对 30° 级角误差完全无感。
- 修复建议：§8.1 把叙述重心从"AP75 显著下降"移到"0.5 壳内可用角剂量分布 + ΔAP50=0"；AP75 列保留但注明其构造相关性。
- 置信度：中高（不影响数字，仅影响解释力度与被攻击面）。

### F8｜认证对象以 GT 匹配为条件，部署时不可观测（定义级 limitation，建议显式写入）

- eligible universe 与场景损失 L_I 均定义在"matched（IoU≥0.5 一对一贪心匹配到 GT）且 matched-GT ar≥2.1"的实例上（`a1_protocol_frozen.json` eligible_universe；m1 mask `matched_gt_ar_ge_thr`）。matched 状态与 GT ar 在部署时均不可得。
- 因此即使某个可部署分数未来通过认证，其认证语义仍是"GT 条件事件"，与部署语义（对所有保留预测的角风险）之间有一个未被弥合的桥。论文当前以"审计而非部署"自我限定（§6、§8.5、§12），方向正确，但建议在 §6.1 或 §12 明确写出"eligibility 依赖 GT，可部署化需要 GT-free 的 eligibility 代理"这一条，否则"部署可用的认证"在概念上永远无法从本协议直接得出，读者应被明确告知。
- 置信度：高（定义层面事实）；严重度：中（与论文自我定位兼容，但属于应当言明的边界）。

### F9｜novelty 边界（一手核查，核查日期 2026-08-05）

结论先行：**组合式 novelty 成立，单件 novelty 均不成立**；相关工作需三处更新。

- AP@0.5 对角度弱敏感 + 长宽比调制角敏感性：ARS-DETR（IEEE TGRS 2024；arXiv:2303.04989；官方实现 github.com/httle/ARS-DETR）已定性主张"AP50 因角容忍过大不适于 OBB、倡导 AP75"，其 AR-CSL 本身就是按长宽比调节角标签平滑。v077 §2.1 仅一句带过（第 33 行）。本文的增量是受控扰动量化（ΔAP50=0 的六单元证据）与 δ_τ(a) 形式化，正文需把与 ARS-DETR 的 credit/差异写透，否则 TGRS 审稿（可能就是该文作者）会视 §8.1 为"确认既有观察"。
- 保形/风险控制×检测：§2.3 引用停在 Andéol 2023 [22]。2025–2026 已有一手新工作：Conformal Object Detection by Sequential Risk Control（2025-05）、Conformal Risk Control under Non-Monotone Losses（arXiv 2604.01502，2026-04）、Probabilistic Object Detection with Conformal Prediction（arXiv 2605.07549，2026-05）。均针对 box 覆盖/尺寸修正、instance 级；无一处理朝向风险或 tiled 航拍的场景级可交换单位。需更新引用并据此划界（这同时强化本文 scene-unit 贡献）。
- 角度置信度估计头：Scientific Reports 2025 "Oriented object detection … based on angle quality estimation"（AQE）直接以"角度质量分数筛选更可靠朝向"为卖点，与本文动机（检测分数排序≠角风险排序）同源。属方法侧，本文属测量/审计侧，但必须引用并划界，否则"分数-角度可靠性分离"这一动机句也非首创。
- 分解式朝向误差指标先例：nuScenes（CVPR 2020）的 TP 指标含 Average Orientation Error（AOE），是"把朝向误差从综合指标中拆出"的驾驶域先例。v077 未引用；建议引用以防"朝向误差单独度量"被误读为全新主张。
- 人工角度双标：UAV-OBB（Data in Brief 2026）用双标 IoU>0.85 一致率做数据集 QA；未见 OBB 域有"度级圆周分歧 + 图像簇 bootstrap CI + 与 official GT 差异分离报告"的先例。此件（表 7/8）是本文最接近单件 novelty 的部分。
- 场景级 abstention-aware 认证 + 完整负结果前沿：检索未见先例；负结果作为主贡献的呈现方式在本领域少见，是可辩护的差异点。
- **杀死条件**：若存在 2024–2026 任一一手论文对 aerial OBB 的角误差做选择性预测/有限样本风险认证（含 conformal/LTT 变体），本文核心 novelty 失效。我的检索（关键词覆盖 orientation reliability / risk-coverage / conformal rotated detection / angle error certification）未命中；此为可证伪断言，欢迎 C 或作者提供反例。
- 搜索为二手信号，上述四篇一手论文的定位均经 arXiv/期刊页面确认标题与摘要级内容；未逐篇读全文，novelty 结论标注为"摘要级核查"。

### F10｜次要与可选项

1. `a=2.1`：δ₀.₇₅(2.1)=15.4°，15.0° 精确交叉在 ar≈2.15（`a4_ideal_delta_lookup.csv` 2.0009–2.1 行）。"约为"成立；建议正文直接给出 δ₀.₇₅(2.1)=15.4° 以免读者以为恰好 15°。
2. §7.3 称"所有区间与统计单位一同报告"，但表 4 未印 NRC 的 bootstrap CI（`m1_all_main_results_ar21.csv` 有 nrc_ci_lo/hi 列）。建议表 4 补 CI 列——数据已存在。
3. 摘要"576…20 非平凡、68 trivial、554 不可行"三类非互斥已在 §8.5 声明，聚合计数逐项复核通过（geometry 144=1/24/142/1；>5° 14/0/130/7；>10° 4/4/140/3；>15° 1/40/142/1）。
4. DOTA 两个 clean 单元（G/H）不进入 576 行前沿的原因论文未说明（G0 记录"G–H incomparable by design"）；建议 §8.5 加一句（如 DOTA 的冻结 cal/audit 角色基于 train 侧，与 val 侧 clean 单元不匹配——以作者答复为准）。
5. `a5_annotator_gt_metrics.csv` 分层显示 DIOR-R 与低 ar 段存在 ~90° 翻转型 annotator-vs-GT 大差异（DIOR-R p95=85.70°；ar<1.6 均值 21.6°/22.0°，P>10° 22.7%/23.3%），而 ar≥2.1 子集干净（均值 2.59°/2.39°）。这一分层证据直接支持 ar≥2.1 主口径，也提示 official GT 在近方形目标上的 le90 规范不稳定，§9.2 值得引用一行，把主口径的合理性再钉一颗钉子。
6. 老 DIOR partial-GT 虚高（0.6964/0.7999/0.8866 → 0.5368/0.6448/0.6462，`k1_table1_superseded_values_065.csv`）已在仓库内成体系地修正与留痕；v077 使用的均为修正后全验证值，未发现旧值回流。
7. 表 4 的 FAIR1M NRC=0.9379（近随机）与表 5 FAIR1M 全部不显著相互印证，论文如实保留（"结果不稳定，完整保留"），符合不掩盖弱结果的自我承诺。

## 2. 数据/协议边界检查摘要（prompt 要求逐项）

- 数据集与 split：DIOR-R trainval→test 全验证（11,738 图/124,445 GT）；SODA-A val tiled（22,994 tile/449,644 GT）；FAIR1M 本地 train_80/val_20（见 F4）；DOTA 仅本地 train→val，不与公开榜比较（§7.1，合规）。
- seed：主 6 单元为既有 checkpoint 的推理评测（无训练 seed 敏感性问题）；K2 多 seed 表未进入 A 正文（边界合规）。
- baseline 公平性：本文无方法对比 claim，score menu 四分数在同一统计层比较，公平性内生。
- matching/tile/NMS：一对一贪心按分数、VOC11 AP；SODA-A 母景跨 cal/audit 角色 → 正式单位 tile/image（表 1 SENSITIVITY_SPLIT_OVERLAP 字段与 §6.2/§12 一致）。
- selection：6 主单元 = 全部 provenance-clean full-val 单元（`r2_cell_inclusion_exclusion_log.csv` 含完整排除理由：DOTA#20 19-img 子集异常、4 个 masked-only、候选无 clean dump）。未发现按结果挑单元的迹象。
- 指标边界：NRC<1 只解释为 informative（§5.2、§11），未见校准混淆。
- 大资产 provenance：见 F6。

## 3. 最致命问题、置信度与最弱环节

- **最致命**：F1（主口径章节混用 legacy DOTA NRC）+ F2（表 4/5 人群未披露且与 §7.1 冲突）。两者都是"论文文本 vs 仓库权威数据"的直接冲突，一次修订可修复；不修复则在数据可得的评审下必然被抓。
- **总体判断**：v077 的主结论方向（AP50 弱敏感的几何来源、可部署分数在严格主风险下广泛不可认证、标注不确定性限定度级语言、measurement-only 定位）与仓库证据一致，负结果披露纪律好于领域常规。修复 F1–F5 的前提下，按证据支持的投稿上限：TGRS 可投且有过稿路径（组合 novelty + 负结果前沿 + 工具箱），需准备好回答"工程读者的可用物是什么"（答案应为协议+工具箱+边界，而非任何认证成功）。不软化：若目标是更高档期刊，当前证据（无可部署正结果、无独立确认单元、第三标注员缺位）不足。
- **最弱环节**：(a) 本快照不可复算，一切精确一致性建立在持久化 CSV 可信之上——若服务器端生成脚本与 CSV 不对应，我的表级"精确一致"失去意义；(b) 预注册顺序不可独立验证（F6）；(c) novelty 为摘要级核查，未逐篇读全文。
- **反证条件**：任一主表在服务器端按脚本重跑与 CSV 偏差超出舍入位；或出现 F9 杀死条件中的一手先例；或 m1/m2 的 D_audit 标注被证明实为全验证（将推翻 F2）。

## 4. 建议的最小裁决实验（供 C/作者参考，不由 B 执行）

1. F2 验证兼修复素材：服务器端以全验证人群重跑 m1 六主行（脚本已存在），与 D_audit 版并排；两版 NRC 差异若 <0.02 则表 4 结论对 split 稳健，一并写入论文。
2. F4 补证：train_80/val_20 图像 ID 交集为空的一次性校验落盘。
3. F6 补证：为 3 个重推理单元补 GT/pred sha256；归档协议冻结时间线证据。
4. F9 判别：作者/C 对四篇新一手文献做全文级核查，确认无朝向风险认证先例（预计半天）。

——以上为阶段一盲审原文，此后不回改。

---

# STAGE_2_ADVERSARIAL_CROSS_REVIEW

```yaml
stage2_start_after_phase1_push: true
phase1_commit: 36f4c4536237f1258a2da53036c0f2f049eec327
read_after_push: [dis/C.md, dis/sug.md, dis/review_state.json]
stage2_time: 2026-08-05 (同一会话内完成)
```

阶段一原文逐字保留于上；以下为读取 C 材料后的逐条对抗复核。所有"已验证"均指本会话内的独立复核（代码阅读、CSV 重新计数、一手网页核查），非对 C 的转述。

## 5. 对 C 各实质观点的裁定

### C-1｜B3/B4 cluster bootstrap 与点估计不是同一 estimand（C.md §2.2.1–2）→ **adopt**（已独立验证，证据强度：高）

- 代码级确认：`run_b3_real_interventions.py` 第 168–188 行，`aggregate_image` 先取图像内 score/risk 均值，`bootstrap_delta` 对图像均值重采样并在均值序列上算 NRC 差；`run_b4_b5_analysis.py` 第 40–46 行 `boot` 对 mother-scene 均值做同样操作。而报告点估计（B3 第 255 行等、B4 第 62 行）是全实例 NRC。NRC 是 pooled ranking 的非线性泛函，cluster-mean NRC 与实例 NRC 即使在期望意义下也不同——estimand mismatch 成立，不是"百分位区间不必包含点估计"能解释的。
- 计数独立复现：B3 `b3_intervention_metrics.csv` 中有限 CI 的候选比较 **58 个，39 个**实例级点差落在区间外；B4 `b4_candidate_external_bootstrap.csv` **24 个中 4 个**。与 C 报告的 39/58、4/24 完全一致（本机 PowerShell 重算，排除 nan-CI 行）。
- 最强反驳已考虑并失败：若聚合是有意定义的"场景级 NRC estimand"，则点估计也应在场景均值上算——现在两者不匹配，且 `dis/sug.md` 授权的 G0 weighted-cluster 实现（multiplicity weights）才是项目内已有的正确参照。无剩余分歧。
- 对 sug.md 修复协议的两点补充建议（供服务器执行时采纳）：
  1. 加权 NRC 必须对三条曲线一致加权：score 降序前缀风险、oracle（按风险加权排序）、random 基线分母（加权均值），并保持冻结的 stable tie order 在权重下不变；
  2. `b3_b4_estimand_equivalence_tests_r001.csv` 除"全 k=1 时与未加权点估计逐位相等"外，应包含一个构造性异质 cluster 合成用例，证明该测试能在旧实现上**失败**（否则测试无判别力）。

### C-2｜B5 gate 硬编码、非可执行门（C.md §2.2.3）→ **adopt**（已独立验证，证据强度：高）

- `run_b4_b5_analysis.py` 第 92–96 行以字面常量循环写出 H1–H4 的 REPLICATED/PARTIALLY_REPLICATED；第 110–115 行以硬编码 dict 写出含 `final_decision=PASS_MECHANISM_BOUNDED` 的全部 gate 行；另见第 101 行 `best=[12,11,11][seed]` 硬编码 best epoch。verdict 不由阈值/健康表/bootstrap 输出计算。
- 细化（非反驳）：其底层数据表（intervention/bootstrap/nontriviality CSV）确为计算产物，且 `b4_variant_identity_ap_audit.csv` 对 post-NMS 干预已如实标注 `NOT_CLAIMED_INVARIANT` / `NMS NOT_RECOMPUTED`——问题精确地在于"结论层不可执行"，与 C 的表述一致。sug.md §3.6 的机器可检查条件是正确修复方向。

### C-3｜主稿 DOTA NRC 0.6912/0.6458 为旧宽掩码值（C.md §2.2.4）→ **adopt**（双方独立发现，收敛；证据强度：高）

- 与我阶段一 F1 完全一致（我在盲审中独立定位了同一冲突及 `074_…full_report.md:353` 的"不能混用"禁令）。双向独立发现使此项成为本轮最强共识：v077:286 必须改为 0.7544/0.7113 或标注 legacy 口径。

### C-4｜PSC 作者错误（C.md §2.3）→ **adopt**（已一手验证；B 阶段一遗漏，如实记录）

- arXiv:2211.06368 确认 PSC（CVPR 2023）作者为 **Yi Yu, Feipeng Da** 两人；v077 参考文献 [9]"Yu Y, Yang X, Li Q, et al."有误。我阶段一未做参考文献作者层核查，此项为 C 独有发现，B 采纳并自记遗漏。

### C-5｜DIOR-R 出处错误（C.md §2.3）→ **adopt**（已一手验证；B 阶段一遗漏）

- arXiv:2110.01931（AOPG，Gong Cheng 等，TGRS 2022）确认 DIOR-R 由该文发布。v077 [3] 用 2016 RICNN（TGRS）承担 DIOR 数据集引用不成立（2016 文早于 DIOR/DIOR-R 存在）。建议同时补 DIOR 基础数据集论文（Li Ke 等，ISPRS 2020）与 AOPG。

### C-6｜novelty 定位与一手清单（C.md §2.1、§2.3）→ **adopt 并合并双方清单**（证据强度：高）

- 与我阶段一 F9 结论收敛："可守 novelty 是系统测量/审计协议及其负结果"，任何"首次角度质量/首次指出 AP50 角度不敏感"表述均不可用。
- C 清单较我更全（SeqCRC arXiv:2505.24038 精确身份、O2 TGRS 2026、OSKDet、CVPR 2024 boundary、ECCV 2024 two-step conformal、CVPRW 2020/CVPR 2023/WACV 2024 校准线）；我已独立验证 SeqCRC 身份（Andéol 等，正是主稿 [22] 同组后续，必须引用）。
- B 补充 C 未列的三项（供合并入 correction 清单）：(a) nuScenes 的 Average Orientation Error（CVPR 2020）是"朝向误差从综合指标拆出"的驾驶域先例，宜引用防误读；(b) Conformal Risk Control under Non-Monotone Losses（arXiv:2604.01502, 2026-04）与 Probabilistic Object Detection with Conformal Prediction（arXiv:2605.07549, 2026-05）应进 §2.3 的 2026 边界；(c) UAV-OBB（Data in Brief 2026）的双标 IoU-QA 与本文度级圆周分歧审计的差异可作表 7/8 novelty 的划界证据。
- AI4IM 2026 watchlist 项：同意仅列 watchlist，不作依据。

### C-7｜"主稿当前数字与引用不可投稿"（C.md 台账第 4 行）→ **adopt，并扩充修正清单**

- C 列出的三处（DOTA NRC、PSC 作者、DIOR-R 出处）全部成立。B 阶段一另发现五处 C 未提的主稿必修/应修项，请求 C 逐条裁定并入同一 correction 清单：
  1. **表 4/5 的 D_audit 人群未披露**，且 §7.1"full-validation matched predictions"与 `m1_ar21_unify.py:157-175`（mask ∩ audit、denominator=audit.sum()、evaluation_scope=D_audit）直接冲突；同口径下表 3 n=49,502 vs 表 4 n=25,065 全文无解释（阶段一 F2）；
  2. **认证置信参数 δ=0.1 未写入论文**（`a1_protocol_frozen.json` 有，正文无；阶段一 F3）；
  3. **FAIR1M 实为本地冻结 train_80/val_20 划分**（官方 val annfiles 为空），§7.1"既有 trainval/test 协议"措辞不准确（阶段一 F4；无泄漏证据，整图级切分）；
  4. **表 1 两行分别取自唯一 practical 点（unit C，target-GT 上界分数）与唯一 trivial 点（unit F，TTA，α=0.01）**，条件未标注，"417 母景"与"576 母景"并置易误读（阶段一 F5）；
  5. 表 2 六行生成路径不对称：3 个重推理单元（DIOR-R/61、FAIR1M/24、SODA-A/4）的结果 JSON 无 GT/pred sha256（阶段一 F6）。
- 另两项表述级建议（阶段一 F7/F8）：扰动叙事重心移到"ΔAP50=0 + 壳内角剂量"（AP75 下降部分为构造使然）；在 §6.1 或 §12 显式承认认证事件以 GT 匹配为条件、部署化需要 GT-free eligibility 代理。

### C-8｜A 保持 measurement-only（台账第 1 行）→ **adopt**（收敛，无分歧）

### C-9｜B5 revise、B6 暂停待统计重审（台账第 2–3 行、sug.md）→ **adopt**

- 顺序正确：estimand 修复与可执行 gate 先行，B6 后议。sug.md 的前置完整性门、固定协议、三态 gate 与早停顺序设计完备；仅补充 C-1 中的两点实现建议。thresholds.yaml 冻结哈希已验证：仓库 blob SHA-256 = `b7c4e649…` 与迁移清单一致，工作树差异纯为 CRLF checkout——C 的换行警告准确且必要（sug.md §2.3 的"raw bytes"表述可直接采用 `git show HEAD:configs/thresholds.yaml | sha256sum` 作为服务器端标准命令）。

### C-10｜"当前不应投稿；修复后按 TGRS 及以上重评"（C.md 头部）→ **revise**（唯一实质分歧，范围很小）

- 一致部分：今天不可投（F1–F5 + 三处引用/事实错误未修，双方一致）；统计修复与主稿修订是硬前置，一致。
- 分歧部分：**独立确认单元是否为投稿硬门**。C 把"独立确认"列入重评前置四条件之一；B 认为对一篇主结论为负结果的 measurement-only 论文，v077 §12 已如实披露 `NO_ELIGIBLE_CONFIRMATORY_UNIT`，可作为已定价风险随稿提交，确认单元是"强烈建议"而非"硬门"。
- 最小裁决路径（转 experiment，不再语言争论）：按 C.md §3 C1 行执行一次新单元复算（未参与协议设计、full-universe、provenance-clean、持久化完整；以 SeqCRC 风格通用基线并行）。
  - pass：新单元方向性复现协议主结论 → 确认单元入稿，分歧消失；
  - fail：主结论方向翻转 → 不仅不能投稿，主 claim 需收缩，C 立场自动胜出；
  - inconclusive（资产/provenance 门不过）：是否带披露投稿由作者/用户裁决，B 维持"可投但风险自担"意见，C 维持更严意见——此时为价值判断而非证据问题，按协议停止争论。
  - 早停：若该单元成本超出一轮服务器预算，直接进入 inconclusive 分支。

## 6. 双向遗漏与证据强度汇总

- B 阶段一遗漏、C 发现且 B 已验证采纳：B3/B4 estimand mismatch（C-1）、B5 硬编码 gate（C-2）、PSC 作者（C-4）、DIOR-R 出处（C-5）。原因如实记录：B 阶段一把深度集中在 active manuscript A 的数字生成端与统计协议，未进入 paper_B 脚本内部与参考文献作者层。
- C 未提、B 阶段一发现待 C 裁定：F2（D_audit 人群披露）、F3（δ）、F4（FAIR1M 措辞）、F5（表 1 条件）、F6（sha 不对称与预注册不可 Git 验证）、F7（扰动叙事）、F8（GT 条件认证语义）、F9 补充文献三项、F10 次要项（表 4 可印 CI、DOTA 不入前沿原因、a5 分层支持 ar≥2.1、δ₀.₇₅(2.1)=15.4°）。
- 双方独立收敛（最高置信）：DOTA NRC 口径混用；novelty 只能定位为协议+负结果；A_MEASUREMENT_ONLY 维持。
- 本轮后剩余分歧集恰为一项：C-10 的"确认单元是否投稿硬门"，已给出最小裁决实验与三态 gate。

## 7. 给 C 的最终意见

1. C 的统计发现（C-1/C-2）是本轮最高价值产出，B 全部独立复现，无保留采纳；sug.md 可直接执行，附 B 的两点实现建议。
2. 请 C 对 B 独有的 F2–F5（主稿必修）与 F6–F8（应修/表述）逐项给出 adopt/revise/reject，以便合并为单一 manuscript correction 清单（本轮双方均不改主稿）。
3. B 不是裁决者：C-10 分歧按第 5 节的 experiment 路径处理；无新证据前 B 不再重复立场。

——STAGE_2 结束。
