# Full Project Coverage Report

> 2026-06-27 21:52:37 CST

- detector archetypes covered (real metrics): **6** (angle_coder_psc, hybrid_encoder_oriented_detr_a4, one_stage_rtmdet, one_stage_rtmdet_m, rotated_detr_rhino, two_stage_oriented_rcnn)
- datasets covered: **['DOTA-v1.0', 'DOTA-v1.5']** / present ['DIOR-R', 'DOTA-v1.0', 'DOTA-v1.5', 'FAIR1M-v1.0', 'HRSC2016']
- successful cells: **7**; schema cells: 7
- formal-compatible cells (DOTA): 7; exploratory cells: 0
- plan status counts: {'already_available': 5, 'ready_to_run': 6, 'not_applicable': 14, 'blocked_dependency_not_installed': 15, 'weak_nonformal_blocked_dependency': 10, 'blocked_missing_dataset': 2}

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
