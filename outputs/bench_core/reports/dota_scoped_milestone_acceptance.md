# DOTA-Scoped Milestone Acceptance

> 2026-06-27 21:18:21 CST

## 验收结论: **PASS within frozen DOTA scope**

- **milestone_verdict**: PASS within frozen DOTA scope
- **D2_formal_status**: partial_frozen DOTA (3-detector) PASS
- **RHINO_host_status**: trained+frozen, mAP 0.7201, sha256 55a90abbace42927
- **O2RTDETR_A4_host_status**: trained+frozen, mAP 0.6497, sha256 3e32fa11114ced82
- **C1_formal_audit**: formal_pass (augmentation-view scope only)
- **A4_formal_audit**: formal_pass (same-host source-attribution scope)
- **thresholds_sha256**: b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae
- **freeze_status**: partial_frozen_dota_d2+host_orientation_gates+c1_a4_formal_thresholds
- **dcal_daudit_disjoint**: True (deterministic md5 split; verified)
- **tests**: 156 passed

## 正式报告路径
- dota_formal_audit / host_formal_audit / c1_formal_audit / a4_formal_audit / c1_a4_threshold_freeze_record / formal_gate_summary / bench_core_v03_formal_gates (.md/.csv)

## 禁止外推 (NO EXTRAPOLATION)
- **不得**外推到 SODA-A / ICDAR-MLT / HRSC / DIOR / FAIR1M。
- **不得**外推到 genuine physical multi-view。
- **不得**外推到 9-detector full benchmark。
- **不得**外推到跨 host 因果。
- 本验收**仅限** frozen DOTA scope（RHINO C1/B + O2-RTDETR A4），非 full project completion。
