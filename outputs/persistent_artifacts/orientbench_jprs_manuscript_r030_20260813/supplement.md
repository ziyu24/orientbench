# Supplementary Material: Aspect-Ratio Eligibility and Orientation Reliability

This supplement is part of the r030 evidence package. It contains formal definitions, complete formal rows, descriptive-table provenance, coefficient records, audit history, and replay instructions. Every descriptive result is labeled `DESCRIPTIVE`; no item in this supplement changes a frozen gate.

## S1. Complete formalization

### S1.1 Canonical angle

Given predicted and GT long-axis angles $\theta_p$ and $\theta_g$, the canonical error is $e_{can}=\min_{k\in\mathbb Z}|\theta_p-\theta_g+180k|$ on the first le90 lobe. Side swapping is performed before angle comparison. `NO_LONGSIDE_AR21` removes this equivalence while preserving the main AR domain.

### S1.2 Shape-normalized risk

For aspect ratio $a\ge1$, $\delta_{0.75}(a)$ is solved by deterministic polygon-IoU bisection for concentric, congruent rectangles. The frozen continuous risk is $r_{geo}=\operatorname{clip}(e_{can}/\max(\delta_{0.75}(a),1),0,3)/3$. `NO_GEONORM_AR21` replaces this geometry normalization inside the same $a\ge2.1$ domain. `NORMALIZED_ALL_AR`, `NORMALIZED_AR16`, and `NORMALIZED_AR13` retain normalization but alter eligibility.

### S1.3 Scores and endpoints

The formal score contrast is `linear_source_frozen - raw_confidence`. The linear feature order is intercept, logit confidence, log predicted aspect ratio, and half log predicted area. TTA angle consistency and corrected TTA localization are descriptive probes. Stable score ties are retained as blocks. AUGRC integrates cumulative generalized risk divided by the full sample size. Risk@70 and Risk@90 are conditional retained risks at 70% and 90% coverage.

### S1.4 Bootstrap and witness predicate

The core archive uses image/tile clusters; DOTA uses 458 mother scenes and 10,000 stored resamples. Let $\Delta_m$ and $\Delta_a$ be linear-minus-raw effects in the main and ablation domains and let $D=\Delta_m-\Delta_a$. A formal witness requires: lower CI($\Delta_m$) above $\epsilon_m$; upper CI($\Delta_a$) below $-\epsilon_a$; Holm-adjusted centered-bootstrap $p<0.05$; CI($D$) excludes zero; $|D|\ge\epsilon_m+\epsilon_a$; and, for fixed-coverage endpoints, both acceptance-set swap fractions meet the frozen threshold. Multiplicity is separated by unit-level and dataset-level families. The gate distinguishes `SUPPORTED`, `NOT_SUPPORTED`, `INCONCLUSIVE_MIXED`, and `INVALID`.

## S2. Formal result tables

The following tables are copied byte-for-value from the r027 paper package, whose formal rows trace to r023 and r026. They are repeated here in full rather than selectively reporting positive rows.

### S2.1 DIOR-R witnesses


<!-- SOURCE: outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/r023_formal_witnesses.csv -->
| level   | key    | contrast             | endpoint   | ablation_id       | effect_class   | hypothesis_key                                                |   main_probe |   main_raw |   ablation_probe |   ablation_raw |   delta_main |   delta_ablation |        dod |   epsilon_main |   epsilon_ablation |   delta_main_ci_low |   delta_main_ci_high |   delta_ablation_ci_low |   delta_ablation_ci_high |   dod_ci_low |   dod_ci_high |     p_raw |   main_swap70 |   main_swap90 |   ablation_swap70 |   ablation_swap90 |    p_holm | supported_direction                    | witness   | full_signature                                                                                  |
|:--------|:-------|:---------------------|:-----------|:------------------|:---------------|:--------------------------------------------------------------|-------------:|-----------:|-----------------:|---------------:|-------------:|-----------------:|-----------:|---------------:|-------------------:|--------------------:|---------------------:|------------------------:|-------------------------:|-------------:|--------------:|----------:|--------------:|--------------:|------------------:|------------------:|----------:|:---------------------------------------|:----------|:------------------------------------------------------------------------------------------------|
| unit    | A      | linear_source_frozen | AUGRC      | NORMALIZED_ALL_AR | AR_DOMAIN      | unit|A|linear_source_frozen|AUGRC|NORMALIZED_ALL_AR           |    0.0212371 |  0.0202697 |        0.0390195 |      0.0498342 |  0.00096742  |      -0.0108147  | 0.0117821  |    0.0005      |        0.000996684 |         0.000722988 |          0.00120068  |             -0.0119842  |              -0.00966616 |   0.0106174  |    0.0129585  | 9.999e-05 |      0.181385 |     0.0897897 |          0.233337 |         0.11915   | 0.0269973 | RAW_BETTER_MAIN__PROBE_BETTER_ABLATION | True      | AR_DOMAIN|NORMALIZED_ALL_AR|linear_source_frozen|AUGRC|RAW_BETTER_MAIN__PROBE_BETTER_ABLATION   |
| unit    | A      | linear_source_frozen | Risk@70    | NORMALIZED_ALL_AR | AR_DOMAIN      | unit|A|linear_source_frozen|Risk@70|NORMALIZED_ALL_AR         |    0.044205  |  0.0418027 |        0.0741812 |      0.100589  |  0.00240234  |      -0.0264082  | 0.0288105  |    0.001       |        0.00201179  |         0.00143551  |          0.00332764  |             -0.0310699  |              -0.022063   |   0.0243242  |    0.0335723  | 9.999e-05 |      0.181385 |     0.0897897 |          0.233337 |         0.11915   | 0.0269973 | RAW_BETTER_MAIN__PROBE_BETTER_ABLATION | True      | AR_DOMAIN|NORMALIZED_ALL_AR|linear_source_frozen|Risk@70|RAW_BETTER_MAIN__PROBE_BETTER_ABLATION |
| unit    | B      | linear_source_frozen | AUGRC      | NORMALIZED_ALL_AR | AR_DOMAIN      | unit|B|linear_source_frozen|AUGRC|NORMALIZED_ALL_AR           |    0.0233296 |  0.0226544 |        0.0409736 |      0.0491348 |  0.000675214 |      -0.00816117 | 0.00883638 |    0.0005      |        0.000982696 |         0.000511388 |          0.000840256 |             -0.00901352 |              -0.00732434 |   0.00800344 |    0.00967945 | 9.999e-05 |      0.144492 |     0.0587502 |          0.172396 |         0.0844038 | 0.0269973 | RAW_BETTER_MAIN__PROBE_BETTER_ABLATION | True      | AR_DOMAIN|NORMALIZED_ALL_AR|linear_source_frozen|AUGRC|RAW_BETTER_MAIN__PROBE_BETTER_ABLATION   |
| unit    | C      | linear_source_frozen | AUGRC      | NORMALIZED_ALL_AR | AR_DOMAIN      | unit|C|linear_source_frozen|AUGRC|NORMALIZED_ALL_AR           |    0.0269712 |  0.0241269 |        0.039752  |      0.0503971 |  0.0028443   |      -0.0106451  | 0.0134894  |    0.000539423 |        0.00100794  |         0.00252376  |          0.0031885   |             -0.0120039  |              -0.00934482 |   0.0121804  |    0.0148761  | 9.999e-05 |      0.176487 |     0.0629736 |          0.214902 |         0.0878575 | 0.0269973 | RAW_BETTER_MAIN__PROBE_BETTER_ABLATION | True      | AR_DOMAIN|NORMALIZED_ALL_AR|linear_source_frozen|AUGRC|RAW_BETTER_MAIN__PROBE_BETTER_ABLATION   |
| unit    | C      | linear_source_frozen | Risk@70    | NORMALIZED_ALL_AR | AR_DOMAIN      | unit|C|linear_source_frozen|Risk@70|NORMALIZED_ALL_AR         |    0.0524127 |  0.0480817 |        0.0765738 |      0.0981831 |  0.004331    |      -0.0216093  | 0.0259403  |    0.00104825  |        0.00196366  |         0.00355768  |          0.0051575   |             -0.0261835  |              -0.0179315  |   0.0222372  |    0.0305758  | 9.999e-05 |      0.176487 |     0.0629736 |          0.214902 |         0.0878575 | 0.0269973 | RAW_BETTER_MAIN__PROBE_BETTER_ABLATION | True      | AR_DOMAIN|NORMALIZED_ALL_AR|linear_source_frozen|Risk@70|RAW_BETTER_MAIN__PROBE_BETTER_ABLATION |
| dataset | DIOR-R | linear_source_frozen | AUGRC      | NORMALIZED_ALL_AR | AR_DOMAIN      | dataset|DIOR-R|linear_source_frozen|AUGRC|NORMALIZED_ALL_AR   |    0.023846  |  0.0223503 |        0.0399151 |      0.0497887 |  0.00149565  |      -0.00987364 | 0.0113693  |    0.0005      |        0.000995774 |         0.00130545  |          0.00168819  |             -0.0109112  |              -0.00886912 |   0.01035    |    0.0124213  | 9.999e-05 |      0.167455 |     0.0705045 |          0.206878 |         0.097137  | 0.0134987 | RAW_BETTER_MAIN__PROBE_BETTER_ABLATION | True      | AR_DOMAIN|NORMALIZED_ALL_AR|linear_source_frozen|AUGRC|RAW_BETTER_MAIN__PROBE_BETTER_ABLATION   |
| dataset | DIOR-R | linear_source_frozen | Risk@70    | NORMALIZED_ALL_AR | AR_DOMAIN      | dataset|DIOR-R|linear_source_frozen|Risk@70|NORMALIZED_ALL_AR |    0.0479627 |  0.0452565 |        0.0761337 |      0.0981937 |  0.00270618  |      -0.02206    | 0.0247662  |    0.001       |        0.00196387  |         0.00204227  |          0.00327561  |             -0.0258857  |              -0.0185917  |   0.0212147  |    0.0285792  | 9.999e-05 |      0.167455 |     0.0705045 |          0.206878 |         0.097137  | 0.0134987 | RAW_BETTER_MAIN__PROBE_BETTER_ABLATION | True      | AR_DOMAIN|NORMALIZED_ALL_AR|linear_source_frozen|Risk@70|RAW_BETTER_MAIN__PROBE_BETTER_ABLATION |
<!-- END_SOURCE -->


### S2.2 DOTA formal hypotheses


<!-- SOURCE: outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/r026_formal_hypotheses.csv -->
| level   | key       | endpoint   |   delta_main |   delta_ablation |       dod |   delta_main_ci_low |   delta_main_ci_high |   delta_ablation_ci_low |   delta_ablation_ci_high |   dod_ci_low |   dod_ci_high |     p_raw |   epsilon_main |   epsilon_ablation |   swap_main_70 |   swap_ablation_70 |     p_holm | witness   |
|:--------|:----------|:-----------|-------------:|-----------------:|----------:|--------------------:|---------------------:|------------------------:|-------------------------:|-------------:|--------------:|----------:|---------------:|-------------------:|---------------:|-------------------:|-----------:|:----------|
| unit    | orcnn     | AUGRC      |   0.00035402 |       -0.0123155 | 0.0126695 |        -1.0875e-05  |          0.000764967 |              -0.0183082 |              -0.00697423 |   0.00736106 |     0.0186728 | 9.999e-05 |    0.000533696 |        0.000974733 |       0.172831 |           0.184553 | 0.00039996 | False     |
| unit    | orcnn     | Risk@70    |   0.00110872 |       -0.0229638 | 0.0240725 |         9.61399e-05 |          0.00200987  |              -0.035895  |              -0.0118066  |   0.0130121  |     0.0367018 | 9.999e-05 |    0.00108035  |        0.00188524  |       0.172831 |           0.184553 | 0.00039996 | False     |
| unit    | rtmdet    | AUGRC      |   0.00236286 |       -0.0136099 | 0.0159727 |         0.00164457  |          0.00318977  |              -0.021116  |              -0.00694385 |   0.00921582 |     0.0236151 | 9.999e-05 |    0.000548816 |        0.000900842 |       0.28799  |           0.263105 | 0.00039996 | True      |
| unit    | rtmdet    | Risk@70    |   0.00433928 |       -0.0296037 | 0.0339429 |         0.00271212  |          0.005919    |              -0.0467954 |              -0.0150398  |   0.0191244  |     0.0513364 | 9.999e-05 |    0.00109107  |        0.00168564  |       0.28799  |           0.263105 | 0.00039996 | True      |
| dataset | DOTA-v1.0 | AUGRC      |   0.00135844 |       -0.0129627 | 0.0143211 |         0.000863355 |          0.00193486  |              -0.0196456 |              -0.00699779 |   0.00833677 |     0.0210285 | 9.999e-05 |    0.000541256 |        0.000937787 |       0.230411 |           0.223829 | 0.00019998 | True      |
| dataset | DOTA-v1.0 | Risk@70    |   0.002724   |       -0.0262837 | 0.0290077 |         0.00155401  |          0.0038486   |              -0.0408481 |              -0.0137766  |   0.0164741  |     0.0436297 | 9.999e-05 |    0.00108571  |        0.00178544  |       0.230411 |           0.223829 | 0.00019998 | True      |
<!-- END_SOURCE -->


## S3. Frozen source coefficients

<!-- SOURCE: top_journal_v3_reaudit_055/jprs_paper_package_r027_20260813/build_package.py -->
| Probe source | Intercept | Logit score | Log predicted AR | Half log predicted area | Status |
|---|---:|---:|---:|---:|---|
| FAIR1M source | -0.26525345 | 0.01355104 | 0.00337013 | 0.02027136 | archived, descriptive on DOTA |
| SODA source | -0.21289442 | 0.01466760 | -0.01161673 | 0.00892121 | archived, descriptive on DOTA |
<!-- END_SOURCE -->

The DOTA formal analysis uses the user-selected DIOR-source probe recorded before first DOTA outcome. The two vectors above are sensitivity probes only and are never used to change the formal result.

## S4. Descriptive tables

All corrected descriptive CSVs are rendered below in full. Tables inherited from r027 that depend on the old TTA-localization definition are excluded and replaced by the r028-corrected files. Sparse class rows carry their original `low_reliability` flag. No cutoff, coefficient, endpoint, or row is selected from these tables to alter a formal witness.


### S4.1 `dota_ap_parity.csv`

<!-- SOURCE: outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/dota_ap_parity.csv -->
| unit   |     ap50 |     ap75 |   expected_ap50 |   expected_ap75 | pass   |
|:-------|---------:|---------:|----------------:|----------------:|:-------|
| orcnn  | 0.706069 | 0.451742 |          0.7061 |          0.4517 | True   |
| rtmdet | 0.716127 | 0.486848 |          0.7161 |          0.4868 | True   |
<!-- END_SOURCE -->

### S4.2 `dota_unit_point_metrics.csv`

<!-- SOURCE: outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/dota_unit_point_metrics.csv -->
| unit   | cohort            | probe                |     AUGRC |   Risk@70 |   rows |
|:-------|:------------------|:---------------------|----------:|----------:|-------:|
| orcnn  | MAIN              | raw_confidence       | 0.0263308 | 0.0529086 |  33030 |
| orcnn  | MAIN              | linear_source_frozen | 0.0266848 | 0.0540173 |  33030 |
| orcnn  | NORMALIZED_ALL_AR | raw_confidence       | 0.0487367 | 0.0942621 |  48889 |
| orcnn  | NORMALIZED_ALL_AR | linear_source_frozen | 0.0364212 | 0.0712983 |  48889 |
| rtmdet | MAIN              | raw_confidence       | 0.0250779 | 0.0502143 |  34385 |
| rtmdet | MAIN              | linear_source_frozen | 0.0274408 | 0.0545536 |  34385 |
| rtmdet | NORMALIZED_ALL_AR | raw_confidence       | 0.0450421 | 0.0842819 |  51736 |
| rtmdet | NORMALIZED_ALL_AR | linear_source_frozen | 0.0314322 | 0.0546783 |  51736 |
<!-- END_SOURCE -->

### S4.3 `dota_risk90_two_domain_cluster_ci_descriptive.csv`

<!-- SOURCE: outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/dota_risk90_two_domain_cluster_ci_descriptive.csv -->
| dataset   | unit         |   cutoff | endpoint   |   rows |   delta_linear_minus_raw |       ci_low |      ci_high |   bootstrap_replicates | status      | cohort         |
|:----------|:-------------|---------:|:-----------|-------:|-------------------------:|-------------:|-------------:|-----------------------:|:------------|:---------------|
| DOTA-v1.0 | orcnn        |      1   | Risk@90    |  48889 |             -0.00718721  | -0.00970996  | -0.00430337  |                    200 | DESCRIPTIVE | ALL_AR         |
| DOTA-v1.0 | orcnn        |      2.1 | Risk@90    |  33030 |              0.00035685  | -4.97086e-05 |  0.000677502 |                    200 | DESCRIPTIVE | MAIN_AR_GE_2.1 |
| DOTA-v1.0 | rtmdet       |      1   | Risk@90    |  51736 |             -0.0163219   | -0.020985    | -0.0106089   |                    200 | DESCRIPTIVE | ALL_AR         |
| DOTA-v1.0 | rtmdet       |      2.1 | Risk@90    |  34385 |              0.00059003  |  0.000125966 |  0.00104439  |                    200 | DESCRIPTIVE | MAIN_AR_GE_2.1 |
| DOTA-v1.0 | equal_unit   |      1   | Risk@90    | 100625 |             -0.0117546   | -0.0151497   | -0.00727454  |                    200 | DESCRIPTIVE | ALL_AR         |
| DOTA-v1.0 | equal_unit   |      2.1 | Risk@90    |  67415 |              0.00047344  |  6.56977e-05 |  0.000769055 |                    200 | DESCRIPTIVE | MAIN_AR_GE_2.1 |
| DOTA-v1.0 | pooled_units |      1   | Risk@90    | 100625 |             -0.0125262   | -0.0169675   | -0.00770875  |                    200 | DESCRIPTIVE | ALL_AR         |
| DOTA-v1.0 | pooled_units |      2.1 | Risk@90    |  67415 |              0.000688689 |  0.000286047 |  0.00101349  |                    200 | DESCRIPTIVE | MAIN_AR_GE_2.1 |
<!-- END_SOURCE -->

### S4.4 `dota_source_beta_sensitivity_descriptive.csv`

<!-- SOURCE: outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/dota_source_beta_sensitivity_descriptive.csv -->
| source        | unit            | cohort   | endpoint   |   rows |     value | status      |      ci_low |     ci_high |   bootstrap_replicates |
|:--------------|:----------------|:---------|:-----------|-------:|----------:|:------------|------------:|------------:|-----------------------:|
| FAIR1M_source | orcnn           | MAIN     | AUGRC      |  33030 | 0.0263893 | DESCRIPTIVE | nan         | nan         |                    nan |
| FAIR1M_source | orcnn           | MAIN     | Risk@70    |  33030 | 0.0530861 | DESCRIPTIVE | nan         | nan         |                    nan |
| FAIR1M_source | orcnn           | ALL_AR   | AUGRC      |  48889 | 0.0477404 | DESCRIPTIVE | nan         | nan         |                    nan |
| FAIR1M_source | orcnn           | ALL_AR   | Risk@70    |  48889 | 0.0929926 | DESCRIPTIVE | nan         | nan         |                    nan |
| FAIR1M_source | rtmdet          | MAIN     | AUGRC      |  34385 | 0.0264952 | DESCRIPTIVE | nan         | nan         |                    nan |
| FAIR1M_source | rtmdet          | MAIN     | Risk@70    |  34385 | 0.0527816 | DESCRIPTIVE | nan         | nan         |                    nan |
| FAIR1M_source | rtmdet          | ALL_AR   | AUGRC      |  51736 | 0.0446954 | DESCRIPTIVE | nan         | nan         |                    nan |
| FAIR1M_source | rtmdet          | ALL_AR   | Risk@70    |  51736 | 0.0846912 | DESCRIPTIVE | nan         | nan         |                    nan |
| FAIR1M_source | DOTA_equal_unit | MAIN     | AUGRC      |  67415 | 0.0264423 | DESCRIPTIVE |   0.0250496 |   0.0276444 |                   1000 |
| FAIR1M_source | DOTA_equal_unit | MAIN     | Risk@70    |  67415 | 0.0529339 | DESCRIPTIVE |   0.0501126 |   0.0554416 |                   1000 |
| FAIR1M_source | DOTA_equal_unit | ALL_AR   | AUGRC      | 100625 | 0.0462179 | DESCRIPTIVE |   0.038328  |   0.0562194 |                   1000 |
| FAIR1M_source | DOTA_equal_unit | ALL_AR   | Risk@70    | 100625 | 0.0888419 | DESCRIPTIVE |   0.0739692 |   0.108405  |                   1000 |
| SODA_source   | orcnn           | MAIN     | AUGRC      |  33030 | 0.0262898 | DESCRIPTIVE | nan         | nan         |                    nan |
| SODA_source   | orcnn           | MAIN     | Risk@70    |  33030 | 0.0527356 | DESCRIPTIVE | nan         | nan         |                    nan |
| SODA_source   | orcnn           | ALL_AR   | AUGRC      |  48889 | 0.0519065 | DESCRIPTIVE | nan         | nan         |                    nan |
| SODA_source   | orcnn           | ALL_AR   | Risk@70    |  48889 | 0.0977607 | DESCRIPTIVE | nan         | nan         |                    nan |
| SODA_source   | rtmdet          | MAIN     | AUGRC      |  34385 | 0.0251997 | DESCRIPTIVE | nan         | nan         |                    nan |
| SODA_source   | rtmdet          | MAIN     | Risk@70    |  34385 | 0.0504741 | DESCRIPTIVE | nan         | nan         |                    nan |
| SODA_source   | rtmdet          | ALL_AR   | AUGRC      |  51736 | 0.0513479 | DESCRIPTIVE | nan         | nan         |                    nan |
| SODA_source   | rtmdet          | ALL_AR   | Risk@70    |  51736 | 0.0943323 | DESCRIPTIVE | nan         | nan         |                    nan |
| SODA_source   | DOTA_equal_unit | MAIN     | AUGRC      |  67415 | 0.0257448 | DESCRIPTIVE |   0.0242666 |   0.0269907 |                   1000 |
| SODA_source   | DOTA_equal_unit | MAIN     | Risk@70    |  67415 | 0.0516049 | DESCRIPTIVE |   0.0485197 |   0.0542898 |                   1000 |
| SODA_source   | DOTA_equal_unit | ALL_AR   | AUGRC      | 100625 | 0.0516272 | DESCRIPTIVE |   0.0411841 |   0.0646675 |                   1000 |
| SODA_source   | DOTA_equal_unit | ALL_AR   | Risk@70    | 100625 | 0.0960465 | DESCRIPTIVE |   0.0773307 |   0.120051  |                   1000 |
<!-- END_SOURCE -->

### S4.5 `dota_uncertainty_mde80_descriptive.csv`

<!-- SOURCE: outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/dota_uncertainty_mde80_descriptive.csv -->
| dataset   | unit   |   clusters | endpoint   |   bootstrap_se |   mde80_normal_approx | status      |
|:----------|:-------|-----------:|:-----------|---------------:|----------------------:|:------------|
| DOTA-v1.0 | orcnn  |        458 | AUGRC      |     0.00290437 |            0.00813225 | DESCRIPTIVE |
| DOTA-v1.0 | rtmdet |        458 | AUGRC      |     0.0036946  |            0.0103449  | DESCRIPTIVE |
| DOTA-v1.0 | orcnn  |        458 | Risk@70    |     0.00609443 |            0.0170644  | DESCRIPTIVE |
| DOTA-v1.0 | rtmdet |        458 | Risk@70    |     0.00830268 |            0.0232475  | DESCRIPTIVE |
<!-- END_SOURCE -->

### S4.6 `all_datasets_uncertainty_mde80_descriptive.csv`

<!-- SOURCE: outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/all_datasets_uncertainty_mde80_descriptive.csv -->
| dataset   | unit   |   clusters |   eligible_clusters_main | endpoint   |   bootstrap_se |   mde80_normal_approx | status      |
|:----------|:-------|-----------:|-------------------------:|:-----------|---------------:|----------------------:|:------------|
| DIOR-R    | A      |       5368 |                     3497 | AUGRC      |    0.000123004 |           0.00034441  | DESCRIPTIVE |
| DIOR-R    | A      |       5368 |                     3497 | Risk@70    |    0.0004826   |           0.00135128  | DESCRIPTIVE |
| DIOR-R    | A      |       5368 |                     3497 | Risk@90    |    0.000336239 |           0.000941469 | DESCRIPTIVE |
| DIOR-R    | B      |       5455 |                     3643 | AUGRC      |    8.47865e-05 |           0.000237402 | DESCRIPTIVE |
| DIOR-R    | B      |       5455 |                     3643 | Risk@70    |    0.000344675 |           0.000965091 | DESCRIPTIVE |
| DIOR-R    | B      |       5455 |                     3643 | Risk@90    |    0.000187233 |           0.000524254 | DESCRIPTIVE |
| DIOR-R    | C      |       5525 |                     3697 | AUGRC      |    0.000167847 |           0.000469972 | DESCRIPTIVE |
| DIOR-R    | C      |       5525 |                     3697 | Risk@70    |    0.000411174 |           0.00115129  | DESCRIPTIVE |
| DIOR-R    | C      |       5525 |                     3697 | Risk@90    |    0.000335997 |           0.000940791 | DESCRIPTIVE |
| FAIR1M    | D      |       1876 |                     1222 | AUGRC      |    0.000159655 |           0.000447035 | DESCRIPTIVE |
| FAIR1M    | D      |       1876 |                     1222 | Risk@70    |    0.000365673 |           0.00102388  | DESCRIPTIVE |
| FAIR1M    | D      |       1876 |                     1222 | Risk@90    |    0.000181764 |           0.000508939 | DESCRIPTIVE |
| SODA-A    | E      |        569 |                      415 | AUGRC      |    0.000134141 |           0.000375594 | DESCRIPTIVE |
| SODA-A    | E      |        569 |                      415 | Risk@70    |    0.000297257 |           0.000832319 | DESCRIPTIVE |
| SODA-A    | E      |        569 |                      415 | Risk@90    |    0.000218598 |           0.000612075 | DESCRIPTIVE |
| SODA-A    | F      |        569 |                      417 | AUGRC      |    4.80217e-05 |           0.000134461 | DESCRIPTIVE |
| SODA-A    | F      |        569 |                      417 | Risk@70    |    0.000115858 |           0.000324403 | DESCRIPTIVE |
| SODA-A    | F      |        569 |                      417 | Risk@90    |    0.000296963 |           0.000831498 | DESCRIPTIVE |
| DOTA-v1.0 | orcnn  |        458 |                      nan | AUGRC      |    0.00290437  |           0.00813225  | DESCRIPTIVE |
| DOTA-v1.0 | rtmdet |        458 |                      nan | AUGRC      |    0.0036946   |           0.0103449   | DESCRIPTIVE |
| DOTA-v1.0 | orcnn  |        458 |                      nan | Risk@70    |    0.00609443  |           0.0170644   | DESCRIPTIVE |
| DOTA-v1.0 | rtmdet |        458 |                      nan | Risk@70    |    0.00830268  |           0.0232475   | DESCRIPTIVE |
<!-- END_SOURCE -->

### S4.7 `dataset_uncertainty_mde80_descriptive.csv`

<!-- SOURCE: outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/dataset_uncertainty_mde80_descriptive.csv -->
| dataset   | unit_aggregation   |   clusters |   eligible_clusters_main | endpoint   |   bootstrap_se |   mde80_normal_approx |   bootstrap_replicates | status                 |
|:----------|:-------------------|-----------:|-------------------------:|:-----------|---------------:|----------------------:|-----------------------:|:-----------------------|
| DIOR-R    | equal_unit         |       5697 |                     3904 | AUGRC      |    9.8397e-05  |           0.000275512 |                  10000 | DESCRIPTIVE            |
| DIOR-R    | equal_unit         |       5697 |                     3904 | Risk@70    |    0.000316381 |           0.000885866 |                  10000 | DESCRIPTIVE            |
| DIOR-R    | equal_unit         |       5697 |                     3904 | Risk@90    |    0.000213288 |           0.000597207 |                  10000 | DESCRIPTIVE            |
| FAIR1M    | equal_unit         |       1876 |                     1222 | AUGRC      |    0.000159655 |           0.000447035 |                  10000 | DESCRIPTIVE            |
| FAIR1M    | equal_unit         |       1876 |                     1222 | Risk@70    |    0.000365673 |           0.00102388  |                  10000 | DESCRIPTIVE            |
| FAIR1M    | equal_unit         |       1876 |                     1222 | Risk@90    |    0.000181764 |           0.000508939 |                  10000 | DESCRIPTIVE            |
| SODA-A    | equal_unit         |        569 |                      419 | AUGRC      |    8.50133e-05 |           0.000238037 |                  10000 | DESCRIPTIVE            |
| SODA-A    | equal_unit         |        569 |                      419 | Risk@70    |    0.000193381 |           0.000541467 |                  10000 | DESCRIPTIVE            |
| SODA-A    | equal_unit         |        569 |                      419 | Risk@90    |    0.000251352 |           0.000703785 |                  10000 | DESCRIPTIVE            |
| DOTA-v1.0 | equal_unit         |        458 |                      458 | AUGRC      |    0.00029117  |           0.000815275 |                    200 | DESCRIPTIVE_CI_DERIVED |
| DOTA-v1.0 | equal_unit         |        458 |                      458 | Risk@70    |    0.000603241 |           0.00168908  |                    200 | DESCRIPTIVE_CI_DERIVED |
| DOTA-v1.0 | equal_unit         |        458 |                      458 | Risk@90    |    0.000179428 |           0.000502398 |                    200 | DESCRIPTIVE_CI_DERIVED |
<!-- END_SOURCE -->

### S4.8 `descriptive_scope_notes.csv`

<!-- SOURCE: outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/descriptive_scope_notes.csv -->
| unit   | bootstrap_columns   | note                                                       |
|:-------|:--------------------|:-----------------------------------------------------------|
| orcnn  | (10000, 16)         | DESCRIPTIVE: R@90 requires recomputation from matched rows |
| rtmdet | (10000, 16)         | DESCRIPTIVE: R@90 requires recomputation from matched rows |
<!-- END_SOURCE -->

### S4.9 `dota_tta_localization_corrected_unit_table.csv`

<!-- SOURCE: outputs/persistent_artifacts/orientbench_corrective_audit_r028_20260813/dota_tta_localization_corrected_unit_table.csv -->
| dataset   | unit   | cohort         | probe                      |   rows |     AUGRC |   Risk@70 |   Risk@90 | status                     |
|:----------|:-------|:---------------|:---------------------------|-------:|----------:|----------:|----------:|:---------------------------|
| DOTA-v1.0 | orcnn  | MAIN_AR_GE_2.1 | raw_confidence             |  33030 | 0.0263308 | 0.0529086 | 0.0550677 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  | MAIN_AR_GE_2.1 | linear_source_frozen       |  33030 | 0.0266848 | 0.0540173 | 0.0554246 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  | MAIN_AR_GE_2.1 | tta_localization_corrected |  33030 | 0.0251842 | 0.0508016 | 0.0538846 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  | ALL_AR         | raw_confidence             |  48889 | 0.0487367 | 0.0942621 | 0.0939727 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  | ALL_AR         | linear_source_frozen       |  48889 | 0.0364212 | 0.0712983 | 0.0867855 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  | ALL_AR         | tta_localization_corrected |  48889 | 0.0450772 | 0.0873387 | 0.0911454 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet | MAIN_AR_GE_2.1 | raw_confidence             |  34385 | 0.0250779 | 0.0502143 | 0.0539627 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet | MAIN_AR_GE_2.1 | linear_source_frozen       |  34385 | 0.0274408 | 0.0545536 | 0.0545528 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet | MAIN_AR_GE_2.1 | tta_localization_corrected |  34385 | 0.0246091 | 0.0492169 | 0.0529699 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet | ALL_AR         | raw_confidence             |  51736 | 0.0450421 | 0.0842819 | 0.092658  | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet | ALL_AR         | linear_source_frozen       |  51736 | 0.0314322 | 0.0546783 | 0.076336  | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet | ALL_AR         | tta_localization_corrected |  51736 | 0.04574   | 0.0864247 | 0.0907028 | DESCRIPTIVE_R028_CORRECTED |
<!-- END_SOURCE -->

### S4.10 `dota_tta_localization_corrected_ar_scan.csv`

<!-- SOURCE: outputs/persistent_artifacts/orientbench_corrective_audit_r028_20260813/dota_tta_localization_corrected_ar_scan.csv -->
| dataset   | unit   |   cutoff |   rows | probe                      |     AUGRC |   Risk@70 |   Risk@90 | status                     |
|:----------|:-------|---------:|-------:|:---------------------------|----------:|----------:|----------:|:---------------------------|
| DOTA-v1.0 | orcnn  |      1   |  48889 | tta_localization_corrected | 0.0450772 | 0.0873387 | 0.0911454 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      1.1 |  44859 | tta_localization_corrected | 0.0277553 | 0.0548249 | 0.0602111 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      1.2 |  43264 | tta_localization_corrected | 0.0249021 | 0.049736  | 0.0543144 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      1.3 |  42222 | tta_localization_corrected | 0.0245806 | 0.0492831 | 0.0532824 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      1.4 |  41095 | tta_localization_corrected | 0.024445  | 0.0492452 | 0.0529767 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      1.5 |  40199 | tta_localization_corrected | 0.0245544 | 0.0494984 | 0.0531422 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      1.6 |  39507 | tta_localization_corrected | 0.0245957 | 0.0496256 | 0.0531886 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      1.7 |  38874 | tta_localization_corrected | 0.0245605 | 0.0495889 | 0.0530447 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      1.8 |  38088 | tta_localization_corrected | 0.0245685 | 0.049634  | 0.0530114 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      1.9 |  36751 | tta_localization_corrected | 0.0246133 | 0.0497399 | 0.0530282 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      2   |  35305 | tta_localization_corrected | 0.0246394 | 0.0498065 | 0.0530473 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      2.1 |  33030 | tta_localization_corrected | 0.0251842 | 0.0508016 | 0.0538846 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      2.2 |  30585 | tta_localization_corrected | 0.025987  | 0.052141  | 0.0550501 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      2.3 |  28735 | tta_localization_corrected | 0.026102  | 0.0523681 | 0.0552655 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      2.4 |  27047 | tta_localization_corrected | 0.0261599 | 0.0525067 | 0.0553964 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      2.5 |  24986 | tta_localization_corrected | 0.0261211 | 0.0524153 | 0.055342  | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      2.6 |  22990 | tta_localization_corrected | 0.0261152 | 0.0524652 | 0.0553386 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      2.7 |  20912 | tta_localization_corrected | 0.0258596 | 0.0518547 | 0.0548338 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      2.8 |  18743 | tta_localization_corrected | 0.0256585 | 0.0514583 | 0.0545956 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      2.9 |  16718 | tta_localization_corrected | 0.0255128 | 0.0510586 | 0.0544172 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | orcnn  |      3   |  14765 | tta_localization_corrected | 0.0251322 | 0.0501943 | 0.0538034 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      1   |  51736 | tta_localization_corrected | 0.04574   | 0.0864247 | 0.0907028 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      1.1 |  47370 | tta_localization_corrected | 0.0274037 | 0.0535606 | 0.0593831 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      1.2 |  45528 | tta_localization_corrected | 0.0244533 | 0.0486727 | 0.053346  | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      1.3 |  44393 | tta_localization_corrected | 0.024196  | 0.0483794 | 0.0527443 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      1.4 |  43201 | tta_localization_corrected | 0.0240388 | 0.0481342 | 0.0522851 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      1.5 |  42273 | tta_localization_corrected | 0.024096  | 0.0482904 | 0.0522746 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      1.6 |  41544 | tta_localization_corrected | 0.0241296 | 0.0484132 | 0.0522349 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      1.7 |  40854 | tta_localization_corrected | 0.0241279 | 0.0484387 | 0.0522386 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      1.8 |  39967 | tta_localization_corrected | 0.0241326 | 0.0484564 | 0.0522492 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      1.9 |  38473 | tta_localization_corrected | 0.0241652 | 0.0484767 | 0.0523366 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      2   |  36876 | tta_localization_corrected | 0.0241496 | 0.048464  | 0.0523292 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      2.1 |  34385 | tta_localization_corrected | 0.0246091 | 0.0492169 | 0.0529699 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      2.2 |  31722 | tta_localization_corrected | 0.0254202 | 0.0505696 | 0.0541538 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      2.3 |  29687 | tta_localization_corrected | 0.0255342 | 0.0507706 | 0.0543474 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      2.4 |  27832 | tta_localization_corrected | 0.0255897 | 0.0508418 | 0.0545494 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      2.5 |  25666 | tta_localization_corrected | 0.0255574 | 0.0507604 | 0.0545477 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      2.6 |  23558 | tta_localization_corrected | 0.0255616 | 0.0507258 | 0.0546591 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      2.7 |  21406 | tta_localization_corrected | 0.025473  | 0.0505784 | 0.0547216 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      2.8 |  19176 | tta_localization_corrected | 0.0254322 | 0.0504797 | 0.054789  | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      2.9 |  17107 | tta_localization_corrected | 0.0254176 | 0.0505757 | 0.0548581 | DESCRIPTIVE_R028_CORRECTED |
| DOTA-v1.0 | rtmdet |      3   |  15128 | tta_localization_corrected | 0.0253799 | 0.0504233 | 0.0550727 | DESCRIPTIVE_R028_CORRECTED |
<!-- END_SOURCE -->

### S4.11 `dota_tta_localization_corrected_class_table.csv`

<!-- SOURCE: outputs/persistent_artifacts/orientbench_corrective_audit_r028_20260813/dota_tta_localization_corrected_class_table.csv -->
| unit   |   class_id | cohort         |   rows |   tta_localization_corrected_AUGRC | low_reliability   | status                     |
|:-------|-----------:|:---------------|-------:|-----------------------------------:|:------------------|:---------------------------|
| orcnn  |          0 | MAIN_AR_GE_2.1 |      4 |                         0.0107122  | True              | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          2 | MAIN_AR_GE_2.1 |    295 |                         0.0282941  | True              | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          3 | MAIN_AR_GE_2.1 |     53 |                         0.0206642  | True              | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          4 | MAIN_AR_GE_2.1 |   4740 |                         0.0233356  | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          5 | MAIN_AR_GE_2.1 |   7911 |                         0.0209296  | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          6 | MAIN_AR_GE_2.1 |  16995 |                         0.0288696  | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          7 | MAIN_AR_GE_2.1 |    755 |                         0.00656433 | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |         10 | MAIN_AR_GE_2.1 |     17 |                         0.0164328  | True              | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |         12 | MAIN_AR_GE_2.1 |   2140 |                         0.0309987  | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |         13 | MAIN_AR_GE_2.1 |     92 |                         0.038352   | True              | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |         14 | MAIN_AR_GE_2.1 |     28 |                         0.0334464  | True              | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          0 | ALL_AR         |   4125 |                         0.0544337  | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          1 | ALL_AR         |    310 |                         0.228484   | True              | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          2 | ALL_AR         |    545 |                         0.046908   | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          3 | ALL_AR         |    192 |                         0.0182724  | True              | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          4 | ALL_AR         |   8705 |                         0.0233885  | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          5 | ALL_AR         |   8084 |                         0.0210433  | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          6 | ALL_AR         |  17442 |                         0.0288481  | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          7 | ALL_AR         |   1423 |                         0.00685699 | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          8 | ALL_AR         |    229 |                         0.0156857  | True              | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |          9 | ALL_AR         |   3349 |                         0.223904   | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |         10 | ALL_AR         |    200 |                         0.0153957  | True              | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |         11 | ALL_AR         |    210 |                         0.222076   | True              | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |         12 | ALL_AR         |   3446 |                         0.0392104  | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |         13 | ALL_AR         |    540 |                         0.0576099  | False             | DESCRIPTIVE_R028_CORRECTED |
| orcnn  |         14 | ALL_AR         |     89 |                         0.120314   | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          0 | MAIN_AR_GE_2.1 |      2 |                         0.107948   | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          2 | MAIN_AR_GE_2.1 |    326 |                         0.0336513  | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          3 | MAIN_AR_GE_2.1 |     50 |                         0.0156903  | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          4 | MAIN_AR_GE_2.1 |   5289 |                         0.023339   | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          5 | MAIN_AR_GE_2.1 |   8123 |                         0.0220214  | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          6 | MAIN_AR_GE_2.1 |  17465 |                         0.0266765  | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          7 | MAIN_AR_GE_2.1 |    767 |                         0.00610866 | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          8 | MAIN_AR_GE_2.1 |      1 |                         0.02554    | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |         10 | MAIN_AR_GE_2.1 |     10 |                         0.0191636  | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |         12 | MAIN_AR_GE_2.1 |   2231 |                         0.0365475  | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |         13 | MAIN_AR_GE_2.1 |     93 |                         0.0366234  | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |         14 | MAIN_AR_GE_2.1 |     28 |                         0.0265986  | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          0 | ALL_AR         |   4180 |                         0.0489513  | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          1 | ALL_AR         |    316 |                         0.215245   | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          2 | ALL_AR         |    574 |                         0.0505502  | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          3 | ALL_AR         |    188 |                         0.0175346  | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          4 | ALL_AR         |   9897 |                         0.023418   | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          5 | ALL_AR         |   8353 |                         0.022136   | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          6 | ALL_AR         |  17970 |                         0.0266888  | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          7 | ALL_AR         |   1422 |                         0.00649506 | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          8 | ALL_AR         |    218 |                         0.0132684  | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |          9 | ALL_AR         |   3974 |                         0.233652   | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |         10 | ALL_AR         |    184 |                         0.0192329  | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |         11 | ALL_AR         |    204 |                         0.170372   | True              | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |         12 | ALL_AR         |   3600 |                         0.0438994  | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |         13 | ALL_AR         |    546 |                         0.0537083  | False             | DESCRIPTIVE_R028_CORRECTED |
| rtmdet |         14 | ALL_AR         |    110 |                         0.104543   | True              | DESCRIPTIVE_R028_CORRECTED |
<!-- END_SOURCE -->

### S4.12 `r027_supersession_manifest.csv`

<!-- SOURCE: outputs/persistent_artifacts/orientbench_corrective_audit_r028_20260813/r027_supersession_manifest.csv -->
| r027_artifact                                | status             | reason                                                                                                       |
|:---------------------------------------------|:-------------------|:-------------------------------------------------------------------------------------------------------------|
| all_units_descriptive_point_table.csv        | SUPERSEDED_BY_R028 | r027 tta_localization was not -(missing_fraction + iou_loss); only rows using that probe require replacement |
| dota_descriptive_ar_scan_and_endpoints.csv   | SUPERSEDED_BY_R028 | r027 tta_localization was not -(missing_fraction + iou_loss); only rows using that probe require replacement |
| dota_descriptive_class_decomposition.csv     | SUPERSEDED_BY_R028 | r027 tta_localization was not -(missing_fraction + iou_loss); only rows using that probe require replacement |
| core_descriptive_ar_scan.csv                 | SUPERSEDED_BY_R028 | r027 tta_localization was not -(missing_fraction + iou_loss); only rows using that probe require replacement |
| all_ar_scans_with_cluster_ci_descriptive.csv | SUPERSEDED_BY_R028 | r027 tta_localization was not -(missing_fraction + iou_loss); only rows using that probe require replacement |
<!-- END_SOURCE -->


## S5. EQS negative and exploratory archive

The selector route is not part of the main contribution. The immutable history is:

- r011 source-supervised geometry transfer: leave-dataset support 0/6 and identifiable leave-detector support 4/5, insufficient for the frozen cross-domain gate (`dis/server_reports/orientbench-c-r011-20260807.md`).
- r012: `FAIL_PROVENANCE_R012`; EQS and HRSC were not evaluated (`dis/server_reports/orientbench-c-r012-20260807.md`).
- r014 was later fixed numerically but failed the prospective protocol seal; the final formal status is `FAIL_PROTOCOL_R014` (`dis/server_reports/orientbench-c-r015-20260808.md`).
- r015 retained six positive Core unit intervals only as `EXPLORATORY_CORE_SUPPORT_R015`; HRSC remained `INCONCLUSIVE_INDEPENDENT_HRSC_R014` with interval crossing zero (`dis/server_reports/orientbench-c-r015-20260808.md`).
- r019 DOTA EQS risk--coverage ended `FAIL_EXTERNAL_DOTA_EQS_RC_R019` (`dis/server_reports/orientbench-c-r019-20260809.md`).

Accordingly, EQS is a failed-transfer/exploratory appendix record, not an externally validated or deployable selector.

## S6. Audit chain

| Round | Purpose | Report or review | Key commit/status |
|---|---|---|---|
| r023 | formal DIOR measurement validity | `dis/server_reports/orientbench-b-r023-measurement-validity-20260813/SERVER_EXECUTION_REPORT.md` | `INCONCLUSIVE_MIXED` |
| r024 | DOTA probe provenance | `dis/server_reports/orientbench-b-r024-dota-external-replication-20260813/SERVER_EXECUTION_REPORT.md` | stopped before DOTA input |
| r025 | first DOTA outcome | `dis/server_reports/orientbench-user-r025-dior-source-dota-replication-20260813/SERVER_EXECUTION_REPORT.md` | `5ce52c23` |
| r026 | initial DOTA closure | `dis/server_reports/orientbench-b-r026-dota-external-confirmation-20260813/SERVER_EXECUTION_REPORT.md` | `747c0dba` |
| r028 | corrective raw audit and bundle | `dis/server_reports/orientbench-b-r028-corrective-audit-20260813/SERVER_EXECUTION_REPORT.md` | `e675a841` |
| r029 | ignored-object Git closure | `dis/server_reports/orientbench-b-r029-bundle-closure-20260813/SERVER_EXECUTION_REPORT.md` | `fe9d0ea5` |
| C/r029 | independent final replay | `dis/reviews/C/orientbench-r029-final-replay-review-20260813.md` | `AUDITED_EXTERNAL_REPLICATION_ACCEPTED` |

## S7. Bundle replay guide

From a clean clone at or after r029 closure, create a temporary output directory and run:

```bash
python audit_bundles/r028/code/revalidate_r026_raw.py \
  --raw audit_bundles/r028/dota \
  --tile-map audit_bundles/r028/dota/tile_to_mother.csv \
  --delta-source audit_bundles/r028/dota/m4_delta_theta_075_frozen.json \
  --compare audit_bundles/r028/dota/r026_hypotheses.csv \
  --output /tmp/orientbench_r026_replay

python audit_bundles/r028/code/revalidate_r023_raw.py \
  --rows audit_bundles/r028/dior/rows.parquet \
  --replicates audit_bundles/r028/dior/hypothesis_replicates.parquet \
  --frozen audit_bundles/r028/dior/r023_hypotheses.csv \
  --output /tmp/orientbench_r023_replay
```

Expected audit receipts are 96/96 consistent r026 checks and 4,950/4,950 consistent r023 checks. The bundle manifest contains 20 non-self-referential objects. Recompute SHA-256 and bytes from Git canonical blobs before consuming any result. Mutation replay should invoke the production validator in a subprocess; pristine inputs must exit zero and each of the six semantic mutations must exit nonzero.

## S8. Supplement figure and table provenance

Figure scripts, dual-format outputs, and SHA-256 records are under `figures/` and `figure_manifest.csv`. Rendered tables below trace to the exact CSV path printed in each heading. The numeric claim checker maps every number token in the main text and this supplement to a frozen artifact, a definition/structure source, or a bibliographic evidence record.
