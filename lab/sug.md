# SERVER 科学指令

本文件是当前任务单槽；只有下面一个活动任务。r009 仅修正 r008 的资产搜索与验证，不训练、
不推理、不下载数据，不计算 H1/H2，不修改论文，也不得自动启动后续实验。

## r009: RarePlanes 资产搜索与模型 readiness 修正审计

### 1. 修正目标

r008 的 `ASSET_UNAVAILABLE_R008` 不予验收：数据搜索只查四个顶层目录别名，遗漏官方常见的
`RarePlanes-Public` 名称和内容特征；两个分类器与权重状态被直接写成 unavailable；O2-RTDETR
没有检查已知的 ai4rs 内部实现位置；独立验证又复用了同一别名集合。

r009 必须真实回答：主机固定资产中是否存在可用 RarePlanes real 数据、五个 detector family、
两个下游 classifier 及其必要权重。不得继续用常量或目录名猜测代替核验。

### 2. 数据资产的完整有界搜索

- 先读取主机固定 dataset 索引，再只在该固定数据根内进行大小写不敏感、符号链接解析后的有界
  枚举；不得扫描数据根之外的磁盘。
- 同时按目录别名和内容签名寻找候选。目录别名至少覆盖 `RarePlanes-Public`、
  `RarePlanes_Public`、`RarePlanes`、`RarePlanes_real` 与 `rareplanes`；内容签名至少覆盖
  full annotations、metadata、license、real imagery 和 real tiled annotations 的官方文件名/结构。
  任一内容签名命中都必须继续解析，不能因父目录名称不同而判 absent。
- 对所有候选报告 canonical identity、regular-file/readability、real/synthetic 分离、许可、版本、
  full GeoJSON、metadata、原始影像和 tiled 影像的实际存在性。候选损坏或语义不明不能写 absent。
- 若找到可用 real 数据，继续完成 r008 已冻结的 full-GeoJSON 唯一对象 census、
  `loc_id↔CAT/source-product` 二部图连通分量、地理重复合并、25 test/25 calibration/至少50
  training components、三个 co-primary 与 secondary role 支持表，以及 pixel-frame
  `(theta_long,L,S)` 几何 fixtures；不得采用官方混地点 default split 或重复统计 tiled objects。

### 3. 五 detector 与两个 classifier 的真实核验

- 读取固定 third-party 注册信息和与本任务相关的权重索引条目；不得把权重状态预填为 false，
  也不得仅以顶层目录是否存在判断 family。
- 分别解析 Oriented R-CNN、Rotated RTMDet、ARS-DETR、O2-RTDETR、FRED 的真实内部实现位置、
  config 可加载性、RarePlanes 单类数据接口可适配性、OBB 输出角语义和必要初始化权重。
- O2-RTDETR 必须检查 ai4rs 中已登记的 rotated-RTDETR project；Rotated RTMDet 不能仅因 ai4rs
  根存在就判 available。ARS-DETR、普通 RT-DETR 与 O2-RTDETR 不得互相冒充；换 backbone 不算
  新 family；普通旋转增强不得冒充 FRED。
- ResNet-50 与 ViT-B/16 必须从实际 classifier 实现和相关权重索引核验，报告可加载性及四输出
  head 的最小适配状态。不得在本轮训练或用随机初始化冒充 ready。
- 只允许 CPU 上的 import/config/build/readability 检查，不运行任何 dataset forward、模型推理
  或训练。确实需要代码适配但资产存在时，记录为 `ADAPTATION_REQUIRED`，不能写成资产 absent。

### 4. 独立验证

第二实现不得导入主审计模块，也不得读取主审计的候选列表或 availability 判定。它必须：

1. 独立读取 dataset 与权重索引；
2. 独立按官方内容签名枚举 RarePlanes real 候选；
3. 独立解析五 family 的实际内部实现位置及两个 classifier 权重；
4. 逐项比较数据候选、real 文件集合、模型 family 身份、权重存在性、readiness reason code、
   component/split/属性计数和最终 token。

两实现候选集合或关键判定不一致、任一搜索异常被吞掉、内容签名命中却未解析，均为
`INCONCLUSIVE_R009_ASSET_AUDIT`，不得用主实现 token 反向证明自己。

### 5. 可复算证据

提交实际搜索、索引解析、数据解析、模型/权重 readiness 和独立验证代码及测试，并生成：

- dataset 索引的 RarePlanes 相关条目、数据根有界枚举摘要、目录别名与内容签名命中表；
- 每个候选的 real/synthetic、许可、full/tiled/metadata/image 完整性与 reason code；
- 五 detector 和两个 classifier 的内部实现、配置、权重与语义 readiness 表；
- 数据可用时的 component lineage、固定 split、属性支持与几何 fixture compact 结果；
- 两实现逐项差异表、mutation tests 和唯一最终 token。

大清单只留运行产物；普通 Git 只提交可复算源码、配置、测试、compact 证据和
`lab/result.md` 结论。

### 6. 唯一裁决

按优先级只输出一个状态：

1. 搜索、解析或双实现不可裁定：`INCONCLUSIVE_R009_ASSET_AUDIT`；
2. 核验有效，但 RarePlanes real 数据、来源分量/属性支持、五 detector、两个 classifier 或必要
   权重任一不足：`ASSET_UNAVAILABLE_R009`；
3. 全部资格门真实通过：`READY_FOR_BC_R010_DESIGN`。

三个状态均不是 H1/H2 科学结果，不改变当前 strong-JSTARS 判断。任何结果都不得下载资产、
启动训练/推理、恢复 SAR、修改论文或自动启动 r010；SERVER 提交证据后停止，等待 B/C 复核。
