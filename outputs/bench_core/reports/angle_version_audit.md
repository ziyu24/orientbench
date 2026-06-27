# angle_version Audit

> 生成时间: 2026-06-25 17:41:55 CST
> 只读 baseline config; 不伪造确定性; unknown 保留 unknown; HRSC mbox 标 uncertain.

- baselines audited: **73**
- angle_version 分布: {'le90': 73}
- source 分布: {'config_scan': 70, 'model_id_suffix': 3}

## Dataset-level GT angle conventions (与 baseline config 分开)
| dataset | gt_angle | certainty | note |
|---|---|---|---|
| DOTA-v1.0/v1.5 | le90_derived_from_poly(cv2.minAreaRect) | derived | poly8 -> minAreaRect; sign convention not asserted le90 |
| DIOR-R | le90_derived_from_corners(cv2.minAreaRect) | derived | robndbox corners -> minAreaRect; raw <angle> retained |
| FAIR1M-v1.0 | le90_derived_from_poly(cv2.minAreaRect) | derived | points polygon -> minAreaRect |
| HRSC2016 | mbox_ang_rad | uncertain | opencv-like radians; le90 equivalence UNVERIFIED |

## Per-baseline (sample, first 12)
| id | model_id | dataset | angle_version | box_type | theta_unit | source |
|---|---|---|---|---|---|---|
| 1 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.0 | le90 | rbox | rad_inferred | config_scan |
| 2 | oriented_rcnn_r50_fpn_1x_le90 | DOTA-v1.5 | le90 | rbox | rad_inferred | config_scan |
| 3 | oriented_rcnn_r50_fpn_1x_le90 | DIOR-R | le90 | rbox | rad_inferred | config_scan |
| 4 | oriented_rcnn_r50_fpn_1x_le90 | SODA-A | le90 | rbox | rad_inferred | config_scan |
| 5 | oriented_rcnn_r50_fpn_1x_le90 | FAIR1M-v1.0 | le90 | rbox | rad_inferred | config_scan |
| 6 | oriented_rcnn_r50_fpn_3x_le90 | HRSC2016 | le90 | rbox | rad_inferred | config_scan |
| 7 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.0 | le90 | unknown | rad_inferred | config_scan |
| 8 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.5 | le90 | unknown | rad_inferred | config_scan |
| 9 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DOTA-v1.5 MS | le90 | unknown | rad_inferred | config_scan |
| 10 | oriented_rcnn_lsknet_s_fpn_1x_le90 | DIOR-R | le90 | unknown | rad_inferred | config_scan |
| 11 | oriented_rcnn_lsknet_s_fpn_1x_le90 | SODA-A | le90 | unknown | rad_inferred | config_scan |
| 12 | oriented_rcnn_lsknet_s_fpn_1x_le90 | FAIR1M-v1.0 | le90 | unknown | rad_inferred | config_scan |

完整逐条见 `angle_version_audit.csv`。theta_unit=rad_inferred 表示由 mmrotate le90/le135/oc 约定推断为弧度，未逐一运行核验。
