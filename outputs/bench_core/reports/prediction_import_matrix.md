# Prediction Import Matrix

> 生成时间: 2026-06-25 23:34:10 CST
> baseline_id × dataset 状态；不推理；不声称正式 gate。

- rows: 75；status 计数: {'needs_inference': 58, 'blocked_missing_dataset': 8, 'not_applicable': 6, 'convertible_nonformal': 1, 'blocked_missing_detector': 2}
- **ready_schema (importable now): 0**

状态语义: ready_schema=可直接导入; convertible_nonformal=可转换但非正式 gate; needs_inference=有 ckpt 待推理(需批准); blocked_missing_dataset; blocked_missing_detector(RHINO/A4); unsupported; not_applicable(invalid baseline)。

| baseline_id | model_id | dataset | status | reason |
|---|---|---|---|---|
| 1 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 2 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.5 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 3 | oriented_rcnn_r50_fpn_1x_le90 | DIOR-R | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 4 | oriented_rcnn_r50_fpn_1x_le90 | MISSING | **blocked_missing_dataset** | dataset 'SODA-A' missing locally |
| 5 | oriented_rcnn_r50_fpn_1x_le90 | FAIR1M-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 6 | oriented_rcnn_r50_fpn_3x_le90 | HRSC2016 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 7 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 8 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.5 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 9 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.5 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 10 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DIOR-R | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 11 | oriented_rcnn_lsknet_s_fpn_1x_le90 | MISSING | **blocked_missing_dataset** | dataset 'SODA-A' missing locally |
| 12 | oriented_rcnn_lsknet_s_fpn_1x_le90 | FAIR1M-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 13 | oriented_rcnn_lsknet_s_fpn_3x_le90 | HRSC2016 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 14 | arsdetr_r50_fpn_36e_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 15 | arsdetr_r50_fpn_36e_le90 | DOTA-v1.5 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 16 | arsdetr_r50_fpn_36e_le90 | DIOR-R | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 17 | arsdetr_r50_fpn_36e_le90 | MISSING | **blocked_missing_dataset** | dataset 'SODA-A' missing locally |
| 18 | arsdetr_r50_fpn_36e_le90 | FAIR1M-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 19 | arsdetr_r50_fpn_36e_le90 | HRSC2016 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 20 | rotated_retinanet_psc_r50_fpn_1x_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 21 | rotated_retinanet_psc_r50_fpn_1x_le90 | DOTA-v1.5 | **not_applicable** | baseline marked invalid in readme |
| 22 | rotated_retinanet_psc_r50_fpn_1x_le90 | DIOR-R | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 23 | rotated_retinanet_psc_r50_fpn_1x_le90 | MISSING | **blocked_missing_dataset** | dataset 'SODA-A' missing locally |
| 24 | rotated_retinanet_psc_r50_fpn_1x_le90 | FAIR1M-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 25 | faa_oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 26 | rotated_retinanet_r50_fpn_1x_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 27 | rotated_retinanet_psc_r50_fpn_loadfrom_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 28 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DIOR-R | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 29 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 30 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.5 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 31 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 32 | rotated_rtmdet_s_fpn_3x_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 33 | rotated_rtmdet_s_fpn_3x_le90 | DOTA-v1.5 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 34 | rotated_rtmdet_s_fpn_9x_le90 | HRSC2016 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 35 | strip_rcnn_s_fpn_1x_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 36 | strip_rcnn_s_fpn_1x_le90 | DOTA-v1.5 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 37 | strip_rcnn_s_fpn_3x_le90 | HRSC2016 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 38 | rotated_rtmdet_m_fpn_3x_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 39 | rotated_rtmdet_m_fpn_3x_le90 | DOTA-v1.5 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 40 | rotated_rtmdet_m_fpn_9x_le90 | HRSC2016 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 41 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.0 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 42 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.5 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 43 | oriented_rcnn_r50_fpn_1x_le90 | HRSC2016 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 44 | arsdetr_r50_fpn_36e_le90 | DIOR-R | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 45 | oriented_rcnn_r50_fpn_1x_le90 | DIOR-R | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 46 | rotated_rtmdet_m_fpn_3x_le90 | DIOR-R | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 47 | strip_rcnn_s_fpn_1x_le90 | DIOR-R | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 48 | strip_rcnn_s_fpn_1x_le90 | DIOR-R | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 49 | strip_rcnn_s_fpn_1x_le90 | DIOR-R | **needs_inference** | ckpt+config present; inference required (approval-gated) |
| 50 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.5 | **needs_inference** | ckpt+config present; inference required (approval-gated) |
