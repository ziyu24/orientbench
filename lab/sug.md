# SERVER 科学指令

## r011：RarePlanes CAT、地理 footprint 与模型就绪证据链最终修正

### 1. 目标与边界

r010 的 `83 components` 来自 26 行 raw `cat_id` 科学计数法损坏，不能继续作为资产结论。
r011 只修复并独立验证 RarePlanes 的来源标识、真实地理 footprint、唯一 lineage、split/统计合同和
模型 build/load readiness；不训练、不做数据集模型 forward 或推理、不读取任何 H1/H2 性能、不计算
风险排序、不修改论文，也不自动启动后续实验。

本轮不是科学 PASS/KILL。HRSC2016 是单类方向检测集，缺少本问题所需的独立细粒度下游属性，
因此不适合这次资产与决策任务；不得用 HRSC 或相似 OBB 数据替代 RarePlanes。

### 2. CAT 源字段规范恢复

- 永久保留 metadata CSV 的 raw `cat_id`。canonical CAT 只允许从同一行 `image_id` 第一个下划线
  后的完整后缀恢复，并必须同时满足：16 位大写十六进制；存在于 full GeoJSON 的 CAT 集合；与
  官方影像产品键唯一回链。格式正常的 raw `cat_id` 必须与该后缀逐字一致。
- 只有同时满足上述条件，才把 26 个科学计数法值标记为 `SOURCE_CSV_FORMAT_CORRUPTION`；任何
  格式、集合或唯一性不一致均进入 inconclusive，禁止猜测、截断、补零或人工映射。
- 主实现与不共享 parser、正则、常量或中间表的第二实现必须逐键一致复现：253 metadata 行、
  26 个损坏值、227 个 canonical CAT、与 GeoJSON CAT 交集 227、footprint 合并前 102 个
  component；预期结构为 97 个单点、4 个双点和 1 个七点。
- 加入科学计数法伪合并、非法后缀、集合缺失、重复回链和至少一个非零 mutation fixture；若 mutation
  不能使验证失败，证据无效。

### 3. 真实 COG footprint、对象 lineage 与最终 component

- 对 253 个官方 real COG 逐一读取 CRS、affine、宽、高及必要的 geospatial header，构造像素外边界
  在共同地理坐标中的地表 footprint。不得由飞机框分布、文件名、地点名或对象经纬度包络代替影像
  footprint。
- 在适当的共同地理或局部等面积坐标中，只将不同基础 component 间 `interior` 正面积重叠记为
  overlap edge；仅边界接触不合并。数值容差只能由一像素地面面积和预先冻结的几何 fixture 确定，
  不得看到 component 数后调整。
- 两个独立实现分别构造 footprint，必须对 253 个 footprint key、每条 overlap edge、最终
  component 成员与规范 key 逐项一致。第二实现不得读取主实现的 edge 或 component 判定。
- 完成 full GeoJSON 对象、official tiled annotation、metadata record 与 COG 的逐键唯一回链；
  tiled annotation 只作 lineage 核验，不重复计入 14,707 个对象 census。对投影、pixel frame、
  minimum-area long-side RP1、`w/h+90°` 等价和非零角扰动设置双实现 fixture。
- 旧 83-component manifest、split、支持表和结论必须保留为历史并明确标记 `INVALID_SOURCE_ID_PARSE`，
  不得静默覆盖或局部沿用。

### 4. 唯一 split、属性支持与未来统计合同

- 只有最终 footprint component 数不少于 100，才把规范 component key 排序并以 PCG64(1010)
  一次置换：前 25 个为 single-use test，后 25 个为 calibration，其余为 train。必须整体重新生成，
  不得沿用旧 83-component split、换 seed、拆分大 component 或按对象数调分区。
- 三个 co-primary 固定为：wing 的 raw `straight` 对 `{swept, delta, variable swept}`；engine count
  的 `2` 对 `{0,1,3,4}`；propulsion 的 `jet` 对 `{propeller, unpowered}`。其他、缺失和未知值只
  记缺失，不得重映射；`role` 仅作 secondary，`wing_position` 排除。
- 每个 co-primary 的每一类在 train/calibration/test 的对象支持至少为 `100/20/20`，包含该类的
  component 支持至少为 `10/5/5`。阈值按 split 分开实现，并以 calibration 19 失败、20 通过等
  mutation 证明没有再次共同误译为 100。
- 输出每个 split 和属性类的对象数、component 数、最大 component 对象占比与 Kish effective
  component 数；这些是设计诊断，不能把大量对象行写成大量独立重复。
- 现在冻结未来主估计量为 `class-balanced × component-equal`：先在每个 component 内算类别平衡
  结局，再对 component 等权；所有 family、seed、coverage 必须同步重采 component。禁止对象池化
  后仅套 cluster bootstrap。
- 冻结未来 calibration-only 功效门：目标差为 2 个百分点、双侧 95% 区间、80% 功效；仅在后续
  calibration 产生 component-level 差值后估计方差。功效不足则 test 保持未打开并输出
  `INCONCLUSIVE_POWER`，不得降低 2pp 门。r011 不模拟或读取任何科学 outcome，不得宣称已有功效。

### 5. 模型与分类器的真实 readiness

- 固定核验 Oriented R-CNN、Rotated RTMDet、ARS-DETR、O2-RTDETR、FRED 五个 detector family，
  以及 ResNet-50、ViT-B/16 两个分类器；换 backbone、普通 RT-DETR、旋转增强或近似实现不得冒充
  缺失 family。
- 每项必须核验官方或作者实现身份、许可、不可变版本、与实际架构匹配的合法初始化；执行真实
  config build 和 state-dict load，公开 missing/unexpected keys。允许未来任务专用输出 head 尚未
  初始化，但 backbone、neck、核心 detector/classifier 不得错配。
- 特别检查并否决把同一 ResNet-50 权重同时当作 RTMDet/CSPNeXt、O2/R50vd 等不同架构的就绪证据，
  以及把一种 ViT 实现与另一来源权重混配。FRED 不得由近似模型替代。
- 只用 synthetic schema fixture 核验 RarePlanes adapter、单类 OBB 输出、三个属性输出维度及
  long-side RP1 语义；不得对 real train/calibration/test 做模型 forward，也不得读取性能。

### 6. 独立证据与公开范围

- 第二实现必须直接读取官方原始 metadata、GeoJSON、tiled annotation、COG header、模型来源与
  权重，不得导入主实现或复用主实现生成的 availability、edge、component、split、support、模型
  清单或合同常量。
- 普通版本库只提交实现、测试、compact key/edge/component 哈希、split 与支持计数、模型
  build/load 摘要、两实现差异摘要及最终结论；原始影像、权重、逐对象大表和完整 footprint 留在
  运行证据中。
- 结论必须追加更正 r010：撤销 `83 components` 和由此产生的 `ASSET_UNAVAILABLE_R010` 数据理由，
  将 r010 记为 `INCONCLUSIVE_R010_ASSET_AUDIT_INVALID`；不得改写或删除旧证据。

### 7. 唯一裁决

按以下优先级只输出一个主状态：

1. CAT、COG/CRS、footprint、lineage、几何 fixture、模型 load 或双实现存在无法裁定的不一致：
   `INCONCLUSIVE_R011_EVIDENCE_REPAIR`；
2. 执行有效，但最终 component 少于 100、任一支持门失败、或任一当前必需 detector/classifier 的
   合法实现、兼容初始化、adapter/build/load 不足：`ASSET_UNAVAILABLE_R011`；
3. 最终数据、split、支持、几何、五 detector 与两 classifier 全部通过：
   `READY_FOR_BC_R012_FINAL_CAUSAL_VALIDATION`。

若第二种状态的唯一剩余模型缺口恰为 FRED，可额外报告非状态字段
`four_family_amendment_feasible=true`；主状态仍不得改为 READY，SERVER 不得自行删掉 FRED。只有
用户随后明确批准 outcome-blind 四 family 修订，且未来固定要求 4/4，B/C 才能另行设计 r012。

任何状态都不自动授权训练、推理、打开 single-use test、开始 r012、恢复 selector/head、转回 SAR
或修改论文。r011 的 READY 只表示最终因果验证具备设计资格，不是方法成功或期刊升档。
