# Numeric SERVER instructions

Formal SERVER instructions use monotonically increasing `rNNN` directories: `r001`, `r002`, `r003`, and so on. A reserved number is never reused.

SERVER first freezes a self-contained
`coordination/executions/<instruction-id>/ABNORMAL-<attempt>.yaml`, including the
terminal journal plus command-log, result, and acceptance checkpoint bindings;
only then does the journal enter its abnormal terminal review gate. The bundle
is pushed on `exec/<instruction-id>` and can be idempotently retried with
`execution publish-abnormal`. An independent B/C worktree fetches and
materializes that exact bundle. Receipts are append-only under
`<instruction-id>/reviews/` and bind it. An ordinary
`CORRECT_PREVIOUS_EXECUTION` plan must bind an `ISSUE_NEXT_R_CORRECTION` receipt
by path and SHA256; a project-persisted recoverable transaction consumes the
receipt exactly once by the next `rNNN`, and
abnormal terminal work never recovers under the old number. Corrected completion
remains pending until B or C binds the exact `RESULT.yaml` and acceptance
checkpoint in a `VERIFIED_CORRECT` receipt.
