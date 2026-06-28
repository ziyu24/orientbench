# Claim Ledger

> 2026-06-27 22:15:09 CST

## allowed_claims
- DOTA-scoped C1 augmentation-view consistency passed frozen D_audit formal gate.
- DOTA-scoped A4 same-host source-attribution passed frozen D_audit formal gate.
- DOTA D2 partial frozen gate (3 detectors) passed.
- Host checkpoints (RHINO 55a90abb, O2-RTDETR 3e32fa11) are locked and hash-recorded.
- Thresholds for D2/host/C1/A4 are frozen from D_cal; D_audit was holdout only.

## qualified_claims
- C1 is augmentation-view consistency, NOT genuine physical multi-view.
- A4 attribution is same-host statistical source attribution, NOT cross-host causality.
- All results are DOTA-scoped (RHINO DOTA-v1.0, O2-RTDETR DOTA-v1.5).
- C1/A4 are partial_pass at project level; full project gate is incomplete.

## forbidden_claims (MUST NOT appear in any formal report)
- OrientBench full benchmark complete.
- C1 genuine physical multi-view solved.
- A4 proves causal source attribution across models.
- 9-detector matrix complete.
- All datasets covered.
- ARS-DETR substituted RHINO.

---
## 020 env-unblock additions (2026-06-27 22:15:11 CST)
### allowed (qualified)
- LSKNet / Strip R-CNN / h2rbox_v2 经 reuse(ai4rs_train, 0.3.4 ckpt 完整加载入 ai4rs 1.x) 跑通真实 4-GPU inference，DOTA-v1.0 D2 metrics（LSKNet NRC 0.71 / Strip 0.72 / h2rbox 0.76）。
### qualified
- h2rbox 为弱监督，标 weak_nonformal_metrics（非 formal angle gate）。full matrix = 9/9 archetype 真实覆盖（除 point2rbox 网络阻塞 + ARS-DETR 0.1.0 无 env）。
- 未创建新 env，未安装依赖（reuse-first）。
### forbidden (unchanged)
- 9-detector matrix complete / all datasets covered（仍不可宣称；ARS-DETR/point2rbox 未跑，非 DOTA 未跑）。

---
## 021 cross-dataset exploratory (2026-06-27 22:36:45 CST)
### allowed (qualified)
- HRSC2016 LSKNet exploratory: mAP sanity 0.906（与 baseline 一致），D2 orientation-reliability NRC 0.81 / med_err 5.9°（**exploratory only**）。
### qualified
- HRSC angle_error_gate_status=blocked_angle_uncertain（mbox→le90 未正式证明）；全部 cross-dataset exploratory，不冻结、非 formal。
- DIOR-R blocked_missing_obb_gt（仅 HBB）；FAIR1M blocked_missing_gt（标注空/路径缺）；env 非阻塞（020 已解）。
### forbidden (unchanged)
- cross-dataset formal gate / all datasets covered / ARS-DETR=RHINO（仍不可宣称）。

---
## 022 cross-dataset GT correction + real runs (2026-06-27 23:49:17 CST)
### corrected (021 error fixed)
- 021 误判 DIOR-R/FAIR1M blocked_missing_gt、SODA-A missing_dataset = **错误**（扩展名/路径/递归不足）。022 递归重扫: DIOR OBB=annfiles/obb robndbox XML、FAIR1M OBB=val_20 points XML、SODA-A present(dota_format_tiled_ss) — 真实 OBB GT 均找到。
### allowed (qualified, exploratory)
- DIOR-R/FAIR1M/SODA-A/HRSC2016 真实 4-GPU inference + exploratory D2 metrics（NRC: DIOR 0.52, FAIR1M 0.86, SODA 0.84, HRSC 0.81）。**全部 cross_dataset_exploratory，非 formal，阈值未变。**
### forbidden (unchanged)
- cross-dataset formal gate / all datasets covered / 9-detector matrix complete / ARS-DETR=RHINO（仍不可宣称）。

---
## 023 cross-dataset multi-detector (2026-06-28 00:13:04 CST)
### allowed (qualified, exploratory)
- 8 cross-dataset cells（DIOR-R orcnn/psc/rtmdet, FAIR1M orcnn/psc, SODA-A orcnn/psc, HRSC lsknet）真实 4-GPU + exploratory D2 metrics。
- 观察(exploratory): PSC angle-coder 在 FAIR1M/SODA NRC>1.0（选择弱于 random），与 DOTA psc 一致——跨数据集模式。
### qualified
- 全 cross_dataset_exploratory；非 formal；阈值未变。DIOR/FAIR1M/SODA 用受控 subset（非静默，已记 fullval_status）。
- 032/C5/source-teacher = **本轮明确忽略**（错误 thread/stage）。
### forbidden (unchanged)
- cross-dataset formal gate / all datasets covered / 9-detector matrix complete / ARS-DETR=RHINO（仍不可宣称）。

---
## 024 full-val + storage (2026-06-28 10:58:48 CST)
### allowed (qualified, exploratory)
- DIOR-R/FAIR1M/SODA-A orcnn **full-val** 真实 4-GPU + exploratory D2 metrics（NRC 0.52/0.84/0.83，consistent with subset）。raw+schema 在 SCRATCH，project 仅 manifest/sha256/metrics。
### qualified
- 全 cross_dataset_exploratory；非 formal；阈值未变。ARS-DETR=needs_env(独立 archetype, NOT RHINO)；point2rbox=needs_download(weak_nonformal)；lsknet/strip cross-dataset=needs_adapter。
### forbidden (unchanged)
- cross-dataset formal gate / all datasets covered / 9-detector matrix complete / ARS-DETR=RHINO（仍不可宣称）。

---
## 025 unlock + full-val (2026-06-28 12:04:12 CST)
### allowed (qualified, exploratory)
- ARS-DETR 隔离 env 建成并 DOTA-v1.0 4-GPU 跑通（independent_archetype, NOT RHINO）；LSKNet cross-dataset full-val（DIOR 0.53/FAIR1M 0.83/SODA 0.76）；psc/rtmdet cross-dataset full-val。
### qualified
- 全 exploratory（非 DOTA）/ARS-DETR DOTA exploratory coverage（不改 frozen D2 gate）；阈值未变；point2rbox blocked_download_source_empty(weak_nonformal)。
### forbidden (unchanged)
- ARS-DETR=RHINO / all datasets covered / 9-detector matrix complete / cross-dataset formal gate（仍不可宣称）。
