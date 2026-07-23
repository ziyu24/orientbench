# 朝向可靠性的测量协议与有限样本保形朝向风险控制

## 摘要

旋转目标检测（oriented object detection, OBB）以 (cx,cy,w,h,θ) 表征目标，其中朝向 θ 是关键几何量。然而，主流评价以 mAP@0.5 为核心，学界已有定性认识：AP@0.5 在一定条件下对朝向错误不够敏感。本文对这一现象作系统的形式化、几何化与协议化，并在此基础上建立朝向可靠性的测量与风险控制框架。我们的工作包括四部分。第一，用完整评测器（旋转多边形 IoU、逐类贪心匹配、全点插值 AP）在六个来源可信、可完整复算的验证单元（三检测族×三数据集）上，对匹配预测注入受几何约束的最大朝向扰动：真实 AP@0.5 完全不变（ΔAP@0.5=0.0000），而 AP@0.75 大幅塌陷、逐实例朝向误差由约 5–9° 升至约 34–41°；配合固定角度、扰动中心/尺度使 AP@0.5 显著下降的反向实验，双向地表明 mAP 与朝向可靠性并不等价。第二，我们给出角度可辨识性随长宽比退化的几何原则，并据此原则化地推导主分析区域：在 IoU 阈值 0.75 下以 15° 朝向容差为工程语义，得到长宽比阈值约 ar≥2.1 作为良态区，长宽比 ar≥1.6、ar≥1.3 作为敏感性区。第三，我们提出以归一化风险-覆盖曲线面积（NRC-AUC）度量朝向排序质量，并建立作用于任意选择打分之上的有限样本保形朝向风险控制层（以完整图像为可交换单元的固定序列 Learn-Then-Test 与 Hoeffding-Bentkus 有界损失上界；精确二项只用于次级图像事件，实例加权风险仅配图像级聚类自助区间）。第四，我们给出一个在充分收敛、跨两数据集、跨三随机种子下可复现的、相位编码器（PSC）内在角度置信度反序排序的机制候选，同时以稠密编码（DCL）内在置信度的有信息（informative）反例说明该现象并非角度编码器的普遍性质。我们如实界定边界：几何感知打分为诊断性候选而非通用默认；由于标注噪声地板的存在，度级均值风险须作 label-noise-aware 解读；保形保证在实用预算下受限、跨域无严格保证；机制结论仅为受限的、相位编码器特定的候选证据。本文不是全面基准，亦不主张可直接部署的方法。

**关键词**：旋转目标检测；朝向可靠性；选择性预测；风险-覆盖；保形风险控制；角度编码器；标注噪声

---

## 1 引言

旋转框检测在遥感、场景文本、工业视觉等场景中广泛使用，朝向 θ 决定了目标的方位刻画。实践与评价却主要围绕 mAP@0.5：一个在 IoU=0.5 判定框匹配、对每类作全点插值的检测精度指标。已有工作（如对角度敏感 DETR 的讨论）定性指出 AP@0.5 对朝向错误的敏感性有限，但缺乏一个把"何时、何种几何条件下 mAP 对朝向弱敏感"讲清楚的形式化协议，也缺乏一个能对朝向可靠性给出有限样本保证的风险控制框架。

本文围绕"测量—诊断—约束"展开。我们不追求刷新公开 mAP，也不构造全面检测器基准，而是回答三个问题：(i) 在真实完整评测器下，mAP 与朝向可靠性在什么几何条件下分离？(ii) 如何在原则化的良态区内度量一个检测器的朝向排序质量，并给出有限样本的尾部风险约束？(iii) 检测器的哪些内在信号能可靠地排序朝向风险？

**贡献。** 本文的定位不是"首次发现 mAP 盲区"，而是：

1. **形式化与几何化**：把 AP@0.5 对朝向弱敏感的定性认识形式化为"AP@τ 的角度容忍宽度 = 使旋转框 IoU 跌破 τ 所需的角度"，并由长宽比与 IoU 阈值共同决定；据此给出一个原则化的 masked 良态区（IoU 0.75、15° 容差下 ar≥2.1）。
2. **双向分离的真实证据**：用完整评测器（非"仅取匹配对"的代理）在六个真实单元上量化 AP@0.5、AP@0.75 与朝向误差在受约束角度扰动下的分离，并以反向扰动补齐另一半，共同确立 mAP 与朝向可靠性的不等价。
3. **朝向可靠性测量协议**：以 NRC-AUC / 风险-覆盖 / 分位风险刻画朝向排序质量，统一 masked 主口径与分层评估。
4. **有限样本保形朝向风险控制**：建立作用于已选打分之上的保证层，给出尾部风险控制与打分菜单在同一保证下的可达覆盖，并如实报告其在实用预算下的受限性与跨域退化。
5. **相位编码器机制候选**：在充分收敛、跨数据集、跨随机种子下给出相位编码器内在置信度反序的可复现证据，并以稠密编码的 informative 反例明确其非普遍性。

我们全程坚持保守表述：不写"mAP 完全看不见角度"，不写"NRC 与 mAP 严格独立"，不写"角度编码器置信度普遍失效"，不写"几何感知打分是通用默认"，不写跨域严格保证。

---

## 2 相关工作

**选择性预测与风险-覆盖。** 带拒识选项的选择性预测与其风险-覆盖权衡由 El-Yaniv 与 Wiener、Geifman 与 El-Yaniv 等奠基；SelectiveNet 将其嵌入训练。本文借用风险-覆盖思想度量朝向排序质量，但对象是几何朝向误差而非分类风险。

**保形预测与风险控制。** 保形预测提供分布无关的有限样本覆盖保证；Conformal Risk Control、Risk-Controlling Prediction Sets（RCPS）与 Learn-Then-Test（固定序列多重检验）把保证从覆盖推广到一般单调风险。协变量漂移与自适应保形处理分布变化，Mondrian 保形处理条件有效性。我们把这些工具用于朝向风险的尾部控制，并明确其在跨数据集迁移下只作经验评估。

**检测器校准。** 现代网络的概率校准与目标检测的多元置信度校准（D-ECE）刻画置信度与正确率的偏差。本文关注的是朝向排序质量与角度分支的内在置信度，与分类置信度校准互补而不等同；我们据此严格区分"NRC<1（非反序、有信息）"与"概率校准（calibrated）"两个概念。

**角度表示与旋转检测损失。** 角度周期性与近方形/方形样本问题催生了多种角度表示：圆滑标签（CSL）、稠密编码标签（DCL）、相位编码（PSC）等把角度回归转化为可解码的中间表示；分布感知损失如 Gaussian Wasserstein Distance（GWD）、Kullback–Leibler Distance（KLD）从优化侧按目标形状调整角度重要性；RSDet、Gliding Vertex 等处理角点表示的边界不连续。本文从评价/可靠性侧给出与之呼应的几何原则，并以角度编码器的内在置信度作机制分析对象。

**测试时增强与不确定性。** 测试时增强（TTA）不确定性与 MC-dropout 是常见的免真值不确定性来源。我们采用 TTA 圆周方差作为一种朝向不确定性基线，并对周期角度统一使用 θ→2θ 圆统计。

**检测器与数据集。** 我们的验证单元覆盖 Oriented R-CNN、Rotated RTMDet、相位编码 RetinaNet 三个检测族与 DIOR-R、FAIR1M、SODA-A、DOTA 等旋转数据集。旋转数据集采用自跑 train/val 协议，不引用官方 trainval/test 数字。

---

## 3 问题定义与朝向可靠性测量协议

**OBB 与朝向误差。** 目标以 (cx,cy,w,h,θ) 表示，采用 canonical 长边约定：长边朝向为 θ（当 w≥h）或 θ+90°（当 w<h）。两框朝向误差定义为长边朝向之差在 π 周期下的最小绝对值，归一化到 [0°,90°]。该定义对 (w,h) 互换对称，避免 90° 伪误差；所有周期角度统计（如 TTA 圆周方差）均在 θ→2θ 圆域内计算。

**长宽比、近方形与几何朝向可辨识性（GV-obliquity）。** 记长宽比 ar=max(w,h)/min(w,h)。当 ar→1（近方形）时，绕中心旋转几乎不改变框，朝向在 IoU 与几何上病态、不可辨识。我们以"几何朝向可辨识度"（geometric-view obliquity, GV-obliquity）刻画一个目标形状对朝向错误的几何敏感程度：定义 δθ_τ(ar) 为使面积归一的共中心矩形绕中心旋转后 IoU 跌破阈值 τ 所需的最小角度，则 GV-obliquity 随 ar 增大而增强（δθ_τ 减小、朝向更易辨识），随 ar→1 而消失（δθ_τ→∞，即近方形在任意 τ 下都难以由 IoU 惩罚朝向）。GV-obliquity 用于三处：(i) 定义 masked 良态区的阈值；(ii) 解释 AP@τ 的朝向容忍宽度；(iii) 作为按长宽比分层评估的依据。它与长宽比单调相关、与"退化/近方形"是同一几何现象的两端，与检测器行为无关。

**masked 良态区（主口径 ar≥2.1）。** 我们不在近方形样本上作朝向可靠性推断。主分析区域取剔除近方形后的 masked 良态区 ar≥2.1（其原则化推导见第 4 节），以 ar≥1.6、ar≥1.3 作敏感性区；未剔除口径仅作对照，不作可靠性结论。

**风险-覆盖与 NRC-AUC。** 给定选择打分 s（越大越先保留）与朝向风险 r（角度误差）。按 s 降序保留 top-k（覆盖 c=k/n），选择性风险为所保留样本平均 r；AURC 为各覆盖选择性风险的平均；Risk@70/90 为覆盖 0.7/0.9 处的选择性风险。归一化风险-覆盖曲线面积为

$$\mathrm{NRC\text{-}AUC}=\frac{\mathrm{AURC}_{\text{model}}-\mathrm{AURC}_{\text{oracle}}}{\mathrm{AURC}_{\text{random}}-\mathrm{AURC}_{\text{oracle}}}.$$

**方向约定（全文一致）**：NRC=0 为 oracle 排序；NRC=1 等价随机排序；NRC>1 为反序（reverse ranking，高打分对应更差朝向）；NRC<1 表示优于随机 / 非反序 / 有信息（informative）。我们不以"校准（calibrated）"描述 NRC<1；"calibrated"仅保留给概率校准或保形语境。

**标定与审计划分。** 每个单元依图像标识作确定性互斥划分，得标定集与审计集；为使保形保证有效，标定集进一步不相交地再分为选择器拟合子集与保形标定子集，审计集仅用于最终报告。该划分一经确定即冻结，全文不变；拟合、标定、审计三者互斥，避免选择器拟合数据与保形标定数据泄漏。

**保形层的定位。** 保形层是风险保证层，而非新的选择打分：给定任意打分 s 与风险预算 α，在标定数据上确定阈值使保留集风险受控，在审计集验证经验覆盖、风险与违例，并给出有限样本界。有限样本界依赖标定口径与损失有界性；跨数据集/分布漂移仅作经验评估，不写严格保证。

---

## 4 几何原则与 masked 良态区

**几何命题（含数值验证）。** 考察面积归一的共中心矩形绕中心旋转 δθ 后的 IoU(δθ; ar)。**命题**：IoU 对 δθ 的敏感性随 ar 单调变化——ar→1 时退化（数值上 ar=1.0 的 IoU 在任意 δθ 下都不低于约 0.707，永不跌破 0.5，即近方形朝向在 IoU 上不可辨识）；ar 增大时使 IoU 跌破 τ 的 δθ_τ(ar) 随之减小。若"角度可辨识性随 ar→1 退化"的 Fisher 信息式严格推导条件不足，本文仅作 remark 而不写定理。

**数值曲线与 AP 盲区的统一解释。** 由 IoU(δθ; ar) 得到 δθ_τ(ar)（表 1）。据此，AP@τ 对朝向的容忍宽度恰为 {δθ: IoU>τ} 的宽度，由 ar 与 τ 共同决定：在 τ=0.5 下即使细长目标也允许可观的角度偏移，故 AP@0.5 对朝向弱敏感；在 τ=0.75 下容忍宽度显著收窄，故 AP@0.75 对朝向敏感。这与第 5 节的经验约束扰动上限（近方形≈68°、细长≈33°、极细长≈15–18°）一致，并统一解释了 mAP 盲区、近方形可靠性悬崖、masked 主口径与按 ar 分层。分布感知损失（如 KLD）已从优化侧按目标形状调整角度重要性，与本文从评价侧的几何原则互为印证。

**表 1. IoU-角度几何敏感性与角度容忍宽度 δθ_τ(ar)**

| 长宽比 ar | δθ 使 IoU 跌破 0.5（°） | δθ 使 IoU 跌破 0.75（°） |
|---|---|---|
| 1.0 | 永不跌破 | 25.5285 |
| 1.3 | 永不跌破 | 23.1417 |
| 1.6 | 69.6358 | 19.6727 |
| 2.0 | 47.4084 | 16.0548 |
| 2.5 | 34.5475 | 12.9594 |
| 4.0 | 19.9234 | 8.1577 |
| 8.0 | 9.6457 | 4.0893 |

**主口径的原则化推导（ar≥2.1）。** 我们以工程语义确定 masked 主口径：取 IoU 阈值 τ=0.75，要求 15° 的朝向偏差应当"几何上有后果"（即足以把 IoU 压到 0.75 以下）。由表 1 在 τ=0.75 下对 δθ_0.75(ar) 反解 δθ=15°：ar=2.0 对应 16.0°、ar=2.5 对应 12.5°，按冻结数值求解得到精确交叉点 **ar=2.15**，报告主阈值取 **ar≈2.1**。故取 ar≥2.1 为原则化良态主分析区——在该区内一个 15° 的朝向错误在 IoU 0.75 下是几何上可辨识、有后果的；ar≥1.6、ar≥1.3 作为敏感性区。此举取代此前把 ar≥1.6 直接当作唯一主口径的做法。

**各数据集的保留比例（表 2）。** 采用 ar≥2.1 主口径后，各数据集约保留 55%–62% 的良态目标，其余为近方形或次良态。近方形（ar<1.6）在 DIOR-R 占比最高（约 33%），FAIR1M、SODA-A 较低（约 12%–13%）。近方形区正是朝向标注最不稳定、朝向可靠性推断最不可靠之处（见第 9 节），故不进入主分析。

**表 2. masked 口径的保留比例（真值目标数为基）**

| 数据集 | 真值目标数 | 近方形 ar<1.6 占比 | 保留 ar≥1.3 | 保留 ar≥1.6 | 保留 ar≥2.1（主口径） |
|---|---|---|---|---|---|
| DIOR-R | 124445 | 0.328 | 0.741 | 0.672 | 0.550 |
| FAIR1M | 78644 | 0.133 | 0.911 | 0.867 | 0.624 |
| SODA-A | 449644 | 0.116 | 0.921 | 0.884 | 0.612 |

**近方形可靠性悬崖。** 在冻结 masked 口径下，良态实例的角度误差分位偏低（90 分位度级、99 分位十度级）；随 ar→1 病态，分位跃升至约 88–90°。悬崖现象是采用 masked 主口径与按 ar 分层保形的直接动因。

---

## 5 主结果一：mAP 与朝向可靠性的双向分离

**实验设计（正向，完整评测器）。** 从原始预测（分数、类别、NMS 后集合）与完整验证集真值出发，用完整评测器（每类按分数降序贪心匹配、IoU 判定 TP/FP、全点插值求 AP）得到真实 AP@0.5/AP@0.75 与假阳性数。随后仅对匹配到真值的预测注入其逐实例最大约束扰动：沿远离真值的方向旋转、并保持与所匹配真值的旋转 IoU>0.5（扰动绕预测框自身中心进行）；未匹配预测与假阳性原样保留，分数与类别不变。再次用完整评测器**重新匹配**并重算全部指标。全程不使用"仅取匹配对"的代理，故不会出现代理式 AP@0.5=1.0 的假象。

**结果（表 3）。** 六个真实单元、跨三检测族、三数据集：约束扰动下真实 **AP@0.5 完全不变（ΔAP@0.5=0.0000）、假阳性数不变**（无重复匹配、无新增假阳性），而 **AP@0.75 大幅塌陷、朝向误差由约 5–9° 升至约 34–41°**。六单元真实 AP@0.5 与各检测器自评量级一致（评测器为旋转多边形 IoU + VOC 全点插值、逐类宏平均，其数值与各检测器自评、与参考实现的 DOTA 度量三方对齐，最大差异约 1.3e-3），佐证评测器正确、结果非人为。

**表 3. 完整评测器下约束角度扰动的 AP 与朝向风险（真实 AP，非代理）**

| 单元 | 数据集 / 检测族 | 真实 AP@0.5 | 扰动 AP@0.5 | ΔAP@0.5 | AP@0.75 | 扰动 AP@0.75 | 朝向误差°（原→扰动） |
|---|---|---|---|---|---|---|---|
| A | DIOR-R / 相位编码 RetinaNet | 0.5368 | 0.5368 | 0.0000 | 0.350 | 0.038 | 8.95→39.19 |
| B | DIOR-R / Oriented R-CNN | 0.6448 | 0.6448 | 0.0000 | 0.428 | 0.048 | 8.67→40.04 |
| C | DIOR-R / Rotated RTMDet | 0.6462 | 0.6462 | 0.0000 | 0.452 | 0.053 | 9.09→40.54 |
| D | FAIR1M / 相位编码 RetinaNet | 0.3462 | 0.3462 | 0.0000 | 0.242 | 0.067 | 4.63→36.52 |
| E | SODA-A / 相位编码 RetinaNet | 0.5991 | 0.5991 | 0.0000 | 0.274 | 0.045 | 5.23→34.42 |
| F | SODA-A / Oriented R-CNN | 0.7295 | 0.7295 | 0.0000 | 0.381 | 0.028 | 5.15→35.89 |

> 六单元均以完整验证集真值与统一评测器重算；真实 AP@0.5 与各检测器自评量级吻合。约束扰动保持 rIoU>0.5，故 TP/FP@0.5 集合不变、假阳性数不变、ΔAP@0.5=0.0000；AP@0.75 与朝向误差同时大幅变化。

**几何门控。** 按长宽比分层，逐实例可注入的约束扰动上限随 ar 增大而减小（近方形约 68°、细长约 33°、极细长约 15–18°，与表 1 的 δθ_0.5(ar) 一致）；但每一层的 ΔAP@0.5 仍为 0，朝向误差在每层都大幅上升。

**反向分离（另一半）。** 固定角度、扰动中心/尺度：AP@0.5 可显著下降（例如某单元中心平移 0.2√面积时 AP@0.5 由 0.80 降至 0.57、另一单元由 0.70 降至 0.52，角度全程不变；尺度缩 15% 时由 0.80 降至 0.76）。即 mAP 可在角度不变时改变。正反两向共同表明 mAP 与朝向可靠性互不等价。

**结论与边界。** 在真实完整评测器下，AP@0.5 对特定几何区（受 ar 与 IoU 阈值门控）的朝向错误结构性弱敏感，而 AP@0.75 与朝向风险敏感。这不是"mAP 完全看不见角度"，而是"在特定几何区与阈值下 mAP@0.5 对朝向弱敏感"；也不意味着 NRC 与 mAP 严格独立，只表明二者不等价。

---

## 6 主结果二：ar≥2.1 朝向排序与尺度混淆裁决

**统一主口径。** 所有正式 NRC、AURC、Risk@70、Risk@90、检测打分、TTA 圆周方差、PSC 相位模长、CSL margin、DCL bit margin，以及两个 DOTA clean full-val 单元，统一使用 matched-GT `ar≥2.1` 且排除预测框或真值框近方形不稳定性的主掩码。旧 `ar≥1.6` 与 `ar≥1.3` 只保留为 sensitivity，不能再进入主表。A--F 的正式统计在冻结 `D_audit` 上完成；K2 端点明确标记为冻结 full-validation endpoint，二者不混称同一 split。

**G2_double_prime 尺度控制。** M2 在冻结的预测框面积分箱（small、medium、large）内，比较 detection score、score+log(predicted ar) 线性、score+log(predicted ar)+log(predicted size) 线性与 nonlinear geometry-aware score；选择器只用预测框几何，在 `D_cal-fit` 拟合，在 `D_audit` 评估，并以图像簇 bootstrap 比较。最终裁决为 **PASS**：A、B、C、E 四个单元提供跨尺寸支持，15 个可用 cell-size bin 中 11 个显示 nonlinear 相对 score+ar+size linear 的稳定优势。该结果排除了固定尺寸分箱内增益完全消失的早停情形，但不等于已经通过跨数据集或跨检测器的可部署性门控。

**几何打分的最终位置。** geometry score 的拟合目标是目标域真值角度误差，只能作为 calibration / upper-bound 分析。尽管 M2 通过尺度混淆门控，它仍整体置于附录，不是主方法、不是 deployable selector；只有后续独立的 Deployable 门控通过后，才允许提升相应方法主张。其数值与固定 size-bin 裁决由最终 M1/M2 表追踪。

**DOTA 边界。** DOTA 只保留 Oriented R-CNN 与 Rotated RTMDet-M 两个 clean full-val 单元；AP50/AP75 与 ar≥2.1 reliability 从持久化 full-val artifact 复算。DOTA#20 被明确排除，不进入任何正式结果。

---

## 7 以完整图像为单位的有限样本风险控制

**正式风险事件。** 主事件冻结为
`angle_error_le90 > delta_theta_0.75(matched_GT_aspect_ratio)`，
其中 `delta_theta_0.75(ar)` 来自共中心、同尺度、全等矩形的第一严格交叉，le90 长边朝向按 pi 周期处理，数值求解精度为 0.001 度。主口径为 ar≥2.1。固定 `>5°`、`>10°`、`>15°` 只作 sensitivity；5° 是 fine-risk，FAIR1M 与 SODA-A 均作 noise-sensitive 解读。

**图像级主损失。** 正式 exchangeable unit 是完整 evaluation image。对阈值 t，令
`L_I(t)` 为图像 I 中保留且可匹配预测的 severe orientation event 比例；若图像无保留预测则 `L_I(t)=0`。外层冻结 `D_cal` 被确定性拆为互斥的 `D_cal-fit` 与 `D_cal-calib`：前者只生成阈值序列，后者只执行固定序列 Learn-Then-Test；`D_audit` 只报告。主 bounded loss 使用 Hoeffding-Bentkus 单侧 UCB，不对 `L_I` 使用精确二项。

**次级与经验端点。** `Z_I(t)=1` 表示图像至少含一个保留 severe prediction；这是二元次级事件，允许使用 exact binomial / 精确二项 Clopper-Pearson 上界。实例加权尾率只写作 empirical instance-weighted risk with image-cluster bootstrap CI，不构成正式有限样本保证。旧 instance-i.i.d. exact-binomial 结果仅是无效独立性反事实对照。

正式表同时报告 mean image-level risk、calibration UCB、nonempty-image proportion、mean instance coverage、total retained instances，以及 calibration/audit image counts。与旧 instance-i.i.d. 口径的阈值、覆盖和有效样本量差异单独列出，不选择性保留旧覆盖数字。

---

## 8 PSC Phase 1 机制分析与拆篇门控

PSC Phase 1 沿用原始开始时间 `2026-07-12 20:14:39 -0700` 与原始截止时间 `2026-08-23 20:14:39 -0700`，没有因接管而重置。径向干预为 `z'=kz`，覆盖 decoded angle、AP50/AP75、angle error、phase magnitude、configured head loss、radial/tangential gradient、box、class 与 post-NMS set。

六个 PSC 冻结单元的径向结果按预注册规则裁成 Branch A 或 Branch B；Branch A 仅表示解码径向不变且配置损失对径向弱约束，Branch B 仅在解码敏感或 configured loss 赋予稳定模长语义时成立。最终分支、结构解释和证据由 `psc_phase1_branch_decision.csv` 逐单元及总体记录。

新机制分数必须同时满足：不是 `negative phase_mod` 的取负或简单单调变换；在 DIOR-R 与 SODA-A 的冻结可用单元上，NRC/AURC/Risk@70/Risk@90 均以图像级 bootstrap 区间稳定优于 `negative phase_mod`；不重训 detector，且 box/class/AP 不变。最终拆篇门控为 **PASS**：径向干预给出可干预的 Branch B 结构性原因；`tta_phase_direction_consistency`、`multi_frequency_consistency`、`unwrap_candidate_energy_gap` 与 `phase_direction_margin` 均通过冻结的非平凡性及双数据集比较，其中 TTA 分数按预注册只覆盖 seed0，其余覆盖三种子。该门控只支持 PSC-specific 机制线独立成篇，不把结果外推为通用 angle-coder failure；PSC phase_mod 仍写作反序，DCL native signal informative，CSL 近随机。

---

## 9 标注噪声代理与人工双标锚点

K3 角点抖动结果始终称为 GT corner-jitter proxy：它只描述标注对小几何扰动的敏感性，不是真实人工方差，也不是真实双标差异。proxy 表与人工表严格分列，风险阈值不能由 proxy 反推。

DIOR-R、FAIR1M 与 SODA-A 的机器准备包各含 500 个 matched-GT 分层实例；私有 manifest 用 matched-GT 的非角度 class/size/ar 定义正式 strata 和 ar≥2.1 子集，预测框只用于 locator/crop。A/B 两套任务包含同一目标集合、不同随机顺序，独立互盲，任务 CSV 不暴露 GT/pred angle、OBB、score 或 strata。

当前没有两名真实、独立、互盲标注者的原始结果，因此人工端点为 **HUMAN_BLOCKED**。本文不以 GT 复制或单人重复伪造双标统计；投稿冻结保持 NOT_FROZEN，直至真实标签完成并通过独立性与最少样本门控。

---

## 10 Scope and Claims（边界）

**允许。** 朝向可靠性可被专门测量；mAP@0.5 对朝向错误存在由长宽比与 IoU 阈值门控的结构性弱敏感区；ar≥2.1 的 NRC / risk-coverage 提供准确率之外的 reliability signal；完整图像单位的 HB-LTT 可给出有限样本 bounded-loss 风险控制；PSC-specific phase_mod reverse-ranking 与 DCL informative 反例可以并列报告。

**须限定。** geometry score 是目标域真值拟合的上界且仅在附录；M2 通过固定尺寸门控，但尚未执行独立的 Deployable 门控，因而不能主张跨域可部署；实例风险只有图像簇 bootstrap 的经验区间；5° 在 FAIR1M/SODA-A 对标注噪声敏感；跨域没有严格保证；PSC Phase 1 的 PASS 只适用于冻结的 PSC-specific 机制与排序证据。

**不主张。** 全面检测器矩阵、项目完成、DOTA SOTA、可直接部署 selector、通用 angle-coder failure、PSC angle head 已被证明损坏、NRC 与 mAP 严格独立，或人工双标已经完成。

---

## 11 局限性

1. 主证据覆盖六个 A--F full-val reliability 单元与两个 DOTA clean full-val 单元，不是全面 detector matrix。
2. M2 PASS 排除了固定尺寸分箱内增益消失，但 geometry score 仍依赖目标域 GT-fit；在 Deployable 门控完成前，它只是 appendix upper-bound。
3. 图像级保证依赖冻结的图像划分与 bounded-loss 假设；审计风险不能反向参与阈值选择。
4. GT corner-jitter proxy 不能替代真实人工一致性；真实独立双标是当前唯一人工冻结 blocker。
5. PSC Phase 1 满足拆篇四条件，但证据仍限于 PSC、DIOR-R/SODA-A 与冻结种子，不能外推到通用 angle coder。

---

## 12 结论

本文以 ar≥2.1 为唯一主口径，把朝向可靠性统一为可测量的排序问题与完整图像单位的有限样本风险控制问题。K1 确立 mAP 与朝向误差的双向不等价；M2 通过固定尺寸尺度混淆门控，但 geometry score 因目标域 GT-fit 属性仍留在附录并等待独立 Deployable 门控；M3 以 `L_I` 和 Hoeffding-Bentkus LTT 取代旧 instance-i.i.d. 主保证；M4 冻结 geometry-normalized severe event 并保留 5°/10°/15° sensitivity。PSC Phase 1 的四条件门控通过，支持受限的 PSC-specific 机制线拆篇。论文协议的机器链已经可复算，但真实人工双标完成前，投稿状态仍为 NOT_FROZEN。

---

## 参考文献

（按作者、年份与预印本编号定位；精确书目字段以官方出处为准。）

1. El-Yaniv, Wiener. On the foundations of noise-free selective classification. 2010.
2. Geifman, El-Yaniv. Selective prediction with a reject option (SR / risk-coverage). 2017.
3. Geifman, El-Yaniv. SelectiveNet: a deep neural network with an integrated reject option. 2019.
4. Vovk, Gammerman, Shafer. Algorithmic Learning in a Random World. 2005.
5. Angelopoulos, Bates. A gentle introduction to conformal prediction and distribution-free uncertainty quantification. arXiv:2107.07511.
6. Angelopoulos, Bates, Fisch, Lei, Schuster, Jordan. Conformal Risk Control. arXiv:2208.02814.
7. Bates, Angelopoulos, Lei, Malik, Jordan. Distribution-free, risk-controlling prediction sets (RCPS). 2021.
8. Angelopoulos, Bates, Candès, Jordan, Lei. Learn-Then-Test: calibrating predictive algorithms to achieve risk control. arXiv:2110.01052.
9. Tibshirani, Barber, Candès, Ramdas. Conformal prediction under covariate shift. 2019.
10. Gibbs, Candès. Adaptive conformal inference under distribution shift. 2021.
11. Vovk, Lindsay, Nouretdinov, Gammerman. Mondrian confidence machines. 2003.
12. Küppers, Kronenberger, Shantia, Haselhoff. Multivariate confidence calibration for object detection (D-ECE). 2020.
13. Guo, Pleiss, Sun, Weinberger. On calibration of modern neural networks. 2017.
14. Yang, Yan. Arbitrary-oriented object detection with circular smooth label (CSL). 2020.
15. Yang, Yan, Feng, Yang. Dense label encoding for boundary discontinuity free rotation detection (DCL). 2021.
16. Yu, Da. Phase-shifting coder for oriented object detection (PSC). arXiv:2211.06368.
17. Yang, Yan, Ming, et al. Rethinking rotated object detection with Gaussian Wasserstein distance loss (GWD). 2021.
18. Yang, Yan, Qian, et al. Learning high-precision bounding box for rotated object detection via Kullback–Leibler divergence (KLD). arXiv:2106.01883.
19. Qian, Zhang, Yao, et al. Learning modulated loss for rotated object detection (RSDet). 2021.
20. Xu, Fu, Wu, et al. Gliding vertex on the horizontal bounding box for multi-oriented object detection. 2021.
21. Ayhan, Berens. Test-time data augmentation for estimating heteroscedastic aleatoric uncertainty. 2018.
22. Gal, Ghahramani. Dropout as a Bayesian approximation. 2016.
23. Xie, Cheng, Wang, Yao, Han. Oriented R-CNN for object detection. 2021.
24. Lyu, Zhang, Huang, et al. RTMDet: an empirical study of designing real-time object detectors. arXiv:2212.07784.
25. Li, Wang, Wang, Yang. Large selective kernel network for remote sensing object detection (LSKNet). 2023.
26. Zeng, Yang, Chen, et al. ARS-DETR: aspect ratio-sensitive detection transformer for oriented object detection. 2023.
27. Xia, Bai, Ding, et al. DOTA: a large-scale dataset for object detection in aerial images. 2018.
28. Cheng, Wang, Li, et al. Anchor-free oriented proposal generator / DIOR-R. 2022.
29. Sun, Zheng, Wang, et al. FAIR1M: a benchmark dataset for fine-grained object recognition in high-resolution remote sensing imagery. 2022.
30. Cheng, Yuan, Wu, et al. Towards large-scale small object detection (SODA-A). arXiv:2207.14096.
31. Liu, Yuan, Ni, et al. A high resolution optical satellite image dataset for ship recognition (HRSC2016). 2017.

---

## 附录

### 附录 A 数据、检测器与划分
主结果覆盖六个来源可信、可完整复算的完整验证单元（相位编码 RetinaNet、Oriented R-CNN、Rotated RTMDet 三检测族 × DIOR-R / FAIR1M / SODA-A 三数据集），并以 DOTA-v1.0 完整验证集上的 Oriented R-CNN、Rotated RTMDet-M 两单元作横向交叉验证。每单元的逐实例匹配表含分数、角度误差、长宽比、近方形标志、尺寸、标定/审计标志、来源检查点与配置引用，均为真实检测器前向 + 匹配产物。旋转数据集采用自跑 train/val 协议，不引用官方数字。每个单元依图像标识作确定性互斥划分为标定集与审计集；标定集再不相交地分为选择器拟合子集与保形标定子集；审计集仅用于最终报告。划分一经确定即冻结。

### 附录 B 完整评测器与约束扰动
从原始预测出发，每类按分数降序贪心匹配、IoU 判 TP/FP、全点插值求 AP。约束扰动仅施于匹配预测：取保持与所匹配真值旋转 IoU>0.5 的逐实例最大角度扰动（绕预测框自身中心、沿远离真值方向），未匹配预测与假阳性原样保留；随后重新匹配、重算全部指标。六单元 ΔAP@0.5=0.0000、假阳性数不变。评测器数值与各检测器自评、与参考旋转检测度量三方对齐（最大差异约 1.3e-3）。

### 附录 C 几何原则与 masked 主口径推导
由面积归一共中心矩形的 IoU(δθ; ar) 得 δθ_τ(ar)（正文表 1）。取 τ=0.75、以 15° 朝向容差为工程语义，对 δθ_0.75(ar) 反解得到精确交叉点 ar=2.15，报告阈值取 ar≈2.1。低阈值 sensitivity 分别使用 ar≥1.6 与 ar≥1.3；各口径保留比例见正文表 2。


### 附录 E 反向扰动（双向分离的另一半）
固定角度、扰动中心/尺度：AP@0.5 显著下降（例如中心平移 0.2√面积时某单元 AP@0.5 0.80→0.57、另一单元 0.70→0.52；尺度缩 15% 时 0.80→0.76），角度全程不变。表明 mAP 可在角度不变时改变，与正向扰动共同确立 mAP 与朝向可靠性不等价。作为边界，不夸大为主贡献。


### 附录 D 图像级风险控制细节
完整 evaluation image 是正式可交换单元。D_cal-fit 生成按覆盖 0.1 到 1.0 排列的固定阈值序列，D_cal-calib 对有界图像损失 L_I 使用 Hoeffding-Bentkus fixed-sequence LTT，D_audit 仅报告。次级二元事件 Z_I 可用精确二项 Clopper-Pearson；instance-i.i.d. exact-binomial 不是正式保证。实例加权风险只配图像级聚类自助区间。

### 附录 F PSC Phase 1 径向干预
原始时间线保持不变。径向缩放 z'=kz 的十个 k 值逐一保存 evaluator、configured loss/gradient 与 post-NMS artifact；actual-head loss 的网络坐标补算只补原 forward 的坐标缺口，不重做 AP/NMS。Branch 与拆篇四条件由持久化证据独立重建。拆篇门控 PASS；结论只适用于冻结的 PSC-specific 机制线，且不在本轮新建论文版本。

### 附录 G 标注噪声与人工锚点
GT corner-jitter proxy 与人工双标严格分列。机器包按 matched-GT 非角度 class/size/ar 分层，每数据集 500 个任务、两套独立随机顺序和 SHA 绑定 crops；真实 A/B 原始标注缺失时只报告 HUMAN_BLOCKED，不生成任何人工分歧数字。
