👇👇👇👇👇👇

# OrientBench v2 — 048 正式论文中文稿 完成

- **048 完成**。无实验/GPU/训练；未改 thresholds(b7c4e649)/P1 split；未补 full matrix；未恢复 P2；未追 DOTA mAP。
- **主文稿（唯一人读）**：`measure_fix_v2/docs/orientation_reliability_paper_zh_full.md`

## 是否包含正式论文完整结构
- **是**：标题 + 中文摘要 + 关键词 + 引言 + 相关工作 + 问题定义与协议 + OrientBench 协议 + Measure + Diagnose + Fix + 实验结果 + 图表占位 + 讨论 + 局限 + 结论 + 附录 A–J + 合作者审稿重点。

## 是否包含核心数据表
- **是**：表 1–10（覆盖、NRC 构造效度、cliff/tail、PSC preflight+Track A、G2_double_prime、Deployable、Route-C real TTA、non-PSC leave-*、supervision spectrum、blockers）。数字均来自已有 report/csv/json。

## 是否包含图表占位
- **是**：Fig.1–9（图题/图注/数据路径/支持/不支持），不实际绘图。

## 是否无 forbidden claims
- **是**：无 venue 名/会议级就绪话术；无 full project complete / P3 final method complete / NRC strictly independent / PSC angle head finally proven broken / DOTA #20 validation；source-supervised 明确**非 fully GT-free**；DOTA #20 = limitation。

## 是否建议交合作者审稿
- **建议交合作者审稿**（文末含审稿重点 7 条）。

## 验证/test/git
- verifier `verify_paper_zh_full_048` → 见下；pytest 全过；thresholds/split 未变；git 0 大文件。

👆👆👆👆👆👆
