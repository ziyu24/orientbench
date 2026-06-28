# Launch Status 028

> 2026-06-28 17:00:08 CST
> approval: SUPERVISOR_APPROVED_028_RUN_NOW_FIX_RUNTIME_AUTONOMOUSLY

## 10 分钟内启动的 GPU job
- **ARS-DETR cross-dataset DIOR-R #16**: bare run_in_background torchrun, 4-GPU world_size=4, master_port=29871, arsdetr env。**RUNNING util 74-76%**，ETA ~3min。raw→/dev/shm/cqc/orientbench/predictions/DIOR-R/16/raw/。

## 根因修复（自主，未请示）
- ARS-DETR cross-dataset blocked_runtime **真根因 = 空 annfiles → ARS-DETR 0.1.0 DOTADataset 加载 0 images → ZeroDivisionError**（mmrotate-1.x 检测器容忍空 annfile，0.1.0 不容忍）。
- 修复: 用真实 GT(DOTA poly8) 填充 DIOR/FAIR1M/SODA farm annfiles（从 fullval_gt.jsonl obb→corners）。重跑即 util 74% 正常推进。
- 之前误判为 launch-method；实为 dataset empty-annfile 不兼容。已纠正。

## 队列
- ARS-DETR: DIOR(running) → FAIR1M(18) → SODA(17) → HRSC(19, native HRSCDataset)。
- Strip cross-dataset: DIOR(47) bare 重试（mmrotate-1.x，annfile 已填充更稳）。
- HRSC 多 detector: orcnn/rtmdet 等。
