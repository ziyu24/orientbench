---
schema_version: 2
dispatch_id: orientbench-b-r045-prospective-axis-drift-decision-20260818
plan_id: b-r045-prospective-axis-drift-decision-20260818
initiator: B
plan_path: dis/plans/B/b-r045-prospective-axis-drift-decision-20260818/sug.md
plan_commit_sha: 605796f58b1f940319380f1f3b6c2f4d618fb0e6
plan_blob_oid: 5601060370eb6b95ebd1941747319fa847dac30d
plan_sha256: 82d06ebc294525bb8032e562217fd7a865773c6af9e901fd56d582ca9a5f9563
dispatch_commit_sha: cb7b0c0a87e5c5373153ac02643b25b0e0fc0de8
server_report_path: dis/server_reports/orientbench-b-r045-prospective-axis-drift-decision-20260818/SERVER_EXECUTION_REPORT.md
execution_status: complete
completion_mode: GATED_EARLY_STOP_APPLICATION_SHIFT_FAIL
starting_commit: cb7b0c0a87e5c5373153ac02643b25b0e0fc0de8
ending_commit: recorded_by_the_result_commit_containing_this_report
---

# Server execution report — business instruction 045

## Outcome

The frozen study completed with terminal state **`APPLICATION_SHIFT_FAIL`**. This is the plan's normal gated early-stop path and maps to `execution_status: complete`; it is not a claim of JPRS/TGRS readiness.

On 98 sealed HRSC2016 D_audit images, `Delta_cont=-0.001951947406305591` with paired image-bootstrap 95% CI `[-0.00759690736733883, 0.003553639725280447]`. `Delta_severe=0` with CI `[0,0]`. Thus G3 fails. Sensitivity deltas at q={0.25,0.50,1.00} are {-0.0031584062,0,0}, so G5's benefit condition also fails. Absolute deployment constraints pass: orientation UCB=0.0399527513, eligible matched coverage=1.0, and AP50=0.9986048424 versus 0.9980072393 for the AP policy.

## Governance, seals, and access order

- Worker `server-primary` mapped to SERVER. The exact dispatch, plan blob/SHA, root `dis/sug.md` mirror, L2 authorization, HTTPS remote, resources, and write set were verified.
- STARTED was independently committed/pushed as `714edef`; ASSET_SEAL as `3cd970b`; operative POLICY_SEAL as `e8f757b`; TARGET_THRESHOLD_SEAL as `e9326cc`. Every data layer opened only after its preceding push.
- A pre-target source amendment was explicitly retracted before any HRSC target access; the operative policy remained the original `POLICY_SEAL.json`. A threshold metadata amendment at `4b43096` added command and score-table SHA information without changing the numeric threshold, before target audit GT access.
- Before target threshold sealing, HRSC D_cal access was limited to image ID, prediction ID, and score. HRSC D_audit inference used the image-only dataset. The first GT-dependent operation was matching after both policy and threshold seals were remotely visible. See `audit_bundles/r045/target_access_audit.json`.

## Execution and provenance

| Stage | Result | Evidence |
|---|---|---|
| Asset/split seal | PASS; three common valid families and four pinned split hashes | `audit_bundles/r045/ASSET_SEAL.json` |
| DIOR-R policy | AP=LSKNet-S full coverage; orientation=R50 @0.90, a nontrivial architecture+coverage change | `audit_bundles/r045/POLICY_SEAL.json` |
| HRSC D_cal threshold | 0.05102584883570671 from 1,385 score-only predictions | `audit_bundles/r045/TARGET_THRESHOLD_SEAL.json` |
| HRSC D_audit | G3 and benefit portion of G5 fail; G4 passes | `audit_bundles/r045/gate.json` |
| Independent recomputation | A/B deterministic fields agree within 1e-12 and bootstrap endpoints within 1e-10 | `target_gate_a/implementation_a.json`; `target_audit/validator_b.json` |
| Mutations | pristine exit 0; split member, threshold, angle error, GT AR, and policy token mutations all nonzero | `mutations/mutation_summary.json` |

Missing predictions were reconstructed deterministically from the registered valid checkpoints without training or fine-tuning. Inference used four GPUs; full log paths are retained under `outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/logs/` and `target_*/*work*`. Matching and the 10,000-replicate paired image bootstrap used 48 workers, seed 20260818. No new dataset was introduced; DOTA-v2.0 val and SODA-A official test were not touched.

## Integrity, deviations, and completion mapping

The endpoint, split bytes, candidate architectures, nominal coverage, numeric target threshold, effect sizes, bootstrap unit/seed, and seven-condition gate were not changed after outcome access. No post-outcome rescue was performed. The source amendment/retraction and threshold metadata amendment are fully persisted; neither changed the operative target decision after target outcomes were opened.

Implementation A produced raw matched-instance and image tables. Validator B read raw predictions and GT and independently recomputed the score quantile, `d_tip/Z`, aggregation, UCB, AP50, bootstrap intervals, and comparison tolerances. The manifest records paths, sizes, hashes, formats, and recomputability. Paper-facing output keeps the venue at `STRONG_JSTARS_OR_REMOTE_SENSING` and makes no readiness claim.

Completion mapping: gated early stop / `APPLICATION_SHIFT_FAIL` → `execution_status: complete` → receipt first line `执行完毕`.
