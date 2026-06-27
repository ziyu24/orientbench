# Cross-Dataset Execution Plan 021

> 2026-06-27 22:34:45 CST
> env solved in 020; cross-dataset blocker = GT availability/angle, not env.

| dataset | archetype | baseline | env | status | note |
|---|---|---|---|---|---|
| HRSC2016 | lsknet_backbone | 13 | ai4rs_train(reuse) | **already_run** | real OBB GT(xml); angle_uncertain |
| HRSC2016 | oriented_rcnn | 6 | mr_dev1x | **ready_to_run** | not run this batch (representative=lsknet) |
| DIOR-R | oriented_rcnn | 3 | mr_dev1x | **blocked_missing_obb_gt** | images present; obb annfiles empty (only HBB xml) |
| DIOR-R | lsknet_backbone | 10 | ai4rs_train(reuse) | **blocked_missing_obb_gt** | same |
| FAIR1M-v1.0 | oriented_rcnn | 5 | mr_dev1x | **blocked_missing_gt** | split_ss_fair1m1.0 absent; val_20 annfiles empty |
| ALL | point2rbox_v2 | 64 | - | **weak_nonformal_blocked_network** | network download in __init__ |
| ALL | arsdetr | - | none(0.1.0) | **blocked_dependency** | mmrotate 0.1.0 no env; NOT RHINO substitute |

- HRSC2016 唯一有真实 OBB GT 的跨数据集（XML mbox）→ 已跑 exploratory（angle_uncertain）。
- DIOR-R/FAIR1M GT 缺失 → blocked。SODA-A/ICDAR-MLT missing。point2rbox/ARS-DETR 保持 blocked。
