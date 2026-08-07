# 旋转目标检测的朝向可靠性测量：几何归一化风险、场景级审计与人工标注不确定性

## 摘要

旋转目标检测通常以平均精度评价整体性能，但一次检测在类别、中心和尺度上正确，并不意味着其角度可信。交并比阈值、目标长宽比、匹配竞争以及标注不确定性会共同改变角度误差的可见程度，使 AP 难以单独回答“高分预测是否具有更可靠的朝向”。本文提出一套面向有向边界框的朝向可靠性测量协议。协议以 le90 长边规范定义周期角度误差，以共中心、同尺度矩形的旋转交并比推导 `ar>=2.1` 的主分析区域，并用随长宽比变化的几何归一化严重事件统一不同形状的风险语义。为评价任意可靠性分数，我们联合报告风险—覆盖曲线、AURC、归一化风险—覆盖面积及固定角度敏感性。六个干净完整验证单元的完整评测器扰动显示：在自适应 IoU 0.50 边界内，AP@0.5 均保持不变，而 AP@0.75 显著下降；真实几何下 `ar>=2.1` 实例的经验中位容忍角约为 25°--30°（IoU 0.50）和 0°--7.5°（IoU 0.75），但固定剂量网格的原始预测并不完整，因而不能确认统一的 AP@0.75 拐点。

本文进一步讨论场景级统计单位、abstention 与有限样本审计的边界，不把未闭合的认证结果作为本文证据。两名独立标注者对 600 个目标的 450 对数值角度给出 2.3112° 的平均分歧；标注者与 official GT 的差异中位数约为 1.76°--1.79°。这些结果说明度级风险解释必须同时考虑几何可辨识性和标注不确定性。

**关键词：** 旋转目标检测；朝向可靠性；风险—覆盖；几何归一化风险；场景级统计；标注不确定性

## 1 引言

有向边界框以 $(c_x,c_y,w,h,\theta)$ 描述目标，广泛用于遥感影像、场景文字和工业视觉。现有旋转检测研究主要围绕 AP、角度编码连续性和定位损失展开。AP 是必要的综合指标，却混合了类别、中心、尺度、角度、分数排序和匹配关系。当 IoU 阈值较低，或目标接近方形时，显著的角度变化仍可能保留匹配；反之，中心或尺度的小变化也可能在角度不变时改变 AP。因此，“检测是否正确”和“朝向是否可信”是相关但不同的问题。

朝向可靠性测量至少面临四个困难。第一，旋转框存在 $180^\circ$ 周期和长短边交换等价性，线性角度差会制造伪误差。第二，目标形状决定角度可辨识性：细长目标的角度变化迅速降低 IoU，近方形目标则可能在很大角度范围内保持几何相似。第三，置信分数对检测正确性的排序能力不必等同于其对角度误差的排序能力。第四，同一图像、同一切片来源或同一原始母景中的实例并不独立；把大量实例当作独立样本会产生过窄的置信上界。

本文将问题限定为**测量与审计**，而非提出新的角度编码器或宣称一个通用可部署选择器。具体贡献如下。

1. 形式化 le90 长边朝向误差，并用风险—覆盖曲线、AURC 和 NRC 独立评价可靠性排序。
2. 从旋转矩形 IoU 推导 `ar>=2.1` 的几何原则化主口径，定义随长宽比变化的 geometry-normalized severe orientation event，并将 5°、10°、15° 保留为固定角度敏感性。
3. 在完整评测器中执行保持预测身份、分数、类别和非角度几何不变的朝向扰动，量化 AP@0.5 与 AP@0.75 的不同敏感性，并比较理想与经验容忍角。
4. 在 DIOR-R、FAIR1M、SODA-A 和 DOTA 的多个 detector-head units 上报告 full-validation AP 与朝向排序，利用固定尺寸分箱排查几何分析中的尺寸混淆。
5. 比较图像、切片和母景统计单位，显式处理 abstained scenes，并将有限样本认证作为历史探索性审计而非本文证据。
6. 通过两名真人标注者的双标、标注者与 official GT 的差异以及未完成的第三人仲裁边界，限定度级风险的科学解释。
7. 提供包含角度规范、几何阈值、排序度量、场景级风险和显式 `INFEASIBLE` 输出的测量工具箱。

不同原生角度信号对不同风险泛函可能呈现不同的排序语义。模型特定的角度编码机制与排序修复不属于本文范围。

## 2 相关工作

### 2.1 旋转目标检测、周期性与几何损失

DOTA、FAIR1M、DIOR 和 SODA-A 提供了复杂遥感场景中的旋转检测基准 [1--4]。Oriented R-CNN 以中间表示和候选框机制构造高效旋转检测器 [5]，RTMDet 系列系统研究了实时检测器设计 [6]。旋转框的角度边界不连续和近方形退化推动了 Circular Smooth Label（CSL）、Dense Coded Label（DCL）和 Phase-Shifting Coder（PSC）等角度表示 [7--9]。Gaussian Wasserstein Distance（GWD）与 Kullback--Leibler divergence（KLD）从分布距离角度缓解旋转框回归的不连续性 [10,11]。ARS-DETR进一步讨论了长宽比与 AP@0.5 的朝向敏感性 [12]。这些方法主要优化检测器；本文研究既有输出的朝向风险如何被定义、排序和审计。

### 2.2 选择性预测、风险—覆盖与校准

选择性分类研究模型在拒绝部分样本后风险如何随覆盖率变化 [13--15]。风险—覆盖曲线适合评价“分数能否把低风险样本排在前面”，与概率校准并不相同。神经网络校准和目标检测校准关注预测概率与经验正确率的匹配 [16,17]；检测期望校准误差（D-ECE）进一步考虑框、类别和置信度的联合结构 [17]。本文的 NRC 是排序度量：NRC 小于 1 只能说明 informative 或 non-reversed ranking，不能推出概率 calibrated。

### 2.3 保形推断与风险控制

保形预测利用可交换性构造有限样本覆盖 [18]。Risk-Controlling Prediction Sets、Learn-Then-Test（LTT）和 Conformal Risk Control 将其扩展到一般风险函数及候选超参数选择 [19--21]；相关研究也将保形思想用于目标检测中的框覆盖和错误控制 [22]。这些理论并不自动解决统计单位的选择。如果同一图像或母景中的实例强相关，instance-i.i.d. 分析会高估有效样本量。本文将这些方法作为认证可行性审计，并完整保留严格预算下的不可行结果。

### 2.4 测试时不确定性与人工标注差异

测试时增强可通过多次变换的一致性提供经验不确定性 [23]。对于 $180^\circ$ 周期的朝向，必须在 $\theta\mapsto2\theta$ 的圆域计算方差，而不能直接对角度做线性方差。另一方面，人工标签并非无噪声常数；标注分歧、任务歧义和聚合规则会改变可解释的风险下限 [24,25]。本文分别报告 inter-annotator disagreement、annotator-vs-official-GT discrepancy 和几何 proxy，不将其中任何一个直接解释为真实 GT error。

## 3 问题定义

### 3.1 le90 长边朝向与周期误差

将任意旋转框规范为长边表示：若 $w<h$，交换长短边并令角度增加 $90^\circ$。规范后的角度记为 $\phi\in[0^\circ,180^\circ)$。预测角 $\hat\phi$ 与参考角 $\phi$ 的圆周误差为

$$
e_\theta(\hat\phi,\phi)
=\min_{k\in\mathbb Z}\left|\hat\phi-\phi+180^\circ k\right|
=\min\left(d,180^\circ-d\right),
$$

其中 $d=|\hat\phi-\phi|\bmod180^\circ$，故 $e_\theta\in[0^\circ,90^\circ]$。该量描述几何长边方向，不判断物体头尾或语义航向。

### 3.2 长宽比与可辨识区域

定义

$$
a=\frac{\max(w,h)}{\min(w,h)}\ge1.
$$

当 $a\to1$ 时，长轴方向趋于不可辨识，角度变化对旋转矩形几何的影响也减弱。本文正文唯一主口径为 `ar>=2.1`，并排除预测框或参考框处于近方形不稳定区的实例。`ar>=1.6` 和 `ar>=1.3` 仅用于敏感性检查，不用于替代主结果。

### 3.3 可靠性分数与风险对象

对实例 $i$，可靠性分数 $s_i$ 越大表示越可信，风险 $\ell_i$ 越小越好。风险既可以是连续角误差 $e_{\theta,i}$，也可以是固定阈值或几何归一化二元事件。同一分数对不同风险泛函的排序含义可能不同，因此任何“可靠/不可靠”结论都必须绑定明确的 score-endpoint unit。

## 4 几何可辨识性与归一化风险

### 4.1 理想几何容忍角

考虑两个共中心、同尺度、长宽比均为 $a$ 的矩形，其中一个相对另一个旋转 $\delta$。记旋转 IoU 为 $J(\delta;a)$。对 IoU 阈值 $\tau$，定义第一处严格越界角

$$
\delta_\tau(a)=
\inf\left\{\delta\in[0^\circ,90^\circ]:J(\delta;a)<\tau\right\}.
$$

数值求解遵循 le90 第一叶，角度精度为 $0.001^\circ$。$a$ 越大，$\delta_\tau(a)$ 通常越小；$\tau=0.75$ 比 $\tau=0.50$ 更早响应角度变化。以“15° 误差应在 IoU 0.75 下产生明确几何后果”为原则，反解交叉点约为 $a=2.1$，由此得到正文主口径。

理想曲线不等于真实检测行为。实际预测与 GT 的中心、尺度、初始 IoU 不同，还存在竞争匹配和 NMS。本文因此将它作为形状归一化坐标，而不是评测器行为的精确预测。

### 4.2 主风险事件与固定角度敏感性

主严重事件定义为

$$
Y_i^{\mathrm{geo}}
=\mathbf 1\left\{e_{\theta,i}>\delta_{0.75}(a_i)\right\}.
$$

该定义对细长目标使用更严格的角度容差，对较低长宽比目标使用更宽的容差。它描述“在理想共中心同尺度模型下超出 IoU 0.75 几何容忍度”，不等价于真实检测框必然跌破 IoU 0.75。

固定角度敏感性为

$$
Y_i^{(q)}=\mathbf 1\{e_{\theta,i}>q\},\qquad q\in\{5^\circ,10^\circ,15^\circ\}.
$$

5° 用于 fine-risk，但对标注不确定性敏感；10° 和 15° 提供更清晰的严重误差解释。

## 5 朝向可靠性测量协议

### 5.1 风险—覆盖曲线与 AURC

按 $s_i$ 降序排列实例。覆盖率 $c=k/n$ 时保留前 $k$ 个预测，选择性风险为

$$
R_s(c)=\frac{1}{k}\sum_{j=1}^{k}\ell_{(j)},
$$

其中 $(j)$ 表示分数降序后的索引。离散 AURC 为

$$
\operatorname{AURC}(s)=\frac{1}{n}\sum_{k=1}^{n}R_s(k/n).
$$

本文同时报告 Risk@70、Risk@90、保留数量与保留比例，避免单个面积掩盖高覆盖区行为。

### 5.2 归一化风险—覆盖面积

不同数据集和检测器的基础角误差不同。令 oracle 按真实风险从小到大排序，random 的期望选择性风险等于全体均值，定义

$$
\operatorname{NRC}(s)=
\frac{\operatorname{AURC}(s)-\operatorname{AURC}_{\mathrm{oracle}}}
{\operatorname{AURC}_{\mathrm{random}}-\operatorname{AURC}_{\mathrm{oracle}}}.
$$

- NRC=0：理想风险排序；
- NRC=1：随机排序基线；
- NRC>1：相对风险反序；
- NRC<1：informative 或 non-reversed ranking，但不表示 calibrated。

所有同分数按持久化预测顺序稳定打破，NaN 不进入指标。

### 5.3 Score menu 与监督分类

本文在同一统计层比较四类分数。

| 分数 | 输入与监督 | 目标推理可得 | 科学定位 |
|---|---|---:|---|
| detection score | 检测器原始置信度，无额外 GT 拟合 | 是 | 可部署基线 |
| TTA circular consistency | 对增强角做 $\theta\mapsto2\theta$，取负圆方差 | 是 | 无目标 GT，但增加推理成本 |
| source-supervised leave-* geometry | 分数、$\log a$、$\log$ size、宽高；在其它源域用 GT 角误差训练 | 是 | 源域监督迁移，不是 fully GT-free training |
| target-GT nonlinear geometry | 同类几何特征，在目标域独立拟合集上用 GT 角误差训练 | 是 | diagnostic/calibration upper bound，不可部署 |

目标域上界的拟合集、认证标定集与审计集相互独立，但这种独立性不消除其目标域 GT 依赖。它只能估计可观测几何特征所包含的 headroom。

## 6 场景级统计与认证可行性审计

### 6.1 Eligible-scene universe 与 abstention

对每个 evaluation unit，先固定 baseline eligible-scene universe：只包含至少一个 `ar>=2.1` eligible matched prediction 的原始场景。该 universe 在所有分数、阈值和风险预算下保持不变。

阈值 $t$ 后，若场景中没有任何保留的 eligible prediction，则该场景记为 **abstained scene**。它进入 nonempty scene rate 的分母，但不以 $L_I=0$ 进入条件风险均值，从而避免通过大量空选择稀释风险。

对非空场景 $I$，定义条件场景损失

$$
L_I(t)=\frac{1}{|S_I(t)|}\sum_{i\in S_I(t)}Y_i^{\mathrm{geo}},
\qquad |S_I(t)|>0,
$$

其中 $S_I(t)$ 为场景中被分数阈值保留的 eligible predictions。另定义 co-primary scene event

$$
Z_I(t)=\mathbf 1\left\{\exists i\in S_I(t):Y_i^{\mathrm{geo}}=1\right\}.
$$

对 $L_I\in[0,1]$ 使用 bounded-loss Hoeffding--Bentkus 单侧上界；对二元 $Z_I$ 使用 Clopper--Pearson 单侧上界。实例加权风险仅作为 empirical instance-weighted risk，并使用图像或场景聚类 bootstrap，不构成 instance-i.i.d. 正式保证。

### 6.2 Mother-scene clustering

DIOR-R 和 FAIR1M 的评测图像可直接对应原始母景。SODA-A 由切片构成，可以从文件名恢复 576 个母景，但同一母景的切片跨越既有标定/审计角色；在不改变数据划分的前提下，严格 mother-scene calibration/audit independence 不成立。因此 SODA-A 的正式统计单位只能写 tile/image-level，母景聚合仅作为相关性敏感性分析。

表 1 展示统计单位改变带来的有效样本量和上界变化。实例独立分析显著更乐观。

**表 1　统计单位对有效样本量与单侧上界的影响示例**

| 数据集示例 | 实例数 | tile/image 数 | mother-scene 数 | instance-i.i.d. UCB | tile/image UCB | mother-scene UCB | 正式定位 |
|---|---:|---:|---:|---:|---:|---:|---|
| DIOR-R | 19,207 | 2,882 | 2,882 | 0.0040 | 0.0188 | 0.0188 | mother-scene 可用 |
| SODA-A | 120,925 | 4,120 | 417 | 0.0061 | 0.0090 | 0.0180 | tile/image 正式；mother-scene 仅敏感性 |

### 6.3 历史统计审计边界

固定序列 LTT、Hoeffding--Bentkus 和 Clopper--Pearson 仅作为既有统计组件。历史探索性审计曾尝试比较预算、覆盖率和场景单位，但其实现未闭环，因此不作为本文的正式认证证据。

## 7 实验设置

### 7.1 数据集与检测器

实验覆盖 DIOR-R、FAIR1M-v1.0、SODA-A 和 DOTA-v1.0。检测器包括相位编码 RetinaNet、Oriented R-CNN、Rotated RTMDet 及相关原生角度头。非 DOTA 数据采用既有 trainval/test 协议；DOTA 仅使用本地 train/val 结果，不与公开 test 数字比较。

AP 由完整预测和完整 GT 通过旋转 IoU、逐类分数排序及一对一贪心匹配计算。可靠性分析基于 provenance-clean full-validation matched predictions。主表仅使用 `ar>=2.1`；匹配实例的筛选不被用作 AP 的替代证据。

### 7.2 完整评测器朝向扰动

六个 clean full-validation evaluation units 先运行完整评测器。随后保持 prediction identity、分数、类别、中心、宽和高不变，只改变角度，并重新匹配、重新计算 AP@0.5、AP@0.75 和角误差。已有权威端点将每个可扰动预测沿远离参考角的方向推进至仍位于 IoU 0.50 匹配边界内的最大角度。

固定剂量网格预先定义为 0°、2°、5°、10°、15°、20°、25°和30°。但完整六单元所需的原始预测没有全部持久化，因此本文不插值固定剂量 AP，也不报告统一 AP@0.75 knee。经验容忍角采用合法近似：在保持真实预测与 GT 的中心、尺度不变时，沿增加当前角误差的方向，以 0.5° 网格找到固定 matched pair IoU 首次低于 $\tau$ 的角度。该近似不重做竞争匹配或 NMS，故与理想曲线只能比较趋势。

### 7.3 不确定性区间

排序指标与人工差异使用图像或原始场景为 cluster 的 bootstrap。场景条件风险使用 Hoeffding--Bentkus 有界损失上界，scene event 使用 Clopper--Pearson 上界。所有区间与统计单位一同报告。

## 8 测量结果

### 8.1 Full-validation AP 与朝向扰动

表 2 给出六个完整评测器单元。自适应 IoU 0.50 边界扰动下，六个单元的 $\Delta$AP@0.5 均为 0，而 AP@0.75 下降 0.176--0.399，平均角误差升至 34.42°--40.54°。这证明 AP@0.5 在明确的几何区域内可以对角度弱敏感；它不意味着 AP@0.5 在所有形状、阈值和扰动下完全忽略角度。

**表 2　完整评测器下的约束朝向扰动**

| 数据集 / 检测器 | 原 AP@0.5 | 扰动 AP@0.5 | 原 AP@0.75 | 扰动 AP@0.75 | 原→扰动平均角误差 |
|---|---:|---:|---:|---:|---:|
| DIOR-R / 相位编码 RetinaNet | 0.5368 | 0.5368 | 0.3503 | 0.0384 | 8.947°→39.189° |
| DIOR-R / Oriented R-CNN | 0.6448 | 0.6448 | 0.4275 | 0.0484 | 8.665°→40.041° |
| DIOR-R / Rotated RTMDet | 0.6462 | 0.6462 | 0.4515 | 0.0532 | 9.087°→40.541° |
| FAIR1M / 相位编码 RetinaNet | 0.3462 | 0.3462 | 0.2422 | 0.0665 | 4.631°→36.516° |
| SODA-A / 相位编码 RetinaNet | 0.5991 | 0.5991 | 0.2735 | 0.0448 | 5.230°→34.416° |
| SODA-A / Oriented R-CNN | 0.7295 | 0.7295 | 0.3805 | 0.0278 | 5.148°→35.893° |

DOTA 的两个 clean full-validation 单元提供额外基线：Oriented R-CNN 的 AP@0.5/AP@0.75 为 0.7061/0.4517，Rotated RTMDet-M 为 0.7161/0.4868。它们不进入不完整的固定剂量网格。

### 8.2 理想与经验容忍角

表 3 汇总 `ar>=2.1` 的实际几何近似。IoU 0.50 的经验中位容忍角集中在 25°--30°，而 IoU 0.75 为 0°--7.5°；0° 表示部分真实匹配对在基准状态已低于 0.75，而非角度测量失败。中心和尺度偏差显著压缩了高 IoU 容忍度。

**表 3　真实几何下固定 matched pair 的经验容忍角**

| 数据集 / 检测器 | n | IoU 0.50 中位数 | IoU 0.50 p10--p90 | IoU 0.75 中位数 | IoU 0.75 p10--p90 |
|---|---:|---:|---:|---:|---:|
| DIOR-R / 相位编码 RetinaNet | 49,502 | 26.5° | 15.0°--38.5° | 6.0° | 0.0°--12.0° |
| DIOR-R / Oriented R-CNN | 54,297 | 27.0° | 15.0°--38.0° | 7.5° | 0.0°--12.0° |
| DIOR-R / Rotated RTMDet | 53,671 | 27.0° | 14.5°--38.0° | 7.0° | 0.0°--12.0° |
| FAIR1M / 相位编码 RetinaNet | 31,801 | 25.0° | 13.0°--36.0° | 0.0° | 0.0°--8.0° |
| SODA-A / 相位编码 RetinaNet | 197,529 | 28.5° | 13.5°--36.5° | 0.0° | 0.0°--9.5° |
| SODA-A / Oriented R-CNN | 235,428 | 30.0° | 14.5°--37.5° | 4.0° | 0.0°--10.5° |

理想 $\delta_{0.50}(a)$ 与经验 IoU 0.50 容忍度在方向上相符，但真实框的 center、scale、matching 和 NMS 使分布显著扩散。当前证据仅支持部分几何对齐，不能声称已发现跨单元统一的 AP@0.75 knee。

### 8.3 主口径下的排序测量

表 4 给出 detection score 在六个主 evaluation units 上的连续角误差排序。NRC 均小于 1，说明检测分数通常包含角度风险信息，但其强弱差异明显；这一结论是 informative ranking，而不是 calibrated probability。

**表 4　`ar>=2.1` 下 detection score 的连续角风险排序**

| 数据集 / 检测器 | retained n | retained ratio | NRC | AURC | Risk@70 | Risk@90 |
|---|---:|---:|---:|---:|---:|---:|
| DIOR-R / 相位编码 RetinaNet | 25,065 | 0.5716 | 0.6082 | 1.2075 | 1.4346° | 1.5866° |
| DIOR-R / Oriented R-CNN | 27,671 | 0.5778 | 0.5741 | 1.3528 | 1.5598° | 1.7512° |
| DIOR-R / Rotated RTMDet | 27,385 | 0.5719 | 0.4653 | 1.3786 | 1.6090° | 1.9066° |
| FAIR1M / 相位编码 RetinaNet | 15,120 | 0.5791 | 0.9379 | 2.2225 | 2.2998° | 2.3004° |
| SODA-A / 相位编码 RetinaNet | 101,102 | 0.6416 | 0.8113 | 1.7827 | 1.8733° | 1.9817° |
| SODA-A / Oriented R-CNN | 120,925 | 0.6290 | 0.6878 | 1.8254 | 2.0645° | 2.2053° |

DOTA clean units 的 detection-score NRC 分别为 0.6912（Oriented R-CNN）和 0.6458（Rotated RTMDet-M），与“检测分数通常 informative、但远非 oracle”这一边界一致。

### 8.4 固定尺寸分箱的几何分析

为排除非线性几何分析只是在利用 size prior，本文在固定 small/medium/large bins 内比较 detection score、score+$\log a$ 线性模型、score+$\log a$+$\log$ size 线性模型以及非线性几何诊断分数。15 个可用 bins 中有 11 个的 image-cluster bootstrap 区间支持非线性分数优于 score+$\log a$+$\log$ size，覆盖多个数据集、检测器和尺寸层。

**表 5　固定尺寸分箱内的非线性几何诊断证据**

| evaluation unit | 可用 bins | 显著支持 bins | 代表性 $\Delta$NRC（线性−非线性） |
|---|---:|---:|---:|
| DIOR-R / 相位编码 RetinaNet | 3 | 2 | medium 0.1388；large 0.1510 |
| DIOR-R / Oriented R-CNN | 3 | 3 | small 0.0419；medium 0.2206；large 0.1850 |
| DIOR-R / Rotated RTMDet | 3 | 3 | small 0.0386；medium 0.1642；large 0.0781 |
| FAIR1M / 相位编码 RetinaNet | 2 | 0 | 结果不稳定，完整保留 |
| SODA-A / 相位编码 RetinaNet | 2 | 2 | small 0.0404；medium 0.0538 |
| SODA-A / Oriented R-CNN | 2 | 1 | small 0.0146 |

该结果说明非线性差异不能完全由尺寸先验解释，但不构成可部署方法证据：该分数使用目标域 GT angle error 拟合，仅是 calibration upper bound。

### 8.5 历史探索性审计

历史认证前沿的实现与证据链未完成闭环，相关表格和数字不作为本文结果。本文仅保留风险—覆盖、场景统计和可复算性边界的测量定义。

## 9 人工标注不确定性审计

### 9.1 独立双标

两名真实标注者独立、互盲地处理 600 个 canonical targets，DIOR-R、FAIR1M 和 SODA-A 各 200。两人均给出数值角度的 primary 子集为 450 对：DIOR-R 122、FAIR1M 169、SODA-A 159。圆周分歧按源图像 cluster bootstrap 计算。

**表 7　Inter-annotator circular disagreement**

| 范围 | 数值对数 | 均值 | 95% CI | 中位数 | p90 | p95 | P(>5°) | P(>10°) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 总体 | 450 | 2.3112° | 1.9970°--2.7854° | 1.6359° | 4.4220° | 5.9359° | 8.00% | 0.89% |
| `ar>=2.1` | 308 | 2.2823° | — | 1.6130° | — | — | 6.82% | 0.65% |

29 个原先仅一方给出数值角度的目标经过匿名盲重检，27 个获得数值角度，2 个仍 ambiguous；该结果仅为 secondary endpoint，不替换 primary 双标。

### 9.2 标注者与 official GT 的差异

将每名标注者的数值角度分别与 official GT 做 le90 圆周比较，得到表 8。此处使用“差异”而非“误差”：official GT 是数据集参考标注，不被假定为绝对无误差真值。

**表 8　Annotator-vs-official-GT discrepancy**

| 比较 | n | 均值 | 中位数 | p90 | p95 | P(>5°) | P(>10°) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Annotator 1 vs official GT | 468 | 5.2721° | 1.7639° | 6.7240° | 10.0975° | 17.31% | 5.13% |
| Annotator 2 vs official GT | 463 | 5.1219° | 1.7899° | 6.9371° | 10.2594° | 16.20% | 5.18% |

较高均值与较低中位数并存，说明少量大差异目标显著影响尾部。它不能证明 detector error 由 annotation noise 主导，也不能被用来从模型误差中减去某个“噪声值”。Corner-jitter 只保留为 proxy sensitivity，不替代真人结果。

### 9.3 风险阈值解释与未完成仲裁

人工结果支持以下解释：

- 1.5°--2° 的 mean-risk budget 已接近 inter-annotator disagreement 尺度，只能作 label-noise-aware mean risk；
- 5° 高于分歧中位数，具有实际 fine-risk 意义，但 8.00% 的双标对仍超过 5°，因而 noise-sensitive；
- 10° 的双标越界率为 0.89%，具有更清楚的 severe-risk margin；
- 每数据集 200 个目标不支持 rare-class 精确率、逐类别排序或 p99/p99.9 极端尾部主张。

第三标注员的 150 个样本已经分层固定为每数据集 50，包括高分歧/ambiguous 边界与随机低分歧对照，但真人结果数仍为 0。三人 circular-median consensus 和 adjudication 尚未形成，本文不把人工标注写成完全闭环。

## 10 工具箱

随协议实现的独立工具箱包含：

1. canonical le90 angle error 与 circular distance；
2. $\delta_\tau(a)$ 数值查询和 geometry-normalized severe event；
3. NRC、AURC、risk-coverage、Risk@70/90；
4. 5°、10°、15° 固定敏感性；
5. image、tile 与 mother-scene cluster bootstrap；
6. eligible-scene universe、nonempty conditional scene risk 与 scene event；
7. fixed-sequence LTT、Hoeffding--Bentkus bounded-loss UCB 和 Clopper--Pearson event UCB；
8. alpha feasibility frontier 与 score-menu certification；
9. AP@0.75、detection-score NRC 和 scene-risk workpoint 的统一命令行输出。

当冻结网格上没有工作点时，工具箱显式输出 `INFEASIBLE`，而不是静默删除 evaluation unit。默认 score menu 不把 target-GT geometry score 当作 deployable score，也不包含模型特定的角度编码机制代码。单元测试、合成 sanity test 和真实持久化数据回归均通过。

## 11 讨论

### 11.1 测量协议回答什么

AP 回答检测系统在给定 IoU 阈值下的综合排序和匹配质量；NRC/AURC 回答可靠性分数能否优先保留低角度风险实例；几何归一化事件回答同一角误差在不同形状上是否具有相近几何严重性；场景级统计审计回答不同交换单位如何改变风险估计和有效样本量。这四层互补，但不能互相替代。

完整评测器扰动和经验容忍度共同说明，AP@0.5 的弱敏感性存在明确几何来源，而 AP@0.75 通常更早响应。然而，真实中心、尺度和匹配竞争使理想曲线无法直接预测 AP。原始预测持久化不完整也阻止了统一固定剂量 knee 的确认，因此本文只保留部分对齐结论。

### 11.2 统计认证的边界

本文不把历史探索性认证结果写成方法成功或科学负结果。可以保留的结论是：实例数很多不等于可交换样本很多，空场景记零会改变风险解释；若要作正式认证，必须先闭合生成端、统计单位、输入身份和独立复核。

### 11.3 标注不确定性的边界

Inter-annotator disagreement 衡量两名标注者之间的一致性；annotator-vs-official-GT discrepancy 衡量人与数据集参考标注的差异；二者都不等于不可观测的真实 GT error。本文不从模型误差中扣除人工分歧，也不把 official GT 当作绝对真值。人工审计的作用是限制风险语言，而不是“校正”模型数字。

## 12 局限性

第一，严格主风险认证没有形成跨 evaluation units 的可部署成功，本文只能作为 measurement-only 研究。第二，SODA-A 的母景可以恢复，但既有数据角色在母景层交叉，正式保证只能是 tile/image-level。第三，没有找到同时满足未参与协议设计、full universe、provenance-clean、持久化完整和可复算要求的独立确认单元；现有确认性证据为空，不能通过更换标准或降低预算弥补。第四，固定剂量完整评测器网格因部分 raw predictions 未持久化而不完整，统一 AP@0.75 knee 尚未确认。第五，第三标注员没有提交真人结果，三人共识与仲裁尚未完成。第六，每数据集 200 个双标目标足以支持总体锚点和宽粒度比较，但不足以支撑稀有类别、精细 size-bin 因果效应或极端尾部。第七，本文覆盖的 detector-head units 具有代表性但不是所有旋转检测器的穷举，且分布漂移下的跨域保证不在本文证据范围内。

## 13 结论

本文建立了一套面向旋转目标检测的朝向可靠性测量协议。该协议以 le90 周期误差和 `ar>=2.1` 几何适用域为基础，用 $\delta_{0.75}(a)$ 定义形状归一化严重事件，以 NRC、AURC 和风险—覆盖曲线评价可靠性排序，并通过完整评测器区分 AP@0.5 与 AP@0.75 的朝向敏感性。图像、切片和母景审计显示，实例独立假设会显著夸大有效样本量；严格预算认证仍需独立、完整的生成链与确认单元；本文不据未闭合历史审计作认证结论。真人双标与 official GT 差异则说明，度级风险必须采用 label-noise-aware 语言。

因此，本文的贡献是可复算的测量定义、统计单位纠正、完整评测器敏感性审计及人工标注不确定性边界；历史认证审计仅作为未闭合的限制。它为后续旋转检测研究提出了一个更严格的问题：在不依赖目标域真值、不过度利用实例数量且保持实用覆盖的条件下，什么分数才能真正支持可认证的朝向选择？

## 参考文献

1. Xia G S, Bai X, Ding J, et al. DOTA: A Large-Scale Dataset for Object Detection in Aerial Images. CVPR, 2018.
2. Sun X, Wang P, Wang C, et al. FAIR1M: A Benchmark Dataset for Fine-Grained Object Recognition in High-Resolution Remote Sensing Imagery. ISPRS Journal of Photogrammetry and Remote Sensing, 2022, 184: 116--130.
3. Cheng G, Han J, Zhou P, et al. Learning Rotation-Invariant Convolutional Neural Networks for Object Detection in VHR Optical Remote Sensing Images. IEEE Transactions on Geoscience and Remote Sensing, 2016, 54(12): 7405--7415.
4. Cheng G, Yuan X, Yao X, et al. Towards Large-Scale Small Object Detection: Survey and Benchmarks. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2023, 45(11): 13467--13488.
5. Xie X, Cheng G, Wang J, Yao X, Han J. Oriented R-CNN for Object Detection. ICCV, 2021.
6. Lyu C, Zhang W, Huang H, et al. RTMDet: An Empirical Study of Designing Real-Time Object Detectors. arXiv:2212.07784, 2022.
7. Yang X, Yan J. Arbitrary-Oriented Object Detection with Circular Smooth Label. ECCV, 2020.
8. Yang X, Hou L, Zhou Y, et al. Dense Label Encoding for Boundary Discontinuity Free Rotation Detection. CVPR, 2021.
9. Yu Y, Yang X, Li Q, et al. Phase-Shifting Coder: Predicting Accurate Orientation in Oriented Object Detection. CVPR, 2023.
10. Yang X, Yan J, Ming Q, et al. Rethinking Rotated Object Detection with Gaussian Wasserstein Distance Loss. ICML, 2021.
11. Yang X, Zhou Y, Zhang G, et al. Learning High-Precision Bounding Box for Rotated Object Detection via Kullback-Leibler Divergence. NeurIPS, 2021.
12. Zeng Y, Chen Y, Yang X, Li Q, Yan J. ARS-DETR: Aspect Ratio-Sensitive Detection Transformer for Aerial Oriented Object Detection. arXiv:2303.04989, 2023.
13. El-Yaniv R, Wiener Y. On the Foundations of Noise-Free Selective Classification. Journal of Machine Learning Research, 2010, 11: 1605--1641.
14. Geifman Y, El-Yaniv R. Selective Classification for Deep Neural Networks. NeurIPS, 2017.
15. Geifman Y, Uziel G, El-Yaniv R. SelectiveNet: A Deep Neural Network with an Integrated Reject Option. ICML, 2019.
16. Guo C, Pleiss G, Sun Y, Weinberger K Q. On Calibration of Modern Neural Networks. ICML, 2017.
17. Küppers F, Kronenberger J, Shantia A, Haselhoff A. Multivariate Confidence Calibration for Object Detection. CVPR Workshops, 2020.
18. Vovk V, Gammerman A, Shafer G. Algorithmic Learning in a Random World. Springer, 2005.
19. Bates S, Angelopoulos A N, Lei L, Malik J, Jordan M I. Distribution-Free, Risk-Controlling Prediction Sets. Journal of the ACM, 2024.
20. Angelopoulos A N, Bates S, Fisch A, Lei L, Schuster T. Conformal Risk Control. ICLR, 2024.
21. Angelopoulos A N, Bates S, Jordan M I, Malik J. Learn Then Test: Calibrating Predictive Algorithms to Achieve Risk Control. arXiv:2110.01052, 2021.
22. Andéol L, Fel T, de Grancey F, Mossina L. Conformal Object Detection. arXiv:2308.16005, 2023.
23. Wang G, Li W, Aertsen M, et al. Aleatoric Uncertainty Estimation with Test-Time Augmentation for Medical Image Segmentation with Convolutional Neural Networks. Neurocomputing, 2019, 338: 34--45.
24. Snow R, O'Connor B, Jurafsky D, Ng A Y. Cheap and Fast—But Is It Good? Evaluating Non-Expert Annotations for Natural Language Tasks. EMNLP, 2008.
25. Plank B. The “Problem” of Human Label Variation: On Ground Truth in Data, Modeling and Evaluation. EMNLP, 2022.
26. Hoeffding W. Probability Inequalities for Sums of Bounded Random Variables. Journal of the American Statistical Association, 1963, 58(301): 13--30.
27. Bentkus V. On Hoeffding's Inequalities. The Annals of Probability, 2004, 32(2): 1650--1673.
28. Efron B, Tibshirani R J. An Introduction to the Bootstrap. Chapman & Hall/CRC, 1993.


## r010 固定剂量统计闭环（新增）

本节基于同一套 full post-NMS 预测与完整 classwise evaluator，仅改变角度并重新匹配。剂量为 0、2、5、10、15、20、25、30 度，主分析域为 GT aspect ratio≥2.1。P 轨道固定施加正向扰动，D 轨道使用 dose=0 的固定匹配方向，仅作 GT-directed diagnostic upper bound；S 轨道独立计算正负两方向并取算术平均，因此是本节不挑方向的检验。

本轮仅支持描述性结论：在若干 Core 单元中 AP75 比 AP50 对剂量更敏感，但统一 knee、因果机制、NMS 效应和可部署选择器均不由本实验得到。完整的 paired AP bootstrap、风险事件和 baseline-cohort 生存表见随附复算表；S 轨道保留正负分量，SODA-A 的 tile/mother-scene 交叉限制仍然存在。严格统计门控状态为 `INCONCLUSIVE_MECHANISM_R010`，因此不把该结果写成广泛风险控制方法。
