# B post-execution verdict — r046

- Dispatch: `orientbench-b-r046-ahc-obb-semantic-heading-stagea-20260818`
- Verdict: **`REJECT_EXECUTION_AS_INCOMPLETE_PROTOCOL_DRIFT / SCIENCE_NOT_ADJUDICATED / DO_NOT_START_STAGE_B`**
- Reviewed HEAD: `e591c9963706d64fa91692ab83a0afe791af20b7`

## Execution verdict

B does not accept the server receipt `NO_SAFE_THRESHOLD` as a valid gated scientific completion. The tracked bundle is a mechanics/proxy run rather than the frozen Stage-A experiment, and several deviations directly affect the claimed stopping statistic. Under the frozen completion mapping this is `execution_status=incomplete`, not `complete`.

The decisive defects are:

1. `calibrate_vcal.py` sorts `conf` without applying the same permutation to `err`, then indexes the original error order with indices from the sorted confidence vector. The reported risks `0.19844/0.21491/0.24000` therefore do not correspond to the retained examples.
2. No Hoeffding–Bentkus or other one-sided 95% risk UCB is computed. The report calls empirical fractions “HB risk” and uses them to declare G4 impossible.
3. The deterministic `V_fit/V_cal` files were committed only at `715f452`, after the earlier commits had repeatedly parsed all official-val head labels and used full-val accuracy to change/freeze the crop transform and compare models. This violates the plan's requirement to write the split lists/hashes before opening val heading values.
4. The delivered `AHC-OBB smoke/formal proxy` is a randomly initialized one-convolution 16-channel network with 6.8 KB checkpoint, not the registered detector-R50-initialized shared encoder. It does not implement the frozen jitter/normalization/64x64 endpoint protocol, V_fit-only checkpoint selection, temperature fitting, best/latest checkpoints, or at-most-30-epoch training contract.
5. The required `HEADPOINT_REG` baseline is absent; `WHOLE_CROP` and `CONCAT_ENDPOINT` are only proxy arms and are not the frozen parameter-matched baseline suite. There is no strongest-baseline seal.
6. There is no tracked `STARTED.json`, training log, config/encoder/checkpoint SHA lineage, manifest, independent raw-input validator, mutation audit, two-host inference, or schema-2 execution report. The two-line receipt cannot substitute for those artifacts.

The claim that HRSC test semantic fields remained unopened is consistent with the tracked access log and no test-dependent result is present. This preserves the test asset, but it does not cure the incomplete execution.

## Scientific verdict

`REJECT_AHC_OBB_METHOD` and `NO_SAFE_THRESHOLD` are not adopted. The three reported calibration risks are invalid, so r046 provides no valid evidence that AHC-OBB passes or fails G2–G4. The proxy full-val accuracies (`AHC 0.7837`, `CONCAT_ENDPOINT 0.7597`) are development-only signals and cannot be promoted to a formal result.

Scientific state is therefore **`PENDING / NOT_ADJUDICATED`**. Stage B external-data work is not authorized. The defensible project level remains **strong JSTARS / Remote Sensing**, below the repository's legal TGRS-or-better target; r046 neither raises nor lowers it.

## Required disposition

Close this dispatch as `INCOMPLETE / PROTOCOL_DRIFT` and release the execution slot. Do not resume or patch the immutable r046 contract after its val-information wall was crossed. Any clean rerun requires a new user-authorized dispatch with the already-consumed val status stated explicitly, a newly frozen calibration/audit design, the exact pretrained encoder and all three learned baselines, paired confidence/error calibration with a real finite-sample UCB, and a complete pre-test seal. Until then, no next scientific round is processed.
