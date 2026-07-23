# R1 30-run status audit (063)

> Corrects the 061 mislabels and freezes the true per-run status. Data:
> `reports/r1_30run_status_audit_063.csv` (per run), `reports/r1_health_gate_decisions_063.csv`.
> Derived from run logs + work_dir checkpoints, not from memory.

## Summary
| classification | count | eligible_for_main_matrix |
|---|---|---|
| **complete (healthy)** | **18** | **true** |
| failed_training | 12 | false |

## Eligible for main matrix (18) — PSC / CSL / DCL × {DIOR-R, SODA-A} × 3 seeds
All trained to 12 epochs under the identical frozen protocol, final `dota/mAP > 0`:
- PSC: DIOR≈0.531–0.539, SODA≈0.597–0.600
- CSL: DIOR≈0.291–0.331, SODA≈0.319–0.379
- DCL: DIOR≈0.322–0.337, SODA≈0.503–0.537

These 18 are under **full instrumented evaluation** (062→063 eval driver): AP50/AP75, canonical
masked ar≥1.6 angle-error, native-uncertainty masked NRC + score masked NRC + bootstrap CI.

## failed_training (12) — NOT eligible, NOT re-burned on the same setting
- **direct_regression_le90 ×6**: NaN divergence under the shared protocol (`loss: nan` persistent
  from ~iter 250, within epoch 1); final mAP 0. Negative control lost at shared hyperparameters.
- **KLD ×6**: `GDLoss_v1(kld)` needs fp32 for `linalg.inv` but the shared protocol uses AMP/fp16
  → `RuntimeError: linalg.inv Low precision Half` crash <30 s on all 4 ranks.

## Corrections applied (vs 061)
- 6 direct_regression runs were mislabeled `complete` by the 061 queue (rc=0 + epoch_12.pth
  written despite NaN weights) → corrected to `failed_training`.
- The 062 queue's generic `rc_fail` for KLD → corrected to the precise AMP/linalg cause.
- No `failed_training` is labeled `complete`; no `running` is labeled `complete`; "orchestration
  complete" is never written as "training complete".

## Gate discipline going forward
`watch_r1_oom_retry_062.py` carries the epoch-1 health gate; the fixed NaN detector distinguishes
terminal `loss: nan` from transient AMP overflow (`grad_norm: inf`), so healthy low-warmup runs
are not false-killed while diverging runs are stopped early. No 12-epoch burns after the gate.
