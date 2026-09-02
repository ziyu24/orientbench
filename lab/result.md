# SERVER 执行结果

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

