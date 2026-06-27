# P2/P3 Readiness Update — 015

> 2026-06-27 20:18:58 CST

## 当前阶段
- host 训练已落地（RHINO C1/B, O2-RTDETR A4）+ host orientation gate（partial_frozen_dota_d2+host_orientation_gates）。
- 本轮搭建 **C1 cross-view (P2) 与 A4 source-attribution (P3) 机制 smoke**（用 locked host）。

## C1 cross-view (P2) — mechanism_smoke_available
- 原语已实现并跑通：OT matching with dustbin、GT-identity 对照(R1)、responsibility、DropRate、view-consistency risk、failure taxonomy、near-square mask、D_cal/D_audit 互斥。
- smoke 结果(RHINO, DOTA-v1.0 val, max_images=80/split): DropRate D_cal 0.235 / D_audit 0.303；OT dustbin mass ~0.22；**OT vs GT-identity reldiff 0.019/0.045（OT 与 GT-identity 接近打平）**；view-consistency orient err ~1.5-1.7°。
- **关键(诚实)**: cross-view 当前为 deterministic synthetic geometric transform（synthetic_view_transform_for_mechanism_smoke=true，missing_real_cross_view_pairs=true）；OT 与 GT-identity 接近打平 → 按 R1，若真实数据上也打平则 OT-dustbin 退役/C1 降级。**这是机制 smoke，非完整 C1 gate。**

## A4 source-attribution (P3) — mechanism_smoke_available
- 原语已实现并跑通：partial-corr(控 GV+class)、HSIC(置换 p, 受控抽样 max_samples=800/seed=0)、bootstrap CI、source sanity(GV/layout/score/entropy vs orientation risk)、per-class、near-square mask、D_cal/D_audit。
- smoke 结果(O2-RTDETR, DOTA-v1.5 val, n_used~13k/split): orientation risk 的 partial-corr — **score ≈ -0.17(p≈0.005)、entropy ≈ +0.16(p≈0.005)、E_layout ≈ -0.05(p≈0.005)、GV ≈ -0.02**。即 selection score / angle-entropy 与朝向风险显著相关，layout 弱相关，GV 控后近零。
- **诚实**: background source 在 smoke 未算(需 raster image annulus)；A4 vs GV/entropy/score 最小 Δ 与 partial-corr/HSIC 上界 (R8) 未冻结。**机制 smoke，非完整 A4 gate。**

## 可进入 D_cal / 仍 blocked
- 可进入 D_cal 探索: 两路机制原语(OT-dustbin/DropRate/view-consistency；partial-corr/HSIC)。
- 仍 blocked（不可进入 formal gate）:
  - C1: 缺真实 cross-view paired capture；OT vs GT-identity 打平阈值未冻结(R8)；R1/R2 完整对照未跑。
  - A4: background source 未算；A_A4 阈值(partial-corr/HSIC 上界、A4 vs baseline Δ)未冻结(R8)；A-gate-1 source sanity 完整流程未做。

## readiness / formal_gate
- readiness: host_ready → **mechanism_smoke_available**（C1 + A4 机制 smoke 跑通）。
- **formal_gate_allowed = False**（不得自动改 true）。仅在 D_cal 标定 + 阈值候选 + 冻结批准 + D_audit 正式评估全部完成后，对应 gate 方可 formal_pass/formal_fail。

## 下一步正式 gate 需要的数据规模与批准
- C1: 对 RHINO 在真实 cross-view（旋转/增强视图）重推理生成 paired predictions（DOTA val 全量或 ≥2000 图），预注册 OT vs GT-identity / DropRate / padding-only 阈值并批准冻结，再 D_audit。
- A4: 对 O2-RTDETR 加 background source（image annulus），扩 D_cal 样本，预注册 partial-corr/HSIC 上界与 A4 vs GV/entropy/score Δ 并批准冻结，再 D_audit；A-gate-1 须同宿主(O2-RTDETR frozen, R3)。

---
## 016 更新：real-化结果
- **C1**: synthetic smoke → **真实 cross-view（旋转视图 + 真实 RHINO inference, mapped back）**。view-consistency orient err median 1.09°(D_cal)/1.20°(D_audit)，p90 ~3.4°；DropRate across views 0.115/0.136。状态=**ready_for_threshold_review**（candidate=thresholds.c1_candidate.yaml）。genuine 多物理视角仍缺（augmentation-view）。
- **A4**: 补 **真实 background source**(image annulus, bg_unavailable_ratio=0.000)。partial-corr orientation risk: score≈-0.20/entropy≈+0.20(p≈0.005 显著)、E_bg≈-0.03~-0.05(弱/不显著)、E_layout≈-0.06、GV≈0。状态=**ready_for_threshold_review**（candidate=thresholds.a4_candidate.yaml）。
- readiness: mechanism_smoke_available → **ready_for_threshold_review（C1+A4）**。**formal_gate_allowed=False**（未冻结/未批准）。

---
## 017 更新：C1/A4 formal gate
- C1/A4 D_cal 阈值已冻结(token 017)；D_audit formal gate: **C1 formal_pass(augmentation-view), A4 formal_pass(same-host)**。
- readiness: ready_for_threshold_review → **formal_pass (scoped)**。formal_gate_allowed=**true_for_frozen_dota_c1_a4_scope_only**。training_allowed 未改。
