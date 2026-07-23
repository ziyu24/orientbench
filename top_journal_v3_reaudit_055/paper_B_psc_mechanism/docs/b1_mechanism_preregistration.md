# B1 PSC mechanism preregistration

Frozen at `2026-07-22 16:14:00 CST`, before B2/B3 computation. No additional hypothesis, score, endpoint, intervention grid, or favorable post-hoc subgroup may be added in this stage.

## Risk endpoints

- `endpoint_continuous`: le90 circular absolute angle error in degrees. The inherited observation is reverse ranking by `phase_mod` in all DIOR-R, SODA-A, and FAIR1M PSC seeds.
- `endpoint_severe_event`: `angle_error > delta_theta_0.75(aspect_ratio)` under the frozen concentric, same-scale geometry. Its inherited `phase_mod` direction varies by dataset and seed.

Every result must name its endpoint. A result for one endpoint cannot be transferred to the other.

## Frozen hypotheses

- **H1 radial decoding sensitivity.** Radial scaling can alter decode, the modulation-threshold state, loss, or numerical boundary response; magnitude is not necessarily a nuisance scale.
- **H2 wrapping/boundary-conditioned failure.** Large errors and reverse ranking concentrate around phase wrapping or candidate-switch boundaries and respond to a controlled boundary crossing.
- **H3 multi-frequency disagreement.** Circular disagreement and unwrap energy gap respond to controlled inter-frequency conflict and are closer to risk than radial magnitude.
- **H4 directional confidence mismatch.** Phase-direction margin and TTA phase-direction consistency respond coherently to directional perturbation and differ from magnitude.

No H5 or open-ended mechanism search is allowed.

## Frozen candidates

1. `tta_phase_direction_consistency = -circular_variance(2*theta_tta)`.
2. `multi_frequency_consistency = -circular_distance(theta_f1/2, theta_unwrapped_f2/2)`.
3. `unwrap_candidate_energy_gap = abs(cos(theta_f1-candidate0)-cos(theta_f1-candidate1))`.
4. `phase_direction_margin = unwrap_candidate_energy_gap * secondary_phase_norm`.

All four were registered after inspecting DIOR-R/SODA-A and are therefore `development-derived`. There is no separately frozen fitted fusion formula in the historical preregistration. FAIR1M is reserved for formula-unchanged confirmation and must not be used to tune these definitions.

## Frozen intervention grids

- Historical radial grid: `k={0.25,0.50,0.75,0.90,1.00,1.10,1.25,1.50,2.00,4.00}`.
- Tangential decoded-angle offsets: `{-15,-7.5,-2,0,2,7.5,15}` degrees, applied synchronously to the two frequency blocks at fixed projected radial norm.
- Single-frequency offsets: the same grid, applied to primary-only or secondary-only phase direction.
- Boundary crossing offsets relative to the closest candidate-switch surface: `{-10,-5,-1,+1,+5,+10}` degrees.
- Boundary strata: near `<10 deg`, intermediate `[10,30) deg`, far `>=30 deg`.
- Main mask: matched predictions with GT aspect ratio `>=2.1`.

Existing full-evaluator radial artifacts are reused without rerunning. Offline vector interventions are performed only on frozen post-NMS matched PSC encodings and cannot establish detector-level AP invariance; such interventions are labeled `MECHANISM_ONLY_NOT_RANKING_ONLY`. Candidate scores computed without changing boxes/classes/NMS are eligible for ranking-only evidence.

## Frozen analysis and success rules

Results are stratified by size, aspect ratio, class, detection score, feature norm, boundary stratum, dataset, and seed. Partial rank correlation, within-bin contrasts, interaction summaries, and image/scene-cluster bootstrap are used where the required fields exist. Missing objectness is explicit because the frozen RetinaNet PSC units have no separate objectness branch.

Mechanism-stage success requires a real PSC-output intervention supporting at least one hypothesis in at least two datasets and multiple seeds, with healthy training and basic confounding controls. A toy model supplies only sufficiency. A vector intervention that changes decoded boxes, NMS membership, or AP cannot support a ranking-only repair claim. This stage does not require any candidate to beat detection score and does not make a repair-level conclusion.
