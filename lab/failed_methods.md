# 主要失败路线

## COI / 干预式轴向可辨识响应（r004）

- 状态：r005 已以同一 global theta-free matcher 完成 correction-only 复核，当前仍是
  `INCONCLUSIVE_R004_PROTOCOL_VALIDITY`，不是正式失败路线。
- 已核实：16 个 split×detector×condition 独立复算的 key 差集为 0、逐行最大绝对差为 0；八个
  test `DeltaY` 点估计都不大于 0.02，最大 0.017158，且八个非坍塌界限均通过。
- 未成立的前提：真实 HRSC G/P/N Holm-32 中八个 `clean-high>0.20` 格（J_eff/M15、两模型、
  两 corruption）均失败；这属于前三类操纵失败，不能转写为 KILL 或失败路线。
- 禁止重入：不得以重推理、重选 test 剂量、删除对象、pooled/global 平均、替换 detector family
  或降低标准化效应阈值来挽救或关闭该路线。

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
