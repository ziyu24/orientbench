👇👇👇👇👇👇

# OrientBench v2 — 040 P3 Deployable Hardening 完成

- **040 完成**。无 detector 训练/full matrix/Track A dump；thresholds(b7c4e649)、P1 split、formal 标签、frozen tag 未改；未恢复 P2；未追 DOTA mAP。
- **主报告（唯一人读）**：`measure_fix_v2/docs/p3_deployable_hardening_report.md`

## Deployable hardening 裁决：**STABLE-PASS（with DOTA #20 documented limitation）**
- ≥75% beat size-linear：all 12/14=85.7%，**非 DOTA 12/12=100%**；retained gain 非 DOTA mean 0.645/median 0.656（all-cells mean 0.481 仅因 DOTA 两负值，差 0.02，提请确认）；LD 6/7 & LDET 6/7 两类均 stable 无 fail；DOTA 已诊断标局限；全程无目标 GT。

## leave-dataset 结果
- 6/7 pass（DIOR/FAIR1M/SODA ✓；DOTA ✗），retained 0.63-0.79。

## leave-detector 结果
- 6/7 pass，PSC→非PSC 3/3（SODA-ORCNN retained 0.946），非PSC→PSC 3/4（DOTA ✗）。

## TTA/proxy 结果
- GT-free local-angle-consistency proxy 在 FAIR1M/DIOR 上优于 score-only 且 < random → route-C 可行；完整 TTA 推理为 next-step（limitation）。

## DOTA #20 failure 原因
- **弱内在结构**：within-target oracle_gain 0.155（四 PSC 最低），masked NRC 0.84 未显著反校准；非样本量/分布 shift/过拟合主因 → documented limitation。

## 是否允许 Track A
- **可有条件准备**（前置满足），本轮未启动；待监督员批准作机制支线（非阻塞）。

## 是否允许 P3 method development
- **支持推进**（deployable reliability-aware selector）。边界：当前仍 source-trained(用 source GT)；route-C GT-free 仅 offline 弱版。**不声称 deployable method 已完成 / 顶会级别**。首步=巩固 route-C TTA + 扩覆盖 + 处理弱结构 cell。

## 验证/test/git
- verifier `verify_deployable_hardening_040` → 见下；pytest 全过；thresholds/split 未变；git 0 大文件（artifacts/logs gitignored）。

👆👆👆👆👆👆
