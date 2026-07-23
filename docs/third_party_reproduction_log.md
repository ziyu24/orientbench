# Command 069 one-click reproduction

This is the authoritative collaborator-facing reproduction entry for 069-CONTINUATION.
It rebuilds CPU-only statistical tables from persistent, SHA-bound detector artifacts. It
does not train, run detector inference, rerun K2, change thresholds, or change D_cal/D_audit.

## Exact entry point

```bash
bash scripts/reproduce_all_main_tables.sh
```

There is no `--fast` formal mode. `--preflight-only` validates frozen assets and persisted
inputs but is not completion evidence.

## Covered outputs

1. M1 ar>=2.1 main results and ar1.6/ar1.3 sensitivity.
2. M2 fixed-size-bin G2_double_prime decision and intervals.
3. M3 complete-image bounded-loss HB LTT.
4. Secondary binary image event and instance-vs-image comparison.
5. Geometry-normalized severe event using frozen delta_theta_0.75.
6. Fixed 5/10/15 degree sensitivity.
7. Human disagreement analysis when two real label files exist; otherwise HUMAN_BLOCKED.
8. PSC Phase 1 radial intervention, preregistered analyses, and terminal split gate.
9. Two persisted DOTA clean full-val cells with DOTA#20 excluded.
10. DIOR full-val lineage and supersession of 052 partial/wrong-split values.
11. Frozen thresholds, D_cal/D_audit, host locks, and formal/exploratory scope checks.
12. Final reproduction status, artifact inventory, root report aliases, and submission gate.

## Authoritative lineage

Formal tables live in `top_journal_v3_reaudit_055/reports/`. Matching paths under
`reports/` are relative symlinks to that single historical-069 namespace, not copies.
Inputs are the persistent M069 A-F full-val matched/universe manifests, frozen K2 index,
PSC per-instance Phase 1 artifacts, targeted DCL/CSL native endpoints, and the two clean
DOTA full-val dumps. No formal table depends on `/dev/shm`.

The frozen M4 artifacts are SHA-256 `80d86a5f72e70405fe4a49db87aad61e6aea20a26af0ad1c5745bfd646d1e5cb` (definition),
`25ed7c7bb86b23cdefc7a0090ac64c41bf84f1e08476a6bbee96badc83a9ff65` (curve), and `b2e2bb7b46671d0496ad059aee8a13d23041075084a3924551bc1ce58d6597f5` (direct-solve audit).
PSC Phase 1 retains start `2026-07-12 20:14:39 -0700` and deadline `2026-08-23 20:14:39 -0700`.

## Decisions from this run

- M1: `PASS`.
- M2: `PASS`; on FAIL, geometry score is appendix-only.
- M3: `PASS`; image is the formal exchangeable unit.
- PSC Phase 1 split gate: `PASS`.
- Human annotation: HUMAN_BLOCKED: two real mutually blind annotation files have not been supplied.
- Submission freeze: `NOT_FROZEN`.

Detailed checks are in `reports/069_final_reproduction_status.csv`; the freeze decision is
in `reports/069_submission_freeze_gate.csv`; hashes and recomputation lineage are in
`reports/069_artifact_manifest.csv`.

<!-- CODEX_070_REPRO_START -->
## Command 070 machine reproduction

- Entry point: `bash scripts/reproduce_all_main_tables.sh --070-machine-only`
- M4 FAIR1M: 9/9 pilots and 9/9 final runs verified; decision `REPLICATES_A`.
- Recomputed from persistent final evaluations: seed results, variance, image-cluster bootstrap, strata decision, and artifact hashes.
- Annotation A/B packages: 1500 tasks each; blind-schema, browser save/restore/export, merge, and disagreement smoke checks pass.
- Real human annotations: 0; state `HUMAN_BLOCKED`. Test labels remain isolated under `/dev/shm` and are not formal results.
- Final gate: `NOT_FROZEN` solely because two real mutually blind annotation submissions are absent.
<!-- CODEX_070_REPRO_END -->





<!-- COMMAND_073_START -->
## Command 073 final reproduction

The default entry point `bash scripts/reproduce_all_main_tables.sh` rebuilds all CPU statistical tables, reconstructs the 600-target human endpoint from persistent A/B raw exports, keeps the 29-target blind recheck secondary, validates frozen machine artifacts, and runs the final freeze verifier. The authoritative log is `logs/reproduce_all_main_tables_073.log`; status and gate outputs are `reports/073_final_reproduction_status.csv` and `reports/073_submission_freeze_gate.csv`. No main table depends on `/dev/shm`.

This final state supersedes the historical 069/070 `HUMAN_BLOCKED` entries above: the real independent annotation endpoint is now complete and the final state is `FROZEN_FOR_COLLABORATOR_REVIEW`.
<!-- COMMAND_073_END -->

