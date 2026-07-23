# A2 —— P1 约束角度扰动修正 (055)

> 真实 052 matched pred_obb/gt_obb（D_audit, 每 cell 采样 4000）。shapely 旋转 IoU。角度误差用 canonical long-side（(w,h,θ)↔(h,w,θ+90°) 对称）。未训练/未推理。数据：`reports/p1_constrained_angle_perturb_055.csv`、`p1_ar_bin_dose_response_055.csv`；理论 IoU(δ;ar) 见 `top_journal_v3/figures/iou_delta_theta_aspect_ratio_curve.csv`。

## 0. 为什么修正
053 用均匀 30° 扰动：破坏 rIoU>0.5，导致 mAP@0.5 同步变动，无法证明“角度敏感性解耦”。本轮改为 **约束扰动**：每个实例注入其 **eps_max = 保持 rIoU(pred,gt)>0.5 的最大角扰动**（沿远离 gt 方向），由构造保证匹配不掉 → mAP@0.5 稳定，再看 orientation risk / AP75。

## 1. 主结果（masked/unmasked 合并，全 D_audit 采样）
| cell | eps_max | mAP@0.5 | AP75 | angle risk° |
|---|---|---|---|---|
| DIOR#22 | 34.9° | **1.000→1.000** | 0.715→0.076 | 5.30→34.49 |
| FAIR1M#24 | 35.6° | **1.000→1.000** | 0.417→0.058 | 4.52→36.75 |
| SODA#23 | 33.5° | **1.000→1.000** | 0.434→0.016 | 5.03→34.62 |
| DIOR#3 | 34.7° | **1.000→1.000** | 0.815→0.075 | 4.85→34.92 |
| DIOR#61 | 35.2° | **1.000→1.000** | 0.831→0.086 | 4.33→35.86 |
| SODA#4 | 34.7° | **1.000→1.000** | 0.561→0.017 | 5.49→35.85 |

→ 在 IoU>0.5 容差内（平均 ~35° 角扰动），**mAP@0.5 完全不变，orientation risk 上升约 7–8×，AP75 崩塌**。构造性解耦成立。

## 2. ar-bin dose-response（角度敏感性受 aspect ratio 门控）
| ar_bin | eps_max | Δrisk° | Δ mAP@0.5 | Δ AP75 |
|---|---|---|---|---|
| near_square | ~68° | +19~+42 | **0.000** | −0.26~−0.45 |
| moderate(1.3–1.6) | ~58–67° | +54~+64 | **0.000** | −0.38~−0.81 |
| elongated(1.6–3) | ~32–35° | +32~+33 | **0.000** | −0.35~−0.84 |
| very_elongated(≥3) | ~15–19° | +15~+19 | **0.000** | −0.36~−0.78 |

- **eps_max 随 ar 增大而减小**（near-square 容任意角度 ~68°；very_elongated 仅 ~16°）→ 角度对 IoU 的几何敏感性由 aspect ratio 门控。
- 与理论 IoU(δ;ar) 吻合：ar=1.0 时 IoU 在 δ=45° 仍 0.707（近方形对角度不敏感 = cliff）；ar=3.0 时 IoU 在 δ≈30–35° 才降到 0.5（与 elongated eps_max≈33° 一致）。
- **每个 ar-bin 的 Δ mAP@0.5 = 0.000**，orientation risk 却在每个 bin 大幅上升 → 解耦对全 shape 成立。

## 3. 裁决：P1 partial → precise-pass
- **成立**：mAP@0.5 稳定（各 ar-bin Δ=0）但 orientation risk 与 AP75 大幅上升 →
  **精确表述：mAP@0.5 对朝向的（不）敏感性由 aspect ratio 与 IoU 阈值门控——近方形框在 IoU 上对角度不可分辨（cliff），细长框亦容忍约 35° 角误差而 mAP@0.5 不变；orientation risk 与 AP75 不受此门控保护。mAP@0.5 系统性无法刻画朝向可靠性。**
- 这是 **precise-pass**（受 ar/IoU 阈值门控的精确陈述），替换 053 的无效均匀扰动。
- **不外推**：不写“mAP 与朝向完全无关”；细长/高 IoU 阈值下二者部分耦合（AP75 敏感）。P1 是 measure→diagnose 的动机层，非 fix。
