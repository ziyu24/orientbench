# OrientBench C 侧 r008 主稿 claim 隔离与证据对账

- round: `orientbench-c-r008-20260806`
- execution_head: `ed99b0dfc748b7937a71406b33b752bef1626592`
- source manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`
- output manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v078.md`
- claim ledger: 215 rows; source-to-ledger and target-to-ledger coverage: 100% / 100%
- v077/v078 SHA-256: identical (`96a8956958c99ab18657cbba6a893b88e009997e23d78f88262d38b9b089982d`)
- forbidden positive phrase scan: none
- numeric, dataset, and method/entity sets: unchanged
- operation counts: training=0; detector inference=0; score-regressor fit/predict=0; GPU=0; download=0; external data access=0
- hygiene_gate: `PASS_CLAIM_QUARANTINE_R008`
- measurement_core_status: `SUFFICIENT_FOR_MEASUREMENT_REVISION`
- interpretation: v077 was already conservative and measurement-only; v078 is a byte-identical audited carry-forward with claim-level evidence ledger. No new scientific number or claim was added.
- authorized writes only: root record, this report, v078, r008 ledger, gate JSON, validator, and final manifest.
