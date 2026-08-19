# B second interim execution review — r048

- Dispatch: `orientbench-b-r048-p2c-lift-directed-obb-stagea-20260819`
- Reviewed server HEAD: `38c49228f07418712fd06c8f1ad475e047a7d34d`
- Execution verdict: **`INCOMPLETE / IMPLEMENTATION_SIGN_ERROR_AND_PROTOCOL_DRIFT / CONTINUE_SAME_DISPATCH`**
- Scientific verdict: **`PENDING / REJECT_P2C_LIFT_DEVELOPMENT_NOT_ADOPTED`**
- Information wall: **`T_cal NOT READ / T_audit SEMANTICS UNOPENED`**

## Real progress accepted

The replacement is no longer the first endpoint-sign placeholder. It now consumes real HRSC header direction, represents an axial residual on doubled angle, has a residual-conditional three-coefficient pole head, regresses the real normalized centre-to-header vector, implements a direct-S1 von-Mises arm, emits row-level val outputs and reports accuracy, circular error, NLL, Brier, ECE and AUGRC. Three P2C capacity traces and four baseline traces were produced with four-rank DDP. G0 remains accepted, and the tracked access log contains no T_cal or T_audit semantic access.

## Fatal pole-convention inversion

The P2C training target and the probability model use opposite meanings for the pole logit:

1. `pole_logit()` documents its output as `q(s=0 | delta,I)`.
2. `_sheet(phi)` returns `1` for the antipodal sheet. In `p2c_logprob()`, sheet 1 correctly receives `logsigmoid(-logit)` and sheet 0 receives `logsigmoid(logit)`, so a positive logit means sheet 0.
3. `train_v2.py` instead passes `sheet` directly as the target to `binary_cross_entropy_with_logits`. This trains a positive logit for sheet 1 and a negative logit for sheet 0—the exact opposite convention used by decoding, likelihood, confidence and evaluation.

The traces expose the failure mechanism. As pole loss falls toward `0.01–0.03`, reported heading accuracy falls toward `0.13–0.18` and median error approaches 179 degrees. Under a pure antipodal correction, the best observed accuracy implied by the same epoch traces is `0.866913` for p2c_small, `0.848429` for p2c_base and `0.857671` for p2c_wide, rather than the reported common `0.502773`. This does not prove the +0.02 gate passes, but it proves the selected checkpoints and every reported P2C G1 comparison were computed with the wrong decoder semantics. `REJECT_P2C_LIFT_DEVELOPMENT` is therefore not a valid scientific token.

## Additional contract gaps

- The frozen transform set requires horizontal flip, vertical flip and 90/180/270-degree rotations. The dataset samples rotations only; horizontal and vertical transforms are never exercised by the loss.
- Baseline training ignores every augmented view returned by the dataset, while P2C consumes it in the equivariance term. The manuscript statement that all arms used identical augmentation is false.
- `run_formal_revised.sh` omits p2c_small, while `run_g1_val.sh` produces jitter rows for p2c_small rather than the report-selected p2c_base. The committed artifacts therefore cannot be reproduced by the committed entry scripts.
- The first-epoch frozen stop condition was met (all P2C arms below 0.60 while CONCAT exceeded 0.65), but training continued for 30 epochs.
- Required FLOPs, latency, complete command logs, checkpoint manifest/hash/chunks and independent transformation/convention tests are absent. Reported trainable-parameter counts also include unused heads/modules and do not establish capacity parity.

## Required continuation under the same business instruction 048

Do not open r049. Preserve accepted G0 and continue the active r048 dispatch without reading T_cal or T_audit:

1. Make the pole convention identical in proper loss, `p2c_logprob`, Bayes decoding and confidence; add deterministic unit tests for both sheets and an explicit 180-degree inversion mutation.
2. Add tested horizontal/vertical/90/180/270 analytic actions and apply the frozen augmentation contract comparably across P2C and baselines.
3. Make the committed formal and evaluation scripts generate all three declared P2C configurations, the selected candidate's jitter table and all four baselines from clean output directories. Deliver commands/logs, true trained-parameter counts, FLOPs/latency and checkpoint hashes or chunks.
4. Re-run G1 from clean initialization and obey the original first-epoch stop. Only a valid, convention-consistent G1 failure may close before T_cal; only a full G1 pass may evaluate the single frozen candidate and all baselines once on T_cal.

The venue remains **strong JSTARS / Remote Sensing**, below the TGRS-or-better target. This run supplies neither a valid negative result nor a venue upgrade.
