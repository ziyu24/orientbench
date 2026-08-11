# OrientBench JPRS Measurement-Validity Dispatch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:superpowers-subagent-driven-development (recommended) or superpowers:superpowers-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish one auditable CPU-only r020 dispatch that adjudicates whether OBB-specific measurement choices materially change reliability conclusions across the sealed Core A-F evidence.

**Architecture:** Archive the consumed receipt3 contract, record its formal abnormal audit status, then atomically replace the shared dispatch and C-side state with the approved measurement-validity design. The server contract uses two independent clean-room implementations, a third comparator, real raw/logic mutations, an acyclic manifest/report/external-receipt chain, and a single final publication commit.

**Tech Stack:** Markdown/YAML, JSON, Git, PowerShell validation, server-side Python/pandas/NumPy/PyArrow/SciPy.

---

### Task 1: Preserve receipt3 and write approved planning artifacts

**Files:**
- Create: `dis/sug/orientbench-c-topjournal-feasibility-receipt3-20260811-abnormal-audit.md`
- Create: `dis/jprs_measurement_validity_gate_design_20260811.md`
- Create: `dis/jprs_measurement_validity_dispatch_plan_20260811.md`

- [ ] **Step 1: Record the source identities before any edit**

Run:

```powershell
git rev-parse HEAD
git rev-parse HEAD:dis/sug.md
git rev-parse HEAD:dis/server_reports/orientbench-c-topjournal-feasibility-receipt3-20260811.md
git rev-parse HEAD:dis/B.md
```

Expected: `594654a95d50b1f14b87252698911cc3fc583b03`, active sug blob `aeb79060e50aeaa615b365065fc087dc7b9e74cc`, receipt3 report blob `498dd8094f713a4a76339890ffd3a9ec45352344`, protected B blob `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`.

- [ ] **Step 2: Move the active receipt3 contract with `apply_patch`**

Move `dis/sug.md` to the archive path without changing its content. Verify filter-aware identity:

```powershell
$archive = 'dis/sug/orientbench-c-topjournal-feasibility-receipt3-20260811-abnormal-audit.md'
if ((git hash-object --filters --path=dis/sug.md $archive).Trim() -ne 'aeb79060e50aeaa615b365065fc087dc7b9e74cc') { throw 'archive mismatch' }
```

- [ ] **Step 3: Save the approved design and this plan**

The design must preserve the truthful user route approval and C-authored specification status, `server_execution_authorized: true`, the four-state gate, five orthogonal geometry/AR ablation classes, 270/135 Holm families, the independent B-before-A order and the no-rescue rule. It must not claim that the user separately reviewed every line of the expanded technical specification.

### Task 2: Write the r020 active server contract with TDD

**Files:**
- Create: `dis/sug.md`
- Future server writes only:
  - `top_journal_v3_reaudit_055/measurement_validity_r020_20260811/**`
  - `outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811/**`
  - `outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811_postseal_receipt/**`
  - `dis/server_reports/orientbench-c-r020-measurement-validity-20260811.md`
  - `claude_code_and_supervisor.md` append-only

- [ ] **Step 1: Run RED assertions before creating the contract**

Run an inline PowerShell verifier requiring the new round id, new code/runtime/report paths, `PASS_TO_EXTERNAL_CONFIRMATION`, `FAIL_GENERIC_OR_NULL`, `INCONCLUSIVE_MIXED`, `NOT_ADJUDICATED`, `B_BEFORE_A`, `270`, `135`, `EQS_FORBIDDEN_SCIENTIFIC_INPUT`, `ACCESS_EVENT_MANIFEST_EXACT`, six real mutations, and the two Chinese status phrases. Expected: nonzero because the active r020 contract does not exist.

- [ ] **Step 2: Create the minimal complete contract with `apply_patch`**

The YAML header must bind planning base `594654a95d50b1f14b87252698911cc3fc583b03`, the protected B blob, receipt3 abnormal status/report/blob, approved design/plan paths, unique future paths, server permissions, `cc_recommendation: no`, and `status: READY_FOR_SERVER_EXECUTION`.

The body must copy the design's frozen population/membership, input hashes, and strict `(image_id,pred_id)` cohort join contract: freeze the D_audit matched base cohort first, semi-select full-table features/scores, require cohort missing/duplicate/drop=0, record but exclude legal RHS extras, and compare `detection_score` only between features and scores. It must also copy the keyed operands/epsilon/swap formulas, endpoint families, absolute-centered p formula, bootstrap, descriptive-only SCENE_MACRO with no IID/material claim, four-state gate and full `(effect_class,ablation_id,contrast,endpoint,supported_direction)` signature; the exact finite-grid/`numpy.interp`/inverse-tail delta algorithm and precision-compatible 0.00105-degree direct-root audit; the pre-data code seal, B-before-A order, hash-chained live tracer plus normalized bidirectional OS-open coverage, correctly ordered four pre-freeze + manifest + planned-report mutations, 48-logical-CPU/39-worker 30-second process-tree resource contract, explicit-HTTPS Git authority with configured origin/upstream treated only as migration metadata, fixed post-seal receipt root/schema/atomic JSON+sidecar, no-cycle closure, exactly one final server commit and completion semantics. No placeholder SHA is allowed except the explicitly future `POST_COMMIT_EXTERNAL_RECEIPT` token in the future server report.

- [ ] **Step 3: Run GREEN assertions**

Expected: every RED token is present exactly in the intended section; Markdown fences balance; no future report exists; no `EQS` gate or receipt3 scientific input is authorized.

### Task 3: Synchronize C-side state

**Files:**
- Modify: `dis/C.md`
- Modify: `dis/review_state.json`
- Modify: `dis/collaboration_protocol.md`
- Modify: `dis/B_START_PROMPT.md`

- [ ] **Step 1: Run RED state assertions**

Require receipt3=`ABNORMAL_EXECUTABLE_AUDIT_FAILURE / PROTOCOL_DRIFT / NOT_ADJUDICATED / non_reusable`, r020=`READY_FOR_SERVER_EXECUTION / NOT_STARTED`, route=`ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC`, learned EQS=`APPENDIX_FAILED_ONLY`, CC=`COMPLETED_CLOSED/no`, and all four new paths. Expected: fail because current files still claim receipt3 `NOT_STARTED`.

- [ ] **Step 2: Apply the four-file state transition**

Use `apply_patch` only. `review_state.json` must be valid JSON and distinguish `existing_core_measurement_reanalysis_authorized: true` from `new_target_dataset_outcome_authorized: false`. GPU/general download/install/training/forward/inference/annotation-root/manuscript/method permissions remain false; new protocol and existing-Core CPU reanalysis are true. `B_START_PROMPT.md` remains a closed CC status notice, never a new invitation.

- [ ] **Step 3: Run GREEN state assertions**

Parse JSON, parse the YAML headers, verify cross-file round/path/status equality, verify the future report is absent, and verify server dialogue is limited to `正常执行完毕` or `异常结束`.

### Task 4: Validate the atomic C-side transition

**Files:** Test exactly the eight paths from Tasks 1-3 and preserve `dis/B.md`.

- [ ] **Step 1: Verify exact scope and ownership**

```powershell
$allowed = @(
  'dis/B_START_PROMPT.md',
  'dis/C.md',
  'dis/collaboration_protocol.md',
  'dis/jprs_measurement_validity_dispatch_plan_20260811.md',
  'dis/jprs_measurement_validity_gate_design_20260811.md',
  'dis/review_state.json',
  'dis/sug.md',
  'dis/sug/orientbench-c-topjournal-feasibility-receipt3-20260811-abnormal-audit.md'
) | Sort-Object
$changed = @(git status --short | ForEach-Object { $_.Substring(3).Replace('\','/') } | Sort-Object)
if (Compare-Object $allowed $changed) { throw 'scope mismatch' }
if (git diff -- dis/B.md) { throw 'B changed' }
if (git diff --cached -- dis/B.md) { throw 'B staged' }
if ((git rev-parse HEAD:dis/B.md).Trim() -ne 'c0c2571f3a5c828673b39e6458ceaed5f14c5a6a') { throw 'B blob mismatch' }
```

- [ ] **Step 2: Verify structures and semantic invariants**

Parse `review_state.json`; parse all changed YAML headers; balance Markdown fences. Require receipt3 report blob `498dd8094f713a4a76339890ffd3a9ec45352344`, archive canonical blob `aeb79060e50aeaa615b365065fc087dc7b9e74cc`, exact 270/135 families, full signature including ablation and direction, exact sign-specific CI inequalities, strict zero-loss 1:1 joins, live hash-chain plus OS-open trace, precision-compatible root audit, correctly ordered six mutations without any post-freeze runtime write, fixed post-seal receipt root/schema/sidecar, `POSTFREEZE_COMMAND_LOG_SEAL` before the no-subprocess receipt writer, and provisional-before-receipt semantics, no S0/EQS gate, no receipt3 scientific input, unique report path, no unresolved planning placeholders, and future report/receipt absence.

- [ ] **Step 3: Run whitespace and staged checks**

```powershell
git -c core.safecrlf=false diff --check
if (git diff --cached --name-only) { throw 'index not empty before publication' }
```

Expected: exit 0 with no output and empty index.

### Task 5: Commit and publish the dispatch

**Files:** Stage exactly the eight authorized paths.

- [ ] **Step 1: Stage explicitly and re-run all checks against the index**

```powershell
git add -- dis/B_START_PROMPT.md dis/C.md dis/collaboration_protocol.md dis/jprs_measurement_validity_dispatch_plan_20260811.md dis/jprs_measurement_validity_gate_design_20260811.md dis/review_state.json dis/sug.md dis/sug/orientbench-c-topjournal-feasibility-receipt3-20260811-abnormal-audit.md
git diff --cached --name-status
git -c core.safecrlf=false diff --cached --check
```

Expected: exactly eight paths, no B path and no whitespace error.

- [ ] **Step 2: Commit once**

Immediately before committing, require explicit HTTPS remote `main` to remain `594654a95d50b1f14b87252698911cc3fc583b03`; if it moved, stop without merge, rebase, commit or push.

```powershell
git commit -m "任务：下发JPRS测量有效性终门"
```

Expected: one non-merge commit whose parent is `594654a95d50b1f14b87252698911cc3fc583b03`.

- [ ] **Step 3: Push explicitly over HTTPS and verify**

```powershell
git push https://github.com/ziyu24/orientbench.git HEAD:main
$head = (git rev-parse HEAD).Trim()
$remote = ((git ls-remote https://github.com/ziyu24/orientbench.git refs/heads/main) -split [char]9)[0]
if ($head -ne $remote) { throw 'push mismatch' }
if (git status --porcelain=v1) { throw 'dirty worktree' }
```

Expected: HTTPS main equals the dispatch commit. Fast-forward the original checkout with HTTPS `git pull --ff-only`; never merge/rebase/reset/force.

### Task 6: Hand off to the server

- [ ] **Step 1: Give the server the exact commit and plan path**

The server must HTTPS fast-forward to the published 40-hex commit and execute only `dis/sug.md`. It must not choose a competing plan or reuse receipt3 paths.

- [ ] **Step 2: Accept only the compact Chinese status**

The server dialogue is exactly the project wrapper plus `正常执行完毕` or `异常结束`. A provisional scientific PASS, FAIL or INCONCLUSIVE with complete protocol and a VALID server-local receipt may say normal; any technical/provenance/audit/publication defect must say abnormal. The ignored receipt never becomes cross-machine formal state. After either phrase, C must HTTPS fast-forward, independently verify the published result commit/report/checker/mutation and then publish a separate `dis/` post-pull adjudication before adopting any scientific gate.
