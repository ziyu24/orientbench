# SERVER 科学指令

历史 r003 已停止且未执行，不得恢复。r005 correction-only 已完成并由 B 独立验收为
`INCONCLUSIVE_R004_PROTOCOL_VALIDITY`。当前唯一活动 SERVER 指令为 r006；不得重复执行
r004/r005、重调 test 剂量或降低门槛。

## r006 — clean-assigned 特征格相位的双轴平移到角泄漏生死门

### 科学问题与边界

检验一个有限命题：对同一遥感目标实施不改变像素内容和 GT 方向的整数平移时，多尺度 detector
的 clean-assigned output-lattice 相位是否产生可重复的 RP1 轴向角振荡；该振荡是否跨
Oriented R-CNN 与 Rotated RTMDet 两种架构，并且不能由匹配、中心、无序边长、分数或一般
检测不稳定解释。

本轮不是通用 shift-equivariance 的首发现，也不是新 angle coder、TTA、预测融合、风险排序或
框修正。不得训练、平均多个角、选择“最好平移”、修改输出或报告性能增益。结果只决定是否允许
下一轮设计 OBB 专属的 phase-consistent 方法；即使通过，也不构成 TGRS/JPRS 结论。

### 数据、模型与一次揭示

- 首次验证固定为训练外的 HRSC2016 official held-out test。official trainval 只用于 clean
  parity、模型层级来源与 active stride 支持度冻结；test 只整体揭示一次。
- detector 固定为 r004 已核实的 Oriented R-CNN R50 与 Rotated RTMDet-M。两者必须保持原
  checkpoint、score/NMS、预处理、角度约定与输出语义；不得以换 backbone 或第三模型救回。
- clean 标准推理先与既有结果做 identity parity。输入、split、模型、角度或层级 provenance
  任一不可核实，只能给 `INCONCLUSIVE_R006_EXECUTION_VALIDITY`。

### 无插值整数平移

平移必须施加在最终 resize 后、normalization 前的网络输入格点。先把同一 clean tensor 放入
固定大小的共同扩边 canvas，再沿水平或垂直方向移动整数像素；所有条件的 tensor 形状、后续
预处理、pad value 与批处理语义完全相同。不得在原图阶段平移后重新 resize，不得做亚像素插值、
旋转、缩放或改变图像内容。

每个变换都必须保存逆移审计：有效对象邻域在逆平移后逐值等于 clean，GT center 只加同一整数
位移，GT polygon、w/h 与 theta 不变。边界影响对象按 trainval 冻结的 receptive-field 安全边距
在构造总体前排除，test 不得按结果扩大边距。每个模型对完全相同的 clean canvas 独立重复三次；
匹配 key 必须一致，canonical angle 的最大差不得超过 0.05 度，否则本轮无效。

扩边 canvas 的 phase-0 还必须与同一模型的标准 clean 推理做逆移 parity：至少保留 95% 的标准
clean matched GT，图像等权 mean le90 的绝对差不超过 0.5 度，AP75 的绝对差不超过 0.005。
任一模型不满足时说明 canvas 自身改变了任务，结果只能是执行无效；不得在 test 上更换 pad 或边距。

### active stride 与扫描集合

不得假设整个多尺度网络只有一个共同周期。clean 推理必须为每个最终预测封存其角特征的实际来源：
Oriented R-CNN 使用最终 RoI extraction level 的 input-pixel stride，Rotated RTMDet 使用进入
NMS 的胜出候选 head level stride。层级记录必须穿过解码与 NMS，并由独立 hook 复核；不能只从
box size 反推。

每个模型的 stride `s` 只在 trainval clean matched predictions 中同时满足占该模型至少 15%、
至少 200 个对象和 100 张 source images 时成为 eligible active stride。该列表在打开 test 前
冻结；不得根据 test 信号挑选、合并或替换 stride。任一模型没有 eligible stride 时停止并给
`INCONCLUSIVE_R006_EXECUTION_VALIDITY`。

若 eligible strides 是嵌套的二次幂，沿水平与垂直轴分别运行
`d=0,...,2*s_max-1`；否则运行到 `2*LCM(eligible strides)-1`。每个 stride 的正式估计量只使用
其最先出现的 `d=0,...,2*s-1` 两个完整周期，不得在结果后挑周期；其他条件只作相位一致性审计。
clean 匹配对象按 phase-0 的 clean source stride 进入冻结的 `U_f,s`。干预后 source level 改变
必须显式记为 level switch，不能把对象重分配到新层或删除。

### 匹配、角度与固定总体

沿用 r005 已独立验证的全候选、全局排序、一对一 theta-free matcher；只能使用 class、center、
area 与无序边长，禁止 theta、angle error、oriented IoU 或结果后调 gate。每个条件把预测 center
逆平移到 clean 坐标后再匹配同一个冻结 GT 总体。

每个输出先转 polygon，再以长边 canonical 得到轴向单位复数 `u=exp(i*2*theta)`；角差固定为
`d_pi(theta1,theta2)=0.5*abs(arg(u1*conj(u2)))`，范围 0 至 90 度。不得直接比较 raw theta，
不得继承未核实的 w/h 加 90 度或 le90 字段。独立实现必须逐行重建 polygon、canonical angle、
source stride、匹配与全部统计量。

每个 `U_f,s` 在每个正式 shift 条件中必须维持同 source level 且成功匹配至少 90%，并至少保留
100 个对象和 50 张图。任一 eligible stratum 不满足即试验不能解释该 active path，裁为
`INCONCLUSIVE_R006_EXECUTION_VALIDITY`；不得缩总体或只保留 survivor。

### 周期相位估计量

对模型 `f`、eligible stride `s`、轴 `a`，令 `theta_i(d)` 为对象 `i` 在平移 `d` 后的
canonical angle。若一对条件没有同时保持匹配和 source level，其角贡献记零并另记不稳定，主量
始终以完整 `U_f,s` 为分母。定义每对象的周期内摆动与同相位跨周期不复现量：

`A_i = mean_{c in {0,1}, p=1,...,s-1} I_valid * d_pi(theta_i(c*s+p),theta_i(c*s))/90`

`R_i = mean_{p=0,...,s-1} I_valid * d_pi(theta_i(p+s),theta_i(p))/90`。

先在每张 source image 内对对象等权，再对图像等权，得到 `A_f,s,a` 与 `R_f,s,a`。`A` 表示
周期内角输出摆动，`R` 表示相同相位在下一周期不能复现的量。每个 unit 登记三项越大越支持的
统计量：`A-0.01`、`A-R-0.005`、`A-2R`。它们分别要求至少 0.9 度的完整总体轴向摆动、至少
0.45 度超过非周期项、且同相位不复现量小于周期内摆动的一半。

同时逐条件报告完整总体上的 miss/level-switch、score、逆移中心、无序长短边、HBB IoU、OBB
angle error 与 AP/AP75 波动；这些描述量不得替代角相位主门，也不得选择最佳相位。

### 定位稳定的角度专属性 witness

为排除一般 box 抖动，对每个 `U_f,s` 预先构造一个 all-shift 交集：对象必须在该轴全部
`0,...,2s-1` 条件中保持同 source level，且相对 clean 的逆移中心误差始终不超过无方向尺度的
2%，两条无序边的绝对 log-ratio 始终不超过 0.02，绝对 score 变化始终不超过 0.05。A 与 R
必须使用完全相同的交集，禁止为两个量使用不同 pair mask；统计仍以完整 `U_f,s` 为分母。

该 witness 必须覆盖至少 50% 的 `U_f,s`、100 个对象和 50 张图；否则说明一般定位/检测波动
足以支配现象，在执行有效的前提下关闭 OBB 专属机制。对每个 unit 定义
`A_stable-R_stable-0.0025`，要求角相位效应在严格稳定对象上仍至少有 0.225 度的完整总体增量。

### 统计合同与裁决

- 使用 10000 次 source-image cluster bootstrap；同一次 image multiplicity 同步用于所有
  shifts、strides、两轴和两模型。每个 `U_f,s` 在 phase-0 单独冻结其非空 source-image
  registry；点估计与每个 replicate 都只在该 registry 上按抽样 multiplicity 先图内等权、再作
  图间加权均值，分母严格为该 registry 的 multiplicity 总和。共同官方图像可复用同步随机数，
  但 registry 外图像不得以零填充进入分母。
- 所有 unit 的三个主统计量组成一个预注册 Holm family，大小固定为
  `3 * eligible(model,stride,axis) 数`；所有 stable witness 统计量组成第二个 Holm family，
  大小为 `eligible(model,stride,axis) 数`。对越大越支持的 `theta` 和零阈值，单侧
  null-recentered p 固定为
  `(1 + count((theta_b-theta_hat) >= theta_hat)) / 10001`；Holm-adjusted p 是唯一显著性裁决，
  普通 percentile CI 只报告。
- 一个 detector family 只有在至少一个预注册 eligible stride 的水平、垂直两个轴上，三项主门
  与 stable witness 全部点估计大于零且对应 Holm-adjusted p 不超过 0.05，才形成 family
  witness。不得以 outcome 后选 stride、单轴、pooled detector 或最大 AP 波动救回。
- 两个 detector family 都形成 witness，且所有资产、确定性、canvas、匹配、source-level、
  retention 与独立复算检查通过，唯一正结果为 `ADMIT_BIAXIAL_TAL_METHOD_STAGE`。
- 在执行有效时，凡不满足“两个 detector family 均形成上述同一 stride 双轴 witness”的任何
  结果——包括部分 stride 通过、单轴、单架构或只存在非周期 shift variance——唯一科学结果
  均为 `KILL_CROSS_FAMILY_BIAXIAL_TAL_R006`。该 token 只关闭本轮预注册的跨架构、双轴、
  clean-assigned output-lattice 路线，不能写成不存在任何 translation-to-angle leakage。
- 输入、层级 provenance、变换恒等性、重复确定性、eligible stratum、匹配、retention、统计
  或独立复算任一无效，唯一结果为 `INCONCLUSIVE_R006_EXECUTION_VALIDITY`；不得换数据、模型、
  stride、边距或阈值继续同一 test。

### 证据与后续边界

必须保存可复算的版本化实现与配置、trainval stride census、test 冻结总体、逐条件 source-level
与 matcher 表、完整逐对象角/中心/边长/score 记录、canvas 与重复确定性 fixtures、全部 bootstrap
draws、Holm 表以及第二实现逐行差异。大型预测和逐行运行产物只保留在项目运行根，不进入普通
Git；Git 只提交源码、配置与四个科学文档的结论。

若 `ADMIT`，下一轮才允许设计 phase-consistent 方法，并必须在未触碰的第二传感器/数据集和至少
第三种架构上验证，同时以 direct/PSC 或 CSL、Structure-Tensor angle coder、BlurPool、APS、
LPS、TIPS 和普通 shift-consistency training 为强基线；最终要同时改善 AP75、轴向角误差和
shift consistency，且 mAP/AP50 非劣，才可讨论 TGRS/JPRS。r006 本身禁止论文改写、期刊升档
或恢复任何已消费路线。

## r005 — r004 matcher、操纵与证据闭环

### 科学目的与边界

本轮不产生新的 detector 结果，只判断 r004 已报告的八个负向 `DeltaY` 是否来自原协议定义的
有效试验。必须复用 r004 已生成的两 detector、clean 与四个冻结干预条件的全部预测和原图；
不得重新推理、训练、重选剂量、换模型、改 score/NMS、删除对象或查看 test 后调整匹配规则。

### 同一冻结 matcher

trainval 与 test 必须调用同一个 matcher 实现、同一代价、同一 gate 和同一确定性 tie-break。
冻结语义沿用 r004：仅使用 class、center、area 与无序边长，先构造全部合格候选，按
`(cost, gt_index, pred_index)` 全局排序后做一对一贪心；禁止 theta、angle error 和 oriented
IoU。matcher 必须返回 GT-pred 配对而不只是 GT 集合，并同时用于剂量资格赛、clean 总体与
所有干预条件。

必须加入能区分旧两种算法的两 GT、两预测反例：一个预测同时是两个 GT 的候选，另一个只对
首个 GT 合格；全局代价排序应保留两个 GT，按 GT 顺序占用只能保留一个。若统一实现不能通过
该反例，或原始预测不再可读，本轮只能 `INCONCLUSIVE_R004_PROTOCOL_VALIDITY`。

### 真实操纵有效性

在完全相同的修正 clean 总体上，按 r004 冻结定义从真实 HRSC 图像计算 G、固定 P 和六个 N
臂的 `J_eff/M_15`。每个对象复用 clean G 或 clean P 的 noise scale、共同有效支持、epsilon、
trainval 均值与 image-cluster SD；不得逐条件重新归一化。计算原注册的 manipulation Holm-32
和每个 detector×corruption×dose 的 test 保留率、对象数与图像数。

前三类操纵 `clean-low>0`、`low-high>0`、标准化 `clean-high>0.20` 任一失败，或任一 test
单元低于 70% 保留、100 个对象、50 张图，结果必须是 `INCONCLUSIVE_R004`；不得用已报告的
低 `DeltaY` 解释为科学失败。前三类成立而 `clean-high-EN>0` 失败时，才可按预注册
specificity 规则给 `KILL_COI_R004`。

### 修正主损失与停止规则

对修正 clean 总体逐对象保存 clean/干预配对、`e0/e1`、retained、`Y0/Y1`、
`C_miss=(1-D1)*(1-e0/90)`、`C_ang=D1*(e1-e0)/90` 与 `DeltaY`；先图内等权，再图间等权。
第二个独立实现必须从同一冻结输入重新计算 matcher、总体 key、全部逐行量和八个点估计，并
报告两实现最大绝对差、key 差集和每单元样本计数。

若真实操纵有效且任一修正 `DeltaY` 点估计不大于 0.02，主损失合取门即为有效失败，可正式
给 `KILL_COI_R004`，无需用后续模型救回。只有八个点估计都大于 0.02 时，才继续完成 r004
原注册的 10000 次同步图像簇 bootstrap、Holm-8、角度贡献 Holm-4、G 机制 Holm-4 和强基线
Holm-6；全部通过才允许 `ADMIT_COI_CROSS_DATASET_STAGE`。

### 证据要求与裁决

运行根必须保存冻结输入清单、完整逐对象表、真实 G/P/N 特征、32 项操纵表、test 非坍塌表、
两实现复算与所有使用到的 bootstrap draws。`lab/result.md` 必须逐表报告全部 gate、样本计数、
实现差异与唯一 token，不能只写八个汇总数或引用运行名称。

唯一允许的裁决是：输入、matcher、真实操纵或独立复算不成立时
`INCONCLUSIVE_R004_PROTOCOL_VALIDITY`；有效试验任一科学门失败时 `KILL_COI_R004`；原 r004
全部门通过时 `ADMIT_COI_CROSS_DATASET_STAGE`。本轮禁止新推理、新模型、新数据、论文修改、
期刊升档或恢复任何已消费路线。

## r004 — HRSC2016 干预式轴向可辨识响应生死门

### 科学问题与边界

检验以下有限命题：在不改变 GT 几何的各向同性模糊和抗混叠降采样干预下，theta-hidden、
oracle-localization 圆形图像域中的局部有效旋转信息 `J_eff` 与全局轴向 alias 间隙
`M_15` 是否随剂量下降，并伴随两种严格不同 detector 架构的轴向损失上升；该链条是否仍
存在于预测裁剪偏差、中心/尺度扰动、普通结构张量、梯度、对比度、像素足迹和漏检贡献之外。

本轮只是一项 detector-side causal falsifier。不得把结果称为信息论上限、普适定律、
human-machine shared law、新不确定性分数、新角度估计器或顶刊完成证据。

### 数据、模型与资产门

- 首个数据集固定为训练外的 HRSC2016 official held-out test。历史 train/val 子集和有训练重叠
  风险的旧预测不得进入正式总体。
- detector 固定为 Oriented R-CNN R50 与 Rotated RTMDet-M 两种架构。换 backbone 的两个
  Oriented R-CNN 不算两种 family，也不得以低质量替代模型事后补位。
- 先核对数据 split、图像与 GT 完整性、模型身份、clean 重推理 parity，以及两个模型各自的
  角度单位、长边 canonicalization 和 le90 语义。历史冻结输出只作 parity anchor。
- 任一正式资产不可解析、official test 与训练集不独立、两架构不足、clean parity 或角度语义
  不成立时，结果只能是 `INCONCLUSIVE_R004`，不得缩总体、换模型或给科学 PASS/KILL。

### 成像干预与冻结顺序

HRSC official held-out test 只允许整体揭示一次。模型、score/NMS、角度约定、匹配规则、
crop、观测量方向与归一化、剂量和数值阈值，全部只能在 official train/val 或不含真实结局的
合成 fixtures 上冻结；不得用 test 的任何字段调参。

对整幅图像先实施干预，再分别完整重跑两个 detector：

1. clean；
2. 各向同性 Gaussian PSF blur 的两个非坍塌剂量；
3. 抗混叠 downsample 后以固定插值恢复原尺寸的两个非坍塌剂量。

候选格固定为 blur sigma `{0.50,0.75,1.00,1.25,1.50}` 个 native pixel，以及
downsample factor `{1.25,1.50,1.75,2.00}`；后者固定使用 area antialias 和 bicubic
restore。只允许依据 train/val 上不含角度的 clean-object 保留率，为每种 corruption 选择
两个最强且在两个 detector 都保留至少 90% clean 匹配对象的共同剂量。若候选格不能提供两个
共同有效剂量，则为干预不可识别，结果是 `INCONCLUSIVE_R004`；test 上不得重选。

### 三种 crop 臂

- **G 主臂**：只向特征进程提供 GT center 与交换 w/h 不变的尺度
  `s=max(w,h)`，圆形半径固定为 `max(48,0.9*s)`；永不提供 GT theta，也不按任何角度
  预对齐。这只是 theta-hidden oracle-localization 条件。
- **P 诊断臂**：使用 clean prediction 的 center 与同样的无方向尺度，并在所有干预间固定。
  使用各干预自身 prediction 的 P 只作 post-treatment 披露，不能进入主门。
- **N nuisance 臂**：围绕 G 固定四个 `±0.15*s` 的水平/垂直中心位移，以及尺度
  `×0.8`、`×1.25` 两个互为倒数的扰动。六个结果全部保留，不得挑选。

特征必须先于任何角度结局封存。G crop builder 不得读取 theta；P/N 也不得扫描候选框、输出
refined angle 或修改 detector 结果。

### 两个共同主观测量

在同一径向窗、共同有效像素和稳健噪声归一化下，令旋转切向量
`g_theta=-y*I_x+x*I_y`。将它对平移、各向同性尺度、光度 gain 和 offset 的 nuisance
切向空间作加权 Moore--Penrose 投影，定义

`J_eff = ||(I-P_N)g_theta||_W^2 / (sigma^2 * sum(W))`。

在轴向商空间的冻结旋转网格上，令 `E(phi)` 为仅允许小平移、各向同性尺度、正 gain 与
offset 后的归一化重建误差，定义

`M_15 = max(0, min_{d_pi(phi,0)>=15deg} E(phi) - E(0))`。

`J_eff` 与 `M_15` 是等权共同主量，数值越大表示越可观测。不得看结果后加权成单分数。
生产实现还必须给出未投影旋转能量、普通 structure-tensor coherence、梯度/边缘能量、局部
对比度、像素 footprint、AR、面积和相应全局自相关基线。

跨干预尺度固定如下。每个对象从 clean G crop 计算
`sigma0=max(1e-4,MAD(I-median3x3(I))/0.67448975)`，G、六个 N 及其全部 corruption
始终复用该 `sigma0`；P 单独从 clean P 得到 `sigmaP0` 并跨 corruption 复用。不得逐条件
重估 sigma。G/N 的 `E(phi)` 也始终以同一 `sigma0^2*sum(W)` 归一化并使用共同有效支持；
P 类同。用于统计的量固定为 `qJ=log1p(J_eff)` 与
`qM=log(M_15+epsilon)`，其中 `epsilon=max(1e-12,0.01*trainval正M_15中位数)`。
每个 detector 分别用 train/val clean 对象先图内等权、再图间等权得到 `qJ/qM` 的均值和
clean image-cluster SD；test 的标准化与 0.20 SESOI 只用这套尺度，不得重估。

对每个 detector 和 `q∈{qJ,qM}`，用上述 train/val 均值与 SD 得到 `zq`；N 上包络唯一为
`EN=max_j |mean_images(mean_objects(zq(N_j,clean)-zq(G,clean)))|`，六臂全部进入 max。
high-dose G 的标准化下降必须大于 `EN`。机制模型中的 N 不使用六列或择优臂，而固定为逐对象
`sqrt(mean_j((Delta zq(N_j)-Delta zq(G))^2))`；P nuisance 固定为
`Delta zq(P)-Delta zq(G)`。所有对象先图内、再图间聚合。

在正式图像前，两个独立实现必须共同通过 constant/radial 零信息、单瓣或椭圆非零信息、
四重对称“局部非零但全局 alias”、旋转后逆变换、pi 周期以及 blur/downsample 单调性的合成
fixtures。独立实现不一致、插值或边界本身制造信号时只允许修实现并报
`INCONCLUSIVE_R004`，不能进入科学门。

### 固定总体、匹配与结局

每个 detector 在 clean 图像上以 class、center、area 和无序边长为唯一信息做一对一匹配；
匹配代价和阈值在 calibration 冻结，禁止使用 theta、angle error 或 oriented IoU。由此冻结
clean-detected GT 总体，干预后仍对同一 GT 用同一角度无关规则匹配，任何对象都不得删除或
替换。

对 clean 对象的长边 canonical le90 误差记为 `e0∈[0,90]`。干预后若保留匹配，
`Y1=e1/90`；若漏检或匹配失败，`Y1=1`；clean 为 `Y0=e0/90`。令 `D1=1` 表示保留，
则总变化必须逐对象精确分为：

`DeltaY = (1-D1)*(1-e0/90) + D1*(e1-e0)/90`。

第一项是 missing contribution，第二项是 retained-angle contribution。主结论使用完整固定
总体的 `DeltaY`，matched-only 和稳定高定位质量子集仅作支持；不得用 complete-case 代替
主结果。post-treatment score、IoU 和定位误差是中介，只能用于分解，不能作为主因果模型的
控制变量。

### 统计合同

- 对每个 detector 单独得到 clean 总体 `U_f`。逐对象结局先在其 source image 内等权平均，
  再对图像等权，避免多目标图支配结果。
- 正式推断采用 10000 次 source-image cluster bootstrap；同一次图像 multiplicity 同步用于
  clean、全部干预、G/P/N 和两个 detector。每次完整重算图像均值、分解与条件模型。
- 条件增量使用预先封存图像 ID 的固定五折 image-grouped cross-fitting。bootstrap 中重复
  图像始终留在原 fold，并以 multiplicity 加权；每个 replicate 重新拟合各 fold，禁止 OOF
  泄漏。共同 `Bbase` 固定包含 corruption/dose、pre-treatment `Y0`、AR、面积、普通
  structure tensor、梯度、边缘、对比度、像素 footprint 的配对变化，以及已冻结的 P-G 差值
  与 N 对称 RMS crop nuisance。`B0=Bbase`，`BJ=Bbase+G-J`，
  `BM=Bbase+G-M`，`BJM=Bbase+G-J+G-M`；四模型只能以这两个 G 列的有无不同，
  必须共享相同 folds、预处理、超参数和全部 P/N nuisance。主因果效应不得控制
  post-treatment score、IoU 或 retained 状态；“信息下降只能预测损失上升”的方向在 test
  前固定。
- 所有门都把统计量写成“越大越支持”的 `theta`。对阈值 `theta0`，唯一单侧 p 为
  `p=(1+count((theta_b-theta_hat)>=(theta_hat-theta0)))/10001`。各预注册族只用
  Holm-adjusted p 控制 FWER 0.05 并决定裁决；普通 95% percentile CI 只报告，不称
  adjusted CI，也不与 p 混用。
- 检验族固定为：操纵 Holm-32、主损失 Holm-8、角度贡献 Holm-4、G 机制系数 Holm-4、
  强基线增量 Holm-6。不得事后合并、拆分或另建 pooled 检验族。

全部以下条件必须同时成立：

1. **有效操纵且非坍塌**：操纵 Holm-32 的成员对
   `q∈{qJ,qM}`、两个 detector、两种 corruption 完整枚举四类统计量：
   `clean-low>0`、`low-high>0`、以 train/val clean SD 标准化的
   `clean-high>0.20`、以及 `clean-high-EN>0`，每类 8 个。32 项各自越过阈值且
   Holm-adjusted p<=0.05。
   八个 detector × corruption × dose 单元各自必须保留至少 `70%*|U_f|`，并至少有 100 个
   retained objects、50 个 source images。前三类操纵或样本界限失败说明试验无效，只能
   `INCONCLUSIVE_R004`；操纵成立但 `clean-high-EN` 失败则为真实 specificity 失败，
   进入 `KILL_COI_R004`。test 上均不得重调剂量。
2. **八单元跨架构轴向恶化**：对两个 detector、两种 corruption、两个 dose 的八个
   `delta_fck=E[DeltaY]` 建立 Holm-8。每个单元都必须拒绝
   `H0:delta_fck<=0.02`，即点估计大于 0.02 且 Holm-adjusted p<=0.05；任何单元失败都
   不能由 pooled/global 平均救回。
3. **不是漏检假象**：逐行保存
   `C_miss=(1-D1)*(1-e0/90)` 与 `C_ang=D1*(e1-e0)/90`。对每个
   detector × corruption 将两个 dose 等权汇总，共四个 Holm-4 门；每个单 dose 的
   `C_ang` 点估计不得为负，四个汇总的点估计都须大于 0.005 且 Holm-adjusted p<=0.05。
   只报告 miss share，不设事后比例门；missing contribution 不能单独形成 PASS。
4. **定位去混杂和方向一致**：机制模型固定为在 `B0` 上加入
   `-Delta log(1+J_eff_G)` 与 `-Delta log(M_15_G+epsilon)`，同时把 P-G 和 N-G 的对应
   差值仅作已定义的 nuisance covariates。四个 G 系数（两机制 × 两 detector）各自须大于零
   且 Holm-4 adjusted p<=0.05；P/N 无符号门，不能替代或救回 G。dynamic P、survivor-only
   regression 和 natural-indirect effect 声称均禁止。
5. **不是经典统计换皮**：强基线 Holm-6 对每个 detector 分别登记三个 nested contrast。
   `BJM-B0` 的裁决统计量为
   `MAE_benefit-max(0.005,5%*MAE_B0)`；`BJM-BJ` 与 `BJM-BM` 各为
   `MAE_benefit-max(0.002,2%*对应reference_MAE)`。reference MAE 在每个 bootstrap
   replicate 同步重算；六项统计量都须大于零且
   Holm-adjusted p<=0.05；任一 detector 不得被另一 detector 或 pooled 结果救回。若增量被
   普通结构张量、梯度、对比度、像素尺度、AR、面积或 recall 完全解释，则失败。

任一科学门只在资产、实现、匹配和干预有效性均成立后判断。有效试验中任一必需 corruption、
detector、G 去混杂门、角度贡献门或强基线门失败，统一结果为 `KILL_COI_R004`；不得改阈值、
删对象、换 family、只报 pooled 平均或改名续命。全部通过时唯一正结果为
`ADMIT_COI_CROSS_DATASET_STAGE`。

### 预期证据与停止条件

结果必须包含可复算的代码与配置、数据/模型/split/干预冻结记录、clean parity 与角度语义审计、
逐对象匹配和所有 crop/剂量特征、完整 `Y` 分解、交叉拟合预测、全部 bootstrap draws、强基线
与 sensitivity、独立实现复算、错误与偏离清单，以及唯一裁决。大型运行产物不进入普通
Git；Git 只提交源码、配置和科学结论。

本轮禁止训练、新 detector/head、score fusion、候选角扫描、框修正、关系场、恢复旧 r003、
修改论文或声称期刊升档。若 `ADMIT`，下一轮才允许设计未触碰的第二数据集/传感器、至少三名
盲标注者或重复标注以及跨 family 确认；若 `KILL`，把适用边界写入失败路线并停止 COI。
