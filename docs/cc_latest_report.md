👇👇👇👇👇👇

# OrientBench — 036 P1 中文论文标准审稿稿 完成

- **036 完成**。无新增训练/GPU、thresholds 未变（b7c4e649）、D_cal/D_audit split 未变。无期刊/会议名称。
- **主文档（唯一人读）**：`docs/orientbench_p1_chinese_paper_draft.md`（论文标准结构，11 节 + 附录 A-F + 图表占位）。

## bootstrap CI 是否完成
- **完成**。PSC + 对照 family masked NRC bootstrap CI（1000×）：**FAIR1M PSC [1.027,1.134]、SODA PSC [1.238,1.281] 显著>1**；**DOTA PSC 0.840 [0.787,0.900] 不显著**（修正此前 unmasked 1.06 为 near-square 驱动）；DIOR PSC 0.55。对照 orcnn/lsknet/rtmdet 全<1。数据：fig3_psc_nrc_ci_data.csv / nrc_bootstrap_ci.json。

## 三张核心图数据路径
- 图1 cliff：`outputs/bench_core/reports/fig1_reliability_cliff_data.csv`
- 图2 CDF：`outputs/bench_core/reports/fig2_angle_error_cdf_data.csv`
- 图3 PSC NRC+CI：`outputs/bench_core/reports/fig3_psc_nrc_ci_data.csv`

## persistent artifacts 是否可复算
- **可复算**。8 key cells（DOTA #20/rhino、DIOR 3/22/47/16、FAIR1M 24、SODA 23）持久化 outputs/persistent_artifacts/orientbench_v2/（gitignored）+ manifest（sha256+生成命令+can_recompute）。⚠️ /dev/shm 非持久已写明。

## claim ledger 是否完成
- **完成**：p1_claim_ledger_final.md（allowed/pending/forbidden）+ license_reproducibility_notes.md。

## 验证/test/git
- verifier `105_verify_p1_chinese_paper_draft_036` → VERIFIED 19/19；pytest 全过；thresholds 未变；git 0 大文件（figures/persistent gitignored）。

## 是否建议交合作者审核
- **建议交合作者审核**（单文档可直接阅读）。

## 下一步是否等待 PSC Track A/B control 批准
- **是**。核心机制主张 pending PSC Track A vs Track B control（angle-head control experiment，需批准+算力）；P3 推进取决于 cliff + PSC control 结果。

👆👆👆👆👆👆
