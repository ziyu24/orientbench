# Inference Command Plan

> 生成时间: 2026-06-25 23:34:10 CST
> 仅计划，**不执行任何推理**；executable_now=False。

- rows: 75；inference-planned (approval-gated): 59；blocked: 16；any_executable_now: **False**

| baseline_id | model_id | dataset | repo/env | blocked_reason | executable_now |
|---|---|---|---|---|---|
| 1 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.0 | onedl-mmrotate 1.1.1 / env=pcp-obb | (none — inference approval-gated) | False |
| 2 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.5 | onedl-mmrotate 1.1.1 / env=pcp-obb | (none — inference approval-gated) | False |
| 3 | oriented_rcnn_r50_fpn_1x_le90 | DIOR-R | onedl-mmrotate 1.1.1 / env=pcp-obb | (none — inference approval-gated) | False |
| 4 | oriented_rcnn_r50_fpn_1x_le90 | SODA-A | onedl-mmrotate 1.1.1 / env=pcp-obb | blocked_missing_dataset: SODA-A | False |
| 5 | oriented_rcnn_r50_fpn_1x_le90 | FAIR1M-v1.0 | onedl-mmrotate 1.1.1 / env=pcp-obb | (none — inference approval-gated) | False |
| 6 | oriented_rcnn_r50_fpn_3x_le90 | HRSC2016 | onedl-mmrotate 1.1.1 / env=pcp-obb | (none — inference approval-gated) | False |
| 7 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.0 | mmrotate 0.3.4 (LSKNet repo / pcp-obb-soda env) / env=pcp-obb-soda | (none — inference approval-gated) | False |
| 8 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.5 | mmrotate 0.3.4 (LSKNet repo / pcp-obb-soda env) / env=pcp-obb-soda | (none — inference approval-gated) | False |
| 9 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.5 MS | mmrotate 0.3.4 (LSKNet repo / pcp-obb-soda env) / env=pcp-obb-soda | (none — inference approval-gated) | False |
| 10 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DIOR-R | mmrotate 0.3.4 (LSKNet repo / pcp-obb-soda env) / env=pcp-obb-soda | (none — inference approval-gated) | False |
| 11 | oriented_rcnn_lsknet_s_fpn_1x_le90 | SODA-A | mmrotate 0.3.4 (LSKNet repo / pcp-obb-soda env) / env=pcp-obb-soda | blocked_missing_dataset: SODA-A | False |
| 12 | oriented_rcnn_lsknet_s_fpn_1x_le90 | FAIR1M-v1.0 | mmrotate 0.3.4 (LSKNet repo / pcp-obb-soda env) / env=pcp-obb-soda | (none — inference approval-gated) | False |
| 13 | oriented_rcnn_lsknet_s_fpn_3x_le90 | HRSC2016 | mmrotate 0.3.4 (LSKNet repo / pcp-obb-soda env) / env=pcp-obb-soda | (none — inference approval-gated) | False |
| 14 | arsdetr_r50_fpn_36e_le90 | DOTA-v1.0 | ARS-DETR fork mmrotate 0.1.0 / env=ars | (none — inference approval-gated) | False |
| 15 | arsdetr_r50_fpn_36e_le90 | DOTA-v1.5 | ARS-DETR fork mmrotate 0.1.0 / env=ars | (none — inference approval-gated) | False |
| 16 | arsdetr_r50_fpn_36e_le90 | DIOR-R | ARS-DETR fork mmrotate 0.1.0 / env=ars | (none — inference approval-gated) | False |
| 17 | arsdetr_r50_fpn_36e_le90 | SODA-A | ARS-DETR fork mmrotate 0.1.0 / env=ars | blocked_missing_dataset: SODA-A | False |
| 18 | arsdetr_r50_fpn_36e_le90 | FAIR1M-v1.0 | ARS-DETR fork mmrotate 0.1.0 / env=ars | (none — inference approval-gated) | False |
| 19 | arsdetr_r50_fpn_36e_le90 | HRSC2016 | ARS-DETR fork mmrotate 0.1.0 / env=ars | (none — inference approval-gated) | False |
| 20 | rotated_retinanet_psc_r50_fpn_1x_le90 | DOTA-v1.0 | onedl-mmrotate 1.1.1 (PSC components) / env=pcp-obb | (none — inference approval-gated) | False |
| 21 | rotated_retinanet_psc_r50_fpn_1x_le90 | DOTA-v1.5 MS | onedl-mmrotate 1.1.1 (PSC components) / env=pcp-obb | not_applicable: baseline invalid | False |
| 22 | rotated_retinanet_psc_r50_fpn_1x_le90 | DIOR-R | onedl-mmrotate 1.1.1 (PSC components) / env=pcp-obb | (none — inference approval-gated) | False |
| 23 | rotated_retinanet_psc_r50_fpn_1x_le90 | SODA-A | onedl-mmrotate 1.1.1 (PSC components) / env=pcp-obb | blocked_missing_dataset: SODA-A | False |
| 24 | rotated_retinanet_psc_r50_fpn_1x_le90 | FAIR1M-v1.0 | onedl-mmrotate 1.1.1 (PSC components) / env=pcp-obb | (none — inference approval-gated) | False |
| 25 | faa_oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.0 | mmrotate 1.x (Phase-Tiny-OBB) / env=pcp-obb | (none — inference approval-gated) | False |
| 26 | rotated_retinanet_r50_fpn_1x_le90 | DOTA-v1.0 | unknown / env=unknown | (none — inference approval-gated) | False |
| 27 | rotated_retinanet_psc_r50_fpn_loadfrom_le90 | DOTA-v1.0 | onedl-mmrotate 1.1.1 (PSC components) / env=pcp-obb | (none — inference approval-gated) | False |
| 28 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DIOR-R | mmrotate 0.3.4 (LSKNet repo / pcp-obb-soda env) / env=pcp-obb-soda | (none — inference approval-gated) | False |
| 29 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.0 | mmrotate 0.3.4 (LSKNet repo / pcp-obb-soda env) / env=pcp-obb-soda | (none — inference approval-gated) | False |
| 30 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.5 | mmrotate 0.3.4 (LSKNet repo / pcp-obb-soda env) / env=pcp-obb-soda | (none — inference approval-gated) | False |
| 31 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.0 | onedl-mmrotate 1.1.1 / env=pcp-obb | (none — inference approval-gated) | False |
| 32 | rotated_rtmdet_s_fpn_3x_le90 | DOTA-v1.0 | unknown / env=unknown | (none — inference approval-gated) | False |
| 33 | rotated_rtmdet_s_fpn_3x_le90 | DOTA-v1.5 | unknown / env=unknown | (none — inference approval-gated) | False |
| 34 | rotated_rtmdet_s_fpn_9x_le90 | HRSC2016 | unknown / env=unknown | (none — inference approval-gated) | False |
| 35 | strip_rcnn_s_fpn_1x_le90 | DOTA-v1.0 | unknown / env=unknown | (none — inference approval-gated) | False |
| 36 | strip_rcnn_s_fpn_1x_le90 | DOTA-v1.5 | unknown / env=unknown | (none — inference approval-gated) | False |
| 37 | strip_rcnn_s_fpn_3x_le90 | HRSC2016 | unknown / env=unknown | (none — inference approval-gated) | False |
| 38 | rotated_rtmdet_m_fpn_3x_le90 | DOTA-v1.0 | unknown / env=unknown | (none — inference approval-gated) | False |
| 39 | rotated_rtmdet_m_fpn_3x_le90 | DOTA-v1.5 | unknown / env=unknown | (none — inference approval-gated) | False |
| 40 | rotated_rtmdet_m_fpn_9x_le90 | HRSC2016 | unknown / env=unknown | (none — inference approval-gated) | False |
| 41 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.0 | onedl-mmrotate 1.1.1 / env=pcp-obb | (none — inference approval-gated) | False |
| 42 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.5 | onedl-mmrotate 1.1.1 / env=pcp-obb | (none — inference approval-gated) | False |
| 43 | oriented_rcnn_r50_fpn_1x_le90 | HRSC2016 | onedl-mmrotate 1.1.1 / env=pcp-obb | (none — inference approval-gated) | False |
| 44 | arsdetr_r50_fpn_36e_le90 | DIOR-R | ARS-DETR fork mmrotate 0.1.0 / env=ars | (none — inference approval-gated) | False |
| 45 | oriented_rcnn_r50_fpn_1x_le90 | DIOR-R | onedl-mmrotate 1.1.1 / env=pcp-obb | (none — inference approval-gated) | False |
| 46 | rotated_rtmdet_m_fpn_3x_le90 | DIOR-R | unknown / env=unknown | (none — inference approval-gated) | False |
| 47 | strip_rcnn_s_fpn_1x_le90 | DIOR-R | unknown / env=unknown | (none — inference approval-gated) | False |
| 48 | strip_rcnn_s_fpn_1x_le90 | DIOR-R | unknown / env=unknown | (none — inference approval-gated) | False |
| 49 | strip_rcnn_s_fpn_1x_le90 | DIOR-R | unknown / env=unknown | (none — inference approval-gated) | False |
| 50 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.5 | onedl-mmrotate 1.1.1 / env=pcp-obb | (none — inference approval-gated) | False |

说明：每行 needs_prediction_schema_conversion=True（mmrotate pkl→prediction schema）。RHINO/A4 标 blocked_missing_detector；SODA-A/ICDAR-MLT 标 blocked_missing_dataset。推理需合作者批准 (collaborator_decision_form D5) 后方可执行。完整 config/ckpt 路径见 .csv。
