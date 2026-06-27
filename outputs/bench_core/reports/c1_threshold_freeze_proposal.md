# C1 Threshold Freeze Proposal (B_C1)

> 2026-06-27 20:41:51 CST
> proposed_by=claude; **approval_status=pending**; thresholds.yaml NOT modified; candidate=configs/thresholds.c1_candidate.yaml.

## 候选阈值（基于真实 cross-view D_cal，待批准）
- view_consistency_orient_err_p90_deg_max: 见 thresholds.c1_candidate.yaml（D_cal p90）
- drop_rate_across_views_max: D_cal DropRate
- near_square_masked: true
- OT vs GT-identity 打平判据（R1）: 需补真实 cross-view 上的 OT-dustbin vs GT-identity 对照（当前 view-A/view-B responsibility 已具，OT-dustbin tie 阈值待预注册）。

## 不允许（本轮无批准）
- 不得改 thresholds.yaml 为 complete_B_C1；不得 formal_pass/formal_fail。
- 仅 candidate / pending_approval。

## 冻结前需要
- 责任角色预注册 p90/DropRate/OT-tie 阈值与统计检验；批准后写 thresholds.yaml B_C1 并设 freeze_time，再 D_audit 正式 gate。
