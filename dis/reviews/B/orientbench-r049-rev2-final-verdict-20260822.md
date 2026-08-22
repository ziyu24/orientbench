# B final post-execution verdict — r049 revision 2

## Verdict

- Execution state: `COMPLETED / GATED_SCIENTIFIC_EARLY_STOP`.
- Scientific state: `REJECT_PEF_METHOD`.
- Manuscript use: prohibited; the method and negative result remain internal only.

The repaired implementation materially corrected the prior review: it now builds a separate periodic field for each FPN anchor template, uses candidate-angle-dependent rotated rectangle sampling, makes DIRECT_DIST and SCALAR_QUALITY operative at inference, and completes the four registered 12-epoch/four-GPU arms.

The frozen G2 conjunction fails without relying on the disputed risk export. Relative to CONT, PEF changes AP75 from `0.2900` to `0.2820` (`-0.0080`, versus required `+0.0100`) and increases AR>=2.1 mean angle error from `1.8581` to `1.9419` degrees (`+4.51%`, versus required reduction >=10%). It also misses the mAP tolerance by `0.0004`. These independent detector-output failures are sufficient to reject PEF and prohibit G3/G4.

## Audit reservation

`PEFAngleBranchRetinaHead.predict_by_feat` does not carry the exact pre-NMS `(level, cell, anchor)` identity through decode/NMS. It calls the parent predictor with only the refined angle codes, then reconstructs an approximate source from the final regressed box's area, center and aspect ratio. Consequently the reported `pef_q`, `pef_native_risk` and `pef_original_angle` are not proven to belong to the exact candidate that produced each retained detection. The native-risk AUGRC/Risk@70 and bootstrap numbers are therefore **not accepted as scientific evidence**.

This reservation does not justify another repair or retraining cycle: AP75 and angle error already kill the strict conjunction, and the user explicitly prohibited spending paper space or further resources on negative-result completion. The accepted conclusion is limited to `PEF fails the primary positive method gate`; no native-risk numerical claim is adopted.

## Storage reservation

The 2026-08-20 cleanup had an explicit project-owner authorization to reduce the worktree below 20 GiB, so it is not treated as an unauthorized deletion. Some removed roots contained formal historical evidence rather than mere resume checkpoints; those objects remain recoverable from Git history, but immediate reproducibility from the current worktree is weaker. Future positive-route evidence must retain compact manifests, final raw predictions, metrics and exact provenance even when large checkpoints are pruned.

## Venue and next-route consequence

The current defensible level remains `STRONG_JSTARS_OR_REMOTE_SENSING`, below the legal TGRS-or-better target. r049 is closed and will not be rescued. The next route must change the observation unit from anchor-corner sampling to exact decoded proposals and make cyclic candidate evidence part of proposal likelihood and localization, not merely an auxiliary risk head.
