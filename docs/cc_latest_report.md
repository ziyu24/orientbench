👇👇👇👇👇👇

# OrientBench — 037 P3 可行性门控 完成

- **037 完成**。无训练/host 重训/full matrix/追 mAP；thresholds 未变（b7c4e649），frozen DOTA D_cal/D_audit 未改。
- **主报告（唯一人读）**：`docs/p3_feasibility_gate_report.md`

## P1 状态
- P1 当前阶段已完成（工程 + 效度审计 + 中文审稿稿），可交合作者审核。

## PSC Track A 是否可用
- **不可用**。4 个 PSC cell 的 saved preds 仅含 bboxes/scores/labels，无 angle logits/distribution/uncertainty。架构上存在（PSCCoder encode_size=6 相位码），需 instrumented forward dump 提取。**P3 现不能声称 PSC angle-head intrinsic miscalibration**。

## Track A/B/C 结果（D_audit，split 互斥）
- Track B det-score：FAIR1M 1.153 / SODA 1.254（反校准，CI 排除 1）。
- **Track C post-hoc selector（D_cal 学→D_audit 验证）：显著改善——FAIR1M 1.153→0.627、SODA 1.254→0.464、DOTA 0.740→0.503；AURC/Risk@70 全面下降**。PSC 问题 = score-proxy mismatch，可由 selector 修复。
- Track A：unavailable（forward dump pending）。
- cliff：near-square vs well-defined p99 delta ~81.6°（主要 near-square 几何退化，trivial）；well-defined p99 ~8.3°（modest 真实问题空间）。

## P3 是否建议启动
- **有条件建议启动**：作为 **unified-proxy / post-hoc selective-orientation 路线**（Track C 在 held-out 显著改善）。**不**建议立项为 intrinsic-only（Track A 未验证）或 near-square-only（trivial）。
- 最小首步 = **PSC forward dump 提取 Track A**（现有 checkpoint，不训练），判别 angle-head 机制 vs score-proxy mismatch。

## 验证/test/git
- verifier `106_verify_p3_feasibility_gate_037` → VERIFIED 14/14；pytest 264 passed；thresholds/split 未变；git 0 大文件。

## 需合作者批准
- PSC Track A forward dump；P3 作 post-hoc/unified-proxy 路线立项；Track C 是否扩更多 detector/dataset。

👆👆👆👆👆👆
