# Final Blocker Evidence (consolidated)

> 2026-06-28 22:14:10 CST

## point2rbox — blocked_upstream_artifact_unavailable_final
- ted.pth: modelscope「文件内容为空」(Code 10990101007) / github releases 9 bytes(asset 缺) / huggingface(model+dataset) 401 / openmmlab 404。所有上游不可用。weak_nonformal，不进 formal gate。

## ARS-DETR FAIR1M/SODA — blocked_class_mapping_final_with_evidence
- FAIR1M: KeyError 'Engineering-Ship'（类名含空格，与空格分隔 DOTA-txt + ARS-DETR 固定 CLASSES 不兼容）。
- SODA: ARS-DETR config CLASSES 与 GT 类名映射不一致(KeyError)，3 次重试未过。
- ARS-DETR DIOR 成功(NRC 0.999)证明 env/pipeline 正常；仅类名映射为剩余工作（非伪造、非失败实验，记为 coverage blocker）。

## Strip non-DIOR cross-dataset — pattern_available / no_baseline
- Strip DIOR 解锁(NRC 0.506, _delete_+DumpDetResults evaluator fix)。FAIR1M/SODA 无 Strip baseline。HRSC: native HRSCDataset farm pattern 可用，未跑(budget)。

## out_of_scope（非失败，仅 coverage blocker）
- genuine physical multi-view C1: 数据集均单视图航拍，无多物理视角采集 → 需新数据。
- cross-host A4: 需多 host 因果设计 + P2/P3 机制 + 批准。

> 说明: 以上 missing/nonformal cells **不是失败实验**，仅为 coverage blocker（上游 artifact / 类名映射 / 无 baseline / out_of_scope）。
