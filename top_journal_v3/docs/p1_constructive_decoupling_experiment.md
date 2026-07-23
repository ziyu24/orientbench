# P1 constructive decoupling experiment

Generated: 2026-07-02 23:52:37 CST

All perturbation results use 052 real post-NMS schema predictions and GT OBBs; each perturbation is rematched before computing mAP, AP75, NRC, AURC and Risk@k.

Decision: P1 construct validity = partial.

Mean |Delta mAP@0.5| at 30 deg angle perturbation: 0.1810. Mean |Delta angle risk|: 26.4883 degrees. Mean reverse-perturb |Delta mAP@0.5|: 0.1219; mean reverse |Delta angle risk|: 0.7657.

Same-dataset paired mining candidates:

- DIOR-R: DIOR-R/22 vs DIOR-R/61, delta_mAP50=0.1902, delta_NRC=0.0765
- DIOR-R: DIOR-R/3 vs DIOR-R/61, delta_mAP50=0.0867, delta_NRC=0.0705
- DIOR-R: DIOR-R/22 vs DIOR-R/3, delta_mAP50=0.1035, delta_NRC=0.0060

The IoU theory curve is written to `top_journal_v3/figures/iou_delta_theta_aspect_ratio_curve.csv`.
