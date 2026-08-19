# Supplementary material

## S1. Scope and evidence identities

This supplement accompanies *Orientation Reliability in Oriented Object Detection: Geometry-Aware Measurement and Image-Level Risk Control*. It records protocol detail, full machine-readable table locations, evidence identities, negative boundaries, and deterministic reproduction commands. It does not add a detector, change a split, select a new threshold, or promote descriptive results to formal evidence.

The principal evidence families are separated as follows:

- controlled full-evaluator angle perturbation: formal measurement-validity evidence;
- rectangle tolerance and geometry-normalized severe event: deterministic geometry plus formal derived evaluation;
- masked NRC: within-setting audited descriptive ranking evidence;
- image-level fixed-sequence LTT: formal finite-sample control under image exchangeability;
- human long-axis annotation: independent blinded human study;
- local DOTA-v1.0: train/validation evidence only, with post-outcome independently checked components explicitly labeled;
- evaluated selector and angle-head repairs: negative evidence or analysis upper bounds only.

The source-to-claim mapping is in `evidence_map.csv` and `claim_ledger.csv`. Every final numeric manuscript or figure claim covered by the validator has an exact source path, exact row selector, transform, expected value, and tolerance in `audit_bundles/r044/claim_spec.csv`.

## S2. Matching and orientation conventions

### S2.1 Long-side canonicalization

For each oriented box, the side labels are canonicalized so that the reported width is the long side and the angle refers to that axis. Angular differences are reduced modulo 180 degrees to the interval [0, 90]. This avoids treating antiparallel axes as different while preserving the difference between the long and short axis.

Boxes that fail finite-value, positive-side, or canonicalization checks are excluded from matched-angle analyses. The main population additionally requires matched-ground-truth aspect ratio at least 2.1 and excludes prediction or ground-truth boxes flagged as near-square. These exclusions are applied after class-constrained matching and before risk summaries.

### S2.2 Deterministic matching

Predictions are processed in the same stable confidence order as the complete evaluator. A prediction can match at most one previously unmatched object of the same class, and a ground-truth object can match at most one prediction. The minimum rotated IoU is 0.5. Orientation risk is undefined for unmatched predictions, so unmatched items are excluded from the angle denominator. They are not removed from AP computation.

This distinction matters when interpreting coverage. Instance coverage is the retained fraction among eligible matched predictions, not recall among all ground-truth objects and not a fraction of all predictions. Nonempty-image proportion reports the fraction of complete evaluation images containing at least one retained eligible prediction.

## S3. Controlled perturbation and reverse control

The full table is `tables/controlled_perturbation.csv`. For each original eligible match, the perturbation rotates the prediction away from the reference angle until just before its pairwise rotated IoU would fall below 0.5. Center, side lengths, confidence, class, and prediction identity remain fixed. Unmatched predictions remain fixed. After intervention, the complete evaluation code reruns classwise matching and AP.

All six rows have identical original and perturbed AP50 and identical false-positive counts at IoU 0.5. The smallest AP75 loss is 0.1731 and the largest is 0.6166. The smallest mean angular increase is 29.186 degrees and the largest is 31.886 degrees. The construction demonstrates non-identification by AP50; it is not an estimate of naturally occurring corruption.

The reverse-control table is `tables/reverse_control.csv`. It applies center or scale changes without changing angle. AP50 and AP75 decrease while the angle-risk change is exactly described as zero. Because localization and orientation interventions move different outputs, the combined evidence supports separate reporting.

## S4. Rectangle tolerance calculation

The input curve is `tables/geometry_tolerance_curve.csv`. The reference rectangles have unit area, aspect ratio (a\), common center, and a relative angle (\delta\). Their vertices are constructed analytically, polygon intersection is evaluated deterministically, and the first strict crossing below IoU (\tau\) is found by bisection. The solve tolerance is 0.001 degrees.

For very large aspect ratios beyond the finite lookup grid, the frozen implementation uses a conservative inverse-aspect-ratio tail with a two-solve-tolerance subtraction. No evaluated principal-domain row exceeds the extended grid maximum. The (a=2.1) event threshold is 15.3297 degrees. The numerical curve is a deterministic property of the stated rectangle model and does not use detector outcomes.

The severe event (Y_i=1\{e_i>\delta_{0.75}(a_i)\}\) is evaluated with matched-ground-truth aspect ratio. It does not assert a causal angle-only IoU for the observed, noncongruent prediction pair. Fixed 5-, 10-, and 15-degree events are sensitivity analyses.

## S5. NRC implementation details

Scores are sorted in declared descending reliability order. Stable ties preserve input order. Risk at coverage uses the retained conditional mean of canonical error. AURC is computed on the fixed coverage grid used by the source analysis. Oracle ranking sorts increasing error. Random AURC is the expectation under random permutation of the same error vector. NRC is normalized by the oracle-to-random gap.

The representative rows in `tables/representative_nrc.csv` use an aspect-ratio threshold of 1.6 because that is the frozen source table's population. They are therefore labeled representative rather than substituted into the (a\geq2.1) formal severe-risk table. The manuscript does not pool these NRC values into a cross-dataset correlation.

Confidence intervals resample complete images. All instances in a sampled image enter with the same multiplicity. This preserves image-level dependence. The procedure estimates uncertainty of the empirical ranking result; it is not a conformal guarantee.

## S6. Image-level finite-sample control

### S6.1 Population and loss

The full evaluation-image universe is fixed before score thresholding. An image without an eligible matched prediction remains in the universe. For each threshold, the bounded image loss is the average geometry-normalized severe-event indicator among retained eligible matches or zero when none are retained. Thus every image contributes one value in [0,1].

The secondary any-failure event is binary and can receive an exact Clopper--Pearson bound. The primary average image loss is bounded but not Bernoulli; it uses Hoeffding--Bentkus. Empirical instance-weighted risk is reported with image-cluster uncertainty and is not treated as a finite-sample iid guarantee.

### S6.2 Data separation

The outer calibration partition is split deterministically into a fit subset and a calibration subset. Candidate thresholds are functions of the fit subset only. The calibration subset evaluates and certifies the fixed candidates. The held-out reporting subset is not used in fitting, threshold definition, testing, or the overall selection decision.

Families are indexed by unit, score, risk event, and target budget. Candidate target coverages run from conservative to permissive in a fixed sequence. At each candidate the null is that expected image loss exceeds the target budget. Testing stops on the first candidate that cannot be rejected. This ordering avoids searching the entire coverage grid and then reporting only its best point.

### S6.3 Image versus instance counterfactual

`tables/image_vs_iid_bound.csv` contains one principal detection-score row per unit at alpha 0.03. `new_image_ucb_calib` is the formal image-level value. `old_instance_iid_cp_ucb_calib_audit_only` is retained solely to illustrate the invalid-independence counterfactual. The latter treats retained instances as independent Bernoulli trials, even though they are nested in images. It is never used to select or certify the manuscript result.

## S7. Human annotation protocol

The primary sample contains 600 targets: 200 from each of DIOR-R, FAIR1M-v1.0, and SODA-A. Two distinct annotators received the same target identities in different random orders. Neither task exposed model angle, ground-truth angle, the other annotator's response, or fields that would identify the intended result. Responses allowed a numeric long-axis angle or a nonnumeric ambiguity/skip state.

The 450 double-numeric outcomes define the primary circular-disagreement endpoint. A source-image cluster bootstrap with 10,000 replicates yields the mean intervals. Nonnumeric decisions are not converted to zero. A secondary blind recheck of 29 one-sided nonnumeric cases yields 27 numeric comparisons and two remaining ambiguities; this endpoint does not overwrite primary outcomes.

The main human summary is `tables/human_disagreement.csv`. The overall mean is 2.3112 degrees; p90 and p95 are 4.4220 and 5.9359. The 5-degree exceedance probability is 0.0800, and the 10-degree probability is 0.008889. SODA-A has the largest mean and tail. The (a\geq2.1) subset contains 308 pairs with mean 2.2823 degrees.

The study estimates inter-annotator disagreement on the sampled tasks. It does not estimate dataset ground-truth error, physical heading error, or an additive noise term. No detector error is corrected by subtracting human disagreement.

## S8. Negative scientific boundaries

No evaluated repair is presented as a positive method contribution. The earlier nonlinear geometry selector is an analysis upper bound whose dominant apparent reversal was tied to the aspect-ratio-defined estimand component. The set-valued transfer approach did not establish transferable coverage benefit. The evaluated orientation-error ranking variants did not improve the prespecified generalized risk--coverage contrast. The evaluated symmetric angular-head configuration caused large AP regressions. Because its implemented gating differed from the frozen formula, only that configuration is rejected; broader impossibility is not inferred.

These results justify the manuscript's measurement-diagnostic scope. The framework can evaluate and, with labeled calibration images, control a declared risk. It does not correct an angle or provide a target-label-free selector.

## S9. Machine-readable tables

- `controlled_perturbation.csv`: all six full-evaluator intervention rows.
- `reverse_control.csv`: representative center and scale controls.
- `geometry_tolerance_curve.csv`: all deterministic aspect-ratio tolerance rows.
- `geometry_normalized_risk.csv`: eight principal geometry-risk units.
- `representative_nrc.csv`: detection-score and intrinsic-phase NRC examples.
- `image_level_ltt_primary.csv`: selected principal LTT rows at alpha 0.03.
- `image_vs_iid_bound.csv`: formal image-level and invalid iid counterfactual values.
- `human_disagreement.csv`: overall, dataset, and aspect-ratio human summaries.
- `evidence_identity.csv`: evidence-status and allowed-use labels.

## S10. Reproduction commands

From the repository root, with the declared analysis environment available:

```bash
conda run -n ai4rs python outputs/persistent_artifacts/orientbench_jprs_manuscript_r044_20260818/build_package.py
python audit_bundles/r044/validate_claims.py
python audit_bundles/r044/run_mutations.py
```

The first command reads only tracked derived evidence and generates CSV, SVG, and PNG outputs. The second performs exact path/key claim validation. The third creates three isolated mutations under the manuscript audit directory, verifies that pristine validation exits zero, and verifies that each mutated input exits nonzero. No command trains a model, runs detector inference, or accesses raw imagery.

## S11. Reproducibility boundaries

The package manifest records size, SHA-256, and `can_recompute` for each in-scope artifact. Derived tables and figures are recomputable from tracked evidence. The manuscript, red-team reports, and submission attachments are authored documents and are marked as such. Raw or matched prediction artifacts needed for upstream scientific recomputation remain in their existing tracked persistent locations and are referenced rather than duplicated.

Reproducibility does not turn a post-outcome analysis into a prospective one. It verifies that stated numbers and transformations match persisted sources. Scientific interpretation still depends on the declared population, split, evidence identity, and limitations.
