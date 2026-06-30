# Orientation Reliability：面向旋转目标检测的可信角度测量、诊断与选择

> 正式论文中文稿。图片不实际绘制（图表占位见 §9）。所有数字来自项目已有 report/csv/json，非凭记忆。证据不足处标 limitation / pending，不编造数据与文献细节。
> 协议约定：DOTA 采用 train 训练 / val 验证自跑协议（不追公开 test mAP）；thresholds 配置冻结（sha256 b7c4e649…），D_cal/D_audit 划分冻结。

---

## 摘要

旋转目标检测（oriented object detection, OBB）以 mAP 为主要评测指标，难以刻画**朝向可靠性**（orientation reliability）：检测器输出的角度在何种条件下可信、何时发生灾难性失配，以及能否在不重训检测器的前提下挑选出可信的角度预测。本文提出一个 **measure → diagnose → fix** 框架。在测量层面，我们定义归一化风险覆盖曲线下面积（NRC-AUC）、风险覆盖（risk-coverage）与 near-square 感知的角度误差度量，并在 **23 个真实评测单元（cells）/ 6 个数据集**上系统测量。结果显示，在当前可比设置中 NRC 与 mAP 未检出显著相关（Spearman ≈ −0.05），即朝向可靠性提供了独立于精度的信号（不主张严格独立）。在诊断层面，我们发现朝向可靠性随长宽比趋近 1 呈现结构性的 **aspect-ratio reliability cliff**，并发现相位编码检测器（PSC）在以 detection-score 作选择时反校准（FAIR1M/SODA 经 bootstrap 显著），且其内在相位模长（phase_mod）亦反校准（3/3 PSC cell NRC>1），构成一个 **angle-coder 机制候选**。在修复层面，我们提出 geometry-aware reliability-aware selector，并通过固定 box-size 分箱实验（G2_double_prime）证明其增益不是 box-size 先验。我们进一步以 **supervision spectrum**（upper-bound / source-supervised target-GT-free / fully GT-free proxy）系统评估不同监督预算下的朝向选择，并在非 PSC 检测器（ORCNN、LSKNet）跨 3 个数据集的 leave-detector / leave-dataset 设置下，证明 source-supervised + target-GT-free 选择器多数情形优于强基线。所有主表/主图所需的原始与匹配预测均已持久化并附 sha256 与可复算说明。**边界**：本文不追公开 mAP、不补全检测器矩阵、不重训检测器；非 DOTA 结果为 exploratory；selector 为 deployable candidate 而非最终方法；real TTA 覆盖与 Track A 机制证据均为候选/有限。

**关键词**：旋转目标检测；朝向可靠性；风险覆盖；选择性预测；遥感目标检测；角度不确定性。

---

## 1. 引言

主流 OBB 检测评测以 mAP 衡量"框是否检出且定位准确"，对**朝向**仅给出聚合误差，无法回答两个可靠性问题：（i）在何种几何条件下角度预测不可信？（ii）能否利用检测器自身信号挑出朝向可靠的预测以做选择性使用？这在遥感密集小目标、近方形目标上尤为关键。

本文采取三点立场。其一，**朝向可靠性是独立于精度的维度**：我们在 23-cell 异质矩阵上测得 NRC 与 mAP 未检出显著相关（§5），可靠性 ≠ 精度。其二，**不追公开 mAP**：DOTA 采用 train 训练 / val 验证自跑协议，val mAP 低于公开论文属正常，与本文命题无关；本文亦不补全 9 检测器矩阵。其三，**不重训检测器**：研究对象是可靠性的测量、诊断与选择，selector 是轻量后处理模块；大规模重训会混淆变量，难以区分可靠性方法的贡献与更强骨干网络的贡献。

本文贡献为四条：（1）**Measure** —— 提出 NRC / risk-coverage 度量刻画 OBB 角度可靠性；（2）**Diagnose** —— 发现 aspect-ratio reliability cliff 与 PSC score-level / phase_mod 机制候选；（3）**Fix** —— geometry-aware selector 在固定 size-bin 内优于 score+ar+size 线性基线，说明非 size 先验；（4）**Deployability spectrum** —— 从 upper-bound 到 source-supervised target-GT-free 再到 fully GT-free proxy，系统评估不同监督预算下的朝向选择。

## 2. 相关工作

**旋转目标检测与角度表示**：基于 anchor / DETR 的旋转检测器与 long-side / le90 角度约定 [R1]。**OBB 角度损失**：GWD / KLD 等基于分布距离的旋转回归损失缓解边界与方形歧义 [R2]。**角度不确定性 / 角度编码**：CSL / DCL / PSC 等将角度离散或编码为相位以缓解周期不连续 [R3]。**检测校准**：D-ECE 等面向定位/分类置信校准 [R4]，与本文聚焦的朝向可靠性不同。**选择性预测 / 风险覆盖**：risk-coverage 与选择性风险是本文 NRC 度量的方法学根源 [R5]。**square-like / near-square ambiguity**：近方形目标朝向的不适定性 [R6]。**遥感 OBB benchmark**：DOTA / DIOR-R / FAIR1M / SODA-A / HRSC 等 [R7]。（无正式 bib，引用以 [R*] 占位，不编造具体文献细节。）

## 3. 问题定义与协议

**Orientation reliability**：给定检测器在图像上的预测集合 {(box_i, score_i)}，每个 box 含角度 θ_i；朝向可靠性以"按可靠性分数排序后的选择性朝向风险"衡量。

**Matched prediction 与 angle error**：将预测以几何匹配到真值；角度误差取 OBB 的 π-周期最短距离 `|((Δθ+π/2) mod π) − π/2| ∈ [0°, 90°]`，并以 canonical long-side 解决 (w,h,θ)↔(h,w,θ+90°) 表征对称。

**Near-square / well-defined region**：当长宽比 max(w,h)/min(w,h) 接近 1 时，"长边"不确定，朝向不适定（near-square）；本文主分析在 well-defined region（aspect ratio ≥ 阈值，默认 1.6）进行，并单独报告 near-square 的退化作用。

**度量**：NRC-AUC（选择分数对朝向风险的排序质量，=1 等价随机、<1 良校准、>1 反校准）；AURC（risk-coverage 曲线下面积）；Risk@70 / Risk@90（70%/90% 覆盖处选择性风险）。

**D_cal / D_audit**：确定性 md5(image_id) 的图像级互斥划分；selector 仅在 D_cal 训练，最终判定只在 D_audit。**formal vs exploratory**：formal 仅限 DOTA 冻结范围；非 DOTA 为 exploratory。

**Track A / B / C 与 supervision spectrum**：A = 检测器原生角度置信（PSC phase_mod）；B = detection-score proxy；C = geometry-aware selector。**Route-C** = Track C 加 GT-free 一致性特征。监督光谱三档见 §7。**正确口径**：Route-C 的 selector 由 source GT angle-error 训练，target 不使用任何 GT，仅做推理 —— 即 **source-supervised + target GT-free inference**，**不是 fully GT-free**。

## 4. OrientBench 测量协议

**数据集与检测器**：DOTA-v1.0、DOTA-v1.5、DIOR-R、FAIR1M-v1.0、SODA-A、HRSC2016；检测器涵盖 oriented R-CNN、rotated RetinaNet+PSC、rotated RTMDet、LSKNet、Strip R-CNN、RHINO、O2-RTDETR、ARS-DETR 等原型。**覆盖**：23 real cells / 6 datasets。**DOTA formal scope**：D2 partial gate、host 训练与冻结、C1 augmentation-view、A4 same-host，阈值经标定后冻结。**cross-dataset exploratory scope**：非 DOTA 数据集上的多检测器测量，未冻结阈值。**prediction schema**：统一 17 字段（含 OBB、score、le90 角度版本、来源与转换版本、sha256）。**persistent artifacts**：主表/主图/TTA/Route-C/Track A 所需原始与匹配预测已持久化（§附录 D）。**不追公开 mAP**：DOTA 自跑 train/val。

## 5. Measure：朝向可靠性测量

**NRC 与 mAP 的关系**。在 23-cell 异质矩阵上：Spearman(NRC, mAP) = **−0.046**（95% bootstrap CI [−0.49, 0.48]），控制 dataset + detector-family 后偏相关 = **−0.005**，NRC 与 mAP 排序的平均 rank distance = 7.83 / 23；NRC 与朝向中位误差中度相关（Spearman ≈ 0.40）。**措辞（最终）**：在当前可比设置中，**未检出 NRC 与 mAP 的显著相关，NRC 提供了 mAP 之外的 reliability signal；受样本量限制，不主张严格独立**。

**Reliability cliff 与 tail**。按长宽比分箱，朝向误差 p99 在 well-defined region（ar > 2）约 8–10°，而在近方形区（ar < 1.3）升至约 88–90°。整体上，masked（去近方形）p99 约 **10–26°**，unmasked p99 约 **88–90°**。后者主要由 near-square 的几何不适定性驱动，**不应解读为检测器灾难性失败**；前者是 well-defined region 的真实非平凡尾部。

## 6. Diagnose：可靠性失效诊断

**Aspect-ratio cliff**。朝向可靠性随 ar→1 断崖式退化（§5）；这是 near-square 感知度量的实证依据，也定义了可学习问题空间主要位于 well-defined region。

**PSC score-level 反校准**（masked，bootstrap）：FAIR1M NRC = **1.083** [1.03, 1.13]、SODA = **1.260** [1.24, 1.28]（显著 > 1）；DOTA = 0.840（不显著）、DIOR = 0.549（不显著）。即以 detection-score 选 PSC 的角度，在 FAIR1M/SODA 上反校准。

**PSC phase_mod 内在信号 —— 机制候选**。通过插桩前向导出 PSC 相位模长 phase_mod（= phase_cos²+phase_sin²），其 NRC = DIOR **1.156** [1.11, 1.19] / SODA **1.117** [1.11, 1.13] / FAIR1M **1.121** [1.08, 1.16]，**3/3 PSC cell 显著 > 1**。即 PSC 自身角度码置信与朝向正确性反相关。**口径**：phase_mod 是一个有原理依据的内在信号；该结论为 **intrinsic angle-coder miscalibration mechanism candidate（supported by phase_mod evidence）**，**不写 PSC angle head finally proven broken**。

**DOTA #20 weak-structure limitation**。DOTA-v1.0 PSC（cell #20）within-target 可学习结构最弱（oracle gain ≈ 0.155，四个 PSC cell 最低），masked detection-score NRC ≈ 0.84（未显著反校准）。其上 selector 边际收益小，属 **applicability boundary / limitation**，**不是 validation**，且全程不为其调参。

## 7. Fix：reliability-aware orientation selector

**G2_double_prime（排除 box-size 先验）**。在固定 box-size 分箱内比较 nonlinear geometry-aware selector 与 score+ar+size 线性基线。结果：在主阈值 ar ≥ 1.6 下，**21/21 个 (cell × size-bin) 组合的 ΔNRC 自助 CI 均 > 0**；ar ≥ 1.3 与 ar ≥ 2.0 敏感性下亦为 20–21 / 21。由于 size 已在线性基线与分箱中被控制，nonlinear 的增益来自 orientation-specific 非线性几何，**非 box-size 先验**。

**Deployable hardening（leave-\*）**。source-supervised selector 训练于源 cells D_cal，应用于未见 dataset/detector 的 D_audit，target 不用 GT。非 DOTA 单元 **12/12** 优于 size-linear，保留 within-target oracle gain 的均值约 0.645；唯一失败为 DOTA #20（limitation）。

**Route-C 与 real TTA**。Route-C 在几何特征上加入 GT-free 一致性（offline 邻域一致性或真实 hflip/vflip TTA 一致性，逆变换经 round-trip IoU=1.0 校验）。real TTA 覆盖 6 cells / 3 datasets / 3 families（PSC、ORCNN、RTMDet），一致性特征多数情形提供几何之外增益。

**non-PSC leave-\***（核心）。在 ORCNN、LSKNet、RTMDet 跨 DIOR/SODA/FAIR1M 的 leave-detector / leave-dataset 设置下，source-supervised + target-GT-free 选择器在 **8/9** 评估中优于 size-linear，覆盖 **2 个非 PSC family（ORCNN、LSKNet）× 3 个 dataset**；RTMDet（DIOR #61）为唯一失败（其上 geometry-only 反而更差，提示 RTMDet/DIOR 的几何-可靠性关系不同）。

**Supervision spectrum**。
- *Upper-bound（calibration）*：本 cell D_cal GT 训练、同 cell D_audit 评估；证明 orientation-specific geometry structure 可学；**非 deployable**。
- *Source-supervised transfer（主 deployable candidate）*：源 GT 训练、目标域无 GT 仅推理；leave-\* 评估，无 target GT 泄漏。**正确口径为 source-supervised + target GT-free inference，不是 fully GT-free**。
- *Fully GT-free proxy*：不训练任何 GT 监督选择器，直接用 TTA / 邻域一致性作选择分数；**fully GT-free 但较弱**（如 leave-detector 中 standalone proxy NRC 多在 0.53–0.82，弱于 source-supervised 的 0.37–0.59）。

明确：**source-supervised transfer 是主 deployable candidate；fully GT-free proxy 是弱但更干净的部署变体。**

## 8. 实验结果

### 表 1：数据集与检测器覆盖（23 real cells / 6 datasets）
| dataset | #det | detectors | scope |
|---|---|---|---|
| DOTA-v1.0 | 6 | orcnn, psc, rtmdet, lsknet, strip, rhino(+h2rbox) | formal-compatible |
| DOTA-v1.5 | 4 | orcnn, rtmdet-s, rtmdet-m, o2-rtdetr | formal-compatible |
| DIOR-R | 6 | orcnn, psc, rtmdet, lsknet, ars_detr, strip | exploratory |
| FAIR1M-v1.0 | 3 | orcnn, psc, lsknet | exploratory |
| SODA-A | 3 | orcnn, psc, lsknet | exploratory |
| HRSC2016 | 1 | lsknet | exploratory |

*分析*：覆盖 6 数据集多检测器原型。*不能支持*：full 9-detector matrix complete；非 DOTA formal。

### 表 2：NRC 与 mAP 构造效度（n=23）
| 量 | 值 | 95% CI |
|---|---|---|
| Spearman(NRC, mAP) | −0.046 | [−0.49, 0.48] |
| partial(NRC,mAP \| dataset+family) | −0.005 | — |
| Spearman(NRC, median err) | 0.40 | — |
| mean rank distance | 7.83/23 | — |

*分析*：未检出显著相关 → NRC 提供 mAP 之外信号。*不能支持*：NRC strictly independent。

### 表 3：reliability cliff / tail risk（角度误差 p99，°）
| 分组 | p99 |
|---|---|
| masked（well-defined） | 10–26 |
| unmasked（含 near-square） | 88–90 |
| 按 ar：>2 / 1.6–2 / <1.3 | ~8–10 / ~11–45 / ~84–90 |

*分析*：reliability 随 ar→1 断崖。*不能支持*：unmasked 90° = detector catastrophic failure。

### 表 4：PSC preflight（detection-score）与 Track A（phase_mod），masked，NRC
| cell | detection-score NRC (CI) | phase_mod NRC (CI) |
|---|---|---|
| DOTA #20 | 0.840 [0.79,0.90] | （未跑，negative control） |
| DIOR #22 | 0.549 [0.53,0.57] | 1.156 [1.11,1.19] |
| FAIR1M #24 | 1.083 [1.03,1.13] | 1.121 [1.08,1.16] |
| SODA #23 | 1.260 [1.24,1.28] | 1.117 [1.11,1.13] |

*分析*：detection-score 在 FAIR1M/SODA 显著反校准；phase_mod 在 3/3 PSC cell 显著 >1 → 机制候选。*不能支持*：PSC angle head finally proven broken；DOTA #20 validation。

### 表 5：G2_double_prime（固定 size-bin，nonlinear vs score+ar+size linear）
| 阈值 | 显著 (cell×bin ΔNRC CI>0) |
|---|---|
| primary ar≥1.6 | 21/21 |
| sens ar≥1.3 / ar≥2.0 | 20/21 / 21/21 |

*分析*：增益非 box-size 先验。*不能支持*：deployable final method。

### 表 6：Deployable hardening（非 DOTA，无目标 GT）
| 指标 | 值 |
|---|---|
| 非 DOTA beat size-linear | 12/12 |
| retained oracle gain（非 DOTA 均值） | 0.645 |
| 失败 | DOTA #20（limitation） |

*分析*：source-supervised transfer 在未见单元多数优于基线。*不能支持*：full deployability。

### 表 7：Route-C real TTA（within-cell calibration 口径，NRC）
| cell | size-lin | geometry | real-TTA |
|---|---|---|---|
| DIOR ORCNN #3 | 0.638 | 0.438 | 0.391 |
| SODA PSC #23 | 0.611 | 0.389 | 0.378 |
| FAIR1M PSC #24 | 0.758 | 0.519 | 0.499 |
| DIOR RTMDet #61 | 0.501 | 0.339 | 0.331 |
| FAIR1M ORCNN #5 | 0.661 | 0.567 | 0.537 |

*分析*：real TTA 一致性多数优于 geometry-only。*不能支持*：deployable（此为 within-cell calibration，非 leave-\*）。

### 表 8：non-PSC leave-\*（source-supervised + target GT-free，NRC）
| 设置 | target | family | size-lin | source-sup | beat |
|---|---|---|---|---|---|
| leave-detector | DIOR #61 | RTMDet | 0.659 | 0.699 | ✗ |
| leave-detector | DIOR #3 | ORCNN | 0.701 | 0.379 | ✓ |
| leave-detector | SODA #4 | ORCNN | 0.582 | 0.380 | ✓ |
| leave-detector | FAIR1M #5 | ORCNN | 0.663 | 0.581 | ✓ |
| leave-detector | DIOR #10 | LSKNet | 0.670 | 0.367 | ✓ |
| leave-detector | SODA #11 | LSKNet | 0.563 | 0.379 | ✓ |
| leave-detector | FAIR1M #12 | LSKNet | 0.679 | 0.589 | ✓ |
| leave-dataset | FAIR1M #5 | ORCNN | 0.664 | 0.588 | ✓ |
| leave-dataset | FAIR1M #12 | LSKNet | 0.680 | 0.596 | ✓ |

*分析*：8/9 优于 size-linear；2 非 PSC family × 3 dataset。*不能支持*：所有 family（RTMDet 失败）；leave-dataset 全覆盖（SODA/DIOR folds 因计算成本未完成）。

### 表 9：Supervision spectrum 对比（典型 NRC 量级）
| 档 | 训练 | 目标 GT | 典型 NRC | 定位 |
|---|---|---|---|---|
| upper-bound | 本 cell D_cal GT | 用（同 cell） | ~0.36–0.52 | calibration（非 deployable） |
| source-supervised | 源 GT | 不用 | ~0.37–0.59 | 主 deployable candidate |
| fully GT-free proxy | 不训练 | 不用 | ~0.53–0.82 | 弱但更干净 |

*分析*：source-supervised 最强且可部署；proxy 较弱但 fully GT-free。*不能支持*：proxy = source-supervised；source-supervised = fully GT-free。

### 表 10：blockers / limitations
| item | status |
|---|---|
| real TTA 覆盖 | limited（6 cells/3 datasets/3 families） |
| Track A | mechanism candidate（非定论） |
| P3 selector | deployable candidate（非 final method） |
| DOTA #20 | weak-structure limitation（非 validation） |
| RTMDet leave-detector | failure（documented） |
| leave-dataset SODA/DIOR folds | compute-cost incomplete（next-step） |
| point2rbox | upstream artifact unavailable |
| ARS-DETR/Strip 部分 | class-mapping / coverage blocker |
| P2/C1 | appendix / negative result |

## 9. 图表占位（不画图）

- **Fig.1 Orientation reliability problem overview** — 图注：mAP 不刻画角度可信度，引出 measure→diagnose→fix。数据：概念图。支持：问题动机。不支持：定量结论。
- **Fig.2 Aspect-ratio reliability cliff** — 图注：p99/NRC 随 aspect-ratio。数据：`outputs/bench_core/reports/fig1_reliability_cliff_data.csv`。支持：cliff 真实。不支持：catastrophic failure。
- **Fig.3 Masked/unmasked angle-error CDF** — 数据：`fig2_angle_error_cdf_data.csv`。支持：90° 尾来自 near-square。不支持：well-defined catastrophic。
- **Fig.4 PSC NRC + CI** — 数据：`fig3_psc_nrc_ci_data.csv`。支持：FAIR1M/SODA 反校准。不支持：DOTA 反校准。
- **Fig.5 G2_double_prime size-bin** — 数据：`measure_fix_v2/reports/fig_g2doubleprime_size_control.csv`。支持：非 size prior。不支持：deployable final。
- **Fig.6 Deployable leave-dataset/leave-detector** — 数据：`fig_deployable_leave_dataset_detector.csv` + `nonpsc_deployable_leave_star_047.csv`。支持：多数 unseen 优于基线。不支持：DOTA/RTMDet/全覆盖。
- **Fig.7 Route-C real TTA** — 数据：`fig_route_c_real_tta.csv` + `real_tta_coverage_044.csv` + `real_tta_nonpsc_046.csv`。支持：real TTA 一致性增益。不支持：full coverage。
- **Fig.8 Track A phase_mod mechanism candidate** — 数据：`track_abc_results_043.csv`。支持：intrinsic 反校准候选。不支持：最终机制证明。
- **Fig.9 Supervision spectrum** — 数据：表 9 + 各 leave-\*/coverage csv。支持：监督预算-性能权衡。不支持：proxy=source-supervised。

## 10. 讨论

**为何不大规模 GPU 训练**：研究对象是可靠性的测量/诊断/选择；重训会混淆变量；已有 checkpoint 足以产生分析对象；GPU 仅用于 inference / TTA / forward dump。**为何不追 DOTA public mAP**：DOTA 自跑 train/val，命题与精度排名无关。**为何不补 full matrix**：贡献是问题定义与机制，而非矩阵全面性。**为何 P2/C1 降为附录**：OT-dustbin 未明确打赢 GT-identity，作为负结果/消融。**为何 P3 是 deployable candidate**：selector 训练仍用 source GT（calibration / transfer），fully GT-free proxy 较弱；故不是 final method。**DOTA #20**：detection-score 已较良校准时 selector 边际收益小（applicability boundary）。**RTMDet failure / compute limitation**：RTMDet/DIOR 几何-可靠性关系不同导致迁移失败；leave-dataset SODA/DIOR folds 因大单元 bootstrap 计算成本未完成。**near-square 的角色**：既是 90° 尾部主因，也是任务核心难点，须以 aspect-ratio 曲线显式处理。**coverage limitation**：real TTA 与 leave-\* 仍未覆盖全部 family×dataset。

## 11. 局限性

- full project incomplete；非 DOTA 为 exploratory（未冻结阈值）。
- real TTA coverage 有限（6 cells / 3 datasets / 3 families）。
- Track A 为 mechanism candidate（phase_mod 一信号，非定论）。
- P3 final method incomplete（selector 为 deployable candidate）。
- point2rbox upstream artifact unavailable；ARS-DETR / Strip 部分 blocker。
- P2/C1 非主线（附录/负结果）。
- **source-supervised transfer 不是 fully GT-free**（selector 权重来自 source GT）。
- fully GT-free proxy 较弱。

## 12. 结论

本文提出朝向可靠性的测量、诊断与选择框架：证明在精度之外存在可测的 angle reliability signal；发现 aspect-ratio reliability cliff 与 PSC 的 score-level / phase_mod 机制候选；并验证 geometry-aware selector 与 supervision spectrum 在当前证据下具有价值（固定 size-bin 内优于线性基线、非 PSC 跨数据集 leave-\* 多数优于强基线、fully GT-free proxy 作为弱替代）。最终方法与更大范围部署验证、机制确认仍需后续工作。

---

## 附录

**A. 数据集与 detector 细节**：见 §4 表 1 与 `outputs/bench_core/reports/final_coverage_matrix.csv`。
**B. D_cal / D_audit split**：确定性 md5(image_id) 互斥划分（冻结，`orientbench/data/splits.py`）。
**C. metric 定义**：NRC-AUC / AURC / Risk@k / canonical long-side angle error / near-square（§3）。
**D. persistent artifact manifest**：`outputs/persistent_artifacts/manifest_047.json`（43 artifacts / 1361 MB，path/sha256/schema/generation_command/can_recompute/source_checkpoint/split；大文件不入 git）。
**E. claim ledger**：`measure_fix_v2/docs/claim_ledger_measure_fix_v1.md`（allowed / qualified / forbidden / pending）。
**F. forbidden claims**：full project complete、P3 final method complete、NRC strictly independent、PSC angle head finally proven broken、DOTA #20 validation、source-supervised = fully GT-free、会议级就绪话术。
**G. reproducibility checklist**：envs / adapters / metrics 脚本 / thresholds sha256 / split 冻结（`final_reproducibility_guide.md`）。
**H. P2/C1 appendix / negative result**：C1 augmentation-view（非 genuine 多视角）、A4 same-host（非跨 host 因果）、OT-dustbin 未打赢 GT-identity。
**I. route status**：`measure_fix_v2/docs/measure_fix_route_status.md`。
**J. license / governance notes**：第三方库与数据集遵循各自 license；原始 dataset 未修改；shadow farm 仅 symlink + 生成 annfile 于 scratch。

---

## 合作者审稿重点

1. **科学主线是否成立**：measure（NRC≠mAP 信号）→ diagnose（cliff + PSC 双重反校准候选）→ fix（geometry selector 非 size prior + 监督光谱）。请审证据链是否自洽、克制。
2. **supervision spectrum 是否清晰**：upper-bound / source-supervised / fully GT-free 三档定位与典型量级（表 9）是否准确传达"监督预算-性能"权衡。
3. **Route-C 口径是否准确**：source-supervised + target GT-free inference（非 fully GT-free）；请确认全文无"fully GT-free selector"误述。
4. **non-PSC leave-\* 是否足够**：8/9、2 family × 3 dataset；RTMDet 失败与 leave-dataset 未完成 folds 是否需补全。
5. **是否还需要补图**：Fig.1–9 占位是否覆盖核心论点；是否需 reliability curve / supervision-spectrum 主图。
6. **是否可进入英文稿**：结构、数据、口径是否已稳定到可英译。
7. **哪些 claim 必须删改**：核对附录 F forbidden claims 是否在正文有任何残留；DOTA #20 是否一处不漏地写为 limitation。
