# OrientBench：全项目创新重评与下一步研究建议

日期：2026-09-04。科学审计基线：`288f05be66e4f9b78b8e51306caf533251c2b676`。
本报告不采用历史期刊标签、内部签字或验收 token 作为创新证据。

## 结论

目前能成立的是一篇有用的遥感方向评价与测量论文的科学核心；我不能据现有创新说服自己它已达到
TGRS / ISPRS JPRS。JSTARS 类领域实证论文是合理候选定位，但“strong JSTARS 已成立”也没有
充分依据，更不等于保证录用或正式分区评级。关键缺口不是还少几个数据集、模型或显著性星号，
而是尚未产生能越过已有几何、等变性、方向规范化与校准工作的新增知识。

最新 r013 不能接受“实现有效，仅功效不足”。公开生成器把 CAT 当作唯一影像键，但同一 CAT
可以包含不同地点的影像；独立官方数据重建发现 calibration 的 7,418 个 full objects 中
2,318 个会被映射到错误 source COG。B 正式状态保留 `INCONCLUSIVE_R013_H1A`，原因优先为
`INPUT_IDENTITY / IMPLEMENTATION_INVALID`。已报告的效应、区间和 POWER 暂不进入科学判断。

唯一保留的创新候选是“有限资源下显式方向测量相对强不变决策的增量价值与可预测边界”，不是
继续证明一个没有旋转增强的分类器怕角扰动。该候选尚未成熟到可以签下一轮训练；本次不下达
SERVER 命令，不打开 test，不恢复 SAR、selector/head 或 detector 训练。

## 1. 复核范围与证据等级

本次先读取同名公开项目 lessons，再同步权威 HTTPS main；读取当前四份 lab、项目规则、架构、
归档说明和最近提交。盘点当前源码/配置与归档父树 `09381f7` 的全量文件，按科学主张回读关键
原始表、协议及生成代码，并由独立历史审计、r013 实现审计和 C 创新红队交叉检查。

覆盖旧科学序列 r001—r052 和当前序列 r001—r013，不把同号轮次混为一轮。不是声称逐字阅读了
归档的 3,278 个文件，更不是重新运行所有实验。没有访问服务器磁盘；当前远端缺 r012/r013
compact 原始预测、draws、canvas/model manifest 的可读取发布，因此六格结果仅能引用为机器
报告。本次真正重新计算的是官方 metadata/GeoJSON 的来源键、连通分量、split 和错源计数。

文献检索覆盖评价分解、方向几何/角编码、旋转等变与规范化、飞机细粒度识别、检测校准和决策效用。
优先使用作者论文、正式 proceedings 和官方数据。全文不可获取的近邻只按机构摘要或正式摘要
界定碰撞，不声称已复现其结果；检索不到完全同题论文不构成“首个”证明。

## 2. 当前结果到底出了什么问题

### 2.1 r013 错源反例与范围

`src/orientbench/r013/prepare_calibration.py:21` 用
`{image_id.split('_', 1)[1]: image_id}` 构造 CAT-only 字典；第 26 行仅按 `cat_id` 选图。
重复 CAT 的后行覆盖前行。相比之下，G0 的几何使用 `(loc_id, CAT)` 查图，其
`eligible_manifest` 还明确保存了 `source_cog`。当前提取器没有消费这一身份字段，而把原图的
像素中心、L/S 用于另一幅图。shape 和文件 SHA 一致无法证明裁到的是声明的飞机。

官方数据是 253 个 image records、227 个 CAT，CAT 并非 image 主键。例如对象 189、214、216
属于 `loc=44, CAT=1040010043B54900`；正确图为 `44_1040010043B54900`，代码却选
`107_1040010043B54900`。独立审计的官方 COG header 显示前者位于 Henderson、4768×9250，
后者位于 North Las Vegas、9706×4810，地理 affine 也不同；不是同图别名。

按既有 lexical-PCG64(1010) split 重建，7,418 个 calibration full objects 中有 2,318 个错源，
涉及 20 个 loc–CAT 键、两个 source components。报告 eligible=7,416，最多排除两个 full
objects，故在这一冻结总体下至少 2,316 个 eligible 会受影响；没有服务器 manifest 不能确定
最后两个排除项。31.25% 是对象行比例，不能当成 component-equal 风险中的权重比例。

同 CAT 地点已在同一 component，故这里不是跨 split 泄漏，而是同 component 内标签、几何与
像素错配，破坏了“同一飞机三臂干预”。不能删除这两个 component 挽救原估计量。

### 2.2 其他会限制验收的代码事实

- `evaluate_model.py` 把 `theta180_pair_order_invariant` 硬写为 True；部分几何检查没有对
  真实 render 进行独立改写。`verify.py` 直接相信生产者的 mutation 布尔值。
- 第二统计实现只核对 Delta、sd、q，没有完整复算并比对 power、上下界和 clean simultaneous
  intervals；head 非恒定检查在三臂循环中覆盖，最终不是专门检查 clean。
- `finalize.py` 的 valid 不含完整 source、模型数量、初始化身份；test 未使用是常量声明。
  `s['delta']` 为二维表，却在后续 effect 分支逐行与 float 比较，存在潜在 TypeError。
- 4,065 个训练对象是新 train split 与旧 `Public_Train==1` 再取交集后的 eligible 集。
  新 split 的 5,370 个 full train objects 中，4,068 个旧 flag=1、1,302 个旧 flag=0。
  r013 已明文继承 4,065，所以不是 r013 暗改样本；但不能称为完整新 train 自然筛除后的集合，
  更不能用 G0 全 train 支持表替代实际训练支持。

已证明的是公开代码在该冻结总体上的错源，不是逐一查看服务器实际 canvas。若实际执行了
未发布修复版本，应先公开其代码与原始证据；在运行与产物绑定缺失时，六格仅按潜在受污染处理。

机器报告的六格效应为 −1.5793pp 至 +2.0956pp，功效 0.07354—0.58798。这些数字目前既不能
证明方向无用，也不能估计新的样本需求。输入错误先于效应/功效判断，原“实现门通过”表述撤销。

### 2.3 可独立重建错源计数的只读代码

以下只读取官方公开元数据，不读影像像素、不运行模型；需 Python 与 NumPy。它重建的是既有
102-component 基础图与注册 split，不替代服务器全部 COG footprint/eligible 审计。

```python
import csv, hashlib, io, json, urllib.request
from collections import defaultdict
import numpy as np

base = 'https://rareplanes-public.s3.amazonaws.com/real/metadata_annotations/'
names = ['RarePlanes_Public_Metadata.csv', 'RarePlanes_Public_All_Annotations.geojson']
raw = [urllib.request.urlopen(base + n, timeout=60).read() for n in names]
meta = list(csv.DictReader(io.StringIO(raw[0].decode('utf-8-sig'))))
features = json.loads(raw[1])['features']
parent = {int(f['properties']['loc_id']): int(f['properties']['loc_id']) for f in features}
def root(x):
    while parent[x] != x:
        parent[x] = parent[parent[x]]
        x = parent[x]
    return x
first, exact, producer = {}, {}, {}
for row in meta:
    loc, image = int(row['loc_id']), row['image_id']
    cat = image.split('_', 1)[1]
    assert (loc, cat) not in exact
    exact[loc, cat] = image
    producer[cat] = image
    if cat in first:
        parent[root(loc)] = root(first[cat])
    else:
        first[cat] = loc
groups = defaultdict(list)
for loc in sorted(parent):
    groups[root(loc)].append(loc)
keys = sorted('loc:' + ','.join(map(str, xs)) for xs in groups.values())
order = np.random.Generator(np.random.PCG64(1010)).permutation(len(keys))
cal = {int(v) for j in order[25:50] for v in keys[int(j)][4:].split(',')}
objects, bad, bad_keys = [], [], set()
for oid, feature in enumerate(features):
    p = feature['properties']
    loc, cat = int(p['loc_id']), p['cat_id']
    if loc not in cal:
        continue
    objects.append(oid)
    if exact[loc, cat] != producer[cat]:
        bad.append(oid)
        bad_keys.add((loc, cat))
print(json.dumps(dict(metadata_rows=len(meta), cats=len(producer), components=len(keys),
    cal_full_objects=len(objects), wrong_source_objects=len(bad),
    affected_loc_cat_keys=len(bad_keys),
    input_sha256=[hashlib.sha256(b).hexdigest() for b in raw]), indent=2))
```

本次 B 与独立审计重建结果均为 `253 / 227 / 102 / 7418 / 2318 / 20`。
官方 CSV SHA-256：`005eb9c6c4ab0f0fea1f8402f202066b6f4d29617ef263f72b1be34dea35edec`；
GeoJSON：`3e4786590cb350038d18120732787b1a6586408ab0685d344ef0730815e79ecb`。
来源：[官方 metadata](https://rareplanes-public.s3.amazonaws.com/real/metadata_annotations/RarePlanes_Public_Metadata.csv)、
[官方 GeoJSON](https://rareplanes-public.s3.amazonaws.com/real/metadata_annotations/RarePlanes_Public_All_Annotations.geojson)。

## 3. 整个项目留下的科学资产，而非任务号数量

| 证据 | 本次可保留的事实 | 对创新的实际贡献与限制 |
| --- | --- | --- |
| 六单元构造性扰动 | AP50 不变，AP75 降 17.57—39.83pp，平均角误差增约 29—32° | 方向不足以被 AP50 约束的反例；扰动读取 matched GT 并搜索保持 IoU>.5 的最大角，不能冒充自然错误发生率 |
| 六单元非 oracle 固定 ±15° | AP50 降 2.88—9.51pp，AP75 降 3.74—17.20pp | 更强的诚实测量证据：高 IoU 评价更敏感；同时反驳“AP50 普遍不敏感” |
| 八单元形状条件风险 | AR=2.1 的同矩形 IoU=.75 容差 15.3297°；severe 率 0.19%—1.67% | 几何解释与测量定义有用，但仍是几何代理事件，不是新信息论或现实损失 |
| 人工 600 目标 | 450 双数值对，分歧均值 2.3112° [1.9970°,2.7854°]；103 双 ambiguous | 可标性锚点；2.31° 条件于双方可数值标注，不是全样本 GT 误差或不可突破的噪声地板 |
| LTT 风险证书 | α=.03 六格 coverage=1；校准上界 .00301—.02588 | 已有理论的应用；仅匹配成功高 AR 对象，空 eligible 图记零，漏检/FP 不入此风险；无非平凡选择收益 |
| r034 | 616,184 行，12 primary、0 witness；AR-only DoD 在 DIOR/DOTA 为 probe 的 8.69/3.10 倍 | 原独占图像信号主张未通过对照；raw-angle 风险仍有描述性信号，不能反向夸大成全部纯公式循环 |
| 旧 r045 | 98 HRSC 图，收益 −.00195195，CI [−.00759691,.00355364] | 冻结策略跨域的几何代理负证据；其 loss=min(1,GT_AR/2×sin(angle_error))，不是实测下游应用 |
| 后续候选 | 无保留下来的正向可迁移方法；r004/5、r006、r013 又存在执行/操纵无效 | 无效不是科学否证；但不能用审计次数抵偿缺失的新发现 |

固定剂量数据源为归档 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/` 的
`reports/fixed_dose_tracks_r011.csv` 与 `scripts/run_joint_closure_r011.py`：S 臂对预测 AR≥2.1
施加固定正/负角，分别计算完整 AP 后取算术平均，不使用 GT 选择扰动幅度或符号。
例如 DIOR/22：AP50 53.68→50.43，AP75 35.03→22.81；SODA/4：72.95→63.44、38.05→20.85。
该表与早期构造扰动表的评价器/基线版本不能逐行混拼，尤其 FAIR1M 基线存在小幅差异。

风险证书所用 held-out 图像中，含 eligible 对象的比例仅为 59.2/61.7/62.5/57.0/35.4/35.8%。
因此须明写条件风险及空图零损失定义，不能包装为全检测系统的安全证书。

原始证据路径和其余成功/失败/未执行轮次详见 `lab/result.md`。本次不删除旧负结果，不让
构造反例、预后审计、执行失败与前瞻确认共享同一个科学身份。

## 4. 外部近邻到底占据了什么

下列是针对科学主张的碰撞表，不是以论文发表场所给本项目打分。

| 近邻及原始来源 | 已有内容 | OrientBench 尚须证明的增量 |
| --- | --- | --- |
| [TIDE, ECCV 2020](https://arxiv.org/abs/2008.08115) | 把检测指标背后的不同错误作分解审计 | 不能只说 mAP 不够；需要新的方向特异发现及由此改变的评价/决策 |
| [Multivariate Confidence Calibration, CVPRW 2020](https://arxiv.org/abs/2004.13546) | 检测置信校准显式考虑位置、尺度等变量 | 分类 score 不等于综合定位可靠性并不是新发现 |
| [Rethinking Boundary Discontinuity, CVPR 2024](https://arxiv.org/abs/2305.10061) | 从 box/object 角映射解释边界并提出 ACM | 不能把 le90/w-h discontinuity 或 OBB 轴≠语义轴本身当成新机制 |
| [Structure Tensor OBB, 2024 作者预印本](https://arxiv.org/abs/2411.10497) | 以张量框表示处理边界与对称性稳健性 | 参数化改名、普通结构张量和 shift 稳健性并非空白；本报告不凭预印本臆定正式发表身份 |
| [ReDet, CVPR 2021](https://arxiv.org/abs/2103.07733) | 旋转等变特征与 rotation-invariant RoI Align | 方向信息与不变识别已经联合研究，不能只对照普通无增强网络 |
| [MessDet, ICCV 2025](https://arxiv.org/abs/2507.09896) | 比较严格/近似旋转等变，讨论下采样破坏并提出轻量检测器 | 普通 alias 或“旋转不稳定”不足以区别于已有检测研究 |
| [Fine-Grained Airplane Recognition, IGARSS 2023，作者机构记录](https://athene-forschung.unibw.de/?change_language=en&id=154661) | 在 FAIR1M 分离检测/识别，并以机头方向规范化改善结果 | RarePlanes H1a 就算正向，也只补充另一条件下的规范化敏感性，不自动成为新应用原理 |
| [Impact of Geometric Priors, ISPRS Annals 2026](https://isprs-annals.copernicus.org/articles/XI-3-2026/289/2026/isprs-annals-XI-3-2026-289-2026.pdf) | 把长度、翼展、翼掠角、引擎等几何信息用于飞机细粒度类别识别 | 几何改善下游飞机识别已有直接近邻；其属性是输入，不是本项目三项属性终点的同题复现，也不把 Annals 误称 JPRS |
| [G-CNN, ICML 2016](https://proceedings.mlr.press/v48/cohenc16.html) | 用群对称性/权重共享降低样本复杂度 | 必须正面对照增强/等变/不变表示，不将归纳偏置收益误称新信息 |
| [Equivariant Frames, ICML 2024](https://proceedings.mlr.press/v235/dym24a.html) | 分析 canonicalization 连续性障碍并构造 weighted frames | 多角平均或平滑规范化不是新理论；其定理不能不核查假设就套到有限栅格裁图 |
| [Learn then Test](https://arxiv.org/abs/2110.01052)；[Risk-Controlling Prediction Sets](https://arxiv.org/abs/2101.02703) | 已有有限样本风险控制工具 | 换几何 loss 并套上证书不是新的风险理论，须证明非平凡且有效的决策价值 |
| [Utility-Directed Conformal Prediction, ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/0c6b452f1bbfb6905f6bac957d73b321-Abstract-Conference.html) | 将下游决策损失纳入预测集合并保持覆盖保证 | H2 若只是多赢一点 score 或套效用集合，仍不足以成为新的贡献 |

这不是说这些论文已经完成本项目每一个控制实验。差别确实存在：OrientBench 有统一冻结总体、
成组反例、人工可标性与独立来源下游设计。但“控制更严格”与“发现新的遥感规律”不是一回事。

## 5. 为何一直没有创新跃迁

第一，反复用同一 GT 几何产生自变量、容差、风险和所谓应用损失。多种漂亮数字可以仍在回答
一个矩形问题；600 人工目标也没有把它变成外部业务证据。

第二，H1a 选择的 wing/engine/propulsion 是内在旋转不变属性，训练禁用旋转增强，干预又改动
狭长裁剪支持。正效应首先说明这条特定处理流程脆弱，而不是遥感决策必须依赖更准确的检测角。
H1a 是本项目旧路线自行规定的门，并不是方向价值在所有应用中的数学必要条件。

第三，许多轮次止于输入身份、操纵有效性或执行语义，没有真正检验完假设。r013 是一个
典型：两个程序复算出同一数字，仍可能对同一批错图做统计。原因是验证集中在输出自洽，缺少
跨越独立原始来源的语义反例；不是需要再添审批层、签字或复杂目录。

第四，六格全≥2pp、100 components、五 detector families、三人标注都是特定设计选择，不是
顶刊统一标准。2pp 若没有实际代价解释，就不能成为创新充分条件；把它跑显著仍可能只重复旧知。
增加 seed 不会增加25个独立来源的数量，但可以降低优化重复的不确定性；增加bootstrap draws
只减少数值 Monte Carlo 误差。基于已观察效应分布的
平移式 power 只能作设计诊断，不能替代事前设计功效，更不能用当前错图分布设计新增样本。

第五，缺少最强反例对照。如果旋转增强、完整支持裁图或不变识别已让损失消失，那么开发一个
更准的角度分数并非该应用的必要工作。旧路线先假定方向可靠性服务有价值，再寻分数，顺序颠倒。

由此我撤回“补完 H1/H2 就自然升级”以及“TGRS 必须有物理模型/新网络”的绝对说法。顶级工作
也可以是深刻测量发现；但本项目现在还缺乏足够新、重要、可外推且改变实践的发现。

## 6. 下一步：只保留一个真正可否证的新问题

工作问题：**在相同训练资产、像素和总计算预算下，显式方向估计相对强旋转不变决策，何时有
实质、可迁移的增量价值，何时应完全绕过它？**

### 6.1 为何这不同于旧 H1a

条件于同一训练资产/外部知识 T，若预测角是完整输入 X 的确定函数 f_T(X)，任意决策
h_T(X,f_T(X)) 都可组成 g_T(X)。因此对不限函数类的完整信息决策，预测角本身不凭空增加
信息。这是简单的函数复合，不是本项目的新定理。

现实收益可以来自像素压缩、有限样本归纳偏置、外部预训练、优化和计算预算，须逐一分清。
若检测器看整景/metadata 而分类器只看裁图，角度对后者可能真的带来额外信息，不能套用上一句。
GT 角度、GT 中心和尺度均属于特权信息；oracle 收益不是已部署收益。属性内在不变也不意味着
实际数据中的方向、地点、背景与类别统计独立，必须排查来源捷径。

### 6.2 最小有判别力的设计草案（未签发实验）

| 比较臂 | 用途与约束 |
| --- | --- |
| 原硬规范化、无增强分类器 | 只作旧 H1a 诊断，不作最强基线 |
| 完整支持、方向无关输入＋旋转增强 | 首要廉价反例；所有合法训练数据与调参预算公平 |
| 强等变/不变表示 | 排除普通网络缺乏归纳偏置；群视图数、训练和推理成本计入总预算 |
| 预测 OBB 轴规范化 | 部署候选；角估计使用的信息和成本不得隐藏 |
| GT 几何轴/独立语义轴规范化 | 分开作特权诊断参考，不喂给部署方案或按结果挑最有利轴；不预设其为严格性能上界 |

先在不打开 test 的设计阶段确定一个由真实属性用途/错误代价支持的 primary endpoint，其他
属性用于复现与异质性；这不是事后从 r013 六格挑正结果。若改 primary，须承认新问题、公开
选择理由与此前已看过 calibration 的事实。最终确认只能使用仍未消费且支持充分的来源集合。

研究变量是预先有应用依据的资源预算和物体/关键部件的有效像素分辨率，不是提高角扰动剂量
以追显著。矩形与方形输入存在支持范围、各向异性缩放和有效分辨率差异，不能只说都为224×224
就算公平。应分开匹配完整可见支持与有效采样密度，控制插值及总计算；做机制分解和预算比较时
分别说明哪个因素固定、哪个是干预，不能宣称所有因素同时相等。

候选估计量是预定预算下最强、事先冻结的不变决策臂风险减去方向辅助臂风险，并报告完整
accuracy–cost 比较。有限组基线的最优结果只是经验比较，不能写成 Bayes 风险或信息论极限。
若 GT/oracle 臂都没有实质收益，或普通增强/完整支持已消除差异，就停止本项目所列属性方案的
方向可靠性投入；这不是所有角辅助方法的不可能性定理，真实几何轴也未必最利于特定有限分类器。
若有收益，再问能否以实测预测角恢复、是否跨来源存在、代价是否值得。

### 6.3 什么结果才值得冲顶刊

单纯画出几条预算曲线仍是比较研究。所需增量是一种可事前预测的机制：例如说明何种可观测的
部件像素/支持损失与预算条件会产生方向辅助收益，给出量化预测，并在未参与拟合的来源、架构
或预算条件下接受失败检验。普通长宽比容差或经验回归拟合本身不够；必须排除既有采样几何、
旋转归纳偏置和来源相关性已能解释的部分。

现在没有这项机制的理论或实验证据。因此它是唯一值得继续论证的候选，不是现成顶刊方案，
更不应写成“下一轮必拿下”。事前功效必须按真正独立来源与合理效应/相关性情景规划；若现有
未消费来源不够，先报告不可行，不自动换 split、追加相似数据或无限训练。

## 7. 立即可做的证据修复，与创新实验分开

建议 SERVER 下一次若获授权，只做 correction-only：公开原始 compact 证据；按 G0 的
source_cog 与 loc–CAT 双重绑定逐对象检查投影/canvas；用来源正确、身份可验证的既有六模型
重建同一 calibration 三臂，独立复算所有统计及真正的 render mutations。冻结模型、样本规则、
split、标签、阈值，不重训、不删受影响 component、不打开 test、不执行 H1b/H2。
如果训练输入或模型身份也不能复核，则停止重算并如实保留 inconclusive，不能静默补训练。

这可能需要既有模型的有限前向，但不是新模型实验，也不是顶刊方案本身。修复后的 calibration
属于看过受污染结果后的透明重建，不能改称一次全新的前瞻盲验证。修复即使仍为 POWER，也不
自动授权增加样本或种子；结果修复即使 PASS，也不自动授权旧 H2 selector。

本次仅给研究建议并完成 B 端文档纠偏，没有控制 SERVER，也没有签发新的 r014。
已结束 r013 的协议由 Git 历史保留，当前单槽回到 `NO_ACTIVE_TASK`。

## 8. C 的独立意见与 B 的回应

C 不签新的 GPU 顶刊实验，认为 r013 即使正确且全过，也只是已有飞机规范化工作的更严格局部
验证。C 拒绝把“OBB 轴不等于语义轴”、多角平均、von-Mises 或 utility-aware selector 单独
重新命名为创新；B 接受。

C 对有限预算候选的保留意见是：外部知识与信息集必须相同；有限样本和优化也可能解释收益；
现实方向–类别相关性不等于内在属性改变；经验 frontier 仍不保证创新。B 已将这些反例写入
设计，不把 C 的同意当作科学证明。

最终建议：保住可发表的测量核心，同时只为能改变科学推断对象的新机制保留探索资格。若新机制
不能战胜已有规范化/不变性解释，就收敛现稿；宁可明确停止，也不靠追加任务号维持顶刊叙事。
