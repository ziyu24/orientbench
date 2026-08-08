# r015 独立验证器闭合

r016 不修改 r015 的数值、代码或稿件。它独立从 r014 的 sealed score、matched labels、冻结 image universe 和 SODA tile-to-mother mapping 重算六个 unit 与三个数据集的同步 bootstrap，并逐字段比较 r015 的 point estimate、percentile CI、centered p、Holm、support 与 gate。

验证确认 r015 的完整 cluster universes：DIOR-R 为 5,900 images，FAIR1M-v1.0 为 2,142 images，SODA-A 为 576 mother scenes；同数据集 units 的集合一致，零 eligible row cluster 被保留。9,000 个 bootstrap 值的最大绝对差不超过 `9.71445146547012e-17`，所有 summary 字段在 `atol=1e-12, rtol=0` 下匹配。

r016 同时复核 r015 的单提交 19 路径范围、`dis/B.md` blob、18 个非自引用 manifest blob、r014 seal 与 final manifest、集合交集、Parquet schema、特征契约 witness、稿件边界、claim hash 与 novelty-source 标记。r015 runtime manifest 未登记其唯一 runtime output 的 bytes/SHA，此项保留为 `R015_MANIFEST_OMISSION`，但 r016 对现存 runtime 只读核验并不回写 r015。

成功 token `VALID_R015_CLOSURE_R016` 仅表示独立验收已完成；它不追认 r015 当时的完成语义，不改变 `FAIL_PROTOCOL_R014`，也不将已揭盲的 Core 数值升级为 confirmatory 或 deployable 证据。
