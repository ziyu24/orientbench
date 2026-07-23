# R1 exploratory rescue — note (063)

> **exploratory_rescue_not_preregistered.** Configs prepared, isolated, and **not launched** this
> round: the 18 valid-run instrumented evaluation has GPU priority (§7.5). Rescue is appendix /
> diagnostic only — it never enters the R1 main matrix or the A/B/C pre-registered decision.

## Prepared (isolated) configs — `configs/r1_angle_coder_rescue/`, `work_dirs/r1_rescue_exploratory/`
| run | deviation from frozen protocol | why |
|---|---|---|
| `KLD__{dior,soda}__seed0__exploratory_rescue` | AmpOptimWrapper → OptimWrapper (**fp32 only**) | resolves `GDLoss_v1(kld) linalg.inv Half` crash; minimal precision-only deviation |
| `REGRESSION__{dior,soda}__seed0__exploratory_rescue` | fp32 + lr 0.005→0.0025 + grad-clip 35→10 | stabilise the direct 5-param regression NaN divergence |

Queue manifest: `reports/r1_exploratory_rescue_queue_063.csv` (all `prepared_not_launched`,
tagged `exploratory_rescue_not_preregistered`).

## Rules when/if launched (future round, after eval frees GPUs)
- 4-GPU launch, epoch-1 health gate, OOM→1200s retry (same watcher discipline).
- Results ONLY to `reports/r1_exploratory_rescue_results_063.csv` — never the main matrix.
- KLD native uncertainty still expected `not_emitted` (point-regression head) — record honestly.
- No mechanism conclusion; PSC/CSL/DCL main line unaffected.
- Main-matrix verdict stays: direct_regression_le90 and KLD = `failed_training` under the frozen
  shared protocol (`r1_direct_regression_failed_training_062.md`).
