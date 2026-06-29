# PSC Track A / B / C control (037)

> 2026-06-29 15:51:43 CST · 现有 checkpoint 离线 selector 对比，无训练。split 互斥（assign_split 确定性 md5），selector 仅在 D_cal 学，D_audit 验证；**未改 frozen DOTA D_cal/D_audit/thresholds**（此处为 cross-dataset PSC cells 的 exploratory 应用）。masked well-defined region。

## 结果（D_audit）
| cell | track | NRC (95% CI) | Risk@70 | AURC (oracle) |
|---|---|---|---|---|
| DIOR #22 | B det-score | 0.557 [0.53,0.59] | 1.49 | 1.18 (0.41) |
| DIOR #22 | C post-hoc | 0.510 [0.46,0.59] | 1.32 | 1.11 |
| DOTA #20 | B det-score | 0.740 [0.69,0.80] | 2.11 | 1.83 (0.79) |
| DOTA #20 | C post-hoc | 0.503 [0.47,0.54] | 1.74 | 1.49 |
| FAIR1M #24 | B det-score | **1.153 [1.07,1.23]** | 2.70 | 2.97 (0.80) |
| FAIR1M #24 | C post-hoc | **0.627 [0.59,0.67]** | 2.24 | 1.98 |
| SODA #23 | B det-score | **1.254 [1.23,1.28]** | 2.60 | 3.07 (0.72) |
| SODA #23 | C post-hoc | **0.464 [0.45,0.48]** | 1.85 | 1.59 |
| 全部 | A intrinsic | **unavailable**（saved preds 无 angle logits；需 forward dump） | — | — |

## 判定
- **Track A**：unavailable → **不能声称 PSC angle-head intrinsic miscalibration**。
- **Track B**：det-score 作 selection 在 **FAIR1M/SODA 反校准（NRC>1，CI 排除 1）**。
- **Track C post-hoc selector**：在 held-out D_audit 上**显著改善**——FAIR1M 1.15→0.63、SODA 1.25→0.46（反校准→良校准），AURC SODA 3.07→1.59、FAIR1M 2.97→1.98；所有 cell NRC/Risk@70/AURC 均下降。
- **结论**：PSC 问题 = **score-proxy mismatch**（detection-score 不适合作 PSC orientation selection），且**可由 post-hoc selector 修复** → **P3 selective-orientation route 有希望**。

## 诚实 caveat
- Track C selector 特征含 score + log(aspect_ratio) + w + h，部分增益来自 **degeneracy-awareness（几何）**；但其在 held-out 上修复 PSC 反校准是真实的。
- Track A intrinsic 仍 pending（forward dump）；若 Track A 也反校准，机制线（angle-coder）成立；若 Track A 正常，则 PSC 问题确为 score-proxy mismatch。
