# Metrics 025 (cross-dataset full-val: psc/rtmdet/LSKNet)

> raw+schema in SCRATCH; project manifests. ALL exploratory; thresholds unchanged.

| dataset | baseline | detector | n_pred | n_used | med_err° | Risk@90 | NRC-AUC |
|---|---|---|---|---|---|---|---|
| DIOR-R | 22 | rotated_retinanet_psc | 30586 | 23362 | 0.725 | 1.6638 | 0.5494 |
| DIOR-R | 61 | rotated_rtmdet_s | 34255 | 28583 | 1.116 | 1.7448 | 0.4274 |
| DIOR-R | 10 | oriented_rcnn_lsknet | 40640 | 29363 | 1.102 | 1.8226 | 0.5294 |
| FAIR1M-v1.0 | 24 | rotated_retinanet_psc | 94363 | 32100 | 1.724 | 2.5463 | 1.0825 |
| FAIR1M-v1.0 | 12 | oriented_rcnn_lsknet | 94432 | 53400 | 1.8 | 2.4445 | 0.8256 |
| SODA-A | 23 | rotated_retinanet_psc | 355270 | 224991 | 1.441 | 2.5956 | 1.2596 |
| SODA-A | 11 | oriented_rcnn_lsknet | 383697 | 273498 | 1.545 | 2.5561 | 0.7632 |
