# G0 Phase-Score Direct Forensics

Decision: **PASS_RISK_FUNCTIONAL_DEPENDENT**

All positive and negative metrics were computed directly on the same matched rows, `ar>=2.1` mask, endpoints, stable tie order, coverage implementation, and paired resamples. No `2-NRC`, AURC symmetry, reverse-index, re-matching, or new NMS approximation was used.

| Dataset | Seed | Endpoint | NRC phase_mod [scene 95% CI] | Direction | NRC -phase_mod |
|---|---:|---|---:|---|---:|
| DIOR-R | 0 | continuous_angle_error | 1.1998 [1.1645, 1.2358] | REVERSED | 1.1484 |
| DIOR-R | 0 | geometry_normalized_severe_event | 0.9520 [0.8342, 1.0487] | NEAR_RANDOM_OR_UNCERTAIN | 1.5086 |
| DIOR-R | 1 | continuous_angle_error | 1.1931 [1.1534, 1.2300] | REVERSED | 1.1667 |
| DIOR-R | 1 | geometry_normalized_severe_event | 0.9534 [0.8442, 1.0679] | NEAR_RANDOM_OR_UNCERTAIN | 1.5098 |
| DIOR-R | 2 | continuous_angle_error | 1.2032 [1.1653, 1.2410] | REVERSED | 1.1780 |
| DIOR-R | 2 | geometry_normalized_severe_event | 0.9295 [0.8258, 1.0369] | NEAR_RANDOM_OR_UNCERTAIN | 1.5587 |
| SODA-A | 0 | continuous_angle_error | 1.1267 [1.0667, 1.1992] | REVERSED | 1.0933 |
| SODA-A | 0 | geometry_normalized_severe_event | 1.0020 [0.8685, 1.1561] | NEAR_RANDOM_OR_UNCERTAIN | 1.7130 |
| SODA-A | 1 | continuous_angle_error | 1.1281 [1.0696, 1.1812] | REVERSED | 1.1199 |
| SODA-A | 1 | geometry_normalized_severe_event | 1.1683 [1.0247, 1.3350] | REVERSED | 1.5760 |
| SODA-A | 2 | continuous_angle_error | 1.1220 [1.0744, 1.1726] | REVERSED | 1.1245 |
| SODA-A | 2 | geometry_normalized_severe_event | 1.3721 [1.1773, 1.5747] | REVERSED | 1.3923 |
| FAIR1M-v1.0 | 0 | continuous_angle_error | 1.1245 [1.1048, 1.1438] | REVERSED | 1.0362 |
| FAIR1M-v1.0 | 0 | geometry_normalized_severe_event | 1.5938 [1.3435, 1.8553] | REVERSED | 1.1655 |
| FAIR1M-v1.0 | 1 | continuous_angle_error | 1.1256 [1.1029, 1.1491] | REVERSED | 1.0500 |
| FAIR1M-v1.0 | 1 | geometry_normalized_severe_event | 1.2340 [1.0540, 1.4458] | REVERSED | 1.4419 |
| FAIR1M-v1.0 | 2 | continuous_angle_error | 1.1163 [1.0919, 1.1420] | REVERSED | 1.0652 |
| FAIR1M-v1.0 | 2 | geometry_normalized_severe_event | 1.1494 [0.9173, 1.3969] | NEAR_RANDOM_OR_UNCERTAIN | 1.4975 |

## Interpretation

`phase_mod` is stably reverse-ranked for continuous angle error in all nine detector-head-seed units, but its geometry-normalized severe-event direction is not uniformly reversed across datasets/seeds. The scientifically valid statement is therefore risk-functional-dependent. Positive and negative scores share an identical prediction identity; sign changes ranking only. `negative_phase_mod` remains a baseline, not a mechanism or method.

Existing generic claims that `phase_mod` is simply and universally reverse-ranked are superseded. Any candidate-versus-negative claim must be endpoint-specific.
