# Final Claim Ledger: Reduced Scope 054

## Allowed claims

- Within-cell conformal orientation risk control is supported on 052 full real matched tables under frozen D_cal / D_audit.
- Orientation reliability benchmark / analysis is supported as a measurement framework for OBB angle reliability.
- P1 provides partial evidence that mAP does not fully characterize orientation reliability.
- Shift audit reports degradation behavior without claiming strict shifted-distribution validity.
- Artifact-governed reproducibility is supported through persistent artifacts, manifest, sha256, verifier scripts and explicit data paths.

## Qualified claims

- NRC / AURC / Risk@70 / Risk@90 provide reliability signals not fully reflected by mAP in the analyzed settings; they are not claimed to be strictly independent from mAP.
- Geometry-aware selector can be discussed as an analysis score or candidate score, but not as a validated deployable method.
- PSC phase_mod can be discussed as a mechanism candidate, not as a proven causal mechanism.
- DOTA #20 can be discussed as a real Track A negative-control cell, not as public leaderboard validation.
- Downstream utility remains unresolved because the 053 rIoU-drop task failed.

## Forbidden claims

- P3 method-success claim.
- Readiness for a broader top-tier venue.
- PSC mechanism proof.
- Downstream utility proof.
- Full project completion claim.
- Strict independence between NRC and mAP.
- Detector leaderboard or DOTA public mAP claim.
- Conformal risk control as an ordinary selection score.
- Distribution-shift strict conformal guarantee.

## Negative results

- P1 = partial: angle risk changes strongly, but mAP@0.5 also responds strongly.
- P3 = partial: only 1/3 PSC free mechanism tests support the mechanism line.
- P4 = partial: TTA circular variance remains competitive; geometry-aware selector does not stably win.
- P5 = fail: angle-induced rIoU drop task does not show reliable downstream risk reduction.

## Future work

- Identify downstream tasks where angle reliability is directly tied to operational cost.
- Extend conformal risk control to principled shift-aware or covariate-shift settings.
- Revisit PSC mechanism only after a separately approved intervention design.
- Add stronger uncertainty artifacts only when they are real detector outputs and can be persisted with manifest and sha256.
