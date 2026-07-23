# R1 config derivation — 062 addendum (post-training head disposition)

> Extends `r1_angle_coder_config_derivation_061.md` with what training revealed. The 061
> derivation (only `bbox_head` changed on the known-good PSC template; data/schedule/optimizer/
> AMP held fixed) is unchanged. This addendum records the trainability outcome per head.

## Final head disposition under the frozen shared protocol (SGD lr=0.005, AMP, 12ep)
| head | detector head | trainable under shared protocol? | main-matrix status |
|---|---|---|---|
| **PSC** | AngleBranchRetinaHead + PSCCoder | **yes** (mAP DIOR≈0.53, SODA≈0.60) | main, 3 seeds ×2 ds |
| **CSL** | AngleBranchRetinaHead + CSLCoder | **yes** (mAP DIOR≈0.29–0.31, SODA≈0.32–0.38) | main, 3 seeds ×2 ds |
| **DCL** | AngleBranchRetinaHead + DCLCoder(BCL) | **yes** (mAP DIOR≈0.32–0.34, SODA≈0.50–0.54) | main, 3 seeds ×2 ds |
| **direct_regression_le90** | mmdet.RetinaHead direct 5-param + L1 | **no — NaN divergence** (ep1) | failed_training |
| **KLD** | mmdet.RetinaHead + GDLoss_v1(kld) | **no — AMP/fp16 `linalg.inv` crash** | failed_training |

## The KLD finding (new in 062)
- KLD was derived (061) from the plain rotated-retinanet head + `reg_decoded_bbox=True` +
  `GDLoss_v1(kld)`, inheriting the PSC template's `AmpOptimWrapper` (AMP/fp16).
- `GDLoss_v1(kld)` computes `linalg.inv` on the covariance; PyTorch `linalg.inv` does not support
  fp16 → `RuntimeError: linalg.inv: Low precision dtypes not supported. Got Half`, crashing all 4
  ranks in <30 s, all 6 seeds/datasets identically.
- This is a **hard incompatibility with the pre-registered AMP protocol**, not a tuning failure.
  KLD is therefore `failed_training` in the main matrix (consistent with direct_regression's NaN
  divergence). A precision-only (fp32) exploratory rescue is documented separately, appendix-only.

## Native uncertainty column — final
- PSC → `phase_mod`; CSL → angle-class entropy/max-prob/margin; DCL → per-bit sigmoid margin.
- direct_regression_le90 → none (negative control) — failed anyway.
- KLD → `not_emitted` (point-regression head emits no per-instance angle variance) — failed anyway.

## No change to frozen assets
`thresholds.yaml` (b7c4e649…) unchanged; D_cal/D_audit unchanged; masked ar≥1.6 protocol unchanged.
No head config's data/schedule/optimizer/AMP was altered (the failures are recorded as-is, not
worked around in the main matrix).
