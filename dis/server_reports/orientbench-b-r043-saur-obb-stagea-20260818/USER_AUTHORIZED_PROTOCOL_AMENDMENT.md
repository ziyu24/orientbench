# User-authorized protocol amendment — r043

## Authority and scope

At 2026-08-18 04:34 PDT, the user explicitly authorized: “dior-r做trainval/test，不要来回拉扯了，其它的也做相应更改。”

For this server execution only, that instruction supersedes the r043 DIOR-R data-boundary clauses that previously required train/val and prohibited every test label.

## Effective execution boundary

| Dataset | Training split | Evaluation split | Purpose |
|---|---|---|---|
| DIOR-R | trainval | test | PSC-host identity parity and all r043 BASE/CONT/SAUR evaluation |
| SODA-A | train | val | PSC-host identity parity and all r043 BASE/CONT/SAUR evaluation |

The change is limited to DIOR-R.  It does not authorize DOTA-v2.0, SODA-A official test, a new dataset, test-label-derived training features, threshold changes, or use of DIOR-R test labels for model selection.  DIOR-R test evaluation remains a fixed, final endpoint under the supplied PSC host protocol.

## Corresponding execution changes

- G0 DIOR-R parity is now the archived PSC `trainval -> test` parity, with the same checkpoint/config lineage.
- DIOR-R CONT and SAUR train on trainval and evaluate each recorded epoch on the fixed test endpoint; the final checkpoint is the predeclared primary result, and no test-driven hyperparameter/seed selection is permitted.
- All r043 reports, inventories, manifests, and gate language must distinguish DIOR-R `trainval -> test` from SODA-A `train -> val`.
- The prior `PROTOCOL_DRIFT_STOPPED` disposition is superseded for the explicit user-authorized DIOR-R endpoint only.  The earlier test evaluation is retained as G0 parity evidence, not as a Stage-A method result.
