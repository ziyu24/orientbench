# r010 统计—机制闭环

本轮从同一批 full post-NMS prediction dump 构造 Core-6 固定剂量轨道。P、D、S 的完整 evaluator 结果按剂量记录；D 是固定 dose=0 匹配方向的 GT-directed diagnostic，S 同时保留正负方向分量。六个 Core 单元均已完成独立 evaluator，且每个单元完成 1000 次 paired image-cluster AP bootstrap 与 baseline-cohort survival 计算。

当前机制门控为 `INCONCLUSIVE_MECHANISM_R010`：评估器和统计复算已完成，但冻结的 D/S 支持条件不足以形成强机制证据。仅允许 endpoint-qualified 描述性结论，不得声称统一因果机制、NMS 效应或 deployable selector。
