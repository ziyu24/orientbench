# orientbench-c r011 server report

## Final decisions

- P1: `PASS_STRONG_JSTARS_EVIDENCE_R011`.
- P3: `P3_CROSS_DOMAIN_INCONCLUSIVE_R011`.
- Joint: `TGRS_NOT_REACHED_R011`; this is not a readiness claim.

## P1 closure

- The official endpoint is `mmrotate.evaluation.functional.eval_rbbox_map`; the independent endpoint uses Shapely polygon IoU and separate matching/AP code.
- Executable golden: 42/42 PASS, including 20 optimized-vs-brute-force paired-bootstrap synthetic cases. Official/clean-room/authority baseline parity: 6/6 PASS, with AP50 and AP75 absolute differences no greater than 0.002.
- The complete fixed grid contains 144 P/D/S rows and 96 independently evaluated +/- components. S is the arithmetic mean of actual positive and negative evaluations.
- Paired full-split image bootstrap: 1,000 replicates per unit. D15 and S15 support are 6/6 and 6/6 after separate Holm correction, covering DIOR-R, FAIR1M-v1.0, and SODA-A.
- D-track AP75 monotonicity: 6/6. Fixed baseline-IoU75 cohort AR-bin survival ordering: 6/6.
- Corrected SODA-A/23 lineage uses the K1 identity dump with 1,663,631 predictions; official AP50/AP75 are 0.599124/0.273483. The older 1,449,379-prediction schema is not used.

## P3 bounded revalidation

- All 12 structural folds are reported; 11 are identifiable and one RTMDet leave-detector fold is `NOT_IDENTIFIABLE`.
- The nonlinear source-supervised candidate is supported in 4/11 eligible folds (36.36%), below the frozen 60% requirement. Leave-dataset support is 0/6.
- Fit uses source D_cal only; target D_audit GT is evaluation-only. The outcome is a negative/inconclusive transfer result, not a deployable selector.

## Reproducibility and compliance

- Read-only validator independently passed 130 checks, including row universes, S arithmetic, bootstrap summaries, Holm decisions, survival cohort grid, P3 leakage/gate, manuscript placement, authorized paths, and the protected `dis/B.md` blob.
- No detector training, detector inference, download, threshold change, D_cal/D_audit change, or public-mAP pursuit occurred.
