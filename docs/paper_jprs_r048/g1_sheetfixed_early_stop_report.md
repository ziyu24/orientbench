# r048 sheet-consistent clean G1 rerun — valid early stop

This supersedes the invalid `formal_revised` scientific verdict that B rejected
at `4965243`.  G0 was reused.  No T_cal field and no T_audit semantic field was
read.

## Corrected contract and tests

The sole pole convention is now **positive `pole_logit` = q(sheet=1)**.
The BCE target is `sheet=1`; the full likelihood gives sheet 1 `logsigmoid(logit)`;
the circular decoder and intrinsic confidence consume that same density.  The
deterministic test covers both sheets, a deliberate 180-degree pole mutation,
and H/V/R90/R180/R270 analytic pull-backs plus rendered-label actions.

All P2C and baseline arms now receive a uniformly sampled H/V/R transform per
training item.  P2C uses its transformed view in the analytic distribution KL;
baselines receive it under their corresponding task loss.  All runs begin from
the registered R50 initialization in new `formal_sheetfixed` paths.

## Frozen first-epoch stop

The fair baseline reference reached val accuracy `0.885397` (whole-crop
binary), exceeding the frozen `0.65` premise.  Each corrected P2C capacity arm
then met the first-epoch stop condition:

| configuration | first-epoch P2C accuracy | stop criterion |
|---|---:|---|
| small | 0.502773 | <0.60 against baseline >=0.65 |
| base | 0.506470 | <0.60 against baseline >=0.65 |
| wide | 0.499076 | <0.60 against baseline >=0.65 |

Per the frozen plan and B's `4965243` review, all three arms stopped rather
than extending an already triggered formal failure.  The val selection rule
chose `p2c_base`; the strongest baseline was `whole_crop_binary`.

| model | accuracy | mean circular error (deg) | AUGRC |
|---|---:|---:|---:|
| P2C base | 0.506470 | 87.741 | 0.423795 |
| whole-crop binary | 0.885397 | 21.336 | 0.024484 |

The selected P2C is worse by `-0.378928` accuracy, `-0.399311` baseline-minus-
P2C AUGRC, and `-66.405°` baseline-minus-P2C circular error.  Its frozen jitter
rows are also uniformly negative:

| jitter | P2C − baseline accuracy | baseline − P2C AUGRC | baseline − P2C error (deg) |
|---|---:|---:|---:|
| 5° | -0.362292 | -0.380929 | -59.888 |
| 10° | -0.273567 | -0.344863 | -44.513 |
| 15° | -0.223660 | -0.324818 | -33.589 |

This is a convention-consistent G1 val failure and therefore a valid early
stop before T_cal; it does not open, evaluate, or tune on T_cal/T_audit.

Raw schema-2 rows, commands, logs, checkpoint hashes and manifest are in
`outputs/persistent_artifacts/orientbench_p2c_lift_r048_20260819/`.
