# r049-rev2 repaired G2 decision

Status: **REJECT_PEF_METHOD**.  The repaired PEF passed G1 implementation
admission, then all four G2 DOTA-v1.0 train-to-val arms completed their frozen
12-epoch four-GPU schedules and were exported from the final epoch only.

| arm | mAP | AP50 | AP75 | AR>=2.1 angle MAE | AUGRC | Risk@70 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| CONT | 0.4171 | 0.5450 | 0.2900 | 1.8581 | 0.009795 | 0.019692 |
| DIRECT_DIST | 0.3155 | 0.4590 | 0.1720 | 6.4672 | 0.035729 | 0.072349 |
| SCALAR_QUALITY | 0.4101 | 0.5350 | 0.2850 | 1.8448 | 0.009786 | 0.019719 |
| PEF | 0.4137 | 0.5450 | 0.2820 | 1.9419 | 0.009659 | 0.019360 |

CONT is the frozen strongest control. PEF fails the required mAP tolerance
(`-0.0034`), AP75 gain (`-0.0080`), angle-error reduction (`-4.51%`), and both
15% risk-reduction requirements (AUGRC `+1.39%`, Risk@70 `+1.69%`).  The
mother-image bootstrap CIs include zero: AUGRC `[-0.000104, 0.000424]` and
Risk@70 `[-0.000283, 0.001183]`.

Therefore G3 and G4 were not run. This is an internal early-stop record only:
the rejected method and these negative results must not enter the target paper,
supplement, appendix, or ablation tables. No DOTA-v2.0, SODA-A official test,
or old `T_audit` semantic field was accessed.

Authoritative machine decision:
`outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/g2_rotated_grid/metrics/gate_dota_psc_repaired.json`.
