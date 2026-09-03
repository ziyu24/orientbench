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
  由对应 fabric result ref 保存，普通 Git 只提交可重建代码、测试、规格及本结论。

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
