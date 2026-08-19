---
schema_version: 2
dispatch_id: orientbench-b-r044-jprs-measurement-manuscript-20260818
plan_id: b-r044-jprs-measurement-manuscript-20260818
initiator: B
plan_path: dis/plans/B/b-r044-jprs-measurement-manuscript-20260818/sug.md
plan_commit_sha: 6679fb2315ace3110a086cf38c72135193c228be
plan_blob_oid: 2e55f656ba843309fc0ba0954ccb4bf69da2f157
plan_sha256: 3b2b6a03f40920afa457ec3e8aecc3e77eaabc7795dabfd128588ff78cf72495
dispatch_commit_sha: 3fb932bb6d717e161b9a9bcc1c76849ea33f5a0e
server_report_path: dis/server_reports/orientbench-b-r044-jprs-measurement-manuscript-20260818/SERVER_EXECUTION_REPORT.md
execution_status: complete
completion_mode: COMPLETE_NOT_JPRS_READY
starting_commit: b8c054f4230a87eb2989e67f97d24102b75ad158
ending_commit: recorded_by_the_result_commit_containing_this_report
---

# Server execution report — business instruction 044

## Summary

T1--T5 completed as a zero-GPU, derived-evidence-only manuscript execution. The package contains an 8,150-word English measurement-diagnostic manuscript, supplement and submission attachments, nine machine-readable tables, six editable SVG figures with six PNG companions, 24 bibliography records with a citation audit, an exact claim checker, three real semantic mutations, a non-self-referential manifest, and two perspective-separated red-team reviews.

The terminal scientific gate is **`NOT_JPRS_READY`**. G1--G3 pass; G4 fails because both red teams score novelty 3/5 while the frozen rule requires all five venue dimensions to be at least 4. This is a gated scientific outcome and maps to execution status `complete`; it is not a server claim that the paper is accepted, submitted, or publication-ready.

## Dispatch, hashes, authorization, and resources

- `git config --local paper.worker-id` returned `server-primary`, which maps to active role `SERVER`.
- The supplied dispatch commit `3fb932bb6d717e161b9a9bcc1c76849ea33f5a0e` exists and is an ancestor of the starting HEAD.
- Coordination names the same dispatch and plan. The frozen plan and root `dis/sug.md` are byte-identical, with blob `2e55f656ba843309fc0ba0954ccb4bf69da2f157` and SHA-256 `3b2b6a03f40920afa457ec3e8aecc3e77eaabc7795dabfd128588ff78cf72495`.
- L2 authorization is present in both coordination and the frozen plan.
- Resource scope was honored: GPU count/hours `0/0`; no detector training, forward pass, inference, checkpoint access, or raw dataset access; CPU work consisted of tracked-table parsing, plotting, hashing, and validation.
- Network use was limited to the declared GitHub HTTPS remote and Crossref metadata queries. No clean or held-out scientific endpoint was contacted.
- Writes are confined to the five declared roots. No B/C-owned plan, memo, review, contest, governance, split, threshold, or frozen evidence file was modified.
- `STARTED.json` was committed separately as `4f39575cb048ebe3a2a7a1839232917ba7f9f357` and pushed via HTTPS before research evidence was opened.

## Actual execution

| Task | Status | Actual commands/configuration | Primary artifacts | Result |
|---|---|---|---|---|
| Governance preflight and STARTED | complete | `git config`, `git cat-file`, ancestry check, `git hash-object`, `sha256sum`, `cmp`, explicit `git add/commit`, HTTPS push | `STARTED.json` | Identity, mirror, L2, 0-GPU, and write-set checks passed |
| T1 evidence map and conflict cleaning | complete | exact `rg`/CSV/JSON inspection of tracked evidence; no raw data | `evidence_map.csv`, `claim_ledger.csv`, `stale_claims_removed.md` | Final human 073 source supersedes stale `HUMAN_BLOCKED` tables; negative methods excluded |
| T2 complete manuscript | complete | evidence-bound authoring from canonical tables | `orientation_reliability_jprs.md`, `references.bib`, `reference_audit.csv` | 8,150 words; all required sections and explicit owner placeholders present |
| T3 supplement, tables, figures, attachments | complete | `conda run -n ai4rs python .../build_package.py` | `supplement.md`, nine CSV tables, six SVG+PNG pairs, highlights, cover letter, checklist | deterministic build completed; no synthetic remote-sensing example or untracked image used |
| T4 exact checker and mutations | complete | `python audit_bundles/r044/validate_claims.py`; `python audit_bundles/r044/run_mutations.py` | `claim_spec.csv`, `claim_check.json`, `mutation_results.json`, mutation fixtures | pristine 57/57 PASS; AP75 mutation, human-mean mutation, and deleted-row mutation all exit nonzero; citation coverage 24/24 |
| T5 frozen red teams and venue gate | complete | read-only review of manuscript SHA `e23077a...5317` | two reviewer reports, `venue_readiness.md`, `gate.json` | both weak reject; novelty 3/5; terminal `NOT_JPRS_READY` |
| Manifest and integrity | complete | `python audit_bundles/r044/build_manifest.py`; governance/write-set checks | `manifest.csv` | paths, sizes, SHA-256, and recomputation flags recorded; manifest intentionally excludes itself |

## Scientific evidence closure

The principal measurement result uses the six-row complete-evaluator source. AP50 is unchanged in every unit; AP75 decreases by 0.1731--0.6166 and mean long-axis error increases by 29.186--31.886 degrees. The deterministic rectangle tolerance gives `delta_0.75(2.1)=15.3297` degrees. The principal severe-event rates span 0.0019--0.0167 across eight geometry rows. At alpha 0.03, selected primary detection-score image-level calibration upper bounds span 0.003008--0.025875 across six units.

The human source is the final 073 summary rather than the older blocked table: 600 completed targets yield 450 numeric pairs, mean disagreement 2.3112 degrees with image-cluster 95% interval 1.9970--2.7854, `P(>5 degrees)=0.0800`, and `P(>10 degrees)=0.008889`. Human disagreement is explicitly not dataset GT error.

The manuscript does not claim that NRC is independent of mAP, that a PSC angle head is universally anti-calibrated, that DOTA public-test state of the art was reached, or that the project is complete. DOTA is local train/validation only. The geometry selector, Q-SetOD, OER/OER-D, and evaluated SAUR configuration appear only as negative boundaries. The SAUR formula deviation is stated as limiting rejection to the evaluated configuration rather than proving class-wide impossibility.

## Gates, deviations, failures, and negative results

| Gate | Status | Evidence |
|---|---|---|
| G1 evidence closure | PASS | exact path/key checker 57/57; no nearest-value match; six figure inputs SHA-bound; citations 24/24 |
| G2 scientific honesty | PASS | failed repair routes not packaged as positive methods; prohibited claims absent |
| G3 manuscript completeness | PASS | 8,150-word full English manuscript, supplement, references, captions, tables, figures, and attachments |
| G4 independent venue red team | FAIL | both reviewers assign novelty 3/5; other four dimensions are 4/5 |

No protocol drift, kill condition, or evidence-conflict early stop occurred. One build-script path-resolution defect occurred before final generation; it wrote only in-scope derived table/figure files, was corrected in the tracked script, and the deterministic build then completed. It did not affect scientific inputs or results.

The minimum remaining scientific gap is not language polishing. It is a prospective held-out remote-sensing decision study showing that the protocol changes a consequential model or threshold choice and preserves image-level risk control under geography, sensor, or acquisition shift, using an orientation-sensitive endpoint not defined solely by the same rectangle-IoU curve.

## Provenance and completion mapping

- Starting worktree: clean `main` at `b8c054f4230a87eb2989e67f97d24102b75ad158`.
- STARTED commit: `4f39575cb048ebe3a2a7a1839232917ba7f9f357`, pushed to the HTTPS origin before evidence access.
- Result worktree: only declared write-set paths changed.
- Python for plotting: conda environment `ai4rs`; validator uses the active standard-library Python. No random resampling was performed in this execution; figures reuse persisted point estimates and intervals.
- Seeds/checkpoints: not applicable; no training, inference, matching, or bootstrap recomputation.
- Final manifest: `audit_bundles/r044/manifest.csv`.
- Completion mapping: gated early stop / `NOT_JPRS_READY` maps to `execution_status: complete` and receipt first line `执行完毕`.
