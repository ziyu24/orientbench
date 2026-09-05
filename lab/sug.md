# SERVER 科学指令

## r013：RarePlanes H1a 六次全新拟合与 calibration-only 生死门

### 1. 唯一问题与结论边界

r012 的 G0 已通过，但 H1a 在 calibration 打开前因外部终止而执行无效；它没有产生科学 PASS 或
KILL。r013 只回答同一个必要性问题：在同一飞机的中心、长短边、source canvas 和分类器全部固定
时，仅把定向规范化角从 theta 改为 theta-10° 或 theta+10°，是否会使 wing、engine 和
propulsion 三项不同属性的 balanced error 在 ResNet-50 与 ViT-B/16 上稳定增加至少 2 个百分点。

RarePlanes 提供本问题必需的独立细粒度飞机属性；单类 HRSC2016 不适配这个下游因果终点。本轮
禁止 detector、H1b、H2、selector、risk/coverage、SAR、HRSC、论文改写，以及任何 test 图像
crop、模型前向或性能计算。

### 2. r012 继承项与严格隔离

- 继承 r012 已通过的 G0：253 个 metadata/COG records、227 个 canonical CAT、14,707 个 full
  objects、lexical-PCG64(1010) 的 test/calibration/train 25/25/52 component split，以及共同
  eligible、支持、lineage、几何和分类器初始化身份。只做输入与既有 G0 compact 证据的一致性
  复核，不重算 split、不更换对象、不重开数据资格选择。
- 继承已冻结的 4,065 个 train eligible objects、共同 source canvas 内容、对象到 canvas 的
  一一对应及 H1a 的 crop/render 规则。身份不一致立即输出 INCONCLUSIVE_R013_H1A，
  reason=INPUT_IDENTITY；不得重提取后静默替代。
- r012 已完成的两个模型、三个未完成状态及其任何训练后参数全部隔离，只能作为执行失败证据。
  r013 不得加载、热启动、平均、比较或据此选择架构、recipe、epoch、seed 或模型。
- r013 的六次拟合全部从 r012 冻结的架构匹配初始化重新开始；三个新二分类 head 重新初始化。
  任何 r012 学得参数进入 r013 即执行无效。

### 3. 六次全新拟合

- 架构固定为 ResNet-50 与 ViT-B/16；每个架构固定 seeds 1201、1202、1203，共六次独立 fit。
  seed 只表示优化重复，不作为独立科学样本。
- 每次 fit 使用同一共享 backbone 和 wing、engine、propulsion 三个二分类 head。标签映射、仅
  train component 拟合、对象像素唯一输入、无几何或光度增强、raw RGB/255、单次 bilinear
  affine render、theta、物理范围 1.20L×1.20S、224×224，全部沿用 r012 冻结定义。
- 标签固定为：wing 的 straight 对 swept/delta/variable swept；engine count 的 2 对 0/1/3/4；
  propulsion 的 jet 对 propeller/unpowered。未知或缺失值不得重映射，role、wing_position、
  loc_id、CAT、成像 metadata 和文件名不得进入模型。
- 优化固定为 AdamW，学习率 0.0003，weight decay 0.0001，batch size 24，固定 8 epochs；
  checkpoint 只取 final epoch。禁止 early stopping、超参数或 checkpoint sweep，也禁止根据
  train 上的 ±10° response 选择任何设置。
- 在六次正式拟合之前，允许各架构在同一冻结 train batch 上做一次加载、前向、反向和有限值
  预检；不得更新参数，不得保存候选模型，不得读取 calibration/test，也不得把预检计作 fit 或
  用于选择 recipe。
- 六次拟合开始后，任一次未完成、出现非有限值、模型身份不一致、产生第七次 fit，或在全部六个
  final-epoch 模型封存前读取 calibration，均立即输出 INCONCLUSIVE_R013_H1A，
  reason=TRAINING_FAILURE。不得补跑缺失单元，不得把 r012 与 r013 模型混合凑数。
- 六个 final-epoch 模型全部完成且身份封存后，calibration 只打开一次；此前 test 始终封闭。

### 4. 唯一 H1a 干预

- 每个 eligible calibration object 只用已冻结的同一 source canvas 构造三臂：theta、
  theta-10°、theta+10°。三臂固定 GT center、L/S、输出大小、颜色、antialias、边界规则和单次
  bilinear affine render，只改变角参数；不得按预测、置信度、内容或边界表现删对象。
- 每一臂同时计算 theta 与 theta+180° 两个 RP1 等价视图，先平均类别概率再 argmax；clean 与
  两种扰动完全相同。像素 identity、theta+180°、w/h+90°、只改角度和非零 ±10° mutation 任一
  失败，输出 INCONCLUSIVE_R013_H1A，reason=IMPLEMENTATION_INVALID。
- calibration 资格和全部三臂在任何模型前向前一次性冻结。不得在看到预测后修改对象、干预、
  标签、阈值或聚合。

### 5. 估计量与同步推断

对架构 m、seed s、属性 k、臂 t、对象 i，以 argmax 是否错误定义 e[m,s,k,t,i]。对每个属性类别，
先在每个含该类的 component 内平均对象错误，再对含该类的 component 等权，最后对两个类别各权
1/2，得到 R[m,s,k,t]；缺少某类的 component 不补零，也不进入该类分母。

六个 co-primary 效应固定为：

Delta[m,k] = mean_s((R[m,s,k,+10] + R[m,s,k,-10])/2 - R[m,s,k,clean])

即 2 个架构×3 个属性。正负扰动先平均、三个 seed 再等权；架构属性 grand effect 只作摘要，不能
救回任何一格。

在冻结的 25 个 calibration components 上，使用 PCG64(12012) 生成 50,000 个有效同步 component
bootstrap draws；同一 draw 的 component multiplicity 同时用于所有架构、seed、属性和三臂，
并完整重算 class-balanced×component-equal 风险。零分母 draw 按原随机流顺次替换并披露数量。

以 sample standard deviation（ddof=1）计算六格 s[j]；对 s[j]>0 的格，以每个 draw 的
max_j(abs((Delta[b,j]-Delta[j])/s[j])) 的固定 type-7 95% 分位 q 构造 simultaneous interval
Delta[j]±q*s[j]。零方差格使用退化区间；六格全零时 q=0。每格功效固定为
mean_b(0.020 + Delta[b,j]-Delta[j]-q*s[j] > 0)。普通逐格区间只披露，不参与裁决。

另用相同 draws 为六格 seed-averaged clean risk 构造独立六维 simultaneous 95% interval。六格
clean upper 必须全部严格小于 0.5，且 18 个 architecture×seed×attribute head 均不得在共同
eligible calibration 集上预测单一类别；否则输出 INCONCLUSIVE_R013_H1A，
reason=TRAINING_UTILITY。

### 6. 唯一三态裁决

按优先级只输出一个状态：

1. 输入、训练、信息墙、crop/RP1 mutation、支持、独立复算或同步推断任一无效：
   INCONCLUSIVE_R013_H1A；
2. 任一 clean utility 门失败：INCONCLUSIVE_R013_H1A，reason=TRAINING_UTILITY；
3. 执行有效且任一格 simultaneous upper 小于 0.020：KILL_R013_H1A；
4. 不满足第 3 项但任一格对 0.020 的功效小于 0.80：
   INCONCLUSIVE_R013_H1A，reason=POWER；
5. 六格功效均至少 0.80，但未同时满足六格 Delta 至少 0.020 且 simultaneous lower 大于 0：
   KILL_R013_H1A；
6. 仅当六格全部满足功效、Delta 至少 0.020 和 simultaneous lower 大于 0：
   PASS_R013_H1A。

PASS 只证明冻结分类器与 RarePlanes calibration components 上规范化角误差存在跨架构、跨属性
的可重复总效应；它包含仿射重采样和背景支持变化，不是像素不变的纯角度效应。PASS 只允许另议
H1b 的 predicted-angle→GT-angle rescue，不能声称 JPRS/TGRS 已成立。KILL 关闭 RarePlanes
顶刊扩展并回到现有测量稿收敛；INCONCLUSIVE 不得包装成正负科学结论。任何状态均不得打开 test
或自动启动后续轮次。

### 7. 必须提交的可复算证据

提交继承输入身份复核、预检不更新参数的证据、六次全新拟合的初始化与 final-epoch 模型身份、
calibration 开启时点、三臂逐对象 compact predictions、六格点估计、同步 bootstrap、
simultaneous intervals、功效、clean utility、mutations、独立复算和唯一裁决。原始影像、模型
参数和大体积中间量不进入普通版本库。
