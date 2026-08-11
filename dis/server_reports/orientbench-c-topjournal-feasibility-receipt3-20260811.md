# OrientBench top-journal feasibility receipt3 server report

## Identity and migration

- round_id: `orientbench-c-topjournal-feasibility-receipt3-20260811`
- retry_of: `orientbench-c-topjournal-feasibility-receipt2-20260810`
- dispatch_base: `35358b5fef838b178aff0e16470ebe0117cab687`
- post_pull_head: `6e0ea32bc3d1c13aa051f8abd9c9e37e5996d025`
- project migration: the project is now executed on the migrated current server; the existing `pcp-obb` conda environment was reused and the migration fact was appended to `claude_code_and_supervisor.md` for the supervisor.
- tracked_report_source: `FROZEN_SNAPSHOT`
- tracked_report_self_validation: `EXTERNAL_GIT_BLOB_ONLY`
- final_commit_sha: `POST_COMMIT_EXTERNAL_RECEIPT`
- git_publish_status: `PENDING_EXTERNAL_RECEIPT`
- receipt_execution: `PENDING_EXTERNAL_RECEIPT`

The source execution remains `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`; every source number remains `DESCRIPTIVE_UNVERIFIED`. Receipt1 remains `ABNORMAL_PREFLIGHT_FAILURE`, `scientific_gate: NOT_ADJUDICATED`, `non_reusable: true`, Track M/D not run; its report/archive blobs remain `4fe331a6a683313150a4fb21cbabd432ffde0f6b` / `11553a92b05b692a14bf9c4f21898a5c9e10d144`. Receipt2 remains `ABNORMAL_MANDATORY_REFERENCE_PROVENANCE_FAILURE`, `scientific_gate: NOT_ADJUDICATED`, `non_reusable: true`, Track M=`NOT_EMITTED_NOT_RUN`, Track D not run; publication commit/report/archive identities remain `a2da27559dc6eb005f02efb9b3b34584ebed57b8` / `8e1407d90f5a7247816c457eddcb60a704291951` / `25ee36ec83db92364134a66bb44b349ac5f34cf9`.

## Pre-seal closure

Preflight passed: the initial pull fast-forwarded `35358b5fef838b178aff0e16470ebe0117cab687 -> 6e0ea32bc3d1c13aa051f8abd9c9e37e5996d025`, the formal HTTPS pull was already up to date, local/upstream/remote were equal, the tree was initially clean, protected `dis/B.md` remained unread with blob `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a` and zero staged/unstaged diff, fixed ancestry and prior receipt blobs passed, and the 74-file read-only source runtime closed at canonical aggregate `2e9f7eb60b7de427b24faa8c91b0ef2017864d99cbc923b04bfe70b500085b43`.

The exact fd-shifts remote was fetched once in attempt-01 and verified at detached clean commit `c4467aec134e99691359da209f811d91283fc1e3`; attempts 02/03 were omitted because the contract required stopping after the first verified attempt. Required blobs were `563be2ed8652c730dd940eb241d8642717e25c0d` (`rc_stats.py`) and `9f99c499f370b587d0ca73e2d9679a358de55e05` (`rc_stats_utils.py`). Normal isolated import failed only on absent `loguru`; the permitted AST adapter used verbatim source spans, dynamically read `AUC_DISPLAY_SCALE=1000`, and matched tie/binary/continuous/boundary curves and unscaled AUGRC at `atol=1e-12, rtol=0`.

All mandatory scientific/audit phases are closed. Validator attempts 01-04 exposed and preserved receipt-field parsing/normalization diagnostics; no source, score, risk, cohort, bootstrap, state, or gate definition changed. Attempt-05 completed the full independent audit. The earlier outer `run_logged` argument rejection did not start a scientific/audit subprocess and produced no runtime object; it is not represented as an executed audit command. No unresolved execution failure or technical stop remains at the pre-seal cutoff.

## Track M

- unique state: `METRIC_REVERSAL`
- complete A-F cohort: true; nonfinite count: 0; row drop: `NO_ROW_DROP_ALLOWED`
- point metric rows: 54; complete generalized risk-coverage rows: 3,313,581
- bootstrap: 10,000/10,000 synchronized cluster replicates, seed 20260809, 39 workers; every saved source delta matched at `atol=1e-12`; CI is report-only.
- state fixtures: all five and only five production branches passed.
- reversal witnesses: `[{"AUGRC": -0.00046159958856810054, "AURC": -0.003022989169882938, "NRC": -0.07210382629941592, "Risk@70": -0.0004541908190616589, "Risk@90": 0.0003300876416621121, "baseline": "tta_angle", "dataset": "DIOR-R"}, {"AUGRC": 4.89448802044011e-05, "AURC": -9.592373804065413e-05, "NRC": -0.0015125611685036233, "Risk@70": 2.9995834927062925e-05, "Risk@90": 0.0006447632942506026, "baseline": "tta_angle", "dataset": "SODA-A"}]`
- learned EQS never drove the state.

## Track D

- `AI-TOD-R`: `LICENSE_BLOCKED` — no closed dataset license, no unique conversion contract, and required local assets absent.
- `UAV-OBB`: `INCOMPATIBLE_ANGLE_CONTRACT` — CC BY 4.0 is closed, but stored center-angle/four-vertex descriptions do not uniquely fix clockwise/long-side/near-square/ignore conversion; required local assets are also absent.
- `ShipRSImageNet`: `LICENSE_BLOCKED` — README academic-only text conflicts with LICENSE 404 and API license null; conversion and assets are also unclosed.
- `ICDAR-MLT`: `CONTAMINATED` — 32 exact prior project outcome/endpoint hits were derived from registered baseline evidence; it is auxiliary-only, with all lower-precedence facts retained.
- eligible independent remote-sensing candidates: 0; common detector-family set: empty; new family: false; target-label tuning would be required.

## Joint gate

- `all_required_angle_contracts_closed`: `false`
- `all_required_license_contracts_closed`: `false`
- `common_at_least_three_detector_families`: `false`
- `fewer_than_two_independent_remote_eligible`: `true`
- `future_target_label_tuning_required`: `true`
- `new_family_not_in_old_core_present`: `false`
- `track_m_negative_state`: `true`

Negative precedence therefore yields the unique joint gate `FAIL_TO_MEASUREMENT_ONLY`. This is a scientific negative receipt, not permission to change the frozen rules or start method design.

## Independent validator and mutations

Implementation B imported neither the generator nor sealed metric implementation A. It independently rebuilt raw risk/scores, verified all source identities and complete row/cluster sets, streamed every saved curve row, replayed every bootstrap replicate, reran pinned-reference vectors, derived Track D facts, and derived the gate. Final validator status: `PASS`.

- `source_hash`: exit `2`, target `source_hash`, rejected=`True`, witness `row=0 field=sha256 d5ae254713e501695b914b3c15ced0c686a8ed01deec0599b62ff0584fd74ca3 -> 0000000000000000000000000000000000000000000000000000000000000000`.
- `bootstrap_replicate`: exit `2`, target `bootstrap_replicate`, rejected=`True`, witness `replicate=0 field=actual__DIOR-R__S0_minus_raw_confidence -0.0013670747469397432 -> 0.09863292525306026`.
- `track_d_evidence_fact`: exit `2`, target `track_d_evidence_fact`, rejected=`True`, witness `candidate=AI-TOD-R official_license_evidence_count 0 -> 1`.
- `joint_gate_clause`: exit `2`, target `joint_gate_clause`, rejected=`True`, witness `clause=new_family_not_in_old_core_present False -> True`.

All mutation copies and raw logs remain preserved under `runtime_root/mutations/**`.

## Governance, scope, and pending publication

- actual pre-seal Git status before report materialization:

```text
 M claude_code_and_supervisor.md
?? top_journal_v3_reaudit_055/feasibility_receipt3_20260811/finalize_receipt.py
?? top_journal_v3_reaudit_055/feasibility_receipt3_20260811/generate_receipt.py
?? top_journal_v3_reaudit_055/feasibility_receipt3_20260811/reference_adapter_probe.py
?? top_journal_v3_reaudit_055/feasibility_receipt3_20260811/reference_full_import_probe.py
?? top_journal_v3_reaudit_055/feasibility_receipt3_20260811/run_logged.py
?? top_journal_v3_reaudit_055/feasibility_receipt3_20260811/run_mutations.py
?? top_journal_v3_reaudit_055/feasibility_receipt3_20260811/validate_receipt.py
```

- planned tracked commit scope: `top_journal_v3_reaudit_055/feasibility_receipt3_20260811/**` (source entry points only; ignored cache files excluded), this report, and the append-only `claude_code_and_supervisor.md` update.
- runtime_root is an ignored persistent artifact, consistent with prior feasibility runtime handling; it is not claimed to be a remote Git blob. Its local frozen manifest is `412855` bytes, SHA256 `f18992fb07ec1b062149267ea51a987c699322a2a461215f436c824cf7896e0c` and will be checked against this declaration by the external receipt.
- manifest self bytes/SHA are `N/A_SELF_REFERENCE`; report self-validation is external Git-blob-only; post-seal events are external-receipt-only.
- protected B blob was unchanged at the pre-seal check. Final add/staged checks/commit/push/remote/published-blob checks have not yet occurred and are not claimed here.
- allowed path boundaries were respected. The only network exception was the exact pinned fd-shifts fetch. General download, GPU, installation, training, forward, inference, new target outcome, annotation content, manuscript edit, frozen threshold/split/formal-label changes did not occur.
- `SOURCE_FIELD_ABSENT`: source bootstrap cluster-multiplicity hashes were absent and were deterministically reconstructed from the pinned seed/protocol; the source worker fields were retained only as telemetry. Unknown or conflicting Track D terms were kept fail-closed.
- `PROPOSED_DEVIATION`: none.
- sug_genuinely_exhausted: `true`

The only remaining work is post-seal Git publication and the external receipt. Until that completes, this report intentionally remains `PENDING_EXTERNAL_RECEIPT`.
