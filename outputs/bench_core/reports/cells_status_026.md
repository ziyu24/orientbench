# 026 Cells Status

> train-if-needed + continue full-matrix

| cell | ckpt_load | inference | reason |
|---|---|---|---|
| ARS-DETR cross-dataset (DIOR/FAIR1M/SODA/HRSC) | OK (missing=0) | **blocked_runtime** | 4-GPU worker crash-restart loop on cross-dataset farm (torchelastic 8 attempts); ARS-DETR DOTA-v1.0 works (025) |
| Strip cross-dataset (DIOR #47) | OK (missing=2/384) | **blocked_runtime** | 4-GPU worker init stall on cross-dataset farm; ckpt-load proven (not fake head) |
| point2rbox | n/a | **blocked_upstream_artifact_unavailable** | ted.pth empty on modelscope, 9B on github, 401 on hf; weak_nonformal |
| HRSC angle | n/a | **resolved_with_evidence** | mbox_ang used directly as le90 rbox theta (hrsc.py:175-181) + LSKNet HRSC mAP 0.906 |
| training | n/a | **no_training_needed** | all remaining cells have valid matching checkpoints in pth_data |

## 说明
- **no_training_needed**：所有 cell（Strip/ARS-DETR cross-dataset, HRSC detectors）在 pth_data 均有 valid matching checkpoint → 不训练，直接 inference（GPU 由 inference 占用，不空闲）。
- Strip/ARS-DETR cross-dataset **ckpt-load 已证**（num_classes adapter，**不假改 head**）；inference 在 cross-dataset farm 上 4-GPU 出现 worker crash/stall → **blocked_runtime**。DOTA scope 的 ARS-DETR(025)/Strip(020)/LSKNet(020) 均已成功，cross-dataset LSKNet(025) 也成功。
- 并行 GPU 已演示（ARS-DETR + Strip 并发共享 4 卡）；出现 worker 重启不稳后**按规则改串行 4-GPU**（仍 blocked_runtime，记录原因继续）。
- thresholds.yaml 未变；非 DOTA 全 exploratory；ARS-DETR independent_archetype/not_RHINO。
