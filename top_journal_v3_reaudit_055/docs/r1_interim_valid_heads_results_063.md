# R1 valid-heads results — restricted PSC-specific mechanism evidence (063 eval, 064 framing)

> **Preliminary mechanism evidence, NOT a proof.** All 18 valid runs (PSC/CSL/DCL × DIOR-R/SODA-A
> × 3 seeds) evaluated. The full **5-head** pre-registered matrix is **NOT complete**:
> `direct_regression_le90` (NaN) and `KLD` (AMP/fp16 `linalg.inv`) `failed_training` under the
> shared protocol (`r1_failed_training_audit_final_064.csv`). So the strongest allowed reading is a
> **restricted A-like, PSC-specific result**, not full pre-registered outcome A. NRC<1 = informative
> / non-reversed (never "calibrated"); NRC>1 = reverse-ranked; NRC≈1 = ~random.

## Method (validated)
Instrumented AngleBranch head captures each kept detection's native uncertainty aligned through NMS
(validated: decode(angle_encoded) vs box θ bimodal {0°,90°}=edge_swap). Match to the same
gt_instances the evaluator uses (rotated IoU, greedy by score). Canonical long-side angle-error,
masked ar≥1.6. Frozen `nrc_auc` (oracle 0 / random 1 / reverse 2) + image-clustered bootstrap CI.
AP validation: self rotated-AP50 vs val-log AP50 **max|diff|=0.0005** over 18 runs → AP75 trustworthy.

## Block-level 3-seed results (masked ar≥1.6) — `reports/r1_valid_head_blocks_final_064.csv`
| block | native signal | mean angle err | NRC_native (min–max) | native CI_lo(min) | all 3 seeds NRC>1 | NRC_score | AP50 | AP75 |
|---|---|---|---|---|---|---|---|---|
| **PSC-DIOR** | phase_mod | 1.70° | **1.201–1.210** | **1.169** | **yes** | 0.574 | 0.536 | 0.350 |
| **PSC-SODA** | phase_mod | 2.35° | **1.129–1.157** | **1.114** | **yes** | 0.956 | 0.598 | 0.269 |
| CSL-DIOR | softmax margin | 15.6° | 0.893–0.895 | 0.869 | no | 1.063 | 0.311 | 0.071 |
| CSL-SODA | softmax margin | 19.2° | 0.921–1.137 | 0.897 | no | 1.139 | 0.346 | 0.042 |
| DCL-DIOR | mean bit margin | 3.20° | 0.194–0.217 | 0.179 | no | 0.707 | 0.329 | 0.109 |
| DCL-SODA | mean bit margin | 3.44° | 0.365–0.370 | 0.352 | no | 1.000 | 0.526 | 0.174 |

## Reading (restricted; per 064 claim ledger)
- **PSC (phase_mod): PSC-specific reproducible reverse ranking under the pre-registered valid-head
  subset.** Reverse-ranked (NRC>1) on **both** datasets, **all 3 seeds**, bootstrap **CI lower
  bound > 1** — higher PSC intrinsic angle confidence tends to correspond to **worse** angle error,
  while the detection-score proxy is informative (0.57/0.96). Notably PSC also has the **best** angle
  accuracy (1.7–2.3° mean masked error), so this is a ranking pathology within otherwise-good
  predictions. This upgrades phase_mod from a single-checkpoint case to a **PSC-specific reproducible
  mechanism candidate / preliminary mechanism evidence** — **not** a mechanism proof.
- **DCL (bit margin): counterexample.** Native confidence is strongly **informative** (NRC
  0.20–0.37 ≪ 1). Therefore we **cannot** claim any "angle-coder confidence universally fails."
- **CSL (margin):** ≈ random / non-reversed (0.89–1.00), on a head with poor angle accuracy (15–19°).
- **direct_regression + KLD:** `failed_training` under the shared protocol — **failure audit only**,
  never mechanism support; not hidden.

## Mapping to the pre-registered A/B/C
- Pre-registered **A** = intrinsic native confidence consistently reverse-ranked across the 5-head
  matrix. **Not reached**: only 3/5 heads trained; and the trained heads **disagree** (PSC reverse,
  DCL informative, CSL random). ⇒ current status = **restricted A-like, PSC-specific evidence**.
- **B/C** not applicable. The measurement protocol + finite-sample conformal orientation risk control
  remains the mainline; R1 is a mechanism **appendix/section enhancement**, not the headline.

## Hard guardrails (obeyed)
No "phase_mod mechanism proven", "PSC angle head proven broken", "angle-coder confidence universally
fails", "TPAMI/CVPR ready", "full project complete". failed_training heads retained and disclosed.
Exploratory rescue is appendix-only, never in the main matrix. phase_mod stays a mechanism candidate.
