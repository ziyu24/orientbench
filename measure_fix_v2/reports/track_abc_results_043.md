# Track A/B/C 结果 (043)

> 2026-06-30 10:12:09 CST。masked well-defined region (ar>=1.6)，D_audit，无目标 GT 调参。Track A = PSC intrinsic phase_mod selection。

| cell | Track | NRC | 95% CI | sig>1 | AURC | Risk@70 |
|---|---|---|---|---|---|---|
| DIOR-R/22 | A_phase_mod_intrinsic | 1.1556 | [1.1147, 1.1928] | True | 1.7728 | 1.607 |
| DIOR-R/22 | B_detection_score | 0.5629 | [0.5442, 0.5812] | False | 1.0871 | 1.364 |
| DIOR-R/22 | C_geometry_selector | 0.3563 | [0.3376, 0.3759] | False | 0.8481 | 1.123 |
| SODA-A/23 | A_phase_mod_intrinsic | 1.1167 | [1.1056, 1.1285] | True | 2.3548 | 2.055 |
| SODA-A/23 | B_detection_score | 0.9823 | [0.9676, 0.998] | False | 2.1574 | 2.065 |
| SODA-A/23 | C_geometry_selector | 0.3893 | [0.3846, 0.395] | False | 1.2866 | 1.642 |
| FAIR1M-v1.0/24 | A_phase_mod_intrinsic | 1.1205 | [1.0841, 1.155] | True | 2.5755 | 2.329 |
| FAIR1M-v1.0/24 | B_detection_score | 0.896 | [0.8662, 0.9294] | False | 2.2197 | 2.333 |
| FAIR1M-v1.0/24 | C_geometry_selector | 0.5185 | [0.5005, 0.5345] | False | 1.6216 | 2.058 |

- **Track A (phase_mod intrinsic) 在 3/3 PSC cell 显著 NRC>1**（CI 下界>1）→ 高 phase_mod（角度码自洽度高）的预测反而朝向误差更大 = **intrinsic 反校准**。
- Track B (detection score) NRC 0.56-0.98（DIOR 不反校准、SODA/FAIR1M 接近 1）。
- Track C (geometry selector) NRC 0.36-0.52（well-calibrated，最佳）。
