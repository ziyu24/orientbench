# r017 静态收据闭合

r017 不重新运行 9,000 次 bootstrap，也不修改 r014-r016。它对 committed CSV/JSON 建立静态数值收据，并从冻结 image universe、matched labels 与 SODA map 重建 zero-eligible cluster 集合和 canonical split 交集。

静态收据确认 bootstrap 表含恰好 9,000 行；六个 unit 与三个 dataset 均完整覆盖 replicate 0--999，无重复、缺失、额外 key 或非有限值。r016 summary 与 r015 的 point、CI、centered p、Holm 和 support 在 `atol=1e-12, rtol=0` 下相同。冻结 gate 由规则重算，不以 6/6 常量替代：支持覆盖三数据集、至少两类检测器、FAIR unit D，并达到 dataset 3/3；`gate_r015.json` 的 status、counts、同步标记与 SODA mother-scene 主统计均一致。

所有六个完整 universe 均含 zero-eligible clusters；收据保存其 count 与 sorted-set SHA。r015 leakage audit 使用 SHA256 80/20 role，而实际 canonical split 是 MD5 parity，该差异固定记录为 `R015_SET_AUDIT_ROLE_DRIFT`；r017 使用 canonical split 重建后未发现禁止交集。

feature/score schema、prelabel/final seal hash、源码行 witness、稿件边界与八条 claim 均静态复核。三个既有实现偏差继续保留，不修历史代码或重评分。novelty 索引中的根页和占位页已在新索引中统一标记为 `UNKNOWN_EXCLUDED`。

`VALID_STATIC_RECEIPT_R017` 只闭合静态验收与投稿证据索引。r016 历史状态仍为协议漂移；Core 数值仍是 `EXPLORATORY_CORE_SUPPORT_R015`，不得升级为 confirmatory 或 deployable 证据。
