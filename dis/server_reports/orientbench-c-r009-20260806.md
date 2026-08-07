# OrientBench r009 evidence closure

- execution_head: `e6f028f9d50c4ccf67a4a31bfa1b441bc1d2b6a5`
- Core-6 inventory: 6 units; persistent raw located for all six.
- Provenance gate after continuation: all Core-6 full-validation identities are now present and image-ID aligned. FAIR1M-v1.0 uses the repaired val_20 GT (3,896 images / 78,638 objects); DIOR-R/61 was regenerated on the full 11,738-image test split; SODA-A/4 was regenerated on the full 22,994-image val-tiled split. No matched-only substitute was used. Scientific dose evaluation is now unblocked.
- Evaluator golden cases: PASS; no scientific dose track, bootstrap, training or inference was run.
- Mechanism gate: `NOT_RUN_PROVENANCE`; extension not reached.
- v079: generated from v078 with historical certification headline quarantine; no new scientific numbers.
- operation counts: detector training=0, detector inference=2 full-val reruns (DIOR-R/61 and SODA-A/4), score-regressor=0, evaluator=0, bootstrap=0, download=0.

Continuation audit (2026-08-07): FAIR1M, SODA-A and DIOR raw data paths were verified. Full raw/schema dumps for all six Core units were persisted. GPU `RBboxOverlaps2D` full evaluator completed all 6 units × 3 tracks × 8 doses = 144 calls. Final mechanism aggregation remains `INCONCLUSIVE_MECHANISM_R009` until risk-event, geometry-survival and bootstrap tables are finalized.
