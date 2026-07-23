# A5 人工标注、official GT 对照与仲裁

第三标注员的 150 个目标已按预注册规则冻结为三数据集各 50，同时包含高分歧/ambiguous 边界和随机低分歧对照。任务包独立随机、匿名、互盲，不暴露前两人、official GT、模型预测或分歧。

Annotator 1 与 official GT 的总体 discrepancy：n=468，mean=5.2721°，median=1.7639°，P(>5°)=0.173077；Annotator 2：n=463，mean=5.1219°，median=1.7899°，P(>5°)=0.161987。这些是人类标注与数据集 official annotation 的差异，不是把 official GT 当绝对真值后得到的“人工误差”。Inter-annotator disagreement 与 annotator-vs-GT discrepancy 始终分列。

高分歧仲裁定义为任一 pairwise disagreement >5° 或任一 ambiguous；三数值角使用 180° circular median，并另报 5° 邻域多数共识。模型预测与 official GT 不参与自动仲裁，也不从模型误差扣除人工分歧。

当前第三真人结果数为 0，因此不生成正式 consensus 数值。**A5 判定：PARTIAL_TWO_ANNOTATOR_WITH_GT；状态 HUMAN_ANNOTATOR_3_BLOCKED。**
