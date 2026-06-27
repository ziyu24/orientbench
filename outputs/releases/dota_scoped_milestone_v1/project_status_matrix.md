# Project Status Matrix

> 2026-06-27 21:18:21 CST

| module | status | scope | evidence | blocking_reason | next_required_action |
|---|---|---|---|---|---|
| baseline inventory | **pass** | DOTA + others (73) | `outputs/bench_core/reports/../../.. inventory` | — | — |
| dataset inventory | **pass** | DOTA/DIOR/HRSC/FAIR1M | `outputs/gt_index` | — | — |
| GT parser | **pass** | mmrotate le90 QuadriBoxes | `scripts/_build_gt_mmrotate.py` | — | — |
| prediction contract | **pass** | 17-field schema | `orientbench/io/predictions.py` | — | — |
| DOTA D2 gate | **partial_pass** | DOTA partial (3 detectors) | `outputs/bench_core/reports/dota_formal_audit` | DOTA-only, 3-detector subset | expand detectors if needed |
| host training RHINO | **pass** | RHINO C1/B, DOTA-v1.0, mAP 0.7201 | `outputs/training/rhino` | — | — |
| host training A4 | **pass** | O2-RTDETR A4, DOTA-v1.5, mAP 0.6497 | `outputs/training/a4_host` | — | — |
| host orientation gate | **pass** | B_C1/A_A4 host orientation | `outputs/bench_core/reports/host_formal_audit` | — | — |
| C1 gate | **partial_pass** | DOTA augmentation-view consistency | `outputs/bench_core/reports/c1_formal_audit` | augmentation-view only (NOT physical multi-view) | genuine multi-view needs new capture |
| A4 gate | **partial_pass** | DOTA same-host source attribution | `outputs/bench_core/reports/a4_formal_audit` | same-host only (NO cross-host causal) | cross-host needs multi-host design + approval |
| threshold freeze | **pass** | D2 + host + C1/A4 (D_cal) | `outputs/bench_core/reports/c1_a4_threshold_freeze_record` | — | — |
| readiness | **partial_pass** | scoped formal true; overall not complete | `outputs/bench_core/reports/readiness_check.md` | — | — |
| missing datasets | **out_of_scope_current** | SODA-A/ICDAR-MLT | `—` | not in current scope | future scope + approval |
| missing full matrix | **not_started** | 9-detector x probe | `—` | not built | future scope + approval |
| genuine physical multi-view | **blocked** | C1 physical multiview | `outputs/bench_core/reports/c1_real_cross_view_availability.md` | no multi-viewpoint capture in datasets | new data acquisition |
| 9-detector matrix | **not_started** | full OrientBench matrix | `—` | not built | future scope + approval |
| cross-dataset generalization | **out_of_scope_current** | DOTA->other | `—` | DOTA-scoped only | future scope + approval |

状态码: pass / partial_pass / blocked / not_started / out_of_scope_current。
**partial_pass = DOTA-scoped 通过，非 full project。**
