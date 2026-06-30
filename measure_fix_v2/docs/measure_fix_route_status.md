# Measure → Fix 总路线状态

> 2026-06-30 10:14:08 CST。主线：Orientation Reliability: Measuring, Diagnosing, and Selecting Trustworthy Angles in OBB Detection。

| 阶段 | 状态 |
|---|---|
| **P1 measure+diagnose** | 当前阶段已完成（Bench-Core / NRC / reliability cliff / PSC score-level miscalibration / DOTA frozen formal gates；thresholds b7c4e649 冻结）。|
| **G2_double_prime** | **PASS**（固定 size bin 内 nonlinear 显著优于 score+ar+size linear → orientation-specific 非线性几何，非 box-size prior）。|
| **Deployable hardening** | **STABLE-PASS**（非 DOTA 12/12 beat size-linear，retained ~0.65，无目标 GT；DOTA #20 documented limitation）。|
| **Route-C offline proxy** | **STABLE-PASS**（GT-free local-angle-consistency，非 DOTA 10/10 beat size-linear，retained 0.718）。|
| **Route-C real TTA** | **STABLE-PASS on tested cells**（DIOR ORCNN#3/PSC#22 real hflip/vflip，2/2 beat size-linear，coverage limited；shadow farm 未改 dataset）。|
| **Track A mechanism diagnostic** | **intrinsic angle-coder miscalibration mechanism candidate — SUPPORTED**（PSC phase_mod 在 3/3 PSC cell 显著 NRC>1；非门控 P3，仅机制解释）。|
| **P2 / C1** | appendix / negative result（OT 未明确打赢 GT-identity，未恢复主线）。|
| **P3 method development** | **继续**（deployable reliability-aware geometry selector；Track C 最佳 selector，修复 PSC intrinsic 缺陷）。**未声称最终完成 / 顶会 ready**。|

## 边界
- 未改 thresholds/D_cal-D_audit/formal 标签/P1 frozen tag/历史 claim ledger；未训练 detector；未补 full matrix；未追 DOTA mAP；未恢复 P2；DOTA #20 未调参。
- upper-bound/calibration（用 source GT 训练）与 deployable（target 无 GT）严格区分。
