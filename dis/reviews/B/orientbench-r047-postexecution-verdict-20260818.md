# B post-execution verdict — r047

- Dispatch: `orientbench-b-r047-ahc-obb-clean-formal-stagea-20260818`
- Verdict: **`REJECT_COMPLETION_AS_PROTOCOL_DRIFT / SCIENCE_NOT_FORMALLY_ADJUDICATED / PRACTICALLY_STOP_AHC_INVESTMENT / DO_NOT_START_STAGE_B`**
- Reviewed HEAD: `dbf68f2242323098ece1e6670abc4dc580161c4a`

## What is real and preserved

The identity-only test partition was committed before test semantic access: T_cal has 225 images and T_audit 228. The tracked code only enumerates T_cal XMLs during calibration, and no T_audit semantic result is present. B therefore treats T_audit as still unopened.

This run also contains substantially more real work than r046. Four arms produced 30 epoch metric traces with `world_size=4`; the model seal records approximately 102 MB R50 checkpoints on the server and registered checkpoint SHA. Development best accuracies are AHC `0.8428835`, WHOLE_CROP `0.8743068`, CONCAT_ENDPOINT `0.8650647`, and HEADPOINT_REG `0.8613678`. The 1,764 tracked T_cal rows keep confidence and error paired by row ID.

B independently recomputed the frozen 70% calibration point from those rows, including all 225 T_cal mother images and the tighter of the specified Bentkus/Hoeffding bounds. The result remains unfavorable:

| view | realized instance coverage | empirical image risk | valid one-sided UCB |
|---|---:|---:|---:|
| GT_BOX | 0.69916 | 0.09166 | 0.15661 |
| PRED_BOX_R50 | 0.69896 | 0.11845 | 0.18904 |
| PRED_BOX_LSKNET | 0.70051 | 0.10249 | 0.17297 |

Thus no common view satisfies both realized coverage `>=0.70` and UCB `<=0.15`. The negative direction is not created by r046's old confidence/error bug.

## Why the formal completion token is rejected

The immutable r047 dispatch first committed a terminal `未执行完毕 / IMPLEMENTATION_OR_ASSET_FAILURE` report at `4db8ced`, then resumed and overwrote that terminal report without a tracked user-resume authorization or new dispatch. There is no `STARTED.json`. More importantly, the post-resume implementation deviates on choices that can affect a near-boundary result:

1. The registered MMRotate environments were declared incompatible, then `run_mmrotate_test.py` manually overwrote `mmcv.__version__` and `mmdet.__version__` strings to bypass import guards. No host AP parity was delivered, so G0 cannot be changed from failure to pass by assertion.
2. The tracked formal trainer has fixed learning rate: it omits the frozen one-epoch warmup and cosine schedule, and omits color jitter. It logs the last training loss as every validation loss, never computes validation AUGRC, and selects checkpoints by accuracy alone.
3. `HEADPOINT_REG` is trained against `[binary_endpoint_sign, 0]`, not the annotated normalized center-to-head 2D vector. It is therefore not the frozen CHP-like baseline.
4. The first AHC DDP run failed. The retry log is empty and the tracked code still lacks the runtime change needed to explain why the same unused-parameter failure disappeared. The exact retry implementation/command is not auditable.
5. T_cal calibration does not fit the required temperature, does not compute the Hoeffding branch, excludes images with no eligible row rather than accounting over all 225 images, and uses independent best-IoU matches rather than one-to-one host matching. Its summary discards the per-coverage evidence while the gate cites untracked numbers.
6. The seal-referenced checkpoints and run summaries are not Git-delivered; there is no complete manifest/can-recompute table, independent raw-row validator, real mutation suite, parameter/FLOP table, access audit, or schema-2 execution report. `MODEL_DEVELOPMENT_SEAL.code_sha256` hashes the seal builder itself, not the trainer.

These are not cosmetic packaging issues. Correct GT-box UCB is only `0.00661` above the gate, so the omitted formal schedule/augmentation and unauditable retry could change the outcome. The frozen scientific token `REJECT_AHC_OBB_VALID_TCAL_SAFETY_FAIL` is therefore not adopted.

## Scientific and venue decision

Formal state remains `PENDING / NOT_ADJUDICATED`, and Stage B is forbidden. Separately, the resource decision is to stop AHC-OBB investment: the antisymmetric arm trails the strongest whole-crop baseline by `3.14` percentage points on consumed development val, and all three independently corrected T_cal safety views miss the gate. A further AHC repair round is unlikely to create a top-journal method and would be post-outcome rescue.

The defensible project level remains **strong JSTARS / Remote Sensing**, below the legal TGRS-or-better target. r047 neither establishes a formal method failure nor supplies the method-level novelty needed for JPRS/TGRS. A future top-journal round must be a genuinely different scientific method/task with new authorization, not another AHC schedule, threshold, environment or audit repair.
