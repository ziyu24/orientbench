# SERVER 科学指令

## r012：RarePlanes 方向规范化因果价值 H1a 单次生死门

### 1. 唯一问题与禁止范围

r011 的机器资产结论未通过 B 验收。本轮不再等待或修补五个 detector，而只回答整个顶刊扩展的
必要前提：在同一飞机的中心、长短边、预提取 source canvas 和分类器全部固定时，仅把定向规范化角从
`theta` 改为 `theta-10°` 或 `theta+10°`，是否会使 wing、engine 和 propulsion 三项不同属性的
balanced error 稳定增加至少 2 个百分点。

任务严格按 `G0 证据修正 → H1a calibration-only` 顺序执行。G0 任一硬门失败即停止，零训练。
本轮禁止 detector、H1b、H2、selector、risk/coverage/AURC、SAR、HRSC、论文修改，以及任何 test
图像 crop、模型前向或性能计算。RarePlanes 是本问题所需的细粒度属性集；单类 HRSC2016 不适配
该下游因果终点。

### 2. G0：outcome-blind 证据修正硬门

- 对官方 metadata、full GeoJSON、tiled annotations 与 253 个 real COG 的输入身份和字节内容做
  一致性核验；保留 raw `cat_id`。canonical CAT 仍只在 `image_id` 后缀为 16 位大写十六进制、
  与 full GeoJSON CAT 及唯一 COG 键三方一致时恢复。两个不共享 parser、常量或中间表的实现必须
  逐键一致得到 253 rows、26 个损坏 raw CAT、227 个 canonical CAT 和 14,707 个 full objects。
- 两个实现分别从全部 COG 的 CRS、affine、宽高构造像素外边界四角的 WGS84 footprint。pair universe
  固定为 253 个 COG 中属于不同基础 component 的全部无序对，不得按距离或当前 component 数删对。
  对每一对，以两个 footprint 球面质心单位向量和的方向为中心建立 WGS84 datum 的局部 Lambert
  azimuthal equal-area 投影；经度先相对该中心解缠，坐标轴固定为 longitude/latitude。若质心单位
  向量和为零或投影失败，G0 直接无效。
- 在上述 pair-local 投影中，令每景单像素地面面积为其 footprint 面积除以 `width*height`，并令
  `tau=max(pixel_area_a,pixel_area_b)`。只有 polygon interior 交面积严格大于 `tau` 才记 overlap
  edge；边界接触或交面积不大于 `tau` 均不合并。两个实现必须公开全部 footprint key、全部跨基础
  component 对的 `intersection_area-tau` 最小绝对裕量摘要、edge 与最终 component；不得把当前报告
  的 0 edge 或 102 components 写成常量，也不得在看到 component 数后改变投影、pair universe 或
  `tau`。
- component 规范 key 唯一固定为：成员 `loc_id` 按十进制升序排列，写成
  `loc:` 加逗号连接的成员；所有 key 再按 UTF-8 字典序排序，以 PCG64(1010) 置换一次，前 25 个
  为 test、后 25 个为 calibration、其余为 train。禁止 r011 的 numeric-tuple 排序、换 seed、
  拆 component 或在两个 manifest 中选择。若最终仍为 102 components，必须复现 test/calibration/
  train 为 `25/25/52 components` 和 `1,919/7,418/5,370 objects`。
- 从 full GeoJSON object 经 metadata CAT 到 source COG 建立唯一、完备且带 multiplicity 的回链。
  tiled annotations 只作次级 lineage 核验，不作为 14,707 census 或 H1a 取样源；必须逐键解释
  full train 10,900 与 tiled unique signature 10,899 的一个对象差异，不得用全局 set-membership
  代替对象回链。
- 对三个冻结二分类逐 split 输出对象数、含该类 component 数、最大 component 占比和 Kish
  effective component 数。对象门为 train/calibration/test `100/20/20`，含类 component 门为
  `10/5/5`；这些门必须真实进入裁决。用改变真实输入或中间值的 fail-closed mutation 验证 CAT
  错并、footprint overlap、split 排序、calibration 19/20、RP1 `w/h+90°` 与非零角扰动，禁止用
  恒真布尔表达式冒充 mutation。
- 独立核验 ResNet-50 与 ViT-B/16 的实现身份、许可、固定版本和架构匹配初始化；实际构建模型并
  严格加载核心权重，完整报告 missing/unexpected keys。只允许三个新二分类 head 尚未初始化；
  静态字典或非严格加载后手写空差异均判 G0 失败。
- G0 compact 证据必须能唯一对应本次实际实现与实际输出；主、独立实现不得读取彼此的 component、
  split、support 或最终状态。任一输入、footprint、lineage、支持、几何、模型身份、独立性或证据
  对应关系不闭合，立即输出 `INCONCLUSIVE_R012_H1A`，reason=`G0_INVALID`，且不得训练。

G0 只可形式核验 test 的 component 身份与既有属性支持；不得提取 test 像素、生成 test crop、把
test 对象交给训练代码或计算任何 test 模型结果。

G0 还必须在任何模型前向前冻结 H1a 的共同 eligible 集合：polygon 合法、三项属性均有冻结映射、
minimum-area 几何有限，且下节规定的共同 square canvas 完整落在 source COG 内。对这个最终共同
eligible 集合重新执行上述每 split×class 的对象门、component 门、最大占比和 Kish 诊断；不得用
全量 14,707 的支持替代 crop 后支持。任一门失败按 `G0_INVALID` 停止。

### 3. 冻结分类器与信息墙

- 只训练 ResNet-50 和 ViT-B/16。每个架构使用一个共享 backbone 与 wing、engine、propulsion 三个
  二分类 head，训练 seed 固定为 `{1201,1202,1203}`，共六次独立 fit；seed 只表示优化重复，
  不作为独立科学样本。
- 三项标签唯一固定为：wing 的 `straight` 对 `{swept, delta, variable swept}`；engine count 的
  `2` 对 `{0,1,3,4}`；propulsion 的 `jet` 对 `{propeller, unpowered}`。未知或缺失值不得重映射，
  `role` 和 `wing_position` 不得作为输入、标签或替代终点。
- 模型输入只有对象像素。禁止把 `loc_id`、CAT、off-nadir、分辨率、对象属性文本、文件名或其他
  metadata 注入模型。所有拟合、超参数选择与停止规则仅在 train components 内按 component 分组
  完成；不得用 calibration 调参或选择 checkpoint。
- 训练只允许上述六次 fit，不做模型、超参数或 checkpoint sweep。每个架构的单一 recipe、固定
  epoch 数、增强、输出尺寸、插值、归一化、优化器、学习率和最终 epoch checkpoint 必须在第一次
  fit 前写定并在六次 fit 中不变；checkpoint 一律取最终 epoch，不做 early stopping。任何 train
  或内部 validation 的 `±10°` response 都不得计算，更不得参与架构、recipe、epoch 或 checkpoint
  选择。六个最终模型、crop 程序和预测规则全部冻结后，calibration 只打开一次。
- 不使用旋转、翻转或其他几何增强；只允许事前写定且不改变空间几何的光度增强。训练失败、非有限
  数值、checkpoint 身份不一致、六次以外的 fit 或 calibration 前后代码改变均进入
  `INCONCLUSIVE_R012_H1A`。

### 4. 唯一 H1a 干预

- full GeoJSON polygon 必须经 source COG 变换到 image-pixel frame，再确定 minimum-area rectangle
  的 `L>=S`、GT center 与 long-side RP1 `theta`。不得使用 nose-tail 航向、经纬度角度、tiled
  重复框或 detector 预测替代。
- 每个对象只预提取一次以 GT center 为中心、边长
  `ceil(1.25*sqrt(L^2+S^2))` 的 axis-aligned square canvas；canvas 必须完整位于 COG 内，不使用
  padding。每一臂都从这同一个 canvas 以单次 bilinear affine render 取得以对象为中心、物理范围
  `1.20L × 1.20S`、输出 `224×224` 的视图，不得先旋转再二次插值。颜色、antialias 和边界规则对
  所有臂完全相同。
- 每个 eligible calibration object 只构造三臂：`theta`、`theta-10°`、`theta+10°`。三臂固定同一
  GT center、同一 `L/S`、同一个预提取 square canvas、同一输出大小和同一 render，只改变 affine
  角参数；不得因任一臂的预测、置信度、裁剪内容或边界表现删对象。对象资格与边界规则在模型前向
  前冻结。
- 每一臂同时计算 `theta` 与 `theta+180°` 两个 RP1 等价视图，并先平均二者的类别概率再作 argmax；
  这一步对 clean 与两种扰动完全相同。加入像素级 identity、`theta+180°`、`w/h+90°`、只改角度和
  非零 `±10°` 的 mutation，任一失败都属于实现无效。

### 5. 唯一估计量与推断

对架构 `m`、seed `s`、属性 `k`、臂 `t` 和对象 `i`，定义错误
`e[m,s,k,t,i]=1(argmax(p)!=y)`。对每个属性类别 `c`，先在每个含 `c` 的 component 内平均对象
错误，再对所有含 `c` 的 component 等权，最后对两个类别各权 `1/2`，得到
`R[m,s,k,t]`。缺少某类的 component 不删除、不补零，也不进入该类分母。

六个 co-primary 效应唯一为：

`Delta[m,k] = mean_s( (R[m,s,k,+10] + R[m,s,k,-10])/2 - R[m,s,k,clean] )`

即 2 个架构 × 3 个属性。`+/-` 先平均，seed 再等权；不得拆成更多可选择假设，也不得把 seed、对象
或 tile 当独立重复。架构与属性等权的 grand effect 只作摘要，不能救回任何 co-primary。

使用 calibration 的 25 个冻结 component，以 PCG64(12012) 做 50,000 个有效的同步 component
bootstrap draw；同一 draw 的
component multiplicity 同时用于全部架构、seed、属性和三臂，并完整重算 class-balanced ×
component-equal 风险。每个属性类的分母是本 draw 中含该类 component 的 multiplicity 总和；任一
分母为零的 draw 不进入有效集合，按同一随机流顺次取下一 draw，并公开零分母 draw 数；不得补行、
另换随机流或改成对象 bootstrap。

以 50,000 个有效 draw 的 sample standard deviation（`ddof=1`）定义六格 `s[j]`，并令
`u[b,j]=Delta[b,j]-Delta[j]`。对 `s[j]>0` 的格构造
`M[b]=max_j(abs(u[b,j]/s[j]))`，取固定 type-7 的 95% 分位 `q`，报告 simultaneous interval
`Delta[j] ± q*s[j]`。若某格 `s[j]=0`，该格不进入 `M`，区间退化为 `[Delta[j],Delta[j]]`；若六格
全为 0，则 `q=0`。只有非有限 `Delta` 或 `s` 才是推断无效，零方差本身不是 inconclusive。

普通逐格区间只作披露，不能用于裁决。每格功效唯一固定为
`power[j]=mean_b(0.020 + u[b,j] - q*s[j] > 0)`；它表示真实效应为 `0.020` 时 simultaneous lower
bound 排除零的概率，不得把观测点估计门 `Delta>=0.020` 并入功效。`s[j]=0` 时该功效为 1。
六格最小功效必须至少 0.80。

另以同一 50,000 个同步 draw，对六格 seed-averaged clean risk
`C[m,k]=mean_s(R[m,s,k,clean])` 构造独立的六维 max-standardized simultaneous 95% interval，
计算规则与上述 `M/q` 相同，零方差沿用退化区间规则。进入 H1a 科学裁决前，六格 clean interval
upper 必须全部严格小于 `0.5`，且 18 个 architecture×seed×attribute head 在共同 eligible
calibration 集上均不得把全部对象预测为同一类别；否则输出 `INCONCLUSIVE_R012_H1A`，
reason=`TRAINING_UTILITY`，不得 PASS 或 KILL。

### 6. 三态裁决

按以下优先级只输出一个主状态：

1. G0、训练身份、信息墙、crop/RP1 mutation、固定支持、独立复算或同步推断任一无效：
   `INCONCLUSIVE_R012_H1A`；
2. 任一 clean utility 门失败：`INCONCLUSIVE_R012_H1A`，reason=`TRAINING_UTILITY`；
3. 执行有效且任一格 simultaneous upper bound 小于 `0.020`，说明该格已排除实质效应：
   `KILL_R012_H1A`；
4. 没有第 3 项证据，但任一格对 `0.020` 的功效低于 0.80：`INCONCLUSIVE_R012_H1A`，
   reason=`POWER`；
5. 六格功效全部至少 0.80，但未同时满足六格 `Delta>=0.020` 且 simultaneous lower bound 大于 0：
   `KILL_R012_H1A`；
6. 只有六格全部满足功效、`Delta>=0.020` 与 simultaneous lower bound 大于 0，才输出
   `PASS_R012_H1A`。

`PASS_R012_H1A` 只证明：在冻结的两个属性分类器和 RarePlanes calibration components 上，
规范化算子的 `±10°` 角参数误差会造成跨架构、跨三属性的可重复总效应；该效应包含仿射重采样和
背景支持变化，不能声称“像素不变的纯角度效应”。它也不证明 detector rescue、无 GT
风险控制、human-machine 共同规律或顶刊已经成立；只允许 B/C 另议下一轮 H1b/H2。任何状态都不
自动打开 test、训练 detector、恢复 selector/head/SAR 或修改论文。

### 7. 必须提交的可复算证据

提交 G0 主/独立逐项差异、规范 component 与 split 清单、逐 split×class 支持/最大占比/Kish、
lineage multiplicity 与 tiled 差异解释、几何和 fail-closed mutations、两分类器严格 build/load
差异、训练配置与六个模型身份、三臂逐对象 compact predictions、六格点估计、同步 bootstrap、
simultaneous intervals、功效表、裁决 reason，以及不读取 test 性能的独立验证。原始影像、模型
权重和大体积中间张量不进入普通版本库。
