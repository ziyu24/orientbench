# Final Matrix Summary (029)

> 2026-06-28 18:19:03 CST
> 全 detector×dataset 真实完成 cell 汇总。DOTA=formal-compatible(阈值未改)；非 DOTA=exploratory。

## detector coverage per dataset
| dataset | #detectors | detectors |
|---|---|---|
| DIOR-R | 6 | ars_detr, oriented_rcnn, oriented_rcnn_lsknet, rotated_retinanet_psc, rotated_rtmdet_s, strip_rcnn |
| DOTA-v1.0 | 6 | h2rbox_v2, oriented_rcnn, oriented_rcnn_lsknet, rhino_rotated_detr, rotated_retinanet_psc, strip_rcnn |
| DOTA-v1.5 | 4 | o2_rtdetr_hybrid_encoder, oriented_rcnn, rotated_rtmdet_m, rotated_rtmdet_s |
| FAIR1M-v1.0 | 3 | oriented_rcnn, oriented_rcnn_lsknet, rotated_retinanet_psc |
| HRSC2016 | 1 | oriented_rcnn_lsknet |
| SODA-A | 3 | oriented_rcnn, oriented_rcnn_lsknet, rotated_retinanet_psc |

## completed cells: **23**

| dataset | baseline | detector | NRC-AUC | med_err° | scope |
|---|---|---|---|---|---|
| DIOR-R | 16 | ars_detr | 0.9985 | 4.264 | cross_dataset_exploratory |
| DIOR-R | 3 | oriented_rcnn | 0.5212 | 1.062 | cross_dataset_exploratory |
| DIOR-R | 10 | oriented_rcnn_lsknet | 0.5294 | 1.102 | cross_dataset_exploratory |
| DIOR-R | 22 | rotated_retinanet_psc | 0.5494 | 0.725 | cross_dataset_exploratory |
| DIOR-R | 61 | rotated_rtmdet_s | 0.4274 | 1.116 | cross_dataset_exploratory |
| DIOR-R | 47 | strip_rcnn | 0.5061 | 1.181 | cross_dataset_exploratory |
| DOTA-v1.0 | 70 | h2rbox_v2 | 0.7602 | 1.871 | weak_nonformal_metrics |
| DOTA-v1.0 | 1 | oriented_rcnn | 0.5699 | 0.878 | formal_compatible |
| DOTA-v1.0 | 7 | oriented_rcnn_lsknet | 0.7138 | 1.456 | formal_compatible |
| DOTA-v1.0 | rhino | rhino_rotated_detr | 0.771 | 1.52 | formal_compatible_locked_host |
| DOTA-v1.0 | 20 | rotated_retinanet_psc | 1.0574 | 1.004 | formal_compatible |
| DOTA-v1.0 | 35 | strip_rcnn | 0.7167 | 1.499 | formal_compatible |
| DOTA-v1.5 | a4_host | o2_rtdetr_hybrid_encoder | 0.5515 | 1.771 | formal_compatible_locked_host |
| DOTA-v1.5 | 2 | oriented_rcnn | 0.6943 | 1.803 | formal_compatible |
| DOTA-v1.5 | 39 | rotated_rtmdet_m | 0.6156 | 1.763 | formal_compatible |
| DOTA-v1.5 | 33 | rotated_rtmdet_s | 0.6263 | 1.902 | formal_compatible |
| FAIR1M-v1.0 | 5 | oriented_rcnn | 0.845 | 1.9 | cross_dataset_exploratory |
| FAIR1M-v1.0 | 12 | oriented_rcnn_lsknet | 0.8256 | 1.8 | cross_dataset_exploratory |
| FAIR1M-v1.0 | 24 | rotated_retinanet_psc | 1.0825 | 1.724 | cross_dataset_exploratory |
| HRSC2016 | 13 | oriented_rcnn_lsknet | 0.8068 | 5.875 | cross_dataset_exploratory |
| SODA-A | 4 | oriented_rcnn | 0.8323 | 1.731 | cross_dataset_exploratory |
| SODA-A | 11 | oriented_rcnn_lsknet | 0.7632 | 1.545 | cross_dataset_exploratory |
| SODA-A | 23 | rotated_retinanet_psc | 1.2596 | 1.441 | cross_dataset_exploratory |

## 口径
- DOTA scoped milestone=pass；DOTA 9-archetype=pass。cross_dataset_matrix=**partial/exploratory（多 detector，多 dataset）**。
- full_project_complete=**false**。formal claims only frozen DOTA scope。non-DOTA all exploratory。ARS-DETR≠RHINO。
