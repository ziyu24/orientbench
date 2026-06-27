# Cross-Dataset Exploratory Metrics (021)

> ALL exploratory; no formal gate; thresholds unchanged. env solved in 020; cross-dataset blocker is now GT availability / angle convention, not env.

| dataset | archetype | baseline | n_used | median_orient_err° | Risk@90 | NRC-AUC | angle_gate | mAP sanity | scope |
|---|---|---|---|---|---|---|---|---|---|
| HRSC2016 | lsknet_backbone | 13 | 240 | 5.875 | 7.1819 | 0.8068 | **blocked_angle_uncertain** | 0.9061 | cross_dataset_exploratory |

## blocked
- DIOR-R: only HBB xml GT (annfiles/obb empty) -> blocked_missing_obb_gt（无 OBB 角度 GT，朝向 metrics 不可算）。
- FAIR1M-v1.0: val_20 annfiles empty + split_ss_fair1m1.0 路径缺失 -> blocked_missing_gt。
## HRSC angle 状态
- mAP=0.906（与 baseline 一致）证明 mmrotate HRSCDataset 的 mbox->le90 内部一致、pred/GT 同 convention；
  但 raw mbox->le90 等价未做正式 read-only 证明 -> **angle_error_gate_status=blocked_angle_uncertain**；orientation err 仅 exploratory，不冻结、不 formal。
