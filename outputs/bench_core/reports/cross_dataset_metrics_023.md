# Cross-Dataset Exploratory Metrics 022 (corrected GT discovery)

> ALL exploratory; no formal gate; thresholds unchanged. real OBB GT rediscovered for DIOR-R/FAIR1M/SODA-A.

| dataset | baseline | detector | n_used | median_orient_err° | Risk@90 | NRC-AUC | angle_status |
|---|---|---|---|---|---|---|---|
| HRSC2016 | 13 | oriented_rcnn_lsknet | 240 | 5.875 | 7.1819 | 0.8068 | blocked_angle_uncertain |
| DIOR-R | 3 | oriented_rcnn | 3281 | 1.132 | 1.6932 | 0.5235 | le90_via_quadriboxes_uncertain |
| DIOR-R | 22 | rotated_retinanet_psc | 2659 | 0.857 | 1.6569 | 0.5898 | le90_via_quadriboxes_uncertain |
| DIOR-R | 61 | rotated_rtmdet_s | 3291 | 1.227 | 1.7819 | 0.4435 | le90_via_quadriboxes_uncertain |
| FAIR1M-v1.0 | 5 | oriented_rcnn | 6770 | 1.888 | 2.6035 | 0.8644 | le90_via_quadriboxes_uncertain |
| FAIR1M-v1.0 | 24 | rotated_retinanet_psc | 4261 | 1.731 | 2.4999 | 1.0343 | le90_via_quadriboxes_uncertain |
| SODA-A | 4 | oriented_rcnn | 11890 | 1.963 | 2.8482 | 0.8397 | le90_via_quadriboxes_uncertain |
| SODA-A | 23 | rotated_retinanet_psc | 8239 | 1.686 | 2.6616 | 1.1688 | le90_via_quadriboxes_uncertain |

## 修正 021 错误结论
- DIOR-R: OBB GT = annfiles/obb/*.xml (robndbox 8-corner)；021 只搜 *.txt 故误判 -> 已纠正，real GT 解析成功。
- FAIR1M-v1.0: OBB GT = split/val_20/annfiles/*.xml (points/quad)；021 find 精度 bug 误判 -> 已纠正。
- SODA-A: present；dota_format_tiled_ss/val_tiled DOTA-poly8 直接可用 -> 不再 missing_dataset。
- HRSC angle 仍 blocked_angle_uncertain；其余 angle le90_via_quadriboxes 标 uncertain（exploratory，不冻结）。
