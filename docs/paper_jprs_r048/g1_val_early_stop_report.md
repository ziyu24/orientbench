# r048 G1 consumed-development result — val early stop

The accepted G0 host-environment/AP-parity evidence was reused.  This report
records the replacement implementation required by B's interim review: actual
HRSC train/val headings, doubled-angle von-Mises axial density, residual-
conditional pole distribution, real center-to-header regression, direct-S1
von-Mises, analytic rotation-equivariance KL, and score-independent intrinsic
confidence.  No T_cal or T_audit semantic field was read.

## Val selection

All models used the registered R50 initialization, identical crop/augmentation,
30 epochs and four-GPU DDP.  The three predeclared P2C configurations yielded
the same best val accuracy (0.502773); the frozen tie-break (lower AUGRC) chose
`p2c_base` (19,306,633 trainable parameters).  The strongest learned baseline
was `whole_crop_binary` (19,306,633 parameters), selected by the stipulated
accuracy/AUGRC/circular-error order.

| model | accuracy | mean circular error (deg) | NLL | Brier | ECE | AUGRC |
|---|---:|---:|---:|---:|---:|---:|
| P2C-Lift base | 0.502773 | 89.572 | 0.669 | 0.258 | 0.452 | 0.544 |
| whole-crop binary | 0.853974 | 26.921 | 0.940 | 0.144 | 0.125 | 0.041 |
| concat endpoint binary | 0.852126 | 27.229 | 0.555 | 0.129 | 0.104 | 0.046 |
| headpoint 2D | 0.831793 | 32.110 | 1.633 | 0.279 | 0.385 | 0.131 |
| direct-S1 von-Mises | 0.593346 | 74.464 | 1.815 | 0.243 | 0.565 | 0.341 |

Relative to the selected baseline, P2C has accuracy delta `-0.351201`,
baseline-minus-P2C AUGRC `-0.503168`, and baseline-minus-P2C mean-circular-
error `-62.652°`.  It therefore fails every required val superiority bound.

## Frozen axis-jitter check

| axis jitter | P2C accuracy | baseline accuracy | delta accuracy | baseline − P2C AUGRC | baseline − P2C error (deg) |
|---|---:|---:|---:|---:|---:|
| 5° | 0.502773 | 0.826248 | -0.323475 | -0.458740 | -55.040 |
| 10° | 0.502773 | 0.792976 | -0.290203 | -0.407027 | -46.512 |
| 15° | 0.502773 | 0.724584 | -0.221811 | -0.339819 | -33.310 |

No jitter direction is positive.  Under G1, this complete val failure is a
gated scientific early stop: do **not** evaluate T_cal, do **not** seal a
model/policy, and do **not** open T_audit.

Raw schema-2 rows and logs are under
`outputs/persistent_artifacts/orientbench_p2c_lift_r048_20260819/g1_val_revised/`.
