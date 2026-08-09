# OrientBench 顶刊路线可行性门设计（书面审阅稿）

```yaml
document_status: AWAITING_WRITTEN_SPEC_REVIEW
date: 2026-08-09
base_commit: a9067fb16d2bbd747dfe69789ac33a5911eb15fe
user_conceptual_approval: true
server_execution_authorized: false
r019_formal_status: INVALIDATED_R019
target_route:
  primary: ISPRS_JPRS_measurement_diagnostic
  conditional: TGRS_method_upgrade
  cvpr_iccv: closed_without_general_mechanism_and_clean_evidence
cc_recommendation: no
```

## 1. 决策与目标

OrientBench 不再把 learned EQS 作为主论文贡献。主线改为：面向旋转目标检测（OBB）的、几何等价感知且以场景为统计单位的方向可靠性测量与诊断框架。目标首先对齐 ISPRS Journal of Photogrammetry and Remote Sensing；只有在后续取得两个真正未触碰的遥感 OBB 数据集并完成新的前瞻性、无目标域标签调参的机制验证后，才升级为 TGRS 方法论文。

r019 的服务器计算已经运行到 DOTA 标签揭示与 10,000 次 bootstrap，但其预注册硬前提没有被可验证地执行：prior-outcome 搜索、零标签访问防护、独立 validator 负例、封存后执行代码和证据清单均不闭合。因此 r019 的正式状态是 `INVALIDATED_R019`，不是可采信的外部 `PASS`、`FAIL` 或 `INCONCLUSIVE`。其数值只能作为失效实验的描述性诊断，不能恢复前瞻身份，也不能通过重跑 DOTA、替换 gate 或启用 HRSC“救场”。

本设计只冻结下一步的可行性审计。它不是服务器执行指令；用户书面审阅通过前，不改写 `dis/sug.md`，不启动服务器任务。

## 2. 论文贡献边界

### 2.1 主张

论文只主张一个窄而可验证的贡献：

> 一个 detector-agnostic、angle-specific、geometry-equivalence-aware、scene-aware 的 OBB 方向失败测量与诊断协议，并提供跨检测器/数据集的可复现实证。

核心组成是：

1. 对 OBB 的长边规范化和 180° 轴向等价进行显式处理，避免把等价框误计为方向错误。
2. 将方向风险按长宽比和严重度分层，区分近方形角度不可辨识与真正严重的方向失败。
3. 以 image 或原始 mother scene 为 cluster 做不确定性估计，禁止把 tile、实例行数或匹配对数量冒充独立样本量。
4. 同时报 AUGRC、完整 risk–coverage 曲线和固定 coverage 工作点；NRC/AURC 仅作为兼容性或敏感性结果。
5. 公开 evaluator、冻结清单、数据口径和可重放统计证据。

### 2.2 禁止主张

不得声称以下概念首创：TTA uncertainty、angle quality、跨检测器 reliability benchmark、selective prediction 或多次推理的 angular dispersion。若使用无训练分数，只能称 `training-free` 或 `no learned parameters`，不能称 `parameter-free`，因为变换集合、匹配、阈值、canonicalization、未匹配处理和 coverage 均是设计参数。

learned EQS、r015 和 r019 不得被包装为“发现—确认”链，不得与新前瞻结果合池或做同一算法的 meta-analysis。它们至多进入附录中的开发史、失败迁移审计或负面结果。

### 2.3 最近工作约束

书写和实验至少正面对照以下相邻工作：

- Wang et al., *High-Quality Angle Prediction for Oriented Object Detection in Remote Sensing Images*, IEEE TGRS 2023, DOI: https://doi.org/10.1109/TGRS.2023.3292111
- Magalhães and Bernardino, *Quantifying Object Detection Uncertainty in Autonomous Driving with Test-Time Augmentation*, IEEE IV 2023, DOI: https://doi.org/10.1109/IV55152.2023.10186713
- Oksuz et al., *Towards Building Self-Aware Object Detectors via Reliable Uncertainty Quantification and Calibration*, CVPR 2023: https://openaccess.thecvf.com/content/CVPR2023/html/Oksuz_Towards_Building_Self-Aware_Object_Detectors_via_Reliable_Uncertainty_Quantification_and_CVPR_2023_paper.html
- Kassem-Sbeyti et al., *Cost-Sensitive Uncertainty-Based Failure Recognition for Object Detection*, UAI 2024: https://proceedings.mlr.press/v244/kassem-sbeyti24a.html
- Traub et al., *Overcoming Common Flaws in the Evaluation of Selective Classification Systems*, NeurIPS 2024: https://openreview.net/forum?id=2TktDpGqNM
- Di Leo et al., *Uncertainty-Aware Rotation Estimation for YOLO-Based Oriented Object Detection*, IEEE AI4IM 2026, DOI: https://doi.org/10.1109/AI4IM69129.2026.11558216

当前可辩护的新颖性级别是“benchmark/measurement 层面的中等实质新颖性”，不是强方法级首创。

## 3. 本轮唯一授权候选：无 GPU 可行性门

书面审阅通过后，下一轮只能生成一份新的、独立的服务器任务书，执行以下两个并行但相互独立的只读审计轨道。该任务不得下载数据、训练、推理、修改主稿或调用 CC。Track M 只可在已经消费、且能闭合来源的旧数据上重算描述性指标；Track D 不得打开任何新候选数据集的标签计算 outcome，也不得生成新 endpoint。

### 3.1 Track M：现有证据的度量稳健性审计

#### 科学问题

在不新增模型运行、不改变样本、不拟合目标域参数的前提下，现有可追溯 raw/GT/risk/score 资产是否足以证明论文的主要测量结论不会因选择性预测指标或部署 coverage 改变而反转？

#### 输入边界

1. 只允许读取已有且能用字节数、SHA256、schema、row key 和来源提交闭合的资产。
2. 先盘点资产，再计算；缺少 raw/GT 或逐实例 score 时必须报告 `INSUFFICIENT_ASSETS`，不得从汇总表反推或补造实例数据。
3. r019 资产必须带 `INVALIDATED_R019_DESCRIPTIVE_ONLY` 标记，不能进入前瞻验证或总体显著性家族。
4. 不允许重新拟合 EQS、改变权重、挑 coverage、换匹配规则，或依据结果选择更有利的指标。

#### 固定评估对象

在 byte-exact 资产确实存在时，评估以下分数；不存在则明确记缺失：

1. 原始 detection confidence。
2. confidence + aspect ratio + object size 的固定线性基线。
3. 通用 TTA localization/angle disagreement 基线。
4. 固定的无学习候选分数 `S0 = -(u_axis + missing_fraction + iou_loss)`。
5. learned EQS 仅作描述性失败迁移参照，不进入候选获胜判定。

#### 固定指标与统计单位

1. 主指标：AUGRC。
2. 必报：完整 risk–coverage 曲线、`Risk@70%`、`Risk@90%`、非空 coverage 范围。
3. 敏感性：原 NRC/AURC，仅用于检查指标排序是否反转。
4. cluster：DIOR/FAIR/HRSC 等按完整 image；SODA/DOTA 等切片数据按原始 mother scene。零 eligible cluster 必须保留。
5. dataset 内先算 unit，再做 unit 等权聚合；禁止 pooled-row 聚合。
6. 置信区间按完整 cluster universe bootstrap；两个比较分数在同一 replicate 使用同步 multiplicity。

#### Track M 输出状态

- `ROBUST_CANDIDATE`：候选分数相对强基线的方向在 AUGRC、固定 coverage 和预定敏感性中一致，且不依赖目标域拟合。
- `METRIC_REVERSAL`：NRC/AURC 的优势被 AUGRC 或任一固定 coverage 主工作点反转。
- `BASELINE_DOMINATED`：同等或更低推理预算的通用基线匹配或优于候选。
- `SENSITIVITY_UNSTABLE`：结论随预定匹配、未匹配、近方形或 canonicalization 敏感性发生方向翻转。
- `INSUFFICIENT_ASSETS`：无法从可追溯逐实例资产完成审计。

这些状态均为可行性裁决，不是新的论文科学 `PASS`。

### 3.2 Track D：未触碰外部数据集的资产与污染审计

#### 科学问题

是否存在两个彼此独立、此前未被 OrientBench 消费 outcome 的遥感 OBB 数据集，能够支持同一组至少三个 detector family 的前瞻验证？

#### 候选顺序

1. AI-TOD-R。
2. UAV-OBB。
3. ShipRSImageNet 仅作备选。
4. ICDAR-MLT 只能作为解析/角度语义的辅助候选；因其不是遥感主任务的充分独立确认，不能单独满足 TGRS/JPRS 双数据集条件。

上述名称只是待核验候选，不表示资产已经存在、许可已经允许、checkpoint 已兼容或数据尚未污染。

#### 只读核验项

每个候选必须逐项提供实际 witness，而不是布尔声明：

1. 官方来源、许可证/使用条款、版本、官方 split、图像和标注规模。
2. OBB 表示、角度范围、顺/逆时针、顶点顺序、近方形与 ignore/difficult 语义。
3. 服务器本地是否存在数据；只允许 path/stat/公开 metadata 级盘点，不打开标签计算指标或 endpoint。
4. 三个共同 detector family 的精确 config、checkpoint、环境、bytes/SHA256、许可证与推理兼容性。
5. Git 仓库和服务器持久目录中的 prior-outcome 搜索：数据集名、别名、config、prediction、feature、score、risk、metric、bootstrap、report 和 endpoint 均须搜索并保存命令、范围、退出码与结果清单。
6. 任何已有真实 prediction、metric、risk 或同一端点结果都使该候选记为污染；只换 detector 不会把已消费的数据集变成独立的未触碰数据集。

不得下载缺失资产，不得训练兼容模型，不得运行 forward，不得读取标签内容做 outcome，不得在本轮补建 parser。

#### Track D 输出状态

- `ELIGIBLE_CANDIDATE`：官方许可清楚、资产可复现、角度合约可独立验证、未发现既有 outcome，且能支持共同的三个 detector family。
- `CONTAMINATED`：发现既有真实 prediction、metric、risk、bootstrap 或同一 endpoint 消费。
- `MISSING_ASSET`：数据、config、checkpoint 或兼容环境缺失。
- `INCOMPATIBLE_ANGLE_CONTRACT`：角度/OBB 语义无法无歧义转换或验证。
- `LICENSE_BLOCKED`：许可证、再分发或研究用途不清楚。

## 4. 联合决策门

### 4.1 `PASS_TO_METHOD_DESIGN`

当且仅当以下条件全部满足：

1. Track M 为 `ROBUST_CANDIDATE`，且不是 learned EQS 获胜所驱动。
2. 至少两个彼此独立的遥感 OBB 数据集均为 `ELIGIBLE_CANDIDATE`。
3. 两个数据集都能支持同一组至少三个 detector family，其中至少一个 family 未参与旧 Core 开发。
4. 许可证、版本、角度合约、资产 hash、环境和 prior-outcome 搜索均有可复核证据。
5. 后续研究无需在目标标签上调权重、阈值、变换集合、匹配规则或 coverage 工作点。

`PASS_TO_METHOD_DESIGN` 只授权另起一轮撰写前瞻协议并再次请求用户批准；它不授权立即下载、训练、推理或揭示标签。

### 4.2 `FAIL_TO_MEASUREMENT_ONLY`

出现下列任一条件即关闭方法升级分支，论文直接走 measurement/diagnostic：

1. `METRIC_REVERSAL`、`BASELINE_DOMINATED` 或 `SENSITIVITY_UNSTABLE`。
2. 找不到两个合格且未触碰的遥感 OBB 数据集。
3. 共同三 detector-family 资产不成立。
4. 需要目标域标签调参才能成立。
5. 许可证或角度契约不能闭合。

不得以 DOTA、HRSC、Core-6、同一数据集的新 detector、换 gate、换 cluster 或开启 r020 来替代失败条件。

### 4.3 `INCONCLUSIVE_FEASIBILITY`

如果现有 runtime 资产已丢失或 hash/schema 不足，导致 Track M 无法重放，但 Track D 尚未出现决定性失败，则记 `INCONCLUSIVE_FEASIBILITY`。该状态不允许宣称方法可行；默认仍按 measurement-only 写作，除非以后获得新的用户授权和新的、未触碰资产。

## 5. 未来服务器任务的证据与验证合约

用户批准本书面稿后，C 侧才把它转换为新的 `dis/sug.md`。未来任务书必须满足：

1. 运行前记录完整 HEAD、HTTPS remote main、默认分支、upstream、工作树、`dis/B.md` blob 和全部输入路径。
2. 独立记录每次实际文件访问的 path、role、bytes、SHA256、schema；禁止把 hardcoded `true` 当证据。
3. prior-outcome 搜索保存 exact command、cwd、start/end、exit code、stdout/stderr SHA 和逐命中清单。
4. validator 必须从原始可追溯输入重算状态，不能导入生成端的 gate 布尔量。
5. 至少提供真实 mutation negative tests：篡改一个 score 字节、删除一个 cluster、注入假 prior outcome、篡改一个 manifest hash 后，validator 均须非零退出。
6. 报告首行明确区分 `FULL_COMPLETION`、`EARLY_STOP_TECHNICAL` 和 `FAILED_EXECUTION`；完整跑出负面可行性结论仍是执行完毕，不是早停。
7. 每个“未发现”“零访问”“一致”“通过”都必须附可复核 witness；缺证据即失败，不允许用声明替代检查。
8. 所有写路径须在新建的隔离目录和唯一 server report 内逐项授权；不得覆盖 r014–r019，禁止修改主稿、`dis/B.md` 或旧证据。

本轮设计文档本身不授权任何上述执行，也不预先占用新的 round 编号。

## 6. 通过可行性门后的实验底线

如果以后得到 `PASS_TO_METHOD_DESIGN`，新的前瞻研究至少需要：

1. 两个未触碰的遥感 OBB 数据集、每个数据集三个共同 detector family。
2. 冻结的 training-free score；目标标签揭示前完成代码、模型、raw prediction、score、cluster map、bootstrap draw 和远端 commit 封存。
3. 同预算比较 raw confidence、confidence+AR+size、通用 TTA localization/angle variance；AQE 或 MC-dropout 仅在原生可用且预算口径公平时加入。
4. 主指标 AUGRC、risk–coverage、`Risk@70%`、`Risk@90%`，并报告推理成本。
5. image/mother-scene cluster bootstrap、dataset 内 unit 等权、held-out detector 和 held-out dataset 转移。
6. 预注册失败条件：任一数据集不支持、通用基线获胜、需要目标标签调参、匹配/未匹配敏感性翻转、AUGRC 排名反转或无两个 pristine 数据集。

这些底线未满足时，不得把 measurement paper 强行包装为 TGRS 方法论文，更不得宣称达到 CVPR/ICCV。

## 7. 若方法分支关闭，measurement-only 稿件动作

1. 主标题候选：*Beyond AP: Geometry- and Scene-Aware Orientation Reliability for Oriented Object Detection*。
2. 删除 learned EQS 的主贡献地位；r015/r019 进入附录中的开发史和失效迁移审计。
3. 主结果改为几何等价、长宽比分层、场景聚类、AUGRC 与固定 coverage 的跨检测器测量结论。
4. 若现有标注复核不足，再单独设计人类标注一致性研究；该研究不能与本可行性门混跑。
5. venue 以 ISPRS JPRS 为首选；TGRS 仅在方法升级和完整前瞻证据成立后恢复为主投目标。

## 8. 书面审阅检查表

- [x] r019 被固定为 `INVALIDATED_R019`，未包装为性能失败或确认结果。
- [x] learned EQS 已从主贡献中移除。
- [x] 当前唯一下一步是无 GPU、无 outcome 的可行性门。
- [x] Track M 与 Track D 的问题、输入、输出和失败状态已冻结。
- [x] 两个独立遥感数据集和共同三个 detector family 的条件无替代解释。
- [x] AUGRC、固定 coverage、scene/mother clustering 与强基线已写入。
- [x] 禁止下载、训练、推理、标签揭示、目标调参和 r020 救场。
- [x] `PASS_TO_METHOD_DESIGN` 只允许再写协议，不直接授权实验。
- [x] 服务器完成/早停/失败语义已明确。
- [x] 没有未决占位符、可替换 gate 或伪首创表述。

## 9. 用户书面审阅点

请用户只审阅三个决定：

1. 是否接受主线永久改为 measurement/diagnostic，learned EQS 仅留附录。
2. 是否接受“两个 pristine 遥感数据集 × 共同三个 detector family”为方法升级的不可降低门槛。
3. 是否接受下一轮服务器仅做 Track M + Track D 的无 GPU 可行性审计，且其通过后仍需再次批准，才可进入真正实验。

只有这三项书面通过后，才生成并推送新的服务器执行任务。
