# Track A Mechanism Boundary (046)

> 2026-06-30 14:46:34 CST。Track A 仅机制支线，不决定主线/venue，不恢复 P2。

## 边界声明
1. **PSC phase_mod 保留为 mechanism candidate**：phase_mod（intrinsic 角度码模长）在 3/3 PSC cell NRC>1 显著（DIOR 1.156[1.11,1.19]、SODA 1.117[1.11,1.13]、FAIR1M 1.121[1.08,1.16]）→ **intrinsic signal supports a mechanism candidate**。
2. **DOTA #20 negative / weak-structure control，不调参**：oracle_gain 0.155（最低）、masked detection-score NRC 0.84（未显著反校准）。未跑 DOTA #20 Track A（未建 farm，negative control）。**不为 DOTA #20 调参**。
3. **若 Track A 正常（NRC≤1）→ 写 score-proxy mismatch**。本项目 Track A **反校准**，故：
4. **Track A 反校准 → 写 intrinsic signal supports mechanism candidate**（而非仅 score-proxy mismatch）。
5. **禁止写 PSC angle head definitively broken**：phase_mod 是**一个** intrinsic 信号；结论为 candidate，需更多 intrinsic 信号（decoded-angle 熵等）与 controlled angle-head 实验（需新批准）方能确证。

## Track A 不做什么
- **不决定主线启动**（P3 由 G2''/Deployable/Route-C 支撑，Track A 非门控）。
- **不决定 venue**。
- **不恢复 P2**（P2/C1 仍 appendix/negative result）。
- **非唯一决定性证据**。

## 与 Fix 的关系
- Track A 反校准解释了"为何 detection-score 与 PSC intrinsic 置信都不适合作 orientation selector" → 支撑 **geometry-aware selector（Track C）** 的动机（修复 intrinsic 缺陷）。这是机制叙事，**非** P3 成立的门控证据。
