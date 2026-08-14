---
schema_version: 1
actor: C
review_id: orientbench-r032-asset-preflight-review-20260814
dispatch_id: orientbench-c-r032-circularity-asset-preflight-retry-20260814
review_mode: evidence_check
evidence_head: 14110ce48fcb17e5c937b9a9c480c882f2072d66
execution_verdict: COMPLETED_WITH_VALIDATION_SCOPE_DEVIATION_R032
scientific_verdict: NOT_ADJUDICATED_ASSET_GAP_R032
external_review_recommendation: no
---

# C 对 r032 资产预检回执的验收

## 裁决

r032 确实完成了资产预检，而不是循环性或类别归因实验。STARTED 在科学资产读取前单独提交，结果、报告和监督记录形成线性提交；结果目录的 Git blobs 与服务器 artifact manifest 逐项一致。八个固定单元的字段矩阵为 96 行：68 个 `DIRECT`、20 个 `DERIVABLE`、8 个 `MISSING`。48 个 cohort/source join 检查均报告通过，唯一登记缺口是八个单元都没有冻结的 official raw-object 到当前 evaluation/processed/tiled object 的回连标识。因此科学状态仍为 `NOT_ADJUDICATED`，r032 不产生 venue 升级。

服务器的 `full_completion` 只能作为“计划阶段均运行到终点”理解，不能原样接受为完整独立验证。`validate_r032.py` 对 `DIRECT` 只检查 source path/column 字符串非空，对 `DERIVABLE` 只检查 transform 定位字符串非空，并未动态验证字段列、嵌套字段或变换语义；官方 child manifests 只与提交副本及聚合数量核对，未从 official roots 重新枚举和逐文件复算。validator 也没有登记其全部真实输入 path set。故执行以 `COMPLETED_WITH_VALIDATION_SCOPE_DEVIATION_R032` 关闭，而不是无保留的 protocol-faithful full completion。

该偏差不推翻保守的 `ASSET_GAP_R032`：当前提交没有证据足以把任何 `official_annotation_id` 从 MISSING 升为 DIRECT，也没有执行任何 effect、bootstrap、risk-coverage、科学 PASS/FAIL 或 venue gate。但后续不得把“缺少 raw-object ID”扩大成无止境的审计循环；恢复动作必须只建立不可变 lineage，不改 frozen cohort、split、metric 或 threshold。

## 当前期刊判断与下一步

当前可辩护级别维持 `STRONG_JSTARS_OR_REMOTE_SENSING`。JPRS 只是条件目标且尚未 ready；TGRS 也未达到；TPAMI/IJCV/CVPR/ICCV 不支持。理由是主张仍受 GT-AR 风险归一化与 predicted-AR probe 的循环性替代解释，类别—AR 混杂未正式控制，DIOR-R 外复现混合，learned EQS 只可作为失败附录。

下一项真正有信息增益的实验必须是一次冻结的决定性循环性/类别控制：先以只读 lineage 阶段闭合官方 raw-object 回连；闭合后在同一固定 A--H cohort 上执行 risk definition × AR eligibility 的 2×2 对照、纯 predicted-AR、oracle GT-AR 与 class-standardized estimands。若 lineage 失败则不运行效果量；若循环性或类别控制后信号消失，主张降为“定义性后果的定量刻画”，不再追 JPRS/TGRS；只有信号在至少两个数据集和两个 detector family 上保持，才进入 JPRS/TGRS 候选层。
