👇👇👇👇👇👇

# OrientBench v2 — 039 G2_double_prime + Deployable 完成

- **039 完成**。无 detector 训练/full matrix/Track A dump；thresholds(b7c4e649)、P1 D_cal/D_audit、formal 标签、frozen tag 未改；DOTA train/val。
- 新阶段独立工作区 `measure_fix_v2/` 已建；输入文件 CLAUDE (8).md + 项目执行文件_v2_measure_fix.md 已复制到 docs/input/。
- **主报告（唯一人读）**：`measure_fix_v2/docs/g2_double_prime_and_deployable_report.md`

## G2_double_prime 裁决：**PASS（明确、稳健）**
- 固定 box-size 分箱内，nonlinear geometry-aware selector **仍显著优于 score+ar+size 线性基线**（D_audit；7 cells × 每个 size bin DELTA CI>0，21/21 primary；ar1.3/2.0 sensitivity 20-21/21）。
- → orientation-specific 非线性几何可靠性结构真实，**非 box-size prior**；含 3 个非 PSC sanity cell 方向一致。

## Deployable 裁决：**PARTIAL-PASS**
- 无目标域 GT 标定：**9/11 unseen-cell 评估** nonlinear 显著优于 score-only 且优于 size-linear，**保留 within-target oracle gain ~69%**。
- leave-dataset 3/4（DIOR/FAIR1M/SODA✓，DOTA✗）；leave-detector PSC↔非PSC 6/7✓（near-oracle）；**唯一例外 DOTA #20**（结构最弱、未显著反校准）。

## 关键指标摘要
- G2DP pooled-cell 示例（primary，NRC）：SODA PSC score 0.982 → size-linear 0.611 → **nonlinear 0.389**；FAIR1M 0.896→0.758→**0.519**。
- Deployable 示例（无目标 GT）：PSC→SODA-ORCNN nonlinear 0.419（oracle 0.399）。

## 是否触发停止条件
- **否**。G2DP 未 fail；Deployable 非 fail（partial-pass）。未声称 P3 顶会级别 / CVPR-ICCV ready；严格区分 upper-bound(G2DP) vs deployable(leave-*) 。

## P1 硬债
- **已完成修订建议**（measure_fix_v2/docs/p1_hard_debt_patch_notes.md）：within-dataset NRC headline、PSC cell-level、GV 定义、related work、持久化、治理下沉。

## 下一步建议
- 待批准：扩 leave-dataset/detector + 路线 C（TTA proxy 无 GT）巩固 deployable；之后再考虑 Track A forward dump（本轮未启动）。venue 决定交合作者。

## 验证/test/git
- verifier `verify_measure_fix_v2_039` → 见下；pytest 全过；thresholds/split 未变；git 0 大文件（artifacts/logs gitignored）。

👆👆👆👆👆👆
