# OrientBench — 031 Final Freeze / Release Report

> 项目当前 approved scope **已完成并冻结**。整体项目未完成（partial）。git tag `orientbench-current-scope-final`。

## 1. 031 完成/未完成
- **031 完成**：最终状态冻结 + 全套最终报告 + release 包 + 验证。无新实验、无 GPU job（仅 backfill 11 个 per-cell manifest，自 aggregate metrics，非重跑）。

## 2. 当前 approved scope 是否完成
- **current_approved_scope_complete = true**。

## 3. 项目是否整体完成
- **full_project_complete = false**（cross-dataset/multi-detector 为 exploratory partial；多 detector cell + multiview/cross-host 未完成）。

## 4. 最终 coverage（23 real cells / 6 datasets）
| dataset | #detectors | detectors |
|---|---|---|
| DIOR-R | 6 | oriented_rcnn, psc, rtmdet, lsknet, ars_detr, strip_rcnn |
| DOTA-v1.0 | 6 | 9-archetype 子集（orcnn/psc/rtmdet/rhino/h2rbox/lsknet） |
| DOTA-v1.5 | 4 | orcnn, rtmdet-s, rtmdet-m, o2-rtdetr(A4) |
| FAIR1M-v1.0 | 3 | orcnn, psc, lsknet |
| SODA-A | 3 | orcnn, psc, lsknet |
| HRSC2016 | 1 | lsknet (angle resolved_with_evidence) |

## 5. formal 成果（DOTA frozen scope）
- DOTA D2 partial formal gate（3 detector）。
- RHINO host(C1/B) + O2-RTDETR host(A4) 训练+锁定（mAP 0.7201 / 0.6497；sha256 55a90abb / 3e32fa11）。
- C1 augmentation-view consistency gate = **formal_pass**（D_audit）。
- A4 same-host source-attribution gate = **formal_pass**（D_audit）。
- 阈值 D_cal 冻结（token 017），thresholds.yaml sha256 **b7c4e649 未变**。

## 6. exploratory 成果
- 23 cross-dataset/multi-detector cells，真实 inference + orientation-reliability(NRC/Risk)。
- full-val: DIOR/FAIR1M/SODA orcnn+psc+rtmdet+lsknet + ARS-DETR DIOR + Strip DIOR。
- ARS-DETR 隔离 env(mmrotate 0.1.0) + DIOR cross-dataset 解锁；Strip DIOR 解锁；HRSC angle resolved。
- 关键 NRC: DIOR orcnn 0.52/strip 0.51/lsknet 0.53/arsdetr 0.999；FAIR1M 0.86/lsknet 0.83；SODA 0.84/lsknet 0.76；HRSC 0.81。

## 7. blocked 项（final_blocker_evidence.md）
- **point2rbox**: blocked_upstream_artifact_unavailable_final（ted.pth 全上游空/9B/401/404）。weak_nonformal。
- **ARS-DETR FAIR1M/SODA**: blocked_class_mapping_final_with_evidence（空格/类名映射）。
- **Strip FAIR1M/SODA**: 无 baseline；**HRSC 多 detector**: pattern available（未跑）。
- **genuine multi-view C1 / cross-host A4**: out_of_scope。
- 说明：以上为 **coverage blocker**，非失败实验、非伪造。

## 8. 可宣称结论
- DOTA 范围内 D2/host/C1(augmentation-view)/A4(same-host) 已冻结 + D_audit formal_pass。
- 6 datasets × 多 detector exploratory orientation-reliability 已真实测量。
- ARS-DETR 独立 archetype（NOT RHINO）。

## 9. 禁止宣称结论
- full project complete / all datasets covered / 9-detector matrix complete。
- C1 genuine physical multi-view / A4 cross-host causal / ARS-DETR=RHINO。
- 任何非 DOTA cell 为 formal gate。

## 10. verification / test / git
- pytest **264 passed**；verifier 90-101 **全部 VERIFIED**（101_verify_final_release_031 21/21）。
- git head `4d4a807`，tag `orientbench-current-scope-final`，**0 大文件**。thresholds **b7c4e649 未变**。

## 11. release 路径
- `outputs/releases/orientbench_final_current_scope/`（final reports + coverage + claim ledger + reproducibility + artifact manifest + SHA256SUMS + thresholds copy + git hash）。
- 报告：`outputs/bench_core/reports/final_*.{md,csv,json}`。
- raw/schema：`/dev/shm/cqc/orientbench/predictions/`（scratch，非持久）；project per-cell `manifest.json`。

## 12. 是否建议停止当前阶段
- **建议停止当前阶段**（current scope 已冻结交付）。无新可执行路径。

## 13. 后续若继续，最小行动
- ARS-DETR FAIR1M/SODA: class-name adapter（config CLASSES ↔ GT 名对齐）。
- Strip/ARS-DETR HRSC: HRSC native farm（pattern 已验证）。
- point2rbox: 待上游恢复 ted.pth。
- C1 genuine multi-view / cross-host A4: 需新数据 + P2/P3 机制 + 批准。
