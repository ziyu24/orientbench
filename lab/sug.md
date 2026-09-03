# SERVER 科学指令

本文件是当前任务单槽；只有下面一个活动任务。r007 是资产资格审计，不是模型实验或科学
PASS/KILL。任何结果都不得自动启动下一轮。

## r007: SAR acquisition-axis 元数据资产资格门

### 1. 目的与结论边界

待检验的未来命题是：SAR 成像的 range/azimuth 轴会对旋转目标的方向可靠性产生可区别于普通
像素坐标偏置的物理各向异性。现有光学数据和只带旋转框的 SAR 切片不能识别这个命题；r007
只判断主机既有数据是否足以设计后续实验，不计算机制效应。

r007 不训练、不推理、不读取任何模型输出，不下载或补造数据，不计算检测误差、关联、显著性
或论文指标。`READY` 仅允许 B/C 另立 r008；它不是科学结果、方法准入或期刊升档。

### 2. 只读候选范围

- 只检查主机固定数据目录中已经存在、具有本地可核验版本与使用许可的 SAR 数据。公开名称可
  用于识别候选，但目录存在本身不算可用；不得联网下载、解压替换或从其他项目复制资产。
- 一个独立域必须对应一个真实独立 SAR sensor/platform。同一传感器的 ascending/descending、
  look direction、polarization 或 imaging mode 只能作为域内 acquisition strata，不能冒充第二域。
- `scene` 固定指一次原始 acquisition/product，不是 tile、chip 或增强样本。同源切片必须回并到
  同一 scene；重复对象和重叠切片不得重复计数。

### 3. 坐标与标签合同

每个 scene 必须从原始产品 metadata 或 geolocation grid 独立解析并记录：sensor/platform、
source product identity、acquisition time、orbit direction、look direction、slant/ground-range 类型、
projection/geotransform、range/azimuth pixel spacing，以及 range/azimuth 轴在 OBB 所在 pixel/map
frame 中的方向。轴方向不得从文件名、图像边缘、目标分布或图像内容猜测；north-up 图像边缘
不得冒充 acquisition axis。

资格分层对每个 scene 只取一次 ground-range axis 在共同 Earth-fixed/local-ENU map frame 中相对
真北的 RP1 axial azimuth，规范到 `[0°,180°)`。azimuth axis 只用于正交性、handedness 与坐标
变换校验，不得作为第二条观测或第二个 stratum；annotation-frame 中的轴方向也只用于未来对象
配准，不进入 READY 的多取向支持门。

每个对象必须唯一回链 scene，并记录 class、ignored、原始 polygon/OBB、label semantics 与生成
方式。明确区分 SAR appearance box、map-footprint 派生框、人工 polygon/minAreaRect 等来源。
主计数只使用非忽略且 long-side aspect ratio `>=2.1` 的对象。对象轴由 polygon 复核后按 RP1
long-side canonicalization 表示；顶点循环移位、顶点逆序和 `w/h + 90°` 必须保持轴向恒等。

若存在 AIS，只在 time、space 与 track identity 均唯一回链时登记为外部锚，并严格区分 true
heading 与 course over ground；AIS 不是 READY 必需条件，也不得用于填补 acquisition metadata
或 OBB。

### 4. 信息墙

r007 只可报告 acquisition-axis 的边际分布与 OBB 轴的边际分布、计数、缺失、重复、键关系和
schema。禁止计算、保存或查看 `theta_OBB - theta_axis`、二者的联合表、任何 association/p 值、
模型预测或方向误差；不得按这些未来结局筛选 sensor、scene、stratum 或对象。

可提交的 compact 证据不得同时包含可由共同键连接的逐 scene axis 值与逐 object OBB theta。
scene-axis 与 object-angle 的逐行审计资产必须分离封存，任何生产或验证进程都不得把两者加载到
同一表；公开的 lineage/key 审计只含身份关系而不含任何角值，axis 与 OBB angle 只分别发布无
共同标识符的边际聚合。独立实现分别从原始记录复核两侧，并只输出逐字段差异摘要。

所有缺失字段逐字段公开，不插补。READY 计数一律在 joint-complete、去重后的冻结总体上计算；
不得先丢失不可读对象再补样或用 chip 数替代 scene 数。

### 5. 唯一资产门

每个候选 sensor/platform 域分别检查，只有同时满足以下全部条件才是合格域：

1. 本地版本、许可文本和本项目研究使用范围可核验；原始 metadata、图像与 OBB annotation 能
   形成唯一 source-product→scene→chip→object 链。
2. joint-complete metadata 覆盖率按 scene 分母和 eligible-object 分母分别均 `>=95%`。
3. 去重后至少 `200` 个独立原始 scenes，且至少 `1000` 个非忽略、AR `>=2.1` 对象。
4. ground-range axial azimuth 使用 `[0°,180°)` 上固定的 18 个 10° 半开 bins：
   `[0°,10°),...,[170°,180°)`，bin center 固定为 `5°,15°,...,175°`；`180°` 归入 `0°`。
   至少两个非空 bin 的中心 RP1 距离 `>=20°`，且每个 bin 至少 `50` 个独立 scenes 和
   `250` 个 joint-complete eligible objects。每 scene 只按 metadata ground-range axis 归入一个
   bin；不得看完分布后改边、合并箱，或使用 azimuth/annotation-frame 轴补足门槛。
5. acquisition axis 已从原始坐标严格变换到 annotation frame；range/azimuth 正交性、坐标轴
   handedness、角度单位和 pixel/map round-trip 夹具全部通过。
6. 按 source scene 可形成互斥划分；同一地理 footprint 的跨时相重复 acquisition 以 geographic
   connected component 成组隔离。若有可配对重复采集，只披露数量，不得替代上述硬门。

最终 READY 必须至少有两个合格且 sensor/platform 不同的域；任何一个传感器都不能由同传感器
的多个轨道、视向或模式重复计数。

### 6. 可复算证据

提交实际解析、坐标变换、去重、分组和验证代码及自动测试，并生成以下 compact 证据：

- 数据版本/许可与候选 census；
- 不带逐 scene 身份的 axis/metadata 边际表、不带逐 object 身份的 OBB geometry 边际表，以及
  两侧各自的字段缺失率表；
- source-product→scene→chip→object 键审计、重复对象审计和 geographic grouping 审计；
- acquisition-axis 边际分层计数与 OBB 轴边际直方图，二者不得进入同一联合表；
- 坐标变换、RP1 canonicalization、round-trip 和非零 mutation 夹具结果；
- 冻结资格判定及逐门 reason code。

第二实现必须直接从原始 metadata 与 annotation 重新解析，不能读取第一实现的 compact 表，
也不能跨信息墙连接逐行 axis 与 OBB theta。
categorical/key 逐项一致；连续坐标误差不超过 `1e-6` pixel，轴向角误差不超过 `0.01°`，所有
域计数和资格 token 必须完全一致。大表不进入普通 Git；可复算代码、配置、compact 结论和项目
结果文档必须提交。

### 7. 三态裁决

按以下优先级给出且只给出一个状态：

1. 原始文件损坏、解析器不能完成、坐标合同无法判定，或两实现超差且不能由原始记录裁定：
   `INCONCLUSIVE_R007_ASSET_AUDIT`。
2. 执行有效，但许可、来源链、metadata 覆盖、数量、分层或双 sensor/platform 任一硬门失败：
   `ASSET_UNAVAILABLE_R007`，项目回到 `NO_ACTIVE_TASK`。
3. 至少两个独立 sensor/platform 域通过全部硬门，且第二实现逐键一致：
   `READY_FOR_BC_R008_DESIGN`。

任何状态都不得输出科学 PASS/KILL、不得评价 acquisition-axis 机制是否成立、不得启动 r008、
训练、推理或改论文。SERVER 完成后只提交证据与本轮资产结论，等待 B/C 复核。
