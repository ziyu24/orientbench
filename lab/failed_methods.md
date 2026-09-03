# 主要失败路线

## COI / 干预式轴向可辨识响应（r004）

- 状态：SERVER 报告负向，但 B 未验收；当前为 `INCONCLUSIVE_R004_PROTOCOL_VALIDITY`，
  不是正式失败路线。
- 未验收事实：八个报告的 `DeltaY` 点估计都小于 0.02，最大值为 0.017163；但 trainval 与
  test 使用了不同一对一 matcher，真实 test 的 `J_eff/M_15` 操纵有效性也未计算。
- 唯一允许动作：复用原 clean 与四个干预预测，统一冻结 matcher 并完成真实操纵与独立复算。
  不得重推理、重选 test 剂量、删除对象、改为 pooled/global 平均或替换 detector family。
- 关闭条件：只有 correction-only 复核证明试验有效且负向主门仍成立，才把本节改为正式
  `KILL_COI_R004`；若输入或操纵有效性无法恢复，则永久保留 inconclusive。

## CMR

- 状态：关闭。
- 触发事实：r001 geometry theta中位`0.2425237894 rad`超过`0.05 rad`门。
- 证据限制：shuffle_class与shuffle_box作废，但不改变geometry负门。
- 禁止重入：不得换shuffle字段、阈值或措辞继续同一条件混合路线。

## GR-EQS

- 状态：负向冻结，不是正式KILL。
- 触发事实：三个数据集风险非劣均失败；18组`lambda=0`，fusion与raw恒等；正式r002又因
  FAIR1M-D cohort从15199/1231漂移到15148/1222而`FAILED_ACCEPTANCE`。
- 证据限制：不能把缺失的51行补写，也不能外推为所有风险控制无效。
- 禁止重入：不得换数据、缩cohort或修改gate挽救同一融合定义。

## 已消费的历史路线

项目历史已经将Q-SetOD、OER、SAUR、AHC、P2C、CORA与PEF列为失败或已消费路线；其中
Q-SetOD的r037集合门没有witness。精确代码、指标和裁决从`doc/ARCHIVE.md`登记的父提交读取。
后续不得只换名称、阈值、数据子集或追加同类消融重新进入；新候选必须改变核心可观测量、
干预或推断对象。

## 非失败项

AIRO/COI的r003从未执行，不能写入失败路线。它仅作为`lab/discussion.md`中的未决候选保留。
