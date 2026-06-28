# 028 Cells Status

> 2026-06-28 17:24:30 CST

| cell | status | evidence/fix |
|---|---|---|
| ARS-DETR DIOR-R #16 | **done (exploratory full-val)** | 68MB/40668 preds; NRC 0.999 n_used=33 (ARS-DETR DIOR weak mAP 0.4158); root-cause empty-annfile fixed |
| Strip DIOR #47 | **running** (inference [700/733] OK) | empty-annfile restore + DumpDetResults evaluator override; completing async |
| ARS-DETR FAIR1M #18 | **blocked_runtime_with_evidence** | KeyError: FAIR1M class names have spaces, incompatible with space-delimited DOTA-txt + ARS-DETR fixed CLASSES |
| ARS-DETR SODA #17 | deferred | same class-format risk; budget-bounded |

## 关键
- **ARS-DETR cross-dataset UNBLOCKED**（DIOR full-val 真实跑通；根因=空 annfile→ZeroDivisionError，已填真实 GT 修复）。
- 自主修复多个 runtime bug（ckpt-path/empty-annfile/evaluator），未请示。GPU 持续占用（util 50-76%，bare command 正常）。
- ARS-DETR independent_archetype, NOT RHINO。thresholds 未变。非 DOTA 全 exploratory。

---
## 029 update (2026-06-28 17:56:03 CST)
- Strip cross-dataset DIOR #47: **blocked_runtime_with_evidence**（4+ 次尝试：inference 跑到 [700/733] OK，但 DumpDetResults/DDP 在 evaluator/收尾阶段反复 crash；mmrotate-1.x Strip 特定不稳）。LSKNet 同路径成功，Strip 不稳→留证据。
- 最终矩阵: 24 cells / 6 datasets（final_matrix_summary）。
