# M1: ar>=2.1 protocol unification

- The only main-table mask is `ar>=2.1`; `ar>=1.6` and `ar>=1.3` are sensitivity only.
- The evaluation mask uses matched-GT aspect ratio; selector geometry uses prediction-box w/h only. `near_square` excludes instability in either matched box.
- A-F use lineage-clean full-validation dumps. Phase and TTA fields come from the same forward and stable detection match, not a local `pred_id` join.
- Every score row records mask, threshold, retained count, retained ratio, source lineage, and metric completeness.
- K2 training and its evaluator matrix are not rerun. Complete PSC phase-modulus metrics use the persisted Phase-1 matched base; complete DCL/CSL native metrics use the preregistered targeted identity-only frozen-checkpoint endpoint dumps (no AP evaluation).
- All K2 endpoint masks are recomputed under the unified matched-GT aspect-ratio definition and exclude near-square prediction or GT geometry; old prediction-AR K2 summary masks are superseded for M1.
- Image-level LTT is authoritative in `m3_image_level_ltt.csv`; GT-noise proxy remains separately authoritative in `k3_gt_angle_noise_by_dataset.csv` and is not called human noise.
- DOTA clean cells remain the two K4b full-val cells; DOTA#20 is excluded.
- NRC direction changes from ar1.6 to ar2.1: 6. New ar2.1 values supersede the old narrative.
- **M1 decision: PASS.**

## NRC direction changes
| cell | score | ar1.6 | ar2.1 | old | new |
|---|---|---:|---:|---|---|
| K2:K2_final__CSL__DIOR-R__seed2 | score_CSL | 1.0004 | 1.0856 | near-random | reversed |
| K2:K2_final__CSL__SODA-A__seed0 | native_CSL | 1.0778 | 1.0046 | reversed | near-random |
| K2:K2_final__CSL__SODA-A__seed2 | score_CSL | 1.0627 | 0.9564 | reversed | non-reversed |
| K2:K2_final__DCL__SODA-A__seed0 | score_DCL | 0.9949 | 0.8892 | near-random | non-reversed |
| K2:K2_final__DCL__SODA-A__seed1 | score_DCL | 0.9844 | 0.8945 | near-random | non-reversed |
| K2:K2_final__DCL__SODA-A__seed2 | score_DCL | 0.9925 | 0.89 | near-random | non-reversed |
