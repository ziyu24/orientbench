# Final Push 030

> 2026-06-28 18:20:05 CST

## 新增成功 cells
- **Strip cross-dataset DIOR-R #47**: NRC 0.506, med_err 1.18°, n_used 27846 (exploratory)。**关键修复 = test_evaluator._delete_+DumpDetResults 绕开 DOTAMetric 空-GT crash**。Strip cross-dataset UNBLOCKED。
- ARS-DETR SODA-A #17: running（async）。

## point2rbox 封口
- ted.pth: modelscope 空 / github 9B / huggingface(model+dataset) 401 / openmmlab 404 → **blocked_upstream_artifact_unavailable_final**。weak_nonformal。
