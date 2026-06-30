# Orientation Reliability：面向旋转目标检测的可信角度测量、诊断与选择

> 合作者审核用论文主稿草案（中文）。无期刊/会议名称、无投稿目标。所有数字来自 measure_fix_v2/ 与 outputs/bench_core/ 的 report/csv/json，非凭记忆。证据不足处标 pending/limitation。
> thresholds.yaml 冻结 sha256 b7c4e649；DOTA 采用 train 训练 / val 验证自跑协议（不追公开 mAP）。

---

## 合作者审核摘要

- **本项目在做什么**：把"旋转目标检测的朝向是否可信"做成一个可测量、可诊断、可初步修复的问题。P1 = measure+diagnose（朝向可靠性度量 NRC、reliability cliff、PSC 反校准）；P3 = fix（reliability-aware orientation selector，后处理选择，不重训 detector）。
- **为什么没有大规模 GPU 训练**：研究对象是 reliability 的**测量/诊断/选择**，不是训练更强 detector。大规模重训会混淆变量；已有 checkpoint 足以产生可靠性分析对象；selector 是轻量后处理模块；GPU 仅用于 inference / TTA / forward dump，不追 mAP。
- **科学贡献点（克制，不绑定 venue）**：① 在当前可比设置中 NRC 提供 mAP 之外的 reliability signal（**不主张严格独立**）；② orientation reliability 随 aspect-ratio 退化呈结构性 cliff；③ PSC 检测器 detection-score 与 intrinsic phase_mod **双重反校准**（机制候选）；④ 一个 reliability-aware selector candidate（source-supervised + target GT-free inference）在多 dataset/detector 上修复部分排序问题。
- **有没有吹牛**：核心结论均有 bootstrap CI + 可复算 artifacts；明确标注 candidate / limited / pending；**不**声称 P3 final method 完成、顶会 ready、PSC angle head 最终证明反校准、full project complete。
- **当前最需要合作者审什么**：① measure/diagnose 的科学口径是否严谨；② P3 selector 定位（candidate vs method）是否合适；③ Track A phase_mod 机制候选的表述强度；④ 下一步是继续写作还是补实验（real TTA 全覆盖 / Track A negative control）。
- **下一步建议**：进入合作者审核；并行补非 PSC real TTA + DOTA #20 Track A negative control（不调参）。

---

## 1. 摘要
旋转目标检测以 mAP 为核心，难刻画**朝向可靠性**（角度何时可信）。本文提出 measure→diagnose→fix 框架：（measure）定义 NRC-AUC/Risk@k/near-square-aware 度量，在 **23 real cells / 6 datasets** 上测量；（diagnose）发现 orientation reliability 随 aspect-ratio→1 的结构性 cliff，以及 PSC 检测器的 detection-score 反校准（FAIR1M/SODA bootstrap 显著）与 intrinsic phase_mod 反校准（3/3 PSC cell NRC>1）；（fix）一个非线性 geometry-aware reliability-aware selector，在固定 box-size bin 内仍显著优于 score+ar+size 线性基线（非 size prior），并在 leave-dataset/leave-detector（无目标 GT）与 real TTA（4 cells/3 datasets）上稳定优于基线。**边界**：selector 为 candidate（非 final method），real TTA coverage 有限，Track A 为机制候选，非 DOTA 为 exploratory，full project 未完成。

## 2. 引言
- **为什么 mAP 不够**：mAP 聚合定位+分类，对朝向只给平均误差，不回答"何时朝向可信"与"能否挑出可信预测"。
- **为什么 angle reliability 是独立问题**：本文测得 NRC 与 mAP 在 23-cell 上**未检出显著相关**（§4），即可靠性 ≠ 精度。
- **不追 DOTA 公开 mAP**：DOTA 用 **train 训练 / val 验证**自跑协议，val mAP 低于公开论文属正常，与本文命题无关。
- **非 detector 训练论文**：贡献是 reliability 的 measure/diagnose/select，不重训 detector（§"为什么没有大规模 GPU 训练"）。

## 3. 任务定义与协议
- **orientation reliability**：检测器角度预测可信度；以 selective risk-coverage 衡量。
- **NRC-AUC**：selection score 排序下的归一化 risk-coverage 面积；=1 等价随机，<1 良校准，>1 反校准。**AURC**：risk-coverage 曲线下面积。**Risk@70/90**：70%/90% coverage 处的 selective risk。
- **angle tail risk**：朝向误差 p90/p95/p99。**near-square / degeneracy**：长宽比→1 时朝向不适定（GV-obliquity gv_obb_needed=1−OBB/HBB area）。
- **D_cal / D_audit**：确定性 md5 image-level split（互斥）；selector 仅 D_cal 训练，判定只 D_audit。
- **formal vs exploratory**：formal 仅 DOTA frozen scope；非 DOTA exploratory。
- **Track A/B/C**：A=detector 原生角度置信（PSC phase_mod）；B=detection-score proxy；C=geometry-aware selector。**Route-C**=Track C + GT-free TTA consistency（deployable）。

## 4. Measure：测量 orientation reliability
- **覆盖**：23 real cells / 6 datasets（DOTA-v1.0 6 / DOTA-v1.5 4 / DIOR-R 6 / FAIR1M-v1.0 3 / SODA-A 3 / HRSC2016 1）。DOTA = formal scope（D2/host/C1/A4 冻结）；非 DOTA = cross-dataset exploratory。
- **NRC vs mAP 构造效度**（within-dataset/comparable，23 cells）：Spearman(NRC,mAP)=**-0.046**（95% CI [-0.49,0.48]），控 dataset+family 偏相关=**-0.005**，mean rank distance 7.83/23 → **未检出显著相关；NRC 提供不同于 accuracy 的 reliability signal**（不主张严格独立，n=23）。
- **aspect-ratio reliability cliff**：朝向误差 p99 随 ar→1 升至 ~88-90°（near-square ill-posedness）；masked（去 near-square）p99 ~10-26°。→ reliability 随退化呈结构性 cliff。
- **tail risk**：well-defined region masked p99 非平凡（10-26°），是真实尾部；unmasked 90° 尾部为 near-square 几何退化（**非** detector 灾难性失败）。

## 5. Diagnose：诊断失效模式
- **PSC detection-score proxy 反校准**（masked，bootstrap）：FAIR1M 1.083 [1.03,1.13]、SODA 1.260 [1.24,1.28] **显著>1**；DOTA 0.840（不显著）、DIOR 0.549（不显著）。→ PSC 在小目标/细粒度 dataset 上 detection-score 选角度反校准。
- **PSC phase_mod intrinsic 机制候选**（Track A，instrumented forward dump）：phase_mod NRC = DIOR **1.156** [1.11,1.19] / SODA **1.117** [1.11,1.13] / FAIR1M **1.121** [1.08,1.16]，**3/3 PSC cell 显著>1** → PSC 自身角度码置信与正确性反相关，支持 **intrinsic angle-coder miscalibration mechanism candidate**。**克制**：phase_mod 是一个 intrinsic 信号；为 candidate / supported by phase_mod evidence，**不能说 PSC angle head 最终证明反校准**；Track A 非唯一决定性证据。
- **DOTA #20 weak-structure negative control**：within-target oracle_gain 0.155（最低）、masked NRC 0.84（未显著反校准）；method 无大幅提升属预期，**不调参**。
- **near-square vs well-defined**：near-square 主导 90° 尾部；well-defined region 才是可学习问题空间。

## 6. Fix：reliability-aware selector
- **G2_double_prime**（排除 box-size prior 替代解释）：在**固定 box-size bin** 内，nonlinear geometry-aware selector 仍显著优于 score+ar+size 线性基线。
- 对照：score-only / score+ar+size linear / nonlinear geometry-aware selector（GBM，score+log_ar+log√area+GV+w+h）。
- **Deployable hardening**：leave-dataset/leave-detector（无目标 GT）。
- **Route-C GT-free proxy**：Track C + GT-free consistency（offline local-angle-consistency 与 real TTA）。
- **real TTA coverage**：shadow farm（未改 dataset）+ real hflip/vflip。
- **Track A** 作为机制支线（非门控 P3）。

## 7. 实验结果（具体数据）
- **G2_double_prime = PASS**：primary ar≥1.6 下 **21/21 size-bin×cell 的 ΔNRC(size_linear−nonlinear) CI>0**；ar1.3/2.0 sensitivity 20-21/21。→ orientation-specific 非线性几何，非 box-size prior。
- **Deployable = STABLE-PASS**：unseen cells **12/14（85.7%）beat size-linear**（非 DOTA **12/12**）；retained oracle gain mean 0.481（all）/ **0.645（非 DOTA）**；leave-dataset 6/7、leave-detector 6/7；唯一 fail = DOTA #20（documented limitation）。
- **Route-C offline = STABLE-PASS**：非 DOTA **10/10 beat size-linear**，8/10 beat geometry-only，retained **0.718**。
- **Route-C real TTA = STABLE-PASS on tested cells**：**4 cells / 3 datasets**（DIOR ORCNN#3+PSC#22；SODA PSC#23 NRC 0.378；FAIR1M PSC#24 NRC 0.499），均 beat size-linear 且 beat geometry-only，tta_match 0.99-1.00。
- **Track A**：phase_mod 3/3 PSC cell NRC>1 显著（见 §5）；Track C geometry 最佳（NRC 0.356/0.389/0.519）。
- **PSC FAIR1M/SODA detection-score 显著>1**（§5）；**DOTA #20 limitation**。

## 8. 消融与图表计划
| 图/表 | 数据路径 | caption draft | 支持 | 不能支持 |
|---|---|---|---|---|
| Fig1 aspect-ratio cliff | outputs/.../fig1_reliability_cliff_data.csv | p99/NRC vs aspect-ratio | reliability cliff 真实 | detector catastrophic failure |
| Fig2 masked/unmasked CDF | outputs/.../fig2_angle_error_cdf_data.csv | 角度误差分布尾部 | 90° 尾来自 near-square | well-defined catastrophic |
| Fig3 PSC NRC+CI | outputs/.../fig3_psc_nrc_ci_data.csv | PSC vs others NRC bootstrap | FAIR1M/SODA 反校准 | DOTA 反校准 |
| Fig4 G2'' size-bin | measure_fix_v2/reports/fig_g2doubleprime_size_control.csv | 固定 size-bin ΔNRC | 非 size prior | deployable final |
| Fig5 leave-dataset/detector | measure_fix_v2/reports/fig_deployable_leave_dataset_detector.csv | 无目标 GT 部署 | 多数 unseen 优于基线 | DOTA / full deploy |
| Fig6 Route-C real TTA | measure_fix_v2/reports/fig_route_c_real_tta.csv | offline vs real TTA | real TTA 一致优于基线 | full coverage |
| Fig7 Track A phase_mod | measure_fix_v2/reports/fig_track_a_psc_mechanism.csv | A/B/C NRC | intrinsic 反校准 candidate | 最终机制证明 |
- caption 细稿见 outputs/.../figures_required_for_top_tier.md 与 measure_fix_v2/reports/fig_table_captions_044.md。

## 9. 局限性
- full project **incomplete**；非 DOTA **exploratory**（未冻结阈值）。
- **real TTA coverage limited**（4 cells/3 datasets，PSC 为主；非 PSC + 更多 dataset = next-step）。**非全覆盖**。
- **Track A 不是最终机制证明**（phase_mod 一信号，candidate；需更多 intrinsic 信号/controlled 实验）。
- P3 selector 训练用 source GT（calibration/upper-bound），**非 final deployable method**。
- P2/C1 = appendix/negative result（OT 未明确打赢 GT-identity），不作主线。
- point2rbox blocked（上游 ted.pth 不可用）；ARS-DETR/Strip 部分 cross-dataset coverage blocker。
- 不追公开 mAP；DOTA #20 不调参。

## 10. 结论
本文提出并验证 **orientation reliability** 这一 accuracy 之外的诊断维度：P1 提供测量与诊断（NRC 提供 mAP 之外的 reliability signal（不主张严格独立）、reliability cliff、PSC 双重反校准机制候选）；P3 初步证明 reliability-aware selector 能修复部分朝向排序问题（固定 size-bin 内非线性、leave-dataset/detector、real TTA 一致优于基线）。**最终方法与更大范围验证仍需后续工作**；本文不声称 P3 final method 完成或顶会 ready。

---

## 为什么本文不以大规模 detector 重训为目标
- 研究对象是 **reliability measurement / diagnosis / selection**，不是训练更强 detector。
- 大规模重训 detector 会**混淆变量**（无法区分是可靠性方法的贡献还是更强 backbone 的贡献）。
- 已有 checkpoint **足以产生可靠性分析对象**（预测 + 角度误差 + intrinsic 信号）。
- selector 是**轻量后处理 / 选择模块**，不改 detector 权重。
- GPU 仅用于 **inference / TTA / forward dump**，不用于追 mAP。

## 简短 claim ledger
- **allowed**：NRC 提供不同于 mAP 的 reliability signal；orientation reliability 存在结构性 cliff；PSC 存在 detection-score proxy 反校准；PSC phase_mod 支持 intrinsic mechanism candidate；G2_double_prime pass；Deployable/Route-C stable-pass on tested cells；P3 method development 可以继续。
- **qualified**：real TTA coverage limited；Track A 是机制候选；P3 不是 final deployable method；cross-dataset 仍 exploratory。
- **forbidden**：full project complete；P3 final complete；top venue ready；PSC angle head finally proven broken；C1 genuine multi-view solved；A4 cross-host causal proved；ARS-DETR equals RHINO；non-DOTA formal gate passed。
