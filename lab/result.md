# SERVER 执行结果

## r004

### 结论

SERVER 声明为 `KILL_COI_R004`；B 独立验收不接受该声明，当前正式科学状态为
`INCONCLUSIVE_R004_PROTOCOL_VALIDITY`。八个负向点估计保留为未验收的描述性结果，不能
改名为信息论上限、通用定律或人机共同规律，也不能据此关闭 COI。

## r005

### 唯一裁决

`INCONCLUSIVE_R004_PROTOCOL_VALIDITY`。

这是一次 correction-only 闭环：未做新的 detector 推理、训练、剂量选择、模型/数据替换或
论文修改。r005 修复了 r004 的 matcher 与证据缺口，但真实操纵 Holm-32 的前三类中
`clean-high>0.20` 有 8 项失败。因此试验有效性未成立，低 `DeltaY` 不能触发
`KILL_COI_R004`。

### 冻结输入、matcher 与独立复算

- 冻结输入清单由 `r005-frozen-input-manifest` 发布在
  `refs/heads/exec/r005-frozen-input-manifest@73a96f3d`；所有输入均为 r004 的 clean/四剂量
  预测、原 HRSC 图像及固定 trainval/test split。
- trainval 与 test 均调用同一 theta-free exhaustive matcher：候选只由 class、归一化 center、
  area、无序边长决定，按 `(cost, gt_index, pred_index)` 全局排序并一对一贪心。它返回完整
  GT--prediction 配对，不读取 theta、angle error 或 oriented IoU。
- 两 GT/两预测反例已由 `src/tests/test_r005_matcher.py` 通过：一个共同候选及一个仅首 GT
  候选时，全局 matcher 保留两对，而 GT 顺序占用仅保留一对。
- 从同一 pkl 输入重新构造候选、总体 key 与全部逐行量的独立实现覆盖 16 个 split×detector×
  condition cell：总 key 对称差为 0，逐行量最大绝对差为 0。

### 修正主损失与非坍塌

下表是 clean 固定总体、逐对象分解后图内等权再图间等权的 `DeltaY`。括号为
`objects / retained / images`；每个 test 单元均满足至少 70% 保留、100 对象和 50 图像。

| detector | blur 1.50 | blur 1.25 | downsample 2.00 | downsample 1.75 |
| --- | --- | --- | --- | --- |
| Oriented R-CNN R50 | 0.017158 (1196/1167/434) | 0.013515 (1196/1173/434) | 0.004848 (1196/1189/434) | 0.003343 (1196/1191/434) |
| Rotated RTMDet-M | 0.002654 (1210/1206/437) | 0.000931 (1210/1209/437) | 0.000208 (1210/1210/437) | 0.000328 (1210/1210/437) |

八个点估计都不大于 0.02；若操纵有效，它们会使主损失合取门失败。但 r005 的裁决顺序先判定
操纵有效性，故这些数字在本轮只是不足以支持 COI 的描述性证据，不能作为正式 KILL 的依据。

### 真实 G/P/N 与 Holm-32

真实 HRSC 原图上先计算 G、固定 clean-P 与六个 clean-N 臂的 `J_eff/M15`，复用 clean noise
scale、共同有效支持、trainval image-cluster 均值/SD 与 epsilon；10000 次同步 image-cluster
draws 的种子为 5005。每格给出标准化方向统计量 `theta` 与 Holm-adjusted p；`+` 表示通过
`theta>0` 且 Holm p≤0.05，`-` 表示失败。

| detector / quantity | corruption | clean-low | low-high | clean-high (>0.20) | clean-high-EN |
| --- | --- | --- | --- | --- | --- |
| ORCNN / J_eff | blur | +0.122378 / .003200 + | +0.029263 / .003200 + | -0.048359 / 1.000000 - | -0.156791 / 1.000000 - |
| ORCNN / J_eff | downsample | +0.042572 / .003200 + | +0.005203 / .003200 + | -0.152225 / 1.000000 - | -0.260657 / 1.000000 - |
| ORCNN / M15 | blur | +0.017572 / .003200 + | +0.004017 / .003200 + | -0.178410 / 1.000000 - | -0.233470 / 1.000000 - |
| ORCNN / M15 | downsample | +0.005776 / .003200 + | +0.000425 / .003200 + | -0.193799 / 1.000000 - | -0.248859 / 1.000000 - |
| RTMDet / J_eff | blur | +0.122312 / .003200 + | +0.029243 / .003200 + | -0.048445 / 1.000000 - | -0.160459 / 1.000000 - |
| RTMDet / J_eff | downsample | +0.042558 / .003200 + | +0.005203 / .003200 + | -0.152239 / 1.000000 - | -0.264253 / 1.000000 - |
| RTMDet / M15 | blur | +0.017595 / .003200 + | +0.004027 / .003200 + | -0.178378 / 1.000000 - | -0.237032 / 1.000000 - |
| RTMDet / M15 | downsample | +0.005780 / .003200 + | +0.000422 / .003200 + | -0.193798 / 1.000000 - | -0.252452 / 1.000000 - |

各 test retained/object/image 依次为 ORCNN blur 1167/1196/434、1173/1196/434、
1189/1196/434、1191/1196/434；RTMDet blur 1206/1210/437、1209/1210/437、
1210/1210/437、1210/1210/437，故八项非坍塌检查全过。前三类合取为假，envelope 合取也为假，
非坍塌合取为真。按照 r005 的预注册分支，这不是 specificity KILL，而是试验无效的 inconclusive。

### 可复算证据

- `refs/heads/exec/r005-real-gpn-observables-normal-equation@ce75a64b232779f101b0becb7efe25ac08d3d2bd`
  包含真实逐对象 G/P/N 特征和该 run 的冻结规格。
- `runs/r005/loss_audit.json` 保留完整逐对象 clean/干预配对、`e0/e1`、retained、`Y0/Y1`、
  `C_miss`、`C_ang` 和 `DeltaY`；`runs/r005/independent_loss_audit.json` 与
  `runs/r005/loss_audit_comparison.json` 是独立重算及比较。
- `runs/r005/manipulation_audit.json` 和
  `runs/r005/manipulation_bootstrap_draws.npz` 保留 Holm-32、非坍塌和全部同步 draws。运行产物
  由对应 fabric result ref 保存；本次这些大型文件也被提交到普通 Git，发布违规见下方 B 审计。

### B 独立验收

B 接受唯一 token `INCONCLUSIVE_R004_PROTOCOL_VALIDITY`，不接受 `KILL` 或 `ADMIT`。独立
复算结果如下：

- 16 个 loss cell 的两实现 key 对称差为 0、逐行量最大绝对差为 0；所有
  `DeltaY=C_miss+C_ang` 恒等式和图像等权汇总均以零误差重现。
- 124168 条 G/P/N 特征无重复 key；trainval normalizer 最大差 `3.55e-15`，32 个操纵点估计
  最大差 `8.33e-17`。10000×437 的抽样索引与 seed 5005 的 PCG64 重放逐元素一致。
- 八个 `clean-high>0.20` 裕量全部为负，因此无论 p 值如何都不能通过操纵有效性门。这一事实
  足以确认当前必须是 inconclusive，而非有效科学 KILL。

另有两项不改变 token、但限制证据复用的问题：六个 N 臂应复用 clean-G noise scale，实际
93126 条相关记录中有 71207 条不一致，最大差约 3.82；ORCNN 点估计使用 434 张图，而 bootstrap
以包含 437 张图的共同 registry 为固定分母并对缺失图填零。故 N envelope、ORCNN CI 与 Holm p
不得作为后续正向证据。

本次 `main` 实际跟踪了七个 `runs/r005` 文件，合计约 54.8 MB，与“大型运行产物不进入普通
Git”的项目规则及上一段最后一句不一致。该发布违规不改变上述保守科学裁决，但不得作为未来
继续跟踪大型产物的先例。

## r004 — 历史基线与原验收记录

### 已冻结资产与资格

- HRSC2016 official trainval/test 为 617/453 图像，ID 交集为零。
- Oriented R-CNN R50 与 Rotated RTMDet-M 均使用已索引的 HRSC trainval→test le90
  checkpoint；trainval clean parity 分别为 mAP 0.9083 与 AP07 mAP 0.9087。
- 两个独立合成实现通过常量/径向、单瓣/四重对称、旋转、pi 周期与 blur/downsample
  单调夹具。trainval 无角度资格赛冻结 blur 1.50/1.25 与 downsample 2.00/1.75；所有
  两模型保留率至少 99.4%。

### SERVER 报告的主损失门

official test 固定 clean 总体使用 center、area、无序边长的一对一匹配，未使用 theta、
angle error 或 oriented IoU。逐图等权的完整总体 `DeltaY` 为：

| detector | blur 1.50 | blur 1.25 | downsample 2.00 | downsample 1.75 |
| --- | ---: | ---: | ---: | ---: |
| Oriented R-CNN R50 | 0.017163 | 0.013542 | 0.004849 | 0.003347 |
| Rotated RTMDet-M | 0.002654 | 0.000931 | 0.000208 | 0.000328 |

八个单元均未达到预注册 `DeltaY>0.02` 的点估计要求；最大值为 0.017163。这些数值若在
有效试验中独立复现，足以使主损失合取门失败，后续角度贡献、机制回归和强基线门不能救回。

### B 独立验收失败原因

- trainval 剂量选择使用全候选按代价排序的一对一匹配；test 快速门使用按 GT 输入顺序逐项
  占用预测的匹配。构造反例已证明两者能冻结出不同 clean 总体，违反“同一 matcher”前提。
- 公开实现没有对真实 HRSC test 计算 G/P/N 的 `J_eff/M_15`、操纵 Holm-32 与 nuisance
  envelope，因此没有证明干预有效改变预注册可观测量。按协议，这一前提缺失只能是
  `INCONCLUSIVE_R004`，不能进入科学 KILL。
- 主损失实现只写出八个聚合点估计，没有逐对象固定总体、test 非坍塌计数、10000 次同步
  bootstrap、Holm 结果或第二实现重算。Git 中也没有可供 B 独立读取的 test 预测或 compact
  audit；当前无法从公开证据复现表中数值。

### 证据与重建

SERVER 声称大型 raw predictions、运行配置、冻结剂量和主损失审计均在项目 `runs/r004/`；其 fabric
运行记录为 `r004-select-trainval-common-doses`、`r004-infer-test-oriented-frozen`、
`r004-infer-test-rtmdet-frozen` 与 `r004-primary-loss-audit`。可复算实现为
`src/orientbench/r004/quick_gate.py`；它使用 long-side canonical le90，并将每一对象精确分为
missing 与 retained-angle contribution。r005 必须在不新增推理的前提下修复 matcher、补齐
真实操纵与独立复算，之后才能更新最终裁决。

## r001

### 假设

CMR试图用条件混合可靠性解释或改善旋转框方向风险。

### 代码与配置

完整历史由`doc/ARCHIVE.md`登记的改造父提交及远端`exec/r001`系列ref保存。

### 基线与主要指标

geometry theta中位数为`0.2425237894 rad`（`13.8956°`），超过预注册门`0.05 rad`
（`2.8648°`）。shuffle_class与shuffle_box使用了不受foreign q影响的字段，两项证据无效。

### 结论

geometry门足以关闭CMR；无效shuffle证据不得继续引用。

### 适用范围

结论只约束该CMR定义、冻结数据与指标，不代表所有旋转可靠性方法无效。

### 大型产物

本次改造未删除服务器产物；Git内历史证据由父提交保存。

### 重建方式

使用`doc/ARCHIVE.md`中的历史工作树命令恢复代码和Git内证据；服务器输入与运行产物仍按原样保留。

## r002

### 假设

GR-EQS尝试以风险语义和分数融合改善选择风险及检测性能。

### 代码与配置

正式执行证据固定在`exec/r002-evidence-closeout-repair-final@8236d149b02268135485f1076bb6c0fdd3c74a55`。

### 基线与主要指标

正式结果为`FAILED_ACCEPTANCE / INCONCLUSIVE_R002_EVIDENCE_UNAVAILABLE`。FAIR1M-D原冻结
cohort为15199行、1231 clusters，修正后只有15148行、1222 clusters。修正G1中三个数据集
risk-noninferiority均未通过，18组均选择`lambda=0`，fusion与raw排序及AP相同。

### 结论

GR-EQS方向负向冻结，但由于冻结universe没有恢复，不能写成正式验收的KILL。

### 适用范围

结论只约束该风险定义、融合规则和冻结cohort；不能外推为所有不确定性、校准或风险控制无效。

### 大型产物

本次改造未删除服务器run回执、数据或权重；Git内compact evidence仍可从执行ref读取。

### 重建方式

从执行ref建立detached worktree复核。历史FAIR1M-D缺失的51行不能伪造，重放失败必须如实保留。

## r003

### 假设

AIRO/COI候选拟检验图像条件方向可辨识性。

### 代码与配置

旧树只有READY计划和expected-results声明，没有已提交的`experiments/r003_airo_stagea`实现。

### 基线与主要指标

没有执行、没有RESULT、没有科学指标。

### 结论

`NOT_RUN`。不得报告为成功、失败、KILL或INCONCLUSIVE实验结果。

### 适用范围

仅说明该计划未执行；候选科学价值仍需未来重新讨论。

### 大型产物

无r003运行产物。

### 重建方式

不从旧协调树恢复执行。若未来继续，B/C必须在新协议中重新形成科学指令。

## r006

### 协议与执行

在 HRSC2016 official held-out test 上，按冻结的 r004 Oriented R-CNN R50 与
Rotated RTMDet-M checkpoint、score/NMS 和输入语义完成 clean-assigned output-lattice
双轴整数平移扫描。ORCNN 的 eligible strides 为 4、8，RTMDet 的为 8、16；列表由
trainval clean census 在 test 前冻结。扫描、canvas test parity、主统计和第二实现的 execution
refs 分别为 `exec/r006-test-orcnn-biaxial-sweep@60302f3464dd04ccb6333693ad089b5859172b95`、
`exec/r006-test-rtmdet-biaxial-sweep@ff3736eb66eccb9cfe0b9cb45fc089feebeda099`、
`exec/r006-test-canvas-parity-retry1@10a64aae0fd7a1e9c05e89d5d035b6f90448c9d5`、
`exec/r006-test-primary-analysis-retry1@3a1871e0b19b5888d29a72b8bf2c2378527e149b` 和
`exec/r006-test-independent-verify-retry1@102767f1cf5fac42b92095cd8200ee2563dc7baf`。

### 执行有效性

两个模型均通过 phase-0 canvas parity：保留率约 99.92%，ORCNN/RTMDet 的 image-equal
mean le90 绝对差为 0.0243°/0.0578°，AP75 绝对差为 0.001952/0.000664，均在预注册界内。
三次 phase-0 确定性与 matcher/source-level 逐行独立复算通过；第二实现不导入主统计或 r005
matcher，实现差为零，并通过 pi 轴向等价和非零角扰动 mutation tests。

但正式 test 中 ORCNN stride 8 的 y 轴冻结总体为 252 对象；shift 10、12、13、14 的保留率分别为
89.68%、89.29%、88.49%、89.29%，低于每 shift 90% 的预注册下限。该 stratum 的 test 不能解释
为 clean-assigned active path，不能以其余 shift、stride、模型或统计结果补救。

### 结论

`INCONCLUSIVE_R006_EXECUTION_VALIDITY`。这不是 KILL，也不支持 ADMIT；不得改变边距、pad、
stride、阈值或重开同一 official test 来修复。主统计的 10,000 次同步 image-cluster draws、完整
逐条件 source-level 预测和独立复算均保留于上述 execution refs；普通 Git 仅保留可复算源码、配置
和本结论。

## r007

### 范围与执行

这是只读 SAR acquisition-axis 资产资格审计：未训练、推理、下载、解压、复制数据，也未读取模型
输出、OBB--axis 相对角或任何联合表。审计只枚举主机固定数据根中预先列出的 RSDD-SAR 与
SAR-AIRcraft 候选目录；未将其他光学数据误识别为 SAR。

### 资产与双实现结果

两个候选在 `/home/rspip/cqc/data/dataset` 下均无本地根目录，因而没有可核验的数据版本、许可、
原始产品 metadata、source-product→scene→chip→object lineage、scene、eligible object 或
ground-range axis strata。主实现与独立实现对两个候选的名称、平台、根不存在状态及 reason code
`LOCAL_SAR_ASSET_ABSENT` 完全一致。RP1 180° 恒等、10° 固定半开 bin、range/azimuth 正交与非零
mutation fixtures 均通过；compact 输出按信息墙分离 axis/OBB 边际，且没有共同键的逐行 axis 与
OBB angle。

### 唯一裁决

`ASSET_UNAVAILABLE_R007`。这是资产不可用，不是科学 PASS/KILL，也不是对 acquisition-axis
机制的反证；项目回到 `NO_ACTIVE_TASK`。不得下载、补造或由普通 north-up 栅格、文件名、图像边缘
或目标方向猜测 acquisition axis，且本结果不自动授权 r008。

## r008

### 范围与执行

本轮只读核验 RarePlanes 真实数据、来源分量划分前提、五个 detector family 与两个下游分类器的
既有资产；没有训练、推理、模型 import/forward、属性误差、方向误差、风险排序或论文修改。

### 资产与 readiness

在固定主机数据根中未发现预注册的 `RarePlanes`、`RarePlanes_real`、`RarePlanes_Public` 或
`rareplanes` 数据根。因此没有可解析的 253 条真实 WorldView-3 records、112 locations、约 14700
objects、full GeoJSON、许可、image/annotation 一致性或 `loc_id↔CAT/source-product` component
lineage；固定 25 test / 25 calibration / 至少 50 training component split 和四属性支持表均不能合法
生成。不得以名称相近数据、synthetic 部分或默认同地点 test split 替代。

现有树仅可识别 ARS-DETR、ai4rs rotated-RTDETR 与若干 mmrotate 相关实现根；它们均缺
RarePlanes 单类接口、初始化权重与 OBB 语义闭环。O2-RTDETR、FRED、ResNet-50 与 ViT-B/16 的
本轮所需实现/权重亦未核验。几何 fixture（RP1、w/h+90°、顶点等价和非零 mutation）通过；第二
实现独立重查数据根及五 family 顺序，结果一致。

### 唯一裁决

`ASSET_UNAVAILABLE_R008`。这是顶刊验证组合的资产不足，不是 H1/H2 的科学 PASS/KILL；不得
下载、拼接、伪造资产或自动启动 r009。项目回到 `NO_ACTIVE_TASK`。

## r009

### 修正审计

按 r009 的完整有界合同，主实现对固定 dataset 根进行了大小写不敏感、符号链接解析、最大五层的
目录别名与官方内容签名枚举；覆盖 `RarePlanes-Public`、`RarePlanes_Public`、`RarePlanes`、
`RarePlanes_real`、`rareplanes`，并检索 full annotations 与 metadata 官方文件签名。没有发现候选
目录或内容签名，且没有搜索异常。独立实现不导入主候选集合，重新枚举后 candidate set 完全一致。

### 模型与权重 readiness

审计实际读取 third-party 内部项目树和 `pth_data/readme.md`：Oriented R-CNN、Rotated RTMDet 与
ARS-DETR 存在相关实现；O2-RTDETR/FRED 没有可识别的已登记内部项目或权重。所有 family 仍缺
RarePlanes 接口、确定的 OBB 语义和可核验的初始化权重闭环；现有 classifier 实现亦缺针对四固定
属性输出的权重/适配闭环。这些均如实记为缺失或 `ADAPTATION_REQUIRED`，没有以目录名或常量冒充。

### 唯一裁决

`ASSET_UNAVAILABLE_R009`。RarePlanes real 数据资产本身不存在，故 r008 的 component/split/属性
支持门不能执行；此结论不是 H1/H2 科学结果，也不授权下载、训练、推理或 r010。项目回到
`NO_ACTIVE_TASK`。

### B 最终验收

B 接受 `ASSET_UNAVAILABLE_R009`。主审计已修复 r008 的四别名常量问题，实际覆盖
`RarePlanes-Public` 等五种目录别名和官方内容签名；搜索无异常。独立实现重新枚举后给出
`passed=true`、`candidate_set_equal=true`，与主实现共同确认当前主机固定数据资产中没有
RarePlanes real。该结论只证明本地资产缺失，不证明官方公开数据不可取得，也不是 H1/H2 的
科学负结果。

## r010

### 官方 real 资产与完整性

仅从官方 `s3://rareplanes-public/` 取得 CC BY-SA 4.0 许可、full GeoJSON、metadata CSV、两份
tiled annotations，以及 test/train 两份 PS-RGB COG 影像包；没有取得或读取 synthetic。最终逐对象
字节校验通过，COG archive 与 253 条 metadata image_id 的一对一回链通过。首次 runner 执行及时
识别出两份 tiled annotations 的不完整传输，未将其作为有效证据；按官方 Content-Length 重取后，
以相同 CPU-only 代码重新执行主审计和不导入主实现的独立复核，二者结论一致。

### 固定 split 与属性门

full GeoJSON census 为 14,707 个对象、253 条唯一 WorldView-3 image records。按固定
`loc_id↔CAT/source-product` 连通图和 PCG64(1010) 置换，实际只有 83 个连通 component；地理
footprint 合并只能进一步减少 component，因而不可能满足预注册的至少 100 个 component 门。虽然
三个固定 co-primary 的 train/calibration/test 支持均超过 100/20/20，component 门已独立失败。

### 模型资产与唯一裁决

已有合法来源可核验 Oriented R-CNN、Rotated RTMDet、ARS-DETR、O2-RTDETR、ResNet-50 和
ViT-B/16 的实现/通用初始化；FRED 的官方实现和合法初始化未公开可得，未以任何近似或旋转增强
替代。主、独立复核一致输出 `ASSET_UNAVAILABLE_R010`：这是预注册 component 数不足且 FRED
资产不足的组合资产结论，不是 H1/H2 科学 KILL 或 PASS。不得启动 B/C r011、训练、推理或以近似
数据集/模型补位；顶刊 RarePlanes 扩展到此停止，项目回到 JSTARS 收敛。
