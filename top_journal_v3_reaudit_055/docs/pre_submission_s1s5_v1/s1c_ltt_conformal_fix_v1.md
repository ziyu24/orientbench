# S1c —— 保证层技术修正 (v1)

> 数据：`reports/pre_submission_s1s5_v1/s1c_ltt_conformal_tables_v1.csv`。D_calib 标定→D_audit 审计（fit≠calib），masked ar≥1.6，δ=0.1。

## 三项修正

### (1) LTT 固定序列（替代 grid + 逐点 Hoeffding UCB，控 FWER）
候选阈值按覆盖从低到高排成固定序列，顺序检验 H0:R≥α，首次不能拒绝即停；保留最高覆盖的有效 λ。indicator（尾部）用 **精确二项检验**（valid 且比 Hoeffding 紧）；均值用 Hoeffding。

### (2) 均值风险有界严格保证
角度误差有界于 [0°,90°]，均值损失有界 → Hoeffding 以 B=90 缩放即为**严格保证**（非近似）。删除“均值损失无界只能近似保证”的旧错误表述。

### (3) image-level clustered bootstrap
split 为 image-level，risk 按 instance 统计；主审计给 **image 级聚类 bootstrap CI**，正文承认 instance-level exchangeability 假设。

## 结果（LTT 有效保证）
尾部 P(err>5°)（二项 LTT）：
| cell | α=0.05: LTT / cov / emp / img-CI | 说明 |
|---|---|---|
| DIOR#22 | PASS / 0.827 / 0.055 / [0.047,0.064] | 点估计轻微 overshoot，CI 跨 0.05 |
| DIOR#3 | PASS / 0.888 / 0.055 / [0.047,0.064] | 同上 |
| DIOR#61 | PASS / 0.896 / 0.054 / [0.048,0.061] | 同上 |
| SODA#4 | PASS / 0.066 / 0.048 / [0.040,0.058] | 合规（大 n_calib，界紧） |
| FAIR1M#24 | **FAIL** | detection score 无法在该保证下控尾部 |
| SODA#23 | **FAIL** | 同上 |

均值 P(mean err≤α)（Hoeffding B=90）：**全部 FAIL**（α=1.5/2.0°）。

## 裁决（诚实）
- **LTT 有效保证比早期乐观版弱得多**：
  - 尾部保证在 detection 已强 cell（DIOR）成立，但点估计有轻微 overshoot（有限样本，CI 跨 α）；在 detection 弱 cell（FAIR1M/SODA#23）以 detection score **失败**——需改用 geometry selector（S1b 显示 geometry 在这些 cell 覆盖显著更高）。
  - **有界均值保证（Hoeffding B=90）过于保守，在 1.5–2° 预算下不可用**（90° 量程使半径远大于预算）。这是 conformal 均值角度保证的真实局限，应如实写。
- P2 保证层由此定位为：**有效的有限样本尾部风险控制协议**（indicator loss + 二项/LTT），但保证 **modest 且 cell-dependent**；均值角度的严格保证不实用。**不得写成干净的普遍保证。**
- S1c = **qualified pass**（技术修正到位；保证真实但弱）。
