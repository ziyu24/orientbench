# r037 Q-SetOD Corrective Adjudication

## Registered outcome

- `G_EVIDENCE=PASS` with 4/8 witnesses: B, A, E, F.
- `G_SET=FAIL` with 0/8 set witnesses.
- All 16 overall lower-tail validity checks: `True`; all supported-bucket and efficiency hard checks: `False`.
- Multimodality: `MULTIMODALITY_NOT_ADJUDICATED` because exact `diptest` is unavailable; no approximation was substituted.
- Final candidate: `QSETOD_EVIDENCE_SCORE_ONLY`.

## Interpretation

TTA evidence remains predictive after confidence, but source-only interval transport fails the registered hard gate; retain scalar evidence-quality only, delete set/coverage and multi-arc claims, do not authorize training or venue upgrade.

## Audit closure

- A/B predictions, support, multiplicities, 20,000 replicates, T2/T3 tables and judgment agree at `atol=1e-10, rtol=0`.
- The self-contained validator independently refit 108 estimators, regenerated multiplicities and all registered metrics; 33,575,312 fields matched with maximum absolute difference 0.
- Eight real temporary-copy mutations were all rejected by the same validator.
- Target-label rows in fit: 0. Clean endpoint access: 0. GPU/training/inference/download: 0.
