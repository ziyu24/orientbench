# r049-rev2 G2 frozen gate decision

Decision: **REJECT_PEF_METHOD**.

All four DOTA-v1.0 train→val arms completed their standard 12-epoch,
four-GPU schedules and were evaluated from their final `epoch_12.pth` with
frozen AP50/AP75 evaluation.  CONT is the strongest control on both relevant
AP measures.

| arm | AP50 | AP75 |
| --- | ---: | ---: |
| CONT | 0.561 | 0.299 |
| DIRECT_DIST | 0.508 | 0.265 |
| SCALAR_QUALITY | 0.559 | 0.294 |
| PEF | 0.500 | 0.258 |

PEF minus CONT is `-0.061` AP50 and `-0.041` AP75.  This fails the frozen G2
requirements of AP50 delta `>= -0.003` and AP75 gain `>= +0.010`.  Both
failures are decisive before the remaining conjunctive angle-error, native
risk, and bootstrap tests; those tests cannot reverse a failed conjunction.

Consequently G3 and G4 are not run.  This result is internal stop-loss
evidence only and must not enter a manuscript, supplement, appendix or
ablation.  No DOTA-v2.0, SODA-A official test, or old `T_audit` semantic field
was accessed.
