# TTA circular variance full table 052

Generated: 2026-07-02 22:09:39 CST

Circular variance is computed on doubled angles, theta -> 2theta, as required for pi-periodic OBB angles. No naive linear standard deviation is used. Rows are full available post-NMS identity anchors, not capped. When a cell lacked identity.pkl but had hflip/vflip plus a full real schema, the schema was used as the identity anchor and this is recorded in identity_source.

- DIOR-R/3: complete_full_real_circular, rows=60881, matched_gt=32161, identity=outputs/persistent_artifacts/orientbench_v2_047/tta_preds/DIOR-R_3/identity.pkl
- DIOR-R/22: complete_full_real_circular, rows=212448, matched_gt=29994, identity=outputs/persistent_artifacts/orientbench_v2_047/tta_preds/DIOR-R_22/identity.pkl
- DIOR-R/61: complete_full_real_circular, rows=131067, matched_gt=32149, identity=outputs/persistent_artifacts/orientbench_v2_047/tta_preds/DIOR-R_61/identity.pkl
- FAIR1M-v1.0/5: complete_full_real_circular, rows=188153, matched_gt=62316, identity=outputs/persistent_artifacts/orientbench_v2_047/tta_preds/FAIR1M-v1.0_5/identity.pkl
- FAIR1M-v1.0/24: complete_full_real_circular, rows=484332, matched_gt=54768, identity=outputs/persistent_artifacts/orientbench_v2_047/tta_preds/FAIR1M-v1.0_24/identity.pkl
- SODA-A/4: complete_full_real_circular, rows=676208, matched_gt=376756, identity=full_schema_anchor_identity_missing
- SODA-A/23: complete_full_real_circular, rows=1663631, matched_gt=309218, identity=outputs/persistent_artifacts/orientbench_v2_047/tta_preds/SODA-A_23/identity.pkl

Output: `top_journal_v3/reports/tta_circular_variance_full_052.csv`
