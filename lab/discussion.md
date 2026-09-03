# B/C 科学讨论

## 当前状态

- r005 correction-only 已完成并由 B 独立复算；唯一可接受结论为
  `INCONCLUSIVE_R004_PROTOCOL_VALIDITY`。这不是 `KILL`，也不准入跨数据集阶段。
- r003 从未执行，旧签字和旧执行计划均不继承。
- r001 只关闭既定 CMR，r002 只把既定 GR-EQS 负向冻结；二者都不能证明所有方向可靠性机制无效。
- 当前证据仍只支持 JSTARS 对标，尚不能声称达到 TGRS 或 ISPRS JPRS。

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
