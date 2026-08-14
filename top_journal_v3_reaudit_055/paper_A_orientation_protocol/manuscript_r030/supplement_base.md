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

<!-- GENERATED_R023_FORMAL_TABLE -->

### S2.2 DOTA formal hypotheses

<!-- GENERATED_R026_FORMAL_TABLE -->

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

<!-- GENERATED_DESCRIPTIVE_TABLES -->

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
