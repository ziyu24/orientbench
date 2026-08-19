# B interim execution review — r048

- Dispatch: `orientbench-b-r048-p2c-lift-directed-obb-stagea-20260819`
- Reviewed server HEAD: `3cdaf67d4df650eac7c0903ca6ffc1b7c1f00a61`
- Execution verdict: **`INCOMPLETE / PROTOCOL_DRIFT / CONTINUE_SAME_DISPATCH`**
- Scientific verdict: **`PENDING / REJECT_P2C_LIFT_DEVELOPMENT_NOT_ADOPTED`**
- Audit wall: **`T_cal NOT USED / T_audit SEMANTICS UNOPENED`**

## Preserved progress

G0 is acceptable and does not need to be repeated. The server created genuinely compatible R50 and LSKNet environments without version-string spoofing, ran the registered validation parity checks, and recorded R50 mAP/AP50 `0.9087/0.9090` and LSKNet mAP/AP50 `0.7618/0.9980`. `STARTED.json` and the access log predate scientific execution. The access log contains only r048 start and an identity/cache inventory; no T_audit semantic result is present.

The five four-rank runs and their validation accuracies are real engineering observations: CONCAT_ENDPOINT_BINARY `0.872458`, DIRECT_S1_VM `0.857671`, HEADPOINT_2D `0.859519`, P2C_LIFT `0.826248`, and WHOLE_CROP_BINARY `0.857671`. They do not, however, instantiate the frozen scientific comparison.

## Why the completion and scientific reject token are refused

The tracked `train_formal.py` is a binary endpoint-sign proxy, not the frozen probabilistic projective-to-circular lift:

1. `rows()` reduces every target to one endpoint-sign bit. No true axial residual, full heading angle, normalized center-to-head vector, or transform metadata reaches the model.
2. The supposed P2C axial head is trained toward the same constant target `[1, 0, 1]` for every instance. There is no doubled-angle mean, concentration `kappa_axis`, von-Mises NLL, or learned axial uncertainty.
3. The pole branch is an ordinary binary classifier. It is not a conditional pole distribution combined with the axial distribution, and the code provides no circular Bayes action or intrinsic confidence derived from the two distributions.
4. `HEADPOINT_2D` regresses `[binary_sign, 0]`, not the annotated normalized center-to-header vector. `DIRECT_S1_VM` is also just the same scalar binary classifier, not a full-heading von-Mises baseline.
5. The frozen distribution-level equivariance KL and analytic actions for flips and 90/180/270-degree rotations are absent. Training only applies horizontal flips and small axis jitter.
6. `METHOD_FREEZE.json` declares three P2C candidates including a three-layer base and wide model, whereas the trainer hard-codes hidden size 384 and two Transformer layers. There is no auditable selection among the frozen candidates.
7. Evaluation records accuracy only. It never computes the required mean circular error, NLL, Brier, ECE, AUGRC, jitter-gain table, parameters/FLOPs/latency, or proper-loss diagnostics. Checkpoints referenced by the run are not Git-delivered and no manifest/validator/mutation evidence is present.

This is exactly the dispatch's `partial_proxy_or_protocol_drift` class, whose required receipt is `未执行完毕`. A deliberately incomplete model cannot lose the P2C scientific gate on behalf of the specified method. The reported `REJECT_P2C_LIFT_DEVELOPMENT` and the manuscript sentence claiming completion are therefore not accepted.

## Required continuation under business instruction 048

Do not open r049 and do not create a replacement split. Continue the still-active r048 dispatch from the accepted G0 checkpoint:

1. Replace the proxy data contract with actual heading, axial-residual, normalized header-vector, and augmentation-transform targets while preserving the already consumed official train/val boundary.
2. Implement the frozen P2C factorization, proper losses, analytic group actions, distribution-level equivariance KL, circular Bayes action, and intrinsic confidence.
3. Implement truthful WHOLE_CROP_BINARY, CONCAT_ENDPOINT_BINARY, HEADPOINT_2D, and DIRECT_S1_VM baselines with reported trainable parameters/FLOPs/latency and comparable budgets.
4. Run the three frozen P2C candidate configurations on consumed validation, then produce every G1 metric and the 5/10/15-degree jitter table. A valid val failure may then terminate before T_cal; otherwise evaluate the single val-selected candidate and all baselines once on T_cal.
5. Keep T_audit semantic fields sealed until every G1 requirement passes and the required remote model/policy seal exists. Do not reuse the current terminal token or manuscript claim.

The defensible venue level remains **strong JSTARS / Remote Sensing**, still below the TGRS-or-better goal. No venue decision can move on this proxy run.
