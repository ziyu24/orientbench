# r036 Q-SetOD paper-kill study

## Registered decision

- Candidate state: `QSETOD_EVIDENCE_ONLY_KEEP_M`.
- KILL-E=False: 5/8 held-out configurations are evidence witnesses.
- KILL-C=True: 4/16 alpha/config rows violate the frozen calibration gate.
- PRUNE-M=False: multimodal row-weighted fraction=0.144760 across 536 strata.
- Clean endpoint inventory: 2 present candidates; inventory does not authorize future use.

The result is a registered server-side candidate pending B/C post-pull replay. It does not revise r034 and does not authorize training.

## T2 evidence increments

| config          |   common_support_rows |   spearman_gain |   spearman_gain_ci_low |   spearman_gain_ci_high |   q75_loss_gain |   AUGRC_gain |   AUGRC_gain_ci_low |   AUGRC_gain_ci_high | evidence_witness   |
|:----------------|----------------------:|----------------:|-----------------------:|------------------------:|----------------:|-------------:|--------------------:|---------------------:|:-------------------|
| HOdet_A_to_B    |                 47816 |      0.0618575  |              0.0501583 |               0.0743302 |        0.21125  |  0.000774914 |         0.000625691 |          0.000928451 | True               |
| HOdet_A_to_C    |                 47817 |      0.0607468  |              0.0537213 |               0.0680489 |       -0.464415 |  0.000443884 |         0.000307445 |          0.000574376 | False              |
| HOdet_BC_to_A   |                 43838 |      0.0830428  |              0.0757194 |               0.0906989 |        0.181587 |  0.000785043 |         0.000645422 |          0.000938714 | True               |
| HOdata_ABC_to_D |                  2920 |      0.00975021 |             -0.0206623 |               0.0460416 |        0.145647 |  6.17442e-05 |        -0.000131331 |          0.00025584  | False              |
| HOdata_ABC_to_E |                 35229 |      0.0505113  |              0.0362056 |               0.066343  |        0.502085 |  0.00187315  |         0.000948099 |          0.00329334  | True               |
| HOdata_ABC_to_F |                 39917 |      0.042277   |              0.030761  |               0.0545507 |        0.446217 |  0.00249173  |         0.00130483  |          0.00448802  | True               |
| HOdata_ABC_to_G |                 31029 |      0.050951   |              0.0318958 |               0.0703577 |        0.212806 |  0.000659633 |         0.000336455 |          0.00112644  | True               |
| HOdata_ABC_to_H |                 32435 |      0.0295731  |              0.0138806 |               0.0458849 |        0.108993 |  0.000390469 |         0.000220008 |          0.000619378 | False              |

## T4 source-only calibration failures

| config          |   alpha |   nominal_coverage |   overall_coverage |   coverage_deviation |   median_width_deg |   near_full_gt150_rate | kill   |
|:----------------|--------:|-------------------:|-------------------:|---------------------:|-------------------:|-----------------------:|:-------|
| HOdata_ABC_to_D |     0.1 |                0.9 |           0.953539 |            0.0535391 |           16.0419  |              0.0559599 | True   |
| HOdata_ABC_to_D |     0.2 |                0.8 |           0.870078 |            0.0700781 |           10.4367  |              0.0518232 | True   |
| HOdata_ABC_to_E |     0.2 |                0.8 |           0.86745  |            0.0674502 |            8.97498 |              0.0527712 | True   |
| HOdata_ABC_to_F |     0.2 |                0.8 |           0.86272  |            0.0627197 |            9.72835 |              0.0448637 | True   |

## Boundary

No GPU, neural training, detector forward/inference, new data download, frozen-threshold change, split change, or target-label fitting occurred.
