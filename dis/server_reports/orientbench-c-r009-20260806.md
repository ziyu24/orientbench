# OrientBench r009 evidence closure

- execution_head: `e6f028f9d50c4ccf67a4a31bfa1b441bc1d2b6a5`
- Core-6 inventory: 6 units; persistent raw located for all six.
- Provenance gate: `INCONCLUSIVE_PROVENANCE_R009`. FAIR1M-v1.0 GT was repaired from the persistent val_20 GT index (3,896 images / 78,638 objects), and the full FAIR1M/24 schema prediction is present. The Core is still blocked because DIOR-R/61 has only a 600-image raw subset and SODA-A/4 has only a 408-image raw subset; neither has a persistent complete full-validation prediction dump. No matched-only substitute was used.
- Evaluator golden cases: PASS; no scientific dose track, bootstrap, training or inference was run.
- Mechanism gate: `NOT_RUN_PROVENANCE`; extension not reached.
- v079: generated from v078 with historical certification headline quarantine; no new scientific numbers.
- operation counts: detector training=0, detector inference=0 (the attempted SODA-A/4 rerun stopped before inference because the local SODA-A image tree is absent), score-regressor=0, evaluator=0, bootstrap=0, GPU=0, download=0.

Continuation audit (2026-08-06): FAIR1M raw data and annotations were verified at the server dataset path and the frozen GT was repaired. Persistent full schemas close DIOR-R/22, DIOR-R/3, FAIR1M-v1.0/24 and SODA-A/23. DIOR-R/61 and SODA-A/4 remain provenance-incomplete; r009 therefore remains stopped before scientific dose evaluation.
