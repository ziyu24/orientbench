# Cross-Dataset Multi-Detector Plan 023

> 2026-06-28 00:12:08 CST
> 基于 022 GT discovery + 020 env reuse。status counts: {'already_available': 8, 'blocked_config_mismatch': 4, 'blocked_dependency': 3, 'ready_to_run': 2, 'weak_nonformal': 1}

| dataset | detector | baseline | env | status |
|---|---|---|---|---|
| DIOR-R | oriented_rcnn | 3 | mr_dev1x | **already_available** |
| DIOR-R | rotated_retinanet_psc | 22 | mr_dev1x | **already_available** |
| DIOR-R | rotated_rtmdet_s | 61 | mr_dev1x | **already_available** |
| DIOR-R | oriented_rcnn_lsknet | 10 | ai4rs | **blocked_config_mismatch (no DIOR-class ai4rs lsknet config)** |
| DIOR-R | strip_rcnn | 47 | ai4rs | **blocked_config_mismatch (no DIOR-class ai4rs strip config)** |
| DIOR-R | arsdetr | 16 | none | **blocked_dependency (0.1.0)** |
| FAIR1M-v1.0 | oriented_rcnn | 5 | mr_dev1x | **already_available** |
| FAIR1M-v1.0 | rotated_retinanet_psc | 24 | mr_dev1x | **already_available** |
| FAIR1M-v1.0 | oriented_rcnn_lsknet | 12 | ai4rs | **blocked_config_mismatch** |
| FAIR1M-v1.0 | arsdetr | 18 | none | **blocked_dependency** |
| SODA-A | oriented_rcnn | 4 | mr_dev1x | **already_available** |
| SODA-A | rotated_retinanet_psc | 23 | mr_dev1x | **already_available** |
| SODA-A | oriented_rcnn_lsknet | 11 | ai4rs | **blocked_config_mismatch** |
| SODA-A | arsdetr | 17 | none | **blocked_dependency** |
| HRSC2016 | oriented_rcnn_lsknet | 13 | ai4rs | **already_available** |
| HRSC2016 | rotated_rtmdet_s | 34 | mr_dev1x | **ready_to_run (HRSC native; not run this batch)** |
| HRSC2016 | oriented_rcnn | 6 | mr_dev1x | **ready_to_run** |
| ALL | point2rbox_v2 | 64 | - | **weak_nonformal (network __init__)** |

- mr_dev1x(orcnn/psc/rtmdet via pth_data config+adapter): 真实跑通。
- lsknet/strip cross-dataset: ai4rs 无 matching-class config → blocked_config_mismatch（需 num_classes/classes 适配，未在本轮）。
- ARS-DETR: blocked_dependency（0.1.0 无 env，不替代 RHINO）。point2rbox: weak_nonformal（网络下载）。
