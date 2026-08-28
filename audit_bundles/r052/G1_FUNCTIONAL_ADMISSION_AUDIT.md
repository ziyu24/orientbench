# r052 G1 Functional Admission Audit

## Verdict

`KILL_CMR_IMPLEMENTATION_PRINCIPLE` — normal gated early stop.  G2 was not
started and is permanently unauthorized for this dispatch.

## Frozen input and executed command

- Dataset input: DOTA-v1.0 train only; no validation input was read by the
  formal admission runner.
- Frozen proposal universe:
  `outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/frozen_1024_positive_proposals.json`
  (`N=1024`, SHA-256
  `04c5c7bdbfd6486c99da8165b58e73c52a16a9f60e74e5fd5a967e98c7589def`).
- Formal command:
  `experiments/r052_cmr_admission/run_g1_native_path_admission.sh`
- Result:
  `outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/formal_native_path_admission/result.json`
  (SHA-256 `a605187c2c8af9ad3f2fe46141f20e9353a6f7c62c046fa3fc9e1143170ea01e`).

## Evidence

The frozen manifest itself is exact, unique, and has proposal/class ingress:

| Required invariant | Result |
| --- | --- |
| exact 1,024 proposal records | pass |
| unique immutable proposal UID at frozen ingress | pass |
| proposal/class fields at frozen ingress | pass |
| r052 native `predict_bbox` override | fail |
| detector inference is not the host passthrough | fail |
| joint output transports proposal/class/candidate UIDs | fail |

The dynamic runtime identity check resolved
`R052JointRoIHead.predict_bbox` to `StandardRoIHead.predict_bbox`.  The
only r052 joint invocation is in training `bbox_loss`; therefore the actual
decode/NMS/raw-export path neither consumes posterior-marginal class/full-box
outputs nor transports the required three UID types.  This is the plan's
explicit G1 failure condition; it is not a recoverable environment failure.

## Scope and stop record

- G0 parity completed normally: DOTA train->val identity mAP/AP50
  `0.7061/0.7060`.
- G1's four-GPU smoke and train-only frozen proposal construction completed
  normally before the formal token.
- The formal G1 token completed normally and rejected the implementation.
- G2 four-arm development training, DOTA val development metrics, and any
  additional CMR repair were not run.
- No DOTA-v2.0, SODA-A official test, HRSC semantics, new dataset, frozen
  threshold, or third-party source was touched.
