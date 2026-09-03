# SERVER 科学指令

当前没有活动 SERVER 指令。r007 与 r008 已分别完成为 `ASSET_UNAVAILABLE_R007` 和
`ASSET_UNAVAILABLE_R008`；不得自动启动训练、推理或 r009。以下保留 r008 协议作为结论边界。

## 历史 r008：RarePlanes 顶刊验证资产与来源分量划分资格门

### 1. 目的与结论边界

外部专家建议本项目停止小型 selector/head 和 SAR，唯一保留的顶刊问题是：OBB 方向误差是否
实质损害细粒度飞机属性决策，以及无 test GT 的方向扰动—决策稳定性是否能在固定覆盖率下降低
该风险。RarePlanes 真实 WorldView-3 数据因具有独立地点、有序飞机 diamond、细粒度属性和
成像元数据而被指定为唯一候选。

r008 只回答现有主机资产能否支持一次严格的 component-held-out r009。不得训练或推理 detector/
classifier，不得计算 H1/H2、角误差与属性错误的关系、风险排序或论文指标，不得修改论文。
`READY` 仅允许 B/C 设计并签署 r009，不代表方法成立或期刊升档。

HRSC2016 不用于本轮，因为 r004--r006 已打开其 official test，且它没有本问题所需的多属性飞机
决策标签；这构成本次首次验证不用 HRSC2016 的科学理由。

### 2. 只读候选范围

- 只检查主机固定数据、第三方实现和权重索引中已经存在且可读取的资产。不得联网下载、从其他
  项目复制、生成伪权重，或用相似数据/模型替代缺失项。
- 数据只允许 RarePlanes 全部真实部分；synthetic imagery、合成 labels 和官方混入同地点
  observations 的默认 test split 均不得进入未来确认设计。
- 记录数据版本、许可和允许用途；目录或文件名存在不等于可用，必须从原始影像、metadata 与
  annotation 实际解析并核对。

### 3. 数据、地点与来源资格

第一实现与独立第二实现分别从原始记录解析，至少核对：

1. 官方量级的 253 个 WorldView-3 real image records、112 个 `loc_id` 和约 14700 个真实飞机；
   分别报告 `(loc_id,CAT)` observations、unique CAT/source products、tiles、locations、objects、
   重复与缺失，禁止把 253 条 observation 预先宣称为 253 个独立 acquisition，也禁止为命中
   名义数字丢弃异常记录。
2. `RarePlanes_Public_All_Annotations.geojson` 是对象 census 的唯一权威；带约 20% overlap 的
   tiled annotations 只做图像定位和一致性核对，不得再次计数或单独进入 split。
3. 构造 `loc_id <-> CAT/source-product` 二部图；共享任一 source product 的地点属于同一
   connected component。再用 metadata 中的机场身份和地理 footprint 合并重复地理位置；最终
   component 才是不可拆分的最高层 cluster，所有日期、observation、tile 与对象随其移动。
4. off-nadir、target azimuth、scan direction、pan resolution、weather、sensor 与 acquisition time
   的字段语义、单位、缺失率和取值范围；不得把缺失值填补成常数。
5. 许可、版本、source lineage、image/annotation 一致性和对象键唯一性全部可复核。

全局真实数据不足以形成 25 calibration、25 single-use test 和至少 50 training connected
components，记资产不可用；不得用 observation、tile、loc_id 或共享 CAT 的地点冒充独立单位。

### 4. diamond、OBB 与属性语义

- 原始 diamond 顶点顺序必须明确为 nose--left wing--tail--right wing，但本项目不把 nose--tail
  360° heading 当 detector 方向。唯一主几何是四点 polygon 在影像 pixel frame 中所得的
  minimum-area rectangle，并唯一规范为 `(theta_long, L, S)`，其中 `L>=S`、`theta_long` 是
  long-side RP1 轴向。未来所有 detector/crop/H1/H2 都只用这一对；不得混入 fuselage axis。
- 若 GeoJSON 为 EPSG:4326，必须先经对应 GeoTIFF geotransform 或局部投影变到 pixel/metric
  frame，禁止直接在 longitude/latitude 上计算角、边长或 min-area rectangle。顶点循环、顶点
  逆序、角度单位和 `w/h+90°` mutation 后 `(theta_long,L,S)` 必须等价。
- 三个 co-primary appearance decisions 现在固定，不得在看到 split 或性能后删类：
  `wing_group={straight, nonstraight}`，其中 full GeoJSON 原始字符串 `straight -> straight`，
  `swept|delta|variable swept -> nonstraight`；若出现任何其他非空原始字符串，记 schema 不可裁定，
  不得由实现自行猜测或静默归组；
  `engine_group={0-or-1, 2, 3-or-4}`；
  `propulsion_group={jet, propeller-or-unpowered}`。映射只由官方原始 `wing_type`、`num_engines`、
  `propulsion` 生成；unknown/missing 不插补。
- `role_group={civil(role_id 1--3), military-support(role_id 4 or 7),
  military-combat(role_id 5 or 6)}` 仅为 secondary endpoint，因为 role 含层级/派生语义，不能
  充当第四次独立机制复现或救回任一 co-primary 失败。`wing_position` 明确排除。
- 对三个 co-primary 和 secondary role 分别给出 class×component 支持表。每个冻结 class 必须
  至少提供 training `100 objects/10 components`、calibration `20 objects/5 components`、test
  `20 objects/5 components`；否则资产门失败，不得事后再合并、删除或换属性。

### 5. outcome-blind 来源分量划分

- 先按上一节 connected component 聚合并按规范化 component ID 排序，再用 PCG64 seed
  `20260903` 做一次固定 permutation；前 25 个 component 为 preregistered single-use test、
  随后 25 个为
  calibration，其余为 training pool，且必须留下至少 50 个 training components。
- permutation 和 split assignment 只能读取 component identity，不得读取属性值、方向、类别频率、
  模型输出或未来风险；不得为改善 class balance 手工移动地点。split 冻结后才可由独立 census
  进程生成上一节的属性支持表。
- RarePlanes 标签与本次 split 都是公开可重建资产，因此这里不是外部私密 blind test。唯一可
  声称的纪律是 preregistered、程序性信息墙与 single-use component-held-out evaluation；未来
  论文不得使用 `sealed test`、`external blind test` 或同义夸大措辞。
- r008 不读取任何模型性能。test annotation 可由 census 进程只用于 schema/计数/支持核验，
  但不得与未来 prediction key 共表；输出只含分层计数，不含可直接恢复 test 对象属性与方向的
  联合逐行表。
- 未来 r009 必须复用本次固定 split；若任一预注册属性支持不足，r008 只能报告不足，禁止在
  r009 开 test 后改 split、删类或换属性。

### 6. 五 detector 与两个下游模型的 readiness

只做现有资产的 import/config/build 级只读检查，不进行 dataset forward、训练或推理：

- 五个严格不同 detector family 必须逐一可识别：Oriented R-CNN、Rotated RTMDet、ARS-DETR、
  O2-RTDETR、FRED。换 backbone 不算新 family；ARS-DETR 不得冒充其他 DETR，普通 RT-DETR
  不得冒充 O2-RTDETR，旋转增强不得冒充 FRED 的全流程等变实现。
- 每个 family 必须有可加载的真实实现、RarePlanes 单类 detector 数据接口、OBB 输出角约定、
  可用初始化权重和足以执行三 seeds 的训练/评价配置。允许 SERVER 为未来列出最小适配工作，
  但不得在本轮编写替代模型或开始训练。
- 两个下游模型固定为 ResNet-50 与 ViT-B/16；必须有可加载实现和初始化权重，并能在同一 crop
  合同下输出四属性各自的完整概率向量。
- 核对未来所需通用非 oracle 基线输入是否可产出：detection score、predicted AR/size、分类
  entropy/margin、TTA 角离散度、三 seed ensemble disagreement、photometric/center/scale
  perturbation stability、off-nadir 与 resolution。AQE/PQA/O2 原生质量只在对应实现真实输出时
  登记，不得伪造为全模型共有信号。

五个 detector family 或两个下游模型任一缺必要实现/权重/语义时，完整顶刊组合不具备资格；
不得以四模型结论、近邻 architecture 或新增小 head 降格补齐。

### 7. 未来 r009 的冻结可行性检查

不运行实验，只生成并验证以下未来协议骨架：

- `H1a`：calibration component 上的 GT box 固定中心及 ordered `(L,S)`，仅作
  `theta_long_GT±10°` 配对扰动；两个分类器的三个 co-primary 等权 balanced error 至少恶化
  2 个百分点，component-cluster CI 下界大于 0。
- `H1b`：每个 detector 同一预测固定中心及 ordered `(L,S)`，只把 predicted long-side theta
  替换为 GT long-side theta；
  错误绝对下降至少 2 个百分点且相对下降至少 20%，两个分类器各至少 4/5 families 同向。
- `H2` 唯一候选：固定预测框，仅在 `{-10°,-5°,0°,5°,10°}` 上改变轴向 crop；对每个属性计算
  原输出与扰动输出的 Jensen--Shannon divergence，并以跨属性/扰动最大值作为风险。它不得与
  score 或其他特征融合，也不得学习 test error。
- test 主门：90% coverage 相比 calibration 选定的最强非 oracle baseline，balanced error 绝对
  改善至少 2 个百分点、相对至少 20%、component-cluster CI 上界小于 0；AURC 相对改善至少 15%，
  70% coverage 不反转，两个分类器各至少 4/5 families，且三个 co-primary 全部同向；secondary
  role 只披露，不能救回或否决主门。
- 未来最高独立单位为 connected component；三个 detector seeds 等权，所有 arm 用同步
  component-cluster bootstrap。test 性能只计算一次，任何阈值、属性、模型和 coverage 不得
  事后修改；这只是 single-use protocol，不得称外部盲测。

只验证这些字段、估计量和强基线能否由当前 schema 唯一实现；不得填入真实预测、属性错误、
相关性、p 值或模拟的 PASS/KILL。若骨架需要 test GT 才能生成部署分数，资格直接失败。

### 8. 可复算证据

提交实际解析、去重、地理分组、diamond/OBB canonicalization、split 生成、模型 readiness 与独立
验证代码和测试，并生成 compact 证据：

- 数据版本/许可/census、observation--CAT/source-product--loc_id--component lineage、full/tiled
  重复与缺失审计；
- 不含模型结果的固定 split manifest，以及 split×attribute×class 的对象/component 支持表；
- diamond/OBB/heading/RP1 语义说明与等价、非零 mutation fixtures；
- 五 detector、两个 classifier 的逐项 readiness 及不可替代 reason codes；
- 未来 H1/H2 估计量、信息墙、强基线、component bootstrap 和一次 test performance calculation
  的 schema-only 合同；
- 第二实现从原始记录独立解析后的 key、计数、连续量容差和最终 token 比较。

大清单和逐对象表只留运行产物；普通 Git 只提交源码、配置、测试、compact 证据与
`lab/result.md` 结论。两实现对数据键和 split 必须完全一致；几何连续量容差由 fixture 在读取
数据前固定，并报告实际最大差。

### 9. 三态裁决

按以下优先级只输出一个状态：

1. 原始文件损坏、许可/版本无法判定、解析或坐标语义不确定，或两实现不一致且不能从原记录
   裁定：`INCONCLUSIVE_R008_ASSET_AUDIT`。
2. 执行有效，但真实数据、独立地点、四属性支持、五 detector families、两个 classifiers、必要
   baseline 输入或 split 任一硬门不足：`ASSET_UNAVAILABLE_R008`。
3. 全部数据、标签、split、模型和协议资格门通过：`READY_FOR_BC_R009_DESIGN`。

三个状态都不是 H1/H2 科学结果，不修改当前 strong-JSTARS 期刊判断，也不得自动训练、推理、
生成 600×3 人工标签、修改论文或启动 r009。SERVER 提交本轮证据后停止，等待 B/C 复核。
