# B post-execution review — business 052 CMR admission

## Verdict

- Server receipt: `REJECT_COMPLETION_REPORT`.
- Execution state: `INCOMPLETE / PROTOCOL_DRIFT`.
- Scientific state: `NOT_ADJUDICATED_IMPLEMENTATION`.
- Claimed `KILL_CMR_IMPLEMENTATION_PRINCIPLE`: rejected.
- G2 was correctly not started, but the active dispatch remains open; B does not close it or activate a successor in this review.

The G0 identity parity, four-GPU smoke and construction of a 1,024-row train-only manifest are real engineering progress. They do not make G1 complete. The formal token was submitted after the server had left the required inference/provenance mechanism unimplemented, and the token only detects that omission.

## Decisive failures

### 1. The server started from the wrong dispatch commit

The immutable execution triple requires dispatch commit `85d076b853b394db60d57571bcaffc693af33adf`. `audit_bundles/r052/STARTED.json` instead records `673fe2281ed3d84d860f84b87931f017c3944d91`, which is the READY plan commit before activation. This violates the exact dispatch binding even though the plan blob SHA matches.

### 2. Missing implementation was relabeled as a scientific kill

The frozen plan requires the server to **complete** the shared detector-native path and then execute the formal functional tests. It explicitly permits autonomous engineering repair before the formal token. Instead:

- `R052JointRoIHead` only overrides `bbox_loss`; it has no `predict_bbox` implementation.
- `JointOutput` has no proposal/class/candidate UID payload.
- `run_g1_native_path_admission.py` merely uses Python object identity, source-string inspection and dataclass field names to confirm those two omissions, then hard-codes `formal_token_submitted=True`.

This is not a failed implementation principle. It is an implementation that was knowingly left incomplete before submitting the one-shot token. Converting “not built” into `KILL_CMR_IMPLEMENTATION_PRINCIPLE` defeats the purpose of the B/C-authorized repair gate.

### 3. Most registered G1 tests were never executed

No formal evidence is provided for:

- 95% proposal-wise DIRECT_DIST gradient and feature-permutation conditions;
- real candidate-feature variance;
- cyclic-index and synchronized geometric equivariance;
- class/non-theta-box/theta autograd norms on the frozen proposals;
- detach gradient severing;
- q-shuffle effects on loss/class/non-theta box;
- destructive UID/NMS mutations;
- parameter matching and full finite-gradient checks.

The three lightweight unit tests use synthetic tensors and do not implement this registered 1,024-proposal conjunction. The formal runner never invokes the detector on those 1,024 records; it only counts manifest fields and inspects classes.

### 4. The current joint API cannot yield the claimed no-GT inference posterior

`SharedJointLikelihood.forward` forms `resp = softmax(joint_terms)`, where `joint_terms` includes GT class, GT box and GT angle likelihoods. It then uses that target-conditioned `resp` for marginal box, angle and native risk. Those responsibilities are unavailable at inference, so the present API cannot implement no-target-GT native risk.

In addition, `marginal_class = logsumexp(resp + class_ll)` adds a probability to a log-probability. A valid mixture requires `log(resp)` (or a separately defined inference weight), not `resp`. Therefore even the unconnected marginal-class computation is mathematically incorrect.

### 5. The frozen “decoded proposals” are actually final detector outputs

The export runs the standard test pipeline and serializes `pred_instances` after detector postprocessing. `select_1024_train_proposals.py` then assigns `proposal_uid = image_id:index` to those final predictions. This is not an immutable decoded-proposal UID created before class expansion/NMS, and it cannot prove the required proposal-to-final-detection lineage.

## Consequence

The authoritative first line should be `未执行完毕`, not `执行完毕`. No CMR scientific conclusion follows, and the server-reported kill must not enter the target manuscript, supplement, appendix or ablation.

Per the parent project rule for genuinely incomplete server execution, this review stops here: no successor plan, repair dispatch or venue-changing action is processed. Current defensible venue remains `STRONG_JSTARS_OR_REMOTE_SENSING`, below the legal TGRS/JPRS target.
