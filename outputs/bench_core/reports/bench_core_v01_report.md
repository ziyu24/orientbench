# Bench-Core v0.1 Report (dry-run)

> 生成时间: 2026-06-26 10:08:38 CST
> stage: core1 — **DRY-RUN / SANITY**，thresholds.yaml 未冻结，无 gate 结论。
> 只读数据；未推理/训练/下载；未替代 RHINO；未启动 9-detector matrix / B-MVE。

## 1. Baseline Inventory
- 总数 **73**，valid **67**，invalid **6**，inference_ready=67。
- pth 不在磁盘: 0；含 warning 记录: 21。
- 字段缺失: {'mmrotate_stack': 21, 'env': 21}。

## 2. Dataset Split 与 Missing 清单
- known=7 present=5 missing=2
- present: DOTA-v1.0, DOTA-v1.5, DIOR-R, HRSC2016, FAIR1M-v1.0
- **missing: SODA-A, ICDAR-MLT**

## 3. GT Index 覆盖
| dataset | split | files_ok | objects | valid_geom | invalid_geom | max_files |
|---|---|---|---|---|---|---|
| dior | trainval | 200 | 1019 | 1019 | 0 | 200 |
| dota10 | train | 200 | 2774 | 2774 | 0 | 200 |
| dota15 | train | 200 | 6727 | 6727 | 0 | 200 |
| fair1m | train | 200 | 2874 | 2874 | 0 | 200 |
| hrsc | trainval | 200 | 613 | 613 | 0 | 200 |

## 4. GV-Obliquity 分布 (per dataset/split/class, controlled sample)
- gv_obliquity_baseline.csv: 93 class 行。数据集/split 汇总：
| dataset/split | objects | valid | near_square |
|---|---|---|---|
| DIOR-R/trainval | 1019 | 1019 | 129 |
| DOTA-v1.0/train | 2774 | 2774 | 53 |
| DOTA-v1.5/train | 6727 | 6727 | 56 |
| FAIR1M-v1.0/train | 2874 | 2874 | 210 |
| HRSC2016/trainval | 613 | 613 | 0 |

## 5. Source Measurement (dry-run)
- max_bg_files=60 jobs=16（background 受控抽样，已记录非静默截断）。
| file | objects | V_layout | bg_ok_obj | V_bg | meanE_layout | meanE_bg |
|---|---|---|---|---|---|---|
| sources_dior_trainval.jsonl | 1019 | 586 | 338 | 206 | 0.441 | 0.025 |
| sources_dota10_train.jsonl | 2774 | 2262 | 1231 | 1174 | 0.695 | 0.081 |
| sources_dota15_train.jsonl | 6727 | 5377 | 1608 | 1551 | 0.607 | 0.085 |
| sources_fair1m_train.jsonl | 2874 | 1204 | 1171 | 1156 | 0.307 | 0.071 |
| sources_hrsc_trainval.jsonl | 613 | 87 | 177 | 177 | 0.108 | 0.021 |
- 公式: layout (V_layout/D_nbr/R_nbr/A_align/E_layout) 与 background (V_bg/A_bg/E_bg/bg_valid_ratio) 按项目执行文件 §6.4/§6.5；未给定常数 (gamma/annulus/bins) 为 dry-run。

## 6. Stress Bucket 数量 (dry-run percentiles, pending_threshold_freeze)
| dataset/split | n | near_square | dense_coherent | dense_incoherent | sparse_bg_strong | evidence_weak | domain_fragile | rotated_valid_mismatch |
|---|---|---|---|---|---|---|---|---|
| DIOR-R/trainval | 1019 | 129 | 45 | 4 | 42 | 328 | 0 | 0 |
| DOTA-v1.0/train | 2774 | 53 | 10 | 0 | 68 | 273 | 0 | 0 |
| DOTA-v1.5/train | 6727 | 56 | 9 | 1 | 84 | 1081 | 0 | 0 |
| FAIR1M-v1.0/train | 2874 | 210 | 36 | 1 | 201 | 1085 | 0 | 0 |
| HRSC2016/trainval | 613 | 0 | 20 | 1 | 52 | 374 | 0 | 0 |
- domain_fragile / rotated_valid_mismatch 为 placeholder（需 domain / rotated-view probe）。

## 7. Default Selection Score 定义 (frozen def, dry-run demo)
| head type | frozen default score |
|---|---|
| native_quality_head | native_plus_benchcore_default_comparison |
| pure_regression_head | calibrated_gv_obliquity_proxy |
| angle_distribution_head | negative_normalized_angle_entropy |
- dry-run demo 行数（per dataset/class）: 93；标注 not_detector_prediction / not_formal_calibration / not_official_result。

## 8. NRC-AUC Sanity + Risk@70 / Risk@90 (SYNTHETIC)
| dataset/split | n | matched | AURC | Risk@70 | Risk@90 | NRC-AUC | oracle | random | risk_mode |
|---|---|---|---|---|---|---|---|---|---|
| DIOR-R/trainval | 978 | 978 | 1.83954 | 2.22137 | 3.65011 | 0.04481 | 1.66983 | 5.45728 | synthetic_prediction_angle_error |
| DOTA-v1.0/train | 2174 | 2174 | 3.36897 | 4.47591 | 6.70332 | 0.02868 | 3.21345 | 8.6364 | synthetic_prediction_angle_error |
| DOTA-v1.5/train | 6140 | 6140 | 2.55928 | 3.27784 | 5.2196 | 0.0333 | 2.40363 | 7.07751 | synthetic_prediction_angle_error |
| FAIR1M-v1.0/train | 2753 | 2753 | 3.17861 | 4.17371 | 6.56766 | 0.02833 | 3.02316 | 8.50977 | synthetic_prediction_angle_error |
| HRSC2016/trainval | 326 | 326 | 2.98775 | 4.08097 | 5.5048 | 0.04158 | 2.83196 | 6.57882 | synthetic_prediction_angle_error |
- risk_mode=`synthetic_prediction_angle_error` 时：orientation_risk 由 GT↔synthetic-pred 匹配后的角度误差(deg)得到，selection_score=pred score。**SYNTHETIC，不代表任何 detector 性能**。

## 8.1 Prediction Contract 状态 (synthetic)
- mode=synthetic detector=synthetic_gv_proxy views=['original']
- synthetic prediction files: 5，总 preds=14007（is_synthetic / not_detector_output）。
- schema: dataset, split, image_id, detector_id, baseline_id, class_name, score, obb_cx, obb_cy, obb_w, obb_h, obb_theta, angle_unit, angle_version, source_path, is_synthetic, warnings

## 8.2 angle_version Audit 摘要
- baselines audited: 73；angle_version 分布: {'le90': 73}；source 分布: {'config_scan': 70, 'model_id_suffix': 3}
- dataset GT 角度: DOTA/DIOR/FAIR1M = le90_derived(minAreaRect)；HRSC = mbox_ang_rad (**uncertain**, le90 等价未核验)。详见 angle_version_audit.md。

## 8.3 Real Prediction Discovery
- candidates: 92；external prediction-ish: 19；coco-style needs_conversion: 2；ready-schema: 0。
- **no_real_prediction_found (ready-schema external): True**（synthetic 不计）。详见 prediction_discovery.md。

## 8.4 D_cal / D_audit Split (R4)
- salt=orientbench_v1 cal_fraction=0.5 all_mutually_exclusive=**True**（deterministic md5 hash）。
| dataset | n_images | n_cal | n_audit | intersection | disjoint |
|---|---|---|---|---|---|
| dior_trainval | 200 | 100 | 100 | 0 | True |
| dota10_train | 161 | 83 | 78 | 0 | True |
| dota15_train | 171 | 89 | 82 | 0 | True |
| fair1m_train | 174 | 82 | 92 | 0 | True |
| hrsc_trainval | 200 | 102 | 98 | 0 | True |

## 8.5 Readiness Check (threshold-freeze / eval)
- **overall_readiness: blocked** (ready=8 pending=7 blocked=4)；formal_gate_allowed=**False**。
- blockers: ['B_C1_thresholds', 'A_A4_thresholds', 'D2_thresholds', 'freeze_time_set', 'responsible_role_filled', 'rhino_host', 'a4_hybrid_host', 'soda_a_icdar_mlt_datasets', 'real_prediction_available', 'angle_version_certain', 'training_approval']

## 8.6 Training Readiness
- **training_allowed: False**（expected False）。
- reasons: ['thresholds not frozen', 'RHINO missing', 'A4 host pending', 'real predictions not yet formal', 'human approval required']
- blockers: ['training_allowed_default', 'R8_thresholds_frozen', 'host_baseline_selected', 'checkpoint_log_path_policy', 'lr_batch_schedule_alignment_plan', 'gpu_plan', 'real_predictions_formal', 'angle_version_verified', 'human_approval']

## 8.7 angle_version Evidence Audit
- **resolved_with_evidence: 5 / uncertain: 2**；HRSC: **uncertain**。
- DOTA/DIOR/FAIR1M GT le90-range 由 poly→obb→poly round-trip IoU + θ∈[-π/2,π/2) 证据支撑；HRSC mbox/le90 检测器等价仍 uncertain（标注 HBB 偏松，交叉验证不一致）；prediction theta unit 待真实 prediction。

## 8.8 Prediction Import Matrix
- rows: 75；status 计数: {'needs_inference': 58, 'blocked_missing_dataset': 8, 'not_applicable': 6, 'convertible_nonformal': 1, 'blocked_missing_detector': 2}。
- ready_schema (importable now): 0（多数 needs_inference / blocked）。

## 8.9 Inference Plan & Decision Packets
- inference_command_plan: 75 行，executable_now=True 的有 **0**（仅计划，不执行）。
- threshold_freeze_review: present（thresholds.yaml 未改）。
- collaborator_decision_form: present（全部 pending）。

## 9. Detector Taxonomy & Probe Matrix Template
- 9-detector archetypes: 9，available 8，missing 1。
- A4 host: hybrid_encoder_oriented_detr — frozen_snapshot_pending。
- probe_matrix_template.csv 为模板（PENDING_PREREGISTRATION / PENDING_MEASUREMENT），非实测。
- missing 标注: RHINO-style rotated DETR missing; A4 hybrid-host frozen snapshot pending; SODA-A dataset missing; ICDAR-MLT dataset missing。

## 10. R1–R8 状态
| 规则 | 内容 | 状态 |
|---|---|---|
| R1 | GT-identity 必跑 (C1 B-MVE-1 一等对照) | active (B 未启动) |
| R2 | B 死不迁 A (cross-view 目标不得入 A4) | active |
| R3 | A-gate-1 同宿主审计 (frozen hybrid-encoder oriented DETR) | pending host |
| R4 | Calibration / Audit split 分离 | pending (dry-run 未分 split) |
| R5 | 扰动族互斥 G_geom ∩ G_style = ∅ | active (probe 未运行) |
| R6 | Host / Baseline 冻结 (A4 / C1=RHINO / D2=9-detector) | RHINO missing; A4 pending |
| R7 | D2 独立性与 Bench-Core 基元统一 | active (GV/NRC/score 单源) |
| R8 | 跑前冻结闸门阈值 | pending (thresholds.yaml 未冻结) |

## 11. Known Limitations / 风险留痕
- **RHINO-style rotated DETR missing**：C1/B host 缺失，待裁示；未用 ARS-DETR 替代；不阻塞 D2；B-MVE-0/1 未启动。
- **SODA-A / ICDAR-MLT dataset missing（监督 006 裁示）**：当前非 Bench-Core 阻塞项，不下载/不改路径/不停工；保留为 missing dataset risk；如 full coverage 需声明覆盖，再由合作者提供路径或裁示排除。
- **synthetic prediction 声明**：当前 prediction 由 GT + 可控 score/angle 扰动生成，is_synthetic=true / not_detector_output=true；NRC/risk 非任何真实 detector 性能。
- **A4 hybrid-host frozen snapshot pending**：A-gate-1 未可执行。
- **thresholds.yaml 未冻结**：所有 bucket/score/risk 输出为 dry-run/sanity，无 gate 结论 (R8)。
- background source 为受控抽样；GV-obliquity 用受控样本（非全量）；NRC-AUC 用 synthetic risk。
- angle_version: DOTA/DIOR/FAIR1M le90 由 poly 推导，HRSC mbox le90 等价未核验（对 GV 无影响）。

## 12. Remaining Blockers / 下一步
- eval readiness blockers: ['B_C1_thresholds', 'A_A4_thresholds', 'D2_thresholds', 'freeze_time_set', 'responsible_role_filled', 'rhino_host', 'a4_hybrid_host', 'soda_a_icdar_mlt_datasets', 'real_prediction_available', 'angle_version_certain', 'training_approval']
- training_allowed=False; reasons=['thresholds not frozen', 'RHINO missing', 'A4 host pending', 'real predictions not yet formal', 'human approval required']
Estimated next actions:
1. 阈值冻结：各责任角色提交 B/C1、A/A4、D2 阈值与统计检验，写 thresholds.yaml 并设 freeze_time。
2. RHINO host 裁示（下载/训练/补充/批准替代）；A4 frozen host 提供后跑 A-gate-1。
3. 接真实 detector predictions（03_collect_predictions）替换 dry-run score / synthetic risk。
4. GV-obliquity / source 全量化（CPU 并行）；补 SODA-A / ICDAR-MLT 路径裁示。
5. angle_version le90 符号一致性核验后再做 angle-error gate。
