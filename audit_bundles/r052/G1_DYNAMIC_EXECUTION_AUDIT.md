# r052 G1 dynamic execution audit

The corrected detector-native G1 completed on the new frozen DOTA-v1.0 train-only universe.  The old static token is retained as rejected historical evidence and is not used here.

- Manifest: exactly 1,024 unique proposal UIDs; SHA-256 `7c9bb83126511ad9a0ac0ac6a972295b81aaeb0351ad652781eec53232605dbf`.
- Raw RPN decoded boxes/scores, class/candidate UID derivation, decoded pre-NMS boxes and NMS lineage were exported at runtime.
- Four destructive UID/NMS mutations were rejected.
- Four-GPU dynamic execution covered all 1,024 rows.  Parameter delta was 0.8263%, below 5%.

The final dynamic numerical conjunction failed:

- physical global-theta equivariance median axial delta: `0.531568` (required `<=0.05`);
- cross-proposal q shuffle class likelihood change: `0.0` (required > `1e-6` on at least 95%);
- cross-proposal q shuffle non-theta box posterior change median: `1.862645149230957e-08` (required > `1e-6` on at least 95%).

All other recorded dynamic checks passed, including direct feature conditioning, candidate variance, cyclic index equivariance, relative-q geometry, autograd evidence consumption, detach counterfactual, finiteness, scorer/four-box-component gradients, provenance mutations and parameter delta.

This is a normal completed G1 scientific gate result: `KILL_CMR_IMPLEMENTATION_PRINCIPLE`.  G2 was not started.  No DOTA-v2.0, SODA-A official test, HRSC, DOTA val selection, or other prohibited endpoint was read.

Evidence paths:

- `outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/dynamic_g1_correction_2/summary.json`
- `outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/dynamic_g1_correction_2/parameter_delta.json`
- `outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g1/correction_pre_nms_export_6000_uid_v3_rpn_provenance/uid_mutation_validation.json`
