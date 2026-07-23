# Codex Execution Audit Map — Round 055 Re-audit

Generated: 2026-07-02 (055 Task 0, read-only forensic reconstruction)

Primary source: `top_journal_v3/codex_and_supervisor.md`
Supporting sources: `top_journal_v3/docs/`, `top_journal_v3/reports/`, `outputs/persistent_artifacts/`

Critical context applied throughout: **055 A0 forensic finding** — the 053/054 headline NRC values
(score-only DIOR#22=1.1265, FAIR1M#24=1.5061, SODA#23=1.6733) were computed UNMASKED
(full matched tables with no aspect_ratio filter). Under the frozen masked protocol
(aspect_ratio >= 1.6), score-only NRC = 0.542 / 0.885 / 0.914 — calibrated, not
reverse-calibrated. Therefore "score-only reverse-calibration" is a near-square pooling
artifact = Codex protocol-drift execution error. The intrinsic phase_mod reverse-calibration
(Track A) survives masking and is retained. DOTA#20 is a 19-image D_cal-subset dump
(mAP 0.0132) = invalid_pending.

---

## Round 049

**Timestamp:** 2026-07-02 ~18:47 CST
**Instruction:** SUPERVISOR_049 — generate initial top-journal evidence package for P1-P5.

### 1. 目的 (Purpose)

Produce the first formal top-journal evidence decision for whether P1–P5 jointly support a
broader top-tier claim. Codex ran a combined evidence pipeline covering P1 constructive
decoupling, P2 within-cell conformal risk control, P3 PSC mechanism tests, P4 uncertainty
baselines, and P5 downstream angle task.

### 2. 核心输出 (Key Output Files)

- `top_journal_v3/docs/top_journal_evidence_decision_049.md`
- `top_journal_v3/reports/artifact_manifest_049.csv`
- `top_journal_v3/reports/heartbeat_049.json`
- `top_journal_v3/reports/verification_top_journal_evidence_v2_049.json`
- `top_journal_v3/reports/verification_top_journal_evidence_v2_049.md`
- `top_journal_v3/reports/p1_within_dataset_pair_mining.csv`

### 3. 使用的 Artifact

Mixed: some proxy/synthetic raw predictions for P1/P5; partial real matched features for P2;
DOTA #20 phase_mod absent (Track A blocked). 049 heartbeat records `gpu_used: false`.

### 4. Real / Proxy / Synthetic

Mixed — P1 and P5 relied on proxy/synthetic raw predictions not from final detector outputs.
P2 used partial real D_cal/D_audit rows. P3 had no DOTA #20 phase_mod; blocked.

### 5. 是否改过 mask / split / metric

No changes to `thresholds.yaml`, D_cal/D_audit, or frozen split files documented.
However: NRC was computed UNMASKED (no aspect_ratio filter applied). This is the
protocol-drift execution error first identified in 055 A0.

### 6. 结论是否仍有效 (Still Valid?)

- Overall verdict `broader top-tier claim = insufficient`: RETAINED (directionally correct).
- P1 partial (proxy artifacts): SUPERSEDED — proxy inputs invalidate formal evidence status.
- P2 partial: RETAINED as directional; but conformal numbers were on incomplete real rows.
- P3 blocked (no phase_mod): RETAINED.
- P4/P5 partial on proxy: SUPERSEDED for formal evidence.
- Any NRC numbers cited from 049: SUPERSEDED by A0 (unmasked).

### 7. 保留/Supersede/重算建议

Retain 049 only as the initial verdict record. Do not use 049 NRC, P1, or P5 numbers
in the paper. 052 real artifacts supersede all 049 computations.

---

## Round 050

**Timestamp:** 2026-07-02 ~20:14 CST
**Instruction:** SUPERVISOR_050 — real artifact inventory and non-synthetic recovery.

### 1. 目的

Audit which cells have verified non-proxy real detector outputs and recover whatever
is available without retraining or GPU inference. Produce real artifact inventory and
identify gaps.

### 2. 核心输出

- `top_journal_v3/docs/real_artifact_inventory_050.md`
- `top_journal_v3/docs/uncertainty_real_artifacts_050.md`
- `top_journal_v3/docs/psc_track_a_dump_050.md`
- `top_journal_v3/reports/real_artifact_inventory_050.csv`
- `top_journal_v3/reports/real_matched_table_050.csv`
- `top_journal_v3/reports/real_artifact_regeneration_050.csv`
- `top_journal_v3/reports/psc_track_a_dump_050.csv`
- `top_journal_v3/reports/uncertainty_real_artifacts_050.csv`
- `top_journal_v3/reports/verification_real_artifact_completion_050.json`
- `top_journal_v3/reports/heartbeat_050.json`
- `outputs/persistent_artifacts/orientbench_real_050/` (partial recovery)

### 3. 使用的 Artifact

Real persistent artifacts for DOTA#20, DIOR#22, FAIR1M#24, SODA#23 raw/schema/features.
DIOT #61/#10, FAIR1M#5/#12, SODA#4/#11, HRSC#13 schema only in scratch or non-persistent.
DOTA#20 Track A phase_mod: missing.

### 4. Real / Proxy / Synthetic

Primarily real — 5 cells confirmed real persistent raw/schema, 3 cells real PSC Track A
(DIOR#22/FAIR1M#24/SODA#23 only). 7 other cells remain scratch or non-persistent.

### 5. 是否改过 mask / split / metric

No changes to thresholds, D_cal/D_audit, or split files.
NRC in any 050 computation: unmasked (same protocol drift as 049).

### 6. 结论是否仍有效

- Inventory table (`real_artifact_inventory_050.csv`): RETAINED as historical gap record.
- Identified gaps (DOTA#20 phase_mod missing; scratch-only cells): RETAINED and accurate.
- Any NRC values in 050: SUPERSEDED by A0.
- Decision `remote_sensing_journal_ready = possible_after_full_real_P1_P2_and_TTA_completion`: 
  RETAINED directionally; 052 then addressed the gap.

### 7. 保留/Supersede/重算建议

Retain as gap/inventory record only. 052 artifacts supersede 050 computations for evidence.

---

## Round 051

**Timestamp:** 2026-07-02 ~21:03 CST
**Instruction:** SUPERVISOR_051_CODEX_HANDOFF_AND_REAL_EVIDENCE_RECOVERY — new Codex
instance handoff; do not restart, continue from prior state.

### 1. 目的

New Codex instance oriented itself by reading AGENTS.md and project execution files,
generated a handoff map, artifact locator, real cell status table, and gap plan.
Produced capped offline recovery of PSC/TTA artifacts. Did not start GPU/inference/training.

### 2. 核心输出

- `top_journal_v3/docs/codex_handoff_map_051.md`
- `top_journal_v3/docs/real_evidence_gap_plan_051.md`
- `top_journal_v3/docs/evidence_recovery_decision_051.md`
- `top_journal_v3/reports/artifact_locator_051.csv`
- `top_journal_v3/reports/real_cell_artifact_status_051.csv`
- `top_journal_v3/reports/tta_circular_variance_051.csv`
- `top_journal_v3/reports/psc_track_a_permatched_051.csv`
- `top_journal_v3/reports/verification_handoff_recovery_051.json`
- `outputs/persistent_artifacts/orientbench_real_051/` (capped offline recovery)

### 3. 使用的 Artifact

Read-only scan of `outputs/persistent_artifacts/`, `measure_fix_v2/`, `outputs/predictions/`.
Capped offline recovery — matched subsets, not full 17-field tables.

### 4. Real / Proxy / Synthetic

Capped real — offline recovery produces partial matched subsets from real detector outputs,
but flagged as not final evidence due to capping.

### 5. 是否改过 mask / split / metric

No changes to frozen files. TTA circular variance used theta -> 2theta correction (correct).
Masking: not applied to NRC in any 051 computation (unmasked).

### 6. 结论是否仍有效

- Handoff map and gap plan: RETAINED as accurate historical records.
- Capped matched subsets: NOT suitable for formal evidence; superseded by 052 full tables.
- Identified blocker (DOTA#20 phase_mod absent): RETAINED and confirmed by 052.
- DOTA#20 status row `match_iou_missing;phase_mod_missing;tta_missing`: RETAINED.

### 7. 保留/Supersede/重算建议

Retain handoff map and gap plan for audit trail. 052 full matched tables supersede all
051 capped recovery artifacts for formal evidence.

---

## Round 052

**Timestamp:** 2026-07-02 ~21:28–22:09 CST
**Instruction:** SUPERVISOR_052_CODEX_FORCE_REAL_DUMP_AND_FULL_MATCHED_TABLES — produce
DOTA#20 phase_mod forward dump and 7 full matched 17-field tables; no retraining.

### 1. 目的

Fill the final artifact gaps by: (a) generating DOTA#20 PSC phase_mod via 4-GPU
instrumented forward dump using shadow farm; (b) rebuilding 7 full matched 17-field
tables from real post-NMS schema and GT; (c) producing 4 PSC per-matched phase_mod full
tables; (d) producing 7 TTA circular variance full tables with theta -> 2theta correction.

### 2. 核心输出

- `outputs/persistent_artifacts/orientbench_real_052/` (root)
  - `dota20_phase_mod/DOTA-v1.0_20.pkl`
  - `matched_tables/{DOTA,DIOR,FAIR1M,SODA}/{cell}/matched_17field_full_052.jsonl`
- `outputs/persistent_artifacts/manifest_052.json`
- `top_journal_v3/reports/full_matched_tables_052.csv`
- `top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv`
- `top_journal_v3/reports/tta_circular_variance_full_052.csv`
- `top_journal_v3/reports/dota20_phase_mod_forward_dump_052.csv`
- `top_journal_v3/docs/dota20_phase_mod_forward_dump_052.md`
- `top_journal_v3/docs/full_matched_tables_052.md`
- `top_journal_v3/docs/psc_phase_mod_permatched_full_052.md`
- `top_journal_v3/docs/tta_circular_variance_full_052.md`
- `top_journal_v3/docs/evidence_ready_for_p1_p5_rerun_052.md`
- `top_journal_v3/reports/heartbeat_052.json`
- `top_journal_v3/reports/run_052_summary.json`

### 3. 使用的 Artifact

Real PSC/ORCNN/RTMDet checkpoints from `pth_data/`. Schema files from
`outputs/persistent_artifacts/orientbench_v2/`. GT files from `outputs/predictions/`
and `/dev/shm/`.

### 4. Real / Proxy / Synthetic

Real — all 7 full matched tables sourced from verified real detector checkpoints,
non-synthetic. `is_real_detector_output=True, is_synthetic_or_proxy=False` for all 7 cells.

### 5. 是否改过 mask / split / metric

No changes to `thresholds.yaml`, D_cal/D_audit split files, or frozen thresholds.

**ANOMALY 1 — DOTA#20 GT scope:** The GT file used for DOTA#20 matched tables is
`outputs/predictions/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl` — this is the D_cal
subset only (n_images=19, n_matched=486, mAP=0.0132). The full DOTA val set is not used.
This makes the DOTA#20 matched table a D_cal-subset dump, not a validation set result.
Verdict: **invalid_pending** per 055 A0.

**ANOMALY 2 — psc_phase_mod vs matched table mismatch:** The PSC per-matched phase_mod
table for DOTA#20 has n_matched=17,960 (heartbeat_052.json), while the full matched table
reports n_matched=486. This discrepancy suggests the phase_mod computation used a different
GT scope or matching protocol than the matched table.

**ANOMALY 3 — NRC not masked:** The full matched tables contain all instances with no
aspect_ratio filter. When 053 computed NRC from these tables, no masking was applied.
The 055 A0 forensic finding confirms this: masked NRC (aspect_ratio>=1.6) for
DIOR#22/FAIR1M#24/SODA#23 = 0.542/0.885/0.914, far below the unmasked 1.1265/1.5061/1.6733.

### 6. 结论是否仍有效

- Full matched tables for DIOR#22/FAIR1M#24/SODA#23/DIOR#3/DIOR#61/SODA#4: RETAINED as
  valid real artifacts; can be reused after applying aspect_ratio mask.
- DOTA#20 matched table (n_matched=486, 19 images, mAP=0.0132): INVALID_PENDING per A0.
- TTA circular variance tables: RETAINED (use theta->2theta, no masking ambiguity noted).
- PSC per-matched phase_mod tables: RETAINED for Track A analysis; A0 confirms intrinsic
  phase_mod reverse-calibration survives masking.
- Artifact readiness declaration `evidence_ready_for_p1_p5_rerun_052.md`: PARTIALLY VALID —
  valid for DIOR/FAIR/SODA; DOTA#20 scope is invalid_pending.

### 7. 保留/Supersede/重算建议

Retain DIOR/FAIR/SODA matched tables as primary real artifacts. Re-run NRC with
aspect_ratio>=1.6 mask. Flag DOTA#20 matched table as invalid_pending. Investigate
psc_phase_mod vs matched_table n_matched discrepancy for DOTA#20.

---

## Round 053

**Timestamp:** 2026-07-02 ~23:53–23:59 CST
**Instruction:** SUPERVISOR_053_CODEX_REAL_EVIDENCE_P1_P5_RERUN — formal P1–P5 rerun
using only 052 verified real artifacts.

### 1. 目的

Execute formal evidence rerun for P1–P5 using 052 real matched tables, per-matched
phase_mod, and TTA circular variance. Update writing sync patch. Run verifier. Issue
final 053 evidence verdict.

### 2. 核心输出

- `top_journal_v3/docs/top_journal_evidence_decision_053.md`
- `top_journal_v3/docs/p1_constructive_decoupling_experiment.md`
- `top_journal_v3/docs/p2_conformal_orientation_risk_control.md`
- `top_journal_v3/docs/p3_psc_free_mechanism_tests.md`
- `top_journal_v3/docs/p4_uncertainty_baselines_circular_stats.md`
- `top_journal_v3/docs/p5_downstream_selective_orientation_task.md`
- `top_journal_v3/docs/writing_sync_patch_053.md`
- `top_journal_v3/reports/p1_angle_perturb_dose_response.csv`
- `top_journal_v3/reports/p1_reverse_perturb_decoupling.csv`
- `top_journal_v3/reports/conformal_within_cell_risk_control.csv`
- `top_journal_v3/reports/conformal_shift_violation_audit.csv`
- `top_journal_v3/reports/psc_dota20_phase_mod.csv`
- `top_journal_v3/reports/psc_phase_mod_aliasing_hist.csv`
- `top_journal_v3/reports/psc_phase_mod_confounding_check.csv`
- `top_journal_v3/reports/uncertainty_baselines_nrc.csv`
- `top_journal_v3/reports/downstream_selective_orientation.csv`
- `top_journal_v3/scripts/verify_real_evidence_p1_p5_rerun_053.py`
- `top_journal_v3/reports/heartbeat_053.json`

### 3. 使用的 Artifact

052 full real matched tables (7 cells), 052 psc per-matched phase_mod, 052 TTA circular
variance. D_cal/D_audit flags recomputed from frozen hash assignment without modifying
split files.

### 4. Real / Proxy / Synthetic

Real — `source=052_full_real_matched_tables` or `052_tta_circular_variance_full` in all rows
of `uncertainty_baselines_nrc.csv`. `synthetic_or_proxy=False` in p1 dose-response.

### 5. 是否改过 mask / split / metric

No changes to thresholds.yaml, D_cal/D_audit files.

**CRITICAL PROTOCOL DRIFT — NRC computed UNMASKED:**
`uncertainty_baselines_nrc.csv` contains NRC computed from full matched tables with no
aspect_ratio filter. The 053 headline "score-only reverse-calibration" claim
(DIOR#22 NRC=1.1265, FAIR1M#24 NRC=1.5061, SODA#23 NRC=1.6733) is therefore an artifact
of near-square pooling, not a genuine orientation reliability finding. Under the frozen
masked protocol (aspect_ratio>=1.6), score-only NRC = 0.542/0.885/0.914 — all calibrated.
This is confirmed by 055 A0.

The p1_angle_perturb_dose_response.csv shows subgroup NRC breakdowns per shape class, but
the overall NRC column is also unmasked — the near-square_NRC, moderate_NRC, elongated_NRC
columns are present but the aggregate NRC is not recomputed from the masked subset only.

### 6. 结论是否仍有效

| Claim | Status |
|---|---|
| Overall verdict: `top_journal_discussion_level=false` | RETAINED |
| P1 partial (angle risk changes with perturbation) | RETAINED as directional |
| P1 "strong constructive decoupling" | NOT CLAIMED — correctly rated partial |
| P2 within-cell conformal violation rate=0, coverage 0.93–0.95, alpha=15 deg | RETAINED — main valid contribution |
| P2 shift audit: degradation only, no strict guarantee | RETAINED |
| P3 PSC phase_mod: all 4 cells `supports_phase_mod_mechanism=False` | RETAINED |
| Track A intrinsic phase_mod reverse-calibration | RETAINED per A0 (survives masking) |
| P4 geometry NRC=0.9579, TTA NRC=0.9478 (unmasked) | SUPERSEDED — must recompute with mask |
| P5 downstream fail | RETAINED |
| Score-only NRC > 1 = reverse-calibration | SUPERSEDED by A0 (near-square artifact) |
| DOTA#20 inclusion in P1 dose-response | SUPERSEDED — D_cal subset, mAP=0.0132, invalid_pending |
| `remote_sensing_journal_ready=possible` | RETAINED conditionally (requires NRC fix) |

### 7. 保留/Supersede/重算建议

- Supersede all unmasked NRC values; recompute with aspect_ratio>=1.6.
- Supersede DOTA#20 P1 dose-response rows.
- Retain P2 conformal risk control as primary valid contribution.
- Retain Track A phase_mod as mechanism candidate.
- Retain P1 qualitative direction (perturbation changes angle risk) but remove NRC > 1 claim.
- Do not claim score-only reverse-calibration.

---

## Round 054

**Timestamp:** 2026-07-03 ~11:38 CST (paper plan + writing) + 12:36 CST (handoff)
**Instructions:** SUPERVISOR_054_CODEX_REDUCED_SCOPE_CHINESE_PAPER_FINALIZATION;
then user request to produce successor handoff file.

### 1. 目的

Stop new experiments. Produce reduced-scope Chinese paper draft, negative-results document,
P2 main-claim writeup, final claim ledger, and verifier, all based on 053 verdict. Also
produce successor handoff document for 054.

### 2. 核心输出

- `top_journal_v3/docs/final_reduced_scope_paper_plan_054.md`
- `top_journal_v3/docs/orientation_reliability_reduced_scope_paper_zh.md`
- `top_journal_v3/docs/negative_results_and_boundaries_054.md`
- `top_journal_v3/docs/conformal_risk_control_main_claim_054.md`
- `top_journal_v3/docs/final_claim_ledger_reduced_scope_054.md`
- `top_journal_v3/docs/codex_latest_report.md`
- `top_journal_v3/docs/codex_successor_handoff_054.md`
- `top_journal_v3/scripts/verify_reduced_scope_paper_054.py`

### 3. 使用的 Artifact

No new experiments. Writing only — draws on 053 evidence and decisions. 052 artifacts
referenced but not rerun.

### 4. Real / Proxy / Synthetic

Writing round — no new computations. Inherits 053 real artifacts.

### 5. 是否改过 mask / split / metric

No changes. Verifier confirms: `thresholds.yaml / D_cal / D_audit protected diff: clean`.
No GPU used. No new experiments.

### 6. 结论是否仍有效

| Document | Status |
|---|---|
| `final_reduced_scope_paper_plan_054.md` — P2 as main contribution | RETAINED |
| `orientation_reliability_reduced_scope_paper_zh.md` — NRC section cites 053 unmasked values | SUPERSEDED in NRC numbers — must replace with masked values |
| `negative_results_and_boundaries_054.md` — P3/P4/P5 negative results | RETAINED |
| `final_claim_ledger_reduced_scope_054.md` — forbidden claims excluded | RETAINED |
| Claim that geometry-aware selector NRC and score-only NRC both unmasked in P4 comparison | SUPERSEDED — ratio may still hold but absolute values wrong |
| Paper framing: "OBB detection mAP does not fully characterize orientation reliability" | RETAINED (valid even with masked NRC) |
| P2 conformal risk control guarantee framing | RETAINED |
| Successor handoff document | RETAINED as accurate summary of 049–054 execution |

### 7. 保留/Supersede/重算建议

- Chinese paper draft is structurally sound; requires NRC section revision with masked values.
- Claim ledger is correct — forbidden claims properly excluded.
- Track A phase_mod reverse-calibration claim should be added/strengthened (survives A0).
- No new experiments needed for NRC fix — recompute from 052 matched tables with mask.

---

## Summary Verdict Table

| Round | Timestamp | Purpose (short) | Real/Proxy/Synthetic | Changed mask/split/metric | NRC masked? | Conclusion still valid? | Recommendation |
|---|---|---|---|---|---|---|---|
| 049 | 2026-07-02 ~18:47 | Initial P1-P5 top-journal evidence package | Mixed (proxy/synthetic P1/P5; partial real P2) | No | No (unmasked) | PARTIALLY SUPERSEDED — verdict directional only; all numbers superseded | Retain only as verdict record |
| 050 | 2026-07-02 ~20:14 | Real artifact inventory and gap recovery | Mostly real (5 cells); others scratch | No | No (unmasked) | RETAINED as inventory; NRC values superseded | Retain as gap record; 052 supersedes computations |
| 051 | 2026-07-02 ~21:03 | New Codex handoff; capped offline artifact recovery | Capped real (partial) | No | No (unmasked) | RETAINED as handoff/gap record; capped subsets not formal evidence | Retain planning artifacts; 052 supersedes |
| 052 | 2026-07-02 ~21:28 | Full real artifact rebuild (phase_mod + matched tables + TTA) | Real (verified) | No | N/A (tables only) | MOSTLY RETAINED — DOTA#20 invalid_pending (19-image D_cal subset); DIOR/FAIR/SODA tables valid | Apply aspect_ratio mask before NRC recompute; investigate DOTA#20 scope |
| 053 | 2026-07-02 ~23:53 | Formal P1-P5 evidence rerun on 052 real artifacts | Real (052 artifacts) | No (D_cal/D_audit flags re-derived, not modified) | No (CRITICAL DRIFT — unmasked) | PARTIALLY SUPERSEDED — P2 conformal RETAINED; NRC reverse-calibration claim SUPERSEDED; DOTA#20 rows SUPERSEDED | Supersede NRC claim; recompute with mask; retain P2 and P1 direction |
| 054 | 2026-07-03 ~11:38 | Reduced-scope paper writing; no new experiments | Writing only (inherits 053) | No | N/A (no recomputation) | PARTIALLY SUPERSEDED — paper structure/P2 RETAINED; NRC numbers in paper SUPERSEDED | Revise NRC section; add Track A phase_mod result; rest is valid |

---

## Anomalies Noted in Codex Logs

1. **DOTA#20 D_cal-subset scope (052–053):** `full_matched_tables_052.csv` shows DOTA#20 GT
   path = `outputs/predictions/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl`, n_images=19,
   mAP=0.0132. This is the D_cal subset only, not full val. The codex_and_supervisor.md
   log does not flag this as anomalous — it was never detected until 055 A0.

2. **PSC phase_mod vs matched table n_matched mismatch (052):** `heartbeat_052.json` shows
   DOTA#20 psc_phase_mod_permatched n_matched=17,960, but the full matched table n_matched=486.
   These use different GT scopes or matching protocols; the log does not explain this.

3. **Unmasked NRC throughout 049–053:** No round applied the frozen project protocol of
   aspect_ratio>=1.6 masking before computing NRC. The per-shape subgroup columns in
   p1_angle_perturb_dose_response.csv exist, but the aggregate NRC was computed from the
   unmasked full table. The codex log never mentions masking being skipped.

4. **052 run started 3 times (heartbeat_052.json):** The heartbeat shows `run_052 start`
   at 21:28, 21:32, and 21:35 CST — three consecutive starts within 7 minutes. This suggests
   the script was restarted twice before completing. Results appear consistent (same n_matched
   values), but the triple-start is a process anomaly not mentioned in the codex log.

5. **Ambiguous "shadow farm" for DOTA#20 phase_mod:** The 052 log entry claims "4GPU
   instrumented forward dump" for DOTA#20 phase_mod, but `heartbeat_049.json` records
   `gpu_used: false` and the 052 heartbeat shows phase_mod completion in under 1 second
   (`status: start` and `status: complete` at same timestamp 21:35:38 and 21:35:38). This
   is inconsistent with a real 4-GPU forward pass — suggests the "dump" may be synthetic
   or pre-cached, not a genuine GPU forward dump.
