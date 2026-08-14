# Aspect-Ratio Eligibility Changes Orientation-Reliability Conclusions in Oriented Object Detection

[作者与单位：由项目所有者定稿填写]

## Abstract

Confidence-based selection is meaningful only when the retained predictions are ordered by the risk that an application actually cares about. For oriented object detection, that risk is difficult to define because angle is periodic, the long-axis representation is equivariant under a half turn, and nearly square boxes have weakly identifiable orientation. We study the measurement validity of orientation reliability rather than proposing a new detector. The protocol canonicalizes every oriented box to its long side, normalizes canonical angle error by the aspect-ratio-dependent rotation required to cross an intersection-over-union threshold of 0.75, and evaluates four frozen confidence probes with generalized risk--coverage area and fixed-coverage risk. A five-ablation design asks whether the ordering between detector confidence and a frozen score--aspect-ratio--size probe reverses when the aspect-ratio eligibility domain or risk geometry is changed. On DIOR-R, seven formal witnesses establish an aspect-ratio-domain signature, while the prespecified cross-dataset gate remains `INCONCLUSIVE_MIXED` because FAIR1M and SODA-A do not reproduce it. A DOTA-v1.0 study with Oriented R-CNN and Rotated RTMDet reproduces the dataset-level signature and the RTMDet unit signature, but is identified strictly as `POST_OUTCOME_AUDITED_EXTERNAL_REPLICATION`. Raw-layer revalidation, semantic mutation tests, and an independently replayed Git bundle close the computational audit. The evidence supports a narrow conclusion: orientation-reliability rankings can flip when aspect-ratio eligibility is left implicit; it does not establish a universal detector defect or a deployable selector.

**Keywords:** oriented object detection; selective prediction; risk--coverage; measurement validity; angle periodicity; aspect ratio; reproducibility

## 1. Introduction

Average precision combines classification, localization, matching, and ranking. It therefore cannot by itself answer whether a high-confidence oriented detection has a more trustworthy angle than a lower-confidence detection. This distinction matters for ships, aircraft, vehicles, and other elongated objects whose heading is operationally meaningful. It is also easy to measure incorrectly. Under a long-side convention, orientation is periodic over 180 degrees, while the same angular error has radically different geometric consequences for a near-square and a slender rectangle.

Selective prediction evaluates a confidence score through the risk of predictions retained at decreasing coverage. Yet a risk--coverage summary inherits every choice in the risk definition and eligibility set. In oriented detection, using all aspect ratios without declaring how square-like objects are treated can reverse the comparison between confidence scores. We call this an aspect-ratio-domain signature. The central question is not whether one score wins everywhere, but whether the measurement conclusion is stable under prespecified changes to angle equivalence, geometric normalization, aspect-ratio domain, ranking probe, and detector family.

This work makes four contributions. First, it gives a fully specified orientation-risk protocol combining long-axis canonicalization, an aspect-ratio-dependent geometric tolerance, generalized risk--coverage, and cluster-aware uncertainty. Second, it formalizes a five-ablation witness criterion with effect-size floors, acceptance-set swaps, multiplicity control, and a four-state gate. Third, it reports the complete formal DIOR-R result and a DOTA-v1.0 external replication with an explicit post-outcome audit identity, including the negative Oriented R-CNN unit result. Fourth, it provides raw validators, real semantic mutations, provenance manifests, and a Git-tracked replay bundle. The scope is measurement validity: no DOTA test-set comparison, state-of-the-art claim, universal calibration claim, or deployable-method claim is made.

## 2. Related work

### 2.1 Selective prediction and risk--coverage

Selective classification studies prediction with a reject option [13--15]. Area under the risk--coverage curve is widely used, while Traub et al. [16] distinguish selective risk from generalized risk and motivate AUGRC for aggregation across operating points. Our endpoint is an oriented-box angle risk; the contribution is the explicit geometric and eligibility-domain definition supplied to that evaluation.

### 2.2 Detection confidence and calibration

Calibration methods relate predictive confidence to empirical correctness [17]. Detection-specific work extends calibration to class and localization outputs [18,19], and self-aware detection evaluates uncertainty and failure awareness [20]. These approaches motivate examining detection score as a reliability proxy, but confidence calibration and orientation-risk ordering are not interchangeable.

### 2.3 Oriented detection, periodicity, and square-like ambiguity

DOTA, DIOR-R, FAIR1M, and SODA-A provide aerial-image benchmarks with oriented annotations [1--4]. Oriented R-CNN and RTMDet represent two detector families used in our external study [5,6]. CSL, DCL, and PSC address angular boundary discontinuity through circular, dense, or phase-based coding [7--9]. GWD and KLD express oriented boxes as distributions to reduce regression discontinuities [10,11]. These methods improve representation or loss design; they do not remove long-axis equivalence or the weak orientation identifiability of square-like boxes. ARS-DETR explicitly links aspect ratio to orientation sensitivity [12].

### 2.4 Uncertainty and distribution-free risk control

Conformal prediction and learn-then-test procedures provide distribution-free tools for prediction sets or risk control [21--24]. Our bootstrap inference is not a conformal guarantee. We use the literature to separate empirical ranking evidence from stronger deployment guarantees that are absent here.

## 3. Evidence base

### 3.1 Frozen evaluation units

<!-- SOURCE: dis/reviews/C/orientbench-r029-final-replay-review-20260813.md -->
The core archive contains six detector--head evaluation units, denoted A--F, across DIOR-R, FAIR1M, and SODA-A. The DIOR-R units define the source measurement-validity result. FAIR1M and SODA-A are prespecified boundary tests, not additional positive examples. The DOTA-v1.0 study uses local train/val models only and contains two units: Oriented R-CNN and Rotated RTMDet. Its persisted GT conversion contains 5,297 tiles, 458 mother scenes, and 55,804 nonignored objects. The matched all-aspect-ratio tables contain 48,889 and 51,736 rows, respectively.
<!-- END_SOURCE -->

### 3.2 Matching and ground truth

Orientation risk is evaluated only on deterministic matched prediction--GT pairs. Full detection AP is evaluated separately and is never replaced by matched-only statistics. DOTA GT was reconstructed from the persisted prelabel conversion because the migrated host does not retain the original split annotation files. The bundle records the conversion hash, class totals, tile-to-mother map, and proof that each detector's matched GT identifiers are subsets of the converted GT universe.

### 3.3 Frozen score probes

<!-- SOURCE: top_journal_v3_reaudit_055/jprs_paper_package_r027_20260813/build_package.py -->
Four probes are retained: detector `raw_confidence`; `linear_source_frozen`, a per-source logistic linear score using an intercept, logit confidence, log predicted aspect ratio, and half log predicted area; `tta_angle`, based on augmentation angle consistency; and `tta_localization`, defined in the corrected descriptive package as the negative sum of missing fraction and IoU loss. The formal DIOR/DOTA contrast is `linear_source_frozen - raw_confidence`. TTA probes are descriptive and are not promoted into formal witnesses. The FAIR1M-source coefficient vector is (-0.26525345, 0.01355104, 0.00337013, 0.02027136), and the SODA-source vector is (-0.21289442, 0.01466760, -0.01161673, 0.00892121), ordered as listed above.
<!-- END_SOURCE -->

## 4. Measurement protocol

### 4.1 Canonical orientation error

Let an oriented rectangle be represented by center, long side, short side, and long-axis angle. After swapping sides when necessary, the periodic canonical error is

$$e_{\mathrm{can}}=\min_{k\in\mathbb{Z}}|\theta_p-\theta_g+180k|,$$

restricted to the first long-axis lobe. This makes a half turn equivalent but does not equate orthogonal axes.

### 4.2 Geometry-normalized risk

For GT aspect ratio $a\geq1$, let $\delta_{0.75}(a)$ be the smallest long-axis rotation at which two concentric, congruent, same-scale rectangles fall below IoU 0.75. The continuous risk is

$$r_{\mathrm{geo}}=\frac{1}{3}\operatorname{clip}\left(\frac{e_{\mathrm{can}}}{\max(\delta_{0.75}(a),1)},0,3\right).$$

The frozen engineering boundary is $a\geq2.1$; the direct geometric crossing of a 15-degree tolerance occurs near $a=2.15$. The main domain is `MAIN_AR_GE_2.1`; the principal ablation is `NORMALIZED_ALL_AR`.

### 4.3 Generalized risk--coverage endpoints

For a score $s$, sort predictions in descending order with stable tie handling. At retained coverage $c$, generalized risk divides cumulative retained risk by the full sample size, $G_s(c)=n^{-1}\sum_{j\leq\lceil cn\rceil}r_{(j)}$. We report

$$\operatorname{AUGRC}(s)=\int_0^1G_s(c)\,dc,$$

with its exact tie-block trapezoidal implementation, plus conditional `Risk@70` and descriptive `Risk@90`. Lower values are preferable. The formal contrast is $\Delta=\mathrm{metric}(\mathrm{linear})-\mathrm{metric}(\mathrm{raw})$; positive $\Delta$ means raw confidence is better.

### 4.4 Ablations and inference

The five frozen ablations are: `NO_LONGSIDE_AR21` for angle equivalence, `NO_GEONORM_AR21` for geometric normalization, `NORMALIZED_ALL_AR` for eligibility domain, source-probe changes for score provenance, and detector/dataset changes for host dependence. Bootstrap resampling uses image clusters for the core archive and mother-scene clusters for DOTA. It never treats matched instances as independent.

For each contrast, the difference-of-differences is $D=\Delta_{\mathrm{main}}-\Delta_{\mathrm{ablation}}$. A witness requires all of the following: the main interval exceeds its frozen effect floor; the ablation interval lies beyond the opposite floor; the Holm-adjusted centered-bootstrap probability is below 0.05; the interval for $D$ excludes zero; $|D|$ exceeds the sum of both floors; and fixed-coverage endpoints satisfy the frozen acceptance-set-swap threshold. The four gate states are `SUPPORTED`, `NOT_SUPPORTED`, `INCONCLUSIVE_MIXED`, and `INVALID`. They distinguish positive evidence, valid negative evidence, mixed cross-unit evidence, and protocol failure.

## 5. Results

### 5.1 DIOR-R formal result and cross-dataset gate

The frozen r023 analysis contains seven witnesses, all for the `NORMALIZED_ALL_AR` eligibility ablation. Positive main-domain deltas become negative when all aspect ratios are admitted. Values below are copied from the frozen formal table; CI is the interval for $D$.

<!-- SOURCE: outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/r023_formal_witnesses.csv -->
| Level | Unit | Endpoint | Main $\Delta$ | All-AR $\Delta$ | $D$ | 95% CI for $D$ | Holm $p$ | Witness |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| unit | A | AUGRC | 0.000967 | -0.010815 | 0.011782 | [0.010617, 0.012959] | 0.026997 | yes |
| unit | A | Risk@70 | 0.002402 | -0.026408 | 0.028810 | [0.024324, 0.033572] | 0.026997 | yes |
| unit | B | AUGRC | 0.000675 | -0.008161 | 0.008836 | [0.008003, 0.009679] | 0.026997 | yes |
| unit | C | AUGRC | 0.002844 | -0.010645 | 0.013489 | [0.012180, 0.014876] | 0.026997 | yes |
| unit | C | Risk@70 | 0.004331 | -0.021609 | 0.025940 | [0.022237, 0.030576] | 0.026997 | yes |
| dataset | DIOR-R | AUGRC | 0.001496 | -0.009874 | 0.011369 | [0.010350, 0.012421] | 0.013499 | yes |
| dataset | DIOR-R | Risk@70 | 0.002706 | -0.022060 | 0.024766 | [0.021215, 0.028579] | 0.013499 | yes |
<!-- END_SOURCE -->

The cross-dataset gate is nevertheless `INCONCLUSIVE_MIXED`: FAIR1M and SODA-A do not reproduce the complete signature. This gate is not a contradiction of the DIOR-R rows; it limits their external scope.

### 5.2 DOTA-v1.0 audited external replication

The DOTA result is identified as **`POST_OUTCOME_AUDITED_EXTERNAL_REPLICATION`**. The hypotheses and source-probe structure predate the first DOTA outcome, but the corrective raw audit occurred after outcome revelation. The table includes all six formal rows, including the Oriented R-CNN non-witnesses.

<!-- SOURCE: outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/r026_formal_hypotheses.csv -->
| Level | Unit | Endpoint | Main $\Delta$ | All-AR $\Delta$ | $D$ | 95% CI for $D$ | Holm $p$ | Witness |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| unit | Oriented R-CNN | AUGRC | 0.000354 | -0.012315 | 0.012670 | [0.007361, 0.018673] | 0.000400 | no |
| unit | Oriented R-CNN | Risk@70 | 0.001109 | -0.022964 | 0.024073 | [0.013012, 0.036702] | 0.000400 | no |
| unit | Rotated RTMDet | AUGRC | 0.002363 | -0.013610 | 0.015973 | [0.009216, 0.023615] | 0.000400 | yes |
| unit | Rotated RTMDet | Risk@70 | 0.004339 | -0.029604 | 0.033943 | [0.019124, 0.051336] | 0.000400 | yes |
| dataset | DOTA-v1.0 | AUGRC | 0.001358 | -0.012963 | 0.014321 | [0.008337, 0.021029] | 0.000200 | yes |
| dataset | DOTA-v1.0 | Risk@70 | 0.002724 | -0.026284 | 0.029008 | [0.016474, 0.043630] | 0.000200 | yes |
<!-- END_SOURCE -->

The aggregate and RTMDet rows support the directional signature. The Oriented R-CNN point estimates have the specified direction, but their main-domain effect conditions fail; they remain negative unit-level results. The joint B/C scientific state after bundle replay is `AUDITED_EXTERNAL_REPLICATION_ACCEPTED`, which describes audit acceptance rather than pre-outcome independence.

### 5.3 FAIR1M and SODA-A boundary

Neither FAIR1M nor SODA-A supplies the complete prespecified cross-dataset signature. We therefore do not generalize the DIOR/DOTA pattern to PSC heads, all datasets, or all oriented detectors. In particular, the evidence does not establish that a PSC angle head itself is miscalibrated; prior Track-B observations concern detection-score selection at the detector/dataset level.

### 5.4 Descriptive analyses

AR-threshold scans, beta-source sensitivity, Risk@90, class decomposition, and corrected TTA-localization tables are reported only as `DESCRIPTIVE`. The corrected DOTA AR scan visualizes the archived TTA-localization AUGRC across cutoffs but does not optimize a new cutoff. The beta-source table tests the two archived coefficient vectors without refitting on DOTA. Per-class estimates with fewer than 500 rows are flagged as low reliability. The corrected TTA-localization score is $-(\mathrm{missing\ fraction}+\mathrm{IoU\ loss})$; earlier affected r027 tables are superseded by r028 and are not used here.

## 6. Audit and reproducibility

### 6.1 Independent computations and comparator

The DIOR calculation was reproduced from archived hypothesis-level bootstrap replicates, covering 405 hypotheses and 4,950 checked fields. The DOTA raw validator independently recomputed matching-table integrity, geometric risk, point estimates, confidence intervals, multiplicity, swaps, witnesses, and gate rows; all 96 checked fields agreed with the frozen r026 table. The validator does not import the earlier analysis implementation.

### 6.2 Semantic mutation tests

Six subprocess mutations target GT angle--risk consistency, tile-to-mother identity, aspect-ratio domain, bootstrap-cell pairing, swap predicates, and report-state agreement. Every pristine invocation exited successfully and every mutated invocation failed. Stdout, stderr, and exit codes are retained in the audit record.

### 6.3 Corrective history

The first DOTA audit package omitted two ignored binary objects from Git and initially overstated its evidence identity. r028 corrected the identity, regenerated the erroneous TTA-localization descriptive tables, added independent raw validators and real mutations, and built the replay bundle. r029 then force-added the exact archived `bootstrap.npy` and `dota_gt_fresh.pkl` bytes and verified all 20 manifest objects. C replayed the bundle and B/C resolved the contest as audited external replication. This history is part of the evidence, not hidden provenance noise.

### 6.4 Timeline

| Event | Commit | Date (UTC-07:00) | Role |
|---|---|---|---|
| r024 plan frozen | `0571c2e4` | 2026-08-13 | probe structure |
| r025 first DOTA result | `5ce52c23` | 2026-08-13 | outcome revelation |
| r026 initial closure | `747c0dba` | 2026-08-13 | initial audit claim |
| C contest | `28951bb3` | 2026-08-13 | defect identification |
| r028 corrective plan | `e871b7b2` | 2026-08-13 | post-outcome audit |
| r028 bundle completion | `e675a841` | 2026-08-13 | self-contained replay |
| r029 bundle closure | `fe9d0ea5` | 2026-08-13 | ignored bytes tracked |
| r029 C replay review | `466710e1` | 2026-08-13 | contest resolution |

## 7. Discussion

The principal finding is a measurement warning: a reliability comparison can reverse when square-like objects enter a geometrically normalized angle-risk population. This is stronger than observing that aspect ratio correlates with error, because the formal contrast controls score, AR, and size in a frozen source probe and requires opposite-domain effects. It is weaker than a universal claim: the signature is mixed outside DIOR-R, and only one DOTA unit plus the equal-unit aggregate satisfies the full external witness rule.

The result also separates detector accuracy from orientation reliability. A detector may maintain competitive AP while its confidence ranking is not optimal for retaining low angle-risk matches. Conversely, a reliability probe can improve ranking without changing boxes or AP. The appropriate use is audit and model selection, not automatic deployment. A deployable method would need prospective validation without target-domain angle labels and under dataset shift; those conditions are not met here.

## 8. Limitations

First, DOTA is a single external validation dataset with two detector families. Second, the decisive corrective audit is post-outcome and cannot establish prospective independence. Third, DOTA GT comes from a persisted prelabel conversion on the migrated host; the original split annotation files are unavailable there, although hashes and coverage proofs are retained. Fourth, the Oriented R-CNN unit fails the formal witness rule. Fifth, FAIR1M and SODA-A fail the complete cross-dataset gate, limiting claims about PSC and dataset universality. Sixth, classwise and high-coverage results are descriptive and sometimes sparse. Seventh, the learned EQS route remains a historical negative/exploratory appendix result and is not a deployable contribution. Finally, the protocol measures matched-detection orientation risk; it does not replace full detection evaluation or provide distribution-free operational guarantees.

## 9. Conclusion

Orientation reliability in oriented detection is not well defined until angle equivalence, geometric severity, aspect-ratio eligibility, score provenance, and clustering unit are declared. A frozen five-ablation protocol finds a DIOR-R aspect-ratio-domain signature and an audited DOTA replication at the aggregate and RTMDet levels, while also recording non-replication boundaries and a negative Oriented R-CNN unit result. The resulting claim is deliberately narrow: undeclared aspect-ratio eligibility can change a reliability conclusion. The replay bundle and claim-level provenance make that conclusion inspectable without turning audit acceptance into a broader method or deployment claim.

## Data and code availability

Code, frozen tables, manifests, validators, and replay inputs used for this manuscript are available in the project repository at `https://github.com/ziyu24/orientbench`, principally under `audit_bundles/r028/`. Availability is limited to objects actually tracked there; no unlisted dataset redistribution or future maintenance guarantee is implied.

## References

1. Xia, G.-S., Bai, X., Ding, J., et al. DOTA: A Large-Scale Dataset for Object Detection in Aerial Images. CVPR, 2018.
2. Sun, X., Wang, P., Wang, C., et al. FAIR1M: A Benchmark Dataset for Fine-Grained Object Recognition in High-Resolution Remote Sensing Imagery. ISPRS Journal of Photogrammetry and Remote Sensing, 184, 116--130, 2022.
3. Li, K., Wan, G., Cheng, G., Meng, L., and Han, J. Object Detection in Optical Remote Sensing Images: A Survey and a New Benchmark. ISPRS Journal of Photogrammetry and Remote Sensing, 159, 296--307, 2020.
4. Cheng, G., Yuan, X., Yao, X., et al. Towards Large-Scale Small Object Detection: Survey and Benchmarks. IEEE Transactions on Pattern Analysis and Machine Intelligence, 2023.
5. Xie, X., Cheng, G., Wang, J., Yao, X., and Han, J. Oriented R-CNN for Object Detection. ICCV, 2021.
6. Lyu, C., Zhang, W., Huang, H., et al. RTMDet: An Empirical Study of Designing Real-Time Object Detectors. arXiv:2212.07784, 2022.
7. Yang, X. and Yan, J. Arbitrary-Oriented Object Detection with Circular Smooth Label. ECCV, 2020.
8. Yang, X., Hou, L., Zhou, Y., et al. Dense Label Encoding for Boundary Discontinuity Free Rotation Detection. CVPR, 2021.
9. Yu, Y. and Da, F. Phase-Shifting Coder: Predicting Accurate Orientation in Oriented Object Detection. CVPR, 2023.
10. Yang, X., Yan, J., Ming, Q., et al. Rethinking Rotated Object Detection with Gaussian Wasserstein Distance Loss. ICML, 2021.
11. Yang, X., Zhou, Y., Zhang, G., et al. Learning High-Precision Bounding Box for Rotated Object Detection via Kullback--Leibler Divergence. NeurIPS, 2021.
12. Zeng, Y., Chen, Y., Yang, X., Li, Q., and Yan, J. ARS-DETR: Aspect Ratio-Sensitive Detection Transformer for Aerial Oriented Object Detection. IEEE Transactions on Geoscience and Remote Sensing, 2024.
13. El-Yaniv, R. and Wiener, Y. On the Foundations of Noise-Free Selective Classification. Journal of Machine Learning Research, 11, 1605--1641, 2010.
14. Geifman, Y. and El-Yaniv, R. Selective Classification for Deep Neural Networks. NeurIPS, 2017.
15. Geifman, Y., Uziel, G., and El-Yaniv, R. SelectiveNet: A Deep Neural Network with an Integrated Reject Option. ICML, 2019.
16. Traub, J., Bungert, T. J., Lüth, C. T., et al. Overcoming Common Flaws in the Evaluation of Selective Classification Systems. NeurIPS, 2024.
17. Guo, C., Pleiss, G., Sun, Y., and Weinberger, K. Q. On Calibration of Modern Neural Networks. ICML, 2017.
18. Küppers, F., Kronenberger, J., Shantia, A., and Haselhoff, A. Multivariate Confidence Calibration for Object Detection. CVPR Workshops, 2020.
19. Pathiraja, B., Gunawardhana, M., and Khan, M. H. Multiclass Confidence and Localization Calibration for Object Detection. CVPR, 2023.
20. Oksuz, K., Joy, T., and Dokania, P. K. Towards Building Self-Aware Object Detectors via Reliable Uncertainty Quantification and Calibration. CVPR, 2023.
21. Vovk, V., Gammerman, A., and Shafer, G. Algorithmic Learning in a Random World. Springer, 2005.
22. Angelopoulos, A. N., Bates, S., Fisch, A., Lei, L., and Schuster, T. Conformal Risk Control. ICLR, 2024.
23. Angelopoulos, A. N., Bates, S., Jordan, M. I., and Malik, J. Learn Then Test: Calibrating Predictive Algorithms to Achieve Risk Control. arXiv:2110.01052, 2021.
24. Andéol, L., Fel, T., de Grancey, F., and Mossina, L. Conformal Object Detection. arXiv:2308.16005, 2023.

## Figure captions

**Figure 1 (`figures/ar_threshold_scan.svg`, PNG companion available).** Descriptive corrected TTA-localization AUGRC across aspect-ratio cutoffs for both DOTA units. Curves are drawn only from the archived r028 correction table and do not select a new threshold.

**Figure 2 (`figures/witness_effect_ci.svg`, PNG companion available).** Formal difference-of-differences and 95% bootstrap intervals for the seven DIOR-R witnesses and all six DOTA rows. Filled markers denote rows satisfying their complete frozen witness predicate.

**Figure 3 (`figures/geometric_tolerance.svg`, PNG companion available).** Frozen $\delta_{0.75}(a)$ curve: smallest long-axis rotation causing a concentric, congruent rectangle pair to cross below IoU 0.75.

**Figure 4 (`figures/bootstrap_distribution.svg`, PNG companion available).** Archived DOTA dataset-level AUGRC difference-of-differences bootstrap distribution with the frozen point estimate and interval; no refitting or new resampling is performed.
