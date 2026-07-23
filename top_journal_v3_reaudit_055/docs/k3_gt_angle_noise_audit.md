# K3 GT 角度噪声审计（066，proxy 版）

> 目的：确认 5° 尾部预算、1.5–2° 均值预算是否高于标注噪声地板。无人工双标 → 用 **corner-jitter refit
> proxy**：对每个采样 GT 框重建四角点，加 σ=2px 高斯角点抖动（标注精度），cv2.minAreaRect 重拟合 le90
> 长边角，重复 30 次，角度 std = 该实例角度噪声地板 σ_gt。脚本 `scripts/k3_gt_angle_noise_proxy_audit_066.py`；
> 数据 `reports/k3_gt_angle_noise_by_dataset.csv`、`reports/k3_gt_angle_noise_by_ar_size_class_066.csv`。
> **未改 thresholds.yaml / D_cal / D_audit。** 每数据集抽样 500 实例。

## 结果（σ_gt，度）
| 数据集 | 全体 mean | 全体 P(>5°) | **masked ar≥1.6 mean** | masked p90 | **masked P(>5°)** |
|---|---|---|---|---|---|
| DIOR-R test | 9.6 | 0.33 | **3.48** | 7.07 | 0.158 |
| FAIR1M val20 | 7.7 | 0.43 | **5.73** | 13.9 | 0.380 |
| SODA-A val | 9.9 | 0.50 | **7.81** | 19.2 | 0.453 |
（按 ar/size/class 细分见 `..._by_ar_size_class_066.csv`；小目标数据集 σ_gt 更大——2px 抖动相对小框更显著。）

## 必答问题
- **σ_gt 是否接近 2°？** masked ar≥1.6 区 σ_gt ≈ **3.5–7.8°**，**明显高于 2°**（三数据集均是）。
- **P(err>5°) 阈值是否明显高于噪声地板？** DIOR：masked P(σ_gt>5°)=0.16，5° 尾部**尚有 margin**；
  FAIR1M（5.7°）与 SODA（7.8°）：masked mean σ_gt **接近/超过 5°**，5° 尾部预算**margin 很薄甚至为负**。
- **near-square 区是否噪声支配？** 是——全体（含近方形）mean σ_gt 7.7–9.9°、P(>5°) 0.33–0.50，近方形/小目标区
  被标注噪声支配，正是 masked 剔除的动因。

## 判定（依 §4.7）
- **均值预算**：masked σ_gt（3.5–7.8°）**处处高于 1.5–2° 均值预算** → 1.5–2° 均值保证**必须标为
  label-noise-aware**，**不得写成强语义保证**。
- **5° 尾部预算**：DIOR 尚在噪声地板之上（可保留，说明 margin）；**SODA/FAIR1M 的 5° 尾部 margin 薄/为负**
  → 尾部控制在小目标数据集需谨慎，说明其相对噪声地板的 margin。
- **K3 初步判定：PARTIAL（偏 FAIL 于小目标数据集）**。均值预算受噪声影响、须重标；5° 尾部预算 margin
  随数据集而异（DIOR 可保留，SODA/FAIR1M 薄）。

## 重要 caveat 与后续
- 本 proxy 用**独立 2px 角点抖动**，对小/近方形框较激进，**可能高估**真实标注噪声（真实标注误差常相关）。
- **真人双标为后续 blocker**（本轮 proxy 版不空缺，但结论待人工双标确认）。
- 对 P2（保形朝向风险控制）的影响：正文均值风险预算须改写为 label-noise-aware；5° 尾部保留但注明各数据集
  相对噪声地板的 margin。**不修改 frozen thresholds**——仅审计与表述层面处理。
