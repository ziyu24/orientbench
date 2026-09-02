# 主要失败路线

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

