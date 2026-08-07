# orientbench-c r010 server report

- Server time: 2026-08-07 17:43 CST
- Source: `dis/sug.md` (r010), scientific snapshot `73f8814b9d0345bfb6b99c1463a61bb01a555f40`
- Repository state pulled first: `248292f`

## Execution result

The independent r010 evaluator completed all six Core-6 units: `DIOR-R/22`,
`DIOR-R/3`, `DIOR-R/61`, `FAIR1M-v1.0/24`, `SODA-A/23`, and `SODA-A/4`.
The paired image-cluster AP bootstrap completed 1000 replicates per unit.
Baseline-cohort survival and fixed-dose risk-event tables were regenerated
from all six persisted unit payloads. Extension units were not run because
they are ambiguous under the frozen provenance rule.

## Gate

`INCONCLUSIVE_MECHANISM_R010`

The r010 evaluator/statistical package is complete, but the mechanism gate is
inconclusive because the frozen D/S bootstrap support criterion is not met in
enough units. No strong unified mechanism, causal, or deployable-selector
claim is allowed. The historical r009 package is retained unchanged; r010
does not overwrite its reports. No training, detector inference, download,
threshold change, split change, or D_cal/D_audit change was performed.

## Key outputs

- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_mechanism_gate_r010.json`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_evidence_manifest_r010.json`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/a4_statistical_mechanism_r010.md`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v080.md` (quarantined wording only)
