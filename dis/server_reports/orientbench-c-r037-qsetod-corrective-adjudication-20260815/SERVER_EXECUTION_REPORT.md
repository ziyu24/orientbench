# SERVER EXECUTION REPORT — orientbench-c-r037-qsetod-corrective-adjudication-20260815

## 1. Execution receipt

- Execution status: `complete`
- Completion mode: `full_completion`
- Registered candidate: `QSETOD_EVIDENCE_SCORE_ONLY`
- `G_EVIDENCE=PASS`
- `G_SET=FAIL`
- Multimodality: `MULTIMODALITY_NOT_ADJUDICATED`
- Starting dispatch commit: `1cc00e7b5ff6ce32efbea497ee23e6af32d2aec7`
- STARTED commit: `0fb717df6d5806106c27c1bb0161878e826d365e`
- Ending scientific-results commit: `8aa9863ad953ba374e794784f1d564e510bb97ad`
- Worker: `server-primary`
- Environment: existing conda environment `pcp-obb`; Python 3.10.20, NumPy 1.24.4, pandas 2.0.3, SciPy 1.15.3, scikit-learn 1.7.2

This round is fully executed. `G_SET=FAIL` is the registered scientific outcome, not an execution failure. It does not authorize Q-SetOD training or a venue upgrade.

## 2. Identity, input, and phase isolation

- Active root plan and committed C plan both had Git blob `5a1a5508b8182dd0353b8cc91398fce7b1282b52` and SHA-256 `65e67bee39ecceda6b8e5a66a73a330a9a9078b5bd94db13946fd70bde8786e1`.
- Locked r036 rows: Git blob `1b348e35dfbe0a699a7bc6cbe79e639fb25384f5`, 34,796,105 bytes, SHA-256 `bb4184089a0cb9e0584cdf9fe340fe76a5d831090f07a6bc0c73e4499ac8da51`.
- Cohort: 616,184 rows, units A--H unchanged.
- Separate runtime views were created for source labels, target covariates, and target evaluation labels.
- Target predictions were sealed before evaluation-label views were opened.
- Fit ledger: 108 estimator fits per implementation/recomputation; `target_label_rows_in_fit=0` throughout.
- Clean endpoint access count: 0. The carried r036 endpoint inventory remained `inventory_not_authorization=true`.
- DOTA-v2.0 and SODA-A official-test clean labels were not listed, opened, decoded, hashed, or used.

## 3. T2 confidence/TTA decomposition and G_EVIDENCE

The only registered TTA increment was `GCT-GC`. `G-GC` and `G-GCT` were retained only as diagnostic columns. Every row below uses 20,000 complete target-cluster bootstrap replicates with per-replicate weighted midranks and whole-tie AUGRC groups.

| Unit | Delta rho | CI low | Delta q75 | CI low | Delta AUGRC | CI low | Holm-8 p | Witness |
|---|---:|---:|---:|---:|---:|---:|---:|:---:|
| B | 0.036274 | 0.024437 | 0.381660 | 0.299620 | 0.000769 | 0.000610 | 0.000400 | yes |
| C | 0.034452 | 0.028694 | -0.449116 | -0.614105 | 0.000288 | 0.000183 | 1.000000 | no |
| A | 0.066740 | 0.060435 | 0.185556 | 0.134756 | 0.000633 | 0.000520 | 0.000400 | yes |
| D | 0.012647 | -0.011492 | 0.188618 | 0.109377 | 0.000047 | -0.000104 | 0.519074 | no |
| E | 0.057232 | 0.041624 | 0.305089 | 0.205217 | 0.000982 | 0.000404 | 0.002000 | yes |
| F | 0.050496 | 0.037432 | 0.190155 | 0.101615 | 0.001215 | 0.000594 | 0.000400 | yes |
| G | 0.044552 | 0.028699 | 0.153561 | 0.082554 | 0.000445 | 0.000146 | 0.012299 | no |
| H | 0.028050 | 0.015626 | 0.076532 | 0.025369 | 0.000281 | 0.000162 | 0.003800 | no |

Witnesses were B, A, E, and F: 4/8, two target datasets, two detector families, and two cross-dataset units. Therefore `G_EVIDENCE=PASS` exactly at the registered threshold.

## 4. T3 interval validity, efficiency, and proper interval score

All intervals used source-only finite-sample higher quantiles and source-defined predicted-AR x predicted-size buckets. Class was not used in the primary Mondrian bucket. Coverage failure used only the registered lower-tail deficit; overcoverage was not treated as invalidity.

| Unit | alpha | coverage | overall pass | worst supported bucket | bucket pass | median width | >150 rate | fallback | IS GC | IS GCT | standardized gain | efficiency pass |
|---|---:|---:|:---:|---:|:---:|---:|---:|---:|---:|---:|---:|:---:|
| B | 0.1 | 0.924293 | yes | 0.883721 | yes | 11.6778 | 0.125732 | 0 | 73.2104 | 64.9801 | 0.112420 | no |
| B | 0.2 | 0.827735 | yes | 0.770627 | yes | 7.2753 | 0.102790 | 0 | 54.3956 | 50.0586 | 0.079731 | no |
| C | 0.1 | 0.885334 | yes | 0.613765 | no | 12.0419 | 0.071021 | 0 | 64.3266 | 84.7299 | -0.317181 | yes |
| C | 0.2 | 0.765230 | yes | 0.566513 | no | 7.4642 | 0.047724 | 0 | 52.5794 | 59.8095 | -0.137509 | yes |
| A | 0.1 | 0.895981 | yes | 0.852575 | yes | 8.6202 | 0.130298 | 0 | 71.4956 | 73.1622 | -0.023311 | no |
| A | 0.2 | 0.804302 | yes | 0.711930 | yes | 6.0830 | 0.115722 | 0 | 56.4517 | 55.3060 | 0.020297 | no |
| D | 0.1 | 0.925685 | yes | 0.815182 | yes | 8.1121 | 0.005822 | 0 | 18.5442 | 15.5913 | 0.159239 | yes |
| D | 0.2 | 0.823630 | yes | 0.686469 | no | 5.6878 | 0.004110 | 0 | 13.7239 | 11.9009 | 0.132829 | yes |
| E | 0.1 | 0.901644 | yes | 0.856397 | yes | 12.3993 | 0.218854 | 0 | 100.7401 | 101.7701 | -0.010224 | no |
| E | 0.2 | 0.786114 | yes | 0.706856 | yes | 8.2995 | 0.206932 | 0 | 79.0229 | 76.5550 | 0.031230 | no |
| F | 0.1 | 0.885412 | yes | 0.846154 | yes | 11.2055 | 0.210086 | 0 | 100.5788 | 100.2759 | 0.003011 | no |
| F | 0.2 | 0.758223 | yes | 0.701371 | yes | 7.5074 | 0.191798 | 0 | 76.6596 | 75.0966 | 0.020389 | no |
| G | 0.1 | 0.888459 | yes | 0.810207 | yes | 9.1604 | 0.117761 | 0 | 58.7098 | 55.5757 | 0.053383 | no |
| G | 0.2 | 0.757646 | yes | 0.649819 | no | 6.2979 | 0.105160 | 0 | 45.0008 | 43.3336 | 0.037048 | no |
| H | 0.1 | 0.908371 | yes | 0.809816 | yes | 9.4130 | 0.139356 | 0 | 51.1538 | 50.7592 | 0.007715 | no |
| H | 0.2 | 0.786126 | yes | 0.674847 | no | 6.4182 | 0.130569 | 0 | 43.1073 | 42.4755 | 0.014658 | no |

All 16 overall lower-tail validity rows passed. Supported-bucket and/or near-full-width hard conditions failed in multiple units, so no unit could satisfy both-alpha hard validity and efficiency.

| Unit | Set gain | 95% CI | Holm-8 p | Both-alpha hard pass | Set witness |
|---|---:|---:|---:|:---:|:---:|
| B | 0.096076 | [0.078411, 0.113324] | 0.000400 | no | no |
| C | -0.227345 | [-0.272016, -0.183055] | 1.000000 | no | no |
| A | -0.001507 | [-0.015030, 0.012290] | 1.000000 | no | no |
| D | 0.146034 | [0.074083, 0.220237] | 0.000400 | no | no |
| E | 0.010503 | [-0.006642, 0.029084] | 0.447778 | no | no |
| F | 0.011700 | [-0.003376, 0.026670] | 0.327234 | no | no |
| G | 0.045215 | [0.024279, 0.068830] | 0.000400 | no | no |
| H | 0.011186 | [-0.009635, 0.038505] | 0.480726 | no | no |

Set witnesses: 0/8. Therefore `G_SET=FAIL` and the registered mapping is `QSETOD_EVIDENCE_SCORE_ONLY`.

## 5. Multimodality

The existing environment could not import a formal `diptest` package. No package was installed, no network was used, and no approximate dip implementation was substituted. Frozen fixtures were therefore not run. Status is `MULTIMODALITY_NOT_ADJUDICATED`, and the multi-arc/multimodality claim must be deleted. This status did not rescue or alter either gate.

## 6. Independent implementations and adversarial audit

- A/B comparator: `PASS`; 16,787,656 compared fields, maximum absolute difference 0 at `atol=1e-10, rtol=0`.
- A/B support keys, all per-config 20,000 multiplicity matrices, bootstrap replicates, predictions, T2/T3 tables, and final judgment matched.
- Self-contained raw validator imported neither A nor B; it independently refit 108 estimators, regenerated all multiplicities, recomputed weighted midranks, whole-tie AUGRC, interval scores, CI/p/Holm values, and the final token.
- Raw validator: `PASS`; 33,575,312 compared fields, maximum absolute difference 0.
- Bundle-internal validator replay: `PASS`.
- Eight real temporary-copy subprocess mutations were all rejected with nonzero exit: wrong registered increment, removing score from GC, fixed observed ranks, absolute coverage semantics, class-by-AR primary buckets, interval-score penalty tamper, final-token tamper, and target-label fit-ledger tamper.

## 7. Resources and deviations

- GPU/CUDA use: 0.
- Neural-network training: 0.
- Detector forward/inference: 0.
- Downloads/new datasets: 0.
- Formal workers: 90/112 logical CPUs (80.36%).
- Accepted formal recomputation was sampled every second, stricter than the registered 30-second cadence.
- Peak aggregate CPU: about 107.4 cores in fitting and 101.7 cores in bootstrap evaluation.
- The 11.2-second interval aggregation was serial and shorter than one 30-second reporting interval; this deterministic matrix/reduction section is recorded in `resource_usage.json` and is not sustained under-utilization.
- Exact `diptest` unavailability is the registered `MULTIMODALITY_NOT_ADJUDICATED` branch, not a substituted approximation.
- Pre-final implementation/API corrections were excluded from accepted artifacts; A/B, strict monitored recomputation, validator, mutations, and bundle replay all passed afterward. No frozen threshold, split, formal/exploratory label, r034/r036 artifact, protected B/C file, or endpoint policy was changed.

No execution failure, kill condition, or protocol drift was triggered. The only stopping branch is the normal scientific mapping caused by `G_SET=FAIL`.

## 8. Persistent paths

- Summary and executable code: `top_journal_v3_reaudit_055/qsetod_corrective_r037_20260815/`
- Persistent runtime artifacts: `outputs/persistent_artifacts/orientbench_qsetod_corrective_r037_20260815/`
- Portable audit bundle: `audit_bundles/r037/`
- Bundle manifest: `audit_bundles/r037/bundle_manifest.csv`
- Bundle size: 563,404,008 non-self bytes across 104 verified objects; every tracked object is below 80 MiB.
- Bundle verifier: `PASS`.
- Scientific results commit was pushed to `origin/main`; the push transferred 215.76 MiB after Git object deduplication.

## 9. Required scientific interpretation

TTA evidence retains measurable predictive information after geometry, class, size, and detector confidence are exhausted. However, it does not produce a registered-valid, efficient source-only interval transport method. Retain only a scalar evidence-quality candidate; delete set/coverage and multi-arc claims; do not authorize training; do not upgrade the paper venue from this result.
