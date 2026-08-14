# r034 Decisive Circularity / Class-Control Report

## Scope and registered decision

This CPU-only round evaluates the fixed A--H cohorts without refitting a coefficient, changing a split/threshold, or running detector inference. The registered primary family contains exactly 12 dataset-level, class-standardized AUGRC hypotheses: DIOR-R and DOTA-v1.0 × three contrasts (`probe-conf`, `ARonly-conf`, `probe-ARonly`) × two risks (`R_norm`, `R_raw`), with one Holm family.

The machine-evaluated candidate state is **`K1_K2_KILL_STRONG_JSTARS`**. This is the preregistered result token, not an assertion that B/C have completed their post-pull verdict.

## Decisive result

- Primary hypotheses: 12/12 present; Holm applied once across all 12; witnesses: 0/12.
- K1: **true**. In both DIOR-R and DOTA, `|DoD_ARonly| >= 0.8 |DoD_probe|`, while `probe-ARonly` is not a witness.
- K2: **true**. `probe-ARonly` is not a registered witness in either DIOR-R or DOTA under `R_norm`, class-standardized AUGRC.
- Survival rule: **false**. Therefore the registered top-journal route does not survive this round; the registered fallback token is STRONG_JSTARS.

| Dataset | Risk | Contrast | Delta AR>=2.1 | Delta all-AR | DoD | 95% CI DoD | Holm p | Witness |
|---|---|---:|---:|---:|---:|---:|---:|---|
| DIOR-R | R_norm | probe-conf | -0.001904 | -0.003616 | 0.001713 | [-0.000295, 0.003745] | 0.09789 | false |
| DIOR-R | R_norm | ARonly-conf | 0.007666 | 0.022551 | -0.014885 | [-0.018009, -0.012052] | 0.00120 | false |
| DIOR-R | R_norm | probe-ARonly | -0.009569 | -0.026167 | 0.016598 | [0.012708, 0.021103] | 0.00120 | false |
| DOTA-v1.0 | R_norm | probe-conf | 0.001002 | -0.002919 | 0.003921 | [0.001490, 0.005270] | 0.00120 | false |
| DOTA-v1.0 | R_norm | ARonly-conf | 0.002709 | 0.014866 | -0.012157 | [-0.015110, -0.007696] | 0.00120 | false |
| DOTA-v1.0 | R_norm | probe-ARonly | -0.001707 | -0.017785 | 0.016077 | [0.010314, 0.019015] | 0.00120 | false |

The remaining six registered `R_raw` rows are in `implementation_a/primary_family.csv`; all are also non-witnesses.

## Three-way decomposition

Replacing `R_norm` with AR-independent `R_raw` does not remove the observed domain contrast: the probe-conf DoD grows from 0.001713 to 0.003749 in DIOR-R (registered disappearance fraction -1.189) and decreases only 8.2% in DOTA. Thus the effect is not explained away as a risk-normalization arithmetic artifact.

AR information dominates the probe-conf DoD magnitude: `|DoD_ARonly|/|DoD_probe|` is 8.69 for DIOR-R and 3.10 for DOTA. The residual `probe-ARonly` DoD is nonzero (DIOR-R 0.016598; DOTA 0.016077), but it is not the registered flip witness because the probe-ARonly deltas remain negative in both eligibility domains rather than crossing the two-sided witness margins. This distinction is why both K1 and K2 fire even though the residual DoD confidence intervals exclude zero.

## Lineage and mechanism diagnostics

All eight units are `LINEAGE_GAP(unit)`, not `LINEAGE_CONTRADICTION`. Official annotation roots and immutable manifests exist, but no frozen map connects official raw-object IDs to the processed/tiled evaluation-object ordinals. Per plan, this gap does not stop T2 and only limits provenance wording.

T3 descriptive outputs record score entropy/quantiles, AR quantiles, near-square fraction, class composition, matching coverage/unmatched handling, and config/checkpoint/NMS identity. They carry no gate or witness interpretation.

## Audit closure

- Implementation A and independent implementation B each ran seed 20260814, replicates 0--9999, with dataset-shared cluster multiplicities.
- Comparator: 576/576 hypothesis keys; 14,976 field checks; max bootstrap metric difference `5.56e-17`, below `atol=1e-10`; judgment exact.
- Raw validator: independently recomputed all 12 primary hypotheses from enriched rows and multiplicities; PASS, with no expected-output assertion.
- Mutations: 6/6 rejected by real subprocess runs, including K1 threshold `0.8→0`, primary estimand replacement, raw-risk corruption, primary DoD corruption, bootstrap multiplicity corruption, and judgment-token corruption.
- Portable bundle: `audit_bundles/r034/`, 39 manifest objects, 229,597,799 bytes; every object is <=80 MiB; manifest and raw replay both PASS.

## Implementation clarifications and limitations

- Dataset-level values are equal-unit means under shared dataset multiplicities, matching the prior frozen witness machine.
- Class-standardized metrics equally average nonempty official class IDs within each eligibility and bootstrap draw. Official class-ID ranges are frozen; classes without an eligible matched row cannot yield a risk-coverage curve and are not assigned fabricated zero risk.
- `R_norm` and the fixed cohort come directly from the r028 audit bundle; `R_raw=clip(e_can/90,0,1)` is independently checked by the validator.
- No result in this round changes frozen cohorts, D_cal/D_audit, thresholds, metrics, or earlier artifacts.

## Paths

- Persistent output: `outputs/persistent_artifacts/orientbench_circularity_decisive_r034_20260814/`
- Execution/audit report directory: `top_journal_v3_reaudit_055/circularity_decisive_r034_20260814/`
- Portable replay bundle: `audit_bundles/r034/`
