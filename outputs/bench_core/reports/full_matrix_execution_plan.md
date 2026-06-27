# Full-Matrix Execution Plan (existing assets)

> 2026-06-27 21:41:39 CST
> 9-archetype x present datasets. existing-assets only; no download/train.

## status counts: {'already_available': 5, 'ready_to_run': 6, 'not_applicable': 14, 'blocked_dependency_not_installed': 15, 'weak_nonformal_blocked_dependency': 10, 'blocked_missing_dataset': 2}

| archetype | family | dataset | baseline | env | env_installed | status | formal_scope |
|---|---|---|---|---|---|---|---|
| two_stage_oriented_rcnn | oriented_rcnn | DOTA-v1.0 | 1 | mr_dev1x | True | **already_available** | formal_compatible |
| two_stage_oriented_rcnn | oriented_rcnn | DOTA-v1.5 | 2 | mr_dev1x | True | **ready_to_run** | formal_compatible |
| two_stage_oriented_rcnn | oriented_rcnn | DIOR-R | 3 | mr_dev1x | True | **ready_to_run** | cross_dataset_exploratory |
| two_stage_oriented_rcnn | oriented_rcnn | HRSC2016 | 6 | mr_dev1x | True | **ready_to_run** | cross_dataset_exploratory |
| two_stage_oriented_rcnn | oriented_rcnn | FAIR1M-v1.0 | 5 | mr_dev1x | True | **ready_to_run** | cross_dataset_exploratory |
| angle_coder_psc | rotated_retinanet_psc | DOTA-v1.0 | 20 | mr_dev1x | True | **already_available** | formal_compatible |
| angle_coder_psc | rotated_retinanet_psc | DOTA-v1.5 | None | mr_dev1x | True | **not_applicable** | formal_compatible |
| angle_coder_psc | rotated_retinanet_psc | DIOR-R | 22 | mr_dev1x | True | **ready_to_run** | cross_dataset_exploratory |
| angle_coder_psc | rotated_retinanet_psc | HRSC2016 | None | mr_dev1x | True | **not_applicable** | cross_dataset_exploratory |
| angle_coder_psc | rotated_retinanet_psc | FAIR1M-v1.0 | 24 | mr_dev1x | True | **ready_to_run** | cross_dataset_exploratory |
| one_stage_rtmdet | rotated_rtmdet | DOTA-v1.0 | 32 | mr_dev1x | True | **already_available** | formal_compatible |
| one_stage_rtmdet | rotated_rtmdet | DOTA-v1.5 | None | mr_dev1x | True | **not_applicable** | formal_compatible |
| one_stage_rtmdet | rotated_rtmdet | DIOR-R | None | mr_dev1x | True | **not_applicable** | cross_dataset_exploratory |
| one_stage_rtmdet | rotated_rtmdet | HRSC2016 | None | mr_dev1x | True | **not_applicable** | cross_dataset_exploratory |
| one_stage_rtmdet | rotated_rtmdet | FAIR1M-v1.0 | None | mr_dev1x | True | **not_applicable** | cross_dataset_exploratory |
| rotated_detr_rhino | RHINO_host | DOTA-v1.0 | rhino | ai4rs_train | True | **already_available** | formal_compatible |
| rotated_detr_rhino | RHINO_host | DOTA-v1.5 | None | ai4rs_train | True | **not_applicable** | formal_compatible |
| rotated_detr_rhino | RHINO_host | DIOR-R | None | ai4rs_train | True | **not_applicable** | cross_dataset_exploratory |
| rotated_detr_rhino | RHINO_host | HRSC2016 | None | ai4rs_train | True | **not_applicable** | cross_dataset_exploratory |
| rotated_detr_rhino | RHINO_host | FAIR1M-v1.0 | None | ai4rs_train | True | **not_applicable** | cross_dataset_exploratory |
| hybrid_encoder_oriented_detr_a4 | O2RTDETR_host | DOTA-v1.0 | None | ai4rs_train | True | **not_applicable** | formal_compatible |
| hybrid_encoder_oriented_detr_a4 | O2RTDETR_host | DOTA-v1.5 | a4_host | ai4rs_train | True | **already_available** | formal_compatible |
| hybrid_encoder_oriented_detr_a4 | O2RTDETR_host | DIOR-R | None | ai4rs_train | True | **not_applicable** | cross_dataset_exploratory |
| hybrid_encoder_oriented_detr_a4 | O2RTDETR_host | HRSC2016 | None | ai4rs_train | True | **not_applicable** | cross_dataset_exploratory |
| hybrid_encoder_oriented_detr_a4 | O2RTDETR_host | FAIR1M-v1.0 | None | ai4rs_train | True | **not_applicable** | cross_dataset_exploratory |
| lsknet_backbone | oriented_rcnn_lsknet_s_fpn | DOTA-v1.0 | 7 | pcp-obb-soda | False | **blocked_dependency_not_installed** | formal_compatible |
| lsknet_backbone | oriented_rcnn_lsknet_s_fpn | DOTA-v1.5 | 8 | pcp-obb-soda | False | **blocked_dependency_not_installed** | formal_compatible |
| lsknet_backbone | oriented_rcnn_lsknet_s_fpn | DIOR-R | 10 | pcp-obb-soda | False | **blocked_dependency_not_installed** | cross_dataset_exploratory |
| lsknet_backbone | oriented_rcnn_lsknet_s_fpn | HRSC2016 | None | pcp-obb-soda | False | **blocked_dependency_not_installed** | cross_dataset_exploratory |
| lsknet_backbone | oriented_rcnn_lsknet_s_fpn | FAIR1M-v1.0 | 12 | pcp-obb-soda | False | **blocked_dependency_not_installed** | cross_dataset_exploratory |
| strip_rcnn | strip_rcnn_s_fpn | DOTA-v1.0 | 35 | unknown | False | **blocked_dependency_not_installed** | formal_compatible |
| strip_rcnn | strip_rcnn_s_fpn | DOTA-v1.5 | 36 | unknown | False | **blocked_dependency_not_installed** | formal_compatible |
| strip_rcnn | strip_rcnn_s_fpn | DIOR-R | 47 | unknown | False | **blocked_dependency_not_installed** | cross_dataset_exploratory |
| strip_rcnn | strip_rcnn_s_fpn | HRSC2016 | None | unknown | False | **blocked_dependency_not_installed** | cross_dataset_exploratory |
| strip_rcnn | strip_rcnn_s_fpn | FAIR1M-v1.0 | None | unknown | False | **blocked_dependency_not_installed** | cross_dataset_exploratory |
| weakly_supervised_h2rbox | h2rbox_v2 | DOTA-v1.0 | 70 | unknown | False | **weak_nonformal_blocked_dependency** | nonformal |
| weakly_supervised_h2rbox | h2rbox_v2 | DOTA-v1.5 | None | unknown | False | **weak_nonformal_blocked_dependency** | nonformal |
| weakly_supervised_h2rbox | h2rbox_v2 | DIOR-R | None | unknown | False | **weak_nonformal_blocked_dependency** | cross_dataset_exploratory |
| weakly_supervised_h2rbox | h2rbox_v2 | HRSC2016 | None | unknown | False | **weak_nonformal_blocked_dependency** | cross_dataset_exploratory |
| weakly_supervised_h2rbox | h2rbox_v2 | FAIR1M-v1.0 | None | unknown | False | **weak_nonformal_blocked_dependency** | cross_dataset_exploratory |
| pseudo_point2rbox | point2rbox_v2 | DOTA-v1.0 | 64 | unknown | False | **weak_nonformal_blocked_dependency** | nonformal |
| pseudo_point2rbox | point2rbox_v2 | DOTA-v1.5 | None | unknown | False | **weak_nonformal_blocked_dependency** | nonformal |
| pseudo_point2rbox | point2rbox_v2 | DIOR-R | None | unknown | False | **weak_nonformal_blocked_dependency** | cross_dataset_exploratory |
| pseudo_point2rbox | point2rbox_v2 | HRSC2016 | None | unknown | False | **weak_nonformal_blocked_dependency** | cross_dataset_exploratory |
| pseudo_point2rbox | point2rbox_v2 | FAIR1M-v1.0 | None | unknown | False | **weak_nonformal_blocked_dependency** | cross_dataset_exploratory |
| rotated_detr_arsdetr_distinct | arsdetr | DOTA-v1.0 | 14 | ars | False | **blocked_dependency_not_installed** | formal_compatible |
| rotated_detr_arsdetr_distinct | arsdetr | DOTA-v1.5 | 15 | ars | False | **blocked_dependency_not_installed** | formal_compatible |
| rotated_detr_arsdetr_distinct | arsdetr | DIOR-R | 16 | ars | False | **blocked_dependency_not_installed** | cross_dataset_exploratory |
| rotated_detr_arsdetr_distinct | arsdetr | HRSC2016 | 19 | ars | False | **blocked_dependency_not_installed** | cross_dataset_exploratory |
| rotated_detr_arsdetr_distinct | arsdetr | FAIR1M-v1.0 | 18 | ars | False | **blocked_dependency_not_installed** | cross_dataset_exploratory |
| all | all | SODA-A | None | - | False | **blocked_missing_dataset** | out_of_scope_current |
| all | all | ICDAR-MLT | None | - | False | **blocked_missing_dataset** | out_of_scope_current |

## 说明
- already_available: 已有真实 prediction schema（5 archetype on DOTA）。
- blocked_dependency_not_installed: 需 pcp-obb-soda/ars/unknown env，未安装（不下载/不安装）。
- weak_nonformal: h2rbox/point2rbox 弱/伪监督，不入 formal angle gate（可 schema smoke）。
- blocked_missing_dataset: SODA-A / ICDAR-MLT 不在 present datasets（仅记录）。
- RHINO 用 locked RHINO host；ARS-DETR 为独立 archetype，**不**替代 RHINO。
- DOTA-v1.0/v1.5 = formal_compatible（不改阈值）；DIOR-R/HRSC/FAIR1M = cross_dataset_exploratory。
