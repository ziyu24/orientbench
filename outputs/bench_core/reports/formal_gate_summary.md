# Formal Gate Summary — 017

> 2026-06-27 21:09:35 CST
> **formal_gate_allowed = true_for_frozen_dota_c1_a4_scope_only**（仅冻结的 DOTA C1/A4 scope）。
> training_allowed=true_for_approved_host_scope（未改）；DOTA D2 partial_frozen 未动。

| gate | host | scope | verdict | key |
|---|---|---|---|---|
| C1_augmentation_view_consistency | RHINO (55a90abb) | DOTA / augmentation-view（**非 genuine physical multi-view**） | **formal_pass** | p90 3.489°<=5.04, DropRate 0.136<=0.184 |
| A4_source_attribution | O2-RTDETR (3e32fa11) | DOTA / same-host source attribution（**无跨 host 因果**） | **formal_pass** | non-GV sig sources HSIC p<=0.05: score/entropy/E_layout |

## 范围声明（克制）
- C1 formal_pass **仅 augmentation-view scope**；不是 genuine physical multi-view 证据。
- A4 formal_pass **仅 same-host A4 source-attribution scope**；不得宣称跨 host 因果。
- DOTA partial（RHINO/O2-RTDETR 各自数据集）；**非全数据集、非 9-detector 全矩阵**。
- D_audit 仅 holdout，未参与阈值；阈值经 D_cal + token 017 冻结。
- SODA-A/ICDAR-MLT/HRSC/genuine multi-view 未纳入。training 当前不需要。

---
## 018 口径更新
- scoped_formal_gate_allowed=true_for_frozen_dota_c1_a4_scope_only
- overall_project_complete=false; training_needed_now=false
- training_allowed=no_new_training_required_for_current_scope（非继续训练许可；历史 host-scope 训练已批准并完成）

---
## 029 (2026-06-28 17:56:03 CST)
- formal gates 不变（frozen DOTA C1/A4 scope）；cross-dataset/multi-detector 全 exploratory，未新增 formal gate；thresholds 未变。
