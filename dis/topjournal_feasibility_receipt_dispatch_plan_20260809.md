# OrientBench Feasibility Receipt Dispatch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:superpowers-subagent-driven-development (recommended) or superpowers:superpowers-executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish one receipt-only server contract that independently validates the abnormal feasibility run without producing a new target outcome, while reducing the server dialogue to one Chinese status line.

**Architecture:** Preserve the executed feasibility instruction as a Git-canonical archive, replace the active instruction with a read-only receipt contract, synchronize the C-side recovery state, then publish the transition atomically. The receipt reads the existing runtime and sealed sources without overwriting them, writes evidence only to a new runtime/code/report scope, and distinguishes scientific findings from execution health.

**Tech Stack:** Markdown evidence contracts, JSON recovery state, Python validator requirements, PowerShell/Git verification, HTTPS publication.

---

## File map

- Create: `dis/sug/orientbench-c-topjournal-feasibility-20260809-executed.md` — canonical archive of the executed instruction.
- Replace: `dis/sug.md` — active receipt-only server contract.
- Modify: `dis/C.md` — post-feasibility abnormal execution adjudication.
- Modify: `dis/review_state.json` — machine recovery state and receipt authorization.
- Modify: `dis/collaboration_protocol.md` — generic one-status-line server dialogue policy.
- Modify: `dis/B_START_PROMPT.md` — keep CC closed and point ownership to the receipt.
- Modify: `dis/topjournal_feasibility_receipt_design_20260809.md` — record written approval.
- Create: `dis/topjournal_feasibility_receipt_dispatch_plan_20260809.md` — this plan.
- Preserve exactly: `dis/B.md`.

The eight C-owned paths are one atomic transition. The future server report is not created by C.

### Task 1: Preserve the executed round and approval

**Files:**
- Create: `dis/sug/orientbench-c-topjournal-feasibility-20260809-executed.md`
- Modify: `dis/topjournal_feasibility_receipt_design_20260809.md`

- [ ] **Step 1: Verify the clean base**

Run from the repository root:

```powershell
$head = (git rev-parse HEAD).Trim()
$remote = ((git ls-remote https://github.com/ziyu24/orientbench.git refs/heads/main) -split [char]9)[0]
if ($head -ne 'bc27506f7d7c0e47c4d67b202b9157bd4016a87a') { throw 'HEAD mismatch' }
if ($remote -ne $head) { throw 'HTTPS main mismatch' }
if (git status --porcelain=v1) { throw 'Dirty worktree' }
if ((git rev-parse 'HEAD:dis/B.md').Trim() -ne 'c0c2571f3a5c828673b39e6458ceaed5f14c5a6a') { throw 'B mismatch' }
```

Expected: no exception.

- [ ] **Step 2: Record canonical archive identity**

```powershell
$oldSugBlob = (git rev-parse 'HEAD:dis/sug.md').Trim()
$oldSugRaw = Get-FileHash -Algorithm SHA256 -LiteralPath 'dis/sug.md'
"$oldSugBlob $($oldSugRaw.Hash.ToLowerInvariant())"
```

Expected: one 40-hex canonical blob and one raw SHA256.

- [ ] **Step 3: Archive with `apply_patch` and verify**

Move the complete current `dis/sug.md` to `dis/sug/orientbench-c-topjournal-feasibility-20260809-executed.md`. Working-tree newline normalization is allowed only when this filter-aware identity check passes:

```powershell
$archiveBlob = (git hash-object --filters --path='dis/sug.md' 'dis/sug/orientbench-c-topjournal-feasibility-20260809-executed.md').Trim()
if ($archiveBlob -ne $oldSugBlob) { throw 'Archive mismatch' }
```

Expected: no exception.

- [ ] **Step 4: Freeze approval metadata**

The design header must contain exactly:

```yaml
document_status: APPROVED_WRITTEN_SPEC
user_conceptual_approval: true
user_written_spec_approval: true
server_execution_authorized: true
```

Do not change the scientific design sections.

### Task 2: Write the receipt-only active instruction

**Files:**
- Create: `dis/sug.md`
- Future server write scope only:
  - `top_journal_v3_reaudit_055/feasibility_receipt_20260809/**`
  - `outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt_20260809/**`
  - `dis/server_reports/orientbench-c-topjournal-feasibility-receipt-20260809.md`
  - `claude_code_and_supervisor.md` append-only

- [ ] **Step 1: Add exact identity and prohibition fields**

```yaml
round_id: orientbench-c-topjournal-feasibility-receipt-20260809
control_base: bc27506f7d7c0e47c4d67b202b9157bd4016a87a
source_execution_commit: cdf764c5a974030739a9992079bedb8b970fb2a7
scientific_data_cutoff: a9067fb16d2bbd747dfe69789ac33a5911eb15fe
source_runtime: outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809
runtime_root: outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt_20260809
server_report_path: dis/server_reports/orientbench-c-topjournal-feasibility-receipt-20260809.md
status: READY_FOR_SERVER_EXECUTION
gpu_authorized: false
download_authorized: false
training_authorized: false
inference_authorized: false
new_target_outcome_authorized: false
manuscript_edit_authorized: false
cc_recommendation: no
```

State that the source run is permanently `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`; this receipt never rewrites it as normal. Source runtime and scientific assets are read-only and must not be deleted, overwritten, renamed, patched, or backfilled.

- [ ] **Step 2: Freeze preflight and error handling**

Require HTTPS `pull --ff-only`, exact branch/upstream/HEAD/remote/clean-tree/B checks, source runtime presence, new runtime absence, and complete rule/readme hashes. Any failure produces a tracked abnormal report when safely possible; no source runtime cleanup or alternate path is allowed.

Old missing event fields must be recorded as `SOURCE_FIELD_ABSENT`; mtime, constants, reconstructed guesses, and hard-coded pass booleans are forbidden substitutes.

- [ ] **Step 3: Freeze Track M receipt**

Require the server to:

1. compare A–F source bytes/SHA/schema/row keys/cluster sets against pre-existing r014/m069 sealed manifests, not a receipt-generated inventory;
2. recompute risk, fixed scores, AUGRC, AURC/NRC, Risk@70/90 and unit-equal aggregates from raw sealed rows;
3. dynamically verify the pinned `fd-shifts@c4467aec134e99691359da209f811d91283fc1e3` reference identity and behavior;
4. replay replicate `0..9999` from the fixed seed and complete cluster universes, comparing every replicate field, CI and status;
5. implement and test all five mutually exclusive Track M states, including `INSUFFICIENT_ASSETS` and `SENSITIVITY_UNSTABLE`.

Missing source assets are an honest receipt finding, never invented or inferred from summaries.

- [ ] **Step 4: Freeze Track D receipt**

Independently rebuild official-source and candidate facts from stored body/header/meta evidence. Search tracked and ignored persistent artifacts explicitly, plus manifests/reports, `pth_data/readme.md` and dataset filename/stat-only views. Do not open candidate annotations.

The validator must derive license, angle, presence, common-family and contamination states from evidence. It must not consume generator booleans as truth. Asset absence must come from real stat/hash evidence.

- [ ] **Step 5: Freeze the complete joint gate**

The validator must implement every clause:

```text
PASS_TO_METHOD_DESIGN requires ROBUST_CANDIDATE, two independent eligible remote-sensing datasets, the same >=3-family set, >=1 family absent from old Core, and no target-label tuning.
FAIL_TO_MEASUREMENT_ONLY applies when any prespecified negative condition is proved.
INCONCLUSIVE_FEASIBILITY applies only when Track M is INSUFFICIENT_ASSETS and Track D has not independently proved FAIL.
```

Require true negative tests for every omitted-clause risk: mutate a source hash, one bootstrap replicate, one Track D evidence fact and one joint-gate clause; each isolated validator run must exit nonzero.

- [ ] **Step 6: Freeze report and one-line dialogue**

All evidence and errors go to the unique tracked report. The final dialogue contains exactly one wrapper and one status phrase, with no path, SHA, explanation or list:

```text
👇👇👇👇👇👇

正常执行完毕

👆👆👆👆👆👆
```

or:

```text
👇👇👇👇👇👇

异常结束

👆👆👆👆👆👆
```

`正常执行完毕` requires every receipt phase, validator, mutations, one commit, HTTPS push and external receipt. A negative scientific finding may still be normal. Any omitted mandatory work, unavailable runtime, invalid validator, provenance gap or failed Git publication is `异常结束`.

### Task 3: Synchronize C-side recovery state

**Files:**
- Modify: `dis/C.md`
- Modify: `dis/review_state.json`
- Modify: `dis/collaboration_protocol.md`
- Modify: `dis/B_START_PROMPT.md`

- [ ] **Step 1: Update `C.md`**

Bind the source execution commit, six authorized server paths, abnormal completion verdict, decisive validator/Track D/joint-gate defects, and the rule that all source-run metrics are `DESCRIPTIVE_UNVERIFIED`. Preserve the conservative measurement-only route; do not claim the source run proved a formal scientific fail.

Set the sole next action to the receipt-only validation. Keep CC closed and prohibit new experiment, r020, gate substitution, DOTA/HRSC/Core rescue and manuscript editing during the receipt.

- [ ] **Step 2: Update `review_state.json`**

Use schema version `1.6` and exact machine states:

```json
{
  "feasibility_source_execution": "ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809",
  "feasibility_source_numbers": "DESCRIPTIVE_UNVERIFIED",
  "feasibility_reported_gate": "FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED",
  "current_route": "ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC",
  "server_status": "READY_FOR_SERVER_FEASIBILITY_RECEIPT",
  "server_dialogue_mode": "CHINESE_STATUS_ONLY_NORMAL_OR_ABNORMAL"
}
```

Point to the new instruction/report/runtime and set every GPU/download/training/inference/new-outcome/manuscript authorization to false. Do not claim the receipt has started.

- [ ] **Step 3: Update protocol and B handoff**

The protocol must preserve the same state, hashes, ownership, receipt-only scope and one-line Chinese status policy. `B_START_PROMPT.md` keeps the old CC round completed, sets `next_owner: C / server feasibility receipt`, and explicitly does not invite new CC work.

### Task 4: Validate the atomic transition

**Files:** Test all eight C-owned paths; preserve `dis/B.md`.

- [ ] **Step 1: Parse and scan**

Parse `review_state.json`, the C/design YAML headers and all Markdown fences. Search changed text for unresolved placeholders, stale active feasibility round, verbose server-dialogue fields, and prohibited runtime authorization values (`gpu_authorized|download_authorized|training_authorized|inference_authorized|new_target_outcome_authorized|manuscript_edit_authorized: true`). The approved design field `server_execution_authorized: true` is required and must not be treated as a failure.

- [ ] **Step 2: Verify path and ownership scope**

```powershell
$allowed = @(
  'dis/B_START_PROMPT.md',
  'dis/C.md',
  'dis/collaboration_protocol.md',
  'dis/review_state.json',
  'dis/sug.md',
  'dis/sug/orientbench-c-topjournal-feasibility-20260809-executed.md',
  'dis/topjournal_feasibility_receipt_design_20260809.md',
  'dis/topjournal_feasibility_receipt_dispatch_plan_20260809.md'
) | Sort-Object
$changed = @(git status --short | ForEach-Object { $_.Substring(3).Replace('\','/') } | Sort-Object)
if (Compare-Object $allowed $changed) { throw 'Scope mismatch' }
if (git diff -- 'dis/B.md') { throw 'B changed' }
if ((git rev-parse 'HEAD:dis/B.md').Trim() -ne 'c0c2571f3a5c828673b39e6458ceaed5f14c5a6a') { throw 'B mismatch' }
git -c core.safecrlf=false diff --check
```

Expected: exact eight-path scope, no B diff, exit 0 and no whitespace output.

- [ ] **Step 3: Verify archive and future paths**

Require archive canonical blob equality with `HEAD:dis/sug.md`, exactly one active receipt report/runtime value, existing source report/runtime references, and absence of the future receipt report in the C worktree.

### Task 5: Commit and publish

**Files:** Stage exactly the eight paths listed in Task 4.

- [ ] **Step 1: Stage explicitly and verify**

```powershell
git add -- dis/B_START_PROMPT.md dis/C.md dis/collaboration_protocol.md dis/review_state.json dis/sug.md dis/sug/orientbench-c-topjournal-feasibility-20260809-executed.md dis/topjournal_feasibility_receipt_design_20260809.md dis/topjournal_feasibility_receipt_dispatch_plan_20260809.md
git diff --cached --name-status
git diff --cached --check
```

Expected: exactly eight paths and no cached whitespace error.

- [ ] **Step 2: Commit**

```powershell
git commit -m "任务：下发顶刊可行性纠偏验收"
```

Expected: one atomic C-side commit.

- [ ] **Step 3: Push and verify**

```powershell
git push https://github.com/ziyu24/orientbench.git HEAD:main
$head = (git rev-parse HEAD).Trim()
$remote = ((git ls-remote https://github.com/ziyu24/orientbench.git refs/heads/main) -split [char]9)[0]
if ($head -ne $remote) { throw 'Push mismatch' }
if (git status --porcelain=v1) { throw 'Dirty worktree' }
```

Expected: local HEAD equals HTTPS main and worktree/index are clean.

### Task 6: Server handoff

- [ ] **Step 1: Provide the server pull target**

Tell the server to HTTPS fast-forward to the final dispatch commit and execute `dis/sug.md`. Do not run the receipt locally or create its future report.

- [ ] **Step 2: Wait for one Chinese status line**

The server dialogue must contain only the wrapper plus `正常执行完毕` or `异常结束`. C reads the repository report afterward; the user is not asked to parse evidence fields from chat.
