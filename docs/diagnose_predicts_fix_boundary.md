# Diagnose → Fix Predictive-Boundary 分析 (046)

> 2026-06-30 14:50:00 CST。称 predictive boundary（非因果链）。**纪律：不得用 D_audit 结果当 predictor 再解释 D_audit gain；oracle_gain 仅解释性上界。**

## 数据
- cell-level 表（14 unseen-cell evals，leave-dataset + leave-detector，040）：diagnose_predicts_fix_boundary.csv。
- 列：cell / mode / detector / is_dota / diagnose_oracle_gain / diagnose_score_nrc / diagnose_phase_mod_nrc / outcome_retained / outcome_beats_sizelin。

## 关键发现与循环论证排查
1. **circular（无效）**：Spearman(oracle_gain, outcome_retained)=0.868（p=0.0001）。**但 retained=(NRC_score−NRC_deployed)/(NRC_score−NRC_oracle)=…/oracle_gain，oracle_gain 在分母 → 循环**。**该相关无效，不得作 predictive 证据。**
2. **non-circular**：以 **abs_deployed_gain=NRC_score−NRC_deployed**（不含 oracle）为 outcome：
   - Spearman(oracle_abs, abs_deployed_gain)=**0.018（p=0.95）** → oracle **不预测**绝对 gain。
   - Spearman(score_nrc, abs_deployed_gain)=0.70 → 但 score_nrc 为 D_audit，且 "score 已差→可改空间大" 为**机械关系**，非干净的 diagnose-predicts-repairability。
3. **无干净 source-side（D_cal）predictor 建立**（本轮未做 D_cal→D_audit/unseen 的非循环预测）。

## DOTA #20（全 cell 统计纳入）
- DOTA diagnose_oracle_gain=0.155（最低）、abs_deployed_gain=[−0.006,−0.151]（负，beats_sizelin=False，两 eval 均失败）。
- **描述性**：DOTA detection-score 已较良校准（NRC 0.70），selector 可改空间小 → 增益集中在 detection-score 反校准的 PSC FAIR1M/SODA。
- **但**：因 (1) 循环、(2) 非循环检验无预测力，**不能把 DOTA 失败包装成 framework 的 validation**。

## 判定：**predictive boundary 未成立（本轮）**
- 强相关循环；非循环检验无预测力；无干净 source-side predictor。
- 故：**measure → diagnose → fix 写成并列结构（parallel），不写 "framework predicts repairability boundaries"**。
- **DOTA #20 仍是 limitation，不是 validation**。
- next-step（若要建立 predictive boundary）：构造 **D_cal-only diagnose 指标**（如 D_cal 内 score-NRC / phase_mod / 退化比例）预测 **unseen-target 绝对 gain**，leave-one-cell-out + permutation，n 仍小须谨慎。
