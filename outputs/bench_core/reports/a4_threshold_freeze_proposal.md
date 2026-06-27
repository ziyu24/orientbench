# A4 Threshold Freeze Proposal (A_A4)

> 2026-06-27 20:41:51 CST
> proposed_by=claude; **approval_status=pending**; thresholds.yaml NOT modified; candidate=configs/thresholds.a4_candidate.yaml.

## 候选阈值（基于真实 source attribution D_cal，待批准）
- partial_corr_max_abs: 0.20（A4 vs 各 source 偏相关上界，draft）
- hsic_p_min_after_correction: 0.05
- A4 vs GV/entropy/score 最小 Δ: 待 A4 q_i 接入后定（当前 source sanity 已具 score/entropy/GV/E_layout/E_bg vs orientation risk）
- near_square_masked: true

## 不允许（本轮无批准）
- 不得改 thresholds.yaml 为 complete_A_A4；不得 formal_pass/formal_fail。

## 冻结前需要
- 责任角色预注册 partial-corr/HSIC 上界 + A4 vs baseline Δ 与多重比较校正；批准后写 thresholds.yaml A_A4 并设 freeze_time，再 D_audit 正式 gate。A-gate-1 须同宿主(O2-RTDETR frozen, R3)。
