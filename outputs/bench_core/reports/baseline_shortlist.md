# Baseline Selection Shortlist

> 生成时间: 2026-06-25 23:45:54 CST
> 优先接入 prediction 的最小集合；RHINO 单列 blocked，**不用 ARS-DETR 替代**。

- selected: 6 / rows: 7

| archetype | status | baseline_id | model_id | dataset | why_selected | risks |
|---|---|---|---|---|---|---|
| two_stage_regression | **selected** | 1 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.0 | two-stage angle regression | prediction requires inference (approval-gated) + pkl->schema conversion + angle verify |
| two_stage_strong_backbone | **selected** | 7 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.0 | strong-backbone two-stage | prediction requires inference (approval-gated) + pkl->schema conversion + angle verify |
| one_stage_realtime | **selected** | 32 | rotated_rtmdet_s_fpn_3x_le90 | DOTA-v1.0 | one-stage real-time | prediction requires inference (approval-gated) + pkl->schema conversion + angle verify |
| angle_coder_psc | **selected** | 20 | rotated_retinanet_psc_r50_fpn_1x_le90 | DOTA-v1.0 | PSC angle-coder (angle distribution) | prediction requires inference (approval-gated) + pkl->schema conversion + angle verify |
| detr_like | **selected** | 14 | arsdetr_r50_fpn_36e_le90 | DOTA-v1.0 | DETR-like (ARS-DETR; NOT a RHINO substitute) | prediction requires inference (approval-gated) + pkl->schema conversion + angle verify |
| weak_pseudo | **selected** | 64 | point2rbox_v2_r50_fpn_1x_le90 | DOTA-v1.0 | weak/pseudo supervision | prediction requires inference (approval-gated) + pkl->schema conversion + angle verify |
| rotated_detr_rhino | **blocked_missing** | None | rhino | (C1/B host) | REQUIRED C1/B host but MISSING | must NOT be substituted by ARS-DETR; needs collaborator ruling (download/train/supply) |
