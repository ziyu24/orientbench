# Track A PSC Mechanism Diagnostic 报告 (043)

> SUPERVISOR_APPROVED_043_TRACK_A_PSC_MECHANISM_DIAGNOSTIC · measure_fix_v2/ · 原始 dataset **未修改** · 未改 thresholds(b7c4e649)/D_cal-D_audit · 未训练 detector · 未补 full matrix · 未恢复 P2 · DOTA #20 未调参。
> 唯一人读主报告。**Track A 仅解释机制，不门控 P3。**

## 1. 为什么现在做 Track A
- P3 已通过 G2_double_prime / Deployable / Route-C real TTA。本轮启动 Track A 机制支线：判定 PSC 反校准是 **angle-coder intrinsic** 还是 **detection-score proxy mismatch**。

## 2. Track A 不再门控 P3
- P3 是否成立由 G2″/Deployable/Route-C 决定（已 pass）。Track A 结果**仅用于机制解释**，不改变 P3 主线。

## 3. PSC instrumentation 方法
- 子类 `InstrumentedAngleBranchRetinaHead`：在 `_predict_by_feat_single` 中，对 NMS 前的每个候选计算 **phase_mod = phase_cos²+phase_sin²（first freq，PSCCoder.decode 内部量）= PSC intrinsic 角度码模长/置信**，作为额外字段附到 InstanceData，过 NMS 进入 pred_instances，DumpDetResults 导出。custom_imports track_a_pkg；4-GPU world_size=4。
- shadow farm（不改原 dataset）：DIOR（042 farm）、FAIR1M（3896 symlinks + dummy-class annfiles）、SODA（原 val_tiled 已 populated，read-only 直跑）。原 dataset 0 文件改动。

## 4. dump 信号是否可用
- **可用**：phase_mod 成功 dump（range 0.18-2.51）。其它信号（softmax entropy / top-2 margin）：PSC 是连续 phase coder（非分类头），无 softmax 分布 → **unavailable_with_evidence**；phase_mod 是 PSC 最自然的 intrinsic 角度置信。

## 5. Track A/B/C 对比（D_audit，masked ar≥1.6）
| cell | A phase_mod (CI) sig>1 | B score | C geometry |
|---|---|---|---|
| DIOR #22 | **1.156** [1.11,1.19] ✓ | 0.563 | 0.356 |
| SODA #23 | **1.117** [1.11,1.13] ✓ | 0.982 | 0.389 |
| FAIR1M #24 | **1.121** [1.08,1.16] ✓ | 0.896 | 0.519 |
- 详见 track_abc_results_043.{md,csv}。

## 6. PSC 机制裁决：**intrinsic angle-coder miscalibration mechanism candidate — SUPPORTED**
- **Track A (phase_mod) 在 3/3 PSC cell 显著 NRC>1（CI 下界>1）**：PSC 自身角度码置信（phase modulus）与朝向正确性**反相关**——高置信角度码反而误差更大。
- 按协议判定规则（"若 Track A 也 NRC>1 且 CI 支持 → PSC intrinsic angle-coder mechanism candidate"）：**支持 intrinsic angle-coder 反校准机制候选**，而**不只是** detection-score proxy mismatch（041 的较弱表述）。
- **克制边界**：phase_mod 是一个（有原理依据的）intrinsic 信号（角度码模长）；本结论为 **mechanism candidate**，非最终定论；其它 intrinsic 信号（如 decoded-angle 分布熵）可后续考察。Track C geometry selector 仍是最佳可用 selector（NRC 0.36-0.52）。

## 7. DOTA #20 negative control
- 本轮未跑 DOTA #20 Track A（未建 DOTA farm；weak-structure negative control，**不调参**）→ delineated next-step。延续 040/041/043 诊断（DOTA #20 oracle_gain 最低、未显著反校准）。

## 8. real TTA coverage 补充状态
- SODA/FAIR1M shadow farms 本轮已建（为 Track A）→ **real TTA（hflip/vflip）可直接复用这些 farm**，但本轮聚焦 Track A、未跑额外 real TTA inference = **documented next-step**（不阻塞 Track A）。042 real TTA 已证 DIOR 2 cells。

## 9. 对 P3 method development 的影响
- Track A 不门控 P3；P3 继续（G2″/Deployable/Route-C 已支撑）。
- Track A 给 P3 增加**机制叙事**：PSC 不可靠不仅是 score-proxy 问题，**angle-coder intrinsic 置信本身反校准** → 强化 "为何需要 geometry-aware reliability selector"（Track C 修复 intrinsic 缺陷）。

## 10. 下一步建议
- 扩 Track A 到 DOTA #20（negative control 对照，不调参）+ 更多 intrinsic 信号（decoded-angle 熵）。
- real TTA coverage 复用 farms 扩 SODA/FAIR1M。
- （非本轮）将 mechanism candidate 推进为 controlled angle-head 实验需新批准。venue 交合作者。
- **未声称**：P3 最终完成；PSC angle head 反校准为最终定论（仅 mechanism candidate，Track A 证据支持）。
