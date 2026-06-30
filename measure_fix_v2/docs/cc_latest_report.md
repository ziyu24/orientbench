👇👇👇👇👇👇

# OrientBench v2 — 046 Claim Cleanup + Route-C Boundary + TTA Extension 完成

- **046 完成**。未训练 detector；未改 thresholds(b7c4e649)/P1 split；未补 full matrix；未恢复 P2；未追 DOTA mAP；未改原 dataset。
- **五个文件**：docs/{claim_language_cleanup_report, route_c_dataflow_audit, diagnose_predicts_fix_boundary, real_tta_non_psc_extension, track_a_mechanism_boundary}.md（并镜像 measure_fix_v2/docs/）。

## Route-C 接缝裁决
- **source-supervised selector + target GT-free inference**（leave-* 无 target GT，无泄漏）。**非 fully GT-free，非 deployable method complete**。standalone consistency proxy 才是较弱的 fully-GT-free 方向。措辞已更正。

## predictive-boundary 是否成立
- **未成立（本轮）**。oracle_gain↔retained 相关(0.87)**循环**（retained 含 oracle_gain 分母）；非循环检验无预测力（Spearman 0.02）。→ measure→diagnose→fix 写**并列结构**；**DOTA #20 仍是 limitation，非 validation**。

## non-PSC real TTA 扩展结果
- 新增 **RTMDet/DIOR（realTTA 0.331）+ ORCNN/FAIR1M（0.537）**，2 非 PSC family × 2 dataset，**均 beat size-linear 且 beat geometry-only，无失败**。real TTA 现 6 cells/3 datasets/3 families。SODA ORCNN #4(304k) 过慢未完成=next-step。

## Track A 边界结论
- 机制支线：phase_mod intrinsic signal supports a mechanism candidate；不决定主线/venue，不恢复 P2，不写 angle head definitively broken；DOTA #20 不调参。

## 是否需要降级 deployable claim
- **不降级为 upper-bound**（无 target GT 泄漏），但**措辞更正**为 source-supervised + target GT-free inference deployable candidate（非 fully GT-free / 非 method complete）。

## 验证/test/git
- verifier `108_verify_claim_routec_boundary_046` → 见下；pytest 全过；thresholds/split 未变；git 0 大文件。

## 下一步建议
- 补 SODA ORCNN #4 等剩余 non-PSC real TTA；构造 D_cal-only diagnose predictor（非循环）；method 正文写作。

👆👆👆👆👆👆
