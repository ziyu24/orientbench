# r015 协议闭合说明

本轮只读审计 r014 的持久化输入，并以完整 D_audit 图像总体（SODA-A 为 mother scene）重新执行同步 cluster bootstrap。r014 的数值不因本文件而转为正式部署性证据：r014 的预标签封存未包含协议与全部执行代码，且在目标审计前不存在可恢复的完整代码级时间锁。

因此，r015 的合法数值定位是探索性 post-audit evidence。同步重算使用同一数据集、同一 replicate 的 cluster multiplicity 同时作用于全部 units；dataset 统计量在每个 replicate 内对 units 等权平均。空 eligible row 的 cluster 保留在总体中。SODA-A 映射为 mother scene，但其冻结角色在母景层并不独立，不能被写为严格 mother-scene 校准/审计保证。

审计还分别记录了物理标签文件读取与拟合使用。源数据读取函数在 role 过滤之前解析完整 matched JSONL；该事实不能由“最终拟合未使用 target role”抵消。特征与 score 的 schema 不含角误差、GT、风险或 split 字段，但这一 schema 属性也不能替代历史时间锁。

结果可支持后续对 EQS 的研究动机，不能支持已验证的 deployable selector、独立外部确认或跨 host 普遍迁移。HRSC2016/LSKNet 的点估计为正而区间跨零，保留为不确定外部检查。
