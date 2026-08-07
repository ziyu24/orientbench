# orientbench-c r010 server report

- Server time: 2026-08-07 01:10 CST
- Source: `dis/sug.md` (r010), scientific snapshot `73f8814b9d0345bfb6b99c1463a61bb01a555f40`
- Repository state pulled first: `248292f`

## Execution result

The independent r010 evaluator completed four Core-6 units: `DIOR-R/22`,
`DIOR-R/3`, `DIOR-R/61`, and `FAIR1M-v1.0/24`.  The two SODA-A Core units
(`SODA-A/23`, `SODA-A/4`) were started with the frozen full evaluator but did
not produce a result within this run and were stopped before any row was
accepted.  They remain explicit `NOT_RUN_EVALUATOR_R010` quarantine rows.

The paired AP bootstrap was not run because the Core-6 evaluator was
incomplete.  No bootstrap estimate, AP75 knee, causal claim, or deployable
selector claim is inferred from the four completed units.  Extension units
were not run because the Core gate was not satisfied.

## Gate

`FAIL_EVALUATOR_R010`

The r010 evidence package is therefore not scientifically closed.  The
historical r009 package is retained unchanged; r010 does not overwrite its
reports.  No training, detector inference, download, threshold change, split
change, or D_cal/D_audit change was performed.

## Key outputs

- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_mechanism_gate_r010.json`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_evidence_manifest_r010.json`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/a4_statistical_mechanism_r010.md`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v080.md` (quarantined wording only)
