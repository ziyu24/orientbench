# P3 G2′ feasibility-to-method 判定报告

> SUPERVISOR_APPROVED_038 · 无 detector 训练 · 无 full matrix · 无 Track A forward dump · 不追公开 mAP（DOTA train/val）· P1 thresholds(b7c4e649)/D_cal/D_audit 未改。
> 合作者可读单文件。本轮仅 G2′ 判定，非 P3 方法开发。

## 1. G2′ 问题定义
P3 = reliability-aware orientation selection：学一个 orientation reliability selector 判断 OBB detector 角度预测是否可信。
**G2′ 判定问题**：在 well-defined 区域，**非线性 geometry-aware selector 是否显著优于 score+aspect-ratio 线性项**？若是，则存在非线性、orientation-specific 几何可靠性结构（非 trivial near-square、非 trivial 线性 ar）。

## 2. 数据 split
- cells（PSC score-proxy 反校准相关）：DOTA #20、DIOR #22、FAIR1M #24、SODA #23，及 pooled。
- **D_cal / D_audit 互斥**（assign_split 确定性 md5）；selector 仅在 **D_cal** 学，**最终判定只看 D_audit**；未用 D_audit 调参。
- 使用现有 matched predictions（persistent artifacts / scratch schema），无新推理。

## 3. well-defined 区域定义（跑前冻结）
- **primary：aspect ratio ar ≥ 1.6**。
- sensitivity：ar ≥ 1.3；补充 ar ≥ 2.0。
- near-square（ar 接近 1）**不进入主分析**。阈值跑前冻结，未因结果改动。

## 4. 三类模型对照
- **baseline 1 — score-only**：selection score = detection score（单调校准不改 rank，故等价原始 score 的 NRC/AURC）。
- **baseline 2 — score + ar 线性**：LinearRegression([score, log_ar]) → 预测 angle error → selection = −pred。检验"是否只是 ar 线性解释"。
- **P3 selector — 非线性 geometry-aware**：GradientBoosting([score, log_ar, sqrt_area, gv_obb_needed, w, h])，n_estimators=200/max_depth=3/lr=0.05/subsample=0.8，**random seed 固定**。

## 5. 特征与标签定义
- 特征：detection score、log aspect-ratio、sqrt(area)、GV-obliquity(gv_obb_needed)、box w、box h。**未用 dataset id**（避免捷径）。
- **标签：matched pair 的 canonical long-side angle error（连续 risk）**。NRC/AURC 以 selector score 降序排序计算。标签跑前定义，未换。

## 6. NRC / AURC / Risk / tail error（D_audit，primary ar≥1.6）
| cell | selector | NRC | AURC | Risk@70 | p99@70%cov |
|---|---|---|---|---|---|
| POOLED | score-only | 0.838 | 1.911 | 2.016 | 10.45 |
| POOLED | score+ar linear | 0.626 | 1.603 | 1.877 | 9.18 |
| POOLED | **P3 non-linear** | **0.409** | **1.290** | **1.630** | **7.80** |
| DOTA #20 | score+ar linear / **P3** | 0.698 / **0.547** | 1.60 / **1.43** | 1.75 / **1.69** | 6.57 / **6.47** |
| DIOR #22 | score+ar linear / **P3** | 0.669 / **0.354** | 1.21 / **0.845** | 1.33 / **1.12** | 6.93 / **6.57** |
| FAIR1M #24 | score+ar linear / **P3** | 0.760 / **0.520** | 2.00 / **1.62** | 2.26 / **2.06** | 9.59 / **8.80** |
| SODA #23 | score+ar linear / **P3** | 0.618 / **0.389** | 1.62 / **1.29** | 1.89 / **1.64** | 9.15 / **8.13** |

## 7. bootstrap CI（核心判定：P3 vs score+ar linear，DELTA = NRC_linear − NRC_p3，>0 表示 P3 更优）
| cell | DELTA median | 95% CI | P3 显著更优 |
|---|---|---|---|
| **POOLED** | **0.217** | **[0.211, 0.221]** | **是** |
| DOTA #20 | 0.150 | [0.131, 0.171] | 是 |
| DIOR #22 | 0.314 | [0.288, 0.339] | 是 |
| FAIR1M #24 | 0.239 | [0.217, 0.263] | 是 |
| SODA #23 | 0.230 | [0.223, 0.236] | 是 |
- 500× bootstrap（重采样 D_audit，selector 固定）。**所有 cell + pooled 的 DELTA CI 均明确 >0**。

## 8. ar 阈值 sensitivity
- ar≥1.3 与 ar≥2.0 下结论**一致**：所有 cell + pooled 的 P3 vs linear DELTA CI 均 >0（pooled ar1.3 DELTA 0.199 [0.193,0.205]；ar2.0 DELTA 0.230 [0.224,0.236]）。判定对 well-defined 阈值稳健。

## 9. feature importance（permutation，MAE）
- 主导特征 = **box size（w/h/sqrt_area）**（w 0.54–1.86，h 0.31–1.72）+ GV-obliquity（0.02–0.25）。
- **log_ar importance 很小（0.02–0.08）**，score 也小（0.007–0.09）→ **P3 增益不是来自 aspect-ratio 或 score**，而是非线性 size/几何结构。
- 旁证：DIOR 上 score+ar 线性（0.669）甚至**劣于** score-only（0.563），而 P3（0.354）显著优于两者 → 线性 ar 非但不够，有时有害；非线性几何才有效。

## 10. G2′ 裁决
**G2′ PASS（明确、稳健）。**
- 在 well-defined 区域（ar≥1.6，near-square 已排除），**非线性 geometry-aware selector 在 held-out D_audit 上显著优于 score+aspect-ratio 线性项**（所有 cell + pooled，bootstrap CI 排除 0），且对 ar 阈值稳健。
- 解释：**存在非线性、orientation-specific 几何可靠性结构**（主要由 box size + GV-obliquity 驱动），非 trivial near-square、非 trivial 线性 ar。

## 11. 下一步建议（pass 分支）
- 允许进入 **P3 G1/G3/G4**：泛化（跨 detector/dataset/host）、部署性（无 GT 标签的可部署变体）、稳健性。
- 允许启动 **Track A forward dump**（现有 checkpoint，不训练）探索机制解释：PSC angle-head intrinsic 是否也反校准。
- 优先验证 **可部署性**：当前 P3 selector 用 GT angle error 在 D_cal 训练，是 **post-hoc / upper-bound** 估计，**非可部署方法**；G1/G3 需做无 GT 监督信号的 deployable 变体。

## 12. 禁止外推声明
- 本轮**未声称** P3 已成立 / 已具备顶会级别。
- 当前 P3 selector 为 **upper-bound post-hoc 估计，非 deployable method**（依赖 D_cal 的 GT angle-error 标签）。
- 增益**不是** near-square trivial gain（主分析在 ar≥1.6 well-defined 区），**不是**线性 ar（log_ar importance 极小）。
- **未**改 thresholds / P1 split；**未**训练 detector；**未**扩 full matrix；**未**做 Track A forward dump；DOTA 仍 train/val 非公开 test。
- 产物：p3_g2prime_results_038.{csv,json}（全 cell × 3 ar 阈值 × 3 selector + DELTA bootstrap + permutation importance）。
