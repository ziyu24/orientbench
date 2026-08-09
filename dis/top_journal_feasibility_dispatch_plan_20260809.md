# OrientBench Top-Journal Feasibility Dispatch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:superpowers-subagent-driven-development (recommended) or superpowers:superpowers-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the approved top-journal feasibility design into one auditable, no-GPU server instruction and synchronized C-side state without touching protected or scientific assets.

**Architecture:** Treat the dispatch as one atomic state transition. First preserve the r019 instruction with identical Git-canonical blob content, then replace the active instruction with a non-numbered feasibility audit contract, synchronize `C.md`, `review_state.json`, `collaboration_protocol.md`, `B_START_PROMPT.md`, and the approved design status, and finally validate and publish the exact C-side diff. The server audit has two independent tracks: metric robustness on already-consumed evidence and pristine-dataset asset/provenance screening; neither track authorizes a new experiment.

**Tech Stack:** Markdown evidence contracts, JSON state, PowerShell validation, Git/HTTPS publication.

---

## File map

- Create: `dis/sug/orientbench-c-r019-20260809-invalidated.md` — immutable Git-canonical blob-identical archive of the r019 instruction.
- Replace: `dis/sug.md` — active no-GPU feasibility audit instruction.
- Modify: `dis/top_journal_feasibility_gate_design_20260809.md` — record written approval and dispatch authorization.
- Modify: `dis/C.md` — C-side post-r019 adjudication and current venue/next-action decision.
- Modify: `dis/review_state.json` — machine-readable recovery state.
- Modify: `dis/collaboration_protocol.md` — cross-machine anchor and server ownership boundaries.
- Modify: `dis/B_START_PROMPT.md` — keep CC closed and point the next owner to the feasibility audit.
- Preserve exactly: `dis/B.md` — protected B/CC-owned file.
- Future server-only report: `dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md` — designated but not created by C.

The C-side transition is intentionally one commit: publishing any subset would leave the active instruction and recovery state contradictory.

### Task 1: Freeze approval and preserve r019

**Files:**
- Create: `dis/sug/orientbench-c-r019-20260809-invalidated.md`
- Modify: `dis/top_journal_feasibility_gate_design_20260809.md`
- Preserve: `dis/B.md`

- [ ] **Step 1: Reconfirm the clean baseline and remote**

Run from the repository root:

```powershell
$head = git rev-parse HEAD
$remoteMain = (git ls-remote https://github.com/ziyu24/orientbench.git refs/heads/main).Split("`t")[0]
$status = git status --porcelain=v1
$bBlob = git rev-parse 'HEAD:dis/B.md'
if ($head -ne 'f2aeeb2edd177f6eb62c390042ea74068316570d') { throw "Unexpected HEAD: $head" }
if ($remoteMain -ne $head) { throw "HTTPS main mismatch" }
if ($status) { throw "Dirty worktree" }
if ($bBlob -ne 'c0c2571f3a5c828673b39e6458ceaed5f14c5a6a') { throw "Protected B mismatch" }
```

Expected: no exception.

- [ ] **Step 2: Record the active r019 instruction identity**

```powershell
$oldSug = Get-Item -LiteralPath 'dis/sug.md'
$oldRawHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $oldSug.FullName).Hash.ToLowerInvariant()
$oldRawBytes = $oldSug.Length
$oldCanonicalBlob = (git rev-parse 'HEAD:dis/sug.md').Trim()
"$oldRawBytes $oldRawHash $oldCanonicalBlob"
```

Expected: one raw working-tree byte count, one raw SHA256, and one 40-character Git canonical blob ID. Retain the blob ID for Step 4; raw size and SHA256 are cross-platform newline diagnostics only.

- [ ] **Step 3: Archive through `apply_patch` and update approval metadata**

Use `apply_patch` to move the complete current `dis/sug.md` text to `dis/sug/orientbench-c-r019-20260809-invalidated.md` without changing its Git-canonical content. Working-tree newline normalization is acceptable only when the filter-aware blob identity in Step 4 matches. In the design YAML header, set exactly:

```yaml
document_status: APPROVED_WRITTEN_SPEC
user_conceptual_approval: true
user_written_spec_approval: true
server_execution_authorized: true
```

Do not change the frozen scientific design sections.

- [ ] **Step 4: Prove archive identity before creating the new active instruction**

```powershell
$archive = Get-Item -LiteralPath 'dis/sug/orientbench-c-r019-20260809-invalidated.md'
$archiveRawHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive.FullName).Hash.ToLowerInvariant()
$archiveRawBytes = $archive.Length
$archiveCanonicalBlob = (git hash-object --filters --path='dis/sug.md' $archive.FullName).Trim()
if ($archiveCanonicalBlob -ne $oldCanonicalBlob) { throw "Archive canonical blob mismatch" }
"$archiveRawBytes $archiveRawHash $archiveCanonicalBlob"
```

Expected: no exception and equal Git canonical blob IDs. Raw byte count or SHA256 may differ only because of working-tree newline normalization and remain diagnostic; any canonical mismatch stops the transition and must not be reconstructed around.

### Task 2: Write the active feasibility audit contract

**Files:**
- Create: `dis/sug.md`
- Future server writes, explicitly authorized by this file only:
  - `top_journal_v3_reaudit_055/feasibility_gate_20260809/**`
  - `outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/**`
  - `dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md`
  - `claude_code_and_supervisor.md` append-only

- [ ] **Step 1: Add the identity and hard scope**

Create `dis/sug.md` with these exact identity values:

```yaml
round_id: orientbench-c-topjournal-feasibility-20260809
control_base: f2aeeb2edd177f6eb62c390042ea74068316570d
scientific_data_cutoff: a9067fb16d2bbd747dfe69789ac33a5911eb15fe
status: READY_FOR_SERVER_EXECUTION
server_report_path: dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md
runtime_root: outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809
gpu_authorized: false
download_authorized: false
training_authorized: false
inference_authorized: false
new_target_outcome_authorized: false
cc_recommendation: no
```

State that this is not r020, not a repair of r019, and not a new scientific endpoint. Fix r019 as `INVALIDATED_R019 / PROTOCOL_DRIFT_R019 / FAIL_IMPLEMENTATION_R019 / FAIL_TIMELOCK_R019`; its numbers are `INVALIDATED_R019_DESCRIPTIVE_ONLY`.

- [ ] **Step 2: Define preflight and completion semantics**

The contract must require the server to:

```text
read all applicable AGENTS.md/CLAUDE.md and pth_data/readme.md;
pull only with git pull --ff-only over HTTPS;
verify current/default branch, upstream, full HEAD, remote main, clean index/worktree;
verify dis/B.md blob c0c2571f3a5c828673b39e6458ceaed5f14c5a6a;
require runtime_root not to exist and never delete/overwrite an old directory;
continue through missing scientific assets and negative feasibility findings;
early-stop only on repository/rule/protected-file/runtime-collision/access-control or executable-audit failure.
```

Missing assets, contaminated datasets, metric reversal, baseline domination, incompatible angle semantics, and license blockage are completed negative findings, not early stops.

- [ ] **Step 3: Freeze Track M inputs, scores, metrics, and status mapping**

Require an inventory-first audit over the six Core units (DIOR-R A/B/C, FAIR1M D, SODA-A E/F) and optional r019 DOTA units marked descriptive-only. Every consumed artifact needs path, role, source commit/manifest, bytes, SHA256, schema, row count, unique row-key witness, cluster count/set SHA, and actual access log. If any required Core unit lacks byte-exact row-level risk and all required score columns, return `INSUFFICIENT_ASSETS`; never infer rows from summaries.

Freeze the reliability scores as:

```text
raw_confidence = identity detection score
linear_source_frozen = existing sealed score+AR+size linear output; no refit
tta_angle = -u_axis
tta_localization = -(missing_fraction + iou_loss)
S0 = -(u_axis + missing_fraction + iou_loss)
learned_EQS = descriptive-only comparator, never candidate driver
```

No missing score may be regenerated by model fitting. Computing the stated algebraic scores from existing byte-exact columns is allowed and must be logged.

Use the frozen r014/r019 continuous orientation severity and only rescale it, without changing ordering or eligibility:

```text
risk_cap3 = clip(angle_error / max(delta_theta_0.75(GT_AR), 1 degree), 0, 3)
residual = risk_cap3 / 3
```

Thus the AUGRC residual is fixed in `[0,1]`; raw `risk_cap3` must also be reported for backward comparison. Freeze generalized risk at threshold `t` as

```text
GR(t) = (1/N) * sum_i residual_i * I(score_i >= t)
```

and AUGRC as trapezoidal integration of the unique-threshold generalized-risk/coverage curve including `(coverage=0, risk=0)`, unscaled; for binary residuals its range is `[0,0.5]`. Tie groups enter together. The implementation must reproduce the pinned official reference behavior from `IML-DKFZ/fd-shifts@c4467aec134e99691359da209f811d91283fc1e3`, `rc_stats.py` and `rc_stats_utils.py`, on binary and continuous toy vectors to `atol=1e-12, rtol=0`; it must not import a floating network package at runtime.

Also report AURC/NRC sensitivity, complete risk–coverage data, `Risk@70%`, `Risk@90%`, and nonempty coverage. For fixed coverage `q`, evaluate only unique score thresholds, choose the threshold-induced coverage that is the smallest coverage `>=q`, report that actual coverage, and compute selective risk as the accepted-set mean residual; never split a tie group or choose the lowest-risk threshold after seeing outcomes. Keep image clusters for DIOR/FAIR and original mother-scene clusters for SODA/DOTA, including zero-eligible clusters. Use unit-first, unit-equal dataset aggregation; never pooled rows. For any 10,000-replicate paired cluster bootstrap use seed `20260809`, synchronized multiplicities across scores within a unit/dataset, percentile 95% CI, and exactly replicates `0..9999`. A CPU-intensive implementation must use at least 39 of 48 cores and record actual child-process CPU/RSS/affinity; a non-intensive serial inventory need not manufacture utilization.

Freeze mutually exclusive Track M states:

```text
INSUFFICIENT_ASSETS: any Core A-F unit lacks the required byte-exact row/score/cluster evidence.
METRIC_REVERSAL: S0 appears better under NRC/AURC but is worse than any equal-budget nonlearned baseline on AUGRC or Risk@70/Risk@90 for any dataset aggregate.
BASELINE_DOMINATED: absent metric reversal, any equal-budget nonlearned baseline has lower AUGRC than S0 on any Core dataset aggregate.
SENSITIVITY_UNSTABLE: absent the above, the S0-vs-baseline direction flips under any prespecified matching/unmatched/near-square/canonicalization sensitivity already derivable from sealed assets.
ROBUST_CANDIDATE: all Core assets are complete; S0 has strictly lower AUGRC than raw_confidence, linear_source_frozen, tta_angle, and tta_localization on every Core dataset aggregate; Risk@70 and Risk@90 never reverse; NRC/AURC and all prespecified sensitivities never reverse; learned_EQS is not used in this decision.
```

Bootstrap CIs are evidence and must be reported, but this feasibility state is a deterministic no-reversal screen, not a formal scientific confirmation.

- [ ] **Step 4: Freeze Track D candidates and evidence rules**

Audit all four candidates even after one fails:

```text
1. AI-TOD-R
2. UAV-OBB
3. ShipRSImageNet (backup)
4. ICDAR-MLT (auxiliary only; cannot satisfy the remote-sensing two-dataset gate)
```

For each, require official source URL and retrieval date, license/use terms, exact version/split/image/annotation metadata, OBB/angle/ignore semantics, local path/stat-only presence, and exact compatible config/checkpoint/environment/hash inventory. No dataset archive may be downloaded, no package installed, no model run, and no target annotation opened to compute an outcome. Official HTML/README/license retrieval is allowed; save URL, HTTP status, bytes, SHA256, and source date.

Run a real prior-outcome search over Git-tracked text, the OrientBench persistent-artifact tree, registered project manifests/reports, `pth_data/readme.md`, and filename/stat-only views under the dataset root. Search candidate names and aliases plus prediction/feature/score/risk/metric/bootstrap/report/endpoint terms. Save exact command, cwd, roots, excludes, start/end, exit code, stdout/stderr hashes, and each hit adjudication. Do not hash or decode candidate annotation contents.

Freeze candidate statuses:

```text
ELIGIBLE_CANDIDATE: clear license, reproducible local assets, independently verifiable angle contract, no prior outcome, and exact assets for one common set of at least three detector families.
CONTAMINATED: any existing real prediction, metric, risk, bootstrap, or same-endpoint consumption.
MISSING_ASSET: data, one of the common three-family configs/checkpoints, or compatible environment is absent.
INCOMPATIBLE_ANGLE_CONTRACT: conversion cannot be independently and unambiguously verified.
LICENSE_BLOCKED: research use, redistribution, or access terms are unclear/incompatible.
```

If multiple failure statuses apply, preserve all facts and choose precedence `CONTAMINATED > LICENSE_BLOCKED > INCOMPATIBLE_ANGLE_CONTRACT > MISSING_ASSET`.

- [ ] **Step 5: Freeze the joint gate**

Write exactly:

```text
PASS_TO_METHOD_DESIGN iff Track M=ROBUST_CANDIDATE AND at least two independent remote-sensing OBB datasets are ELIGIBLE_CANDIDATE AND both support the same >=3 detector-family set AND >=1 family was absent from old Core development AND no future target-label tuning is needed.

FAIL_TO_MEASUREMENT_ONLY iff Track M is METRIC_REVERSAL, BASELINE_DOMINATED, or SENSITIVITY_UNSTABLE; OR fewer than two remote-sensing candidates are ELIGIBLE_CANDIDATE; OR no common >=3-family set exists; OR license/angle contracts do not close; OR target-label tuning would be required.

INCONCLUSIVE_FEASIBILITY only when Track M=INSUFFICIENT_ASSETS and Track D has not independently triggered FAIL_TO_MEASUREMENT_ONLY. It never authorizes a method study and defaults to measurement-only writing.
```

`PASS_TO_METHOD_DESIGN` authorizes only a future protocol draft and another user approval. It does not authorize download, training, inference, label access, or an experiment.

- [ ] **Step 6: Freeze interpretation and novelty boundaries**

The task and report must state that a positive feasibility gate is not a scientific confirmation, not venue readiness, and not evidence for CVPR/ICCV. It may support drafting a future protocol only. It must not claim first use of TTA uncertainty, angle quality, selective prediction, multi-pass angular dispersion, or cross-detector reliability evaluation. A fixed score may be called `training-free` or `no learned parameters`, never `parameter-free`. The measurement contribution remains the detector-agnostic, angle-specific, geometry-equivalence-aware, scene-aware OBB reliability protocol; learned EQS stays appendix-only.

Pin the AUGRC conceptual source to Traub et al., *Overcoming Common Flaws in the Evaluation of Selective Classification Systems*, NeurIPS 2024 / arXiv:2407.01032, and the exact implementation reference to the commit already specified. No additional novelty search or manuscript edit is authorized in this server task.

- [ ] **Step 7: Specify implementation freedom, validator, evidence, and report**

Allow implementation freedom only for process scheduling, internal filenames, and table formatting. Require separate generator and validator entry points; the validator reads raw sealed inputs, never generator gate tokens. Require true mutation tests that each exit nonzero after: changing one score byte, deleting one cluster, inserting a fake prior-outcome hit, and changing one manifest hash.

Require at least:

```text
protocol.json
preflight.json
track_m_asset_inventory.csv
track_m_metrics.csv
track_m_bootstrap.csv or an exact replicate inventory plus hash
track_m_status.json
track_d_candidate_inventory.csv
track_d_official_sources.csv
track_d_prior_outcome_hits.csv
track_d_status.json
joint_gate.json
execution_ledger.csv
resource_telemetry.csv/json
evidence_manifest.json
validator.json
protocol_closure.md
dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md
```

The report must distinguish `FULL_COMPLETION`, `EARLY_STOP_TECHNICAL`, and `FAILED_EXECUTION`, enumerate every completed/omitted phase, and say whether `dis/sug.md` was genuinely exhausted. Final dialogue line 1 is exactly `执行完毕` only if both tracks, validator, commit, push, and external Git receipt complete; otherwise `未执行完毕`. Line 2 is the unique report path. Missing/negative scientific findings can still be `FULL_COMPLETION`.

- [ ] **Step 8: Close write and Git scope**

Authorize only the four paths listed in this task’s file header. Require exactly one server result commit, explicit staging, HTTPS push, no force/merge/rebase/reset/clean/checkout/stash, unchanged protected B blob, and a post-push external receipt that does not write into the commit it verifies. The tracked report uses `final_commit_sha=POST_COMMIT_EXTERNAL_RECEIPT` and `git_publish_status=PENDING_EXTERNAL_RECEIPT`; the final dialogue provides actual final/remote SHA, changed-path count, B equality, and clean worktree.

### Task 3: Synchronize C-side recovery state

**Files:**
- Modify: `dis/C.md`
- Modify: `dis/review_state.json`
- Modify: `dis/collaboration_protocol.md`
- Modify: `dis/B_START_PROMPT.md`

- [ ] **Step 1: Replace `C.md` with the post-r019 adjudication**

The document must bind:

```yaml
round_id: orientbench-c-topjournal-feasibility-dispatch-20260809
control_base: f2aeeb2edd177f6eb62c390042ea74068316570d
scientific_data_cutoff: a9067fb16d2bbd747dfe69789ac33a5911eb15fe
r019_formal_status: INVALIDATED_R019
current_route: ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC
tgrs_status: CONDITIONAL_ON_METHOD_UPGRADE
cc_recommendation: no
```

State the decisive r019 audit witnesses, keep its positive linear contrast and negative standalone guard descriptive-only, remove learned EQS from the main contribution, and designate the no-GPU feasibility gate as the sole next action. Explicitly prohibit DOTA/HRSC/Core rescue, r020, gate substitution, and repeated CC.

- [ ] **Step 2: Update `review_state.json` with valid JSON**

Use `schema_version: 1.5`, `round_id: orientbench-c-topjournal-feasibility-20260809`, `review_base_sha: f2aeeb2...`, `scientific_snapshot_sha: a9067fb...`, protected B blob unchanged, and these key states:

```json
{
  "r019_execution": "COMPUTATION_REACHED_TARGET_AND_10000_BOOTSTRAP",
  "r019_formal_verdict": "INVALIDATED_R019_PROTOCOL_DRIFT_FAIL_IMPLEMENTATION_FAIL_TIMELOCK",
  "r019_numbers": "INVALIDATED_DESCRIPTIVE_ONLY",
  "learned_eqs_role": "APPENDIX_FAILED_MIGRATION_ONLY",
  "current_route": "ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC",
  "tgrs_status": "CONDITIONAL_ON_FUTURE_METHOD_UPGRADE",
  "top_conference_status": "NOT_SUPPORTED"
}
```

Set C/server/next action to `READY_FOR_SERVER_FEASIBILITY_GATE`, point to the new instruction/report/runtime root, set all GPU/download/training/inference/new-outcome authorizations false, and retain CC as completed/no recommendation.

- [ ] **Step 3: Update the collaboration and CC handoff files**

`collaboration_protocol.md` must use the same current state, SHAs, instruction/report paths, protected B blob, no-GPU boundaries, joint gate, and completion semantics. `B_START_PROMPT.md` must keep the prior CC round completed, set `next_owner: C / server feasibility gate`, state `cc_recommendation: no`, and point to the new `dis/sug.md`; it must not invite new B work.

- [ ] **Step 4: Parse and cross-check state**

```powershell
$state = Get-Content -LiteralPath 'dis/review_state.json' -Raw -Encoding UTF8 | ConvertFrom-Json
if ($state.round_id -ne 'orientbench-c-topjournal-feasibility-20260809') { throw 'round mismatch' }
if ($state.server.instruction_path -ne 'dis/sug.md') { throw 'instruction mismatch' }
if ($state.server.report_path -ne 'dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md') { throw 'report mismatch' }
if ($state.scientific_state.r019_formal_verdict -notmatch '^INVALIDATED_R019') { throw 'r019 status drift' }
```

Expected: no exception.

### Task 4: Validate the complete dispatch

**Files:**
- Test all seven C-owned changed files.
- Preserve: `dis/B.md`.

- [ ] **Step 1: Run placeholder, uniqueness, and contract checks**

```powershell
$changedText = @(
  'dis/sug.md',
  'dis/C.md',
  'dis/review_state.json',
  'dis/collaboration_protocol.md',
  'dis/B_START_PROMPT.md',
  'dis/top_journal_feasibility_gate_design_20260809.md',
  'dis/top_journal_feasibility_dispatch_plan_20260809.md'
)
rg -n "TODO|TBD|PLACEHOLDER|READY_FOR_SERVER_R019|PASS_EXTERNAL_DOTA_EQS_RC_R019" -- $changedText
```

Expected: no unresolved placeholder or stale active-state match. Historical negative references must be inspected rather than mechanically deleted.

Check exactly one active report path and exactly one active runtime root across `C.md`, `review_state.json`, `collaboration_protocol.md`, and `sug.md`. Check that the future report does not already exist.

- [ ] **Step 2: Verify scope and protected ownership**

```powershell
$allowed = @(
  'dis/B_START_PROMPT.md',
  'dis/C.md',
  'dis/collaboration_protocol.md',
  'dis/review_state.json',
  'dis/sug.md',
  'dis/sug/orientbench-c-r019-20260809-invalidated.md',
  'dis/top_journal_feasibility_dispatch_plan_20260809.md',
  'dis/top_journal_feasibility_gate_design_20260809.md'
)
$changed = @(git status --short | ForEach-Object { $_.Substring(3).Replace('\','/') } | Sort-Object)
if (Compare-Object $allowed $changed) { throw "Changed-path scope mismatch" }
if (git diff -- 'dis/B.md') { throw 'Protected B changed' }
if ((git rev-parse 'HEAD:dis/B.md') -ne 'c0c2571f3a5c828673b39e6458ceaed5f14c5a6a') { throw 'Protected B blob mismatch' }
git -c core.safecrlf=false diff --check
```

Expected: no exception, exit code zero, and no diff-check output. This command checks genuine whitespace errors while suppressing Windows `core.safecrlf` line-ending warnings.

- [ ] **Step 3: Self-review against the approved design**

Map every section of `dis/top_journal_feasibility_gate_design_20260809.md` to an active `dis/sug.md` section. Confirm these invariants manually:

```text
r019 is invalidated, not repaired;
learned EQS cannot drive a positive gate;
Track M uses only consumed byte-exact evidence;
Track D cannot download, train, infer, or compute candidate outcomes;
two remote-sensing datasets x one common >=3-family set is irreducible;
PASS_TO_METHOD_DESIGN still requires another user approval;
negative feasibility findings are FULL_COMPLETION, not early stop;
CC remains closed;
no r020 exists.
```

### Task 5: Commit and publish atomically

**Files:**
- Stage exactly the eight allowed paths from Task 4.

- [ ] **Step 1: Stage explicitly and validate the index**

```powershell
git add -- dis/B_START_PROMPT.md dis/C.md dis/collaboration_protocol.md dis/review_state.json dis/sug.md dis/sug/orientbench-c-r019-20260809-invalidated.md dis/top_journal_feasibility_dispatch_plan_20260809.md dis/top_journal_feasibility_gate_design_20260809.md
git diff --cached --name-status
git diff --cached --check
if (git diff --cached --name-only -- 'dis/B.md') { throw 'Protected B staged' }
```

Expected: exactly the eight authorized C-owned paths; archive shown as create, active instruction/state as modifications.

- [ ] **Step 2: Commit with the repository identity**

```powershell
git commit -m "任务：下发顶刊可行性审计"
```

Expected: one commit containing only the validated C-side transition.

- [ ] **Step 3: Push over HTTPS and independently verify**

```powershell
git push https://github.com/ziyu24/orientbench.git HEAD:main
$head = git rev-parse HEAD
$remoteMain = (git ls-remote https://github.com/ziyu24/orientbench.git refs/heads/main).Split("`t")[0]
if ($head -ne $remoteMain) { throw 'Push verification failed' }
if (git status --porcelain=v1) { throw 'Worktree not clean' }
if ((git rev-parse 'HEAD:dis/B.md') -ne 'c0c2571f3a5c828673b39e6458ceaed5f14c5a6a') { throw 'Protected B changed' }
```

Expected: HTTPS `main` equals local HEAD, worktree/index are clean, and the protected B blob is unchanged.

### Task 6: User/server handoff

**Files:**
- Read: committed `dis/sug.md`

- [ ] **Step 1: Return the exact server pull target and instruction**

Report the final dispatch commit SHA and tell the server to pull HTTPS `main` and execute `dis/sug.md`. State plainly that the server must report whether every task section was genuinely completed or where it technically stopped; missing assets and negative scientific findings are completed results, not early stops.

- [ ] **Step 2: Stop C-side work**

Do not run the server audit locally, edit the manuscript, contact CC, create the future server report, or start a method experiment. Wait for the unique server report and final external Git receipt.
