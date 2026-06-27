# Formal Gate Blockers — 016

> 2026-06-27 20:46:07 CST
> formal_gate_allowed = **False**（未自动改 true；无冻结审批）。DOTA D2 = partial_frozen_dota_d2+host_orientation_gates 未动。

| gate | status | 进展 | blocker（进入 formal_pass/fail 前必须） |
|---|---|---|---|
| C1 (B_C1, RHINO) | **ready_for_threshold_review** | 真实 cross-view（旋转视图 + 真实 RHINO inference）跑通；candidate 已出 | ① R8 预注册+批准冻结 c1 阈值(p90/DropRate/OT-tie)；② genuine 多物理视角缺失→当前为 augmentation-view（如需真视角须新采集）；③ OT-dustbin vs GT-identity 真实对照阈值(R1) |
| A4 (A_A4, O2-RTDETR) | **ready_for_threshold_review** | 真实 background source(annulus, bg_unavailable=0)+attribution 跑通；candidate 已出 | ① R8 预注册+批准冻结 a4 阈值(partial-corr/HSIC 上界, A4 vs baseline Δ)；② A4 q_i 接入做 A4 vs GV/entropy/score Δ；③ A-gate-1 同宿主完整 source sanity(R3) |

## 共同
- 无冻结审批（本轮只 candidate）；D_audit 仅 holdout 未调阈值；hosts 不混用；ckpt hash 校验通过。
- formal_gate_allowed 仅在「D_cal 标定 + 阈值候选 + 冻结审批 + D_audit 正式评估」全完成后，对应 gate 方可 formal_pass/formal_fail。
