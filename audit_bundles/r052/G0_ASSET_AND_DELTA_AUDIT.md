# r052 G0 asset, parity, and delta-collision audit

## Frozen asset identity

- Dataset: DOTA-v1.0 train -> val, root /home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10.
- Host: valid Oriented R-CNN R50-FPN 1x le90.
- Baseline config: /home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/config.py.
- Baseline training log: /home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/train_20260430_175419.log.
- Checkpoint: /home/rspip/cqc/pro/study/pth_data/baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_7061_epoch_11.pth.
- Checkpoint SHA-256: f988b9a6b3d3662b22f2499679269bb00164417801957017082f6acdc9cf314c.
- Registered final val mAP/AP50: 0.7061/0.7060 at epoch 11; four-GPU global batch 4, SGD LR 0.02, SyncBN absent and frozen BN evaluation, mmrotate/mmengine stack in pcp-obb.

The train and val directories, annfiles, and images were verified present through the DOTA-v1.0 split symlink. The strict four-GPU identity-val rerun completed normally: mAP/AP50 = 0.7061/0.7060, exactly matching the registered epoch-11 value. Log: outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/g0/identity_val/test.log. No host retraining occurred.

## Delta collision screen

The primary-source audit in docs/paper_jprs_r051/primary_prior_art_audit.md was re-read. It covers RoI Transformer, Oriented R-CNN, ReDet, PSC, AQE, O2-RT-DETR, PQA, and FAA. r052 narrows the screen to the joint conjunction: decoded proposal; K candidate visual observations; shared posterior; class plus full-box plus axial-angle mixture likelihood; and native posterior-tail risk.

No cited primary source states or implements that full conjunction. Components such as rotated RoI features, periodic coding, direct angle distributions, feature alignment, mixture-like inference, and scalar quality outputs remain prior art and are not claimed as novelty. Result: PASS_G0_NO_EXACT_DELTA_COLLISION, pending the frozen identity-val parity rerun.

No DOTA-v2.0, SODA-A official test, HRSC semantic field, or new dataset was accessed.
