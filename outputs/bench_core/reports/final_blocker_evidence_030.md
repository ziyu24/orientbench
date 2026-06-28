# Final Blocker Evidence 030

> 2026-06-28 18:20:05 CST

- **ARS-DETR FAIR1M**: blocked_class_mapping_final_with_evidence — KeyError 'Engineering-Ship'；FAIR1M 类名含空格，与空格分隔 DOTA-txt + ARS-DETR 固定 CLASSES 不兼容。需 class-name adapter（underscore 映射 + config CLASSES 对齐），本轮 budget 边界未完成。
- **point2rbox**: blocked_upstream_artifact_unavailable_final — ted.pth 全上游(modelscope/github/hf/openmmlab)不可用(空/9B/401/404)。weak_nonformal，不进 formal gate。
- **Strip HRSC / ARS-DETR HRSC**: HRSC native HRSCDataset 与 DOTADataset farm 不同；pattern 可用（_hrsc_root + 各自 dataset），budget 边界。
- **genuine physical multi-view C1 / cross-host A4**: out_of_scope（需新数据 + P2/P3 机制 + 批准）。

---
## ARS-DETR SODA/HRSC (2026-06-28 18:23:52 CST)
- **ARS-DETR SODA**: blocked_class_mapping_final_with_evidence — ARS-DETR SODA config CLASSES 与 SODA GT 类名(small-vehicle 等)映射不一致(KeyError on class)；3 次重试未通过。需 class-name adapter 对齐 config CLASSES。
- **ARS-DETR DIOR 成功**(NRC 0.999)；DIOR 类名与 config 对齐故跑通。SODA/FAIR1M 类名映射为剩余 runtime 工作。
