# B/C 科学讨论

## 当前状态

- 2026-09-04 全项目创新重评覆盖归档科学序列与当前 r013；本次不使用历史期刊标签作为依据。
  完整证据、近邻文献、否证设计和 C 反对意见见 `doc/INNOVATION_REASSESSMENT_20260904.md`。
- r013的CAT-only错源历史不变；r014已发布修正概率。2026-09-05 B从发布端独立复算
  7,416对象、25 components、50,000 draws及全部区间/功效/clean utility，数值一致。
  六格效应−1.4622至+2.1439pp，功效0.07378至0.58606；这不是新方法或跨架构正向收益。
- r014剩余验收已完成：全量7,416 calibration来源像素、实际render和真实反例入口均未发现
  新的语义错误；但r013原fit与calibration冻结manifest缺失，训练身份链不可恢复。终态为
  `INCONCLUSIVE_R013_H1A / INPUT_OR_IMPLEMENTATION`；POWER仅保留为条件数值诊断。
- 当前可支持领域测量论文的核心素材，尚不能说服 B/C 其创新已达 TGRS/JPRS；旧“strong JSTARS
  已成立”及“H1/H2 通过即可升档”均撤回，不以模型数、2pp 或内部签字代替新意判断。
- r014已按合同终结：不重训、不再模型前向、不打开test、不启动r015；缺失历史记录不由
  新执行追认，也不自动追加repair或新实验。

## r014 执行后复核与期刊判断（2026-09-05）

本次真正推进是raw公开及B完整统计复现：全部bootstrap风险最大差2.22e-16，功效差0；
clean upper最大0.392332且18个head非恒定。ResNet propulsion的效应下界为正，
不能误写六格都跨零；但ViT该属性为−1.4622pp，原六格合取未过，且所有upper仍高于2pp。
条件于执行有效时应为POWER而非KILL；优先的实际render/证据前提尚未全部成立。

新mutation中的概率加法交换律、ID不等、NaN非有限和固定零区间不等于实际验证器已拒绝
错误输入。原任务已经要求这类检验，此次只要求完成原合同，不新增科学门。
原模型文件不变也不能替代初始化/训练输入绑定；缺失的原执行记录不能靠本轮重新前向追认。

当前仍是JSTARS类领域测量论文候选，不是TGRS/JPRS。依据是项目缺少超越已有几何、
方向规范化与不变表征的新增机制和独立决策价值，不以旧期刊标签、实验轮次或2pp门替代判断。
有限资源下方向测量是否优于强不变决策仍只是未成熟候选，不签新训练来充当“顶刊推进”。

## r014 correction-only 原始执行设计（2026-09-05；前向权限已被剩余验收安排收窄）

本轮落实上次B/C一致建议，不把新任务号当作新的科学假设。先公开原执行代码与原产物绑定，
区分公开代码必然错源与实际canvas已确认错源，再逐对象证明原训练输入和既有六模型可复用。
训练canvas实际生成器已使用loc–CAT联合键，但缓存存在时跳过重提取，因此仍须从原影像逐
像素验证，不能仅凭生成器看起来正确或manifest自洽批准复用。

允许修正calibration的source绑定并复用六模型重算，不允许修复训练、增删对象、调整阈值或
查看test。原两视图是RP1配对而非相同像素，等价性应验证视图对及平均预测，不制造不合理的
逐视图恒等门。统计实现需完整验证raw→错误→分母→draws→同时区间/功效/clean utility→裁决，
不再只校验Delta、sd、q或信任生产者的布尔值。全部数学门沿用原r013，修正后披露为重建结果，
不能恢复一个未曾成立的前瞻身份。

RarePlanes具有原问题所需的独立细粒度属性，单类HRSC2016不适配；本轮不改数据。新预算/不变性
问题仍是待论证候选，不纳入r014。完成任何裁决后停止，B再依据可公开复算证据判断后续科学价值。

以下记录保留各轮当时的讨论语境；与以上当前结论冲突的期刊定位、必要性或验收表述不再有效。

## 历史状态摘要（已被当前复核取代）

- 已复核当前精简树、`09381f7a360e5ad730e77157fb427401555620f5` 归档父树、全部主要结果表、
  失败路线、未执行轮次和最近提交；项目不是只有当前 r001--r011。两套主线存在同号 r 轮次，
  全项目总账以归档/当前前缀区分并已写入 `lab/result.md`。
- r011 的机器结论 `ASSET_UNAVAILABLE_R011` 未通过 B 验收。发布证据没有对应的修复后执行记录，
  split 又把既有 lexical `loc:` key 改成 numeric tuple 后重新置换；lineage、支持门、footprint
  双实现和模型严格加载也未闭合。当前正式状态是 `INCONCLUSIVE_R011_EVIDENCE_REPAIR`。
- r010 的 `83 components / ASSET_UNAVAILABLE_R010` 不能接受。官方 CSV 有 26 行 raw `cat_id`
  被科学计数法破坏；以满足严格三方一致条件的 `image_id` 后缀恢复后，227 个 CAT 与 GeoJSON
  集合完全一致，得到 102 个 footprint 合并前 component。正式地理 footprint 与模型 readiness
  仍未闭环，故当前唯一状态为 `INCONCLUSIVE_R010_ASSET_AUDIT_INVALID`，不是 READY。
- r005 correction-only 已完成并由 B 独立复算；唯一可接受结论为
  `INCONCLUSIVE_R004_PROTOCOL_VALIDITY`。这不是 `KILL`，也不准入跨数据集阶段。
- r003 从未执行，旧签字和旧执行计划均不继承。
- r001 只关闭既定 CMR，r002 只把既定 GR-EQS 负向冻结；二者都不能证明所有方向可靠性机制无效。
- 经不继承历史标签的重新评估，当前证据上限仍是 strong JSTARS；尚不能声称达到 TGRS 或
  ISPRS JPRS。唯一仍可能改变该结论的是一次跨来源 component-held-out 的独立下游因果与无 GT
  决策风险验证。

## 从 AIRO 到干预式轴向可辨识响应

B 最初提出以局部有效旋转信息 `J_eff` 和全局轴向 alias 间隙 `M_15` 描述 COI。C 接受
它们作为一次可证伪测量，但拒绝“信息论上限”或“普适定律”的措辞：两个 detector 的经验误差
不能约束更强 estimator，经典结构张量、配准 CRLB/Ziv--Zakai 界、Lie derivative 和全局配准
歧义也不是本项目的新理论。

B 接受该修正。新命题只称为“干预式轴向可辨识响应”：对同一图像实施不改变 GT 几何的
各向同性模糊和抗混叠降采样后，`J_eff`、`M_15` 是否按剂量下降，并伴随不同 detector
架构的轴向损失上升。它不声称基本极限，不输出新角度，不训练不确定性 head，也不把观测量
融合进 detection score。

## C 的最强反例与 B 的处理

C 的决定性异议是 predicted-crop 混杂。错误的预测中心、尺度和背景可能同时降低观测量并
增大角误差；因此旧式回顾性相关即使为正，也可能只是“坏框裁到坏图”。B 接受以下边界：

- 主分析只使用 GT 中心和交换不变的无方向尺度裁圆形 patch，任何阶段都不向特征提取器提供
  GT theta；这只是 oracle-localization、theta-hidden 条件，不是部署方案。
- clean prediction 定义的裁剪只作诊断，并在各干预间固定；随干预变化的预测裁剪属于
  post-treatment 次分析，不能支撑主结论。
- 围绕主裁剪加入平衡中心位移和互为倒数的尺度扰动，形成 crop nuisance envelope。真实成像
  效应若落入该 envelope，必须判机制失败。
- 主因果结局固定在 clean 图像已检测到的 GT 对象总体。干预后漏检记为最大损失，并把总变化
  精确拆成漏检贡献与保留匹配对象的角度恶化贡献；只有后者也为正，才不是普通 recall 崩塌。

## 数据与资产边界

新问题首次验证按项目规则优先 HRSC2016。它的单类、高长宽比船舶适合先隔离方向机制，因此
r004 只做 HRSC2016 生死门，不把跨域失败混入首次机制判断。历史清单曾登记 Oriented R-CNN、
Rotated RTMDet、ARS-DETR 和 Strip R-CNN 的 HRSC 模型，但当前 Git 中可核实的冻结输出只覆盖
同一 Oriented R-CNN detector family，且部分旧子集有训练重叠风险。SERVER 必须重新解析训练外
official test 和至少 Oriented R-CNN、Rotated RTMDet 两种严格不同架构；换 backbone 不算第二
family，旧预测只能作 identity parity 对照。

## 先验碰撞与可保留的新意

普通图像结构张量已能描述主方向和各向异性；配准文献已给局部 Fisher/CRLB 与全局歧义界；
OBB 文献已有参数结构张量、周期角度质量、rotation-equivariance 测量和频域角对齐。因此
`J_eff` 或 `M_15` 单独作为新分数不足以形成顶刊贡献。唯一仍可能成立的科学增量是：在
theta-hidden、定位去混杂、强经典基线和真实成像干预下，人和多架构 detector 是否共同呈现
可重复的方向特异响应。

## B/C 联合裁决

C 对 r004 给出条件签署，B 接受全部限制：r004 仅是 HRSC2016 detector-side causal falsifier。
全部门通过只允许进入第二数据集/传感器和至少三名盲标注者或重复标注的确认阶段；不构成方法
成立、human-machine shared law、TGRS/JPRS 升档或论文结论。若 GT 主裁剪信号消失、只有预测
裁剪有效、角度贡献不为正、任一必需 detector/corruption 反向，或新量被结构张量、梯度、尺度
等强基线等价复现，则关闭该机制，不得改名回到 selector、head、CMR、PEF、Q-SetOD 或 GR-EQS。

## r004 SERVER 结果的 B 独立复核

SERVER 报告八个 detector×corruption×dose 的完整总体 `DeltaY` 点估计均低于 0.02。若资产、
匹配、操纵和实现有效，这一事实足以使主损失合取门失败；但当前公开实现没有建立这些前提，
因此 B 不接受其 `KILL_COI_R004`，当前科学状态为
`INCONCLUSIVE_R004_PROTOCOL_VALIDITY`。

决定性问题不是“缺少更多显著性”，而是冻结 matcher 被改变。trainval 剂量选择先汇总全部
候选并按代价全局排序后做一对一贪心；test 快速门改为按 GT 输入顺序逐个占用最近预测。两者
可在同一输入上冻结出不同总体：一个两 GT、两预测的最小反例中，前者保留两个 GT，后者只
保留一个。由此八个 test 点估计不是原协议所定义的同一 matcher 下估计量。

同时，公开代码只实现了合成夹具、剂量选择和主损失快速聚合，没有对真实 HRSC test 生成
G/P/N 的 `J_eff/M_15`，也没有计算操纵 Holm-32、test 非坍塌、10000 次图像簇 bootstrap、
逐对象审计或独立重算。缺少真实操纵证据时，低 `DeltaY` 既可能代表机制失败，也可能只是
干预没有充分改变预注册可观测量；按 r004 的冻结优先级只能记为 inconclusive。

下一步只允许复用已经生成的 clean 与四个干预预测做 correction-only CPU 闭环。不得重推理、
重选剂量、换模型、删对象或在 test 上调 matcher。只有同一 matcher、真实操纵有效性和独立
复算全部成立后，负向点估计才可正式关闭 COI。当前期刊证据仍只支持 JSTARS 对标。

## r005 B 最终验收

B 从 Git 中公开的逐对象表和 bootstrap draws 独立复算，确认统一 matcher 后的 16 个
split×detector×condition cell 在两实现间 key 对称差为 0、所有逐行量最大绝对差为 0；八个
test `DeltaY` 与报告完全一致，最大值为 0.017158。逐对象恒等式
`DeltaY=C_miss+C_ang` 与图内等权、图间等权聚合也以零误差复现。

真实 G/P/N 表共 124168 行且无重复 key。trainval normalizer 最大复算差为 `3.55e-15`，32 个
操纵点估计最大复算差为 `8.33e-17`，seed 5005 的 10000 次 PCG64 图像抽样矩阵可逐元素重建。
决定性事实是八个 G 主臂 `clean-high>0.20` 裕量全部为负：J_eff 在 blur/downsample 的裕量约
-0.048/-0.152，M15 约 -0.178/-0.194；两 detector 结论一致。因此前三类操纵合取不成立，
按冻结优先级只能接受 `INCONCLUSIVE_R004_PROTOCOL_VALIDITY`。

复核同时发现两项实现限制。第一，六个 N 臂中 93126 个应复用 clean-G noise scale 的记录有
71207 个实际使用了各自 clean-N scale，最大差约 3.82；因此 nuisance envelope 不能作为合格
specificity 证据。第二，ORCNN 操纵点估计使用 434 张有对象图，而 bootstrap registry 含 437
张并把其余图置零后仍以 437 为分母，导致其 bootstrap 分布与点估计总体不完全一致。这两项
都不影响当前保守裁决，因为 G 主臂八个 SESOI 点估计本身已经失败；但它们禁止未来引用 N
envelope、CI 或 Holm p 作为正向证据。

r004/r005 至此停止：不得重调 test 剂量、降低 0.20 门、重推理或换模型救回，也不得把
inconclusive 写成机制已被证伪。当前仍只支持 JSTARS 对标；没有 TGRS/JPRS 升档依据。

## r006 新候选：平移到轴向角的特征格相位泄漏

B 在停止 COI 后重新检索项目历史和外部先验。通用 CNN 的像素平移不稳定、下采样 alias、
[BlurPool](https://proceedings.mlr.press/v97/zhang19a.html) 与
[adaptive polyphase sampling](https://openaccess.thecvf.com/content/CVPR2021/html/Chaman_Truly_Shift-Invariant_Convolutional_Neural_Networks_CVPR_2021_paper.html)、
[TIPS](https://openaccess.thecvf.com/content/WACV2025/html/Saha_Improving_Shift_Invariance_in_Convolutional_Neural_Networks_with_Translation_Invariant_WACV_2025_paper.html)
已直接研究；已有 [object-detection shift-equivariance](https://arxiv.org/abs/2008.05787) 工作也在
COCO 和 DOTA 水平框上报告过一像素平移造成的 AP 波动。因此“detector 不具 shift equivariance”
不是本项目的新命题，简单把 BlurPool、APS、LPS 或 TIPS 搬到旋转检测也不足以成为顶刊贡献。

定向检索尚未找到直接检验下述更窄问题的工作：在物体与 GT 方向完全不变时，无插值整数平移
是否通过多尺度采样格的 polyphase 改变，被定向 detector 专门泄漏成 RP1 轴向角振荡；该角振荡
是否在中心、无序边长、分数和匹配均稳定的对象上仍存在。这个问题不同于 PSC 的“角编码相位”、
旧 OER/GR-EQS 的输出排序或融合、旧 CMR/PEF 的候选角修正，也不同于 r004/r005 的图像模糊与
降采样可观测量。

C 的首要反例是：多尺度 Oriented R-CNN 和 RTMDet 同时经过多个 stride 路径，“存在 active
stride 8”不等于整个输出以 8 为周期。若只扫描两个 8 像素周期，真实的 stride 16/32 泄漏会被
误判为不复现。B 接受这一反例并撤回共同 stride 8 方案。r006 必须从 clean 计算图封存每个最终
预测的实际角特征来源：两阶段模型记录最终 RoI extraction level，单阶段模型记录胜出候选的
pre-NMS head level；只按 trainval 预先定义有足够支持的全部 active stride 建层，test 不得按
结果挑 stride。每个层固定使用最先出现的两个完整周期，并把 level switch 当作不稳定而不是静默
重分层。

C 同时要求三项有效性边界，B 全部接受：平移必须发生在最终 resize 后的网络输入格点，避免前处理
插值；所有条件使用同一扩边 canvas，逆移后的对象邻域逐值相同并隔离边界；同一输入重复推理必须
先证明计算确定性。输出角只能从 polygon/长边 canonical 后的 `exp(i2theta)` 计算 RP1 距离，
禁止直接比较 raw theta，以免 w/h 交换、90 度 canonicalization 或角编码边界制造伪振荡。

最危险的直接近邻是 2024 年的
[Structure Tensor OBB](https://arxiv.org/abs/2411.10497)，其公开材料声称同时改善 rotation 与
spatial-shift robustness；但其 tensor 是 OBB 参数表示，且现有实验没有分离 fixed-GT-angle 的
shift-only、逐实例 source-stride 相位归因。这个差异只留下一个很窄的候选空隙，不能写成“首个”
或“理论创新”。

B/C 对结论边界也一致：执行有效时，只有两个 detector family 都在各自至少一个预注册 eligible
stride 上同时通过水平、垂直全部门，才准入下一阶段；任何部分通过、单轴、单架构或非周期结果都
统一关闭这条“跨架构、双轴、clean-assigned output-lattice TAL”路线。该 KILL 不能外推成不存在
任何 translation-to-angle leakage。C 在复核三分区、phase-0 stride provenance、固定前两周期、
canvas/phasor、all-shift mask 与各总体 bootstrap 分母后给出
`C_FINAL_SIGNED_R006_DIAGNOSTIC`。

r006 只是一轮 HRSC2016 跨两架构的机制生死门，不训练、不聚合多视图、不修框、不输出可靠性
排序。即使通过，也只说明存在值得处理的 OBB 专属 translation-to-angle leakage；下一阶段仍须
在未触碰的第二传感器/数据集与第三架构上确认，并与 direct/PSC 或 CSL、Structure-Tensor angle
coder、BlurPool、APS、LPS、TIPS 做正面对照，最终同时改善 AP75、角误差和 shift consistency
且不损伤 mAP/AP50，才有讨论 TGRS/JPRS 的基础。当前不升档。

## r006 执行收口与禁止重开

SERVER 已完成 r006 的扫描、canvas parity、主统计和第二实现复算。B 接受其唯一状态为
`INCONCLUSIVE_R006_EXECUTION_VALIDITY`：ORCNN stride 8 的 y 轴冻结总体在 shift 10、12、13、14
只有 89.68%、89.29%、88.49%、89.29% 保留率，低于逐 shift 90% 的预注册下限。其余 parity、
确定性和复算即使通过也不能替代这个失败的执行前提。不得调整 padding、margin、stride、阈值，
也不得再次打开同一 HRSC official test；这不是 TAL 的科学 KILL 或 ADMIT。

## r007 候选清理：拒绝旧路线换名

B 提出的“多模型一致 + 人类/official-GT 偏差”候选被 C 否决。其核心仍是旧 A5/M4 同批双人
标注上的 label discrepancy，多模型一致只能增加相关性三角证据，不能排除共同训练标签、角度
规范或架构偏置；AR>=2.1 的 DIOR+SODA 双人数值样本上限约 211，旧审计中单人相对 GT 的
`>=10°` 事件又只有约 1--2%，不足以支撑新的稀有事件机制。

B 随后复查旧 PSC 解码机制，曾考虑用 unit phase 与独立 concentration 构造 gauge-separated
axial likelihood。C 指出更晚的权威重审已经把候选门改判为 `FAIL_CANDIDATE_GATE / STOP_B6`：
外部 RotatedFCOS-PSCD 上没有候选同时胜过 phase modulation 与 detection score。单位相位、
mean--concentration 解耦和 axial von-Mises proper likelihood 也都是已有 directional-distribution
工具；该提案实质是旧 B6 repair，而不是新路线。B 接受否决，不签发训练任务。hard-FPN routing
同样因 PANet/AugFPN/GRoIE/ProFPN 等软层融合先验过密而不占用新任务号。

## r007 唯一下一步：SAR acquisition-axis 资产资格门

B/C 共同认为，若要从当前 JSTARS 级回顾性相关推进到可能支撑 TGRS/JPRS 的新科学对象，最有
价值的方向是区分“普通 raster/网络偏置”与“真实 SAR acquisition range/azimuth 成像各向异性”。
但这个问题不能用只带 JPEG/XML 旋转框的切片伪造：例如官方 RSDD-SAR 说明其 7000 个切片来自
高分三号与 TerraSAR-X 的 127 景数据，并提供旋转框、极化和分辨率，但公开说明本身不足以证明
每个对象可回链 acquisition-axis 坐标；SAR-AIRcraft-1.0 的公开页也只明确图像尺度、模式、极化
和框位置。因而首要风险是资产不可识别，而不是模型不够复杂。

C 要求 r007 只能做 asset qualification：两个域必须来自两个独立 sensor/platform；同一传感器
的轨道、视向或模式只作域内分层；每个 acquisition axis 必须由原始产品 metadata/geolocation
变换到 OBB frame，不能从 north-up 边缘或目标分布猜测。每域须有至少 200 个原始 acquisition
scenes、1000 个 joint-complete 高长宽比对象，以及两个相隔至少 20°、各含至少 50 scenes 和
250 对象的 acquisition-axis strata。scene 与对象分母的 joint-complete metadata 覆盖均须
至少 95%，许可、去重、地理分组和双实现也必须闭合。

这里的 strata 只按每个 scene 的 ground-range axis 在共同 Earth-fixed/local-ENU frame 中相对
真北的 `[0°,180°)` 轴向方位，以固定 10° 半开 bins 建立；azimuth axis 只作正交校验，不能把
同一 scene 平凡地计成第二取向，chip/raster 旋转也不能制造支持。compact 证据不同时公开带共同
键的逐 scene axis 与逐 object OBB theta；两边只给无共同标识符的边际量，lineage 表不含角值。

r007 严禁计算 OBB 轴与 acquisition axis 的相对角、关联或任何模型结果，避免在设计未来假设
前偷看效应。全门通过只记 `READY_FOR_BC_R008_DESIGN`；资产门失败记
`ASSET_UNAVAILABLE_R007` 并回到 `NO_ACTIVE_TASK`；解析或双实现不可裁定才记
`INCONCLUSIVE_R007_ASSET_AUDIT`。三者都不是科学 PASS/KILL，也不自动授权 r008。C 最终
复核固定分箱、双传感器与信息墙后给出 `C_FINAL_SIGNED_R007_ASSET_QUALIFICATION`，B 已逐项
写入唯一 SERVER 任务。

## 外部专家复审与 r007 后续暂停

外部专家在审阅项目全量结果后给出 `REVISE`：现有工作可形成扎实的方向可靠性测量论文，现实
定位仍是 strong JSTARS；直接以当前证据冲 TGRS/JPRS 不成立。继续新增小型 selector、角度 head、
相似光学 OBB benchmark 或仅证明“角度重要”不会自然形成顶刊贡献。SAR acquisition-axis 虽有
潜在物理价值，但在资产元数据、AIS true heading 与匹配链尚未证实时不应成为本项目主线。

B 接受这项总裁决。外部意见到达前，SERVER 已完成 r007 只读审计：主机固定数据根中的
RSDD-SAR 与 SAR-AIRcraft 候选均不存在，双实现一致给出 `ASSET_UNAVAILABLE_R007`。这只是
资产不可用，不是 SAR 机制 KILL；与专家“暂停 SAR”的意见一致。未来若另立传感器物理项目须
重新形成独立目标，不得由本项目自动恢复。

## r008：RarePlanes 顶刊验证资产资格门

专家指出，现稿真正缺少的不是第六个角度分数，而是可量化的独立下游后果。唯一保留问题收敛
为：预测 OBB 驱动飞机定向归一化和细粒度属性识别时，方向误差是否造成至少 2 个百分点的因果
决策损失；若造成损失，一个不由 test GT 拟合的方向扰动—决策稳定性分数能否在 90% 自动覆盖率
下降低该损失。

RarePlanes 官方资料报告 253 个 WorldView-3 real image records、112 个地点、约 14700 个飞机、有序
nose--wing--tail diamond、细粒度属性及 off-nadir、分辨率等成像元数据，适合纯
location/source-component-held-out 验证。官方同时提示 `wing_position` 一致性有限；未来将
wing type 的 straight/nonstraight、engine count 与 propulsion 的预注册合并类作为三个
co-primary，role 只作派生语义
的 secondary endpoint。普通 OBB 统一按 minimum-area rectangle 的 long-side RP1 轴向处理，
不能把 nose--tail 航向或经纬度坐标中的伪角偷给部署模型。

当前仓库和历史主树均无 RarePlanes 数据或既有实验，FRED 也没有本项目现成闭环；ARS-DETR 与
O2-RTDETR 的历史资产来自其他数据集，不能证明 RarePlanes 就绪。C 因此反对把五模型三 seeds
训练与资产发现自动串在同一任务中，B 接受。r008 只做数据、许可、diamond/属性语义、
`loc_id↔CAT/source-product` 连通分量 split、五 detector families、CNN/ViT 及强基线输入的
只读资格审计；不训练、不推理、不读取模型性能。全门通过只允许 B/C 另签唯一一次 r009 顶刊
验证，不代表 H1/H2、方法或期刊已成立。

RarePlanes 标签和本次固定 split 均是公开可重建资产，故未来 test 只能称为“预注册、程序性
信息墙下的 single-use component-held-out test”，不能称 external blind 或真正 sealed test。
未来 r009 若获签，必须先在 calibration 地点通过 GT `±10°` 破坏和 predicted-to-GT angle
rescue 的 H1 因果价值门；H1 不过便不计算 test 性能。H1 通过后才允许冻结唯一 max-JSD 方向扰动
分数与强非 oracle 基线并一次揭示 test。外部建议的 RarePlanes 600 目标、三人互盲标注不能由
SERVER 自动完成；即使自动 H1/H2 全过，也只能生成盲标包并等待真实人工记录，不能直接宣称
JPRS 证据闭环。

C 最终复核后给出 `C_FINAL_SIGNED_R008_ASSET_SPLIT_QUALIFICATION`：来源独立单位、full GeoJSON
对象 census、long-side RP1 几何、三个 co-primary 固定分组、secondary role、公开 single-use
test 边界和 READY token 均已闭合。B 接受该签字；r008 即使 READY 也只允许另行设计 r009，
不得自动训练或推理。

## r008 SERVER 结果与 B 驳回

SERVER 给出 `ASSET_UNAVAILABLE_R008`，但实现没有执行已签署的完整资产核验。数据搜索只对
固定数据根直接拼接四个目录名，遗漏官方常见的 `RarePlanes-Public`，也没有读取 dataset 索引、
按 full annotation/metadata 内容签名或对候选做有界枚举。故“这四个目录不存在”不能推出
“RarePlanes real 资产不存在”。

模型侧的负结论也由常量产生：五个 family 的 weight 与 OBB/RarePlanes readiness 均直接写为
false，ResNet-50、ViT-B/16 availability 也直接写为 false；权重索引虽被运行记录声明为输入，
实际命令和程序没有读取。O2-RTDETR 未检查 ai4rs 内已知的 rotated-RTDETR project，反而把
ai4rs 根存在当作 Rotated RTMDet 的 availability。独立验证再次使用同一四目录别名，未独立
检查 third-party 和权重，只验证主程序已输出 unavailable。

B 因此把当前状态限定为 `INCONCLUSIVE_R008_ASSET_AUDIT`。这不是说资产存在，而是现有证据
不能证明不存在；H1/H2 仍未运行，期刊判断不变。唯一下一步是 r009 correction-only：完整但
有界地查 dataset 索引、官方内容签名、真实内部项目与相关权重，并由不共享候选表的第二实现
复核。r009 仍不训练、不推理、不下载，也不自动授权后续顶刊实验。

## r009 最终验收与 r010 顶刊资产落地

r009 已完成上述修正。主实现覆盖 `RarePlanes-Public` 等五种目录别名和官方 full annotation、
metadata 内容签名，搜索无异常；独立实现没有导入主候选集合，给出 `passed=true`、
`candidate_set_equal=true`。B 因此接受 `ASSET_UNAVAILABLE_R009`，并删除结果文件中遗留的 r008
旧驳回段落。该 token 的含义只是“当前主机没有资产”，不能外推为 RarePlanes 官方数据不存在。

官方 [AWS Open Data RarePlanes 登记](https://registry.opendata.aws/rareplanes/) 仍提供无账号读取的
`rareplanes-public` 资源，许可为 CC BY-SA 4.0；官方登记的 real 部分为 253 景 WorldView-3、112
地点和约 14700 个飞机实例。官方
[数据说明](https://github.com/jdc08161063/RarePlanes/blob/master/datasets/README.md) 同时表明 real 与
synthetic 可分开取得。因而当前唯一合理操作不是换数据、恢复 selector 或转向 SAR，而是只把
顶刊一次性验证所需的官方 real 数据及合法模型初始化资产物化到主机固定资产体系。

r010 是资产落地，不是第二次科学验证：只取得 RarePlanes real、许可、元数据、完整标注与原始
影像，构造不泄漏的 source-component 划分，并补齐五个既定 detector family 与两个分类器的合法
实现/初始化来源；不下载 synthetic，不训练、不推理、不读取 H1/H2 结果。只有全部闭合才记
`READY_FOR_BC_R011_FINAL_VALIDATION`，随后 B/C 只再签一次包含 H1 因果价值门和 H2 决策风险门的
正式实验。若官方资源不可访问、许可不允许、来源分量或属性支持不足、关键模型族不能合法复现，
则停止顶刊扩展并回到 JSTARS 收敛；不得再找近似数据集替代。

## 全项目复核后的 r010 更正

B 没有接受 SERVER 的 r010 token，而是从官方 HTTPS 原文件独立重算。metadata CSV 的 253 行中，
26 行 `cat_id` 被压成三个科学计数法字符串；r010 主、独立实现都直接把这些伪值加入 union-find，
于是把本无关的地点合成 25-location 巨分量并得到 83。保留 raw 值、只在后缀格式、GeoJSON CAT
集合和影像键三方唯一一致时从 `image_id` 恢复后，metadata 与 GeoJSON 都是同一组 227 CAT，基础
图为 102 components（97 单点、4 双点、1 七点）。这属于源字段 canonicalization 修错，不是看到
结果后降低 100-component 门。

旧 83 图上的 train/calibration/test 对象数和支持表整体失效。按同一 PCG64(1010) 重新计算的候选
结构为 52/25/25 components，对象数为 5,370/7,418/1,919，三项属性的六个类别对象支持均超过
冻结门；但这仍只是 footprint 合并前结果。r010 代码并未读取 COG 的 CRS、affine、宽高计算地表
footprint，102 又只比门槛多 2，因此任何正式 READY 仍须等待真实 overlap edge 的双实现复核。

模型侧也没有形成 READY：FRED 缺失被硬编码，所谓独立验证复用了主实现清单；其余条目主要验证
目录、许可和一个通用权重存在，未证明 RTMDet/CSPNeXt、O2/R50vd、ViT 等实现与 checkpoint
架构兼容，更未做真实 config build/state-dict load。由此 B 将 r010 更正为
`INCONCLUSIVE_R010_ASSET_AUDIT_INVALID`。这既撤销错误的资产停止结论，也拒绝把 102 直接包装成
实验就绪。

## 为什么取得 RarePlanes，以及它究竟要回答什么

取得新数据不是为了把数据集数从五个增加到六个。DIOR-R、FAIR1M、SODA-A、DOTA 和 HRSC2016
已经充分覆盖“AP50 可掩盖方向误差、长目标更敏感、score 不是方向质量”的测量问题；继续追加相似
OBB benchmark 只会重复同一几何结论。HRSC2016 又是单类船舶数据，缺少独立细粒度属性，不能回答
“方向错误是否真正改变遥感决策”。这就是本次新问题不继续优先用 HRSC 的科学原因。

RarePlanes real 的作用是提供 WorldView-3 来源、独立 location/source-product component、飞机
细粒度属性及成像元数据，把评估终点从 OBB 的 IoU/角误差换成独立属性决策。唯一顶刊命题是两段
合取：H1 证明只改变方向会造成至少 2 个百分点的下游 balanced-error 损失，并且把预测角替换为
GT 角能产生实质 rescue；H2 证明无需 test GT 的方向扰动—决策稳定性在固定 90% 自动覆盖下，
相对最强非 oracle 基线带来绝对至少 2pp、相对至少 20% 的错误下降及至少 15% 的 AURC 改善。
H1 或 H2 任一失败，顶刊扩展停止，现有测量稿按 JSTARS 收敛。SAR 已暂停，小 selector/head 也不再
进入候选池。

## 不继承旧标签的期刊重评

当前最强正证据是六单元受控扰动、八单元几何风险、600 目标人工双标和图像级风险控制；最强负证据
是唯一前瞻 r045 应用迁移收益 `-0.00195195`、95% CI `[-0.00759691,0.00355364]`，以及随后所有
候选方法没有留下正向胜者。现稿证明了指标缺口，却没有证明独立决策后果、可部署控制收益或新的
成像/检测机制。全项目 616,184 行也不能冒充 616,184 个独立重复，真正统计层级仍是来源 component、
图像和模型单元。

因此独立结论是：现在可形成 strong JSTARS 级的严谨测量/审计稿；JPRS 只有在 RarePlanes H1+H2
和后续真实三人互盲锚点同时闭环后才成为可信目标；TGRS 还需要更强的成像物理或实质检测方法创新，
当前不得承诺。最强拒稿理由可以压缩为一句：论文严谨证明了现有检测指标不能充分表达方向可靠性，
却没有证明这种可靠性在独立遥感决策中造成并能被无 GT 方法控制的非平凡收益。

## B/C 对 r011 的联合裁决

B 提出 r011 只做一次证据链 correction/design，C 进行独立红队后给出
`C_FINAL_SIGNED_R011_EVIDENCE_CHAIN_REPAIR`。C 接受其科学理由：大胆不等于立刻烧算力；先把唯一
single-use test 的独立单位、统计估计量和模型身份锁死，才有资格用一次实验真正推翻或支持顶刊命题。

C 的三条硬边界已全部写入当前唯一指令：READY 必须建立在真实 COG footprint 合并后的最终
component，而不是中间数 102；r011 只能冻结 class-balanced × component-equal 估计与
calibration-only 功效规则，不能用对象数宣称已有功效；每个模型必须真实 build/load 且权重架构
匹配。若唯一剩余缺口是 FRED，仍输出 `ASSET_UNAVAILABLE_R011`，只报告四 family 修订可行，等待
用户明确决定，SERVER 不得自行删模型或用近似替代。

上述是 r011 执行前的联合设计：原计划只有
`READY_FOR_BC_R012_FINAL_CAUSAL_VALIDATION` 才另签包含 H1a/H1b/H2 的最终实验。下面的执行后审计
证明 r011 未达到可验收终态，因此不沿用其 numeric split，也不直接启动原定全链实验；新的 r012
改为先补 outcome-blind G0，并只在 G0 通过后执行必要性最强、代价最小的 H1a。

## r011 验收失败与 r012 的最小顶刊生死门

B 对已发布 r011 逐代码和逐证据复核后，拒绝机器的 `ASSET_UNAVAILABLE_R011`。其最直接的反证是：
登记执行在 RP1 修复提交之前已经结束，登记产物位置也不是后来发布的 repair 产物位置，而发布
内容却使用了修复后的逻辑。它不能证明发布证据来自所登记执行。进一步，r010 已公开的 component
规范 key 是 lexical 字符串 `loc:...`；r011 改用 numeric tuple 排序后再置换，使 102 个 component
中只有 43 个留在原分区。lexical split 的 test/calibration/train 是 25/25/52 components、
1,919/7,418/5,370 objects，r011 numeric split 则变为 3,766/6,747/4,194 objects。没有任何 H1/H2
outcome 被读取，因此应恢复事前 lexical split，而不是在两个 split 中择优。

其余缺口同样属于执行有效性而非资产不足：支持门没有进入 finalizer；calibration 19/20 fixture
只是恒真表达式；粗属性 signature 没有形成 annotation→tile→COG→full object 的唯一 lineage，
且 full train 10,900 个对象与 tiled 的 10,899 个 unique signature 仍差 1；两个 footprint 实现
共享同一简化判定；detector 用非严格加载后硬写空 missing/unexpected keys，FRED 缺失也仍由常量
产生。故当前不得把 r011 写成数据门通过或模型资产确定失败。

B/C 不再等待五 detector 资产，也不把 H1a 与 H1b/H2 混跑。H1a 是整个顶刊扩展的必要前提：若在
GT 中心、尺度和同一预提取 source canvas 固定时，仅把规范化算子的角参数改为 `theta±10°` 都不能
稳定增加独立属性 balanced error，则没有理由继续训练 detector 或发明无 GT selector。这个量是
规范化算子的总效应，包含仿射重采样与背景支持变化，不包装成像素不变的纯角度效应。新的唯一
r012 因而严格分两段：先做
outcome-blind G0，恢复 lexical split 并闭合 footprint、lineage、支持、几何与两分类器身份；G0
任一项失败即零训练。只有 G0 通过，才用 train components 训练 ResNet-50 与 ViT-B/16 各三个
固定 seed，并在 calibration components 一次性执行 H1a；test 不提取 crop、不前向、不计算性能。

C 先给出 H1a-only 条件签署；统计红队随后把主量冻结为 2 architecture × 3 attribute 的六个
co-primary、class-balanced × component-equal 风险、同步 component bootstrap、clean utility 与
同时区间。B 再锁定全 footprint pair 的投影/容差、共同 eligible、exactly six fits 和禁止以任何
train `±10°` response 选模型后，C 给出 `C_FINAL_SIGNED_R012_H1A_ONLY`，统计红队给出
`STATS_FINAL_PASS`。六格必须全部达到 2pp 实质门且有同时区间支持，才能记 `PASS_R012_H1A`；
执行有效且有功效但失败则记 `KILL_R012_H1A`；证据、实现或功效不足统一记
`INCONCLUSIVE_R012_H1A`。PASS 也只准 B/C 另议 H1b/H2，不代表 JPRS/TGRS 已成立。

## r012 外部终止复核与 r013 决策

C 只读登录 26 服务器复核了当前项目。事实是：项目处于与远端一致的完整提交，工作树干净，r012
已经没有存活进程；ResNet-50 的 seeds 1201、1202 分别约 94 秒和 97 秒完成，另外三个拟合的空日志
在 2026-09-04 23:56:58 +08:00 同时创建，均未留下 Python traceback、final-epoch 模型或训练输出，
ViT-B/16 seed 1203 未启动。final 证据约 173.5 秒后开始写入并裁决 TRAINING_FAILURE。用户级日志
没有对应 OOM、Xid 或重启记录，当前四张 A30 也可正常识别。

可以确认的是三个拟合被训练程序之外的事件同时终止，而不是三个模型各自正常失败。高置信推断是
父命令、交互会话或执行器存在约 180 秒的外部时限；这比三个相互独立的 Python/CUDA 故障同时发生
更符合时序。未知项仍然存在：当前账号无权读取完整 kernel journal/dmesg，也没有 process
accounting 或退出信号记录，因此不能把“180 秒超时”写成已证明事实，也不能严格排除系统级 OOM。
上述复核不产生新的科学 outcome，r012 仍只能是 INCONCLUSIVE_R012_H1A，而不是 H1a 失败。

用户批准的唯一补救是 r013：科学问题、六格估计量、2pp 门、同步 component bootstrap、clean
utility 和 calibration/test 信息墙全部不变；r012 的两个完整模型及所有部分状态永久排除，六次
fit 从冻结的架构匹配初始化全新开始。正式拟合前仅允许不更新参数的单批次资源预检。任一正式拟合
失败即整轮 inconclusive，不补跑、不混合。只有六个 final-epoch 模型全部封存后才一次性打开
calibration。

r013 PASS 仍只是 H1a 必要性证据，下一步必须是 predicted-angle→GT-angle 的 H1b rescue；之后才
可能设计不使用 test GT 的 H2 风险控制、来源独立确认与真实三人互盲锚点。r013 KILL 则关闭
RarePlanes 顶刊扩展。当前论文级别在 r013 结果回来前仍是 strong JSTARS，不因重新执行而升档。
