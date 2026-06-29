# DOTA #20 Failure Analysis (040)

> 2026-06-29 20:55:55 CST。专门分析 039/040 中 DOTA #20 leave-dataset/leave-detector 迁移失败。

## 各 PSC cell within-target 可学习结构（oracle gain = NRC_score − NRC_oracle_within）
| cell | n_audit | median_err | ar_median | NRC_score | oracle_within | **oracle_gain** | spearman(score,err) |
|---|---|---|---|---|---|---|---|
| DOTA-v1.0/20 | 6696 | 1.513 | 2.71 | 0.7035 | 0.5481 | **0.1554** | -0.185 |
| DIOR-R/22 | 10999 | 0.811 | 2.7 | 0.5629 | 0.3563 | **0.2066** | -0.2288 |
| FAIR1M-v1.0/24 | 13796 | 1.832 | 2.34 | 0.896 | 0.5185 | **0.3775** | -0.052 |
| SODA-A/23 | 105343 | 1.43 | 2.34 | 0.9823 | 0.389 | **0.5933** | -0.1215 |

## 结论：**根因 = DOTA #20 PSC 本身可学习 orientation-reliability 结构最弱**
- DOTA #20 oracle_gain = **0.155，为四个 PSC cell 最低**（DIOR 0.207 / FAIR1M 0.378 / SODA 0.593）。即便用 DOTA 自己的 D_cal 训练，within-target 提升也最小 → **没有多少结构可供迁移**，迁移来的 selector 反而引入 mismatch → 迁移为负。
- 与 039 一致：DOTA PSC masked NRC 0.84（**未显著反校准**，CI[0.79,0.90]），是唯一未显著反校准的 PSC cell。
- 非主因：样本量 n=6696（最小但非过小）；ar 分布（2.71，与他者相近）；score↔err 关系（-0.185，与他者同量级）。无明显 size-bin/class shift 主导。
- **判定**：DOTA #20 失败 = **弱内在结构（weak learnable structure）**，非样本量/分布 shift/过拟合主因 → 标为 **documented limitation**（stable-pass 准则 4）。
