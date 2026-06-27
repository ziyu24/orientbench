# Full-Matrix Metrics Summary

> DOTA=formal-compatible(阈值未改); 非 DOTA=cross_dataset_exploratory.

| archetype | dataset | baseline | n_used | median_orient_err° | Risk@70 | Risk@90 | AURC | NRC-AUC | scope |
|---|---|---|---|---|---|---|---|---|---|
| two_stage_oriented_rcnn | DOTA-v1.0 | 1 | 529 | 0.878 | 0.9977 | 1.1773 | 0.8809 | 0.5699 | formal_compatible |
| angle_coder_psc | DOTA-v1.0 | 20 | 361 | 1.004 | 1.4682 | 1.3539 | 1.4275 | 1.0574 | formal_compatible |
| rotated_detr_rhino | DOTA-v1.0 | rhino | 19157 | 1.52 | 1.9513 | 2.0475 | 1.8174 | 0.771 | formal_compatible_locked_host |
| hybrid_encoder_oriented_detr_a4 | DOTA-v1.5 | a4_host | 26613 | 1.771 | 2.0535 | 2.3314 | 1.7887 | 0.5515 | formal_compatible_locked_host |
| two_stage_oriented_rcnn | DOTA-v1.5 | 2 | 26360 | 1.803 | 2.1427 | 2.3603 | 1.9784 | 0.6943 | formal_compatible |
| one_stage_rtmdet | DOTA-v1.5 | 33 | 27916 | 1.902 | 2.184 | 2.4322 | 2.0109 | 0.6263 | formal_compatible |
| one_stage_rtmdet_m | DOTA-v1.5 | 39 | 28413 | 1.763 | 2.0536 | 2.3153 | 1.8953 | 0.6156 | formal_compatible |

- failures: 0 (见 full_matrix_failures.csv)
