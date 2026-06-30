👇👇👇👇👇👇

# OrientBench v2 — 043 Track A PSC Mechanism Diagnostic 完成

- **043 完成**。原始 dataset 未修改；未改 thresholds(b7c4e649)/P1 split；未训练 detector；未补 full matrix；未恢复 P2；DOTA #20 未调参。
- **主报告（唯一人读）**：`measure_fix_v2/docs/track_a_psc_mechanism_report.md`

## Track A 信号是否可提取
- **可提取**。InstrumentedAngleBranchRetinaHead 子类把 PSC **phase_mod**（角度码模长 = intrinsic 置信）经 NMS 附到 pred_instances 导出（4-GPU，shadow farm 未改 dataset）。entropy/margin: PSC 为连续 coder，无 softmax → unavailable_with_evidence。

## Track A/B/C 结果（masked ar≥1.6, D_audit）
- **Track A (phase_mod) 3/3 PSC cell 显著 NRC>1**：DIOR #22 1.156[1.11,1.19]、SODA #23 1.117[1.11,1.13]、FAIR1M #24 1.121[1.08,1.16]。
- Track B (score) 0.56-0.98；Track C (geometry) 0.36-0.52（最佳）。

## PSC 机制裁决
- **intrinsic angle-coder miscalibration mechanism candidate — SUPPORTED**：PSC 自身角度码置信(phase modulus)与朝向正确性反相关 → 不只是 detection-score proxy mismatch，**angle-coder intrinsic 反校准**。克制：phase_mod 为一 intrinsic 信号，结论为 candidate 非最终定论。

## DOTA #20 状态
- 未跑 Track A（未建 farm；weak-structure negative control，**未调参**）= next-step。

## real TTA coverage 补充状态
- SODA/FAIR1M shadow farms 已建（Track A 用），real TTA 可直接复用，本轮未跑额外 = next-step（不阻塞 Track A）。

## 是否继续 P3 method development
- **继续**（Track A 不门控 P3；P3 由 G2″/Deployable/Route-C 支撑）。Track A 给 P3 增机制叙事（geometry selector 修复 PSC intrinsic 缺陷）。**不声称 P3 最终完成 / 顶会 ready**。

## 验证/test/git
- verifier `verify_track_a_psc_mechanism_043` → 见下；pytest 全过；原 dataset 0 改动；thresholds/split 未变；git 0 大文件。

👆👆👆👆👆👆
