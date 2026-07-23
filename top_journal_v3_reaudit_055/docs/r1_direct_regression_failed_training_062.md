# R1 failed_training under the shared pre-registered protocol (062)

> Two heads cannot run under the frozen shared training protocol (same optimizer, batch/lr,
> schedule, **AMP/fp16**, augment). Both are marked `failed_training` in the R1 **main** matrix.
> Neither is tuned/rescued into the main matrix (that would break the controlled comparison).
> Evidence is in the per-run logs under `logs/r1_angle_coder/`.

## Verdict A — direct_regression_le90 (negative control): NaN divergence
- All 6 runs (DIOR-R seed0/1/2, SODA-A seed0/1/2) diverged: `loss: nan` from ~iter 250–760
  (within epoch 1), persisting to epoch 12; final `dota/mAP = 0.0000`.
- The old 061 queue mislabeled them `complete` (rc=0 + epoch_12.pth written despite NaN weights).
  Corrected here to `failed_training`.
- **Reason (recorded verbatim in matrix):** *shared pre-registered optimizer setting diverged
  with NaN under direct 5-parameter regression head; no valid detector; native uncertainty
  unavailable; NRC not computed.*
- Head: `mmdet.RetinaHead` direct 5-param regression + L1, lr=0.005 + AMP. The direct angle
  regression is unstable at this lr/precision; the AngleBranchRetinaHead coder heads
  (PSC/CSL/DCL) are not.

## Verdict B — KLD: AMP/fp16 incompatibility (hard crash)
- All 6 runs crash in <30 s on all 4 ranks with:
  `RuntimeError: linalg.inv: Low precision dtypes not supported. Got Half`.
- Cause: `GDLoss_v1(loss_type='kld')` computes a matrix inverse (`linalg.inv`) for the
  Gaussian-distance loss, which requires fp32; the frozen shared protocol uses AMP/fp16
  (`AmpOptimWrapper`, inherited by every head from the PSC template). KLD is therefore
  incompatible with the shared protocol **as pre-registered**.
- **Reason (in matrix):** *GDLoss_v1(kld) requires fp32 for linalg.inv but the frozen protocol
  uses AMP/fp16 → linalg.inv Half crash on all ranks; native uncertainty unavailable; NRC not
  computed.*
- Note (from 061 pre-registration): even had KLD trained, the standard KLD-RetinaNet head emits
  no per-instance angle variance, so KLD's "native uncertainty" would be `not_emitted` anyway.

## Consequence for the R1 main matrix
- **Main matrix = PSC, CSL, DCL** (18/18 healthy, 3 seeds × 2 datasets each), all trained under
  the identical frozen protocol → a clean controlled comparison of the three classification-coder
  angle heads.
- **direct_regression_le90 and KLD = failed_training**, excluded from the main matrix and from
  any mechanism conclusion.
- This is itself an honest finding about the shared protocol (AngleBranch coder heads train under
  shared AMP; direct-regression-based heads do not), not a fabrication and not a claim that either
  head is "broken" in general — only that it does not run **under this pre-registered protocol**.
- Exploratory non-AMP / stabilised re-runs are **appendix/diagnostic only** — see
  `r1_direct_regression_exploratory_rescue_plan_062.md`. They must never enter the main matrix or
  support a mechanism conclusion.
