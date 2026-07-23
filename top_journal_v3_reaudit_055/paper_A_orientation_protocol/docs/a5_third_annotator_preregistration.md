# A5 第三标注员与仲裁预注册

冻结时间：2026-07-22 14:20 CST，早于第三标注员任务生成和任何第三人结果。

- 从既有 600 canonical targets 中固定抽取 150 个，三数据集各 50。
- 每个数据集优先包含 15 个边界目标：数值双标最大圆周分歧大于 5 度，或任一原标注为 ambiguous/skip；其余 35 个从低分歧/常规目标按固定种子 20260722 随机抽取。
- 在上述配额内以 size、aspect-ratio、class 和 `ar>=2.1` 覆盖为次级平衡目标，不用模型结果或 official GT discrepancy 选样。
- 第三标注员独立、匿名、互盲；界面不显示前两人、official GT、模型框、disagreement 或 reliability score。
- 高分歧仲裁集合冻结为：三人任一 pairwise circular disagreement 大于 5 度，或任一人标记 ambiguous。
- 三个数值角存在时使用 180 度周期 circular median；若至少两人落在 5 度邻域，报告该多数邻近共识；否则标记 unresolved。official GT 和模型预测均不参与仲裁。
- 第三人真实结果缺失时只生成协议和空 schema，不生成 consensus 数值。
