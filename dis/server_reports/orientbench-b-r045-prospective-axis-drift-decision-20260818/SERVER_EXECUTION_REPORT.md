# r045 server execution report

执行完毕

Execution status: normal early stop (`APPLICATION_SHIFT_FAIL`).

Completed units: T0 asset/split seal, DIOR-R source policy seal, HRSC D_cal score-only threshold seal, HRSC D_audit target matching, independent implementation-A recomputation, and five real mutation checks.

Primary result: `Delta_cont=-0.001951947406305591`, paired image-bootstrap 95% CI `[-0.00759690736733883, 0.003553639725280447]`; primary gate G3 failed. G5 also failed; G4 was not adjudicated after the prespecified G3 stop.

Independent audit: `outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/target_gate_a/implementation_a.json`; mutation audit: `.../target_gate_a/mutation_audit.json` (pristine=0, all five mutations nonzero).

Forbidden endpoints: DOTA-v2.0 not touched; SODA-A official test not touched. No detector training, threshold rescue, or post-outcome protocol change occurred.
