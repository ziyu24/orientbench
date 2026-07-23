# R1 evaluation spec (062) — reuse run_052 matcher; add per-head native-uncertainty dump

> Supersedes `r1_eval_spec_061.md` with the concrete reusable asset located this round.
> Scope now: **18 healthy runs** = PSC/CSL/DCL × {DIOR-R, SODA-A} × 3 seeds. The 12 failed runs
> (direct_regression NaN, KLD AMP-incompat) are excluded. GPUs are now free (R1 training queue
> ended), so this is the immediate next execution step. Status this round: AP50 recorded for all
> 18 (from epoch-12 val); AP75 / angle-error / masked-NRC = **pending** (see below).

## Reusable assets (do NOT reimplement — identical semantics to the frozen 052 cells)
- Matcher: `top_journal_v3/scripts/run_052_real_dump_matched_tables.py::fast_match_image`
  (greedy by score, class-indexed, rotated IoU>0.5, one row per prediction).
- Canonical angle error: `orientbench.metrics.angle_contract.angle_error_contract`
  (`angle_error_canonical_longside`).
- Record schema: 17-field `matched_17field` (incl the `phase_mod` / native-uncertainty column).
- Masked NRC / risk-coverage: `orientbench.metrics.nrc_auc.nrc_auc`,
  `orientbench.metrics.risk_coverage.{risk_at_coverage, aurc}` (oracle→0, random→1, reverse→2).
- Bootstrap CI: image-level clustered, per `a0_bootstrap_ci_055.py`.

## The one new piece to build: per-head native-uncertainty inference dump
Run each checkpoint on its eval split (DIOR-R test / SODA-A val_tiled), dump per **kept** detection:
`score, obb(cx,cy,w,h,theta)`, and the head's native-uncertainty logits, aligned to NMS output.
- **PSC** → hook PSC angle branch; recompute `phase_mod = phase_cos²+phase_sin²` from the kept
  boxes' angle logits (reuse `run_052` phase_mod path — a `dota20_phase_mod` dump already exists).
- **CSL** → 45-way CSL logits of kept boxes → softmax → entropy / max-prob / margin.
- **DCL** → 8 BCL logits of kept boxes → per-bit sigmoid → mean/min margin.
Alignment (kept-detection ↔ angle logits) is the correctness-critical step; validate on one run
(PSC/DIOR-R/seed0) by checking decoded angle from dumped logits == model's output angle before
scaling to 18 runs.

## Metrics to fill (per run, then per 3-seed block)
1. AP50 (have), AP75, mean masked ar≥1.6 angle-error.
2. masked ar≥1.6 `nrc_auc(native_uncertainty, angle_error)` — the head's intrinsic ranking.
3. masked ar≥1.6 `nrc_auc(score, angle_error)` — detection-score proxy baseline (hook-free;
   computable from standard matched predictions, could be filled first).
4. bootstrap CI on NRC. Then seed-variance (mean/std/min/max NRC, reproducible-direction).

## Guardrails
- ar≥1.6 masked protocol + D_cal/D_audit unchanged. NRC<1 ⇒ informative/non-reversed, never
  "calibrated". Single seed / partial ⇒ no mechanism conclusion. phase_mod stays a mechanism
  candidate until the 3-seed matrix supports pre-registered outcome A or B. Do not write PSC
  "proven broken" or "phase_mod mechanism proven".
