# r049 G1 numerical repair verification

The G1 stop was caused by two **zero-area DIOR training annotations**, not by
CORA. The host-only continuation reproduced the same `loss_bbox: inf`; after
the project-local pipeline removed width/height `<=1` boxes before target
encoding, the repaired CORA smoke completed normally.

| evidence | outcome |
|---|---|
| host control, unfiltered | `loss_bbox: inf` at iter 150 |
| CORA, unfiltered AMP and FP32 | `loss_bbox: inf` at iter 150 |
| host control, invalid-box filter | all reported losses finite |
| CORA, invalid-box filter, 4 GPUs, 200 iter | all reported losses and gradient norms finite |
| full validation | AP50 `0.5110`, AP75 `0.2770` |

The repair leaves source annotation files, images, train membership, checkpoint,
optimizer, global batch, LR, BN, evaluation endpoint and CORA losses unchanged.
It only skips two invalid boxes (`04137.txt:14`, `07007.txt:37`) that have zero
area and cannot produce a valid rotated-box target.

The full smoke log is
`outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g1/dior_cora_smoke_200_repaired_fullval_bg/20260819_062910/20260819_062910.log`.
No G2 or seed0 run was started by this repair task.
