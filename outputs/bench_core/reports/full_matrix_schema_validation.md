# Full-Matrix Schema Validation

> cells=10; all is_synthetic=false, not_detector_output=false.

| archetype | dataset | baseline | detector | n_pred | schema_ok |
|---|---|---|---|---|---|
| two_stage_oriented_rcnn | DOTA-v1.0 | 1 | oriented_rcnn | 921 | 921 |
| angle_coder_psc | DOTA-v1.0 | 20 | rotated_retinanet_psc | 2428 | 2428 |
| rotated_detr_rhino | DOTA-v1.0 | rhino | rhino_rotated_detr | 300000 | 300000 |
| hybrid_encoder_oriented_detr_a4 | DOTA-v1.5 | a4_host | o2_rtdetr_hybrid_encoder | 180000 | 180000 |
| two_stage_oriented_rcnn | DOTA-v1.5 | 2 | oriented_rcnn | 37508 | 37508 |
| one_stage_rtmdet | DOTA-v1.5 | 33 | rotated_rtmdet_s | 91051 | 91051 |
| one_stage_rtmdet_m | DOTA-v1.5 | 39 | rotated_rtmdet_m | 79394 | 79394 |
| lsknet_backbone | DOTA-v1.0 | 7 | oriented_rcnn_lsknet | 28818 | 28818 |
| strip_rcnn | DOTA-v1.0 | 35 | strip_rcnn | 30395 | 30395 |
| weakly_supervised_h2rbox | DOTA-v1.0 | 70 | h2rbox_v2 | 86446 | 86446 |
