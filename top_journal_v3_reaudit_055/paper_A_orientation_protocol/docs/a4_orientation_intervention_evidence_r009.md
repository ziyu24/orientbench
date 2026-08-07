# r009 角度干预证据闭合

Core-6（DIOR-R 三单元、FAIR1M-v1.0、SODA-A 两单元）均已通过 full-validation provenance。P（统一正向）、D（GT-directed diagnostic）和 S（正负扰动平均）三条预注册轨道在 0/2/5/10/15/20/25/30° 完成 GPU `RBboxOverlaps2D` 全评估，共 144 次调用。

逐匹配的 geometry-normalized severe-event 结果、500 次 image-cluster bootstrap 及 0/15/30° 的精确 IoU=0.75 生存审计已落盘。该包用于量化 AP50/AP75、角度风险和几何生存的剂量响应；GT-directed 轨道是诊断性上界，不能被解释为可部署选择器。r009 不包含训练、阈值或 split 修改，也不把 matched-only 结果升级为 full-val AP 证据。

最终证据状态：`PASS_R009_EVIDENCE_CLOSED`。这表示 r009 证据包完成，不表示 deployable selector 已成立。
