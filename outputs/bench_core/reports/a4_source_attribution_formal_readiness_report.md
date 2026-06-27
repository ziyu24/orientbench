# A4 Source-Attribution Formal-Readiness (O2-RTDETR host, WITH background)

> A4 frozen sha256=3e32fa11114ced82…; background=image annulus (real). bg_unavailable_ratio=0.0 (max_bg_images=200). status=**ready_for_threshold_review**. 非完整 A4 gate（阈值未冻结）。

| split | n_used | E_bg pc | E_bg HSIC p | E_layout pc | score pc | entropy pc | GV pc |
|---|---|---|---|---|---|---|---|
| D_cal | 2951 | -0.033 | 0.05472636815920398 | -0.0589 | -0.2041 | 0.1978 | -0.0005 |
| D_audit | 2974 | -0.0521 | 0.7213930348258707 | -0.0233 | -0.1675 | 0.1603 | 0.0295 |

## 关键（真实，含 background source）
- partial-corr 控 GV+class；HSIC 置换 p（受控抽样 800/seed0）。E_bg=image annulus 梯度方向证据。
## 状态: A4 = **ready_for_threshold_review**
- ready_for_threshold_review 时 candidate 见 thresholds.a4_candidate.yaml；formal_gate_allowed 仍 False（阈值未冻结）。
- D_audit 仅 holdout，未调阈值。A-gate-1 同宿主(O2-RTDETR frozen, R3)。
