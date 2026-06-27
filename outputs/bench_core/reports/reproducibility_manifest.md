# Reproducibility Manifest

> 2026-06-27 21:18:21 CST

- thresholds.yaml sha256: `b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae`
- freeze_status: `partial_frozen_dota_d2+host_orientation_gates+c1_a4_formal_thresholds`
- RHINO ckpt: `outputs/training/rhino/best_dota_mAP_epoch_35.pth` sha256 `55a90abbace429276e593f8e4418fad002240ff1951912172367d997b474f9d9`
- A4 ckpt: `outputs/training/a4_host/best_dota_mAP_epoch_70.pth` sha256 `3e32fa11114ced82c2fb5ecdb25031ff45c1d2815b034a315b1af11ef8487e32`
- split: deterministic md5(image_id) -> D_cal/D_audit (disjoint)
- split files (path + sha256):
  - c1_view_a: `outputs/predictions/DOTA-v1.0/rhino/schema/pred_rhino_val.jsonl` sha256 `f89b767e42ca7848`
  - c1_view_b: `outputs/probes/c1_cross_view_real/view_b_unrotated.jsonl` sha256 `f0aba9a1aecf5781`
  - c1_gt: `outputs/predictions/DOTA-v1.0/_dcal_subset/gt_mmrotate.jsonl` sha256 `5b90795a37b40223`
  - a4_pred: `outputs/predictions/DOTA-v1.5/a4_host/schema/pred_a4_host_val.jsonl` sha256 `671076ecbdea702f`
  - a4_gt: `outputs/predictions/DOTA-v1.5/_dcal_subset/gt_mmrotate.jsonl` sha256 `c41da59cb4c482b3`
- test: `python -m pytest tests/ -q` -> 156 passed
- seeds: {'hsic': 0, 'bootstrap': 0, 'training': 42}
- env: {'analysis': 'mr_dev1x (mmrotate 1.x, numpy, cv2, shapely)', 'host_train_infer': 'ai4rs_train (torch 2.4, mmrotate ai4rs)'}
- gpu: host training 4xA30 (016-prior); 018 acceptance is CPU read-only; no new GPU use
- secrets: none (paths+hashes only).

**scope: frozen DOTA C1/A4 milestone — NOT full project.**
