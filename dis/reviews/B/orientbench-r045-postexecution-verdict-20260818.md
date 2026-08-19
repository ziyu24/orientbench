# B post-execution verdict — r045

- Dispatch: `orientbench-b-r045-prospective-axis-drift-decision-20260818`
- Verdict: **`ACCEPT_GATED_EARLY_STOP_WITH_AUDIT_QUALIFICATION / ADOPT_APPLICATION_SHIFT_FAIL / STOP_TOP_JOURNAL_EXPERIMENT_EXPANSION`**
- Reviewed HEAD: `070b17d1fbc311829732a9788cb0141554f8b967`

## Execution verdict

B accepts the held-out target result and the plan-defined gated early-stop mapping as complete, with an explicit audit qualification. The operative DIOR-R policy seal selected Oriented R-CNN R50 at nominal coverage 0.90 against the AP-only LSKNet full-coverage policy. The operative policy commit `e8f757b` and target score-only threshold commit `e9326cc` were pushed before the first persisted HRSC D_audit GT-dependent operation. The source amendment was retracted before target access; the later threshold amendment added metadata without changing the numeric threshold.

Implementation A and validator B recomputed the target gate from raw predictions and HRSC GT and agree to `1e-12` on deterministic fields and `1e-10` on bootstrap endpoints. B independently recomputed the reported image-table means, verified all 106 manifest entries against the Git blob bytes, compiled the r045 Python files, ran the peer-governance validator/tests, and confirmed that all five real validator mutations returned nonzero. DOTA-v2.0 val and SODA-A official test remained unopened.

## Audit qualification

The final bundle is not internally pristine. `source_analysis/` and the operative `POLICY_SEAL.json` consistently use the frozen all-prediction score quantile (`0.0711999685` for R50), but the later, non-operative `source_policy/source_policy_results.json` uses `0.8387539387` and reports different source statistics; its associated supervisor entry also cites an untracked `experiments/r045_axis_drift/source_policy.py`. This branch must not be used as claim evidence or described as a reproducible implementation of the operative seal. The Git history also temporarily rewrote `STARTED.json` after ASSET_SEAL and later restored the original blob; immutable execution records should not be edited this way.

These defects qualify the execution package but do not rescue or reverse the target result: both source variants still select R50 at nominal 0.90, the HRSC threshold was independently fixed from target score-only rows, and both raw-input target implementations obtain the same negative result. No target-outcome-dependent policy change occurred.

## Scientific verdict

Adopt `APPLICATION_SHIFT_FAIL`. On 98 sealed HRSC2016 D_audit images, the prespecified orientation policy is slightly worse, not better:

- `Delta_cont = -0.0019519474`, paired image-bootstrap 95% CI `[-0.0075969074, 0.0035536397]`;
- `Delta_severe(q=0.50) = 0`, CI `[0, 0]`;
- sensitivity deltas at `q={0.25,0.50,1.00}` are `{-0.0031584062, 0, 0}`.

The absolute constraints pass—orientation-risk UCB `0.0399527513`, eligible matched coverage `1.0`, and AP50 `0.9986048424` versus `0.9980072393`—but they cannot substitute for a positive application benefit. G3 and the benefit component of G5 therefore fail exactly as frozen. Endpoint, threshold, coverage, candidate, or selector retries on this opened audit split are forbidden.

## Venue and next action

The only prospective application study justified by r044 has failed, so it does not lift novelty from the dual-red-team `3/5` level. The defensible project level remains **strong JSTARS / Remote Sensing**, below the repository's legal TGRS-or-better target. The present manuscript is not honestly JPRS/TGRS-ready and should not be submitted there.

No r046 rescue dispatch should be activated from the current evidence. Reopening a top-journal route now requires an explicitly authorized, genuinely new scientific increment—such as independently collected downstream application labels with a prospective decision endpoint, or a new orientation-reliability method validated on untouched endpoints—not another threshold, endpoint, selector, audit, or prose iteration on the consumed DIOR-R/HRSC split.
