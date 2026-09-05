# 全项目科学结果总账

本文件同时覆盖两套同号轮次：旧科学序列 r001--r052 截止于
`5e7c3ea`，当前同号序列自 `7e67f9f` 开始；简化前完整树可从归档父提交
`09381f7a360e5ad730e77157fb427401555620f5` 读取，但该快照本身已包含当前序列到 r003 的内容。
裸 `rNNN` 不能跨两套序列直接等同；下文以“归档主线/当前主线”明确区分。

## 全项目总裁决（2026-09-05）

- 本次全项目创新重评及官方数据只读复算见 `doc/INNOVATION_REASSESSMENT_20260904.md`。
  最新r014的逐概率完整复算与剩余验收见`doc/R014_B_ACCEPTANCE_20260905.md`。
  修正数值已独立复现；但真实render/反例测试与原输入/模型证据未闭合，因此保留
  `INCONCLUSIVE_R013_H1A`，优先为剩余实现/证据有效性，不能接受机器valid=true或仅POWER。
  当前唯一任务仍是r014剩余验收，不再模型前向，不启动新实验。
- 已建立的主结果是“构造性方向扰动可被 AP50 完全掩盖，却显著损伤高 IoU 矩形评价；高长宽比
  矩形的解析角度容差更紧”，并有六个完整检测单元、八个几何风险单元、600 个人工目标及
  图像级有限样本分析支撑。它尚不是独立现实下游影响。
- 尚未建立的结果是“方向可靠性会改善独立遥感决策，而且其风险可在无测试 GT 时被识别并控制”。
  r045 的负结果仅针对由 GT_AR 与角误差合成的几何代理损失，不是实测下游应用；此后所有
  selector/head/融合路线均失败、降级或未裁决。
- 独立比较现有文献后，当前有领域测量/审计论文的核心素材，JSTARS 是合理候选定位；但撤回
  “strong JSTARS 已成立”。尚无足够新的机制、方法或独立应用价值说服 B/C 达到 TGRS/JPRS。
  RarePlanes H1a 即使修复并 PASS，也不自动越过已有飞机方向规范化与旋转等变工作的创新边界。
- r010 的 `83 components / ASSET_UNAVAILABLE_R010` 已被独立审计推翻：26 行官方 CSV
  `cat_id` 被科学计数法破坏，规范恢复后为 102 个 footprint 合并前 component。由于正式地理
  footprint 合并和模型 build/load 尚未闭环，当前状态改为
  `INCONCLUSIVE_R010_ASSET_AUDIT_INVALID`，不是 READY，也不是科学 KILL。
- r011 的机器 token `ASSET_UNAVAILABLE_R011` 也未通过 B 验收：发布产物与所登记执行的源码、
  时间和产物位置不可能同时成立，且 split 被未预注册地从 lexical key 改为 numeric tuple；
  lineage、支持门、footprint 双实现和模型严格加载均未闭合。正式状态为
  `INCONCLUSIVE_R011_EVIDENCE_REPAIR`，H1/H2 仍为零条科学结果。

## 可保留的稳定测量事实

### 六单元受控方向扰动

后期权威 full-validation 表为归档
`top_journal_v3_reaudit_055/reports/table1_fullval_final_065.csv`。在只改变方向、保持其他检测输出
不变的构造性扰动中，六单元 AP50 均严格不变，而 AP75 大幅下降：

| 数据/单元 | AP50 原始→扰动 | AP75 原始→扰动 | 平均角误差 原始→扰动 |
| --- | ---: | ---: | ---: |
| DIOR-R / 22 | 0.5368→0.5368 | 0.3503→0.0384 | 8.947°→39.189° |
| DIOR-R / 3 | 0.6448→0.6448 | 0.4275→0.0484 | 8.665°→40.041° |
| DIOR-R / 61 | 0.6462→0.6462 | 0.4515→0.0532 | 9.087°→40.541° |
| FAIR1M / 24 | 0.3462→0.3462 | 0.2422→0.0665 | 4.631°→36.516° |
| SODA-A / 23 | 0.5991→0.5991 | 0.2735→0.0448 | 5.230°→34.416° |
| SODA-A / 4 | 0.7295→0.7295 | 0.3805→0.0278 | 5.148°→35.893° |

因此权威范围是 AP75 下降 `0.1757--0.3983`、平均角误差增加 `29.186--31.885°`。旧 r044
稿件写入的 AP50 和 AP75 下降 `0.1731--0.6166` 已被该 full-validation 表取代，不得继续引用。

本次生成代码复核收紧解释：构造扰动读取 matched GT，只处理原 TP@0.5，以 1° 步长搜索仍满足
IoU>.5 的最大角。因此 AP50 不变是构造约束，不能解释为自然方向错误普遍被掩盖。

非 oracle 固定剂量 S 臂补充了更强边界：在预测 AR≥2.1 的输出框上分别施加 +15°/-15°，
完整计算 AP 再取平均；六单元 AP50 降 `2.88--9.51pp`，AP75 降 `3.74--17.20pp`。
DIOR/22 的 AP50 为 53.68→50.43、AP75 为35.03→22.81；SODA/4 为72.95→63.44、
38.05→20.85。正确主张是高 IoU 评价更敏感，不是 AP50 普遍不敏感。该表来自归档
`top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/fixed_dose_tracks_r011.csv`，
其评价器/基线版本不能与前表逐行混拼。

### 几何、风险与人工锚点

- 同心同尺度矩形在 `AR=2.1` 时的 `IoU=0.75` 方向容差为 `15.3297°`。这是解析几何阈值，
  不是观测预测框的真实 IoU 事件。
- 八单元几何归一 severe-risk 的 eligible 数依次为
  `49,502 / 54,297 / 53,671 / 31,801 / 197,529 / 235,428 / 33,029 / 34,383`，对应率为
  `0.0081 / 0.0082 / 0.0167 / 0.0052 / 0.0036 / 0.0053 / 0.0019 / 0.0029`。该事件仍由同一
  矩形 IoU 几何定义，不能当作独立现实后果。
- 图像级 LTT 在 `alpha=0.03` 时，A--F 六单元均选择 `coverage=1.0`；校准 HB UCB 为
  `0.0153817 / 0.0161449 / 0.0258754 / 0.00536176 / 0.00307779 / 0.00300844`。它证明冻结
  calibration 获得 HB 证书且 held-out 经验风险相容，但没有形成非平凡拒识决策；有限样本保证仍
  依赖 exchangeability，也不证明部署域迁移。
  该风险只统计 IoU≥.5 已匹配且 GT_AR≥2.1 的对象，空 eligible/retained 图记零，漏检和 FP
  不进入该风险；held-out 图中含 eligible 对象比例为59.2/61.7/62.5/57.0/35.4/35.8%。因此
  它不是完整检测系统的安全证书。
- 人工双标共 600 个目标、450 个双人数值对；轴向分歧均值 `2.3112°`，图像簇 95% CI
  `[1.9970°, 2.7854°]`，`P(>5°)=0.0800`、95% CI `[0.055679,0.105621]`，
  `P(>10°)=0.008889`、95% CI `[0.002208,0.017897]`；`AR>=2.1` 时 `n=308`、均值
  `2.2823°`。这是条件于双方数值可标的标注者分歧，不是 official GT error 或全600目标噪声
  地板；103 个目标双方均为 ambiguous，不能把它们隐去后声称普遍2.31°精度。
- DOTA 的 ORCNN/RTMDet `POST_OUTCOME_AUDITED_EXTERNAL_REPLICATION` 得到 AP50
  `0.706069/0.716127`、AP75 `0.451742/0.486848`。ORCNN 的 AUGRC/Risk@70 DoD 为
  `0.0126695 [0.0073611,0.0186728]` / `0.0240725 [0.0130121,0.0367018]`，均不满足 witness；
  RTMDet 为 `0.0159727 [0.0092158,0.0236151]` / `0.0339429 [0.0191244,0.0513364]`，均满足；
  equal-unit 为 `0.0143211 [0.0083368,0.0210285]` / `0.0290077 [0.0164741,0.0436297]`，均满足。
  这不是前瞻确认。r034 只终结由这些量导出的 selector/剩余图像机制解释，不推翻 AP、matched
  census 或上述 post-outcome descriptive DoD 数值本身。

### 归档 r011 评价器与机制边界

归档 r011 完成 42/42 evaluator golden checks；官方、clean-room、authority 三实现的六单元
AP50/AP75 均在 `0.002` 内一致。144 个 P/D/S grid 中，`D15`、`S15` 均获 6/6 支持，AP75
单调性 6/6、AR survival 6/6；但 P3 仅 4/11 eligible folds，leave-dataset 为 0/6，联合结论为
`TGRS_NOT_REACHED_R011`。它稳固了测量实现和有限机制边界，没有产生可迁移方法。

归档固定尺寸非线性诊断在 15 bins 中 11 个显著，支持单元 A/B/C/E；但拟合目标直接使用
target-domain GT angle error，只能作为 diagnostic upper bound，不能充当部署风险分数。

## 归档主线：方法与机制裁决

| 路线 | 可复核结果 | 科学裁决与边界 |
| --- | --- | --- |
| PSC 候选 B3/B4 | 本域 27/58 候选同时胜 phase modulation 与 score；外部 RotatedFCOS-PSCD 为 0/24 | `FAIL_CANDIDATE_GATE / STOP_B6`；局部解码响应可描述，repair 不得复活 |
| 旧 score-cause r004--r007 | score-ranking limit 0/90；33 项 structural、57 项 oracle/data/grid；split-FST 仅 14 qualified rows、只覆盖 A/B/C 与 DIOR；r007 的 exact-integer、boundary、taint、split-FST-sim 四项关键 validity 为 false，lineage 为 true | r004 `FAIL_SCORE_LIMIT_DOMINANT`；r005 attribution inconclusive；r006 `FAIL_NO_BROAD_TARGET_FREE_DEVELOPMENT`；r007 invalid |
| r034 循环性审计 | 616,184 行；DIOR/DOTA/FAIR/SODA 为 5900/458/2142/576 clusters；12 个 primary、0 witness | `K1=true, K2=true, SURVIVAL=false`；旧 selector-signature 主张终局降级 |
| r023 mixed gate | 405 hypotheses、5 个 unit witness、2 个 dataset witness、无 passing signature；A/B 10,000 replicates 最大差 0 | `INCONCLUSIVE_MIXED`，不能由零复算误差升级为方法成功 |
| r036/r037 Q-SetOD | r036 被 C 标为 `CONTESTED`；r037 `G_EVIDENCE=4/8`、`G_SET=0/8`，且 A/B 仅 4 行标签差、validator 与 A 相似度 `0.930769` | 正式 protocol drift；只能描述部分标量信号，集合运输未成立 |
| r042 OER | 八个 `Delta_AUGRC` 全负：`-0.0004563,-0.0004223,-0.0003500,-0.0005216,-0.0002698,-0.0001390,-0.0001190,-0.0000190` | `REJECT_OER_METHOD` |
| r043 SAUR | DIOR `0.5370→0.3340`，SODA `0.5990→0.4320` | 拒绝该冻结实现；公式 gate 偏差禁止外推到所有 SAUR 类方法 |
| r045 前瞻几何代理迁移 | HRSC 98 图；连续风险收益 `-0.00195195`，95% CI `[-0.00759691,0.00355364]`；severe 收益 0 | 历史 token 为 `APPLICATION_SHIFT_FAIL`，但实际 loss=`min(1,GT_AR/2*sin(angle_error))`；仅反对该冻结策略的几何代理跨域收益，不是实测应用反证 |
| r046/r047 AHC | 开发 accuracy `0.84288` vs whole-crop `0.87431`；正确 T_cal UCB `0.15661/0.18904/0.17297` | 协议漂移，`NOT_ADJUDICATED`；不得包装成正式方法结果 |
| r048 P2C | base accuracy/角误差/AUGRC `0.506470/87.741°/0.423795`，whole-crop `0.885397/21.336°/0.024484` | `REJECT_P2C_LIFT_DEVELOPMENT` |
| r049 CORA-v1 | AP50/AP75 `0.491/0.248` vs control `0.496/0.275`；AUGRC/R70 增益仅 `0.000404/0.000223` | `REJECT_EXECUTED_CORA_V1`，仅约束 v1 |
| r049-rev2 PEF | PEF vs control：mAP `0.4137/0.4171`、AP75 `0.2820/0.2900`、角 MAE `1.9419°/1.8581°` | `REJECT_PEF_METHOD`；native q 不能精确穿过 NMS，不引用其风险数 |
| 旧 r051/r052 CMR | r051 实现未消费其边缘似然；旧 r052 geometry equivariance median `0.531568` | r051 `NOT_ADJUDICATED_IMPLEMENTATION`；当前 r001 后审发现旧 shuffle 字段不受 q，故两项 shuffle 作废，但旧/当前 geometry 门分别仍足以关闭该实现 |

归档 r003（A6R 资产缺失）、r012（来源/zero-pred 缺口）、r020/r021/r022/r024/r031（技术或治理
早停）、r032（仅资产）、r038/r050（运行前撤回）、r040/r041（资产/推理修复）均没有可写成
科学 PASS/KILL 的结果。归档 r008--r010、r013、r016--r018、r033、r035、r039 只涉及 quarantine、
证据闭环、机械回执、稿件/提案或未激活计划；除本总账另行列出的复算事实外，不构成新的科学
PASS/KILL。

r014 的表面正结果在 r015 法证后永久降为 `FAIL_PROTOCOL_R014`；同步重算的 DIOR、FAIR、SODA
探索量分别为 `0.1733 [0.1458,0.2020]`、`0.2436 [0.2048,0.2848]`、
`0.1645 [0.1062,0.2300]`，HRSC 为 `0.060167 [-0.014323,0.143800]`。r016 的 replicate 最大差
`9.714e-17` 只证明数值复算，不恢复 confirmatory 身份。

r019 的描述性 aggregate linear-v-EQS 为 `0.0671856 [0.0279736,0.1117938]`，standalone guard
却为 `-0.025558 [-0.037808,-0.014127]`；后续权威状态是
`INVALIDATED_R019_PROTOCOL_DRIFT_FAIL_IMPLEMENTATION_FAIL_TIMELOCK`。旧 r030 supplement 仍写
`FAIL_EXTERNAL_DOTA_EQS_RC_R019`，属于未修正的历史稿件 claim，不得沿用。

归档 r044 稿共 8,150 词、57/57 claim checker，只证明旧稿对旧输入自洽；venue gate 为 G1--G3
通过、G4 失败，两名内部红队均给 novelty `3/5`、其余维度 `4/5`，正式
`NOT_JPRS_READY`。其受控扰动表又已被后期 full-validation 表替代，不能把“协作者审阅冻结”解释为
顶刊 ready。

## 当前极简主线：总览

- r001：CMR geometry theta 中位 `0.242523789 rad=13.8956°`，超过 `0.05 rad=2.8648°`；
  该定义关闭，两个 shuffle 证据无效。
- r002：三个数据集 risk non-inferiority 未全过，18/18 选择 `lambda=0`，融合与 raw 恒等；
  FAIR1M-D 从 `15199/1231` 漂到 `15148/1222`，故只作负向冻结，不签正式 KILL。
- r003：未执行。
- r004/r005：八个 `DeltaY` 最大 `0.017158<0.02`，但真实操纵有效性、N scale 与 bootstrap
  分母存在决定性问题；`INCONCLUSIVE_R004_PROTOCOL_VALIDITY`。
- r006：ORCNN stride-8 y 轴若干 shift 保留率 `88.49%--89.68%<90%`；
  `INCONCLUSIVE_R006_EXECUTION_VALIDITY`。
- r007：SAR 固定资产不存在；`ASSET_UNAVAILABLE_R007`，只说明资产不可用，SAR 已暂停。
- r008/r009：RarePlanes 本地资产资格/修正审计，不是科学实验；r009 仅证明当时本地无资产。
- r010：官方 real 资产已取得，但资产审计实现无效，详见本文件末尾更正。

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

### 仍成立的官方资产事实

官方 real 资产已取得，未混入 synthetic。独立读取官方 HTTPS 原文件复现：metadata CSV 为
48,458 bytes、253 行、253 个唯一 `image_id`、112 个 `loc_id`；full GeoJSON 为 12,529,647
bytes、14,707 个 plane Polygon。许可、官方对象字节和上述 census 仍成立；这些事实不等于 split、
footprint lineage 或模型 readiness 已通过。

### 83-component 结论的撤销

旧审计直接使用 CSV 的 raw `cat_id`。其中 26 行在官方 CSV 原字节中呈现为科学计数法字符串：
`1.04001E+15` 21 行、`1.04E+12` 4 行、`1.04E+11` 1 行，导致无关地点被伪合并为一个
25-location 巨分量。对每行保留 raw 值，并仅在 `image_id` 后缀为 16 位十六进制、与 full
GeoJSON CAT 集合及影像键唯一一致时规范恢复，可得 227 个 CAT，恰与 GeoJSON 的 227 个 CAT
完全相等；修正后的 footprint 合并前图为 102 个 component（97 个单点、4 个双点、1 个七点），
不是 83。

按同一规范 key、同一 PCG64(1010) 确定性重算的候选 split 为：test `25 components / 26 locs /
1,919 objects`，calibration `25 / 32 / 7,418`，train `52 / 54 / 5,370`。三个 co-primary 的
六类对象支持均超过冻结的 train/calibration/test `100/20/20` 门。旧 83-component split 与其
全部对象比例、支持表整体失效；仅 40/112 个地点仍处于同一分区，不能局部修补或沿用旧 test。
由于尚未训练、推理或读取任何 H1/H2 性能，这一确定性源字段更正尚未消费 single-use test。

### 尚未闭合的执行有效性

- r010 声称执行了 geographic-footprint merge，代码实际只连接 loc、CAT 和 image 键，没有读取
  253 个 COG 的 CRS、affine、宽高并计算地表 footprint 相交。102 只比 100 多 2，仍不能据此
  宣布数据门通过。
- tiled annotations 只做了大小检查，没有完成 full GeoJSON、tile、COG、对象的逐键唯一回链；
  long-side RP1、投影和 w/h+90° 的真实几何 fixture 也未实现。
- 模型清单以目录/许可/通用权重存在代替真实 config build 与 state-dict 兼容性；同一 ResNet-50
  权重被用于不匹配的 RTMDet/CSPNeXt、O2/R50vd 等架构，ViT 实现与权重来源也未闭合。FRED
  availability 是硬编码，所谓独立验证又读取主实现生成的同一清单，因此不能把“其余六项 READY、
  FRED 独立确认缺失”当作已验证事实。
- repair artifacts 没有对应的独立运行记录；主、独立代码还把三个 split 的对象支持门共同误译为
  100，而签署协议是 `100/20/20`。本次对象数恰均超过 100，不改变上述源字段诊断，但说明双实现
  没有真正独立翻译合同。

### B 更正后的唯一裁决

`INCONCLUSIVE_R010_ASSET_AUDIT_INVALID`。旧 `ASSET_UNAVAILABLE_R010` 及“83<100 已关闭
RarePlanes”的理由正式撤销，但当前也绝不升级为 READY。唯一允许的 r011 是 correction/design-only：
双实现闭合 CAT、真实 COG footprint、lineage、component-equal 统计合同和模型 build/load；不得
训练、推理、读取 H1/H2、修改论文或自动进入最终验证。

## r011

以下前两节只记录 SERVER 机器报告，未获 B 验收；正式科学状态以第三节为准。

### SERVER 机器报告的数据与几何证据（未验收）

SERVER 报告双实现独立解析 253 条 metadata 行，并把 26 条科学计数法形式的 raw `cat_id` 仅在 `image_id`
16 位十六进制后缀、full GeoJSON CAT 集和唯一 COG 键三方一致时恢复。两实现均得到 227 CAT。
读取全部 253 个 COG 的 header（未读像素）：CRS 均为 EPSG:4326。以 affine、宽高导出的实际
影像 footprint 按严格正面积相交建图，边数为 0，最终为 102 个 component（97 个单点、4 个双点、
1 个七点）；组件哈希为 `34fda94b2f05c5a5846b96de88b84a305ba262bf5e4ad46c96d081a31c17e3f5`。
旧 83-component 结论因此只是历史无效证据，不能再引用。

PCG64(1010) component split 与 six-class object/component 支持门均通过；test/calibration/train
为 25/25/52 个 component。完整 GeoJSON、COG 与 tiled 标注 lineage 已逐键闭合：test 为 2,710
tiles/6,812 annotations，train 为 5,815/18,393，全部 source 与 annotation signature 可回链。
RP1 的 w/h+90°、边界相切、非零 footprint、CAT 表示及 calibration 19/20 等 mutation fixture 均通过。
这些仅是设计/资产证据，未训练、未推理、未读取 H1/H2 outcome。

### SERVER 机器报告的模型 readiness 与裁决（未验收）

机器报告称两份独立运行记录对 build/load 结论一致。Oriented R-CNN、Rotated RTMDet、ResNet-50、ViT-B/16
均完成实际 config build 和严格 state-dict load。ARS-DETR 因现有环境的 MMCV 1.7.2 与其要求
`<=1.6.0` 不兼容而无法初始化；O2-RTDETR 因 MMCV 2.3.4 与其 bundled mmrotate 1.0.0rc1 的
`<=2.2.0` 要求不兼容；FRED 没有本地主机可用的官方/作者实现及合法初始化，未以 surrogate 替代。
因此 `four_family_amendment_feasible=false`，唯一裁决是 `ASSET_UNAVAILABLE_R011`。

这不是科学 PASS/KILL，也不授权训练、GPU 推理、H1/H2、HRSC、RSAR 或论文修改；r012 也未启动。
全部实际代码、run spec、双实现 raw audit、模型记录和最终汇总已随 r011 result ref 发布。

### B 独立复核与正式科学状态

B 不接受机器的 `ASSET_UNAVAILABLE_R011`，正式状态改为
`INCONCLUSIVE_R011_EVIDENCE_REPAIR`。可保留的描述性事实只有：官方输入表面复现
253 metadata rows、26 个科学计数法 raw CAT、227 个 canonical CAT、253 个 COG，以及两实现均报告
102 个基础 component 和 0 条 footprint edge；这些尚不足以证明最终 data/model readiness。

决定性原因如下：

- `RUN.json` 绑定修复前 `573d439`，并在 RP1 修复提交产生前结束；它声明输出在 `artifacts`，发布
  证据却位于 `repair_artifacts`，且内容反映结束后才提交的修复逻辑。没有与发布产物对应的新运行
  回执或输入/输出哈希，因此 provenance 自相矛盾。
- r010 已公开的规范 key 是字符串 `loc:...`；r011 改为数值 tuple 排序后再用同一 PCG64(1010)，
  未预注册地重随机化了 single-use split。原 lexical split 的 test/calibration/train 为
  `25/25/52 components`、`1,919/7,418/5,370 objects`；r011 numeric split 变成
  `3,766/6,747/4,194 objects`，三个分区仅分别重合 5/10/28 个 component。r011 numeric test 不得沿用。
- support 数值本身在 numeric split 上通过，但 support 门没有进入 finalizer；所谓 19/20 mutation
  只是恒真布尔表达式。指令要求的逐 split×class 最大 component 占比和 Kish effective count 未输出；
  numeric calibration 最大 component 占 `55.343%`，overall Kish 仅约 `2.928`。
- tiled lineage 只检查粗属性 signature 是否存在于全局集合，没有建立
  `annotation→tile→source COG→full object` 的唯一、多重性和完备回链。粗签名重算显示 test 的
  6,812 annotations 只有 3,807 个 unique signatures，train 的 18,393 只有 10,899 个；full flags
  为 3,807+10,900，至少一个 train full object 的差异未解释。
- 两个 footprint 实现共享同一简化 CRS 判断、经纬度面积近似和阈值，没有公布 footprint key、
  最小间距裕量或真正独立 geospatial 路径；独立实现也没有 projection/pixel-frame/RP1 fixtures。
- ORCNN/RTMDet 用 `strict=False` 加载后直接写空 missing/unexpected keys；FRED 缺失仍由常量产生；
  ARS-DETR/O2-RTDETR 报的是所选运行环境版本冲突，而不是科学资产不存在。静态 schema dict 也没有
  实例化 RarePlanes adapter。故模型来源、许可、版本、兼容 load 与第二实现均未闭合。

r011 没有读取 H1/H2 outcome，故以上问题没有消耗科学 test；但任何后续任务必须恢复事前已有的
lexical split，并先 outcome-blind 修正上述 G0 证据，不能把 r011 numeric test 当作新冻结 test。

## r012

### G0

G0 的主、独立实现对同一官方 RarePlanes 元数据、full GeoJSON、COG header 与 tiled lineage
给出一致结果：253 metadata/COG rows、26 个保留 raw CAT 的科学计数法损坏值、227 个 canonical
CAT、14,707 个 full objects，及 lexical-PCG64(1010) 的 25/25/52 component split。两实现对
共同 eligible census、支持门和 strict core state-dict load 均通过；G0 结果为
`G0_PASS_H1A_TRAINING_AUTHORIZED`。G0 未打开 test 像素、未做模型前向或性能计算。

### H1a

正式 recipe、冻结训练 canvas 程序及其 source commit 已在拟合前提交。官方训练 COG 仅用于
4,065 个 eligible train object 的一次性 canvas 预提取；canvas manifest SHA-256 为
`1586f6864d21e3fda49565b4f9dded15ebe770696e4fd992170cf41ecf10d99a`。ResNet-50 seeds
1201、1202 各完成 final epoch checkpoint，SHA-256 分别为
`85e5c3f3afb2192c6e9d9bfe77f0a5f065f75111e3ed7a80d2f03ec34a409401` 与
`85ce91648e56f26657714625548f9b9a1011b9c08208a026e944eed4064eeee1`。

随后并发调度的 ResNet-50/1203、ViT-B/16/1201、ViT-B/16/1202 均在产生 final-epoch
checkpoint 前被外部终止；三个重定向日志为空，且系统日志未给出 Python exception 或 OOM 证据。
ViT-B/16/1203 未启动。由于冻结合同规定训练失败即为执行无效，不能将两个已完成模型与任何
部分运行混合，也不得重试来凑满“恰六次”拟合。

因此唯一裁决为 `INCONCLUSIVE_R012_H1A`，reason=`TRAINING_FAILURE`。calibration 未打开，
未构造 calibration/test 性能结果，未执行 bootstrap；test 像素、test crop、test model forward
和 test performance 均为零。r012 不产生 H1a PASS 或 KILL，也不授权 H1b/H2、detector、risk/
coverage、SAR、HRSC、论文修改或其他扩展。

运行证据位于 `runs/r012/h1a/`（`fit_manifest.json`、`final.json`、canvas manifest、两个完整
checkpoint 与对应日志）；大文件不进入普通 Git。相关实现与固定配置已推送至 main。

### C 的 26 服务器只读复核

C 在服务器项目内确认 r012 已无存活进程。ResNet-50 seeds 1201、1202 完成；ResNet-50/1203、
ViT-B/16/1201、ViT-B/16/1202 的空日志在同一时刻创建，均未产生 traceback 或 final-epoch
checkpoint，ViT-B/16/1203 未启动。final 证据约 173.5 秒后开始写入。用户级日志没有对应 OOM、
Xid 或重启证据；但完整 kernel journal、dmesg、process accounting 与退出信号不可得。

因此可确认的是外部同时终止；约 180 秒的父命令、会话或执行器时限只是高置信推断，不是已证明
根因，也不能严格排除系统级 OOM。本次复核不改变唯一科学状态
`INCONCLUSIVE_R012_H1A` / `TRAINING_FAILURE`，不产生 H1a 正向或负向结果。

## r013

### SERVER 机器报告（未获 B 科学验收）

以下拟合、像素、信息墙、mutation 和数字均是服务器报告；不能把源码和摘要已推送等同于原始
证据已公开，也不能把本节后半的机器 POWER 当作 B 当前裁决。正式纠偏见下一节。

r013 先复核 r012 G0 compact input 和 4,065 个 train canvas manifest，随后对 ResNet-50、ViT-B/16
各执行 seed 1201/1202/1203 的六次全新 final-epoch fit。每个模型均从架构匹配初始化重新开始，未加载、
热启动、平均或比较 r012 参数。双架构单 batch 预检均为 finite，optimizer step 均为零。六个 checkpoint
的 SHA-256、preflight 和 canvas 身份记录均在 `runs/r013/`；所有六次训练正常完成。

模型封存后一次性冻结了 7,416 个 calibration eligible canvas，随后仅对 calibration 执行三臂和
RP1 `theta/theta+180` 平均推理。test component 的 canvas/pixel/model forward/performance 均为零。
六个 compact raw prediction 表均有 `3×7416×3` 概率，像素 identity、非零角扰动、theta+180 pair-order
及 w/h+90 补偿 mutation 均通过。独立验证器不导入生成器或统计实现，从 raw tables 重算 25 component、
50,000 个 PCG64(12012) 同步 bootstrap draws，逐格 Delta、标准差和 simultaneous q 与生成器一致。

六格（ResNet wing/engine/propulsion，ViT wing/engine/propulsion）Delta 为
`[0.004671, 0.005044, 0.020956, -0.001333, 0.009405, -0.015793]`；simultaneous upper 为
`[0.034201, 0.023530, 0.039691, 0.037985, 0.033825, 0.026484]`，没有任一格排除 2pp；对应功效为
`[0.20112, 0.58798, 0.55370, 0.08172, 0.31790, 0.07354]`。六格 clean simultaneous upper 均小于
0.5（最大 `0.397037`），18 个 head 均非单一类别。因此 clean utility 和实现门通过，但最小功效远低于
0.80。

唯一裁决为 `INCONCLUSIVE_R013_H1A`，reason=`POWER`。不得把其中单格 2.096pp 点估计包装为正向结果，
也不得据此输出 KILL、PASS、开启 H1b/H2、detector、risk/coverage、SAR、HRSC 或论文修改。完整 raw
predictions、draws、replicates、模型身份、独立验证和 final token 位于 `runs/r013/`；可复算代码与本结论
已推送至 main。

### B 独立审计：输入错源优先于 POWER

正式状态保留 `INCONCLUSIVE_R013_H1A`，原因优先为 `INPUT_IDENTITY / IMPLEMENTATION_INVALID`。
上节“实现门通过”“仅功效不足”撤销；机器六格值只保留为潜在受污染、未独立复算的历史报告。

B 与独立审计分别从官方 metadata/完整 GeoJSON 重建既有 lexical-PCG64(1010) split：253 个
image records、227 CAT、102 components、calibration 7,418 个 full objects。代码
`src/orientbench/r013/prepare_calibration.py:21` 只用 CAT 建字典，第26行依此取图，重复 CAT
后值覆盖前值；G0 的几何却来自正确的 `(loc_id,CAT)` 对应影像，并已保存 `source_cog`。

按公开生成器与冻结总体，2,318个 full objects 会被配到错误 COG，涉及20个 loc–CAT 键、两个
component。报告共同
eligible=7,416，故至少2,316个 eligible 会受影响；无实际 manifest 不给最终精确排除数。
31.25% 是对象比例，不是 component-equal 权重。例如 loc44 的项目对象189/214/216（按冻结
GeoJSON顺序枚举，不是官方永久ID）应读取
`44_1040010043B54900`，却被映射为`107_1040010043B54900`；独立 COG header 核验确认它们
是不同机场、不同宽高和 affine，不是同图别名。这不是跨 split 泄漏，而是标签、原图像素几何
与另一影像错配；三臂自洽也无法恢复“同一飞机”的因果单位。

同时，真实 render mutation 并未独立验证：theta180 项硬写 True，验证器相信生产者布尔值。
统计 verifier 未完整核对 power/区间/clean utility，finalizer 未纳入完整输入及模型身份。
本次没有服务器实际执行源码/产物的完整绑定，不能断言所有报告数字确由该代码版本产生；若
SERVER 实际使用另一个修复版本，仍须公开实际代码及证据，不能以未发布实现替当前报告验收。
远端 main 和 execution refs 未提供 r012/r013 compact raw、draws 与输入/模型 manifests，故 B
无法独立复现六格数值或证明报告的零 test 访问。完整代码定位、只读复算程序、输入 SHA 与创新
边界见 `doc/INNOVATION_REASSESSMENT_20260904.md`。

4,065 train eligible 的来源也须澄清：新 train split 的5,370 full objects中4,068旧
Public_Train=1、1,302旧flag=0；再取旧train交集及几何资格得到4,065。r013合同明确继承此集，
故不是本轮暗改，但G0完整新train支持不能当作实际训练支持。

建议后续仅 correction-only：先公开旧证据、逐对象核验来源，模型身份成立时复用六个既有模型
重建同一calibration三臂并独立复算；不重训、不改split/样本/阈值、不删受影响component、不
打开test。修复结果是透明重建，不是新的前瞻盲验证；即使PASS也不自动授权H1b/H2或升档。

## r014

### SERVER首批报告（执行结束，不等于B验收；下文保留报告语境）

本节来自SERVER的执行摘要；来源像素、模型身份和mutation通过等声明须以随后B复核为准，
不能因写入结果总账便视为全部已验证。已发布概率的数值与语义有效性分开判断。

r014 是来源身份 correction-only，不是新训练或新方法。旧 r013 产物、模型、raw predictions、draws、
统计和原裁决均保留；用 r014 统计程序从 preserved r013 averaged raw probabilities 重建旧六格，
Delta 与 q 的最大绝对差均为 `0`，故历史机器报告的数值本身可复现，但其像素来源错误，不能作为
有效 H1a 证据。

逐键审计官方 metadata、完整 GeoJSON、G0 lexical split 与 frozen manifest 得到：253 image records、
227 canonical CAT、14,707 full objects；train/calibration/test 分别为 54/32/26 locations（对应
52/25/25 components）。实际训练保持 5,370 train full → 4,068 `Public_Train=1` → 4,065 common
eligible，对应 wing `3023/1042`、engine `1682/2383`、propulsion `1195/2870` 的正/负支持。4,065
个旧 train canvas 与 `(loc_id,CAT,image_id,source_cog)` 正确来源的独立重建逐像素一致，六个 r013
final-epoch checkpoint 的参数未变化且仅 strict-load/eval 使用。

calibration 为 7,418 full、7,416 eligible；缺失对象 ID 9082、10788 均为 loc 105 / CAT
`104001002F92BB00`，理由是未进入原 frozen eligible manifest。公开 r013 生成代码的 CAT-only
字典后值覆盖使 2,318 个 eligible 对象（20 个 loc–CAT 键、两个 component）错配到另一 COG，且这些
2,318 个旧 canvas 与正确来源像素均实际不同。修正 canvas 单独保存在 r014，不覆盖旧 canvas。独立
GeoJSON→COG affine 几何对全部 eligible 的 L/S、center、RP1 theta、canvas side 零 mismatch；固定
reference set 的 2,385 个 corrected canvas 第二路径逐像素差也为零。

仅复用原六模型从正确 canvas 产生完整三臂、两视图概率。模型参数本体 SHA-256 在每次评估前后相同；
概率有限、在 `[0,1]` 且二类和为 1。identity、非零角响应、w/h+90 补偿、theta+180 pair order、
错 source/错行/NaN/缺模型拒绝和零方差夹具均由独立 mutation fixture 通过。修正 raw 与旧 raw 的
对象、component、标签集合相同；受影响对象的最大概率差介于 `0.8659–1.0000`，未受影响行只保留
浮点级差异（最大 `4.875e-4`）。

从完整修正 probabilities 以 float64 重算 50,000 个 PCG64(12012) 同步 component draws。独立实现
不导入生成器/统计模块，六格 Delta、sd、q 与主实现最大 Delta 差 `2.78e-17`。修正 Delta 为
`[0.005070, 0.005082, 0.021439, -0.000307, 0.009485, -0.014622]`，simultaneous upper 为
`[0.034394, 0.023599, 0.040060, 0.038661, 0.033944, 0.027798]`，功效为
`[0.20396, 0.58606, 0.56040, 0.08280, 0.31648, 0.07378]`。clean simultaneous upper 最大
`0.392332<0.5`，18 个 clean head 均非单一类别。

机器据此输出`INCONCLUSIVE_R013_H1A`、reason=`POWER`、valid=true，并声称旧输入/实现优先原因
已经闭合。B不接受其中“valid=true/全部闭合”，原因见下节；不得把单格2.144pp包装为整项
正结果。原末尾“单槽归于NO_ACTIVE_TASK”不符合尚未完成的r014合同，现予纠正。

### B独立复核：数值成立，验收尚未完成（2026-09-05）

读取的main为`8687d2e5de9eff12c27272f9290ee613f1b99500`，实际证据提交为
`bead82282b100ec89f7b58f50f5a32b2d6c2bf0e`。完整复核、代码反例定位和可运行的B只读
复算程序见`doc/R014_B_ACCEPTANCE_20260905.md`。

这次六模型raw、两视图、旧/新概率、draws与风险replicates确已公开。B不导入生产/验证模块，
从完整二类概率独立计算7,416对象、25 components的逐对象错误、class/component分母、
全部50,000同步draws、逐seed风险、六格区间/功效和clean utility。
draws与错误逐值相同，bootstrap风险最大差2.22e-16，Delta最大差2.78e-17，功效差0。

| 架构/属性 | Delta（pp） | 六维95%同时区间（pp） | 原合同功效 |
| --- | ---: | --- | ---: |
| ResNet-50 / wing | 0.5070 | [-2.4254, 3.4394] | 0.20396 |
| ResNet-50 / engine | 0.5082 | [-1.3435, 2.3599] | 0.58606 |
| ResNet-50 / propulsion | 2.1439 | [0.2817, 4.0060] | 0.56040 |
| ViT-B/16 / wing | -0.0307 | [-3.9275, 3.8661] | 0.08280 |
| ViT-B/16 / engine | 0.9485 | [-1.4973, 3.3944] | 0.31648 |
| ViT-B/16 / propulsion | -1.4622 | [-5.7042, 2.7798] | 0.07378 |

clean同时upper最大0.3923319，18个clean head均非恒定。实际无零分母draw、无零方差格；
argmax与单列概率>0.5在本数据上没有分类差异。因此生产代码的退化处理缺失没有改变这批
已发布数字，但不能代表其边界检验已经通过。ResNet propulsion下界为正，不是六格都跨零；
全部upper仍大于2pp、全部功效低于0.80，所以给定有效执行前提才可接受条件POWER，而非KILL。

按发布source_records计数，校准2,318行声明旧/正确canvas像素不同、训练0行不同；
这是读取服务器记录，不是B独立读取全部原COG像素。训练227行affected是CAT-only碰撞的
假想标记，不能当作训练错图。按该标记划分的5,098个未受影响对象，六模型三臂三属性相对
旧概率均没有分类翻转；最大概率差4.875e-4的执行来源尚未单独证明，不能直接称机器精度误差。

剩余不接受项是具体而非泛称“不严谨”：

- mutation的theta180只验证概率加法交换律；identity是同实现调用两次；错源/错行/NaN/
  缺模型仅计算布尔表达式，未把坏输入送入真实验证器。零方差区间直接赋常量。
- 第二路径像素只发布2,385/7,416对象；来源键直接取主审计表，缺记录会跳过，
  未完成原合同全canvas独立来源/像素核验。
- 原G0/共同eligible及旧输入登记、六模型初始化/完成训练/输入绑定记录未随证据发布。
  磁盘模型内容不变不能代替内存参数/buffer及原训练身份。两排除对象缺原资格原因。
- SERVER统计verifier只比较Delta/sd/q；finalizer硬编码受影响数与部分执行声明，不能以
  all_pass追认语义。B已补齐本批数学复算，不要求重新运行六模型。

正式状态仍为`INCONCLUSIVE_R013_H1A`，原因优先为剩余实现/证据有效性。
r014当前仅完成原有验收缺口；不重训、不再模型前向、不打开test、不追加r015。
原始身份不可恢复或实际render存在实质语义错误则如实结束，不能用新执行覆盖历史。
本次提升的是可复算性，不是新方法；全项目仍为JSTARS类领域测量论文候选，尚非TGRS/JPRS。

### SERVER剩余验收完成（2026-09-05）

本次没有训练、模型前向、test像素、test crop或test性能计算。独立从官方metadata恢复
`(loc_id,CAT)→image_id`后，逐像素比较全部7,416个calibration canvas，差异为0；相对旧canvas
有2,318行改变。全部4,065个旧训练canvas比较仍为零差异。逐对象记录已进入结果证据。

实际生产render在87个calibration source（覆盖全部20个受影响loc--CAT键）上与不导入生产
坐标函数的独立reference比较：最大像素差2.54810e-5，theta+180度视图换序最大差2.95043e-5。
这是float32生产三角函数和float64独立常量的重建误差；本次事后重建检查公开使用5e-5容差，
不回填为事前阈值。方向结构解析夹具的+10度像素响应为1.0。

独立验收器不导入生产统计、风险或裁决模块，从完整二类概率重建50,000个PCG64(12012)同步draw、
六格区间/功效和clean统计；最大发布差为3.10862e-15。真实入口已拒绝错source、错标签行、错概率行、
度弧度、缺模型、NaN、越界概率和零类别分母；共同重排被接受，合法全零方差退化得到q=0。

但原r013 fit manifest与calibration manifest不在服务器：当前只能确认六个磁盘模型SHA-256，
无法恢复指定初始化、8 epoch训练完成、训练输入绑定或calibration冻结时点。该缺口不能由本轮新检查
追认。因此最终裁决为`INCONCLUSIVE_R013_H1A`，reason=`INPUT_OR_IMPLEMENTATION`；此前给定执行来源
成立时的`POWER`诊断保留，但不是终态。不得据此重训、重新前向、打开test或自动创建新轮次。
