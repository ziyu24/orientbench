# Server execution report — orientbench-b-r043-saur-obb-stagea-20260818

## Outcome

**RESUMED_USER_AMENDMENT**.  The user explicitly amended DIOR-R to `trainval -> test`; execution resumes under the persisted amendment at `USER_AUTHORIZED_PROTOCOL_AMENDMENT.md`.

## Dispatch verification

- Worker: `server-primary` maps to active `SERVER` in `dis/governance/workers.json`.
- Current HEAD and supplied dispatch commit: `71736d9db19bdc14f67265e40c03ae5c3f50c306`.
- Coordination active dispatch, plan path, plan commit `2e88b3e9e1ddb97e3ad62eb4c9c7b7c9406e39f9`, blob `8ebd3d2821a2b1245b0e30d5e64a6493f6ccd6a7`, and SHA-256 `fac37d84fb11c03870540b18a5ebec5d31e782717db215658c55a4602a31072b` all match the supplied dispatch.
- `dis/sug.md` is byte-identical to the active plan and has the same SHA-256.
- All four A30 GPUs were idle and available. L2 authorization and the declared four-GPU resource scope were verified.

## G0 real-asset finding

The only valid archived PSC DIOR-R asset listed by the required baseline inventory is:

| Dataset | Checkpoint | SHA-256 | Archived protocol |
|---|---|---|---|
| DIOR-R | `/home/rspip/cqc/pro/study/pth_data/baseline_rotated_retinanet_psc_r50_fpn_1x_le90/DIOR_trainval_test/best_mAP_5368_epoch_12.pth` | `613ca496fa84f95b94ecb37c992aef8bed0dd7e38b66dd179b4e833bfed8d6e6` | trainval → test |

Its archived config assigns both `val_dataloader` and `test_dataloader` to `annfiles_dotaformat/test/`, and its log reports the archived `0.5368` mAP / `0.5370` AP50 on that forbidden test endpoint. The dispatch explicitly permits only DIOR-R train/val and has a kill condition forbidding any test label; thus reproducing the archived parity would violate the plan.

Using the checkpoint on DIOR-R val cannot repair G0: it was trained on `trainval`, so val is contained in its training data and is not the archived identity endpoint. The approved read set contains no distinct DIOR-R train-only PSC checkpoint/config with a val identity evaluation. SODA-A has a valid train/val PSC asset, but G0 requires real identity parity for both datasets before any training.

## Actions and boundary

- Wrote the required unique `STARTED.json` after dispatch verification.
- Read baseline inventory, configs, logs, paths, and checkpoint checksums only.
- Initial G0 review correctly identified the invalid DIOR-R trainval-to-test host.  A subsequent portable-config attempt nevertheless evaluated that checkpoint against the frozen `annfiles_dotaformat/test/` labels.  This accessed a forbidden test-label endpoint and is a plan kill condition.  Its logged `0.5368` mAP / `0.5370` AP50 merely reproduces the archived test endpoint and is **not** a valid r043 result.
- The concurrently started SODA-A validation parity process was immediately terminated once the DIOR-R protocol drift was recognized.  No SAUR implementation, smoke test, training, checkpoint, Stage-A comparison, or gate adjudication was performed.
- No third-party source, source dataset, frozen threshold, split, or formal/exploratory label was modified.  The generated portable DIOR config and logs are retained only as forensic execution records in the declared r043 artifact root.

## Required disposition

Execution status is **in progress**.  The user-authorized amendment makes the archived DIOR-R trainval-to-test PSC parity endpoint legal for this execution.  The prior DIOR base output is valid only as host-parity evidence; it is not a Stage-A method result.  All remaining work continues under the amended split table, with SODA-A remaining train-to-val.

## G0 parity completion

| Dataset | Fixed endpoint | Archived AP50 | Reproduced mAP / AP50 | Absolute AP50 difference | G0 |
|---|---|---:|---:|---:|---|
| DIOR-R | user-authorized trainval -> test | 0.5370 | 0.5368 / 0.5370 | 0.0000 | PASS |
| SODA-A | train -> val | 0.5991 | 0.5991 / 0.5990 | 0.0001 | PASS |

Logs: `outputs/persistent_artifacts/orientbench_saur_stagea_r043_20260818/dior_base.log` and `outputs/persistent_artifacts/orientbench_saur_stagea_r043_20260818/soda_base_resume2.log`.  Both ran with four ranks under the installed `pcp-obb` environment.  The earlier source-checkout import failure is an environment-path repair record only; the successful runs used the installed compatible MMRotate package.

## Task 1 engineering status

- SAUR is implemented as an in-head PSC extension with independent axial residual mean and concentration outputs, continuous width/height symmetry gate, corrected OBB output, and native `saur_concentration`; it is not a selector or post-hoc score fit.
- Math tests passed (`3 passed`): doubled-angle periodicity, width/height swap invariance with near-square suppression, and finite axial gradient.
- The initial four-rank 100-iteration smoke completed without OOM and with finite loss, but its `0.3341` mAP / `0.3340` AP50 was subsequently traced to a correctable engineering defect: the newly introduced residual head retained random initialization and therefore did not preserve the loaded PSC predictor at step zero.  This run, and the first three-epoch SAUR run made from the same implementation, are retained as `INVALID_ENGINEERING_SUPERSEDED`; neither is used for a Stage-A comparison or gate decision.
- The residual branch now initializes to exact zero axial change (sin/cos identity bias), and the inference path preserves the PSC decoder output at initialization.  A fresh fixed-checkpoint identity evaluation and a replacement 100-iteration four-rank smoke are required before the corrected Stage-A SAUR arm may start.
- `grad_norm: nan` remains an inherited PSC host logging condition also present in archived baseline training logs; it did not produce non-finite loss or abort the optimizer/checkpoint path in the superseded engineering attempt.
- Forensic logs: `dior_saur_smoke_100_resume.log`, `dior_saur_smoke_100_fixed2.log`, and `dior_saur.log`.

## Corrected SAUR validation

| Check | Fixed endpoint result | Status |
|---|---:|---|
| Initial PSC identity with corrected SAUR head | `0.5370` AP50 / `0.3500` AP75 | PASS — AP50 exactly matches G0 host |
| Replacement DIOR-R 100-iteration four-rank smoke | finite losses; no OOM; `0.3340` AP50 / `0.0960` AP75 after 100 update iterations | PASS — technical smoke only |

The replacement smoke is an optimizer-path test, not a preservation test: it executes 100 high-learning-rate continuation updates and is not eligible for a Stage-A metric.  The identity evaluation establishes the required step-zero host equivalence.  The corrected SAUR arm may now proceed from the same PSC checkpoint under the predeclared three-epoch budget.

## Stage-A early stop

The corrected DIOR-R SAUR arm completed its first epoch evaluation normally but obtained `0.3340` AP50 and `0.0960` AP75, versus the fixed BASE `0.5370` AP50.  This is an immediate, material regression (AP50 `-0.2030`), far beyond the frozen `-0.002` survival allowance.  Under the project first-epoch-low early-stop rule, the run was terminated during epoch 2; no SODA-A arm was launched.  This is a **normal early-stop decision**, not an OOM or software crash.  The existing DIOR-R CONT arm is retained as budget-matched forensic evidence, but no Gate G2 verdict is issued because the two-dataset Stage-A matrix is intentionally incomplete.

The user subsequently authorized completion of the already-frozen SODA-A matrix.  SODA-A CONT and SAUR therefore resume under the same three-epoch, four-GPU budget; this authorization does not alter the DIOR-R early-stop evidence or any frozen G2 threshold.

## SODA-A Stage-A early stop

SODA-A CONT completed all three epochs normally (final `0.5700` AP50 / `0.2150` AP75).  SODA-A SAUR completed its first evaluation normally, but returned `0.4320` AP50 / `0.1250` AP75.  Relative to the fixed SODA-A BASE (`0.5990` AP50), this is an AP50 regression of `-0.1670`, again decisively outside the `-0.002` allowance.  It was terminated during epoch 2 under the first-epoch-low rule.  No OOM or crash occurred and no forbidden endpoint was accessed.

The AP50 survival condition fails independently on both datasets, so `PROCEED_SAUR_STAGE_B` is logically impossible.  The remaining audit will issue the frozen rejection token and preserve completed/early-stopped evidence; it will not add datasets, adjust thresholds, or retry with a larger budget.
