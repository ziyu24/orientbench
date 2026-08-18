# Server execution report — orientbench-b-r043-saur-obb-stagea-20260818

## Outcome

**PROTOCOL_DRIFT_STOPPED** (plan-defined G0 failure / kill condition). The r043 run is incomplete and its only DIOR result is invalid for this dispatch.

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

Execution status is **incomplete** under the plan's `failure_early_stop` mapping. The only permissible continuation is the plan-specified one-time repair of the identified asset/host root cause: provide a real DIOR-R train-only → val PSC checkpoint, config, and archived val parity record. A new exact dispatch is required before any subsequent execution.  The invalid DIOR test-evaluation output must not be used as evidence.
