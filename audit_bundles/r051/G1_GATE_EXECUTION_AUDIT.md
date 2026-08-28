# r051 G1 execution audit

- Dispatch: orientbench-b-r051-cmr-obb-cyclic-marginalized-roi-20260822
- Plan commit: 0d96d7b1474ef9416d3049e4a233837b3130c007
- Final execution state: normal gated scientific early stop
- Gate verdict: REJECT_CMR_CHEAP_SIGNAL
- Dataset protocol: DOTA-v1.0 train -> val only; no DOTA-v2.0, SODA-A official test, or other prohibited endpoint was touched.

## Completion evidence

G0 passed. The final CMR implementation was admitted by a four-GPU smoke export and independent mutation validator on 92,908 final detections; deletion of UID, level/cell exchange, NMS-mapping tampering, and duplicated candidates were all rejected. See outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1/dota_orcnn_cmr_smoke_20/evaluation/provenance_validation.txt.

All three frozen-host G1 arms completed on exactly four GPUs for three epochs with DOTA val evaluation each epoch. The first parallel attempt encountered CUDA OOM in the CMR and DIRECT_DIST arms; both were subsequently rerun serially on the unchanged four-GPU protocol and completed normally. No three-GPU fallback, split change, or threshold change occurred.

## Frozen G1 result

The immutable adjudication is outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1/metrics/g1_gate.json.

| Arm | AP50 | AP75 | AR>=2.1 mean angle error | AUGRC | Risk@70 |
| --- | ---: | ---: | ---: | ---: | ---: |
| CMR | 0.6490 | 0.3820 | 2.3858 | 0.013384 | 0.026341 |
| DIRECT_DIST (strongest control) | 0.6650 | 0.4010 | 2.0289 | 0.011360 | 0.022443 |
| SINGLE_ROI_QUALITY | 0.6620 | 0.3730 | 2.0835 | 0.011575 | 0.023150 |

CMR relative to DIRECT_DIST: AP50 delta -0.0160, AP75 delta -0.0190, angle-error relative change -17.59%, AUGRC relative change -17.81%, Risk@70 relative change -17.37%. The 1,000-replicate mother-image bootstrap lower bounds were -0.002834 (AUGRC) and -0.005309 (Risk@70). Consequently all seven frozen G1 conjunctive checks failed.

## Required disposition

G1 requires every check to pass. REJECT_CMR_CHEAP_SIGNAL therefore closes r051 as a valid gated early stop. G2/G3/G4 full-detector, multi-data, and transfer expansion were not started.

The complete file-level evidence manifest, including SHA-256 for logs, checkpoints, configs, exports, and adjudication artifacts, is outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/g1/metrics/g1_evidence_inventory.json.
