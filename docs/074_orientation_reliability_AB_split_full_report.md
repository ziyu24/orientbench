# Orientation Reliability A/B 拆篇总报告：通用测量与风险控制，以及 PSC 机制与排序修复

## 目录

- 第一部分：A/B 拆篇理由与科学边界
  - 1. 两条科学问题为何不同
  - 2. 贡献形式为何不同
  - 3. 非重叠发表边界
  - 4. 独立机制线的证据是否充分
- 第二部分：A 篇完整中文正式论文
  - 论文题目、摘要与关键词
  - 1. 引言
  - 2. 相关工作
  - 3. 问题定义
  - 4. 朝向可靠性测量协议
  - 5. 几何敏感性与归一化严重事件
  - 6. 图像级有限样本风险控制
  - 7. 实验设置
  - 8. 实验结果
  - 9. 讨论与局限性
  - 10. 结论
  - 参考文献
- 第三部分：B 篇完整研究计划
  - 1. 科学问题与研究边界
  - 2. 已有事实、当前解释与未证假说
  - 3. 有限机制假说
  - 4. 候选可靠性分数
  - 5. 强制基线与非平凡性审计
  - 6. 干预设计
  - 7. 数据、指标与统计
  - 8. 成功条件与失败分支
  - 9. 与 A 篇的资产边界
  - 10. 阶段化执行方案

---

# 第一部分：A/B 拆篇理由与科学边界

## 1. 两条科学问题本质不同

A 篇研究的是**通用的朝向可靠性测量问题**。它不要求检测器采用某一种角度头，而是回答：旋转框朝向误差应如何按 $180^\circ$ 周期定义；AP@0.5 为何会在特定长宽比和 IoU 阈值下弱感知显著角度错误；如何由共中心、同尺度矩形的几何关系定义形状归一化的严重事件；如何使用 NRC、AURC 和风险—覆盖曲线评价任意排序分数；如何把完整图像而非相关实例作为可交换单位建立有限样本风险保证；以及真人双标分歧如何限制 1.5°--2°、5° 和 10° 风险预算的语义。

B 篇研究的是**PSC 特定的机制与修复问题**。它回答：充分收敛后 `phase_mod` 为何跨数据集、跨随机种子稳定反序；相位向量模长是否具有可识别的不确定性语义；径向缩放、周期解缠、调制阈值和多频一致性如何改变解码与排序；以及能否构造不依赖目标域真值、推理端可得、非 `phase_mod` 简单取负或单调变换的新分数，在不改变框、类别、NMS 集合和 AP 的前提下修复可靠性排序。

因此，两篇论文的因变量也不同。A 篇的主要对象是跨检测器协议、风险事件与有限样本控制；B 篇的主要对象是 PSC 内部相位变量、可干预机制和推理侧排序分数。A 篇可以在没有 PSC 的场景中独立成立，B 篇则必须以 PSC 的编码结构为研究对象。

## 2. 贡献形式不同

A 篇的贡献形式是 measurement protocol、evaluation methodology、finite-sample risk control、geometry analysis 与 annotation analysis。它强调定义是否正确、统计单位是否正确、证据是否跨检测族成立以及结论的噪声边界。

B 篇的贡献形式是 model-specific mechanism、intervention、uncertainty semantics 与 reliability-score repair。它强调变量能否被干预、机制是否可证伪、新分数是否非平凡，以及排序改善能否在保持检测输出不变时成立。

把两条线合并会产生六个具体问题：

1. 从完整评测器扰动、几何推导、风险—覆盖、图像级统计到 PSC 径向干预，主线过长。
2. 读者难以判断核心贡献究竟是通用协议还是 PSC 修复方法。
3. PSC 的网络内部机制会挤压通用协议所需的定义、证明条件、消融和人工标注边界。
4. 通用协议容易被误解为 PSC 专用诊断，而事实上它已在多个检测族和四个数据集上成立。
5. 相同的 PSC 动机数据若同时承担协议验证和机制证明，会失去“现象—干预—修复”的证据层次。
6. 对一篇论文的评审标准会混杂：协议论文要求统计有效性和适用边界，机制论文要求可干预原因和非平凡方法增益。

## 3. 拆篇不是为了重复发表

两篇的主表、方法公式和科学主张严格分离。

**A 篇保留：**

- `phase_mod` 在 DIOR-R、SODA-A、FAIR1M 三个数据集上的反序现象，作为“检测置信不等于角度置信”的简洁观察；
- DCL native signal informative、CSL margin 接近随机的对照，用于说明现象是 head-specific；
- 一段说明独立干预研究支持结构性解释，但不提供干预表、新分数公式或修复结果；
- 通用测量协议、图像级风险控制、完整验证集扰动、几何归一化事件、DOTA 结果和真人双标分析。

**A 篇删除：**径向缩放详细实验、wrapping/modulation 条件表、新机制分数公式、`negative_phase_mod` 详细比较、非平凡性主表和 PSC 排序修复方法。

**B 篇独占：**PSC 径向/切向干预、wrapping 与 modulation threshold、多频一致性、unwrap energy gap、phase-direction margin、TTA phase-direction consistency、新分数对 `negative_phase_mod` 的严格比较，以及保持框、类别和 AP 不变的排序修复。

**B 篇不重复：**A 篇的完整通用协议表、完整图像级风险控制表、完整 DOTA/DIOR-R/FAIR1M/SODA-A benchmark 和人工双标主分析。B 篇只简要引用 NRC 定义与 PSC 三数据集反序这一动机事实。

## 4. 独立机制线的最低证据已经满足

证据链不是来自初步训练。等预算、逐 head 调参且充分收敛的三随机种子结果显示：DIOR-R 上 PSC `phase_mod` 的角度误差 NRC 为 1.2073、1.2024、1.2176，SODA-A 为 1.1316、1.1338、1.1259，所有区间均在随机基线 1 之上。FAIR1M 独立扩展的三种子均值为 1.1222，三个种子的图像级区间下界也均高于 1。DCL 在 DIOR-R、SODA-A、FAIR1M 的均值分别约为 0.249、0.373、0.551，是明确的 informative 反例；CSL 随种子波动并总体接近随机，不支持“所有角度编码器都反序”。检测分数通常仍有信息，进一步表明问题集中在 PSC 原生模长的风险语义，而非整个检测器完全失效。

径向干预 $z'=kz$ 使用固定网格 $k\in\{0.25,0.50,0.75,0.90,1.00,1.10,1.25,1.50,2.00,4.00\}$。六个 PSC 单元均进入分支 B：跨单元最大 decoded-angle 中位/p95 变化达到 8.6623°/40.1550°，实际 head loss 的最大相对变化达到 20.8734，说明解码或损失对径向并非普遍不变。基于该分支定义的四个候选分数在 DIOR-R 与 SODA-A 的可用单元上均优于 `negative_phase_mod`，配对图像 bootstrap 的 NRC、AURC、Risk@70、Risk@90 差值区间上界均小于 0。非平凡性审计又排除了简单取负、单调映射、温度缩放和 detection-score 复制；候选全部为推理端信号，不依赖目标域真值拟合。排序变化复用同一预测身份，不改变 box、class、NMS 或 AP。

这组事实足以形成一条独立、可评审的机制研究线，但它仍不是通用角度编码理论：现有证据不能推出所有 PSC 实现必然失效，不能推出 PSC angle head 本身错误，也不能推广为所有角度编码器的统一不确定性定理。

---

# 第二部分：A 篇完整中文正式论文

# 旋转目标检测中的朝向可靠性：几何归一化测量与图像级有限样本风险控制

## 摘要

平均精度综合衡量旋转目标检测的分类、定位和排序，却不能单独回答预测角度是否可信。本文建立一套与检测架构解耦的朝向可靠性协议。首先，在六个完整验证单元上，仅旋转已匹配预测并保持其与对应真值的旋转 IoU 大于 0.5，随后用完整评测器重新匹配。六个单元的 AP@0.5 均保持不变，而 AP@0.75 显著下降，平均角度误差由 4.63°--9.09° 增至 34.42°--40.54°。其次，我们用共中心、同尺度全等矩形定义 $\delta_{0.75}(a)$，由 IoU=0.75 与 15° 容忍语义反解得到长宽比约 2.1，将 `ar>=2.1` 作为唯一主分析域，并定义形状归一化严重事件。再次，我们以 NRC、AURC、Risk@70/90 评价任意置信分数，并把完整图像作为可交换单位，对图像内保留预测的严重事件比例应用固定序列 Learn-Then-Test 和 Hoeffding--Bentkus 有界损失上界。六个 primary families 在三个风险预算下共获得 18 个非退化选择；审计集非空图像比例为 35.38%--62.54%，而实例独立反事实给出过于乐观的上界。最后，两名真实标注者独立互盲标注 600 个目标。450 对数值角度的平均圆周分歧为 2.3112°，图像聚类 bootstrap 95% 区间为 1.9970°--2.7854°；P(>5°)=8.00%，P(>10°)=0.89%。这说明 1.5°--2° 均值预算只能作 label-noise-aware 解读，5° 是有意义但 noise-sensitive 的 fine-risk，10° 具有更清楚的 severe-risk 语义。本文贡献是测量与有限样本风险控制协议，不是目标域可直接部署的选择器。

**关键词：**旋转目标检测；朝向可靠性；风险—覆盖；选择性预测；几何归一化风险；有限样本风险控制；人工标注噪声

## 1. 引言

旋转目标检测以 $(c_x,c_y,w,h,\theta)$ 描述目标，广泛用于遥感、场景文字和工业视觉。现有研究通常以 AP@0.5 或 mAP 为主要指标。ARS-DETR 已指出 AP@0.5 对角度偏差可能具有较大容忍度 [13]，但“AP@0.5 不适于高精度朝向评价”仍需要三个层次的补充：其一，必须用完整评测器而非只在已匹配实例上计算代理指标；其二，必须解释长宽比和 IoU 阈值如何共同决定角度容忍区；其三，必须给出独立于 AP 的排序度量与有限样本风险保证。

角度可靠性还受到近方形退化和图像内相关性的影响。接近正方形的框在旋转后几何变化很小，长轴方向本身不稳定；同一遥感图像中大量密集目标共享场景、尺度和成像条件，不能被当作独立伯努利样本。若忽略这两点，极低的实例尾率可能来自几何不可辨识样本的混入，有限样本上界也会因虚高的有效样本量而过度乐观。

本文提出完整的 orientation reliability protocol，贡献包括：

1. 通过完整验证集的受约束角度扰动与反向中心/尺度扰动，证明 AP 与角度风险在特定几何区间不等价，而不作“mAP 不看角度”的绝对化表述。
2. 从共中心矩形旋转 IoU 推导 `ar>=2.1` 主分析域，并定义随长宽比自适应的几何归一化严重事件。
3. 以 risk-coverage、AURC 和 NRC 衡量选择分数的角度排序质量，同时报告固定覆盖风险、保留数和保留比例。
4. 以完整图像为可交换单位，构造固定序列 Learn-Then-Test 与 Hoeffding--Bentkus 有界损失控制；精确二项只用于二元图像次级事件。
5. 在 DIOR-R、FAIR1M、SODA-A、DOTA 和多个检测族上验证协议，并用真实双标量化风险阈值的标签噪声边界。

## 2. 相关工作

**选择性预测与风险—覆盖。** 带拒识选项的分类研究了在覆盖率降低时控制风险的问题 [14--16]。风险—覆盖曲线把“保留多少预测”和“保留预测有多危险”联合起来。本文把这一思想用于旋转框角度，不把 NRC<1 等同于概率校准。

**保形推断与风险控制。** 经典保形预测在可交换性下提供有限样本覆盖 [17,18]。RCPS 将保证推广到一般损失 [19]；Learn-Then-Test 将候选参数选择表述为多重检验 [20]；Conformal Risk Control 控制单调损失的期望 [21]。目标检测中的 conformal bounding-box 方法主要构造坐标预测区间 [22,23]，而本文控制的是保留旋转预测的朝向风险。加权保形方法说明协变量漂移需要额外条件和修正 [24]，因此本文不宣称跨域严格保证。

**检测器校准。** 温度缩放等方法研究分类置信度 [25]；D-ECE 将位置和框尺度纳入目标检测校准 [26]。这些方法关注置信概率与正确率的一致性，本文关注分数对角度损失的排序能力，两者互补但不等价。

**旋转检测、周期性和近方形问题。** DOTA、DIOR、FAIR1M 和 SODA 为遥感检测提供了多样场景 [1--4]。Oriented R-CNN 与 RTMDet 代表不同检测范式 [5,6]。CSL、DCL 和 PSC 分别以圆滑标签、稠密编码与相位编码处理角度周期性和边界问题 [7--9]。GWD 与 KLD 将旋转框表示为二维高斯并从分布距离优化高精度框 [10,11]；调制损失和 square-like 研究直接处理边界与边交换 [12]。这些工作主要改善训练目标，本文从评价侧定义“朝向何时可辨识、分数是否能排序角度风险”。

**测试时不确定性。** MC dropout 与测试时增强可从重复预测的分散程度构造经验不确定性 [27,28]。旋转角具有 $180^\circ$ 周期，本文在 $\theta\mapsto2\theta$ 圆域计算 TTA circular variance。

## 3. 问题定义

### 3.1 le90 长边角与圆周距离

将旋转框规范化为长边角：若 $w<h$，交换 $w,h$ 并令角度增加 $90^\circ$。对预测角 $\hat\theta_i$ 与参考角 $\theta_i$，定义

$$
d_{180}(\hat\theta_i,\theta_i)
=\min_{k\in\mathbb Z}|\hat\theta_i-\theta_i+180^\circ k|
\in[0^\circ,90^\circ].
$$

记 $e_i=d_{180}(\hat\theta_i,\theta_i)$。该定义只描述 OBB 几何长轴，不判断物体头尾，不涉及 semantic heading。

### 3.2 合格预测与主掩码

可靠性分析的合格实例是与真值同类、一对一匹配且旋转 IoU 不低于 0.5 的预测。令真值长宽比

$$a_i=\frac{\max(w_i,h_i)}{\min(w_i,h_i)}.$$

主分析使用 $a_i\ge2.1$，并排除预测框或真值框处于近方形数值不稳定状态的匹配。评价掩码中的长宽比来自 matched GT；选择器可以使用的几何特征只来自预测框，二者不得混用。

## 4. 朝向可靠性测量协议

### 4.1 风险—覆盖曲线

给定“越大越可信”的分数 $s_i$，按 $s_i$ 降序排列。覆盖率 $c\in(0,1]$ 下保留前 $\lceil cn\rceil$ 个实例，角度风险为

$$
R_s(c)=\frac{1}{\lceil cn\rceil}\sum_{i\in\operatorname{Top}(s,c)} e_i.
$$

离散覆盖网格 $\mathcal C$ 上的面积定义为

$$
\operatorname{AURC}(s)=\frac{1}{|\mathcal C|}\sum_{c\in\mathcal C}R_s(c).
$$

Risk@70 与 Risk@90 分别为 $R_s(0.7)$ 和 $R_s(0.9)$。令 oracle 按误差从小到大排序，random 为随机排序期望，则

$$
\operatorname{NRC}(s)=
\frac{\operatorname{AURC}(s)-\operatorname{AURC}(\mathrm{oracle})}
{\operatorname{AURC}(\mathrm{random})-\operatorname{AURC}(\mathrm{oracle})}.
$$

NRC=0 是理想排序，NRC=1 是随机排序，NRC>1 是反序，NRC<1 仅表示 informative 或 non-reversed。NRC 不是概率校准误差。

### 4.2 Score menu

本文统一比较以下分数：

1. **Detection score：**后处理后检测置信度 $s_i^{det}$。
2. **TTA circular consistency：**对 $M$ 个增强视图映射回原图的角度 $\tilde\theta_{im}$，定义
   $$V_i^{circ}=1-\left|\frac1M\sum_{m=1}^M e^{\mathrm i2\tilde\theta_{im}}\right|,$$
   排序分数为 $-V_i^{circ}$。
3. **原生角度信号：**PSC 的 `phase_mod`、CSL 的 softmax top1-top2 margin、DCL 的 bit margin。它们只沿用各 head 的既定定义。
4. **线性几何基线：**$\beta_0+\beta_1s_i^{det}+\beta_2\log\hat a_i$，以及加入 $\beta_3\log\hat q_i$ 的版本，其中 $\hat a_i$ 和 $\hat q_i$ 是预测框长宽比与面积。
5. **非线性几何分数：**以预测端的 score、宽高、长宽比和尺度为输入的非线性排序器。其拟合目标是目标域真值角度误差，因此只能作为 diagnostic/calibration upper bound。

选择器拟合、保形标定和最终审计按图像相互独立：第一部分只拟合分数，第二部分只选择风险阈值，第三部分只报告结果。目标域真值拟合与数据独立性是两个不同问题；独立划分不能把 geometry score 变成 deployable method。

## 5. 几何敏感性与归一化严重事件

### 5.1 旋转 IoU 的角度容忍宽度

考虑共中心、同尺度、面积归一且长宽比为 $a$ 的两个全等矩形，其中一个相对另一个旋转 $\delta$。记多边形交并比为 $J(\delta;a)$，定义

$$
\delta_\tau(a)=\inf\{\delta\in[0^\circ,90^\circ]:J(\delta;a)<\tau\}.
$$

采用 le90 长边角和 $0.001^\circ$ 数值求解精度，取第一处严格交叉。$a\to1$ 时角度可辨识性退化；$a$ 增大时，达到同一 IoU 损失所需角度减小。

| 长宽比 $a$ | $\delta_{0.5}(a)$ | $\delta_{0.75}(a)$ |
|---:|---:|---:|
| 1.0 | 不跌破 | 25.5285° |
| 1.3 | 不跌破 | 23.1417° |
| 1.6 | 69.6358° | 19.6727° |
| 2.0 | 47.4084° | 16.0548° |
| 2.5 | 34.5475° | 12.9594° |
| 4.0 | 19.9234° | 8.1577° |
| 8.0 | 9.6457° | 4.0893° |

令“15° 朝向偏差在 IoU=0.75 下应产生几何后果”，反解 $\delta_{0.75}(a)=15^\circ$ 得到 $a\approx2.15$，报告主阈值取 2.1。`ar>=1.6` 与 `ar>=1.3` 只用于敏感性检查。

### 5.2 几何归一化严重事件

主事件定义为

$$Y_i=\mathbf1\{e_i>\delta_{0.75}(a_i)\}.$$

该事件表达“角度误差超过同形状矩形在 IoU=0.75 下的容忍角”。它不表示实际预测框与真值框一定因角度而跌破 0.75，因为实际框还包含中心和尺度误差。固定事件 $e_i>5^\circ,10^\circ,15^\circ$ 只作 sensitivity。

## 6. 图像级有限样本风险控制

### 6.1 主损失与次级事件

完整 evaluation image 是可交换单位。对阈值 $t$，令 $S_I(t)$ 为图像 $I$ 中满足主掩码且分数不低于 $t$ 的预测，定义

$$
L_I(t)=
\begin{cases}
|S_I(t)|^{-1}\sum_{i\in S_I(t)}Y_i,&|S_I(t)|>0,\\
0,&|S_I(t)|=0.
\end{cases}
$$

$L_I(t)\in[0,1]$。次级二元事件为

$$Z_I(t)=\mathbf1\{\exists i\in S_I(t):Y_i=1\}.$$

只有 $Z_I$ 使用 exact Clopper--Pearson 上界；$L_I$ 不使用 exact binomial。

### 6.2 固定序列 Learn-Then-Test

风险预算取 $\alpha\in\{0.03,0.05,0.10\}$，置信失败概率 $\delta=0.10$。候选覆盖按 0.1 到 1.0 的固定序列排列，阈值由拟合子集定义，在独立标定图像上计算 Hoeffding--Bentkus 单侧上界 $U_{HB}(t;\delta)$。从低覆盖到高覆盖顺序检验

$$H_t:\mathbb E[L_I(t)]>\alpha,$$

以固定序列控制 family-wise error rate；遇到首个不能拒绝的候选即停止。审计图像完全不参与阈值选择。

实例级尾率只报告

$$
\widehat R_{inst}(t)=
\frac{\sum_I\sum_{i\in S_I(t)}Y_i}{\sum_I|S_I(t)|},
$$

并以图像为 cluster 重采样给出区间。图像 bootstrap 每次抽取图像及其全部实例，保留图像内相关性。

## 7. 实验设置

实验覆盖 DIOR-R、FAIR1M-v1.0、SODA-A 与 DOTA-v1.0，检测器包括相位编码 RetinaNet、Oriented R-CNN 和 Rotated RTMDet，原生角度信号对照另含 CSL 与 DCL。非 DOTA 数据采用 trainval/test 口径；DOTA 采用本地 train/val，并只报告完整验证集。AP 由旋转多边形 IoU、逐类分数排序、贪心匹配和 VOC 插值计算。

完整验证集扰动从原预测、完整真值和 NMS 后集合出发。仅对已匹配预测沿远离参考角方向施加保持对应旋转 IoU 大于 0.5 的最大旋转；中心、尺度、分数、类别及未匹配预测均保持不变。扰动后重新执行完整匹配和 AP 计算，因而不是 matched-only AP 代理。FP@0.5 集合在协议约束下不变，报告 $\Delta FP=0$。

## 8. 实验结果

### 8.1 完整验证集扰动

| 数据集 / 检测器 | AP50 原始 | AP50 扰动 | $\Delta$AP50 | AP75 原始 | AP75 扰动 | 平均角误差原始→扰动 | $\Delta$FP@0.5 |
|---|---:|---:|---:|---:|---:|---:|---:|
| DIOR-R / PSC | 0.5368 | 0.5368 | 0.0000 | 0.3503 | 0.0384 | 8.947°→39.189° | 0 |
| DIOR-R / Oriented R-CNN | 0.6448 | 0.6448 | 0.0000 | 0.4275 | 0.0484 | 8.665°→40.041° | 0 |
| DIOR-R / Rotated RTMDet-S | 0.6462 | 0.6462 | 0.0000 | 0.4515 | 0.0532 | 9.087°→40.541° | 0 |
| FAIR1M / PSC | 0.3462 | 0.3462 | 0.0000 | 0.2422 | 0.0665 | 4.631°→36.516° | 0 |
| SODA-A / PSC | 0.5991 | 0.5991 | 0.0000 | 0.2735 | 0.0448 | 5.230°→34.416° | 0 |
| SODA-A / Oriented R-CNN | 0.7295 | 0.7295 | 0.0000 | 0.3805 | 0.0278 | 5.148°→35.893° | 0 |

AP@0.5 不变而 AP@0.75 和角度误差显著变化，说明 IoU=0.5 在这些长宽比与扰动幅度下形成弱敏感区。结论是“AP@0.5 在特定几何区可能弱感知严重角度误差”，而不是“mAP 不看角度”。固定角度而扰动中心/尺度的反向实验又显示 AP@0.5 可以在角度不变时下降，两向证据共同表明二者不等价。

### 8.2 `ar>=2.1` 主口径与 detection-score 排序

| 单元 | 数据集 / 检测器 | 保留数 | 保留率 | mask 剔除率 | NRC | AURC | Risk@70 | Risk@90 |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| A | DIOR-R / PSC | 25,065 | 57.16% | 42.84% | 0.6082 | 1.2075 | 1.4346 | 1.5866 |
| B | DIOR-R / Oriented R-CNN | 27,671 | 57.78% | 42.22% | 0.5741 | 1.3528 | 1.5598 | 1.7512 |
| C | DIOR-R / RTMDet-S | 27,385 | 57.19% | 42.81% | 0.4653 | 1.3786 | 1.6090 | 1.9066 |
| D | FAIR1M / PSC | 15,120 | 57.91% | 42.09% | 0.9379 | 2.2225 | 2.2998 | 2.3004 |
| E | SODA-A / PSC | 101,102 | 64.16% | 35.84% | 0.8113 | 1.7827 | 1.8733 | 1.9817 |
| F | SODA-A / Oriented R-CNN | 120,925 | 62.90% | 37.10% | 0.6878 | 1.8254 | 2.0645 | 2.2053 |
| G | DOTA / Oriented R-CNN | 33,029 | 67.56% | 32.44% | 0.7544 | 1.5543 | 1.6859 | 1.7716 |
| H | DOTA / RTMDet-M | 34,383 | 66.46% | 33.54% | 0.7113 | 1.4932 | 1.6363 | 1.7288 |

Detection score 在八个单元均为 informative，但 NRC 从 0.4653 到 0.9379，说明其角度排序能力并不稳定。主口径下 geometry-normalized severe rate 为 0.19%--1.67%；固定 $>5^\circ$ 尾率为 5.03%--10.88%，$>10^\circ$ 为 0.34%--1.91%，$>15^\circ$ 为 0.05%--0.91%。

### 8.3 较低长宽比阈值敏感性

| 单元 | NRC (`ar>=2.1`) | NRC (`ar>=1.6`) | NRC (`ar>=1.3`) | 方向结论 |
|---|---:|---:|---:|---|
| A | 0.6082 | 0.5644 | 0.5716 | informative |
| B | 0.5741 | 0.5271 | 0.5427 | informative |
| C | 0.4653 | 0.4153 | 0.4230 | informative |
| D | 0.9379 | 0.9059 | 0.9322 | informative，接近随机 |
| E | 0.8113 | 0.8963 | 0.9778 | informative，较低阈值更接近随机 |
| F | 0.6878 | 0.7055 | 0.7295 | informative |
| G | 0.7544 | 0.6866 | 0.7005 | informative |
| H | 0.7113 | 0.6353 | 0.6271 | informative |

较低阈值改变数值并在部分原生信号上改变 near-random/reversed 标签，因此不能替代原则化主口径；但 detection score 的总体方向一致。

### 8.4 固定尺寸分箱的几何诊断

在预测框面积定义的 small/medium/large 固定分箱内，对比 detection score、score+$\log(ar)$ 线性、score+$\log(ar)$+$\log(size)$ 线性和 nonlinear geometry。差值定义为 NRC(linear score+ar+size)$-$NRC(nonlinear)，正值且图像 cluster bootstrap 区间下界大于 0 表示非线性分数更优。

| 单元 | 尺寸 | n | det | +ar | +ar+size | nonlinear | 差值 [95% CI] |
|---|---|---:|---:|---:|---:|---:|---:|
| A | small | 15,234 | 0.7027 | 0.7065 | 0.7065 | 0.7050 | 0.0020 [-0.0205, 0.0248] |
| A | medium | 7,589 | 0.5838 | 0.8799 | 0.7384 | 0.5991 | 0.1388 [0.0943, 0.1805] |
| A | large | 2,242 | 0.5897 | 0.6479 | 0.6233 | 0.4719 | 0.1510 [0.1034, 0.1983] |
| B | small | 17,081 | 0.6538 | 0.7077 | 0.6742 | 0.6324 | 0.0419 [0.0085, 0.0780] |
| B | medium | 8,030 | 0.6608 | 0.9785 | 0.8372 | 0.6172 | 0.2206 [0.1777, 0.2617] |
| B | large | 2,560 | 0.5388 | 0.7021 | 0.6627 | 0.4777 | 0.1850 [0.1389, 0.2295] |
| C | small | 16,836 | 0.5621 | 0.5796 | 0.5797 | 0.5413 | 0.0386 [0.0222, 0.0553] |
| C | medium | 7,859 | 0.5578 | 0.8305 | 0.7261 | 0.5603 | 0.1642 [0.1312, 0.1977] |
| C | large | 2,690 | 0.4236 | 0.4562 | 0.4367 | 0.3587 | 0.0781 [0.0464, 0.1070] |
| D | small | 13,765 | 0.9661 | 0.7735 | 0.7735 | 0.7368 | 0.0364 [0.0000, 0.0784] |
| D | medium | 1,136 | 0.9573 | 0.6655 | 0.6594 | 0.7107 | -0.0513 [-0.1216, 0.0254] |
| E | small | 99,811 | 0.7848 | 0.5991 | 0.5802 | 0.5400 | 0.0404 [0.0270, 0.0538] |
| E | medium | 1,291 | 1.3570 | 0.4422 | 0.4384 | 0.3845 | 0.0538 [0.0177, 0.0923] |
| F | small | 119,367 | 0.6858 | 0.5877 | 0.5577 | 0.5430 | 0.0146 [0.0048, 0.0256] |
| F | medium | 1,558 | 0.9495 | 0.4129 | 0.4171 | 0.4400 | -0.0232 [-0.0789, 0.0198] |

15 个可用分箱中 11 个显著支持 nonlinear，证据覆盖 A/B/C/E，并非单一尺寸层驱动。因此非线性优势不能完全由 size prior 解释。另一方面，该分数使用目标域 GT angle-error 拟合，仍只能是 diagnostic/calibration upper bound；它不是 fully deployable 方法，也不是通用默认。

### 8.5 图像级有限样本结果

六个 detection-score families 与三个风险预算形成 18 个 primary families，均获得非退化选择。表中每个单元在三个预算下选择相同的最高候选覆盖，故按单元合并报告。

| 单元 | $n_{cal}$ 图像 | $n_{audit}$ 图像 | 标定 HB UCB | 审计 mean image risk | 非空图像比例 | mean instance coverage | 审计保留实例 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A | 3,003 | 5,900 | 0.01538 | 0.01208 | 59.22% | 59.22% | 25,065 |
| B | 3,003 | 5,900 | 0.01614 | 0.01325 | 61.69% | 61.69% | 27,669 |
| C | 3,003 | 5,900 | 0.02588 | 0.02153 | 62.54% | 62.54% | 27,383 |
| D | 1,137 | 2,142 | 0.00536 | 0.00349 | 57.00% | 57.00% | 15,120 |
| E | 5,717 | 11,522 | 0.00308 | 0.00163 | 35.38% | 35.38% | 101,101 |
| F | 5,717 | 11,522 | 0.00301 | 0.00223 | 35.76% | 35.76% | 120,923 |

非空图像比例和按全部图像平均的实例覆盖为 35.38%--62.54%；在存在合格实例的条件口径下，保留实例比例约为 99.99%--100%。因此 target coverage=1 不等于覆盖全部图像：大量完整图像没有合格匹配实例，仍以 $L_I=0$ 进入正式总体。新图像级 UCB 比旧 instance-i.i.d. 反事实更保守。例如单元 A 的图像级 UCB 为 0.01538，而实例独立反事实为 0.00866，保留实例数相对图像数造成约 4.43 倍有效样本量虚高。并非所有分数和预算都必然有实用覆盖，跨数据集也没有无条件保证。

### 8.6 DOTA clean full-validation

| 检测器 | AP50 | AP75 | 主口径保留数/率 | NRC | AURC | Risk@70 | Risk@90 | mean angle error |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Oriented R-CNN | 0.7061 | 0.4517 | 33,029 / 67.56% | 0.7544 | 1.5543 | 1.6859 | 1.7716 | 1.834° |
| Rotated RTMDet-M | 0.7161 | 0.4868 | 34,383 / 66.46% | 0.7113 | 1.4932 | 1.6363 | 1.7288 | 1.814° |

两单元均使用 55,804 个完整验证真值。历史表在较宽掩码下给出的 NRC 为 0.6912/0.6458；上表采用统一 `ar>=2.1` 后的权威主口径，不能混用。

### 8.7 PSC、CSL 与 DCL 的简洁观察

| 数据集 | head / native signal | 三种子 NRC | 三种子 detection-score NRC | 解释 |
|---|---|---|---|---|
| DIOR-R | PSC / phase_mod | 1.2073, 1.2024, 1.2176 | 0.5906, 0.5972, 0.6049 | 稳定反序 |
| DIOR-R | CSL / margin | 0.8663, 0.9254, 1.1210 | 0.8403, 0.8651, 1.0856 | 跨种子不稳定、近随机 |
| DIOR-R | DCL / bit margin | 0.2445, 0.2436, 0.2599 | 0.6375, 0.6436, 0.6315 | informative |
| SODA-A | PSC / phase_mod | 1.1316, 1.1338, 1.1259 | 0.8065, 0.8409, 0.8595 | 稳定反序 |
| SODA-A | CSL / margin | 1.0046, 0.9416, 1.1162 | 1.0913, 1.1187, 0.9564 | 近随机、方向不稳 |
| SODA-A | DCL / bit margin | 0.3699, 0.3781, 0.3702 | 0.8892, 0.8945, 0.8900 | informative |

FAIR1M 三种子均值进一步给出：PSC angle-error NRC=1.122、geometry-event NRC=1.326、AURC=2.462、Risk@70/90=2.240/2.232；CSL 为 0.974、1.011、14.362、14.528/14.522；DCL 为 0.551、0.392、2.496、2.872/3.231。PSC 三个种子的 angle-error NRC 区间下界均大于 1；DCL 三种子均低于 1；CSL 不呈稳定反序。该结果只支持 head-specific 观察。独立干预研究支持存在结构性原因，但详细机制和修复不属于本文范围。

### 8.8 真人双标噪声锚点

两名真实标注者对同一 600 个 canonical targets 独立互盲标注，DIOR-R、FAIR1M、SODA-A 各 200。双方都给出数值角度的 primary 对为 450：DIOR-R 122、FAIR1M 169、SODA-A 159。ambiguous 与 skip 不作为 0°。

| 范围 | n | mean [image-cluster 95% CI] | median | p90 | p95 | P(>5°) [CI] | P(>10°) [CI] |
|---|---:|---:|---:|---:|---:|---:|---:|
| Overall | 450 | 2.3112° [1.9970, 2.7854] | 1.6359° | 4.4220° | 5.9359° | 8.00% [5.57, 10.56] | 0.89% [0.22, 1.79] |
| DIOR-R | 122 | 1.6725° [1.4091, 1.9524] | 1.2069° | 3.4602° | 4.5410° | 4.10% | 0.00% |
| FAIR1M | 169 | 2.0655° [1.8128, 2.3369] | 1.6805° | 4.3297° | 5.4238° | 7.69% | 0.00% |
| SODA-A | 159 | 3.0623° [2.2854, 4.2848] | 2.0374° | 5.1520° | 8.0200° | 11.32% | 2.52% |
| `ar>=2.1` | 308 | 2.2823° [1.8674, 2.9426] | 1.6130° | 4.1978° | 5.5860° | 6.82% | 0.65% |

人工分歧给出四条解释边界。其一，1.5°--2° mean angle-risk budget 接近人工分歧地板，只能称为 label-noise-aware mean risk。其二，5° 高于中位数且有实际意义，但 8.00% 人工对仍越界，因此是 noise-sensitive fine-risk。其三，10° 的人工越界率仅 0.89%，具有更清楚的 severe-risk margin。其四，SODA-A 尾部更高，该数据集的 5° 结果必须更克制。

29 个单方无数值目标另行进行匿名盲重检：27 个获得数值角度、2 个仍 ambiguous；27 对 mean=2.2126°、median=1.9302°、p90=3.8216°、p95=4.1811°。重检严格属于 secondary endpoint，不替换 primary。人工 disagreement 不是数据集真实 GT error，不能从模型误差中扣除。corner-jitter 只保留为偏保守的 proxy sensitivity，不能称为真实 $\sigma_{gt}$。

## 9. 讨论与局限性

**AP 与可靠性互补。** AP 衡量检测整体结果，NRC 衡量角度风险排序，图像级风险控制衡量有限标定样本下阈值是否满足风险预算。三者回答不同问题，不应互相替代。

**几何事件优先。** 固定角度对细长和较宽目标的意义不同。$\delta_{0.75}(a)$ 提供统一几何语义，因此作为主事件；5°/10°/15° 只承担可解释敏感性。

**上界与部署边界。** 固定尺寸结果证明预测几何包含超出简单 size prior 的诊断信息，但 nonlinear geometry 使用目标域真值拟合。本文没有证明无需目标域标定的通用 selector，也没有证明跨域有限样本保证。

**样本范围。** 证据覆盖多个检测族和四个数据集，但不是 exhaustive detector matrix。真人标注每数据集 200 个目标足以支持总体锚点、宽粒度数据集比较、主长宽比边界及 5°/10° 解释；不足以支持 rare-class 精确噪声率、每类正式排序、精细 size-bin 因果结论或 p99/p99.9 extreme-tail 主张。

**机制边界。** PSC 模长反序不能推广为所有角度编码器失效。DCL 是明确反例，CSL 也未表现出稳定反序。本文不判断 PSC angle head 本身“错误”，只判断特定原生分数的排序语义。

## 10. 结论

本文给出旋转目标检测朝向可靠性的完整测量与风险控制框架。完整验证集扰动揭示 AP@0.5 在特定几何区对角度弱敏感；共中心矩形分析给出 `ar>=2.1` 主分析域和形状归一化严重事件；NRC、AURC 与风险—覆盖量化选择分数；图像级有界损失避免实例独立假设造成的过度乐观；真人双标则限定了度级风险预算的语义。该协议使“检测是否正确”与“角度是否可信”成为可同时报告但不相互混淆的两个维度。

## 参考文献

1. Xia G S, Bai X, Ding J, et al. DOTA: A Large-Scale Dataset for Object Detection in Aerial Images. CVPR, 2018: 3974--3983.
2. Li K, Wan G, Cheng G, et al. Object Detection in Optical Remote Sensing Images: A Survey and A New Benchmark. ISPRS Journal of Photogrammetry and Remote Sensing, 2020, 159: 296--307.
3. Sun X, Wang P, Wang C, et al. FAIR1M: A Benchmark Dataset for Fine-Grained Object Recognition in High-Resolution Remote Sensing Imagery. ISPRS Journal of Photogrammetry and Remote Sensing, 2022, 184: 116--130.
4. Cheng G, Yuan X, Yao X, et al. Towards Large-Scale Small Object Detection: Survey and Benchmarks. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2023, 45(11): 13467--13488.
5. Xie X, Cheng G, Wang J, et al. Oriented R-CNN for Object Detection. ICCV, 2021: 3520--3529.
6. Lyu C, Zhang W, Huang H, et al. RTMDet: An Empirical Study of Designing Real-Time Object Detectors. arXiv:2212.07784, 2022.
7. Yang X, Yan J. Arbitrary-Oriented Object Detection with Circular Smooth Label. ECCV, 2020: 677--694.
8. Yang X, Hou L, Zhou Y, et al. Dense Label Encoding for Boundary Discontinuity Free Rotation Detection. CVPR, 2021: 15819--15829.
9. Yu Y, Da F. Phase-Shifting Coder: Predicting Accurate Orientation in Oriented Object Detection. CVPR, 2023: 13354--13363.
10. Yang X, Yan J, Ming Q, et al. Rethinking Rotated Object Detection with Gaussian Wasserstein Distance Loss. ICML, 2021: 11830--11841.
11. Yang X, Yang X, Yang J, et al. Learning High-Precision Bounding Box for Rotated Object Detection via Kullback-Leibler Divergence. NeurIPS, 2021: 18381--18394.
12. Qian W, Yang X, Peng S, et al. Learning Modulated Loss for Rotated Object Detection. AAAI, 2021, 35(3): 2458--2466.
13. Zeng Y, Chen Y, Yang X, Li Q, Yan J. ARS-DETR: Aspect Ratio-Sensitive Detection Transformer for Aerial Oriented Object Detection. arXiv:2303.04989, 2023.
14. El-Yaniv R, Wiener Y. On the Foundations of Noise-Free Selective Classification. Journal of Machine Learning Research, 2010, 11: 1605--1641.
15. Geifman Y, El-Yaniv R. Selective Classification for Deep Neural Networks. NeurIPS, 2017.
16. Geifman Y, Uziel G, El-Yaniv R. SelectiveNet: A Deep Neural Network with an Integrated Reject Option. ICML, 2019: 2151--2159.
17. Vovk V, Gammerman A, Shafer G. Algorithmic Learning in a Random World. Springer, 2005.
18. Angelopoulos A N, Bates S. A Gentle Introduction to Conformal Prediction and Distribution-Free Uncertainty Quantification. arXiv:2107.07511, 2021.
19. Bates S, Angelopoulos A, Lei L, Malik J, Jordan M I. Distribution-Free, Risk-Controlling Prediction Sets. Journal of the ACM, 2021, 68(6): 1--34.
20. Angelopoulos A N, Bates S, Candès E J, Jordan M I, Lei L. Learn Then Test: Calibrating Predictive Algorithms to Achieve Risk Control. The Annals of Applied Statistics, 2025, 19(2).
21. Angelopoulos A N, Bates S, Fisch A, Lei L, Schuster T. Conformal Risk Control. ICLR, 2024.
22. Andéol L, Mossina L, Mazoyer A, Gerchinovitz S. Conformal Object Detection by Sequential Risk Control. arXiv:2505.24038, 2025.
23. Mukama B C, Messoudi S, Rousseau S, Destercke S. Copula-Based Conformal Prediction for Object Detection: A More Efficient Approach. Proceedings of Machine Learning Research, 2024, 230: 140--157.
24. Tibshirani R J, Barber R F, Candès E J, Ramdas A. Conformal Prediction Under Covariate Shift. NeurIPS, 2019.
25. Guo C, Pleiss G, Sun Y, Weinberger K Q. On Calibration of Modern Neural Networks. ICML, 2017: 1321--1330.
26. Kuppers F, Kronenberger J, Shantia A, Haselhoff A. Multivariate Confidence Calibration for Object Detection. CVPR Workshops, 2020: 326--327.
27. Gal Y, Ghahramani Z. Dropout as a Bayesian Approximation: Representing Model Uncertainty in Deep Learning. ICML, 2016: 1050--1059.
28. Wang G, Li W, Aertsen M, et al. Aleatoric Uncertainty Estimation with Test-Time Augmentation for Medical Image Segmentation with Convolutional Neural Networks. Neurocomputing, 2019, 338: 34--45.
29. Hoeffding W. Probability Inequalities for Sums of Bounded Random Variables. Journal of the American Statistical Association, 1963, 58(301): 13--30.
30. Bentkus V. On Hoeffding's Inequalities. The Annals of Probability, 2004, 32(2): 1650--1673.
31. Efron B, Tibshirani R J. An Introduction to the Bootstrap. Chapman & Hall/CRC, 1993.

---

# 第三部分：B 篇完整研究计划

## 1. 暂定科学问题与研究边界

核心问题是：**为什么 PSC `phase_mod` 在充分收敛、跨数据集、跨随机种子条件下稳定反序，以及如何构造具有可识别不确定性语义的非平凡推理侧排序分数？**

研究对象限于 PSC 及其相位编码变量。目标不是提高检测 AP，也不是重新训练 detector，而是在固定预测身份、box、class、score 和 NMS 结果的条件下研究角度可靠性排序。主分析域为 `ar>=2.1`，主事件为 geometry-normalized severe event，统计以完整图像 cluster bootstrap 完成。

## 2. 已有事实、当前解释与尚未证明的假说

### 2.1 已有事实

1. K2 full-converged、per-head 等预算调参的三随机种子矩阵复现结局 A：PSC `phase_mod` 在 DIOR-R 与 SODA-A 的 angle-error NRC 均稳定大于 1。
2. FAIR1M 第三数据集三种子均值 NRC=1.1222，三个图像级区间下界均大于 1，跨数据集范围扩展到 DIOR-R、SODA-A、FAIR1M。
3. PSC detection score 在相同端点通常 informative；反序不是整个检测器失去排序信息。
4. DCL bit margin 在三个数据集均 informative，构成“非通用 angle-coder failure”的反例；CSL margin 总体近随机且跨种子不稳定。
5. 径向缩放分支为 B。六个单元出现稳定的 radial decoder sensitivity 或 configured-loss magnitude semantics；最大 decoded-angle median/p95 变化为 8.6623°/40.1550°，最大实际 head-loss 相对变化为 20.8734。
6. 在 geometry-normalized event 上，四个预注册候选在 DIOR-R 与 SODA-A 的可用单元上均优于 `negative_phase_mod`，配对图像 bootstrap 支持 NRC、AURC、Risk@70、Risk@90 四项差值。
7. 候选通过非平凡性审计：不依赖 GT、不做目标域拟合、推理端可得、不是 `phase_mod` 的简单取负/单调变换，也不是 detection score 复制。
8. 所有候选只改变排序；box、class、NMS 集合和 AP 保持不变。

### 2.2 当前最小解释

现有干预支持：PSC 模长受到径向尺度、调制和周期解缠结构共同影响，因而“模长越大越可靠”不是由解码结构自动保证的语义。跨频相位方向的一致性和候选能量间隔更接近解码歧义，而原始模长混合了幅值、边界与损失约束。

### 2.3 尚未证明

- 未证明某一个内部算子是反序的唯一原因。
- 未证明所有 PSC 配置、频率数、实现或数据域必然产生反序。
- 未证明新分数是概率校准量或完整不确定性理论。
- 未证明无需任何标定即可在任意新域保持增益。
- 未证明候选优于所有可能的通用 TTA 或 detection-score 组合。

## 3. 有限、可证伪的机制假说

只研究以下预注册机制，不扩展开放式候选：

**H1：径向解码敏感性。** 若 $z'=kz$ 改变 decoded angle、NMS 集合或损失梯度，则相位模长与方向并非完全可分；若在全部单元和 $k$ 网格上角度不变且损失弱约束，则 H1 被否证。

**H2：调制阈值条件化。** 反序主要集中在模长跨越解码/调制阈值的实例。若阈值两侧的配对风险差在控制 size、class、objectness 后消失，则 H2 被否证。

**H3：wrapping-conditioned ambiguity。** 接近周期边界的实例具有更高的多频分歧或更小 unwrap energy gap。若 boundary/non-boundary 分层下候选差异一致且无交互，H3 不成立。

**H4：模长—风险语义错位。** `phase_mod` 主要反映相位向量幅值而非候选方向之间的判别余量。若 `phase_mod` 对新分数可被单调映射以 $R^2\ge0.95$ 解释，H4 被否证。

**H5：多频与方向一致性提供可识别语义。** 多频 circular disagreement、unwrap energy gap、phase-direction margin 或 TTA direction consistency 至少一个在三个数据集稳定优于 `negative_phase_mod`、detection score 和通用 TTA。若无法满足，则不支持修复方法主张。

## 4. 方法候选

设 PSC 两个频率块投影得到 $(p_{1s},p_{1c})$ 与 $(p_{2s},p_{2c})$，主相位

$$\phi_1=-\operatorname{atan2}(p_{1s},p_{1c}),$$

次相位

$$\phi_2=-\tfrac12\operatorname{atan2}(p_{2s},p_{2c}).$$

由次相位构造两个解缠候选 $c_0,c_1$，对齐能量为 $A_j=\cos(\phi_1-c_j)$。

### 4.1 TTA phase-direction consistency

对 identity、horizontal flip、vertical flip 的相位方向映射回原坐标，定义

$$s_{tta}=-\left(1-\left|\frac1M\sum_m e^{\mathrm i2\tilde\theta_m}\right|\right).$$

- 输入：多视图 phase direction。
- 推理端可得：是；需要额外增强前向。
- GT/目标域拟合：不需要。
- 复杂度：约为增强视图数倍前向成本。
- 区别：使用方向一致性而非单次模长；不是 `negative_phase_mod`。

### 4.2 Multi-frequency consistency

令 $c^*=\arg\max_{c_j}A_j$，定义周期方向分歧 $D_{mf}=d_{180}(\phi_1/2,c^*/2)$，排序分数

$$s_{mf}=-D_{mf}.$$

- 输入：同一前向的双频相位。
- 推理端可得：是；无额外前向。
- GT/目标域拟合：不需要。
- 复杂度：每实例常数级。
- 区别：衡量频率间方向一致性，不使用模长符号翻转。

### 4.3 Unwrap candidate energy gap

$$s_{gap}=|A_0-A_1|.$$

- 输入：主相位与两个解缠候选。
- 推理端可得：是；无额外前向。
- GT/目标域拟合：不需要。
- 复杂度：每实例常数级。
- 区别：衡量解缠候选的判别间隔，和 `phase_mod` 的径向幅值不同。

### 4.4 Phase-direction margin

令次频向量范数 $r_2=\sqrt{p_{2s}^2+p_{2c}^2}$，定义

$$s_{margin}=s_{gap}\,r_2.$$

- 输入：解缠能量差和次频向量范数。
- 推理端可得：是。
- GT/目标域拟合：不需要。
- 复杂度：每实例常数级。
- 区别：把候选方向间隔与次频证据强度结合；不是主 `phase_mod` 的单调变换。

现有 paired results 的 angle-normalized-event NRC 均值如下，作为后续复核起点而不是最终三数据集结论：

| 数据集 | negative phase_mod | detection score | TTA direction | multi-frequency | unwrap gap | direction margin |
|---|---:|---:|---:|---:|---:|---:|
| DIOR-R | 1.526 | 0.239 | 0.753（seed0） | 0.674 | 0.674 | 0.741 |
| SODA-A | 1.560 | 0.577 | 0.410（seed0） | 0.433 | 0.433 | 0.558 |

## 5. 强制基线与非平凡性审计

### 5.1 强制基线

- `phase_mod`；
- `negative_phase_mod`；
- detection score；
- 通用 TTA circular variance；
- DCL bit margin；
- CSL softmax margin；
- 四个机制候选。

不同 head 只在自身预测端点内与 detection score 配对，不把 DCL/CSL 数值当作 PSC 实例级替代分数。

### 5.2 非平凡性审计

对每个数据集、种子和候选报告：

1. 与 `negative_phase_mod` 的 Spearman $\rho$ 与 Kendall $\tau$；
2. 归一化秩差 $n^{-1}\sum_i|r_i^{new}-r_i^{-mod}|$；
3. top-10% overlap；
4. 双方向 isotonic regression 的最佳 $R^2$；
5. 与 detection score 的 Spearman；
6. unique-value 数与退化检查；
7. 去掉频率差、能量差、次频范数或 TTA 视图的 feature ablation；
8. detection-score replication test。

若 $|\rho|\ge0.95$、isotonic $R^2\ge0.95$、top-10% overlap$\ge0.90$、rank disagreement$\le0.05$，或与 detection score 的相关达到同等阈值，则候选判为简单复制，不能作为新方法。现有审计中各候选在可用单元均未触发该判据。

## 6. 干预设计

### 6.1 径向缩放

对解码前相位向量施加 $z'=kz$，固定

$$k\in\{0.25,0.50,0.75,0.90,1.00,1.10,1.25,1.50,2.00,4.00\}.$$

逐层记录：decoded angle；主/次 `phase_mod`；配置中实际 angle-head loss；径向梯度 $|\partial\ell/\partial r|$；切向梯度范数；$|\partial\ell/\partial k|$；AP50/AP75；角度误差；预测框、类别和 NMS 集合签名。

### 6.2 Boundary/wrapping 条件分析

按主相位距周期边界、候选能量差、调制阈值侧别分层，并在 class、size、aspect ratio、objectness 上做固定分层或协变量控制。报告交互效应而非只展示相关散点。

### 6.3 多频与方向干预

- 单独扰动一个频率块的径向尺度，检查 multi-frequency disagreement 与 unwrap choice 是否按预期变化；
- 保持向量范数固定，仅沿切向小幅旋转，检查候选分数对方向歧义的敏感性；
- 对 identity/hflip/vflip 比较映射后的 phase direction，验证 TTA 分数来自方向一致性而非检测分数变化；
- 每次干预均核验 box、class、NMS 和 AP invariance；若改变检测集合，则该干预不能用于“仅排序修复”主张。

## 7. 数据、范围、指标与统计

必做数据集为 DIOR-R、SODA-A、FAIR1M。DOTA 只可作为可选外部检查，不能用扩矩阵替代机制证据。复用充分收敛 checkpoint，不重训 detector；主分析 `ar>=2.1`，较低阈值只作 sensitivity；只重排同一预测集合。

评价包括 NRC、AURC、Risk@70、Risk@90、geometry-normalized severe risk、5°/10°/15° sensitivity、Spearman、Kendall、rank disagreement、top-k overlap，以及 AP/box/class/NMS invariance。所有分数比较按图像 cluster bootstrap，候选相对 `negative_phase_mod`、detection score 和 TTA 报告 paired difference 及 95% CI。

## 8. B 篇成功条件与失败分支

### 8.1 全部成功条件

1. 结构性原因可由径向、切向或 wrapping 干预验证，而非只有相关性。
2. 新分数不是 `phase_mod` 取负、单调映射、温度缩放或 detection score 复制。
3. DIOR-R、SODA-A、FAIR1M 三个数据集方向一致。
4. 至少一个新分数稳定优于 `negative_phase_mod`。
5. 图像级 paired bootstrap CI 支持 NRC、AURC、Risk@70、Risk@90 的主要比较。
6. box、class、NMS 和 AP 不改变。
7. 分数不依赖目标域 GT 或目标域 GT 拟合。
8. 分数在推理端可得，并报告实际计算成本。
9. 相对 detection score 和通用 TTA 具有实际、非零的增益；仅打赢 `negative_phase_mod` 不足以形成强修复结论。

### 8.2 失败分支

若新分数无法稳定优于 `negative_phase_mod`，机制只有相关而不可干预，必须使用目标域 GT，必须重训 detector，改善来自简单取负，或三数据集方向不稳定，则 B 不形成完整方法论文。有效结果保留为 PSC 机制技术报告或后续研究，不回流改变 A 篇的通用协议、风险保证或跨检测器结论。

## 9. 与 A 篇的资产边界

| A 篇独占 | B 篇独占 | 可共享但不重复主表 |
|---|---|---|
| 通用 measurement protocol | radial scaling | PSC 三数据集反序的动机事实 |
| image-level risk control | radial/tangential gradient | 数据集与 checkpoint 的简述 |
| human annotation anchor | wrapping/modulation | NRC 定义的简化引用 |
| full-val perturbation | PSC 新分数公式 | `ar>=2.1` 评价口径 |
| geometry-normalized event | negative phase_mod 对照 | 图像 cluster bootstrap 原则 |
| DOTA 主结果 | mechanism intervention 与 score repair | 不重复数值主表 |

## 10. 阶段化执行方案

| 阶段 | 输入 | 动作 | 输出 | 通过条件 | 失败条件 | GPU | 新训练 |
|---|---|---|---|---|---|---|---|
| B0 权威产物冻结 | 现有三数据集结果、checkpoint、预测身份 | 核验数据集/seed/分数定义与 invariance | 单一事实表与数据字典 | 三数据集来源一致、可复算 | 身份或口径不可对齐 | 否 | 否 |
| B1 机制公式化 | PSC coder 与四个既定信号 | 写出相位、候选、阈值和可证伪预测 | 机制命题与预测矩阵 | 每个假说有明确反证条件 | 只能给相关故事 | 否 | 否 |
| B2 干预复算 | 既有径向前向和必要的固定 checkpoint | 复核 $k$ 网格、径向/切向、wrapping 分层 | 六单元干预统计 | 结构响应跨 seed 可复现 | 响应异质或检测集合改变 | 可能需要推理 | 否 |
| B3 新分数实现 | 相位向量、多频与 TTA 输出 | 实现四个固定候选，仅计算排序 | 同预测身份的 score dump | 无 GT、推理端可得 | 依赖 GT 或需改 detector | TTA 候选需要 | 否 |
| B4 非平凡性审计 | 候选、phase_mod、detection score | Spearman/Kendall/isotonic/top-k/ablation | 非平凡性表 | 至少一候选非复制 | 全部为单调或 score 复制 | 否 | 否 |
| B5 三数据集比较 | DIOR-R、SODA-A、FAIR1M | 在统一风险事件下配对比较 | NRC/AURC/Risk 表 | 三域方向一致且优于强基线 | 跨域不稳定 | 否 | 否 |
| B6 统计与消融 | 图像 ID、class/size/ar/boundary | cluster bootstrap 与结构分层 | CI、消融和限制 | CI 支持且非单层驱动 | CI 跨零或单层驱动 | 否 | 否 |
| B7 写作门控 | B0--B6 全部结果 | 按九项成功条件裁决 | 方法论文或技术报告决定 | 九项全部满足 | 任一核心条件失败 | 否 | 否 |

执行纪律是：不以扩大 detector matrix 替代机制证据，不因结果不理想改变候选集合，不以目标域 GT 调参挽救分数，也不把 B 的失败反馈为 A 的协议失败。
