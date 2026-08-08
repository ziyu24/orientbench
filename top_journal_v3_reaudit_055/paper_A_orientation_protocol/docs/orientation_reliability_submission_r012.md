# 旋转目标检测的朝向可靠性：几何归一化测量、场景级审计与跨域迁移边界

## 摘要

旋转目标检测通常以平均精度评价整体性能，但类别、中心和尺度正确并不意味着预测朝向可信。交并比阈值、目标长宽比、匹配竞争和标注不确定性共同决定角误差是否被 AP 感知。本文提出一套面向有向边界框的朝向可靠性测量与诊断协议：用 le90 长边规范定义周期角误差；由共中心、同尺度矩形的旋转 IoU 推导 `ar>=2.1` 的主分析域；用随长宽比变化的几何归一化严重事件统一风险语义；并以风险—覆盖曲线、AURC 和 NRC 评价任意可靠性分数。六个完整验证 evaluation units 的约束扰动显示，在保持类别、分数、中心和尺度不变时，AP@0.5 可处于几何上明确的弱敏感区，而 AP@0.75 更早响应；`ar>=2.1` 实例的经验中位容忍角约为 25°--30°（IoU 0.50）与 0°--7.5°（IoU 0.75）。场景级审计表明，把实例视为独立样本或把空选择场景记为零风险会产生乐观上界。两名互盲标注者对 600 个目标中的 450 对数值角度给出 2.3112° 的平均圆周分歧，说明度级风险必须采用 label-noise-aware 解释。

本文还审计了从诊断上界向跨数据集选择器迁移的证据。目标域 GT 拟合的非线性几何分数在固定尺寸分箱内显示 headroom，但不具可部署性；源域迁移在严格 leave-dataset 设计中未形成支持。进一步的等变性选择器评价因 FAIR1M 完整原始预测总体无法闭合而在任何特征拟合和目标标签加载前停止。因此本文的贡献限定为 measurement→diagnose：给出可复算的朝向风险定义、评测器敏感性、统计单位纠正、人工标注审计以及对不成立迁移证据的显式边界。

**关键词：** 旋转目标检测；朝向可靠性；风险—覆盖；几何归一化风险；场景级统计；标注不确定性

## 1 引言

有向边界框以 $(c_x,c_y,w,h,\theta)$ 描述目标，广泛用于遥感影像、场景文字和工业视觉。旋转检测研究主要围绕 AP、角度编码连续性与定位损失展开。AP 是必要的综合指标，却混合类别、中心、尺度、角度、置信排序与匹配关系。当 IoU 阈值较低或目标接近方形时，显著角度变化仍可能保持匹配；中心或尺度的小变化也可能在角度不变时改变 AP。因此，“检测是否正确”和“朝向是否可信”相关但不同。

朝向可靠性测量至少面临四个困难。第一，旋转框存在 $180^\circ$ 周期和长短边交换等价性，线性角度差会制造伪误差。第二，目标形状决定可辨识性：细长目标的角度变化迅速降低 IoU，近方形目标则在较大角度范围内保持相似。第三，检测分数对检测正确性的排序能力不等同于其对角误差的排序能力。第四，同一图像、切片或原始母景中的实例并不独立，instance-i.i.d. 推断会夸大有效样本量。

本文将问题限定为测量与诊断，不提出新的角度编码器，也不宣称通用可部署选择器。主要贡献如下：

1. 形式化 le90 周期角误差，以 risk-coverage、AURC 和 NRC 独立评价可靠性排序。
2. 从旋转矩形 IoU 推导 `ar>=2.1` 的几何原则化主域，并定义 geometry-normalized severe orientation event。
3. 在 full evaluator 中执行保持预测非角度属性不变的朝向扰动，量化 AP@0.5 与 AP@0.75 的不同敏感性。
4. 在 DIOR-R、FAIR1M、SODA-A 和 DOTA 的多个 detector-head units 上报告 full-validation AP、连续角风险排序与固定尺寸分箱诊断。
5. 比较实例、图像、切片与母景统计单位，显式处理 abstention，并完整保留不可行迁移与来源失败。
6. 通过真人双标和 annotator-vs-official-GT discrepancy 限定度级风险语言。

不同原生角度信号对不同风险泛函可能呈现不同排序语义；模型特定角度编码机制与排序修复不属于本文范围。

## 2 相关工作

### 2.1 旋转目标检测与周期性

DOTA、FAIR1M、DIOR 和 SODA-A 提供遥感旋转检测基准 [1--4]。Oriented R-CNN 与 RTMDet 代表两类常用检测结构 [5,6]。CSL、DCL 和 PSC 通过分类或相位编码处理角度周期与边界不连续 [7--9]；GWD、KLD 与后续边界研究从分布距离或编码方式缓解旋转框回归不连续 [10,11,26]。ARS-DETR明确讨论长宽比与 AP@0.5 的朝向敏感性 [12]，OSKDet以方向敏感关键点和定位质量不确定性改进旋转检测 [27]。本文不主张首次观察 AP 的角度宽松，而是把周期误差、形状可辨识域、风险排序和场景统计统一到可复算测量协议。

### 2.2 选择性预测与检测校准

选择性分类研究拒绝部分样本后风险如何随覆盖变化 [13--15]。风险—覆盖排序不同于概率校准；神经网络校准、D-ECE、MCCL 和 self-aware object detection 分别处理分类置信、定位质量、域移和场景拒绝 [16,17,28,29]。Optimal Correction Cost 也指出 mAP 的全局实例排序不等同于图像级一致性 [30]。本文的 NRC 小于 1 仅表示 informative/non-reversed ranking，不推出 calibrated。

### 2.3 保形推断与风险控制

保形预测以可交换性构造有限样本覆盖 [18]。RCPS、Learn-Then-Test 与 Conformal Risk Control 将其扩展到一般风险和候选选择 [19--21]，SeqCRC进一步面向检测的顺序风险控制 [31]。理论保证依赖估计对象和交换单位；同一母景中的实例或切片不能自动视为独立样本。本文把这些方法用于可行性审计，而不把未闭合的认证结果包装为方法成功。

### 2.4 评测扰动与人工差异

Borji 系统研究了水平检测指标对受控定位扰动的响应 [32]，说明“扰动—指标敏感性”并非本文首创。本文的增量是 OBB 角剂量、le90 周期误差、长宽比归一化和场景簇统计。测试时增强可提供经验不确定性 [23]；对 $180^\circ$ 朝向必须在 $\theta\mapsto2\theta$ 的圆域计算。人工标签亦非无噪声常数 [24,25]，Oriented Cell Dataset 已在 OBB 场景报告多标注者变异 [33]。本文只主张遥感朝向、度级圆周分歧及其与 official GT 分离报告。

## 3 问题定义与几何归一化

### 3.1 le90 长边角误差

将旋转框规范为长边表示：若 $w<h$，交换长短边并令角度增加 $90^\circ$。规范角记为 $\phi\in[0^\circ,180^\circ)$。预测与参考角的圆周误差为

$$
e_\theta(\hat\phi,\phi)=\min_{k\in\mathbb Z}|\hat\phi-\phi+180^\circ k|
=\min(d,180^\circ-d),
$$

其中 $d=|\hat\phi-\phi|\bmod180^\circ$，故 $e_\theta\in[0^\circ,90^\circ]$。该量描述几何长边方向，不判断头尾或语义航向。

### 3.2 可辨识域与容忍角

定义长宽比 $a=\max(w,h)/\min(w,h)\ge1$。考虑两个共中心、同尺度、长宽比同为 $a$ 的矩形，一个相对另一个旋转 $\delta$，旋转 IoU 记为 $J(\delta;a)$。对阈值 $\tau$ 定义

$$
\delta_\tau(a)=\inf\{\delta\in[0^\circ,90^\circ]:J(\delta;a)<\tau\}.
$$

以 0.001° 精度数值求解 le90 第一叶。由“15° 误差在 IoU 0.75 下应产生明确几何后果”反解得交叉点约 $a=2.1$。因此 `ar>=2.1` 是正文唯一主分析域；`ar>=1.6` 与 `ar>=1.3` 只作敏感性。理想曲线不等于真实检测行为，因为真实框还受中心、尺度、竞争匹配和 NMS 影响。

### 3.3 风险对象

主严重事件为

$$
Y_i^{\mathrm{geo}}=\mathbf1\{e_{\theta,i}>\delta_{0.75}(a_i)\}.
$$

它表示超出理想共中心、同尺度的 IoU 0.75 容忍度，不表示真实框必然跌破 0.75。固定敏感性为 $Y_i^{(q)}=\mathbf1\{e_{\theta,i}>q\}$，$q\in\{5^\circ,10^\circ,15^\circ\}$。5° 是 noise-sensitive fine risk；10° 与 15° 提供更清晰的严重尾部解释。

## 4 朝向可靠性协议

### 4.1 Risk-coverage、AURC 与 NRC

令分数 $s_i$ 越大越可信，按其降序排列。覆盖 $c=k/n$ 时

$$R_s(c)=\frac1k\sum_{j=1}^k\ell_{(j)},\qquad
\operatorname{AURC}(s)=\frac1n\sum_{k=1}^nR_s(k/n).$$

令 oracle 按真实风险升序，random 的期望风险等于总体均值，定义

$$
\operatorname{NRC}(s)=\frac{\operatorname{AURC}(s)-\operatorname{AURC}_{oracle}}
{\operatorname{AURC}_{random}-\operatorname{AURC}_{oracle}}.
$$

NRC=0 为理想排序，NRC=1 为随机排序，NRC>1 为反序，NRC<1 仅表示 informative/non-reversed。本文同时报告 Risk@70、Risk@90、保留数与比例。

### 4.2 分数菜单与监督边界

| 分数 | 监督与输入 | 目标推理可得 | 定位 |
|---|---|---:|---|
| detection score | 原生置信度，无额外 GT fit | 是 | 可部署基线 |
| TTA circular consistency | 增强预测的双角圆一致性 | 是 | 增加推理成本 |
| source-supervised geometry | 源域 GT 监督的 score、AR、size 几何模型 | 是 | 迁移候选，不是无监督训练 |
| target-GT nonlinear geometry | 目标域独立拟合集的 GT 角误差 | 是 | diagnostic/calibration upper bound |

目标域上界的 selector-fit、calibration 与 audit 可相互独立，但不能消除目标 GT 依赖，故不能称 deployable。

### 4.3 场景总体与 abstention

对每个 evaluation unit 固定 baseline eligible-scene universe，只包含至少一个 `ar>=2.1` eligible matched prediction 的场景。阈值后没有保留预测的场景记为 abstained scene，进入 nonempty rate 分母，但不以零损失稀释条件风险。对非空场景

$$L_I(t)=|S_I(t)|^{-1}\sum_{i\in S_I(t)}Y_i^{\mathrm{geo}},$$

并定义 $Z_I(t)=\mathbf1\{\exists i\in S_I(t):Y_i^{\mathrm{geo}}=1\}$。对 $L_I\in[0,1]$ 可用 bounded-loss 单侧上界，对二元 $Z_I$ 可用 Clopper--Pearson；但保证必须绑定场景交换单位、nonempty rate 与 coverage。

## 5 实验设置

实验覆盖 DIOR-R、冻结本地 FAIR1M train_80/val_20（18,505/4,362 images）、SODA-A 与 DOTA-v1.0。检测器包含相位编码 RetinaNet、Oriented R-CNN 与 Rotated RTMDet。DOTA 仅使用本地 train/val，不比较公开 test 数字。AP 通过完整预测与完整 GT 的 classwise full evaluator 计算；matched-only 表只用于朝向风险，不替代 AP。

六个主要 evaluation units 的朝向扰动保持 post-NMS prediction identity、分数、类别、中心、宽与高，只改变角度并重新运行完整评测器。经验容忍角在固定预测—GT 几何上沿增加当前误差方向搜索 IoU 首次越界。区间以图像或母景为 cluster；实例级结果只作 empirical instance-weighted risk。

## 6 结果

### 6.1 Full-validation AP 与约束扰动

| 数据集 / 检测器 | 原 AP@0.5 | 扰动 AP@0.5 | 原 AP@0.75 | 扰动 AP@0.75 | 原→扰动平均角误差 |
|---|---:|---:|---:|---:|---:|
| DIOR-R / 相位编码 RetinaNet | 0.5368 | 0.5368 | 0.3503 | 0.0384 | 8.947°→39.189° |
| DIOR-R / Oriented R-CNN | 0.6448 | 0.6448 | 0.4275 | 0.0484 | 8.665°→40.041° |
| DIOR-R / Rotated RTMDet | 0.6462 | 0.6462 | 0.4515 | 0.0532 | 9.087°→40.541° |
| FAIR1M / 相位编码 RetinaNet | 0.3462 | 0.3462 | 0.2422 | 0.0665 | 4.631°→36.516° |
| SODA-A / 相位编码 RetinaNet | 0.5991 | 0.5991 | 0.2735 | 0.0448 | 5.230°→34.416° |
| SODA-A / Oriented R-CNN | 0.7295 | 0.7295 | 0.3805 | 0.0278 | 5.148°→35.893° |

约束 IoU 0.50 边界扰动使六单元 $\Delta$AP@0.5=0，而 AP@0.75 下降并伴随角误差升至约 34°--41°。这说明 AP@0.5 存在几何上明确的弱敏感区，不等于“AP 不看角度”。固定剂量曲线目前只可作 single-evaluator descriptive candidates，不能用于统一 knee 或形式显著性主张。

DOTA 的两个 clean full-validation 单元为：Oriented R-CNN AP@0.5/AP@0.75=0.7061/0.4517，Rotated RTMDet-M=0.7161/0.4868。

### 6.2 理想与经验容忍角

| 数据集 / 检测器 | n | IoU 0.50 中位数 | IoU 0.50 p10--p90 | IoU 0.75 中位数 | IoU 0.75 p10--p90 |
|---|---:|---:|---:|---:|---:|
| DIOR-R / 相位编码 RetinaNet | 49,502 | 26.5° | 15.0°--38.5° | 6.0° | 0.0°--12.0° |
| DIOR-R / Oriented R-CNN | 54,297 | 27.0° | 15.0°--38.0° | 7.5° | 0.0°--12.0° |
| DIOR-R / Rotated RTMDet | 53,671 | 27.0° | 14.5°--38.0° | 7.0° | 0.0°--12.0° |
| FAIR1M / 相位编码 RetinaNet | 31,801 | 25.0° | 13.0°--36.0° | 0.0° | 0.0°--8.0° |
| SODA-A / 相位编码 RetinaNet | 197,529 | 28.5° | 13.5°--36.5° | 0.0° | 0.0°--9.5° |
| SODA-A / Oriented R-CNN | 235,428 | 30.0° | 14.5°--37.5° | 4.0° | 0.0°--10.5° |

理想曲线与经验 IoU 0.50 容忍度方向一致，但真实中心、尺度与匹配使分布扩散。0° 的 IoU 0.75 容忍角表示基准 matched pair 已低于 0.75，不是角度计算失败。证据只支持部分几何对齐。

### 6.3 `ar>=2.1` 连续角风险排序

| 数据集 / 检测器 | retained n | ratio | NRC | AURC | Risk@70 | Risk@90 |
|---|---:|---:|---:|---:|---:|---:|
| DIOR-R / 相位编码 RetinaNet | 25,065 | 0.5716 | 0.6082 | 1.2075 | 1.4346° | 1.5866° |
| DIOR-R / Oriented R-CNN | 27,671 | 0.5778 | 0.5741 | 1.3528 | 1.5598° | 1.7512° |
| DIOR-R / Rotated RTMDet | 27,385 | 0.5719 | 0.4653 | 1.3786 | 1.6090° | 1.9066° |
| FAIR1M / 相位编码 RetinaNet | 15,120 | 0.5791 | 0.9379 | 2.2225 | 2.2998° | 2.3004° |
| SODA-A / 相位编码 RetinaNet | 101,102 | 0.6416 | 0.8113 | 1.7827 | 1.8733° | 1.9817° |
| SODA-A / Oriented R-CNN | 120,925 | 0.6290 | 0.6878 | 1.8254 | 2.0645° | 2.2053° |

DOTA 上统一 `ar>=2.1` 的 detection-score NRC 为 0.7544（Oriented R-CNN）与 0.7113（Rotated RTMDet-M）。上述结果说明检测分数通常包含角风险信息，但离 oracle 很远且强度随 evaluation unit 变化。

### 6.4 固定尺寸分箱与诊断上界

在固定 small/medium/large bins 内比较 score-only、score+$\log a$、score+$\log a$+$\log$ size 与非线性几何诊断分数。15 个可用 bins 中 11 个的 image-cluster interval 支持非线性分数优于 score+$\log a$+$\log$ size，覆盖 DIOR-R 与 SODA-A 的多个 detector-head units；FAIR1M 两个 bins 均不稳定。该结果表明增益不能完全由 size prior 解释，但分数由目标域 GT 角误差拟合，只能作为 calibration upper bound。

### 6.5 场景统计与认证可行性

| 数据集示例 | 实例 | tile/image | mother scene | instance-i.i.d. UCB | tile/image UCB | mother UCB |
|---|---:|---:|---:|---:|---:|---:|
| DIOR-R | 19,207 | 2,882 | 2,882 | 0.0040 | 0.0188 | 0.0188 |
| SODA-A | 120,925 | 4,120 | 417 | 0.0061 | 0.0090 | 0.0180 |

SODA-A 的 22,994 tiles 可映射到 576 个 mother scenes，但冻结 calibration/audit 角色在母景层交叉，故正式统计只能写 tile/image-level，mother aggregation 仅为相关性敏感性。严格绝对风险预算下，可部署 detection score、TTA consistency 与 source-supervised geometry 未形成稳定非平凡认证；唯一 practical point 来自 target-GT 上界，因此只说明 headroom，不说明部署成立。

### 6.6 跨数据集迁移审计

源监督非线性几何候选在 leave-dataset 设计中为 0/6 支持；可识别的 leave-detector 设置中 4/5 支持，但这些 fit 都含同数据集 sibling units，不能作为跨数据集证据。为避免把上界当部署方法，进一步冻结了 identity/hflip/vflip 等变性选择器评价，并要求所有 source fit 排除整个目标数据集。

该评价在来源门停止。FAIR1M 冻结 val split 为 4,362 images / 78,644 GT；持久化 identity/hflip/vflip raw 与 schema 只有 3,896 image IDs / identity 484,332 predictions，缺少 466 个 split image rows。另一个历史 manifest 登记 4,362 images / 488,194 predictions，但相应完整 raw prediction dump 未持久化，无法逐图核验或建立相同 prediction identity。AP endpoint 接近不能替代 universe equality。因此没有执行变换前向、特征构建、source fit、target label attach 或 bootstrap，也不存在可报告的跨数据集 EQS 收益。这一结果关闭当前方法路线，但不是选择器性能本身的成功或失败证据。

## 7 人工标注不确定性

两名真实标注者独立互盲处理 600 个 canonical targets，DIOR-R、FAIR1M、SODA-A 各 200；双方均给数值角度的 primary 子集为 450 对。

| 范围 | n | 均值 | 95% CI | 中位数 | p90 | p95 | P(>5°) | P(>10°) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 总体 | 450 | 2.3112° | 1.9970°--2.7854° | 1.6359° | 4.4220° | 5.9359° | 8.00% | 0.89% |
| `ar>=2.1` | 308 | 2.2823° | - | 1.6130° | - | - | 6.82% | 0.65% |

Annotator 1 与 official GT 的差异为 n=468、均值 5.2721°、中位数 1.7639°、P(>5°)=17.31%；Annotator 2 为 n=463、均值 5.1219°、中位数 1.7899°、P(>5°)=16.20%。这里报告 discrepancy 而非 error：official GT 不是绝对无误差真值，inter-annotator disagreement 也不等于真实 GT error。

因此 1.5°--2° mean-risk budget 接近人工分歧尺度，只能作 label-noise-aware 解释；5° fine risk 有意义但 noise-sensitive；10° 的人工越界仅 0.89%，有更清晰 margin。每数据集 200 个目标不足以支持 rare-class 或极端尾部强主张。29 个盲重检只作 secondary endpoint；第三标注员的 150 个样本虽已冻结，真人结果仍为 0，三人共识未形成。

## 8 工具与复现边界

测量工具箱覆盖 canonical angle error、$\delta_\tau(a)$、geometry-normalized event、NRC/AURC/risk-coverage、固定角敏感性、image/tile/mother-scene bootstrap、eligible-scene universe、nonempty conditional risk 与显式 `INFEASIBLE` 输出。它不把 target-GT geometry 作为默认可部署分数。

来源核验同样是复现的一部分：每个 raw registry 必须显式包含完整 image universe，包括 `n_pred=0` 的图像；manifest 计数或近似 AP 一致不能替代逐图身份。无法闭合时应在加载目标标签前停止，而不是通过拼接不同总体继续计算。

## 9 讨论与局限性

本文区分四层问题：AP 衡量给定 IoU 阈值下的检测排序和匹配；NRC/AURC 衡量分数能否优先保留低角风险实例；几何归一化事件把形状依赖纳入严重性；场景审计决定推断的交换单位。四者互补，不能互相替代。

主要局限有：第一，跨数据集可部署选择器没有获得有效评价，当前证据只支持 measurement→diagnose。第二，固定剂量配对 AP 只保留为描述性候选，不能支持统一 knee、NMS 因果或形式显著性。第三，SODA-A 的 frozen split 不满足严格 mother-scene calibration/audit independence。第四，目标域 GT 拟合几何分数只是诊断上界。第五，缺少未参与协议设计且 full-universe、provenance-clean、持久化完整的独立确认单元。第六，第三标注员未完成，人工审计未形成三人仲裁。第七，覆盖的 detector-head units 不是所有旋转检测器的穷举，本文不作跨域分布无关保证。

## 10 结论

本文建立了旋转目标检测的朝向可靠性测量框架：以 le90 周期误差和 `ar>=2.1` 可辨识域为基础，用 $\delta_{0.75}(a)$ 定义形状归一化严重事件，以 NRC、AURC 与风险—覆盖描述排序，并用 full evaluator、场景聚类和真人标注审计限制解释。结果显示 AP@0.5 存在几何弱敏感区，detection score 通常 informative 但远非 oracle，实例独立推断会显著乐观，度级风险还受非忽略人工分歧约束。

更重要的是，本文没有把诊断上界或不完整迁移链写成可部署方法。leave-dataset 迁移未获支持，新的等变性路线又因完整预测总体无法复现而在拟合前停止。可靠性研究不仅需要新分数，也需要严格的估计对象、数据身份和统计单位；无法闭合这些条件时，最可信的结论是明确保留负迁移与不可评价边界。

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
12. Zeng Y, Chen Y, Yang X, Li Q, Yan J. ARS-DETR: Aspect Ratio-Sensitive Detection Transformer for Aerial Oriented Object Detection. IEEE Transactions on Geoscience and Remote Sensing, 2024. doi:10.1109/TGRS.2024.3364713.
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
26. Xu H, Liu X, Xu H, et al. Rethinking Boundary Discontinuity Problem for Oriented Object Detection. CVPR, 2024: 17406--17415.
27. Lu D, Li D, Li Y, Wang S. OSKDet: Orientation-Sensitive Keypoint Localization for Rotated Object Detection. CVPR, 2022: 1182--1192.
28. Pathiraja B, Gunawardhana M, Khan M H. Multiclass Confidence and Localization Calibration for Object Detection. CVPR, 2023: 19734--19743.
29. Oksuz K, Joy T, Dokania P K. Towards Building Self-Aware Object Detectors via Reliable Uncertainty Quantification and Calibration. CVPR, 2023: 9263--9274.
30. Otani M, Togashi R, Nakashima Y, et al. Optimal Correction Cost for Object Detection Evaluation. CVPR, 2022: 21107--21115.
31. Andéol L, Mossina L, Mazoyer A, Gerchinovitz S. Conformal Object Detection by Sequential Risk Control. arXiv:2505.24038, 2025.
32. Borji A. Sensitivity of Average Precision to Bounding Box Perturbations. arXiv:2206.10107, 2022.
33. Kirsten L, Angonezi A, Marques J, et al. Oriented Cell Dataset: A Dataset and Benchmark for Oriented Cell Detection and Applications. WACV, 2025: 3996--4005.
