# B post-execution verdict — r048

- Dispatch: `orientbench-b-r048-p2c-lift-directed-obb-stagea-20260819`
- Accepted server HEAD: `d4acafb7826fd041a359081d35b433b1c7ed0c8f`
- Verdict: **`ACCEPT_EXECUTION / ADOPT_REJECT_P2C_LIFT_DEVELOPMENT / STOP_P2C_ROUTE / DO_NOT_OPEN_T_CAL_OR_T_AUDIT`**

## Decision evidence

The final clean rerun fixes the prior decisive defect. `pole_logit` now has one meaning—positive is `q(sheet=1)`—in the BCE proper loss, full S1 likelihood, circular decoder and intrinsic confidence. Deterministic tests cover the two sheets, an explicit 180-degree mutation, and H/V/R90/R180/R270 pull-backs and rendered labels. P2C and all four baselines start clean from the registered R50 mapping and consume the declared transform family; all traces report four-rank execution.

The frozen first-epoch early-stop condition holds even under the strict contemporaneous comparison, without relying on a 30-epoch baseline endpoint. CONCAT_ENDPOINT_BINARY reaches `0.656192` at epoch one, exceeding the required baseline premise `>=0.65`; P2C small/base/wide reach only `0.502773`, `0.506470`, and `0.499076`, each below `0.60`. Stopping all three P2C configurations after that epoch is therefore protocol-correct.

The delivered row-level val metrics independently reproduce the selected comparison:

| model | accuracy | mean circular error | AUGRC |
|---|---:|---:|---:|
| P2C base | 0.506470 | 87.741° | 0.423795 |
| whole-crop binary | 0.885397 | 21.336° | 0.024484 |

Thus P2C-minus-baseline accuracy is `-0.378928`, baseline-minus-P2C mean-error improvement is `-66.405°`, and baseline-minus-P2C AUGRC improvement is `-0.399311`. All three 5/10/15-degree jitter comparisons remain negative. The method misses every G1 superiority condition by a margin far beyond rounding or checkpoint tie-breaking.

The access log and delivered artifacts show no T_cal or T_audit semantic access. G2–G5 correctly remain unopened. The server's final `REJECT_P2C_LIFT_DEVELOPMENT` token is adopted, and no further P2C tuning, T_cal confirmation, T_audit evaluation or external Stage B is permitted.

## Qualification and venue decision

The manifest hashes server-resident checkpoints rather than delivering Git chunks, and the negative package does not include the planned FLOPs/latency table. These are reproducibility/packaging debts, so r048 should remain an internal route-kill result or appendix note, not a headline publication contribution. They cannot plausibly reverse the registered epoch-one survival failure and do not justify another P2C run.

The project remains at **strong JSTARS / Remote Sensing**, below the TGRS-or-better target. Repeated selector/head routes—Q-SetOD, OER/OER-D, SAUR, AHC and now P2C—have not produced a surviving method contribution. The next top-journal attempt must not be another HRSC crop-head rescue. It requires genuinely new scientific authority and evidence: preferably a detector-native probabilistic orientation/reliability objective plus an independent, source-disjoint application endpoint or newly collected direction/reliability labels. Large detector training or new data acquisition requires explicit user approval under the project boundary.
