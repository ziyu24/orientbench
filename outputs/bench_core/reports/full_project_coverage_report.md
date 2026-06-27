# Full Project Coverage Report

> 2026-06-27 22:14:33 CST

- detector archetypes covered (real metrics): **9** (angle_coder_psc, hybrid_encoder_oriented_detr_a4, lsknet_backbone, one_stage_rtmdet, one_stage_rtmdet_m, rotated_detr_rhino, strip_rcnn, two_stage_oriented_rcnn, weakly_supervised_h2rbox)
- datasets covered: **['DOTA-v1.0', 'DOTA-v1.5']** / present ['DIOR-R', 'DOTA-v1.0', 'DOTA-v1.5', 'FAIR1M-v1.0', 'HRSC2016']
- successful cells: **10**; schema cells: 10
- formal-compatible cells (DOTA): 10; exploratory cells: 0
- plan status counts: {'already_available': 8, 'ready_to_run': 11, 'not_applicable': 21, 'weak_nonformal_blocked_dependency': 5, 'blocked_dependency_not_installed': 5, 'blocked_missing_dataset': 2}

## blockers
- dependency: LSKNet(pcp-obb-soda)/ARS-DETR(ars)/strip/point2rbox/h2rbox(unknown) envs not installed
- missing datasets: ['SODA-A', 'ICDAR-MLT']
- angle: HRSC angle uncertain (not run this batch); weak/pseudo: h2rbox/point2rbox -> weak_nonformal
- OOM: none (all 4-GPU cells healthy, no OOM); config mismatch: none in run cells

## 口径
- DOTA scoped milestone = **pass**；full project complete = **false**；full matrix status = **partial**；training_needed_now = **false**。
## next minimum actions
- install/register LSKNet/ARS-DETR/Strip/point2rbox/h2rbox envs (needs approval; this round forbidden)
- run DIOR-R/HRSC/FAIR1M exploratory cells for available-env detectors
- resolve HRSC angle convention before any HRSC angle gate
- acquire SODA-A/ICDAR-MLT datasets (out of scope)
