# r049-rev2 superseded G2 engineering record

Status: **NOT_ADJUDICATED_IMPLEMENTATION**.  This is not a scientific gate
decision and must not be used to reject the repaired PEF method.

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

PEF minus CONT is `-0.061` AP50 and `-0.041` AP75.  The historical source
implementation was subsequently rejected because it did not implement the
frozen per-candidate field and did not export q/native risk at inference.
Consequently these numbers are retained only as engineering evidence.

G3 and G4 remain unrun.  After repaired G1 admission, all four G2 arms must
be rerun before any scientific decision.  No DOTA-v2.0, SODA-A official test,
or old `T_audit` semantic field was accessed.
