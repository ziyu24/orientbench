# R1 angle-head config derivation (061)

> Pre-registration provenance for the 5-head × 2-dataset × 3-seed matrix. Written BEFORE any
> non-PSC run finished, so results cannot be re-storied afterwards. Generator:
> `top_journal_v3_reaudit_055/scripts/gen_r1_angle_head_configs.py`. Smoke:
> `scripts/smoke_test_r1_configs.py` → `reports/r1_config_smoke_061.csv` (30/30 PASS).

## Controlled-comparison principle
Every head config is produced by loading the **known-good PSC seed0 template** (per dataset)
as an mmengine `Config` and changing **only** `model.bbox_head`. Everything else —
`data_root`, `ann_file`, train/val/test pipelines, `train_dataloader`, schedule
(`max_epochs=12`, MultiStepLR [8,11], LinearLR warmup), optimizer (SGD lr=0.005 mom=0.9 wd=1e-4,
AmpOptimWrapper, grad-clip 35), anchors, assigner (MaxIoU pos=0.5/neg=0.4, RBboxOverlaps2D),
sampler, evaluator (`DOTAMetric` mAP), and the frozen masked ar≥1.6 audit split — is inherited
byte-for-byte. So the **only** variable across heads is the angle representation.

Datasets (unchanged from the trained PSC baselines):
- **DIOR-R**: 20 classes, trainval→test (§4.3 non-DOTA), n_train=11725, data_prep DOTA-txt.
- **SODA-A**: 9 classes, train_tiled→val_tiled (tiled_ss), n_train=23063.

Detector held fixed for all heads: single-stage `mmdet.RetinaNet` + ResNet-50 + FPN, le90.

## Per-head diff (vs PSC template) and pre-registered native uncertainty

| head | head type | angle_coder | angle/bbox loss changed | encode_size | native uncertainty (pre-registered) |
|---|---|---|---|---|---|
| **PSC** (baseline) | AngleBranchRetinaHead | PSCCoder(dual_freq,num_step=3) | loss_angle=L1(0.2) | 6 | phase_mod (`phase_cos²+phase_sin²`) |
| **CSL** | AngleBranchRetinaHead | CSLCoder(omega=4,gaussian,r=3) | loss_angle→SmoothFocalLoss(0.8) | 45 | angle-class softmax entropy / max-prob / margin |
| **DCL** | AngleBranchRetinaHead | **DCLCoder(BCL,omega=1)** *(project-local)* | loss_angle→CrossEntropy(sigmoid,0.8) | 8 | per-bit sigmoid margin (mean/min over bits) |
| **direct_regression_le90** | mmdet.RetinaHead | none (direct 5-param) | loss_bbox=L1(1.0) | 1 | **NONE — negative control** |
| **KLD** | mmdet.RetinaHead | none (direct 5-param) | reg_decoded_bbox=True, loss_bbox→GDLoss_v1(kld,log1p,τ=1) | 1 | **not natively emitted (documented gap, see below)** |

Held constant for the AngleBranchRetinaHead heads (PSC/CSL/DCL): `loss_bbox=L1(0.5)`,
`loss_cls=FocalLoss(1.0)`, `num_classes`, anchors — so PSC/CSL/DCL differ **only** in
`angle_coder` + `loss_angle`. `use_normalized_angle_feat` is forced **False** for CSL/DCL
(it is a PSC-specific feature; upstream CSL/DCL references leave it off) and documented here.

## Two honesty flags recorded before training (per §III.6, "不伪造")
1. **KLD native uncertainty gap.** The pre-registration lists KLD's native uncertainty as
   "predicted angle variance / distribution uncertainty." But the standard KLD-RetinaNet head
   (`mmdet.RetinaHead` + `GDLoss_v1`) regresses a **point** (x,y,w,h,θ) and emits **no**
   per-instance angle variance. GDLoss shapes the *training* loss, not a test-time variance
   output. Therefore at eval KLD will have **only** the detection-score proxy available, same
   as direct_regression — differing solely in training loss. This is recorded now; the eval
   will report KLD native-uncertainty as `not_emitted` (blocker), not a fabricated variance.
2. **DCL coder is a project-local reimplementation.** `DCLCoder` is absent from the installed
   `mmrotate 1.0.0rc1` (third_party, not modifiable). We implemented the BCL (Binary Coded
   Label) variant in `orientbench_ext/dcl_coder.py`, mirroring the CSLCoder/PSCCoder interface,
   registered via `custom_imports`. It is gated by a round-trip unit test
   (`orientbench_ext/test_dcl_coder.py`, PASS: max round-trip error 0.50° within the 1° bin).
   DCL cells carry `head_impl=project_local_BCL` provenance. **No mechanism conclusion** is
   drawn from a single self-implemented coder absent the completed pre-registered matrix.

## Verification performed (061)
- `gen_r1_angle_head_configs.py`: 28 configs written + 2 PSC templates = 30 files.
- `smoke_test_r1_configs.py`: **30/30 PASS** = config-parse + `MODELS.build(model)` (validates
  each coder's `encode_size` → angle-branch conv wiring) + one real train sample
  (`dataset[0]`, validates data paths + annotation format). DIOR n=11725, SODA n=23063.
- No change to `thresholds.yaml` (sha256 b7c4e649… intact), D_cal/D_audit, or any frozen asset.
