# Final Coverage Matrix

> 2026-06-28 22:14:10 CST

| dataset | #detectors | detectors |
|---|---|---|
| DIOR-R | 6 | ars_detr, oriented_rcnn, oriented_rcnn_lsknet, rotated_retinanet_psc, rotated_rtmdet_s, strip_rcnn |
| DOTA-v1.0 | 6 | h2rbox_v2, oriented_rcnn, oriented_rcnn_lsknet, rhino_rotated_detr, rotated_retinanet_psc, strip_rcnn |
| DOTA-v1.5 | 4 | o2_rtdetr_hybrid_encoder, oriented_rcnn, rotated_rtmdet_m, rotated_rtmdet_s |
| FAIR1M-v1.0 | 3 | oriented_rcnn, oriented_rcnn_lsknet, rotated_retinanet_psc |
| HRSC2016 | 1 | oriented_rcnn_lsknet |
| SODA-A | 3 | oriented_rcnn, oriented_rcnn_lsknet, rotated_retinanet_psc |

- **23 real cells / 6 datasets**. DOTA=formal-compatible(阈值未改); 非 DOTA=exploratory。
- point2rbox final blocked; ARS-DETR DIOR 解锁/FAIR1M·SODA blocked; Strip DIOR 解锁/其它 pattern; HRSC angle resolved。
