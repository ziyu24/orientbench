👇👇👇👇👇👇

# OrientBench v2 — 045 Measure→Diagnose→Fix 论文主稿 完成

- **045 完成**。无 GPU/训练；未改 thresholds(b7c4e649)/P1 split；未补 full matrix；未恢复 P2；未追 DOTA mAP。
- **主文稿（唯一人读）**：`measure_fix_v2/docs/orientation_reliability_measure_diagnose_fix_draft.md`

## 本文到底在做什么
- 把"旋转检测朝向是否可信"做成可测量(P1: NRC/reliability cliff)、可诊断(PSC 双重反校准机制候选)、可初步修复(P3: reliability-aware selector)的问题。非 detector 训练论文。

## 为什么没有大规模 GPU 训练
- 研究对象是 reliability measurement/diagnosis/selection；大规模重训会混淆变量；已有 checkpoint 足够；selector 是轻量后处理；GPU 仅 inference/TTA/forward dump，不追 mAP。

## 顶刊点在哪里
- ① NRC 独立于 accuracy 的可靠性维度(Spearman -0.046)；② aspect-ratio reliability cliff；③ PSC detection-score(FAIR1M/SODA 显著) + intrinsic phase_mod(3/3 NRC>1) 双重反校准机制候选；④ deployable reliability-aware selector candidate(G2''/Deployable/Route-C/real TTA 4 cells/3 datasets)。

## 是否存在过度宣称
- 无。核心结论均有 bootstrap CI + 可复算 artifacts；明确标 candidate/limited/pending；含 claim ledger(allowed/qualified/forbidden)。未声称 full project/P3 final/顶会 ready/PSC angle head 最终证明反校准。

## 是否建议进入合作者审核
- **建议进入合作者审核**（主稿含合作者审核摘要 + 10 节 + why-no-GPU + claim ledger + 图表计划）。

## 验证/test/git
- verifier `verify_measure_diagnose_fix_draft_045` → 见下；pytest 全过；thresholds/split 未变；git 0 大文件。

👆👆👆👆👆👆
