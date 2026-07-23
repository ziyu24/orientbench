# B3 real PSC intervention analysis

## Scope and identity

Nine frozen PSC detector-head-seed units were analyzed under `ar>=2.1`. DIOR-R and SODA-A reuse the historical full-evaluator radial interventions; FAIR1M phase vectors were recovered from the frozen checkpoints and required exact numerical identity with the persistent M4 matched arrays. No detector was trained.

The four candidate formulas were frozen from the DIOR-R/SODA-A development analysis before the FAIR1M vector extraction. FAIR1M therefore remains a formula-unchanged confirmation unit: multi-frequency consistency and unwrap gap are informative for continuous risk in all three FAIR1M seeds, while their severe-event bootstrap evidence is heterogeneous. No FAIR1M result was used to alter a formula.

`phase_mod` remains reversed for continuous angle risk in all nine units (NRC range 1.1163--1.2032). Severe-event NRC is heterogeneous (range 0.9295--1.5938); the endpoints are not merged.

## Interventions

- H1: radial scaling changes the modulation-gate state, decoded angle and actual configured head loss in the historical six full-evaluator units. The response repeats across DIOR-R/SODA-A and all seeds. Because non-unit scaling can change decoded boxes, NMS membership and AP, it is mechanism evidence, not ranking-only repair evidence.
- H2: directly crossing the dual-frequency candidate-switch surface changes candidate identity and decoded risk in 9 of 9 units under the frozen criterion. This establishes boundary sensitivity, but the forced crossing is large and baseline reverse ranking is not uniformly confined to boundary-near instances; H2 therefore remains partial. Effects are reported by boundary stratum.
- H3: primary-only, secondary-only and opposing multi-frequency perturbations generate different decode/risk responses in 9 of 9 units at fixed radial statistics. Multi-frequency disagreement and unwrap gap are not monotone sign flips of `phase_mod`.
- H4: fixed-norm tangential perturbation produces coherent directional response in 9 of 9 units. The directional-score interpretation remains partial because TTA phase direction exists only for seed0 in the development dumps and external confirmation belongs to B4.

## Confounding and limits

The report includes raw and partial rank correlations controlling log aspect ratio, log size, detection score, feature norm where available, boundary distance and class fixed effects, plus within-bin and within-class estimates. RetinaNet has no separate objectness branch, so objectness is explicitly unavailable rather than proxied by detection score. Dataset and seed results remain separate. Continuous-risk and severe-event responses differ, consistent with G0.

Only unchanged candidate-score ranking is eligible for `RANKING_ONLY`. Any radial, tangential, frequency or boundary intervention that changes decoded angle is `MECHANISM_ONLY_NOT_RANKING_ONLY`. FAIR1M vector interventions preserve the frozen matched identity but do not claim full-evaluator AP invariance.

The strongest structural contrast is frequency-specific: primary-only direction perturbation has zero median decoded-angle response in all nine units over the frozen grid, whereas secondary-only, synchronized tangential, and conflicting-frequency perturbations produce the prescribed directional response. Together with the radial modulation gate, this localizes the observed sensitivity to secondary-frequency decode/gating and candidate selection rather than to an undifferentiated vector norm.

Stage decision: **PROCEED_B4_EXTERNAL_VALIDATION**. The current allowed statement is that PSC radial modulation/candidate selection and dual-frequency direction conflicts have repeatable causal decode responses, while the risk-ranking consequence is endpoint-dependent. It is not yet permissible to claim an externally validated repair, universal PSC failure, or ranking-only AP-invariant fix.
