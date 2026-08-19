# Prospective DIOR-R → HRSC2016 application decision study

The policy was fixed on DIOR-R before HRSC2016 audit outcomes were opened. AP-only selection chose Oriented R-CNN LSKNet-S at full evaluator coverage. The orientation-reliability rule chose Oriented R-CNN R50 at nominal score coverage 0.90. On unlabeled HRSC D_cal predictions, the sealed score quantile mapped to `0.05102584883570671`; no HRSC target GT informed architecture or threshold selection.

On the 98-image sealed HRSC D_audit split, the orientation policy did not improve cross-track tip drift. Mean image-level `d_tip` was 0.0379551 for the AP policy and 0.0399070 for the orientation policy, giving `Delta_cont=-0.00195195` with paired image-bootstrap 95% CI `[-0.00759691, 0.00355364]`. Primary `Z_0.50` risk was zero under both policies, so `Delta_severe=0` with CI `[0,0]`. The q=0.25 sensitivity also favored the AP policy (`Delta=-0.00315841`); q=0.50 and q=1.00 were ties.

Detection utility and the absolute risk constraints survived: AP50 was 0.9980072 versus 0.9986048, orientation eligible matched coverage was 1.0, and its one-sided 95% image-risk UCB was 0.0399528. These facts do not rescue the prespecified benefit gate. The terminal result is `APPLICATION_SHIFT_FAIL`; no target-outcome-dependent endpoint, threshold, coverage, or selector retry is permitted.

The application loss is not the prior rectangle-IoU tolerance estimand. `audit_bundles/r045/axis_drift_vs_iou_tolerance.csv` evaluates `asin(2q/a)` and the frozen `delta_0.75(a)` on the registered aspect-ratio grid and records their numerical non-equivalence without making a new theoretical claim.
