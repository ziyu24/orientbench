# R1 exploratory rescue plan — direct_regression_le90 + KLD (062)

> **exploratory_rescue_not_preregistered.** These re-runs deviate from the frozen R1 protocol
> and therefore may go **only** into an appendix / diagnostic table. They MUST NOT enter the R1
> main matrix (`r1_angle_coder_matrix.csv`) and MUST NOT support any mechanism conclusion. Any
> artifact produced carries the tag `exploratory_rescue_not_preregistered` in its filename,
> table column, and doc. Running rescue is OPTIONAL and does not block PSC/CSL/DCL evaluation.
> Requires supervisor go-ahead before consuming GPU (touches experimental-design integrity).

## Why a deviation is needed
Both heads fail **only** because of the shared protocol's choices (lr=0.005 + AMP), not because
the reliability question is ill-posed for them. A stabilised re-run would let us report whether a
no-native-uncertainty control (direct regression) and a distribution-aware-loss head (KLD) *could*
have been measured — as a boundary/appendix note, not as pre-registered evidence.

## Proposed exploratory settings (isolated work_dir, tagged configs)
Output dir: `work_dirs/r1_rescue_exploratory/`, configs suffixed `__exploratory_rescue`.

### direct_regression_le90 (NaN divergence)
- Disable AMP: `AmpOptimWrapper` → `OptimWrapper` (fp32).
- Lower lr: 0.005 → 0.0025 (and/or warmup longer).
- Stronger grad-clip: max_norm 35 → 10.
- epoch-1 health gate applies (same watcher logic).

### KLD (AMP crash)
- Disable AMP only: `AmpOptimWrapper` → `OptimWrapper` (fp32) — this alone resolves the
  `linalg.inv Half` crash; keep lr/schedule/grad-clip at the shared values so the deviation is
  the minimal one (precision only).
- Native uncertainty: still expected `not_emitted` (point-regression head) — record honestly,
  do not fabricate an angle variance.

## Guardrails
- Tag everywhere: `exploratory_rescue_not_preregistered`.
- Separate report file (never the main matrix), e.g.
  `reports/r1_exploratory_rescue_metrics_0XX.csv`.
- No mechanism conclusion; no promotion to main matrix; PSC/CSL/DCL main line unaffected.
- 4-GPU launch + epoch-1 gate + OOM/1200s retry preserved.
