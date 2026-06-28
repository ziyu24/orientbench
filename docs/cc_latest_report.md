# OrientBench — 030 Final Push Report

> 阶段性完成（030）。本轮已把可解的 cross-dataset cell 跑通，剩余给硬证据封口。建议进入 031 final freeze/report。

## 1. 030 状态
- **阶段性完成**。Strip cross-dataset 解锁成功；ARS-DETR SODA/FAIR1M 与 point2rbox 给最终证据封口。

## 2. 10 分钟内启动的 GPU job
- Strip cross-dataset DIOR-R #47（bare 4-GPU，arsdetr→ai4rs，master_port=29931）→ 跑通。
- ARS-DETR SODA-A #17（4-GPU）→ class-mapping crash。

## 3. 新增成功 cells
- **Strip cross-dataset DIOR-R #47**：NRC 0.506, med_err 1.18°, n_used 27846（exploratory）。
  - 关键修复：`test_evaluator._delete_=True + DumpDetResults` 绕开 DOTAMetric 空-GT crash（task 1 指定 dump raw only）。**Strip cross-dataset 自此 UNBLOCKED**。

## 4. 仍 blocked final cells + 证据
- **ARS-DETR FAIR1M**：blocked_class_mapping_final_with_evidence（KeyError 'Engineering-Ship'，FAIR1M 类名含空格 ↔ 空格分隔 DOTA-txt 不兼容）。
- **ARS-DETR SODA**：blocked_class_mapping_final_with_evidence（SODA config CLASSES 与 GT 类名映射不一致，KeyError；3 次重试未过）。
- **point2rbox**：blocked_upstream_artifact_unavailable_final（ted.pth：modelscope 空 / github 9B / huggingface 401 / openmmlab 404，全上游不可用）。weak_nonformal。
- **Strip/ARS-DETR HRSC**：pattern_available（HRSC native HRSCDataset farm；budget 边界未跑）。
- **genuine physical multi-view C1 / cross-host A4**：out_of_scope（需新数据 + P2/P3 机制 + 批准）。

## 5. 最终 detector × dataset 覆盖率（23 real cells / 6 datasets）
| dataset | #detectors | detectors |
|---|---|---|
| DIOR-R | 6 | oriented_rcnn, psc, rtmdet, lsknet, ars_detr, strip_rcnn |
| DOTA-v1.0 | 6 | 9-archetype 子集（orcnn/psc/rtmdet/rhino/h2rbox/lsknet 等） |
| DOTA-v1.5 | 4 | orcnn/rtmdet-s/rtmdet-m/o2-rtdetr(A4) |
| FAIR1M-v1.0 | 3 | orcnn, psc, lsknet |
| SODA-A | 3 | orcnn, psc, lsknet |
| HRSC2016 | 1 | lsknet（angle resolved_with_evidence） |

## 6. full-val 状态
- DIOR/FAIR1M/SODA：orcnn + psc + rtmdet + lsknet full-val 完成；ARS-DETR DIOR full-val；Strip DIOR full-val。HRSC test split。

## 7. 关键 metrics（exploratory NRC-AUC，near-square masked）
- DIOR-R：orcnn 0.52 / psc 0.55 / rtmdet 0.43 / lsknet 0.53 / strip **0.506** / arsdetr 0.999
- FAIR1M：orcnn 0.86 / psc 1.08 / lsknet 0.83
- SODA-A：orcnn 0.84 / psc 1.26 / lsknet 0.76
- HRSC：lsknet 0.81
- 观察：PSC angle-coder 在 FAIR1M/SODA NRC>1.0（选择弱于 random），跨数据集一致模式。

## 8. 状态汇总
- **point2rbox**：blocked_upstream_artifact_unavailable_final（weak_nonformal）。
- **ARS-DETR**：cross-dataset DIOR 解锁（independent_archetype, NOT RHINO）；SODA/FAIR1M class-mapping blocked。
- **Strip**：cross-dataset DIOR 解锁（evaluator fix）；FAIR1M/SODA 无 baseline；HRSC pattern 可用。
- **HRSC**：lsknet 完成；angle resolved_with_evidence；多 detector pattern 可用。

## 9. GPU / 存储 / thresholds
- GPU：间歇持续（Strip DIOR 跑通；ARS-DETR SODA crash 后释放）。bare-command 4-GPU world_size=4，batch override=false，无降 batch。
- 存储合规：raw+schema 全 scratch，project 0 大文件（pred schema），仅 manifest/sha256/metrics/GT-index。
- thresholds.yaml sha256 **b7c4e649… 未变**。

## 10. verification / test / git
- pytest **262 passed**（修正后）；verifier 90-100 全过（含 100_verify_final_push_030）。
- git：lightweight 提交，0 大文件。

## 11. 是否建议进入 final freeze/report
- **建议进入 031 final freeze/report**。剩余 cells 为：ARS-DETR SODA/FAIR1M class-name adapter、HRSC 多 detector（pattern 已验证）、point2rbox（上游死）——均非新可执行路径或需额外 runtime 预算；无新增可执行路径即可冻结。

## 12. 产物路径
- `outputs/bench_core/reports/{final_matrix_summary,final_push_030,final_blocker_evidence_030,remaining_blockers,verification_final_push_030}.*`
- `outputs/predictions/DIOR-R/47/manifest.json`（Strip）；raw+schema：`/dev/shm/cqc/orientbench/predictions/`
- `scripts/{74_final_matrix_summary,100_verify_final_push_030}.py`、`tests/test_030_final_push.py`
