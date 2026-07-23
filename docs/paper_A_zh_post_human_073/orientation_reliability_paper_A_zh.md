# 旋转目标检测中的朝向可靠性：测量协议、几何归一化风险与图像级有限样本控制

## 摘要

旋转目标检测通常以平均精度衡量整体性能，但检测正确并不意味着角度可信。尤其在中低交并比阈值下，框的中心、尺度和类别可以保持正确，而朝向仍存在较大误差。本文建立一套面向旋转框角度的可靠性测量协议。首先，我们通过保持分数、类别和假阳性集合不变的完整验证集扰动实验，揭示 AP@0.5 与朝向误差之间的结构性分离：六个检测器—数据集单元的 AP@0.5 均保持不变，而 AP@0.75 显著下降，平均朝向误差由 4.63°--9.09° 增至 34.42°--40.54°。其次，我们从共中心、同尺度矩形的旋转交并比推导朝向可辨识区域，将 `ar>=2.1` 作为唯一主分析口径，并以几何归一化严重事件统一不同长宽比目标的风险语义。再次，我们用归一化风险—覆盖面积、选择性风险及图像级有限样本控制评价任意置信分数。正式保证把完整图像作为可交换单位，对图像内保留预测的严重事件比例应用固定序列 Learn-Then-Test 和 Hoeffding--Bentkus 有界损失上界。最后，我们在 DIOR-R、FAIR1M、SODA-A 和 DOTA 的完整验证单元上验证协议，并以两名真实标注者对 600 个目标的独立互盲标注刻画标签噪声。450 对数值角度的平均圆周分歧为 2.3112°，图像聚类自助法 95% 区间为 1.9970°--2.7854°；5° 和 10° 分歧率分别为 8.00% 和 0.89%。结果表明，5° 风险有实际意义但对标签噪声敏感，10° 事件具有更清楚的严重风险解释。本文提供的是测量与风险控制协议，而非可直接部署的选择器。

**关键词**：旋转目标检测；朝向可靠性；选择性预测；风险—覆盖；有限样本风险控制；标注噪声

## 1 引言

旋转框检测广泛用于遥感、场景文字和工业视觉。其输出通常写为 $(c_x,c_y,w,h,\theta)$，其中 $\theta$ 决定物体几何长轴方向。现有评测主要围绕 AP 展开，它同时受到定位、尺度、类别、排序和角度影响，因而不能单独回答“被保留预测的角度是否可信”。当交并比阈值较低或目标接近方形时，较大的角度变化仍可能保持匹配，AP 与角度风险由此产生结构性错位。

这一问题包含三个相互关联的困难。第一，近方形目标的长轴方向本身不可稳定辨识，若不先规定几何适用域，任何角度统计都可能被退化样本主导。第二，检测分数是否能够排序角度误差，不能由 AP 推断；它需要独立的风险—覆盖评价。第三，同一图像中的预测高度相关，把实例当作独立样本会夸大有限样本保证的有效样本量。

本文围绕“几何定义—测量—有限样本控制”建立统一协议，主要贡献如下。

1. 提出完整验证集朝向扰动协议，在不改变分数、类别及假阳性集合的条件下直接重算 AP，给出 AP@0.5 与朝向风险双向不等价的实证证据。
2. 从共中心、同尺度矩形的旋转交并比曲线推导 `ar>=2.1` 良态区域，并定义随长宽比变化的几何归一化严重事件。
3. 以归一化风险—覆盖面积、AURC、Risk@70 和 Risk@90 测量角度排序质量，并以完整图像为可交换单位构造固定序列风险控制。
4. 在多个检测族和四个数据集上进行完整验证，同时用 600 个真实双标目标给出标签噪声锚点，明确度级风险预算的可解释边界。

## 2 相关工作

**旋转目标检测与角度表示。** DOTA、FAIR1M、DIOR-R 和 SODA-A 推动了遥感旋转检测的标准化评测 [1--4]。Oriented R-CNN、Rotated RTMDet 等方法分别从候选框和实时检测架构改进旋转检测 [5,6]。角度周期性与边界不连续催生了圆滑标签、稠密编码和相位编码等表示 [7--9]；Gaussian Wasserstein Distance、Kullback--Leibler divergence 和调制损失则利用分布或几何结构改善旋转框回归 [10--12]。这些工作主要优化检测精度，本文关注已有检测输出的角度排序与风险。

**选择性预测与校准。** 拒识学习和选择性分类研究风险随覆盖率变化的规律 [13--15]。神经网络概率校准 [16] 及检测器校准 [17] 关注置信度与正确率的一致性。本文的排序指标不等同于概率校准：小于随机基线只表示有信息，不能据此称为 calibrated。

**保形推断与风险控制。** 保形预测以可交换性提供有限样本覆盖 [18]。Learn-Then-Test、risk-controlling prediction sets 与 conformal risk control 将该思想推广到一般有界损失和多阈值选择 [19--21]。本文将它们用于图像级朝向风险，避免实例独立性假设。

**不确定性估计。** 测试时增强和随机前向可提供无需真值的经验不确定性 [22,23]。对旋转角而言，线性方差忽略周期边界，本文统一在双角圆域计算朝向分散度。

## 3 问题定义

### 3.1 长边朝向与周期误差

采用长边规范：若 $w<h$，交换边长并令角度增加 $90^\circ$。长边朝向具有 $180^\circ$ 周期。预测角 $\hat\theta$ 与参考角 $\theta$ 的误差定义为

$$
e_\theta=\min_{k\in\mathbb Z}|\hat\theta-\theta+k\cdot180^\circ|\in[0^\circ,90^\circ].
$$

该定义不判断物体头尾，避免把等价旋转框计为 $180^\circ$ 错误。测试时增强的圆周统计使用 $\theta\mapsto2\theta$ 后的单位圆表示。

### 3.2 几何适用域

令 $a=\max(w,h)/\min(w,h)$。当 $a\to1$ 时，长轴方向趋于不可辨识；角度小变化对框几何的影响也趋弱。主分析仅使用匹配真值满足 `ar>=2.1` 且预测框与真值框均不处于近方形不稳定区的预测。`ar>=1.6` 和 `ar>=1.3` 只用于敏感性分析，不进入主结论。

### 3.3 选择性朝向风险

给定“越大越可信”的分数 $s_i$，按 $s_i$ 降序保留覆盖率 $c$ 的预测集合 $S(c)$，其选择性风险为

$$R(c)=\frac{1}{|S(c)|}\sum_{i\in S(c)}\ell_i.$$

连续覆盖率上的平均为 AURC。为消除不同单元基础误差尺度的影响，定义归一化风险—覆盖面积

$$
\mathrm{NRC}=\frac{\mathrm{AURC}(s)-\mathrm{AURC}_{\rm oracle}}
{\mathrm{AURC}_{\rm random}-\mathrm{AURC}_{\rm oracle}}.
$$

NRC=0 对应理想排序，NRC=1 对应随机排序，NRC>1 表示反序；NRC<1 仅表示 informative 或 non-reversed。我们同时报告 Risk@70、Risk@90、保留数与保留比例。

## 4 几何归一化风险

### 4.1 长宽比阈值的几何原则

考虑两个共中心、同尺度、长宽比为 $a$ 的全等矩形，其中一个相对另一个旋转 $\delta$。记其交并比为 $J(\delta;a)$，并定义

$$
\delta_{0.75}(a)=\inf\{\delta\in[0^\circ,90^\circ]:J(\delta;a)<0.75\}.
$$

多边形求交采用 $0.001^\circ$ 数值精度，并取第一处严格越界。$a$ 越大，朝向变化对交并比越敏感；$a$ 趋近 1 时方向可辨识性退化。把“$15^\circ$ 误差应在 IoU 0.75 下产生几何后果”作为预先规定的工程语义，反解得到交叉点约为 $a=2.15$，故报告阈值取 `ar>=2.1`。

### 4.2 主事件与固定角度敏感性

主严重事件定义为

$$
Y_i=\mathbf 1\{e_{\theta,i}>\delta_{0.75}(a_i)\}.
$$

该事件使细长目标采用更严格的角度容差、较低长宽比目标采用更宽的容差，避免统一固定角度掩盖几何差异。额外报告 $e_\theta>5^\circ$、$10^\circ$、$15^\circ$。其中 $5^\circ$ 是 fine-risk，$10^\circ$ 与 $15^\circ$ 提供更清楚的严重误差敏感性。

## 5 图像级有限样本风险控制

### 5.1 正式损失

完整图像是正式可交换单位。对阈值 $t$，令 $S_I(t)$ 为图像 $I$ 中分数不低于 $t$ 的合格预测，定义

$$
L_I(t)=
\begin{cases}
|S_I(t)|^{-1}\sum_{i\in S_I(t)}Y_i,&|S_I(t)|>0,\\
0,&|S_I(t)|=0.
\end{cases}
$$

显然 $L_I(t)\in[0,1]$。对预先排序的阈值序列，我们使用固定序列 Learn-Then-Test，并对标定图像上的均值应用 Hoeffding--Bentkus 单侧上界。阈值只由标定数据决定，最终审计图像不参与选择。报告均值图像风险、上置信界、非空图像比例、平均实例覆盖、保留实例总数以及标定/审计图像数。

### 5.2 次级事件与经验实例风险

定义二元图像事件

$$Z_I(t)=\mathbf 1\{\exists i\in S_I(t):Y_i=1\}.$$

该端点可以使用精确二项上界，但仅作为“图像内至少一次严重错误”的次级结果。实例加权尾率只报告为 empirical instance-weighted risk，并以图像聚类自助法给出区间。将每个实例视为独立伯努利试验得到的精确二项结果仅用于展示有效样本量虚高的反事实差异，不构成正式保证。

## 6 实验设置

### 6.1 数据集与检测器

实验覆盖 DIOR-R、FAIR1M-v1.0、SODA-A 和 DOTA-v1.0。主验证单元包含相位编码 RetinaNet、Oriented R-CNN 与 Rotated RTMDet；内在角度信号比较还包含圆滑标签和稠密编码头。非 DOTA 数据遵循 trainval/test 协议；DOTA 仅使用本地 train/val 协议和完整验证集，不与公开 test 数字比较。

### 6.2 评测与数据划分

AP 使用旋转多边形 IoU、逐类分数排序、贪心匹配和全点插值计算。可靠性只在一对一类别匹配且 IoU 不低于 0.5 的预测上计算。每个单元按图像确定性划分为标定和审计部分；选择器拟合子集与保形标定子集进一步互斥。所有主表使用 `ar>=2.1`，较低阈值只检查方向稳健性。

### 6.3 完整验证集朝向扰动

对原始预测先运行完整评测器。随后仅旋转已匹配预测，使其沿远离真值角的方向达到仍保持匹配的最大扰动；中心、尺度、分数、类别以及未匹配预测均保持不变。扰动后重新进行完整匹配并重算 AP。反向实验固定角度而改变中心或尺度，用于检验 AP 能否在角度不变时变化。

## 7 结果

### 7.1 AP 与朝向可靠性的分离

表 1 汇总六个完整验证单元。所有单元的 AP@0.5 在约束扰动前后完全相同，AP@0.75 则大幅下降；平均朝向误差增至 34°--41°。这说明在保持 IoU 0.5 匹配关系的几何区域内，AP@0.5 对角度可以显著弱敏感，但并非在所有阈值和形状上都忽略角度。反向实验中，固定角度而改变中心或尺度可显著降低 AP@0.5，进一步说明 AP 与朝向可靠性不等价。

**表 1　完整评测器下的约束朝向扰动**

| 数据集 / 检测器 | 原 AP@0.5 | 扰动 AP@0.5 | 原 AP@0.75 | 扰动 AP@0.75 | 平均角误差（原→扰动） |
|---|---:|---:|---:|---:|---:|
| DIOR-R / 相位编码 RetinaNet | 0.5368 | 0.5368 | 0.350 | 0.038 | 8.95°→39.19° |
| DIOR-R / Oriented R-CNN | 0.6448 | 0.6448 | 0.428 | 0.048 | 8.67°→40.04° |
| DIOR-R / Rotated RTMDet | 0.6462 | 0.6462 | 0.452 | 0.053 | 9.09°→40.54° |
| FAIR1M / 相位编码 RetinaNet | 0.3462 | 0.3462 | 0.242 | 0.067 | 4.63°→36.52° |
| SODA-A / 相位编码 RetinaNet | 0.5991 | 0.5991 | 0.274 | 0.045 | 5.23°→34.42° |
| SODA-A / Oriented R-CNN | 0.7295 | 0.7295 | 0.381 | 0.028 | 5.15°→35.89° |

### 7.2 主口径下的排序结果

检测分数在六个主单元中的 NRC 为 0.4653--0.9379，说明它通常含有角度信息，但信息强弱显著依赖检测器与数据集。测试时增强圆周方差在若干单元进一步改善排序。固定尺寸分箱内，将分数、长宽比和尺寸的线性基线与非线性几何打分比较，15 个可用分箱中有 11 个显示非线性打分的稳定优势，且证据来自多个检测单元和尺寸层。因此该差异不能完全归结为尺寸先验。

需要强调，非线性几何打分使用目标域真值角度误差拟合。它只能作为 calibration upper bound 或 diagnostic score，用于判断“现有可观测几何是否包含额外排序信息”；选择器拟合数据与保形标定数据相互独立，但这不消除其目标域真值依赖。因此它不是 fully deployable 方法，也不是默认选择分数。

### 7.3 内在角度信号的差异

相位编码头的 `phase_mod` 在 DIOR-R、SODA-A 和 FAIR1M 上稳定表现为 NRC>1，即较大模长反而对应较差的角度排序。稠密编码头的原生 bit margin 在 DIOR-R、SODA-A 及 FAIR1M 的重复运行中均为 informative；圆滑标签头的 margin 整体接近随机且不呈稳定反序。这一对照说明反序现象是 head-specific，而非所有角度编码器的共同缺陷。独立的干预研究支持存在结构性原因，但具体径向干预、边界条件和修复分数不属于本文范围。

### 7.4 DOTA 完整验证单元

DOTA-v1.0 仅纳入两个 clean full-validation 单元。Oriented R-CNN 的 AP@0.5/AP@0.75 为 0.7061/0.4517，Rotated RTMDet-M 为 0.7161/0.4868。两者均由 55,804 个验证真值和完整预测重新评测；其检测分数在主长宽比口径下的 NRC 分别为 0.6912 和 0.6458。该结果仅用于协议的跨数据集验证，不用于公开榜单比较。

### 7.5 图像级风险控制

图像级协议在每个单元上报告候选阈值的标定均值风险、Hoeffding--Bentkus 上界和审计风险。与实例独立假设相比，图像级方法的有效样本数由图像数决定，置信上界更保守；例如 DIOR-R 相位编码单元在全覆盖附近，图像级上界约为 0.0154，而实例独立反事实上界约为 0.0087。实例数与图像数之比约为 4.43，直接解释了旧做法的有效样本量虚高。尽管部分阈值在两种做法下均可通过，正式结论只采用图像级有界损失保证。

### 7.6 真人双标噪声锚点

两名真实标注者在独立、互盲条件下标注同一组 600 个 canonical targets，DIOR-R、FAIR1M 和 SODA-A 各 200 个。primary 原始决策中，450 对双方均给出数值角度：DIOR-R 122 对、FAIR1M 169 对、SODA-A 159 对。按 $180^\circ$ 周期计算，总体平均分歧为 2.3112°，按源图像聚类的自助法 95% 区间为 1.9970°--2.7854°；中位数、p90 和 p95 分别为 1.6359°、4.4220° 和 5.9359°。

**表 2　真人双标圆周分歧**

| 范围 | 数值对数 | 均值 | 中位数 | p90 | p95 | P(>5°) | P(>10°) |
|---|---:|---:|---:|---:|---:|---:|---:|
| 总体 | 450 | 2.3112° | 1.6359° | 4.4220° | 5.9359° | 8.00% | 0.89% |
| DIOR-R | 122 | 1.6725° | 1.2069° | 3.4602° | 4.5410° | 4.10% | 0.00% |
| FAIR1M | 169 | 2.0655° | 1.6805° | 4.3297° | 5.4238° | 7.69% | 0.00% |
| SODA-A | 159 | 3.0623° | 2.0374° | 5.1520° | 8.0200° | 11.32% | 2.52% |
| `ar>=2.1` | 308 | 2.2823° | 1.6130° | 4.1978° | 5.5860° | 6.82% | 0.65% |

这组结果给出三点边界。第一，1.5°--2° 的均值风险预算已经接近人工分歧地板，只能称为 label-noise-aware mean risk，不能解释为强语义精度保证。第二，5° 明显高于人工分歧中位数，因而不是无意义阈值；但仍有 8.00% 的人工分歧越界，必须称为 noise-sensitive fine-risk。第三，10° 的人工越界率仅 0.89%，具有更清楚的 severe-risk 余量。SODA-A 的尾部明显更高，该数据集的 5° 结论尤其需要克制。

29 个单方未给出数值角度的目标另行进行了匿名盲重检，其中 27 个获得数值角度、2 个仍为 ambiguous；27 对的均值为 2.2126°，中位数为 1.9302°，p90/p95 为 3.8216°/4.1811°。该重检只作为 secondary endpoint，从未覆盖或替换 primary 原始决策。

人工分歧不能解释为数据集真实 GT error，也不能从模型误差中减去作为“去噪修正”。此前的 corner-jitter 仅保留为 proxy sensitivity；若其量级高于真人分歧，应理解为偏保守或高估，而不能替代真人锚点。

## 8 讨论

**协议价值。** AP 回答检测整体排序与匹配是否正确，NRC 和风险—覆盖回答高置信预测的角度是否更可信，图像级风险控制则回答在有限标定图像下某个阈值能否获得有界风险。这三层互补而非替代。

**标签噪声与风险语义。** 几何归一化事件避开了统一固定角度对不同形状语义不一致的问题，因此作为主风险。固定角度事件帮助读者理解绝对偏差，但必须结合真人锚点：5° 是噪声敏感的细风险，10° 和 15° 更适于严重误差解释。

**可用信号的边界。** 检测分数和测试时增强可直接获得，但跨检测头表现不同。目标域真值拟合的几何分数展示了可达上界，不提供部署保证。相位模长反序揭示了可靠性信号不能仅凭“幅值像置信度”来命名，使用前必须通过独立排序审计。

## 9 局限性

第一，主证据覆盖多个代表性检测族和四个数据集，但不是所有旋转检测器的穷举。第二，有限样本保证依赖图像可交换性；分布漂移下只能重新标定或作经验评估。第三，双标协议每数据集 200 个目标足以支撑总体噪声锚点、宽粒度数据集比较、主长宽比边界与 5°/10° 解释，但不足以支撑 rare-class 精确噪声率、逐类别正式排序、精细 size-bin 因果比较、p99/p99.9 极端尾部或 class×size×ar 的稳定统计。第四，SODA-A 的人工分歧尾部较高，可能同时受到小目标、遮挡和标注可辨识性的影响，现有样本不能分解其因果来源。第五，本文不提供无需目标域真值的通用选择器。

## 10 结论

本文提出旋转目标检测朝向可靠性的统一测量与有限样本控制协议。完整验证集扰动表明 AP@0.5 与角度可信度在明确几何区域内可以显著分离；共中心矩形几何给出 `ar>=2.1` 主适用域和形状归一化严重事件；NRC、AURC 与风险—覆盖刻画任意分数的角度排序能力；以完整图像为可交换单位的有界损失控制避免了实例独立假设造成的过度乐观。真实双标进一步表明，度级均值预算必须考虑标签噪声，5° 风险有意义但噪声敏感，而 10° 事件具有更清楚的严重风险解释。该框架为比较旋转检测器“角度是否可信”提供了独立于单一 AP 数字的可复现依据。

## 参考文献

1. Xia G S, Bai X, Ding J, et al. DOTA: A large-scale dataset for object detection in aerial images. CVPR, 2018: 3974--3983.
2. Sun X, Wang P, Wang C, et al. FAIR1M: A benchmark dataset for fine-grained object recognition in high-resolution remote sensing imagery. ISPRS Journal of Photogrammetry and Remote Sensing, 2022, 184: 116--130.
3. Cheng G, Han J, Zhou P, et al. Learning rotation-invariant convolutional neural networks for object detection in VHR optical remote sensing images. IEEE Transactions on Geoscience and Remote Sensing, 2016, 54(12): 7405--7415.
4. Cheng G, Yuan X, Yao X, et al. Towards large-scale small object detection: Survey and benchmarks. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2023, 45(11): 13467--13488.
5. Xie X, Cheng G, Wang J, et al. Oriented R-CNN for object detection. ICCV, 2021: 3520--3529.
6. Lyu C, Zhang W, Huang H, et al. RTMDet: An empirical study of designing real-time object detectors. arXiv:2212.07784, 2022.
7. Yang X, Yan J. Arbitrary-oriented object detection with circular smooth label. ECCV, 2020: 677--694.
8. Yang X, Hou L, Zhou Y, et al. Dense label encoding for boundary discontinuity free rotation detection. CVPR, 2021: 15819--15829.
9. Yu Y, Yang X, Li Q, et al. Phase-shifting coder: Predicting accurate orientation in oriented object detection. CVPR, 2023: 13354--13363.
10. Yang X, Yan J, Ming Q, et al. Rethinking rotated object detection with Gaussian Wasserstein distance loss. ICML, 2021: 11830--11841.
11. Yang X, Zhou Y, Zhang G, et al. The KFIoU loss for rotated object detection. ICLR, 2023.
12. Qian W, Yang X, Peng S, et al. Learning modulated loss for rotated object detection. AAAI, 2021, 35(3): 2458--2466.
13. El-Yaniv R, Wiener Y. On the foundations of noise-free selective classification. Journal of Machine Learning Research, 2010, 11: 1605--1641.
14. Geifman Y, El-Yaniv R. Selective classification for deep neural networks. NeurIPS, 2017, 30.
15. Geifman Y, Uziel G, El-Yaniv R. SelectiveNet: A deep neural network with an integrated reject option. ICML, 2019: 2151--2159.
16. Guo C, Pleiss G, Sun Y, Weinberger K Q. On calibration of modern neural networks. ICML, 2017: 1321--1330.
17. Kuppers F, Kronenberger J, Shantia A, Haselhoff A. Multivariate confidence calibration for object detection. CVPR Workshops, 2020: 326--327.
18. Vovk V, Gammerman A, Shafer G. Algorithmic Learning in a Random World. Springer, 2005.
19. Angelopoulos A N, Bates S, Jordan M I, Malik J. Uncertainty sets for image classifiers using conformal prediction. ICLR, 2021.
20. Angelopoulos A N, Bates S, Fisch A, et al. Learn then test: Calibrating predictive algorithms to achieve risk control. arXiv:2110.01052, 2021.
21. Angelopoulos A N, Bates S, Candès E J, Jordan M I, Lei L. Conformal risk control. ICLR, 2024.
22. Gal Y, Ghahramani Z. Dropout as a Bayesian approximation: Representing model uncertainty in deep learning. ICML, 2016: 1050--1059.
23. Wang G, Li W, Aertsen M, et al. Aleatoric uncertainty estimation with test-time augmentation for medical image segmentation with convolutional neural networks. Neurocomputing, 2019, 338: 34--45.
24. Hoeffding W. Probability inequalities for sums of bounded random variables. Journal of the American Statistical Association, 1963, 58(301): 13--30.
25. Bentkus V. On Hoeffding's inequalities. The Annals of Probability, 2004, 32(2): 1650--1673.
26. Efron B, Tibshirani R J. An Introduction to the Bootstrap. Chapman & Hall/CRC, 1993.
27. Gneiting T, Raftery A E. Strictly proper scoring rules, prediction, and estimation. Journal of the American Statistical Association, 2007, 102(477): 359--378.
