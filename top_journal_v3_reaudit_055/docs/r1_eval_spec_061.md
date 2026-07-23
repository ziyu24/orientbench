# R1 per-run evaluation spec (061) — reuse frozen metrics, fill native uncertainty

> Status this round: **specified + reuse-path verified, NOT executed.** Only 1/30 runs is
> complete (PSC/DIOR-R/seed0), the 4 GPUs are saturated by the active seed1/seed2 training,
> and no mechanism conclusion is possible from a single seed. Running an inference dump now
> would contend with the live 4-GPU training. Executed next round once ≥1 head has 3 seeds and
> a GPU frees. seed0 AP50 (=0.5310, from its epoch-12 val on DIOR-R **test**) is already in the
> matrix; AP75 / angle-error / masked-NRC are marked `pending` there.

## What each completed run must produce (per detection, matched to GT)
Records in the **frozen `matched_17field` schema** (same as
`outputs/persistent_artifacts/orientbench_real_052/matched_tables/*/matched_17field_full_052.jsonl`)
so the frozen metric code is reused verbatim. Fields: `score`, `angle_error` (canonical
long-side, radians→used as-is), `pred_obb{cx,cy,w,h,theta}`, `gt_obb`, `match_iou`,
`aspect_ratio`, `near_square`, `split`, plus the **native uncertainty** column the frozen 052
dump left empty (`phase_mod`) — filled here via forward hooks.

### Native-uncertainty column per head (pre-registered, see `r1_angle_coder_config_derivation_061.md`)
- **PSC** → `phase_mod = phase_cos² + phase_sin²` from the PSC angle branch (hook the angle
  logits before `PSCCoder.decode`; recompute phase_mod with the coder's `coef_sin/coef_cos`).
- **CSL** → angle-class softmax over the 45-way CSL logits: report entropy, max-prob, margin.
- **DCL** → per-bit sigmoid over the 8 BCL logits: report mean/min bit-margin `|σ(logit)-0.5|·2`.
- **direct_regression_le90** → **none** (negative control): only detection-score proxy.
- **KLD** → **not natively emitted** (documented gap): only detection-score proxy. Record
  native column as `not_emitted`; do NOT fabricate a variance.

## Pipeline (to implement next round)
1. **Inference**: `tools/test.py <config> <best_ckpt> --work-dir <wd>` OR a custom dump loop,
   single-GPU, batch=1, on the eval split (DIOR-R test / SODA-A val_tiled). Register a forward
   hook on the bbox_head angle branch to capture per-anchor angle logits for the kept dets.
2. **Match** kept detections to GT by rotated-IoU (RBboxOverlaps2D), IoU>0.5, greedy by score
   — identical matcher to the 052 dump — emit `matched_17field` records + native-uncertainty.
3. **AP50/AP75/angle-error**: DOTAMetric at IoU 0.5 and 0.75 (AP50 already have from val log);
   angle-error = mean |Δθ| over matched dets (masked ar≥1.6).
4. **Masked NRC** (reuse, DO NOT reinvent):
   `from orientbench.metrics.nrc_auc import nrc_auc` and
   `from orientbench.metrics.risk_coverage import risk_at_coverage, aurc`.
   Under the frozen masked ar≥1.6 protocol compute, for each head:
   - `nrc_auc(native_uncertainty, angle_error)` — the head's intrinsic-signal ranking;
   - `nrc_auc(score, angle_error)` — the detection-score proxy (baseline).
   Verified reuse contract: oracle→NRC≈0.0, reverse→NRC≈2.0, random→1.0.
   NRC<1 ⇒ report as **non-reversed / informative ranking**, NEVER "calibrated".
5. **Bootstrap CI**: image-level clustered bootstrap (same as `a0_bootstrap_ci_055.py`) on NRC.
6. Write `reports/r1_angle_coder_matrix.csv` (per run) and, once a head has 3 seeds,
   `reports/r1_angle_coder_matrix_seed_variance.csv` (mean/std/min/max NRC, reproducible-reverse).

## Guardrails
- ar≥1.6 masked protocol + D_cal/D_audit split **unchanged** (frozen). No new thresholds.
- Single seed / partial matrix ⇒ **no** mechanism conclusion (report "否").
- Do not write PSC "proven broken"; phase_mod stays a mechanism candidate until the matrix
  completes and satisfies pre-registered outcome A (intrinsic beats score-proxy consistently)
  or B (intrinsic reverse-calibrated consistently) across seeds.
