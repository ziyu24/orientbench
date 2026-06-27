# Claim Ledger

> 2026-06-27 21:48:46 CST

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
## 019 full-matrix additions (2026-06-27 21:48:47 CST)
### allowed (qualified by scope)
- DOTA-v1.0/v1.5 上 7 个 detector cell（oriented_rcnn/psc/rtmdet-s/rtmdet-m/RHINO/O2-RTDETR）已跑真实 D2 orientation-reliability metrics（NRC/Risk@90），DOTA formal-compatible（阈值未改）。
### qualified
- full matrix status = **partial**（7 cells / 9 archetypes；新 inference 均 4-GPU world_size=4，无 batch override）。
- 非 DOTA detector 家族多因 env 未安装 blocked_dependency；SODA-A/ICDAR-MLT missing。
### forbidden (unchanged)
- 9-detector matrix complete / all datasets covered（**仍不可宣称**）。
