# C1 Real Cross-View Formal-Readiness (RHINO host)

> RHINO frozen (sha256 55a90abbace42927…). View B = **真实** RHINO inference on 90°-rotated image, mapped back.
> **real_inference_on_transformed_view=True**；genuine_multi_physical_viewpoint=**False**（augmentation-consistency）。非完整 C1 gate（阈值未冻结）。

| split | imgs | GT | both-views | DropRate | view-consist err med° | err p90° | masked |
|---|---|---|---|---|---|---|---|
| D_cal | 286 | 10879 | 9627 | 0.1151 | 1.085 | 3.363 | 93 |
| D_audit | 314 | 10470 | 9042 | 0.1364 | 1.203 | 3.489 | 86 |

## 关键（真实，非 smoke）
- view-consistency orientation risk = 同一 GT 在原视图 vs 旋转视图下 RHINO 预测朝向之差（真实 detector 视图稳定性）。
- DropRate across views = 在某一视图有责任、另一视图丢失的 GT 比例（真实视图鲁棒性）。
## 状态
- C1 = **ready_for_threshold_review**（真实 cross-view 跑通，candidate 见 thresholds.c1_candidate.yaml）。
- formal_gate_allowed 仍 False（阈值未冻结，需 R8 批准）。D_audit 仅 holdout，未调阈值。
## 诚实边界
- cross-view 为 augmentation-view（旋转）+ 真实 inference，**非** genuine 多物理视角；若需后者，需新数据采集（见 availability audit）。
