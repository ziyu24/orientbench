# SERVER 科学指令

## r010：RarePlanes 官方 real 资产落地与最终验证就绪

### 1. 目标

r009 已确认当前主机没有 RarePlanes real，但官方 AWS Open Data 资源仍公开可读。r010 直接取得并
冻结唯一一次顶刊验证所需的官方 real 数据、来源分量划分、五个 detector family 与两个分类器的
合法实现和初始化资源。本轮不训练、不推理、不计算 H1/H2，不下载 synthetic，也不修改论文。

### 2. 官方数据的最小获取范围

- 只从官方 RarePlanes Open Data 来源获取 real 部分；禁止镜像、二次加工版本和 synthetic 部分。
- 必须包含并逐项校验 CC BY-SA 4.0 许可、版本/来源说明、完整 real 元数据、full annotations、
  253 条 WorldView-3 real image records 对应的官方 real 影像产品，以及从影像到对象标注的唯一回链。
- 先取得官方清单并计算预计字节数；只同步上述必需对象。禁止为方便而递归同步整个公开资源。
- 对每个取得对象记录官方键、字节数并完成内容完整性校验；缺失、重复、损坏、real/synthetic 混淆或许可
  不可核验均不得静默补齐。

### 3. 唯一来源分量与 single-use 划分

- 对象 census 只以 full GeoJSON 为权威；官方 tiled annotations 只作回链核验，不重复计数。
- 以 `loc_id↔CAT/source-product` 二部图连通分量为基础，再合并地理 footprint 重叠分量；同一
  source product、地点或重叠地理分量不得跨 split。
- 在看任何模型输出前，将规范化 component key 排序后用 PCG64 固定种子 1010 做一次确定性置换：
  前 25 个 component 为 test，接着 25 个为 calibration，其余为 train；不足 100 个 component
  直接判资产不足，不更换种子。
- test 只能称为预注册、程序性信息墙下的 single-use component-held-out test，不得称 external
  blind。r010 不得读取 test 的模型结果或下游损失。
- 主几何只使用从 GeoJSON 经正式投影/GeoTIFF 变换进入 image-pixel frame 后的 minimum-area
  rectangle long-side RP1 `(theta_long,L,S)`；nose-tail 航向和经纬度角不得替代普通 OBB 轴向角。

### 4. 固定属性支持门

三个 co-primary 预先固定为：

1. wing：`straight` 对 `swept-back|delta|variable-sweep`；
2. engine count：`2` 对 `0|1|3|4`；
3. propulsion：`jet` 对 `propeller|unpowered`。

以上是固定二分类映射；缺失、未知或其他原值不进入该属性，不得在看到计数后重映射。`role` 只作
secondary endpoint，`wing_position` 排除。每个 co-primary 的每个类别必须在
train/calibration/test 分别至少有 100/20/20 个 joint-complete 对象；任一 co-primary 无法形成至少
二分类则判资产不足。不得换 split、删困难 component 或看模型性能后改映射。

### 5. 最终验证所需模型资产

- detector family 固定为 Oriented R-CNN、Rotated RTMDet、ARS-DETR、O2-RTDETR、FRED；换
  backbone 不得冒充新 family。
- classifier 固定为 ResNet-50 与 ViT-B/16。只取得许可兼容的官方实现、不可变版本和通用初始化
  权重；RarePlanes 属性 head 后续由 train split 训练，本轮不得训练。
- 复用已存在且可核验的实现/权重；仅对 r009 证明缺失的项目取得官方来源。所有新增来源必须记录
  许可、版本、内容完整性和最小适配缺口，且不得用普通 RT-DETR 冒充 O2-RTDETR、用旋转增强冒充
  FRED、用 ARS-DETR 权重冒充其他 family。
- CPU 配置构建与接口单元测试允许；dataset forward、模型推理、性能读取和随机初始化占位禁止。

### 6. 独立核验与可复算证据

第二实现不得读取主实现的 availability 判定，必须从官方清单、已取得文件及注册索引重新核验：

- official key、bytes、许可和 real-only 完整性；
- full GeoJSON 对象 census、影像/标注回链、component 图及 split key 完全一致；
- 三个 co-primary 的逐 split 支持计数和 long-side RP1 fixtures；
- 五 detector 与两个 classifier 的实现身份、版本、初始化资源和许可。

普通 Git 只提交获取/验证代码、配置、compact 清单、计数、差异摘要和最终结论；原始影像、权重及
大型清单留在主机固定资产或运行产物中，不进入普通 Git。

### 7. 唯一裁决

按优先级只输出一个状态：

1. 官方清单、下载、许可、完整性、解析或双实现不一致且无法裁定：
   `INCONCLUSIVE_R010_ASSET_MATERIALIZATION`；
2. 核验有效，但 real 数据、component 数、属性支持、任一必需模型实现或合法初始化资源不足：
   `ASSET_UNAVAILABLE_R010`；
3. 数据、split、属性及全部模型资产均通过：`READY_FOR_BC_R011_FINAL_VALIDATION`。

只有第三种状态允许 B/C 另签唯一一次 H1/H2 正式验证；它本身不是科学 PASS，也不授权 SERVER
自动训练或推理。第二种状态意味着停止 RarePlanes 顶刊扩展并按 JSTARS 收敛，不得继续换近似
数据集、恢复 selector/head 或恢复 SAR。
