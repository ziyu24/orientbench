# Supplement: Orientation Reliability Measurement-Validity Evidence

## S1. Formal decision rule

For each matched prediction, long-side canonicalization maps the OBB orientation to the angle of its longer edge. We calculate the periodic error modulo 180 degrees and normalize it using the frozen \(\delta_{0.75}(AR)\) tolerance rule. The resulting geometric risk is `clip(e_can / max(delta_0.75(AR), 1), 0, 3) / 3`.

The formal primary comparison is `linear_source_frozen - raw_confidence`, under `MAIN_AR_GE_2.1` and `NORMALIZED_ALL_AR`. Formal endpoints are AUGRC and Risk@70. A formal witness requires the predeclared directional CI conditions, nonzero DoD CI, centered-bootstrap p value surviving the applicable Holm family, epsilon/effect-band conditions, and for Risk@70 a tie-aware acceptance-set swap requirement. No r027 result is a formal witness.

## S2. Formal evidence tables

The seven r023 witness rows—point deltas, DoD, all CIs, raw p values, Holm p values, and swap fields—are persisted in [L1]. The r023 gate records the FAIR1M/SODA non-replication boundary [L2]. The six r026 hypotheses, including the two DOTA aggregate witnesses and the non-witness Oriented R-CNN rows, are in [L3]. All four AP parity values are in [L4].

`claim_recompute_r027.py` reads the immutable r023 bootstrap replicate parquet and r026 source tables independently. It recomputes the r023 witness CIs/p values and audits every r026 hypothesis field, swaps, all-AR matched counts (48,889/51,736), and four AP parity values. `claim_check.json` records 177 consistent field checks [L8].

## S3. Frozen probe definitions and source sensitivity

The DIOR-source probe is

`-0.23342829 + 0.00830977 logit_score + 0.02817757 log_pred_ar + 0.00753967 half_log_pred_area`.

The FAIR1M-source and SODA-A-source variants are retained only for DOTA sensitivity analysis. Their point estimates and 1,000 mother-cluster bootstrap CIs for AUGRC/Risk@70 in both domains are in [L12]. They are DESCRIPTIVE and do not alter r026's frozen DIOR-source formal claim.

## S4. Complete descriptive tables and figure data

All items in this section are marked `DESCRIPTIVE` and must not be read as new gates.

- `all_ar_scans_with_cluster_ci_descriptive.csv` supplies 21 AR cutoffs (1.0--3.0) × AUGRC/Risk@70/Risk@90 for DIOR A/B/C, DOTA two units, equal-unit DOTA, and pooled DOTA. The equal-unit CI directly resamples mother clusters jointly and averages detector metrics within each draw [L9].
- `dota_risk90_two_domain_cluster_ci_descriptive.csv` is the compact Risk@90 table for DOTA two units and two declared aggregates at `MAIN_AR_GE_2.1` and `ALL_AR` [L10].
- `dota_descriptive_class_decomposition.csv` contains the 15 DOTA classes in both domains; any class-domain row with fewer than 500 matched instances is flagged low reliability [L11].
- `all_units_descriptive_point_table.csv` has DIOR A/B/C, FAIR1M D, SODA-A E/F, DOTA Oriented R-CNN/RTMDet, four probes, three endpoints, both domains, and all row counts [L13].
- `dataset_uncertainty_mde80_descriptive.csv` reports dataset aggregation, cluster and main-eligible cluster counts, bootstrap SE, and normal-approximation MDE80. DOTA Risk@90 uses the explicitly labelled CI-derived SE because r026's frozen formal bootstrap did not include Risk@90 [L14].

## S5. Historical negative routes and audit chain

Learned EQS is a historical/appendix negative route, not support for the present formal result [L5]. The r014/r018/r019 trail is preserved as historical governance and reproducibility context [L6]. The current paper evidence map is `evidence_ledger.csv`: `[L#]` resolves to round, immutable path, SHA-256, formal/descriptive status, and generator. r023 and r026 provide the formal evidence; r027 only packages descriptive analyses and drafts for B/C review.

## S6. Scope and reproducibility limits

The migrated machine uses persisted DOTA tile-level GT conversion; the original 5,297 split annfiles are absent. No GPU, detector training, inference, data download, frozen-threshold modification, D_cal/D_audit alteration, or submission is part of r027. The scripts under `jprs_paper_package_r027_20260813/` regenerate the r027 package from existing frozen inputs.
