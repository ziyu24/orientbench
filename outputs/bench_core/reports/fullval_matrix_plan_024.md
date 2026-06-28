# Full-Val Matrix Plan 024

> 2026-06-28 10:21:30 CST
> full-val priority: DIOR/FAIR1M/SODA/HRSC. raw/schema->SCRATCH; project keeps manifest.

| dataset | detector | baseline | status | note |
|---|---|---|---|---|
| DOTA-v1.0 | orcnn/psc/rtmdet/RHINO/lsknet/strip/h2rbox | - | **already_available** | 9-archetype done (DOTA scope) |
| DOTA-v1.5 | orcnn/rtmdet/A4 | - | **already_available** | done |
| DIOR-R | oriented_rcnn | 3 | **ready_to_run_fullval** | full-val running |
| DIOR-R | rotated_retinanet_psc | 22 | **ready_to_run** | subset done; fullval pending |
| DIOR-R | rotated_rtmdet_s | 61 | **ready_to_run** | subset done |
| DIOR-R | oriented_rcnn_lsknet | 10 | **needs_adapter** | class-map adapter (20cls); ckpt head matches |
| DIOR-R | strip_rcnn | 47 | **needs_adapter** | class-map adapter (20cls) |
| FAIR1M-v1.0 | oriented_rcnn | 5 | **ready_to_run_fullval** | full-val running |
| FAIR1M-v1.0 | rotated_retinanet_psc | 24 | **ready_to_run** | subset done |
| FAIR1M-v1.0 | oriented_rcnn_lsknet | 12 | **needs_adapter** | class-map adapter (37cls) |
| SODA-A | oriented_rcnn | 4 | **ready_to_run_fullval** | full-val running |
| SODA-A | rotated_retinanet_psc | 23 | **ready_to_run** | subset done |
| SODA-A | oriented_rcnn_lsknet | 11 | **needs_adapter** | class-map adapter (9cls) |
| HRSC2016 | oriented_rcnn_lsknet | 13 | **already_available** | test split done (angle uncertain) |
| HRSC2016 | rotated_rtmdet_s | 34 | **ready_to_run** | HRSC native farm |
| ALL | arsdetr | - | **needs_env** | isolated mmrotate 0.1.0 env; independent_archetype; NOT_RHINO |
| ALL | point2rbox_v2 | 64 | **needs_download** | offline init weight to scratch + patch clone; weak_nonformal |

- ready_to_run_fullval: orcnn DIOR/FAIR1M/SODA full-val（running，4-GPU，raw->scratch）。
- needs_adapter: lsknet/strip cross-dataset 用 class-map adapter（ckpt head 已匹配数据集 num_classes，不假改 head）。
- needs_env: ARS-DETR 隔离 0.1.0 env（independent_archetype, NOT_RHINO）。needs_download: point2rbox 离线 init 权重（weak_nonformal）。
