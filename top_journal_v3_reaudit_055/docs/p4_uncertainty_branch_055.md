# A4 / P4 —— uncertainty-branch 处理 (055)

> 冻结 masked 协议 ar≥1.6，D_audit NRC(selection score → angle_error)。真实 052 matched + TTA circular variance + PSC phase_mod。GBR selector 仅用 D_cal。数据：`reports/p4_uncertainty_branch_055.csv`、`p4_selector_vs_tta_bootstrap_055.csv`。前置：A0 masked 协议已调和。

## 1. masked NRC（越低越好）
| cell | detection | geometry | tta_circ_var | phase_mod |
|---|---|---|---|---|
| DIOR#22 | 0.562 | **0.520** | 0.534 | 1.128(反校准) |
| FAIR1M#24 | 0.921 | **0.599** | 0.647 | 1.117(反校准) |
| SODA#23 | 0.906 | **0.502** | 0.527 | 1.091(反校准) |
| DIOR#3 | 0.528 | **0.487** | 0.570 | — |
| DIOR#61 | 0.419 | **0.396** | 0.684 | — |
| SODA#4 | 0.706 | **0.505** | 0.948 | — |

## 2. 配对 bootstrap（geometry 减 对手，CI<0 = geometry 显著更好）
- **geometry vs detection：6/6 cell geometry 显著更优**（ΔNRC −0.02 ~ −0.40，CI 全 <0）。
- **geometry vs TTA：5/6 显著更优**（DIOR#22 打平：Δ −0.014，CI [−0.083,0.045]）。
- TTA circular variance 不稳定：DIOR#61(0.684)、SODA#4(0.948) 明显差，SODA#23 好。

## 3. 分支裁决
- masked 协议下 **geometry selector 优势恢复且稳定** → **Fix 故事回归**：推荐默认 = geometry-aware reliability selector（可加 conformal guarantee layer，见 P2 score menu）。
- **TTA + conformal 作 GT-free 后备**：TTA 不需 target GT，但作为 score 不稳定（5/6 弱于 geometry），仅在无法训练 selector 时退而求其次。
- **learning selector 不降为可选**：它是主线（geometry selector 显著且一致）。
- **intrinsic phase_mod 不作 selector**：masked 下反校准（NRC>1），作 selector coverage≈0；它只作为 **机制诊断信号**（A0-3：angle-coder 内在置信度反序），不作可靠性排序。

## 4. checkpoint ensemble（circular variance ensemble）
- 末几个 epoch 的 checkpoint **未持久化保存**（pth_data 仅存 best + last，非多 epoch 序列）→ 无法构造 checkpoint-ensemble circular variance。**标 unavailable，不编造**。现有 TTA circular variance（augmentation 一致性）已覆盖 uncertainty-branch 的 GT-free 变体。

## 5. 与 P2 的关系
P4 不单独成节，**并入 P2 score menu**：conformal guarantee layer + geometry selector = 推荐默认；detection-score / TTA / phase_mod 作对照。P4 的贡献是“选哪个 score 喂 conformal 层”的实证答案（geometry selector）。
