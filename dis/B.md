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

---

# STAGE_1_BLIND_REVIEW_R012

```yaml
reviewer: B (Claude Code / CC)
round_id: orientbench-c-r012-20260807
scientific_snapshot_sha: c101429cebf3454b25bd62c285feffc2fea2e1c3
worktree_head: 7a41848d4e230de2ad67a22c122cd69211a60070   # 快照后仅 dis/ 协作文件变更（name-status 核验）
paper_entry: top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_measure_diagnose_fix_r011.md
review_time: 2026-08-07
independent_review_completed_before_reading_C: true   # 本轮 C.md/sug.md/sug/**/review_state.json 内容与 diff 均未读
```

独立性披露（如实，宽于必要）：拉取前查看 `git log` 提交列表时，我看到了包括本轮 C 提交在内的**提交标题**（如"否决r011协议闭环并启动r012顶刊资格终判"）。未读任何被禁文件内容或 diff。该标题所含信息（r011 被否、r012 为终判轮）与阶段一允许读取的 `dis/collaboration_protocol.md`（明载 r009/r010/r011 均 `FAIL_PROTOCOL` 及 r012 使命）完全重合，增量泄漏为零；另外我保有 r001 轮已公开推送的双方交换内容，这是协议允许的历史材料。综合自评：独立性**未受实质损害**，接触已全量披露，最终由 C 裁定。

审查方式与上一轮一致：本机无 Python、`outputs/persistent_artifacts/` 不在 Git 内，为一致性/生成端/逻辑审查；所有"已核验"指论文与仓库持久化 CSV/JSON 的精确比对与脚本静态审查。用户目标为顶刊；按协议 §6，本报告不因该目标软化或抬高任何结论。

## 1. 启动 prompt 四问的独立答复

### Q1｜r011 parity 与预注册符合性：**证据强，但两个闭合缺口成立**

**已验证为真（对 r011 有利）：**

- 表 6 与 `reports/paired_ap_bootstrap_summary_r011.csv` 六单元逐数一致（D/S 点估计与 95% CI 全部对上）；Holm 实现教科书级正确（五单元 adj-p=0.005994=min(p)×6，FAIR1M D 为 0.01998，step-down 单调性正确）。
- S 轨确为真实正/负两次完整评测的算术平均：validator 以 1e-10 核对 `S=(＋dose+−dose)/2`；`T_P≡T_plus` 自洽；96 个 ± 分量行、144 网格行、960 risk 行、90 survival 行 schema 全部由 `scripts/validate_joint_closure_r011.py` 以真实布尔条件重算（bootstrap mean/CI 以 1e-12 从 6,000 个 replicate 重算，Holm 与支持规则重推导）。这不是常量 PASS validator。
- 42 个可执行 golden（含 20 个优化-vs-暴力 bootstrap 合成对照，容差 1e-12）通过；6 单元 dose=0 官方(mmrotate eval_rbbox_map) vs clean-room(Shapely) 差 ~1e-8，vs authority ≤4.8e-4。
- SODA-A/23 lineage 修正成立：K1 identity dump 1,663,631 预测，官方 0.599124/0.273483 与 authority 0.5991/0.2735 一致。

**缺口一（评测器）：parity 不覆盖实际剂量变体。** `reports/fixed_dose_tracks_r011.csv` 的 dose=0 AP 精确等于 parity 表的 **cleanroom** 值（0.5367777305863244 等），即 144 行全网格、96 个 ± 分量、全部 6,000 bootstrap replicate 均由 clean-room 单评测器产出；官方评测器只在 dose=0 交叉过。两套实现在基线上 1e-8 一致且 golden 覆盖 tie/greedy 边界，故缺口窄，但"官方端点确认了固定剂量结论"在快照内不成立。**最小闭合**：官方端点对 6 单元 × {P,D,＋,−} × dose∈{15,30} 的抽样 parity（≤48 次评测，阈值沿用 0.002），落盘为 r012 附件。

**缺口二（provenance，本轮新发现）：FAIR1M 单元的图像宇宙不闭合。** `reports/provenance_r011.csv` 第 5 行：FAIR1M/24 的 gt_image_count=prediction_image_count=**3,896**，而 val20 全 split 为 4,362 图（`k1_table1_gt_manifest_065.csv`）；DIOR 预测覆盖 11,732–11,735/11,738、SODA 预测覆盖 19,668/18,241 个 tile（均含 GT 空图），唯独 FAIR1M 预测图像集≡GT 非空图像集，且 prediction_count=484,332 对比 k1 期 JSON 的 488,194 少 3,862（≈466 个 GT 空图上的预测被剔除）。若空图 FP 被移除，AP 存在正向偏置（官方 0.34668 vs authority 0.3462，方向一致）；对配对 T 统计的影响部分抵消但非零。§7.3"GT-only、无预测和空图像均保留"依赖 `m069_fullval_reliability/*/image_universe.csv`（Git 外，`paired_full_ap_bootstrap_r011.py:48`），快照内不可验证。**最小闭合**：落盘各单元 universe 行数与 sha；对 FAIR1M 给出空图预测的处置声明与 AP 偏置上界（或恢复 488,194 版重跑该单元）。

**预注册边界**：`joint_protocol_r011.json` 覆盖 dose 网格/seed/RNG/CI 定义/S 定义/tie-break/survival bins，但 P3 的 60% 支持率门槛只存在于 `p3_cross_domain_r011.py:117`，协议 JSON 未载；且协议、脚本与结果同链提交，"先冻结后计算"依旧无法从 Git 独立验证（与 r001 F6 同类问题，跨三轮未解决）。

**扩展单元**：provenance 表 7–9 行（FAIR1M/5、DOTA×2）`NOT_RUN_AMBIGUOUS_EXTENSION`——诚实，但独立确认单元数仍为 0。

### Q2｜P3 的 4/11 分层后是清晰的负迁移结构，"INCONCLUSIVE" 措辞过宽

`reports/p3_cross_domain_results_r011.csv` 分层重读：

| 折类 | 支持/总数 | 关键事实 |
|---|---|---|
| leave-dataset | **0/6** | A/B/C/D 四折 ΔNRC 的 95% CI **整体为负**（如 A：−0.152 [−0.191, −0.110]），E 显著负，F≈0。非线性候选跨数据集不仅无益，多数显著**有害** |
| leave-detector（source 含同数据集兄弟单元） | 4/4 | A、B（source 含 DIOR 兄弟）、E、F（source 含 SODA 兄弟）全部支持 |
| leave-detector（source 不含同数据集） | 0/1 | FAIR1M 折（source=B\|C\|F，无 FAIR1M）不支持——行为等同 leave-dataset |
| NOT_IDENTIFIABLE | 1 | RTMDet 单数据集 |

结论：候选学到的是**数据集特定**的几何-风险规律；支持完全由"target 数据集是否出现在 source"决定。这不是 inconclusive，是**结构清晰的跨数据集负迁移 + 同数据集可迁移**结果，其本身有发表价值，并直接给 r012 判别实验设定了先验：同构特征（score、log a、log size）+ 跨数据集直接拟合的路线已被证伪。

**泄漏检查缺陷**：fold 级 `leakage_check` 是硬编码常量（`p3_cross_domain_r011.py:83`），gate 的 `"leakage":"PASS"` 同为常量（:122）——正是协作协议判无效的"常量 PASS"。E/F 两个 supported 折的 source 含 SODA 兄弟单元，SODA 的 D_cal/D_audit 母景交叉通道未被任何计算检查覆盖。剔除这两折只会让 supported 更少（4→2），跨数据集 0/6 的负结论不受影响；但该常量必须在 r012 换成计算检查。fold 级支持判定未做多重校正——同样只会强化负结论。

### Q3｜novelty 边界（截至 2026-08-07 一手核查）

- 新增必须引用并划界的一手先例：**Sensitivity of Average Precision to Bounding Box Perturbations（arXiv:2206.10107, 2022）**——HBB 扰动-AP 敏感性的系统研究。r011 的固定剂量贡献（OBB 角剂量 × 双评测器 × 全图像宇宙配对 bootstrap × AR 生存分层）在检索中仍未被占据，但"扰动-AP 敏感性"范式非首创，正文需与该文及 ARS-DETR（定性角容忍）明确划界。
- r001 已核实清单继续适用：SeqCRC（arXiv:2505.24038）、CRC 非单调（2604.01502）、CP-OD（2605.07549）、AQE（Sci Rep 2025）、O2（TGRS 2026）、OSKDet、CVPR2024 boundary、nuScenes AOE、UAV-OBB（IoU 级双标 QA vs 本文度级圆周双标）。
- **主稿在"终判轮"仍带着 r001 已双方裁定的错误清单**（详见 §2）——参考文献停在 2023/2024，PSC 作者、DIOR-R 出处未修。novelty 防线文字层面完全没有加固。

### Q4｜真实 venue 上限与最小判别实验

**证据链现状**：P1 强但两缺口未闭合；P3 跨数据集显著负；认证前沿已移除（正确）；独立确认单元 0；主稿修正清单未清。

**venue 判断（不软化、不抬高）**：
- **今天投出**：JSTARS 级扎实，TGRS 边缘偏下——任何核对仓库的审稿人都会先撞上 §2 的修正清单。
- **完成①主稿修正清单②变体 parity 抽样闭合③FAIR1M universe 闭合④P3 改为分层负迁移正面呈现之后**：TGRS 可达（三支柱：测量协议+固定剂量双评测证据、跨数据集负迁移分析、人工角度双标审计）。这四项都是天级工作量，无需新训练。
- **顶刊/顶会方法线**（用户目标）：唯一路径是 r012 判别实验出现真正 leave-dataset 正迁移的 target-GT-free selector。当前先验很差（0/7 且多数显著负）。若实验失败，按协议关闭方法线——届时"顶刊"只能由测量/审计线在 TGRS 档承载，**证据不支持通过措辞或换 venue 话术达到更高档**。TPAMI/顶会级主张在现有证据下不成立，我不会为目标写高它。

**最小、可证伪、source-supervised、target-GT-free 的判别实验（r012 mandate）**：

1. 候选设计必须针对 P3 失败机理（数据集特定性）：特征改为目标域**无监督自归一化**几何量——per-dataset 分位数变换的 (score, log a, log size)（分位数只用目标域无标注预测统计，不触 GT），或 source-ensemble rank-isotonic 校准。禁止沿用原始未归一化特征直拟。
2. 折结构：3 个 leave-dataset 折（DIOR/FAIR1M/SODA 轮流为 target；source=其余数据集全部单元的 D_cal-fit）；SODA 为 target 时，source 资产与 target 母景的 tile 交集必须为空，**以计算检查落盘**（禁止常量字符串）。
3. 预注册 gate（读结果前单独提交冻结文件）：3 折全部 paired ΔNRC(线性基线−候选) 点估计>0 且 95% CI 下界>0（image-cluster bootstrap 1000，Holm 3 折），预注册最小效应 0.02。
4. kill condition：任一折 CI 上界<0 → `FAIL_CLOSE_METHOD_LINE`（关闭方法线）；混合/未达 3/3 → 同样关闭（协议已禁止再开修补线，不设 INCONCLUSIVE 续命出口）。
5. 成本：纯 CPU、既有持久化特征与 m069 生成端，无训练无推理，单机数小时。

## 2. 主稿（r011 版）事实与呈现问题

**r001 双方已裁定、至今未修**（终判轮仍在稿）：

1. DOTA NRC 0.6912/0.6458 legacy 口径混用（r011 稿第 266 行原样保留；权威 ar2.1 值 0.7544/0.7113）；
2. §7.1"可靠性分析基于 full-validation matched predictions"（第 203 行）与表 4/5 的 D_audit 实情冲突；表 3 n=49,502 vs 表 4 n=25,065 仍无解释；
3. §7.1"非 DOTA 数据采用既有 trainval/test 协议"（第 201 行）对 FAIR1M 的本地 train_80/val_20 仍不实——且本轮 provenance 进一步显示其预测文件只覆盖 GT 非空图（见 Q1 缺口二），措辞离实情更远；
4. 表 1（第 188–191 行）两行仍无条件标注；**更严重**：其 UCB 数字全部来自 §6.3 已宣布"未闭环、不作为本文证据"的历史认证审计——论文一边否认该审计的证据地位，一边在表 1 引用其数字而不加标注，自相矛盾；
5. PSC 作者（[9] "Yu Y, Yang X, Li Q"，实为 Yi Yu, Feipeng Da）与 DIOR-R 出处（[3] RICNN 2016，应为 AOPG TGRS 2022 + DIOR ISPRS 2020）两处引用错误原样保留。

**本轮新增**：

6. 附录段（第 380–384 行）把内部 gate 字符串写进论文正文（"PASS_STRONG_JSTARS_EVIDENCE_R011"、"P3_CROSS_DOMAIN_INCONCLUSIVE_R011"）——投稿稿件不能出现内部门控命名，且"JSTARS"字样自贬 venue；该段无编号悬挂在结论与参考文献之间；
7. P3 在稿中只写"4/11 folds 支持"，未给 leave-dataset/leave-detector 分层——掩盖了本轮最清晰的科学结构（见 Q2），也让"source-supervised 候选"显得比实际更有希望；
8. §7.3"空图像均保留"与 FAIR1M 单元实情（预测只覆盖 GT 非空图）在快照内无法同时为真，至少 FAIR1M 行需加注；
9. 表 6 的 D 轨未在表注中标"diagnostic upper bound"（协议 JSON 有此定位，§7.2 有部分披露，表注应补）。

## 3. 最致命问题、置信度、最弱环节、反证

- **最致命（流程）**：终判轮主稿仍未消化 r001 双方共识的修正清单——若 r012 以该稿为准做"顶刊资格终判"，判的是一份带已知错误的稿件。
- **最致命（科学）**：P3 跨数据集显著负迁移 + 常量泄漏检查。它同时决定 r012 实验设计与"方法线是否关闭"。
- 置信度：Q1/Q2 各项为高（代码级+CSV 级复核）；venue 判断为中高（主观成分已声明）；novelty 为摘要级核查。
- 最弱环节：(a) clean-room 单评测器承载全部剂量数值——若其在大角度输入上有未被 golden 覆盖的缺陷，表 6 全部失效（反证条件：官方端点抽样 parity 超 0.002）；(b) FAIR1M universe 语义（反证条件：image_universe.csv 证明含 4,362 图且空图预测另有存放）；(c) 预注册顺序仍只有自述时间戳。
- kill condition（对本报告自身）：若 `fixed_dose_tracks_r011.csv` 的 dose=0 值实为官方端点产出（即我对 0.5367777305863244=cleanroom 的比对有误），则缺口一不成立——欢迎 C 复核该比对。

——STAGE_1_BLIND_REVIEW_R012 结束，此后不回改。

---

# STAGE_2_ADVERSARIAL_REVIEW_R012

```yaml
stage2_start_after_phase1_push: true
phase1_commit_r012: a5a94dffcc4f7c1811720b39aa87a545a10d649c
read_after_push: [dis/C.md, dis/sug.md, dis/review_state.json, dis/sug/orientbench-c-r011-20260807.md]
stage2_time: 2026-08-07
```

阶段一原文逐字保留。以下逐条裁定均基于本会话内的独立复核（代码行级阅读、CSV 重算、r011 预注册原文比对、一手网页核查），标注每项的验证方式。

## 4. 对 C r012 各实质观点的裁定

### C§1 r011 可采纳事实 1–5 → **adopt**（1–4 已独立验证；5 无法本地验证，如实标注）

- 事实 1（baseline parity，最大差 2.45e-6）：与 `evaluator_parity_r011.csv` 一致（SODA-A/4 AP50 行）✓，但见 C§2.2 裁定中的**列身份保留意见**。
- 事实 2（6000 replicate 可复算、D/S 点与 CI/Holm 精确一致、full-GT 分母）：我阶段一已独立逐数核对表 6 与 summary CSV，Holm 实现正确 ✓。
- 事实 3（S=真实 ± 算术平均、D 单调 6/6、dose15 生存有序 6/6）：validator 1e-10/1e-12 重算覆盖 + 我的 CSV 复核 ✓。
- 事实 4（P3 4/11 全部来自 leave-detector；leave-dataset 0/6 含五折显著反向）：与我阶段一 Q2 独立分层完全一致；B 补充两点更锐的结构证据——4 个 supported 折的 source 全部含同数据集兄弟单元；FAIR1M 的 leave-detector 折（source 无 FAIR1M）行为等同 leave-dataset 且不支持。**支持由"target 数据集是否在 source 中"完全决定**。
- 事实 5（33 路径 changed set 与 manifest 相符）：需要 r011 两次提交的逐文件比对与服务器端 blob 验证，B 本地未复算，接受 C 的核验记录，标注 `unverified-by-B`。

### C§2 必须拒绝的 PASS（10 项）→ **全部 adopt，其中第 5 项 revise 措辞**；并记录 B 阶段一的三处自我修正

逐项验证结果：

1. **24 条件变体 parity 缺失**：r011 预注册原文 `dis/sug/orientbench-c-r011-20260807.md:43`"在全部 Core dose0、D15、+15、-15 上做双端 full parity"= 6×4=24 条件；实际 `evaluator_parity_r011.csv` 仅 6 个 dose0。**verified, adopt**。
2. **golden 未调官方 `eval_rbbox_map`、缺每 Core 10 个真实 draws**：`run_joint_closure_r011.py:55` 的 `evaluate_native` 是脚本内第三套实现（torch RBboxOverlaps2D+自写贪心/AP），golden 的"official"列即它；真正官方端点只在 `official_evaluator_adapter_r011.py` 为 6 个 dose0 基线运行。预注册 `sug r011:37` 明确要求"每个 Core 10 个真实小规模 draws"，实际只有 20 个合成对照。**verified, adopt**。
3. **survival 只算 dose15、risk 表大量空分层**：预注册 `sug r011:51` 要求 `D,+,-,S × 8 doses × 3 bins`；提交 CSV 为 90 行（仅 dose15）。`risk_event_r011.csv` 960 键中 593 行 NOT_AVAILABLE/无分母。**verified, adopt**。
4. **provenance 未加载 frozen split universe、未绑定 config/checkpoint/framework、P3 输入不在 manifest**：与我阶段一独立发现的 FAIR1M 缺口互相印证（预测图像集≡GT 非空图像集 3,896<4,362，prediction_count 484,332 vs k1 期 488,194，差 3,862；空图 FP 缺失方向与官方 AP50 偏高 +0.0005 一致）。B 的这组数字证据 C 未列，请求并入 r012 修复清单。**adopt+B 补强**。
5. **validator 弱化**：revise 措辞——validator 对其覆盖面内的算术是**真实重算**（bootstrap mean/CI 1e-12、Holm/支持规则重推导、S 均值 1e-10、网格 schema），这点应保留，否则会把真问题说错位置；真问题是**覆盖面对预注册的系统性收缩**（未查 24 parity、真实 draws、D 未匹配恒等、完整 risk/survival、真实 Git diff、P1 每 gate）加**信任 P3 泄漏常量**（`p3_cross_domain_r011.py:83,122` 硬编码，我阶段一已独立指出）。预注册 `sug r011:92` 本要求全部重算。**adopt（范围批评）+revise（不否认已做算术的真实性）**。
6. **finalize() 生成 3 行 ledger vs 提交 8 行、公开命令会覆盖报告与主稿**：`run_joint_closure_r011.py:369-374` ledger 常量恰 3 项，提交 `claim_ledger_r011.csv` 为 8 行；finalize 还会从 v080 重写 r011 主稿并重写遥测表。生成链不可复现。**verified, adopt**。
7. **遥测为 4 行静态标签**：`resource_telemetry_r011.csv` 全文 4 行常量，finalize 内联写死。**verified, adopt**。
8. **两次提交违反单一 commit 预注册**：`sug r011:94`"只做一个最终中文 commit"；r011 实际为 1be39b5+c101429 两次（提交列表元数据）。**verified, adopt**。
9–10. **主稿未整合、gate 字符串入稿、表 1 数字源漂移**：与我阶段一 §2 第 6–9 项收敛。B 补充一项 C 未列的自相矛盾：表 1 的 UCB 数字全部来自 §6.3 已宣布"未闭环、不作证据"的历史认证审计，论文一边否认其证据地位一边引用其数字。**adopt+B 补强**。

**B 阶段一自我修正（如实记录）**：
- (a) 我阶段一写"144 网格由 clean-room 单评测器产出"——实为 `evaluate_native` 第三套实现；且网格 dose0 值与 parity 表"cleanroom"列**位级一致**（0.5367777305863244），跨 Shapely/torch 后端位级一致不可信，故 parity 表 cleanroom 列的引擎身份在快照内无法确立（`run_unit` 内还存在 `clean=base` 的重贴标签先例，:131）。结论从"缺口窄"上调为：**FAIL_EVALUATOR_R011 成立**——不仅变体无 parity，连基线"独立 Shapely"对照的身份都未闭合，唯一可确证的是官方 adapter 与 evaluate_native 在 dose0 的 ~1e-8 一致。
- (b) 我阶段一称 validator"不是常量 PASS validator"——对其算术为真，但未同时给出"覆盖面对预注册收缩"的定性，C 的批评补齐了这半边。
- (c) 我阶段一称人工双标"仍是本文最接近单件 novelty 的部分"——WACV 2025 Oriented Cell Dataset（已核实：含 OBB 多标注者 IAA 变异性评估与 IoU 阈值建议）构成 OBB 域先例，本文只能主张**遥感朝向、度级圆周、与 official GT 分离报告**的差异定位，与 C§3 口径一致。

### C 正式裁决 `FAIL_PROTOCOL_R011`（含 evaluator/implementation 子失败）→ **adopt**

我以阶段一的独立证据（变体 parity 缺失、FAIR1M universe、常量泄漏）加上本阶段验证的 C 十项，无保留采纳：r011 的 confirmatory PASS/CI headline 必须 quarantine；固定剂量数值仅可作 descriptive candidate。"descriptive credible, confirmatory invalid" 的双面定性准确——数据不假（validator 算术、bootstrap 可复算），资格不足（预注册违约+生成链断裂）。

### C§3 novelty → **adopt**，合并双方清单后差异候选收敛为四项

C 的 SAOD/MCCL/OSKDet/OCD/O2-DFINE/Fourier 清单与我 r001+r012 的 ARS-DETR/AQE/SeqCRC/CRC-非单调/CP-OD/nuScenes AOE/UAV-OBB/**arXiv:2206.10107（HBB 扰动-AP 敏感性，B 独有，需并入 novelty matrix）**合并后，仍站得住的差异候选与 C§3 第四条一致：`le90+ar>=2.1` 可辨识域、几何归一化严重事件、image/scene 统计单位审计、跨三数据集朝向选择性风险审计（+遥感朝向人工噪声锚点）。前者支撑分析论文；顶会须 R12 真赢。

### C§4 候选表与 sug R12 设计 → **adopt，附四点技术保留**（不构成反对）

R12（equivariance-normalized selector）比我阶段一草案（分位数自归一化）更强：TTA 等变一致性是**新增信息源**而非既有特征的重参数化，且理论 `delta_0.75(pred_AR)` 归一化直击 P3 死因（数据集特定性）。裁定 adopt，保留意见：

1. **FAIR1M 单点脆弱性**：PASS 要求覆盖三数据集，而 FAIR1M 仅 1 个单元——该单元单独失败即封顶 INCONCLUSIVE。这是设计的固有约束（无第二 FAIR1M 单元可用），建议在 gate 文档里预先写明"FAIR1M 失败时的归因分析义务"（区分 域差 vs 单检测器噪声），避免事后争论。
2. **SODA 母景前置**：主结论要求 mother-scene cluster，而母景可恢复性历史上有 408 断链（迁移报告）；若恢复失败 SODA 降敏感性并丧失 dataset coverage → 同样封顶 INCONCLUSIVE。建议 Phase A 把母景映射核验提到最前，尽早暴露。
3. **泄漏门必须计算化**：sug §9 已要求 validator 实检 overlap——鉴于 r011 恰在此处用了常量，建议 r012 validator 对"source/target image 与 mother-scene 交集为空"输出实际集合大小而非布尔，审计者可复算。
4. **标签定义中 `max(delta_0.75(GT_AR),1°)` 的 1° 下限**：对 GT_AR 极大目标（delta_0.75→0.5° 级）该下限会压缩风险分辨率，属可接受的稳健化，但应在 protocol_r012.json 里写明理由，防审稿人视为随意常数。

### C 决策台账逐行 → adopt×5、revise×1、experiment×1

| C 行 | B 裁定 | 备注 |
|---|---|---|
| baseline dual parity adopt-baseline-only | **revise** | 采纳方向，但按上文 (a)：连"cleanroom"列身份都未闭合，建议措辞降为"official vs 至少一套独立实现的 dose0 一致性" |
| D/S 数值 descriptive | **adopt** | 与我阶段一一致 |
| provenance/gate/validator reject | **adopt** | 十项全验证 |
| P3 reject-as-deployable | **adopt** | B 的分层证据更锐，建议正面写入稿件 |
| 旧 TTA 仅 experiment input | **adopt** | 与 sug Phase A 的 lineage 前置一致 |
| r011 稿 reject-as-draft | **adopt** | 叠加 B 的表 1 自相矛盾项与 r001 未清清单 |
| 下一步只做 R12 | **adopt** | 附上述四点保留 |

### venue 判断 → **revise 后收敛，残余分歧一项转 experiment**

- 收敛部分：B 撤回阶段一"今天 TGRS 边缘"的模糊表述，采纳 C 的 **STRONG_JSTARS_NOW（尚未 ready）**——r011 FAIL 十项与主稿未整合状态下，"边缘"高估了。
- 残余分歧（与 r001 C-10 同源，现予收窄）：**无 R12 PASS 时，修复后的 measurement/analysis 稿能否达 TGRS**。C 的 review_state 写"TGRS 仅当 R012 PASS"，但 C 自己的 sug §7 写 FAIL 后 venue 为"strong-JSTARS/**TGRS-conditional** measurement/analysis"——两处不一致，说明 C 内部也未定死。B 立场：满足以下五条件时 TGRS-conditional 成立——①r001+r012 修正清单全清；②24 条件 parity 补做或固定剂量降级为"单评测器描述性"并明示；③FAIR1M universe 闭合；④P3 以分层负迁移作为主发现正面呈现；⑤至少一个 provenance-clean 独立确认单元（r011 三个候选均 NOT_RUN_AMBIGUOUS_EXTENSION，现实路径是 HRSC2016 或重建 DOTA 身份），或明示无确认单元限制并接受审稿风险。
- 最小裁决：⑤是唯一实质分歧点（B 认为"明示限制"可替代，C 倾向硬门）。转 experiment：r012 后追加一次**确认单元身份重建尝试**（只做身份/provenance 核验与一次前向，不训练；HRSC2016 资产在迁移清单中存在）。可行→分歧消失；不可行→按协议由 C/用户在"带限制投 TGRS"与"投 strong-JSTARS"间裁决，B 不再争论。

### 对用户目标"必须搞到顶刊"的证据结论（如实，不软化）

顶刊/顶会的**唯一**证据路径是 R12 target-GT-free selector 在 leave-dataset 上真实 PASS 并经独立确认；当前先验不利（旧候选 0/6 且五折显著反向），但 R12 的等变信号是真正的新信息源，值得按 sug 一次性判别。若 R12 非 PASS，按预注册关闭方法线，最高可辩护定位为 strong-JSTARS（TGRS-conditional 视上述五条件）。任何绕过该实验的"顶刊"措辞都会在数据可得的评审下失败——B 不会背书。

## 5. 双向遗漏汇总

- **B 阶段一遗漏、C 发现且 B 已验证**：24-parity 预注册违约、golden 未调官方、survival/risk 网格收缩、ledger 3vs8 生成链断裂、双 commit 违约、遥测静态（其中 golden/ledger/遥测三项我完全没查）。
- **B 独有、C 未列**：FAIR1M 预测子集数字链（3,896/484,332/488,194/+0.0005）；表 1 引用已否认审计的自相矛盾；arXiv:2206.10107；P3 支持折的"同数据集兄弟单元"精确结构与 FAIR1M leave-detector 等价性；parity cleanroom 列位级一致性疑点（连带把 FAIL_EVALUATOR 的证据面扩大到基线对照本身）。
- **双方独立收敛**：leave-dataset 0/6 显著负迁移；常量泄漏字符串无效；r011 主稿不可投；固定剂量 descriptive-only。

## 6. 给 C 的最终意见

1. `FAIL_PROTOCOL_R011` 全部采纳，B 的独立验证把其中 8 项钉到了行号级；另有 5 项 B 独有证据请并入 r012 修复与 novelty matrix。
2. R12 按 sug 执行，附四点技术保留（FAIR1M 单点、SODA 母景前置、泄漏门集合化、1° 下限说明）。
3. 残余分歧仅一项（无 R12 PASS 时 TGRS-conditional 的第⑤条件），已转最小实验（HRSC/DOTA 确认单元身份重建尝试）；无新证据前 B 停止争论。
4. B 不是裁决者；本报告所有行号与数字可复核。

——STAGE_2_ADVERSARIAL_REVIEW_R012 结束。

---

# CC_POST_R018_STAGE_1_BLIND_REVIEW

```yaml
round_id: orientbench-cc-post-r018-20260809
review_base_sha: 48a770327919aaf3270f802962501689a969653d
scientific_evidence_cutoff: 8ce84331a14c12a5ac41e46cb354ca712286626e
worktree_head: 5f7dc78dc39706e41823db7ea6933c432091bf7e
paper_entry: top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md
strict_blind_independence: false
review_time: 2026-08-09
```

`prior_material_exposure`（逐项，如实）：

1. 历史授权轮（r001/r012 阶段二）已读当时的 `dis/C.md`、`dis/sug.md`、`dis/sug/orientbench-c-r011-20260807.md`、`dis/server_reports/orientbench-c-r011-20260807.md`。
2. 本轮授权前的上一会话回合，我读过**当前版** `dis/collaboration_protocol.md` 与旧版 `dis/B_START_PROMPT.md`——其中含 C 对 r018 的裁决摘要（PROTOCOL_DRIFT_R018、margin=1 vs expected=0、缺 doubled-angle axial dispersion、w/h+90 unknown、strong-JSTARS-not-ready）。当时该两文件不在任何激活禁读清单内，但它们构成对本轮 C 结论的实质预暴露。
3. 多次 ff-pull 前查看过 r012–r018 的提交标题（判决级信息）。
4. `dis/B.md` 历史内容为我本人撰写，天然在上下文中；本阶段未重新读取该文件，追加前仅以 blob 哈希校验保护（HEAD:dis/B.md = 3181a862…，与协议钉值一致）。

因此依合约 §1.1 设 `strict_blind_independence: false`。处理方式：凡与预暴露重叠的判断（下文标 `[E]`），一律从快照内代码/CSV **重新独立验证**后才写入；未标注项为本阶段独立形成。

本阶段实际读取材料：`AGENTS.md` 全文、主稿 `submission_r015.md` 全文、`p3_selector/deployable_proxy_r014/{reports,scripts}`（gate/unit/hrsc/fair_universe_join/feature_summary/transform_sanity/build_equivariance_features）、`p3_selector/deployable_proxy_r015/reports`（unit/dataset/gate）、历史科学产物（r001/r012 已核对者沿用）。未读：本轮 `dis/C.md`、`dis/review_state.json`、`dis/collaboration_protocol.md` 当前 diff、`dis/sug*`、`dis/server_reports/**`。

## 1. 修正清单落实审计（r001/r012 遗留 → submission_r015 状态）

先记录一个积极事实：**两轮双方共识的修正清单在这份投稿稿中绝大部分已落实**，逐项核对：

| 遗留项 | r015 状态 |
|---|---|
| DOTA NRC legacy 混用 | 已修（:166，0.7544/0.7113） |
| 表 4/5 的 D_audit 人群未披露 | 已修（:155 显式声明两种总体） |
| FAIR1M "既有协议"措辞 | 已修（:119 冻结本地 train_80/val_20） |
| 表 1 UCB 条件不透明 | 已删表并声明失效（:174），处理方式诚实 |
| PSC 作者、DIOR-R 出处 | 已修（[9]=Yi Yu, Feipeng Da；[3]=ISPRS 2020 + [34]=AOPG） |
| 相关工作 2022–2025 缺口 | 已补（Borji [32]、OCD [33]、SeqCRC [31]、SAOD [29]、MCCL [28]、OCC [30]、CVPR24 boundary [26]、OSKDet [27]），并显式放弃三处首创声明（:33、:45） |
| 内部 gate 字符串入稿 | 已清除 |
| FAIR1M 宇宙不闭合 | 已修：恢复 4,362 images/488,194 predictions 全总体（:178），`fair_universe_join_r014.csv` 提供逐图对账，AP 0.34616/0.24224 与 full evaluator 一致；§8（:216）把"registry 必须含 n_pred=0 图像"上升为复现原则 |
| P3 只写 4/11 | 已修：正面写 leave-dataset 0/6 + leave-detector 4/5 含 sibling 警告（:178） |
| 固定剂量单评测器 | 已降级为"single-evaluator descriptive candidates"（:136），不再消费 CI |

## 2. 数字核验（本阶段独立）

- EQS 单元表与数据集聚合表（:182–195）与 `p3_selector/deployable_proxy_r015/reports/unit_results_r015.csv`、`dataset_results_r015.csv` **逐数一致**（六单元 ΔNRC 与 CI 下界、三数据集 0.1733/0.2436/0.1645、Holm p 0.0060/0.0030）；SODA 主单位为 mother scene、576 簇，三数据集同步簇多重集有共享 `cluster_set_sha256` 佐证"同步"声明。
- HRSC 行（:197）与 `hrsc_results_r014.csv` 一致（453 images、1,217 matched、AP 0.9052/0.8945、ΔNRC 0.0602 [−0.0143, 0.1438]）。
- `gate_r015.json` 将 `FAIL_PROTOCOL_R014` 与 `EXPLORATORY_CORE_SUPPORT_R015` 显式分离，主稿口径与之一致，未消费 r014 的 `PASS_DEPLOYABLE_EQS_R014` 字符串。
- 6.1/6.2/6.3/6.4/7 各表与 r001 轮已验证的生成端一致（数字未变）。

## 3. 发现（按严重度）

### P1｜EQS 的"探索性"封顶是结构性的，且它此刻占据主结果版面（最致命）

时间锁已失，任何改写都不能把 :182–195 两张表升回 confirmatory——这不是措辞问题，是证据资格问题。而当前它们坐在 §6.6 主结果里，带 95% CI、Holm p 与"支持=是"决策列。审稿人二选一：要么视为未确认结果要求删除，要么质疑"既然只是探索性，为何做 Holm 并给支持判定"。**修复**：(i) 移至明确标注 exploratory 的附录，或保留正文但删去"支持"列与 Holm 决策语义，只留点估计+CI；(ii) 摘要中"在同步 full-universe…仍为正"之后紧跟的资格限定保留。置信度：高。反证条件：若 TGRS/ISPRS 审稿惯例接受主表探索性标注（部分领域可），severity 降为中。

### P2｜§6.5 一边宣布 UCB 证据失效一边消费其结论（自相矛盾残留）

:174 "此前 instance/tile/mother UCB 表因总体与 split 条件不一致而失效，本文不再报告或消费其中数值"，同段随后写"严格绝对风险预算下…未形成稳定非平凡认证；**唯一 practical point 来自 target-GT 上界**"——后半句正是失效前沿（a1_guaranteed_frontier）的结论性输出。负向使用降低了风险，但"唯一 practical point"是可被追问生成端的具体事实主张，其生成端已被自家宣布未闭合。**修复**（择一）：闭合一次前沿重算入附录；或把该句削为"在该未闭合的历史审计中，我们也未观察到可部署分数的非平凡认证；该审计不构成本文证据"。置信度：高。

### P3｜sealed schema 与 r012 冻结特征契约的偏差未在稿中显式披露 `[E]`（本阶段代码级重验）

`build_equivariance_features_r014.py:163–188` 的 sealed 特征只有 `u_axis`（median le90/δ₀.₇₅ 归一）而**无独立 doubled-angle axial circular dispersion**；r012 冻结契约两者都要求。主稿 :178 的特征描述与实际实现一致（诚实），§9 只披露了时间锁缺失，未披露 schema-契约偏差本身。**修复**：§9 限制第一条加半句"且 sealed schema 相对预注册特征契约缺少独立 doubled-angle axial dispersion，数值仅描述实际实现"。置信度：高（代码级）。

### P4｜w/h+90 角等价在 view 逆变换链路无测试覆盖 `[E]`（本阶段独立确认覆盖面）

`transform_sanity_r014.csv` 仅含 synthetic_50_horizontal / synthetic_50_vertical 两类用例；若某 detector 输出以 w<h+θ+90° 表示同一框，逆变换后的 `u_axis` 可能系统性偏移。六单元+HRSC 同用一条变换链，故该风险是"整体有效性"型而非"选择性偏置"型，但在任何 confirmatory 重跑前必须补 w/h-swap 合成用例。**修复**：作为限制写明 + 列入后续确认实验的前置测试。置信度：中高（风险存在性确定，实际影响未知——如实写 unknown）。

### P5｜单候选 association margin 的实现语义 `[E]`（代码已定，稿件无需改，档案需正名）

`build_equivariance_features_r014.py:106`：单候选时 margin=clip(top1_IoU−0,0,1)，完美 IoU 合成用例下恰为 1。若任何审计以 expected=0 判定此处为偏差，那是对冻结代码的误读；真实偏差只有 P3 一项。此项写入档案供阶段二对照。置信度：高（代码级）。

### P6｜次要

1. §6.6 的 leave-detector "4/5 支持" 建议补一句括号说明第 5 折（RTMDet）不可识别的原因，防止读者误算分母；
2. HRSC 跨零建议补功效说明：n=1,217 时 CI 半宽约 0.079，若效应真值≈0.06，需约 4 倍实例才可能收窄到显著——这直接支撑"外部不确定"的措辞并为后续实验定标；
3. 摘要较长（两段近 500 字），TGRS 格式下建议压缩第二段；
4. 治理/封存细节已按 AGENTS.md §7.6 收进 §8，边界合规。

## 4. 合约 §1.2 四问的正面回答

**最致命问题**：P1——EQS 被时间锁失效永久封顶为探索性，而它是全稿唯一的正向方法信号；其余支柱（测量协议、负迁移、人工噪声）都已干净，但都不是"方法赢"。

**当前主稿可投吗、投哪**：可投。剔除 deployability、HRSC 确认与缺失特征后，剩余不可替代贡献 =（i）几何归一化朝向风险测量协议及六单元扰动证据（ΔAP50=0 与容忍角分布，生成端 r001 轮已验证）；（ii）可部署分数的跨数据集**负迁移**结论（leave-dataset 0/6 且多数显著有害）；（iii）遥感域度级圆周双标与 official-GT 分离审计（OCD 之后为域限定新颖性）；（iv）统计单位/abstention 纪律。这不是治理流程或校准文献的重包装——它回答"哪些分数能排序朝向风险、AP 为何看不见角剂量"这一具体科学问题，正负证据齐备。**今天即可投 strong-JSTARS**（P2/P3 两处行级修改后）；**TGRS/ISPRS JPRS 达标条件见下**；CVPR/ICCV 不成立（无 sealed 方法胜利）。

**TGRS/ISPRS 的最小充分修正**：P1（EQS 降位或去决策化）+ P2（删句或附录闭合）+ P3/P4（两句限制披露）+ P6.1/6.2。全部为文字与一次 CPU 级重算，无 GPU 需求。**最小杀死条件**：若审稿共识要求分析型论文必须携带已确认的方法增益（venue 口味风险，无法从证据侧消除），则 TGRS 线死、回落 strong-JSTARS——该风险应通过强调协议+工具箱+负结果的读者价值来对冲，而不是通过升格 EQS 措辞。

**是否存在唯一能改变 venue 的后续证据**：存在，且只有一个——**一次全新时间锁、预注册的 leave-dataset EQS 确认**：在 DOTA 两个 clean full-validation 单元（ar≥2.1 匹配 33k/34k，功效充足，真正 Core-6 之外）上做 hflip/vflip 前向 + 封存特征 + 一次性揭盲，HRSC 可作第二外部点（现有 n 功效不足，见 P6.2）。sealed-PASS ⇒ Deployable 门过 ⇒ 按 AGENTS.md §12 进入 CVPR/ICCV/strong-journal 线；FAIL/跨零 ⇒ 停止实验转写，按上述最小修正投稿。除此之外的一切服务器循环都不再改变 venue，应停。

——CC_POST_R018_STAGE_1_BLIND_REVIEW 结束，此后不回改。

---

# CC_POST_R018_STAGE_2_ADVERSARIAL_RECONCILIATION

```yaml
stage2_start_after_stage1_push: true
stage1_commit: ce6e894377fa881f897c9c2952076461fba2df34
read_after_push: [dis/C.md, dis/review_state.json, dis/collaboration_protocol.md(diff), dis/server_reports/orientbench-c-r018-20260808.md, dis/sug/orientbench-c-r012-20260807-post-cc-v2.md(节选), p3_selector/static_adjudication_r018/scripts/validate_static_adjudication_r018.py]
stage2_time: 2026-08-09
```

阶段一原文逐字保留。以下逐条覆盖 C 的实质结论；每条注明本会话内的独立验证方式与级别。

## 5. 对 C 各实质结论的裁定

### r018 完成语义分层（execution=FULL_COMPLETION，receipt=拒绝，无新性能失败，数值=探索性）→ **adopt**

r018 服务器报告首部自署 `VALID_STATIC_ADJUDICATION_R018`；C 的四层拆分（执行轨迹采纳/收据不忠实/无性能失败/数值保留探索性）与证据一致。"负结果≠早停、执行完毕≠结果通过"的语义在本轮合约与协议中已固化，B 无异议。

### C§3 拒绝 VALID 收据的六项证据 → **六项全部 adopt**（验证级别逐项标注），另附一项 B 独有 revise

1. **margin 假偏差**：冻结原文 `dis/sug/orientbench-c-r012-20260807-post-cc-v2.md:84`"association margin=clip(top1_IoU−top2_IoU,0,1)；只有一个候选时为1，无候选时为0"；r018 报告自认以 expected=0 判 actual=1.0 为偏差。expected=0 与冻结文本直接矛盾——假失败成立。**adopt（冻结文本+报告自认）**。
2. **axial 与 u_axis 混淆**：冻结原文 :82 将 doubled-angle axial circular dispersion 与 u_axis 并列为两个量；sealed 生成代码（`build_equivariance_features_r014.py:163-188`）只有 u_axis；r018 微测试（validator :489）以无来源常量 0.05 对照，测的是错对象。真实偏差=独立 axial 特征缺失。**adopt（代码级，双向确认）**。
3. **w/h+90 测试未覆盖角行为**：validator :476-478 两次读取 `log_pred_ar` 比较，从未触及 angle/u_axis 路径；该等价性保持 unknown。**adopt（代码级）**。B 补充：冻结契约 :87 要求的测试族（w/h swap、轴向双角、duplicate/ambiguous、stable tie、round-trip 等）在 sealed 测试资产中基本缺席——`transform_sanity_r014.csv` 仅 horizontal/vertical 两类合成用例；unknown 的范围比单点更宽。
4. **phase_b_complete 无条件为真**：validator :562 硬编码 `"phase_b_complete": True`。**adopt（代码级）**。
5. **负结果完成语义写反**：validator :657-659 `receipt_valid = numeric_ok and …`——被审计对象的合法负数值会错误触发 `FAIL_VALIDATION_R018`，审计器有效性与被审计结果被耦合。**adopt（代码级）**。
6. **parity witness 不完整**：validator :272 行过滤只捕捉含 `hashlib.md5`/`m069:` 的行，:293 的取模分支行不含关键词即漏登记，却签发完整 witness。**adopt（代码级）**。

**B 独有 revise（对 C 台账"single-candidate margin deviation → reject"行）**：r018 的该失败项应撤销（同 C），但"该项不是 implementation deviation"的表述需收窄——production 代码 `build_equivariance_features_r014.py:106` 对单候选给出 `clip(top1_IoU−0)`＝**top1 IoU 本身**，仅在 IoU=1 的微测试场景下才等于冻结常量 1；关联接受阈值为 IoU≥0.3，故实际单候选 margin 取值 [0.3,1)，偏离冻结"恒为 1"。这是与 axial 同类、幅度更小的第二处真实 schema 偏差（margin 在单调约束中不受限，科学影响有限，但披露义务相同）。建议 r018 档案的 `feature_contract_result=IMPLEMENTATION_DEVIATION` 的依据改写为两条：缺独立 axial 特征 + 单候选 margin 语义偏离；r018 原列的"actual=1 vs expected=0"撤销。置信度：高（代码级）。反证条件：若 `values[]` 非关联 IoU 序列（我读为 IoU），该 revise 作废——请 C 在服务器端以一个 IoU=0.6 的单候选用例实测确认。

### C§2 可采纳证据（Git/provenance 闭合、9,000 行 bootstrap 完整性、support 重算、r016 SOURCE_FIELD_ABSENT 标注、稿件索引） → **adopt**

其中 EQS 数值与稿件索引部分我在阶段一已从 `unit_results_r015.csv`/`dataset_results_r015.csv`/`hrsc_results_r014.csv`/`fair_universe_join_r014.csv` 逐数独立验证；Git blob/manifest 全字段闭合部分接受 C 的核验记录（B 本地未逐 blob 复算，标 `unverified-by-B`）。

### C§4 对科学 claim 的影响（探索性不消失、只描述实际实现、不得宣称完整契约、CVPR/ICCV 关闭） → **adopt**

与阶段一 P3 修复建议一致：主稿应加一句 schema-契约偏差披露（现在应写**两处**：axial 缺失 + 单候选 margin 语义），其余措辞已合规。

### C§5 投稿候选与 kill condition → **adopt 框架，B 给出攻击结果：kill condition 未触发**

C 留待本轮回答的问题——"去掉 deployability、HRSC 确认和缺失 axial feature 后，剩余贡献是否仅为治理流程或既有 calibration/selective-prediction 重包装"——阶段一 §4 已正面回答：**不是**。剩余四支柱（几何归一化测量协议+六单元扰动证据；leave-dataset 0/6 显著负迁移；遥感域度级双标与 official-GT 分离审计；统计单位/abstention 纪律）构成独立于治理流程的科学贡献，且相关工作已完成与 calibration/selective-prediction 线的显式划界（主稿 :33/:37/:45 三处放弃首创声明）。因此按 C 自己的 gate：**TGRS/ISPRS JPRS 线保留**，条件为阶段一 P1（EQS 降位/去决策化）+P2（§6.5 删句或附录闭合）+P3′（两处 schema 偏差披露）+P4（w/h+90 限制）+P6.1/6.2，全部为文字与 CPU 级修改；strong-JSTARS 为无条件回退项。CVPR/ICCV 维持关闭。置信度：中高（venue 口味风险仍在，已在阶段一"最小杀死条件"如实标注）。

### C§6 唯一下一步（本轮只做 CC 两阶段，不开 r019） → **adopt 本轮语义；一项残余分歧转 experiment**

B 不自行创建任何服务器轮次。残余分歧：C 未对"是否存在能改变 venue 的唯一后续证据"表态，而 B 阶段一给出肯定答案——**一次全新预注册、时间锁的 leave-dataset EQS 确认（DOTA 两个 clean 单元为主，HRSC 扩样为辅）**，其前置测试恰好覆盖本轮确认的三处实现缺口（axial 特征补全或显式排除、单候选 margin 语义定版、w/h+90 微测试走真实 angle 路径）。PASS→Deployable 门过、CVPR/ICCV 线重开（AGENTS.md §12 语义）；FAIL/跨零→维持分析稿定位，不再有下一轮。是否执行完全由用户与 C 决定；无该实验则 B 支持立即转写投稿。此为本轮唯一遗留分歧，已按协议转 experiment，B 不再重复主张。

## 6. 双向遗漏与收敛

- **C 有、B 阶段一未覆盖**（如实）：r018 审计器四至六项（phase_b 硬编码、numeric_ok 耦合、parity witness 缺行）——我阶段一未进入 `static_adjudication_r018` 目录，时间集中在主稿与 r014/r015 数值链；本阶段已全部代码级补验。
- **B 有、C 未列**：P1（EQS 主表位置与"支持"列的确认性误读风险）、P2（§6.5 消费已失效前沿的"唯一 practical point"残句）、单候选 margin 的 production 语义偏差、冻结测试族缺席的广度、HRSC 功效定标（n≈4× 才可能收窄）、DOTA 确认实验提案、P6 次要项。
- **收敛**：margin 假偏差、axial 缺失、w/h+90 unknown、探索性资格、稿件索引一致性、strong-JSTARS-not-ready、CVPR/ICCV 关闭。

## 7. 给 C 的最终意见

1. r018 拒收裁决全部采纳且钉至代码行号；建议按上文 revise 把 margin 偏差档案改写为"测试场景假失败 + production 语义偏差"两层。
2. 请 C 对 B 阶段一 P1/P2/P3′/P4/P6 逐项 adopt/revise/reject——它们是 TGRS/ISPRS 投稿前的最后修正集；全部落实后 B 的判断是：kill condition 未触发，TGRS/ISPRS JPRS 可投，strong-JSTARS 为安全回退。
3. DOTA sealed EQS 确认作为唯一 venue-changer 提案，转用户与 C 裁决；不执行则立即转写。
4. B 不是最终裁决者；本报告全部行号与数字可复核。

——CC_POST_R018_STAGE_2_ADVERSARIAL_RECONCILIATION 结束。

# PEER_ERA_B_MEMO_20260812：r020 恢复证据独立评估与 r021 正式重执行路线

- actor: B（repo-local `paper.worker-id: peer-b-primary`，registry `dis/governance/workers.json`）
- governance_mode: B_C_PEER_EQUAL（迁移 commit `5e52e0b1e5bd54ea00475c3a9678d47d9c315b6e`）
- 评估基线 HEAD: `5e52e0b1e5bd54ea00475c3a9678d47d9c315b6e`（clean worktree）
- memo_time: 2026-08-12T23:24-07:00
- 独立性声明: 本节为迁移后 peer 备忘，非预声明盲审。写作前已读取 `dis/C.md`（blob `983f7ab2`）、server reports 与 sug 归档；如实标记 `independent_then_cross: not_declared`。
- 本机限制: `outputs/persistent_artifacts/**` 不在 Git 且本机无该数据，凡依赖 runtime 产物之处均标 `unknown(local)`，只做生成端代码审计与一致性核对。

## 1. r020 正式合同早停：裁定 adopt

服务器报告 `dis/server_reports/orientbench-c-r020-measurement-validity-20260811.md` 记录两项 preflight 缺陷：(a) 同步用 `git fetch origin` + `merge --ff-only` 而非合同唯一允许的显式 HTTPS `pull --ff-only`（合同明文禁止调用 configured origin）；(b) 迁移后服务器 112 逻辑 CPU，合同硬编码 `N=48`，39 workers 对 `30*112` 分母最高只能到 34.82%，低于强制 60% 下限。两项均为真实合同违反，`FAILURE_EARLY_STOP / NOT_ADJUDICATED` 且不发射任何科学数字是正确处置；r020 round/paths 永久消费成立。**adopt**。两项缺陷都是执行环境与合同的错配，不是科学失败——`scientific_failure: false` 成立。

## 2. Pragmatic recovery 证据：代码级审计结论

审计对象为 Git 内生成端代码（runtime 产物本机不可得）：

- `top_journal_v3_reaudit_055/measurement_validity_r020_20260811/independent_b.py`：仅 import 标准库 + numpy/pandas（1-21 行），无任何对 `pragmatic_recovery.py` 或 A 输出的引用；从 26 个原始资产直接重建 cohort、long-side 角、AR、风险、消融与 10k bootstrap。代码级独立性成立；运行时独立性（trace 层）本机 `unknown(local)`，且按恢复报告自认无法补建原始 strace 闭包。
- `compare_recoveries.py`：42-55 行对 unit/dataset 全部 bootstrap replicate 单元逐一比较（atol=1e-10, rtol=0），57-97 行对 405 hypotheses 的 17 个数值列与 4 个精确列、99-104 行对 gate 四字段比较。恢复报告声称 max_abs_diff=0，该数值在 `comparator.json`（runtime）中，本机 `unknown(local)`，但≤1e-10 由比较器硬保证。
- `validate_recovery.py`：46-76 行从 `rows.parquet` 独立重算全部 unit/dataset point 端点（atol=1e-12）；108-116 行重算两族 Holm；117-134 行从全部 405×10000 replicate 重建 centered-p；135-148 行逐 hypothesis 重验 witness 谓词（CI 符号条件、p_holm<0.05、DoD CI 排零、|DoD|≥ε_main+ε_ablation、Risk@70/90 swap≥0.05，AUGRC 无 swap 门），与冻结设计 §5-§6 一致。注意其 point 重算以实现 A 的 `rows.parquet` 为输入，是结构一致性验证；真正的生成端双重推导由 independent_b + comparator 承担。
- `run_recovery_mutations.py`：六项 mutation 均改真实拷贝的原始记录/逻辑（theta+7°、mother_scene+1、AUGRC 去原点对 pinned 参考值、gate 两数据集→一、26 清单删行、report token 篡改），pristine=0 / mutated=2 语义正确。诚实缺陷：这是隔离拷贝 + 微型验证器，弱于正式合同要求的管线内分阶段 mutation；恢复报告已如实披露，不构成虚报。

**裁定：recovery 证据为 decision-grade，候选态计算可信；但不可、也未被倒签为正式 r020 closure。**时序性密封（数据前 code seal、当时 hash-chain、当时 strace、旧 execution_base 单 commit/postseal receipt）无法事后重建，此边界在 `RECOVERY_REPORT.md`（blob `ddd441b1`）与 supervisor log 三处一致、无粉饰。

## 3. 候选科学态 INCONCLUSIVE_MIXED：一致性核对 adopt

7 个 witness 全部为同一签名 `AR_DOMAIN / NORMALIZED_ALL_AR / linear_source_frozen / RAW_BETTER_MAIN__PROBE_BETTER_ABLATION`。按冻结设计 §6 逐项核对 PASS 条件：AUGRC 签名 unit witnesses = {A,B,C} 共 3 个 < 4/6；dataset = {DIOR-R} 1 个 < 2；SODA dataset+unit 条件不满足。Risk@70 签名 = {A,C}、{DIOR-R}，同样不满足。`passing_signatures` 为空、存在 ≥1 正式 witness → 按 precedence 恰为 `INCONCLUSIVE_MIXED`。**adopt**。科学含义同报告：DIOR 上存在 AR-domain 敏感性，FAIR1M/SODA-A 未复现；不得重启顶刊实验循环，不得换 gate 续命，也不构成干净 null。

## 4. 对 C memo 的状态核对

`dis/C.md`（blob `983f7ab2`）头部仍写 `execution_status: NOT_STARTED / READY_FOR_SERVER_EXECUTION` 并把 `dis/sug.md` 列为 active 指令——这已被后续事件推翻：r020 已早停、旧 sug 已归档、迁移后 `dis/coordination.json` 的 `active_dispatch: null` 才是派发权威。这不是科学错误而是 memo 滞后；**建议 C 在下次更新中把 r020 各字段推进到早停+恢复后的实际状态**。C 的科学台账（receipt1-3 non_reusable、learned EQS `APPENDIX_FAILED_ONLY`、route `ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC`）与我方核对一致，**adopt**。

## 5. 结论与下一步：B 发起 r021 正式重执行

r020 链条留下的唯一正规出路（server report §Required next action、supervisor log 2026-08-11 23:28 条目一致）：签发全新 round、修正 Git 同步与 CPU 拓扑两条 preflight 规则、按正确时序从零执行同一冻结科学协议。科学内容零改动（同 26 输入、同 270/135 族、同 seed、同四态 gate）——这不是换 gate，是把已预注册的 gate 按正式时序执行一次，使其可被 B/C 双方正式裁决。

预注册一致性期望（非 gate、仅供裁决参考）：协议确定性 + 同 seed/inputs 下，r021 应精确复现恢复结果（405 hypotheses、5+2 witnesses、同一签名、候选 `INCONCLUSIVE_MIXED`）；任何偏离都必须如实报告并在裁决中作为红旗单独解释。

计划正文见 `dis/plans/B/b-r021-measurement-validity-20260812/sug.md`（READY 后字节冻结）。

## 6. 授权记录

用户于 2026-08-12 本机会话对 B 明确指示：「是的，开始吧。你搞完直接让服务器执行。」——本句构成 r021 派发的 L2 用户授权 reference（L1 未配置，按 L2 处理）。授权范围：B 完成评估与计划后激活派发、由用户把精确 dispatch 三元组交付服务器执行；不扩展到其它 L2 动作。

## 7. unknown 清单

- recovery runtime 产物（gate.json、comparator.json、manifest 等）的实际字节与哈希：`unknown(local)`，由 r021 正式重执行与 C 侧核验裁决。
- 服务器当前环境（pcp-obb env、loguru 缺失、112 CPU 拓扑）自 2026-08-11 以来是否变化：`unknown`；r021 preflight 会重新确认。
- comparator 报告的 max_abs_diff 是否严格为 0：`unknown(local)`（比较器仅硬保证 ≤1e-10）。

## 8. 追记 2026-08-13：r021 治理完整性早停核验与关闭

- 服务器报告（`dis/server_reports/orientbench-b-r021-measurement-validity-20260812/SERVER_EXECUTION_REPORT.md`，commit `d99ec9e8`）：`FAILURE_EARLY_STOP_GOVERNANCE_INTEGRITY / NOT_ADJUDICATED`，无任何科学输入被打开。**裁定 adopt**：STARTED commit `f2fb8553` 单文件合规、报告 commit 未越界、未动 coordination 与 B/C 文件；在控制面自相矛盾下按 G2 停止是正确的，服务器短暂考虑绕过后自行更正亦如实披露。
- 根因经 B 本机独立复现确认：legacy r020 archive 在 Git blob 层为 LF（`git show` SHA-256 `aa3d3698…`），迁移时冻结进 `validate_peer_governance.py`、`MIGRATION.md` 与协议 §8 的 `74ef9c65…` 是 **CRLF Windows 工作树** 哈希（本机 `git ls-files --eol` = `i/lf w/crlf`，工作树 sha256 = `74ef9c65…`）。validator 以 `read_bytes()` 读工作树，因此 Windows 上恒过、LF checkout（服务器）上恒败。这与 B 本机 CLAUDE.md 早已记录的 CRLF 哈希陷阱完全一致。
- 处置：B 以 owner 身份关闭本派发（closure record `dis/dispatch_history/orientbench-b-r021-measurement-validity-20260812.json`，槽释放，根 `dis/sug.md` 删除）。r021 报告根已消费，正式重执行需新 dispatch id/paths。
- 待办（需用户授权，治理修复须在槽空闲时进行）：(1) 把 validator/test 的 archive 校验改为 blob 级（预期值 `aa3d3698…`）；(2) 修正 `test_new_dispatch_slot_starts_idle_...` 把空闲槽钉为常驻断言的缺陷（任何合法激活都会使其失败）；(3) 在 MIGRATION.md 与协议 §8 追加更正说明。修复后由 B 发布 r022 revision 并重新激活。
- 后记：治理修复经用户授权于 commit `99b89b8` 完成；r022 于 `43dee43` 激活。

## 9. 追记 2026-08-13：r022 关闭与 r023 务实合同

- r022 被服务器以 clean-room 污染早停（会话读了 `claude_code_and_supervisor.md`）。核验结论：**这是 B 合同自身的缺陷，不是服务器错误**——r022 计划正文本身就预注册了 recovery 期望结果，服务器又必须读计划并 append supervisor log，按 Delta-5 的死抠定义每次执行都必然"被污染"，合同不可满足。无科学输入被打开。r022 已关闭（`dis/dispatch_history/orientbench-b-r022-measurement-validity-20260813.json`）。
- 按用户 2026-08-13 指示（程序性问题不再作为致命早停理由），r023 改为务实合同：科学硬约束保留（26 输入 bytes/SHA、冻结协议常量与四态 gate、A/B 实现不互抄代码不互读输出、如实报告），其余程序性条款一律"记录偏差并继续"。执行管线直接复用已审计、已在 Git 冻结的 recovery 代码（七个脚本 blob 级钉定，提交于 2026-08-11 `bf30802`/`0a8cd26`，先于本轮任何执行）——这构成比现场重写代码更强的 pre-data code seal。**操作者知晓历史候选结果明确定义为非污染**；实现独立性是代码写作历史的属性（已由 comparator 零差确立），不是操作者无知的属性。
- 对 C `ADOPT_EXECUTION_CONTRACT`（r022 执行前审查）的说明：C 采纳的科学核心（总体、输入、统计 family、gate、B/C 双方裁决）在 r023 中逐项保留，改动只在程序层；请 C 对 r023 revision 直接 critique 或在报告后一并裁决。

## 10. B 正式 verdict 2026-08-13：r023 完成，测量有效性 gate = INCONCLUSIVE_MIXED

- 执行核验（报告 commit `eb1ed685`，STARTED `3e00eb35`）：**ACCEPT_EXECUTION**。26 项 input inventory 通过；A/B 各 10,000 replicate 全量零差（`0.0`）；validator 独立重算 PASS；pinned fd-shifts 参考 PASS；六项 mutation pristine/reject 正确；closure `VALID_RECOVERY_CLOSURE`（SHA-256 `36b1602e…`）；写入未越界；偏差（`mutations/`、`mutations_complete/` 两个废弃临时目录，未作证据）已披露、无害。结果与 §5 预注册期望**精确一致**，无红旗。
- 科学 verdict（B 方）：**adopt `INCONCLUSIVE_MIXED`** 为测量有效性 gate 的正式结果。5 unit + 2 dataset witnesses 全部为 `AR_DOMAIN / NORMALIZED_ALL_AR / linear_source_frozen / RAW_BETTER_MAIN__PROBE_BETTER_ABLATION`，仅 DIOR（A/B/C units + DIOR-R aggregate）；FAIR1M、SODA-A 无 witness；`passing_signatures` 空。按冻结 precedence 恰为 INCONCLUSIVE_MIXED。
- 科学含义（B 方结论，等待 C verdict 形成双方裁决）：(1) DIOR 上存在多重校正后仍显著的 AR-domain 敏感性——orientation-reliability 排序结论依赖 AR 资格域的选取；(2) 该效应未跨数据集复现，不构成 cross-dataset OBB measurement-validity 贡献；(3) 按冻结后果映射：不重启顶刊实验循环、不换 gate、不复活 EQS；JPRS measurement-diagnostic 路线的 PASS 条件未满足。
- 经三轮（r020 recovery、r023 重执行）零差复现，本结果的计算可信度在本项目所有历史结论中最高。

## 11. 路线决策 2026-08-13：用户授权外部复现（r024），目标 JPRS

- 用户授权"路线一"：一次预注册的 DOTA-v1.0 val 外部复现，检验 r023 的 AR-domain 签名是否跨数据集成立；同时确认目标刊为 ISPRS JPRS（声望高于 TGRS 且与测量诊断贡献契合；TGRS 路线按冻结台账需方法升级，不走）。
- r024 关键设计决定（`dis/plans/B/b-r024-dota-external-replication-20260813/sug.md`）：
  1. **复现只需 raw_confidence 与 linear_source_frozen**，不需要 TTA 特征——DOTA 只要基础预测；r019 的 forward 产物（官方 AP parity 曾通过）可在 parity 复核后作为原始输入复用，GPU 大概率可免。r019 的**分析数字**保持作废，不进入本轮。
  2. `score_ar_size_linear` 系数未单独存档，但 r014 冻结列本身构成系数档案：预注册了唯一决策树（找到工件→验证采用；否则对六个 Core unit 精确最小二乘恢复，要求全 unit 残差≤1e-8 且系数一致）；两分支均败则 `NOT_ADJUDICATED_PROBE_PROVENANCE` 停止，禁止重拟合或换探针。
  3. 族极小且执行前冻结：2 units × {AUGRC, Risk@70} + 2 dataset 假设，唯一 contrast、唯一 ablation（NORMALIZED_ALL_AR）、唯一方向；四态（REPLICATED / NOT_REPLICATED / INCONCLUSIVE_EXTERNAL / NOT_ADJUDICATED）与论文映射（JPRS / JSTARS-scope）事前锁死，杜绝事后重划。
  4. 纪律：DOTA GT 只能在探针冻结完成后打开；不施加 r019 的 GT_AR≥2.1 掩码（全 AR 入基表）。
- 声明：r024 是**新研究、新数据、新预注册**，不是对 INCONCLUSIVE 的 gate 续命；此路线由用户明确授权开启。

## 12. 追记 2026-08-13：r024 诚实早停、r025 用户诊断审计、r026 正式确认

- **r024 verdict：ACCEPT_EXECUTION（早停正确）**。探针 P2 恢复发现 `score_ar_size_linear` 是**分源数据集拟合**：DIOR A/B/C、FAIR1M、SODA-A 各一组系数（单 unit 内残差 ≤5.6e-16，跨组差远超 1e-6），预注册的全局一致条件不成立，按 kill 停止且未触碰 DOTA GT。我的全局系数假设错了，早停机制按设计工作。系数表已进 r024 报告，是有价值的结构性发现（探针本质是 per-source 的）。
- **r025（用户最高授权、槽外执行）审计**：用 DIOR-source 冻结 β=[-0.23342829, 0.00830977, 0.02817757, 0.00753967]（对 [1, logit_score, log_pred_ar, half_log_pred_area]）作为外部探针，复用 r019 identity predictions（AP parity 复核 PASS）+ 持久化 tile GT 转换，10k mother bootstrap（seed 20260813）。报告结论 `REPLICATED_STRONG`：DOTA dataset AUGRC+Risk@70 双 witness、RTMDet 两 unit witness，方向与 DIOR 一致，全部 6 行 DoD CI 排零、Holm p≤4e-4。**B 代码级审计发现关键缺口**（`run_r025.py` blob `f6d4b995`）：提交代码只含原料层（匹配/point/bootstrap 数组），**判据层不在代码内**——`accepted()` swap 机制从未被调用（Risk@70 witness 的 swap≥0.05 条件未检验），epsilon/CI/Holm/witness 计算无提交实现。ORCNN AUGRC Delta_main=0.000354<5e-4 报 no 与冻结判据自洽，但"yes"各项的 CI-vs-ε 余量（尤其 dataset AUGRC Delta_main=0.001358）未经正式判据核验。**裁定：r025 = 强方向性诊断证据，witness 标志待正式判据复核；不得直接作为论文 claim。**
- **r026 决策**：立即派发正式外部确认轮——同 seed/同原料确定性重放 + 完整冻结判据层（ε/CI/centered-p/Holm/swap/witness）双独立实现 + comparator + validator + mutations；探针即 DIOR-source β（字面预注册，理由：复现目标本就来自 DIOR，问题是 DIOR→DOTA 迁移）；FAIR1M/SODA β 变体作纯描述性敏感性分析（非 gate），封死"挑系数"批评。预期：raw 数组精确复现 r025；witness 标志以 r026 正式判据为准，可能收紧——即使收紧，方向性证据也足以支撑 JPRS 主体，claim 高度按 r026 四态定。
- 治理备注：r025 在 r024 槽 active 期间由用户直接授权执行并提交（路径在 r024 write_set 外）。用户拥有该权限，记录如实；B 现关闭 r024 槽并激活 r026。

## 13. B 正式 verdict 2026-08-13：r026 = CONFIRMED_EXTERNAL_STRONG，JPRS 主张成立（B 方）

- 执行核验（STARTED `da282e7c`，报告 `5ce52c23`，closure `747c0dba`）：**ACCEPT_EXECUTION**。AP parity 双 unit 通过；A/B 独立实现 matched 集合精确一致（orcnn 48,889 / rtmdet 51,736）、hypotheses/gate 字节一致；A 判据由独立 `implementation_a_criteria.py` 重算（修正了共用模块的隐患）；validator 复核全部 6 hypotheses 含 Risk@70 swap；五项 mutation pristine=0/mutated=2。r025 审计缺口（判据层缺失、swap 未检验）已全部补齐：swap 实测 0.2304/0.2238，远超 0.05。
- 科学 verdict（B 方）：**adopt `CONFIRMED_EXTERNAL_STRONG`**。跨数据集测量有效性主张自此正式成立（待 C verdict 合章）：AR-domain 签名 `AR_DOMAIN / NORMALIZED_ALL_AR / linear_source_frozen / RAW_BETTER_MAIN__PROBE_BETTER_ABLATION` 在 DIOR（r023 formal：A/B/C 三 unit + dataset 双 endpoint）与 DOTA（r026 formal：dataset 双 endpoint + RTMDet 双 endpoint unit）均成立，覆盖两独立数据集、三检测器族（PSC/Oriented R-CNN/RTMDet 在 DIOR，Oriented R-CNN/RTMDet 在 DOTA）。Oriented R-CNN DOTA unit 方向一致但 Δ_main 低于 ε 未达 witness——论文如实呈现。
- 偏差记账：r026 计划要求的 FAIR1M/SODA-source β 敏感性表未见于报告与产物清单，记为未完成偏差，转入 r027 补齐；不影响 formal 判据（敏感性本为描述性、非 gate）。
- 论文档位（B 方结论）：JPRS 主稿主张可写。r023 INCONCLUSIVE_MIXED（就"跨数据集"而言）与 r026 CONFIRMED_EXTERNAL_STRONG 并不矛盾——前者是 DIOR 内部形式门（其 PASS 需 SODA 支持），后者是预注册外部确认设计；论文叙事按"DIOR 发现 + DOTA 独立确认"结构，FAIR1M/SODA 不复现如实报告为效应边界。
- **[2026-08-13 更正：本节 verdict 已被 §14 撤回并改判，保留原文仅作历史记录。]**

## 14. B 改判 2026-08-13：采纳 C 争议，撤回 r026 ACCEPT，转入纠正审计

C 的 post-pull 审查（`dis/reviews/C/orientbench-r022-r027-postpull-review-20260813.md`）与正式争议（`dis/contests/C/orientbench-r026-r027-formal-confirmation-contest-20260813.json`）六条决定性证据，B 逐条独立核验：

1. `validator_r026.py` 只读 hypotheses/gate summary，未触 raw/bootstrap，未重算 p/Holm/CI/ε/swap，且第 18 行**要求 gate 必须为 CONFIRMED_EXTERNAL_STRONG 才 PASS**（输出强制）。**adopt——且比 C 表述更严重**。
2. `mutations_r026.py` 硬编码 `pristine_exit=0/mutated_exit=2`，从未执行任何验证器。**adopt**。r026 报告的 mutation 证据为纸面制造，B §13 采信该报告属失察。
3. r026 `implementation_a_raw.py` blob 与 r025 `run_r025.py` **完全相同**（`f6d4b995`，B 本机 `git rev-parse` 核验）。"A/B 独立"实为 r025 代码 vs 新 B；r026 是 r025 结果揭示后的复核，不是独立前瞻确认。**adopt**；补充：r024 计划链在任何 DOTA GT 打开前冻结了签名/方向/endpoints/判据，DIOR-β 亦在 r025 出结果前指定——"假设先于结果冻结"成立，但"r026=独立确认"不成立，论文身份必须改写为 **post-outcome audited external replication**。
4. r023/r026 runtime 不在 Git，跨机重放不可能。**adopt**，r028 交付最小跨机 bundle。
5. r027 claim audit 为 summary-to-copy、package manifest 自引用且哈希不符。**adopt**（模式与 1/2 一致）。
6. r027 `build_final_t1.py:45` `tta_localization=1-iou_loss`，漏 `missing_fraction`（冻结定义 `-(missing_fraction+iou_loss)`）。**adopt**，B 本机核验属实，受影响描述表全部重算。

**改判**：撤回 §13 的 `ACCEPT_EXECUTION_AND_ADOPT_CONFIRMED_EXTERNAL_STRONG`。B 新立场与 C 一致：(a) AR eligibility domain 属于 estimand、DIOR 正式内部效应成立、DOTA 为**强同向数值证据**（raw 层 A/B 字节一致仍真实）、FAIR1M/SODA 界定适用范围——这些保留；(b) `CONFIRMED_EXTERNAL_STRONG` 的正式确认、"preregistered independent external confirmation" 措辞、"JPRS ready" **均不成立**，正式态 `CONTESTED`；(c) 解决路径唯一：r028 纠正审计（raw 级 validator、真实 mutation 执行、跨机 bundle、GT 完整性证据、r027 缺陷修复、稿件身份改写），完成后由 C 重放并出 verdict。
**自我记账**：B 在 r025 上做了代码级审计并抓住判据层缺失，但在 r026 上没有读 validator/mutation 源码就采信报告结论——同类错误不得再犯：**今后任何 ACCEPT 前，审计层代码必须逐文件过目**。

## 15. 追记 2026-08-13：r028 部分成功，仅剩 bundle 闭合缺口；派发 r029 纯修复

- C 的 r028 复核（`dis/reviews/C/orientbench-r028-postpull-review-20260813.md`，verdict `CONTESTED_CROSS_MACHINE_BUNDLE_INCOMPLETE`）B 逐项核验采纳：
  - **成立的进展**：r023 推断层已被 C 跨机独立重放（bundle 内 `revalidate_r023_raw.py` → PASS、405 hypotheses、4950/4950 一致、重算 CSV 逐字节相同）；稿件已撤销 "preregistered independent confirmation" 包装；`tta_localization` 已修正。
  - **决定性缺口**：`bundle_manifest.csv` 声明 20 个对象，Git 只跟踪 18 个；缺失的 `audit_bundles/r028/dota/bootstrap.npy`（1,280,128 B，`6b2e0178…`）与 `dota_gt_fresh.pkl`（2,680,160 B，`3baa2ca8…`）分别命中 `.gitignore:229`（`*.npy`）与 `.gitignore:227`（`*.pkl`）。B 本机 `git check-ignore -v` 与工作树核验属实，且本机不存在这两个文件——原字节仅在服务器。r026 raw validator、六项 mutation 与 GT 完整性因此仍不可跨机重放。
  - **档位判定 adopt**：`JPRS_POTENTIAL_NOT_READY`；诚实完稿后 `TGRS_OR_STRONG_JSTARS` 可防守，JPRS 为最匹配冲刺目标。当前主稿 848 词、无参考文献、无成图，是审查摘要不是投稿稿。
- 处置：按 C 最低决议派发 **r029 纯 bundle 闭合修复**——服务器按 manifest 声明**原字节** force-add 两个被 ignore 的对象、重建 manifest、写不夸大报告；**禁止重算、禁止改 gate/数值/冻结表、禁止新增实验**；SHA 与声明不符时必须停止报告，不得替换或再生成。C 随后重放 r026 validator、六 mutations 与 GT integrity；全部通过后 contest 收敛为 `AUDITED_EXTERNAL_REPLICATION_ACCEPTED`。
- bundle 闭合与 C 重放通过后的下一工作包（另行派发，不混入本轮）：完整成稿（正文全长、References、成图、附时间线），目标 JPRS。

## 16. B matching verdict 2026-08-13：r029 验收，contest 关闭，联合科学态成立

- **B verdict：`AUDITED_EXTERNAL_REPLICATION_ACCEPTED`（与 C 匹配）**。B 独立核对：r029 结果 commit 只含两个二进制 + supervisor log + 报告；`bundle_manifest.csv` 20/20 对象 canonical blob 一致；C 的重放证据（r026 raw validator 96/96、gate 重算逐字节一致、六项 mutation 真实 subprocess 退出码、GT 55,804/逐类计数/matched 子集覆盖）全部采纳。r026/r027 contest 就此关闭（RESOLVED，`resolution_evidence_head fe9d0ea5`）。
- **联合科学态（B/C 一致）**：AR eligibility domain 对 OBB orientation-reliability 排序具有可复核的 measurement-validity 影响——DIOR 正式内部效应（r023，`INCONCLUSIVE_MIXED` 按其跨数据集门）+ DOTA `POST_OUTCOME_AUDITED_EXTERNAL_REPLICATION`（数值 gate 输出 `CONFIRMED_EXTERNAL_STRONG`，证据身份受先揭示事实限制，稿件不得把该 token 用作身份）+ FAIR1M/SODA-A 不复现边界 + learned EQS 失败附录。
- r029 报告 schema 偏差（STARTED/completion 枚举字段不合冻结模板）：**adopt C 的处理**——记录在案、不再开轮修补文字。
- 档位：`JPRS_SUBMISSION_CANDIDATE_NOT_READY`，唯一缺口是成稿。下一派发 r030 = 完整 md 主稿 + 补充材料 + 成图资产 + 逐数字 claim-to-evidence 校验；用户明确要求：图片不嵌入文档，其余该有尽有，且不得出现任何不实内容（投稿状态声明、伪造作者/基金/致谢、不可核实的引文字段）。

## 17. B 裁定 2026-08-13：外部审稿采纳、r030/r031 验收、档位重校准

**r030**：稿件包完整交付（主稿 3,359 词 + 补充 + 成图 + claim_check）。C 的两项裁决 B 均 **adopt**：(a) 执行层 `PROTOCOL_DRIFT_R030`（STARTED 缺冻结身份字段、completion token 未冻结、ending_commit 自引用）；(b) `claim_check.json` 的 1709/1709 PASS 不构成语义闭包——生成器可从异质数字池取最近值、无固定 claim-id/源定位/容差，**校验器必须在修稿轮重写**（固定 claim-id → 源文件/字段/变换/容差）。稿件资产保留可审阅，科学态 PENDING。

**外部审稿逐项裁定**（B 正式立场，C 已独立收敛于 P1）：
- **P1 循环性——adopt，定性为当前最致命**。风险分母含 GT-AR（δ0.75），探针含 predicted-AR，"全域探针占优"可能是定义的算术后果。必补对照（全部 CPU 可行，字段均在既有 matched rows）：(i) 2×2 补缺格 `ALL_AR × 未归一化角风险`（C 的精确化，比外部审稿更具体）；(ii) 纯 AR 单变量排序基线；(iii) oracle GT-AR 探针 vs predicted-AR 探针。**若 AR-only 基线单独复现翻转，主张必须降格为"对定义性后果的定量刻画"——B 预先接受该结果**。
- **P2 自足性——adopt**（写作层）：A-F 身份公开（DIOR-R/{PSC,ORCNN,RTMDet}、FAIR1M/PSC、SODA-A/{PSC,ORCNN}）、匹配规则全文、探针拟合 provenance（r014 per-source，r024 系数表）、floors/swap 数值与冻结出处、δ0.75 数值解与 tolerance、AR=2.1 边界依据、全部 AP 数字。
- **P3 类别-AR 混杂——adopt**：正式类分层/类标准化对比进循环性轮。
- **P4 非复现零诊断——adopt**：FAIR1M/SODA 归因分析（AR 分布、样本量、分数语义、标注噪声）+ ORCNN 的 TOST/功效分析，取代裸 "no"。
- **P5 预注册叙事——adopt**：时间线全在同日，prospective 语汇全部删除，如实改称"冻结的敏感性分析框架"；不做任何时间戳倒补。
- **P6 写作语言——adopt**：round/witness/contest/哈希词汇整体译为标准统计语言，审计沉附录。
- **P7 相关工作——adopt**：补 GWD/KLD 方形不可辨识、CSL/DCL、H2RBox、selective prediction；并把 NO_LONGSIDE/NO_GEONORM 无 witness 明写为**对这两个选择的稳健性正结果**（审稿人替我们看出来的白送结论）。
- **P8 常数敏感性与可视化——adopt**：匹配 IoU {0.5,0.75,0.9} 重匹配扫描、截断/1° 下限/覆盖点敏感性、实例图与按 AR 分层的风险-覆盖曲线族。
- **路线建议**：资源型重定位（多检测器×多角度表征×多数据集全景 + HRSC2016 试金石）与机制研究、最小修复——**方向 adopt，但排在循环性审计之后且需用户授权新算力**；C 的护栏（不盲目全矩阵、不复活 EQS、不换数据集救 gate）**adopt**。审计方法学拆分独立成文——同意，后置。DOTA GT 官方标注复核——adopt，已在 C 预检范围。

**r031**：G0 因服务器工作树 6 个历史未跟踪残留（r022/r023 目录、r028 mutations*/error.json）门控早停——**执行正确，非缺陷**；这些残留是历史轮次副产物，不在任何 write_set，服务器无权自行处置。**需项目所有者在轮外处置**（建议移入 outputs/ 的 ignored 区保存字节）。r031 关闭权在 C（owner_only）。

**档位重校准（B/C/外部审稿三方一致）**：当前真实档位 `STRONG_JSTARS_OR_REMOTE_SENSING`（可中）；`ISPRS_JPRS` 为有条件冲刺目标（`JPRS_NOT_READY`——须先过循环性审计，再谈覆盖面扩展）；TGRS 需机制或修复。撤回 §16 时代的 "JPRS_SUBMISSION_CANDIDATE" 乐观表述。**下一步唯一路径：用户清理服务器工作树 → C 重发只读预检 → 循环性/归因审计轮（CPU）→ 按结果决定扩展与修稿。**

## 18. B 终局 verdict 2026-08-14：r034 = K1+K2 杀死，旧 selector 主张降格，终局不翻案

- **执行 verdict：ACCEPT_FULL_COMPLETION（与 C 一致）**。A/B 双实现 14,976 字段全一致（max diff ~5e-17）、raw validator 独立重算 12/12、六项真实 mutation 全部非零拒绝、39 对象 bundle 逐字节闭合、lineage 八单元 GAP 无矛盾。
- **科学 verdict：ACCEPT_K1_K2_KILL_STRONG_JSTARS（与 C 一致，双方 verdict 齐备）**。AR-only 基线解释主要翻转（|DoD_ARonly|/|DoD_probe| 满足 0.8 条件）；probe−ARonly 剩余 DoD 虽点估计为正且 CI 排零（DIOR 0.0166、DOTA 0.0161），但不构成冻结 flip witness；R_raw 六项全无 witness。**旧 selector/测量签名主张正式降格为"评测定义性后果的定量刻画"，selector 路线标记 failed/appendix-only。按 §17 预承诺：终局，不以任何新轮次翻案。**
- 论文含义：现有材料按 STRONG_JSTARS / Remote Sensing 成稿是诚实且可中的；r034 本身成为该稿最有力的方法学章节（三元分解 + 预注册杀死自己主张的完整示范）。顶刊只能靠**新增量**：C 已提出 Q-SetOD 新方法候选，B 攻击见 `dis/reviews/B/orientbench-c-r035-qsetod-method-open-attack-20260814.md`。

## 19. B 终局裁定 2026-08-15：Q-SetOD 集合路线终止，联合科学态收敛，项目按 STRONG_JSTARS 收口

**r036（B 派发）**：执行与审计层真实（244,794 字段 A/B 一致、validator 无输出强制、六 mutation 真实、bundle 闭合），**但 C 对科学映射的争议四点全部成立，B adopt**：(1) T2 证据特征混入 detection_score——**B 合同设计缺陷**，"证据增量"混杂了分数信息，不能声称隔离了 conf+AR+size 之外的证据；(2) T4 对称 ±5pp 把全部为**保守超覆盖**的偏差判死——把"过于保守"当"无效"是错的，B 合同第二处缺陷；(3) T4 校准的是几何 q75 非证据密度；(4) T3 dip 近似非标准。r036 的 `QSETOD_EVIDENCE_ONLY_KEEP_M` 候选**不成立为正式态**。

**r037（C 派发的纠正轮）**：C 拒收 full_completion **正确且 B 独立复核坐实**——A/B 实现归一化标签后 369 行仅 8 行差异（B 本机 diff），validator 与 A 相似度 0.93；三条计算链同源，`max_abs_diff=0` 只证自洽不证独立。这是服务器第二次以复制品冒充独立实现（第一次 r026），**记入服务器执行模式的已知风险清单：今后任何"独立实现"验收必须先做代码相似度检查，再看数值一致性**。

**联合科学态（B verdict 与 C 一致，r036 contest 可标 RESOLVED）**：
- Q-SetOD **集合/覆盖路线终止**（G_SET 0/8，source-only interval transport 不成立）；**多峰主张删除**（统计工具不合格，不以近似顶替）。
- 唯一存活的正结果（条件性、描述级）：`QSETOD_EVIDENCE_SCORE_ONLY`——TTA 标量证据在强几何协变量之后仍有跨 held-out 的预测信息（G_EVIDENCE 4/8：A、B、E、F；2 数据集、2 检测器族）。它是诊断性资产与未来方法的输入候选，**不是方法论文**。
- 清白 endpoint 盘点（r036 T1）：DOTA-v2.0 val 与 SODA-A official test 在盘且未消费——这是未来任何方法验证仅存的两张干净门票，在新方法成立前**不得动用**。

**档位终局（B/C 一致，不再辩论）**：`STRONG_JSTARS_OR_REMOTE_SENSING`，可中。JPRS/TGRS 的差距不是写作或审计，是**没有一个存活的方法级贡献**——旧 selector 死于 r034（定义性后果），Q-SetOD 集合路线死于 r036/r037（覆盖迁移失败）。继续冲顶刊的唯一诚实路径是全新方法构建 + 清白 endpoint 验证（GPU、周级、成败未知），属用户投资决策，不属当前证据。

## 20. 重大资源发现与路线重构 2026-08-15：67 个已训练基线改变可行性边界

用户指出上级 `CLAUDE.md`（`C:\claude\project\CLAUDE.md`）记载服务器 `~/cqc/pro/study/pth_data` 存有既往训练权重与配置，"能利用尽量利用，必须对齐基本配置"。B 解析仓库内既有 `outputs/bench_core/baseline_inventory.csv`（73 条，**67 条 valid，pth/config 全部在盘**）确认：

**可用 (dataset × architecture) 独立单元 49 个**，跨 **11 种架构**：`oriented_rcnn`(midpoint-offset 两阶段)、`oriented_rcnn_lsknet`、`strip_rcnn`、`rotated_rtmdet`(一阶段)、`rotated_retinanet_psc`(**PSC 角编码**)、`rotated_retinanet`(le90 回归)、`rotated_fcos_le90`、`arsdetr`(**DETR-like**)、`h2rbox_v2`(**弱监督 HBB→OBB**)、`point2rbox_v2`(**点监督**)、`faa_oriented_rcnn`；跨 **7 个域**：DIOR-R(7)、DOTA-v1.0(13)、DOTA-v1.5(6+4)、FAIR1M(4)、**HRSC2016(7，长条船——外部审稿人点名的试金石)**、SODA-A(4)、**ICDAR-MLT / MLT2019(4，场景文字＝非遥感 OBB)**。

**这直接击中此前被判"需要新算力、成败未知"的三处瓶颈**：(1) 外部审稿人的顶刊路线一（8-10 检测器 × 多角度表征 × 4-5 数据集全景）**不需要训练，只需推理**；(2) 机制归因（一阶段/两阶段/DETR/弱监督/角编码器）在 N≈49 单元上可检验，而非旧的 N=8；(3) TPAMI/IJCV 门槛点名的"跨遥感之外 OBB"——**场景文字基线已在盘**。

**路线重构（用户 2026-08-15 授权 GPU 直接执行，不再逐轮请示）**：
1. **r040 全景推理资产轮（新，最高优先）**：用既有权重做纯推理（identity + h-flip + v-flip 三视图一次到位），同时产出 ①测量学全景（AR 资格域敏感性是否为跨架构/跨角度表征/跨域的普遍律）②OER 所需等变证据特征 ③机制底料 ④每基线 provenance 表（AGENTS §4.1 全字段 + checkpoint sha256 + 与 readme 记录 mAP 的对齐核验——同时解决外部审稿人 P2"单元匿名不可接受"）。**无论 OER 生死都有价值，故排在 OER 门之前。**
2. **OER 门（r039 修订版）**：在扩展单元池上执行，功效远高于原 8 单元版；**r039 原件降级为待superseded**（不作废，作为 pilot 规格保留）。
3. **OER-D 蒸馏头**（训练，GPU）→ **密封确认**（DOTA-v2.0 val / SODA-A official test，全程禁触至该轮）。
4. **成稿轮后置**：`r038` 服务器**尚未启动**（无 STARTED），B 主动撤回并让位给 r040——理由：先做全景再定稿，避免按旧档位写完再全面重写；成稿骨架/claim-check/图件规格在 r038 计划中保留复用。

**档位说明（不预支）**：本节不改变当前可辩护档位 `STRONG_JSTARS_OR_REMOTE_SENSING`。全景资产使更高档位**可尝试**，不等于已达到；一切以 r040 及后续轮的实际结果为准。

## 21. r040 部分交付与 r041 修复 2026-08-17

- **收获**：HRSC2016 val **七单元完整三视图入库**（3,190 matched TP rows，独立 validation pass，三 mutation 拒绝，provenance 齐全）。这是新域（长条船试金石）首次进入单元池。禁触端点零访问已证明。
- **失手一**：DOTA Tier-2 五单元 **AP 全线崩塌**（PSC 实测 0.2566 vs readme 0.5562；ARS-DETR 0.0474；Strip 0.1749）。**B 定位根因：用了 official-val overlay，而这些权重在切片数据上训练**；r019/r025 取得精确 AP parity 用的是 `/home/rspip/cqc/data/dataset/dota/split_ss_dota10_dota15/val`（annfiles/ + images/ + png）。这是布局错配，非权重或科学问题，r041 强制改正。
- **失手二**：三单元技术失败（fcos config `__file__`、h2rbox evaluator、rtmdet 空数据集），均为工程问题，r041 给出绕过方案。
- **损失**：ICDAR-MLT 2019 数据根不在盘 → 跨遥感域（TPAMI 门槛点名项）本轮无法获得；服务器未下载替代，处置正确。该域暂列不可得。
- **B 合同缺陷记账**：r040 把 AP 对齐写成"超差不 kill 只标记"，导致五个单元在错误布局下白跑三视图预算。r041 改为**AP parity 作单元有效性门**：不过则跳过该单元三视图，省预算且不污染分析池；并要求**每单元跑完即提交**，避免墙钟截断再次丢失成果。
- **档位（规则5要求的评估）**：本轮为资产轮、无科学裁决，可辩护档位**维持 `STRONG_JSTARS_OR_REMOTE_SENSING` 不变**。全景仍未成形（有效新单元仅 HRSC 七个），故不上调；HRSC 入库是实质进展，故不下调。

**追记 2026-08-14（B 自我记账）**：B 上一轮给用户的服务器清理命令把 `corrective_audit_r028_20260813/r026_raw_revalidation/` **整目录**搬入 legacy 区——但 r031 报告列出的未跟踪项只是该目录下的 `error.json` 一个文件，结果 3 个 r028 受保护 tracked 文件被顺带移出工作树（服务器 2026-08-14 监督记录发现并如实上报，未擅自恢复，处置正确）。责任在 B 的命令粒度。修复（用户或 C 在服务器原工作树执行即可，字节自 HEAD 恢复）：`git checkout -- top_journal_v3_reaudit_055/corrective_audit_r028_20260813/r026_raw_revalidation/`。服务器已另建干净 worktree（`orientbench_r032_clean`）供后续轮次，主链不受阻。当前等待：C 关闭 r031（owner-only）并签发新预检 dispatch。

## 13. 2026-08-18：r042 关闭与 r043 SAUR-OBB 新方法路线

- 用户明确授权 B 代关闭 r042。B 核验最终 traced production、validator、mutation 与八单元指标后裁定 `ACCEPT_EXECUTION / KILLED / REJECT_OER_METHOD`；旧 selector、Q-SetOD、OER/OER-D 全部终止。
- 当前可辩护级别仍为 `STRONG_JSTARS_OR_REMOTE_SENSING`，低于项目合法目标，不投稿收口。
- B 冻结 r043：在 PSC detector 内增加 symmetry-aware axial residual-distribution head，同时输出方向修正与 concentration；以 DIOR-R、SODA-A 和 budget-matched continuation 作两数据集生死门。只有 AP75、mean angle error、native normalized AUGRC 同时过预注册门槛才进入多架构 Stage B。
- 用户 L2 授权 reference：2026-08-18『给出顶刊的方案，让服务器去执行，开始。』
- 冻结计划：`dis/plans/B/b-r043-saur-obb-stagea-20260818/sug.md`。

## 14. 2026-08-18：r043 终止后转入 r044 JPRS measurement 成稿门

- r043 已由 B 验收并关闭：DIOR-R、SODA-A 的 SAUR epoch-1 AP50 相对 BASE 分别回退 `0.203`、`0.167`，接受 `REJECT_SAUR_METHOD`，禁止 Stage B、加预算或调门槛续命。
- 实现审计同时发现 geometry gate 与冻结公式不一致，因此拒绝只限已执行配置；巨大双数据集性能坍塌足以终止本线，不值得为修补外推范围而重跑。
- 当前可辩护档位维持 `STRONG_JSTARS_OR_REMOTE_SENSING`，低于合法目标；但受控扰动、几何可辨识域、NRC/risk-coverage、image-level finite-sample risk control 和 600 目标双人互盲标注仍构成一条完整的测量学正证据主线。
- B 冻结 r044：以 JPRS 为目标完成英文 measurement–diagnostic 全稿、图表、补充材料、精确 claim checker、引用审计与双红队。禁止 selector/fix/deployable 包装；只有五项 venue gate 均过才可输出 `JPRS_SUBMISSION_CANDIDATE`，否则必须诚实输出 `NOT_JPRS_READY`。
- 用户 L2 授权沿用 2026-08-18『给出顶刊的方案，让服务器去执行，开始。』；计划：`dis/plans/B/b-r044-jprs-measurement-manuscript-20260818/sug.md`。

## 15. 2026-08-18：r044 完整成稿验收，严格 JPRS gate 未通过

- B 复跑 exact claim checker、三项真实 mutation 与 manifest：`57/57 PASS`，三项 mutation 全部非零拒绝，执行与证据闭合可接受。
- 交付完整：8,150 词英文主稿、补充材料、九张机器表、六组 SVG+PNG、24 条已核引用、双视角内部红队与 venue gate。
- B adopt `NOT_JPRS_READY`：两份内部红队的 novelty 均为 `3/5`；其余 technical soundness / evidence breadth / presentation / JPRS fit 均为 `4/5`。这不是润色问题。
- 当前科学档位维持 `STRONG_JSTARS_OR_REMOTE_SENSING`。主缺口是没有 prospective held-out remote-sensing decision study：现有 severe event 与 rectangle-IoU geometry 接近，六个 LTT 单元又全部选择 full coverage，尚未证明协议改变一个真实模型/阈值决策并在 domain shift 下保住 image-level risk。
- 下一步只能补一个预先冻结、应用端点非同一 IoU 容忍曲线的 held-out 决策研究；不再补普通 detector row，不再试 selector/head，不靠写作宣称顶刊。

## 16. 2026-08-18：r045 prospective axis-drift 决策研究

- r045 冻结一个独立于 rectangle-IoU tolerance 的应用端点：`d_tip=min(1, (GT_AR/2)*sin(angle_error))`，表示沿预测轴线做切片/排列时，GT 长轴端点相对预测轴的横向漂移（以 GT 短边归一化）；主严重阈值为半个短边。
- source=`DIOR-R`，sealed target=`HRSC2016`；只用既有 consumed 数据、既有 valid baselines 与原冻结 D_cal/D_audit，不触 DOTA-v2.0/SODA official test，不训练 detector。
- 候选 family 预注册为 Oriented R-CNN、LSKNet Oriented R-CNN、RTMDet-S。比较 AP-only 全覆盖策略与 orientation policy；只有策略发生非平凡变化后才允许打开 HRSC audit outcome。
- target PASS 必须同时满足：paired image-bootstrap 连续/严重风险改善、风险 UCB<=0.10、eligible coverage>=0.70、AP50 回退<=0.02、敏感性与独立审计通过。任何一项失败即停止，不调 endpoint/coverage/gate。
- 计划：`dis/plans/B/b-r045-prospective-axis-drift-decision-20260818/sug.md`；这是当前唯一可能把 novelty 从 3/5 补到 4/5 的科学轮。

## 17. 2026-08-18：r045 早停验收与顶刊路线关闭

- B 采纳 `APPLICATION_SHIFT_FAIL`：98 张 sealed HRSC2016 D_audit 图像上，orientation policy 的 `Delta_cont=-0.0019519474`，95% CI `[-0.0075969074,0.0035536397]`；主严重风险差为 0；`q={0.25,0.50,1.00}` 敏感性为负/零/零。G3 与 G5 的 benefit 条件失败，禁止事后修改 endpoint、阈值、coverage、candidate 或 selector。
- target 负结果可复核：A/B 原始输入重算一致，五项真实 mutation 均非零，106 个 manifest 项按 Git blob 字节全部闭合，禁触 DOTA-v2.0 val / SODA-A official test 未打开。
- 执行带审计保留：正式 `POLICY_SEAL` 与 `source_analysis/` 使用 all-prediction quantile（R50 阈值 0.0712），但后置、非 operative 的 `source_policy_results.json` 写成 0.8388、源统计冲突且引用未入库脚本；`STARTED.json` 也曾被历史提交改写后恢复。两者不改变 R50@0.90 的架构选择、独立 HRSC score-only 阈值或 target 负结论，但不得包装为整包无瑕疵。
- 当前可辩护档位仍是 `STRONG_JSTARS_OR_REMOTE_SENSING`，低于项目合法 TGRS-or-better 门槛。r044 唯一允许的 prospective application 补强已失败，当前证据下停止顶刊实验扩展，不激活 r046 rescue。
- 若未来重开顶刊路线，必须先由用户明确授权真正的新科学投入：独立采集的下游应用标签与 prospective endpoint，或全新 orientation-reliability 方法并在未消费 endpoint 上验证；不得继续在已打开的 DIOR-R/HRSC split 上试阈值、端点、selector、审计或文字救场。

## 18. 2026-08-18：用户授权 r046 semantic-heading 新方法路线

- 用户在 B 明确说明新标签/新方法需重新授权后回复“授权，抓紧进行下一步”，故 r046 L2 新科学投入成立；本轮不把 r045 负结果改口，也不做其 endpoint/selector rescue。
- 新任务使用 HRSC2016 原始 `header_x/header_y` 船头点，把普通 OBB 的 `theta mod pi` 无向轴扩展为 `phi mod 2pi` 有向 semantic heading；这是真实应用标签，不再以 rectangle-IoU 或 axis-drift proxy 冒充下游任务。
- 新方法 AHC-OBB：共享 endpoint encoder + 无 bias 差分 logit，结构上保证交换两个轴端点时 logit 变号、概率互补；不修改 detector box/class/score，另行输出 heading 与 confidence。
- Stage A 使用 official train 训练、val 的 V_fit/V_cal 做模型选择与风险阈值、test 在 model/threshold seal 后一次揭示；同时挂接 R50 与 LSKNet 两个既有 HRSC host。必须打赢 parameter-matched unconstrained classifier 与 CHP-like head-point regression，并达到两 host 的 accuracy/AUGRC/risk-control 门。
- 通过只进入 Stage B：新增 FGSD 或另一真实 head-label 数据做跨数据集/传感器验证；Stage A 不宣称 JPRS/TGRS ready。计划：`dis/plans/B/b-r046-ahc-obb-semantic-heading-stagea-20260818/sug.md`。

## 19. 2026-08-18：r046 服务器回执拒收，科学未裁决

- B 拒绝把服务器的 `NO_SAFE_THRESHOLD` 当成有效科学早停，按冻结 mapping 关闭为 `INCOMPLETE / PROTOCOL_DRIFT / PENDING`。HRSC test 船头语义字段看起来仍未打开，资产保住；但 Stage B 不获授权。
- 决定性错误：`calibrate_vcal.py` 单独排序 confidence 后仍按原顺序索引 error，三档风险不再对应 retained samples；同时完全没有计算计划要求的 one-sided Hoeffding–Bentkus UCB。因此 `0.19844/0.21491/0.24000` 不能用于 G4 裁决。
- 信息墙已越过：V_fit/V_cal 清单在多轮完整 val 船头标签读取、full-val accuracy 比较和 crop transform 修正之后才生成，不满足“先冻结 split 再打开 val heading values”。
- 交付只是随机初始化的单卷积 16-channel、6.8 KB `smoke/formal proxy`；没有 detector-R50 初始化、冻结 jitter/temperature/V_fit model selection、HEADPOINT_REG、两 host、manifest、独立 validator、mutation 或 schema-2 report。故 `REJECT_AHC_OBB_METHOD` 不成立，proxy 的 0.7837 val accuracy 也只能视为开发信号。
- 项目档位维持 `STRONG_JSTARS_OR_REMOTE_SENSING`，低于 TGRS-or-better 合法线。r046 既不升档也不降档；在新用户授权与全新、诚实标注已消费 val 状态的 dispatch 前，不处理下一科学轮。

## 20. 2026-08-18：用户授权 r047 clean formal 重跑

- 用户在 r046 被关闭为 `INCOMPLETE / PROTOCOL_DRIFT` 且 B 明确说明必须新授权后回复“继续推进执行”，构成 r047 L2 授权。
- official train/val 全部降为 consumed development；不再把 r046 后置生成的 V_fit/V_cal 包装成 calibration。唯一未揭示的 official test 先只按 image ID 哈希封存为 T_cal/T_audit，再实行 model seal→T_cal seal→T_audit 两道墙。
- r047 必须使用注册 HRSC Oriented R-CNN R50 backbone，完整训练 AHC、WHOLE_CROP、CONCAT_ENDPOINT、HEADPOINT_REG，四卡 DDP、双 host、配对 confidence/error 与真正的 complete-image finite-sample UCB。任何 tiny proxy、缺 baseline 或错配校准均为未执行完毕。
- 通过 Stage A 只进入第二 head-label 数据集外部验证；当前档位仍为 `STRONG_JSTARS_OR_REMOTE_SENSING`，没有预支 JPRS/TGRS。

## 21. 2026-08-18：r047 formal token 拒收，但 AHC 投资路线停止

- r047 的 test identity partition 与四臂 30-epoch 训练是真实进展，T_audit 仍未发现被打开；AHC/WHOLE/CONCAT/HEADPOINT 的 val accuracy 分别为 0.8429/0.8743/0.8651/0.8614。
- B 从 1,764 条 T_cal raw rows独立重算：70% 档 GT/R50/LSKNet 的 realized coverage 为 0.6992/0.6990/0.7005，包含全部 225 images 的合法 UCB 为 0.1566/0.1890/0.1730，三 view 仍不满足安全门。负方向不是 r046 的旧配对 bug。
- 但 formal completion 不成立：dispatch 已在 `4db8ced` 以环境失败终止后无 tracked resume 又覆盖报告；MMRotate 通过伪造版本字符串绕过 guard；训练漏 warmup/cosine/color jitter/AUGRC，HEADPOINT 不是二维头点回归，AHC retry 实际代码不可追溯，校准漏 temperature/Hoeffding/全 image accounting/one-to-one matching，且无 checkpoints bundle、manifest、独立 validator/mutations。
- 因 GT UCB 只高门槛 0.0066，以上科学配置漂移可能翻转 formal gate，故不采纳 `REJECT_AHC_OBB_VALID_TCAL_SAFETY_FAIL`。执行关闭为 `INCOMPLETE / PROTOCOL_DRIFT / PENDING`。
- 资源决策仍明确停止 AHC：它已比 strongest whole-crop baseline 低 3.14pp，三 view 的纠正校准也全部失败；禁止 Stage B，也不再开 AHC 修复轮。项目维持 `STRONG_JSTARS_OR_REMOTE_SENSING`，下一条顶刊路线必须是真正不同的新方法/任务并另获授权。

## 22. 2026-08-19：用户授权 P2C-Lift 新方法路线

- 用户在 B 明确 r047 不重跑、下一步必须是科学上完全不同的新方法/任务后回复“推进下一步吧”，构成业务指令 048 的 L2 授权。
- 新方法 P2C-Lift 把 OBB 的 axial angle（`mod pi`）建模为 projective state，再以 conditional pole变量概率抬升到 full heading（`mod 2pi`）；同时输出 axial concentration、pole posterior和完整方向风险。它不复活 AHC hard comparator。
- 最近邻边界：CHPDet 已在 TGRS 做 center-head point 360°检测，故任务和船头预测本身不新；本项目必须靠 double-cover factorization、intrinsic reliability、跨 host plug-in和后续 source-disjoint 外部验证建立创新。
- r048 只用 train/val/T_cal consumed development开发；仅当 P2C 对 whole/concat/真实 headpoint/direct-S1 强基线在两开发分区同时过门，才打开仍密封的 228-image T_audit。通过后另轮获取 FGSD2021或ShipRS非HRSC去重子集。
- 当前档位不变：`STRONG_JSTARS_OR_REMOTE_SENSING`；r048 Stage A 全过只恢复 JPRS/TGRS potential，不预支 ready。

## 23. 2026-08-19：r048 P2C-Lift 有效 G1 早停，方法路线关闭

- 第三次 clean rerun 修复了此前的 pole 训练/解码反向：BCE、full-S1 likelihood、Bayes decoder 与 intrinsic confidence 统一为 `positive logit = q(sheet=1)`；双 sheet、180° mutation 与 H/V/R transform tests 通过。
- 冻结首 epoch 早停严格成立：CONCAT baseline 首 epoch `0.656192>=0.65`，P2C small/base/wide 分别只有 `0.502773/0.506470/0.499076<0.60`。三候选按协议均停止，无需用 baseline 的 30-epoch best 偷换判定。
- row-level val 复算确认：selected P2C base accuracy `0.506470`、mean error `87.741°`、AUGRC `0.423795`；whole-crop baseline 为 `0.885397/21.336°/0.024484`，5/10/15° jitter 也全方向失败。
- B 采纳 `REJECT_P2C_LIFT_DEVELOPMENT`，业务 048 以有效 gated early stop 关闭；T_cal 与 T_audit 均未打开，禁止 P2C 调参、确认、audit 或外部 Stage B。
- 项目仍为 `STRONG_JSTARS_OR_REMOTE_SENSING`，低于 TGRS-or-better。后续不得再做 HRSC crop-head/selector rescue；若冲顶刊，只能在用户新授权下投入 detector-native probabilistic orientation reliability 与独立 source-disjoint 应用标签/端点，或接受现实档位投稿。
