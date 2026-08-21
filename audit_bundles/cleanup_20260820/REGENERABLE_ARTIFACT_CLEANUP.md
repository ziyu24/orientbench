# Regenerable artifact cleanup — 2026-08-20

## Authorization and scope

Authorized by the project owner on 2026-08-20: reduce the current OrientBench
worktree from approximately 63 GiB to below 20 GiB by removing **regenerable**
training outputs.  The cleanup is limited to this repository.  Source code,
frozen governance records, plans, paper sources, and the minimum live r49
evidence/checkpoints are retained.

## Reproduction record

Every removed run was generated from versioned configuration and/or its
corresponding frozen dispatch in `dis/plans/`.  To reproduce a removed unit,
start from its dispatch commit, use the plan's recorded conda environment and
launch command, and write the result under `outputs/persistent_artifacts/`.
The deletion list below is intentionally path-level so that a future run can
distinguish removed runtime products from source-controlled specifications.

For r49 specifically, reproduce via
`dis/plans/B/b-r049-rev2-pef-multidata-multihost-20260819/sug.md` at dispatch
commit `8ff39d36c1edbe510c0111ae7f75cd6e6c2ca7d8` (or the current repaired
implementation commits recorded in the r49 reports).  The retained best
checkpoints support the remaining r49 comparison without retraining.

## Deletion classes

1. Superseded historical detector/selector run directories larger than 100 MiB
   under `outputs/persistent_artifacts/`.
2. r49 G1 smoke checkpoints and invalid/pre-geometry G2 branches: all are
   reproducible smoke or rejected implementations.  Their small logs, configs,
   and the final gradient proof remain.
3. Redundant r49 `epoch_11.pth` / `epoch_12.pth` resume checkpoints after a
   completed run: the best-mAP checkpoint and logs remain.  The failed scalar
   run is removed in full.

## Retained live r49 material

- `orientbench_r049_rev2_pef_obb_20260819/g1/**/full_model_gradient.json`
  and lightweight configs/logs;
- `.../g2_rotated_grid/dota_psc_cont/best_dota_mAP_epoch_12.pth`;
- `.../g2_rotated_grid/dota_psc_direct_dist_residual/best_dota_mAP_epoch_12.pth`;
- the corresponding configs, metric JSON, and logs.

The post-cleanup size, exact removed roots, and verification results are added
below after execution.

## Execution result

Completed 2026-08-20 18:45--18:48 PDT.

- Repository size: **63 GiB -> 15 GiB** (approximately 48 GiB reclaimed),
  which is below the requested 20 GiB ceiling.
- The filesystem gained approximately 48 GiB of free capacity.
- Removed superseded/reproducible artifact roots:
  `orientbench_p2c_lift_r048_20260819`, `m069_psc_phase1`,
  `orientbench_v2`, `orientbench_r011`,
  `orientbench_cora_obb_r049_20260819`, `orientbench_r010`,
  `m069_fullval_reliability`, `orientbench_saur_stagea_r043_20260818`,
  `orientbench_v2_047`, `m4_third_dataset_070`, `orientbench_r014`,
  `orientbench_semantic_heading_r047_20260818`, `orientbench_real_052`,
  `orientbench_panorama_r040_20260815`, `orientbench_r019`,
  `orientbench_qsetod_corrective_r037_20260815`,
  `orientbench_topjournal_feasibility_receipt3_20260811`,
  `orientbench_topjournal_feasibility_20260809`,
  `orientbench_measurement_validity_r020_20260811`,
  `orientbench_measurement_validity_r023_20260813`,
  `orientbench_circularity_decisive_r034_20260814`,
  `orientbench_qsetod_kill_study_r036_20260814`,
  `orientbench_oer_stagea_r042_20260817`, and `k1_table1_fullval_065`.
- Removed r49 invalid/pre-geometry G2 branches, G1 smoke `.pth` files,
  stopped scalar-quality files, and completed-run redundant resume checkpoints.
- Preserved `orientbench_panorama_r041_20260817` because an existing r041
  process was still writing there; it was not interrupted.  Also retained
  source, plans, audit bundles, archives, and the live r49 minimum evidence
  enumerated above.
