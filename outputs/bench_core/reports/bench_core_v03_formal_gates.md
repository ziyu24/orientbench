# Bench-Core v0.3 — Formal Gates (DOTA C1/A4 partial)

> 2026-06-27 21:09:35 CST

## 进展链
- v0.1 dry-run → v0.2 prediction contract → DOTA D2 partial formal audit(3 detector) → host 训练(RHINO/O2-RTDETR) + host orientation gate → C1/A4 formal-readiness → **C1/A4 D_audit formal gate (本轮)**。

## 已冻结 (configs/thresholds.yaml)
- DOTA D2 partial（#1/#20/#32, NRC<=1.0, Spearman<=0.95）。
- host orientation gates（B_C1/A_A4 host）。
- **C1_augmentation_view_consistency**（D_cal 冻结, token 017）。
- **A4_source_attribution**（D_cal 冻结, token 017）。

## 本轮 formal gate 结果（D_audit holdout）
- C1: **formal_pass**（augmentation-view scope only）。
- A4: **formal_pass**（same-host source attribution scope）。

## formal_gate_allowed
- **true_for_frozen_dota_c1_a4_scope_only**（严格限定；范围受限, 非全项目完成）。

## 仍未做（边界）
- genuine physical multi-view C1；跨 host A4 因果；A4 q_i 接入；全 DOTA val；其它数据集(SODA-A/ICDAR-MLT/HRSC)；9-detector 全矩阵。
