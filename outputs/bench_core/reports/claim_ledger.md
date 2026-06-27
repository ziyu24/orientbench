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
