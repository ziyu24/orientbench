# M4：风险事件定义

- 冻结主事件：`angle_error_le90 > delta_theta_0.75(aspect_ratio)`；角度采用 le90 长边朝向、pi 周期，几何模型为共中心、同尺度、全等矩形。
- 数值求解为确定性多边形 IoU 二分，角度容差 0.001 度；冻结定义未变（frozen_at=2026-07-12 20:14:39 -0700，derived_ar@15deg=2.15）。
- 查找表扩展至 ar=1024.0；ar>8 不再钳制到 ar=8；超表范围采用 `conservative_inverse_ar_tail_minus_2solve_tol`。本次主区 ar>8 共 2931 条，超表范围 0 条。
- direct-solve 稳定性见 `m4_delta_theta_direct_solve_stability.csv`；观测 AR 支持域见 `m4_observed_ar_numerical_stability.csv`；输入 lineage 见 `m4_input_lineage_audit.csv`，partial/wrong-split 输入会在正式表写入前失败。
- 主口径唯一为 ar>=2.1；固定角度 >5 度（fine-risk）、>10 度、>15 度仅作敏感性。
- 主掩码与几何归一化事件中的 aspect ratio 均来自 matched GT box；选择器侧预测几何与此评估几何分开记录。
- FAIR1M/SODA-A 的固定角度结果均作 dataset-level noise-sensitive 标记，其中 5 度阈值接近 proxy floor。corner-jitter 仅为 proxy，不是 sigma_gt、不是人工双标，不进入风险阈值定义。

## Geometry-normalized 主风险（ar>=2.1）
| cell | dataset | n | severe rate | mean error | p90 | delta@ar2.1 | n(ar>8) |
|---|---|---:|---:|---:|---:|---:|---:|
| A | DIOR-R | 49502 | 0.0081 | 1.719 | 4.313 | 15.33 | 306 |
| B | DIOR-R | 54297 | 0.0082 | 1.897 | 4.429 | 15.33 | 677 |
| C | DIOR-R | 53671 | 0.0167 | 2.183 | 4.73 | 15.33 | 647 |
| D | FAIR1M-v1.0 | 31801 | 0.0052 | 2.269 | 5.161 | 15.33 | 177 |
| E | SODA-A | 197529 | 0.0036 | 2.029 | 4.669 | 15.33 | 110 |
| F | SODA-A | 235428 | 0.0053 | 2.28 | 5.172 | 15.33 | 125 |
| G_dota_orcnn | DOTA-v1.0 | 33029 | 0.0019 | 1.834 | 4.036 | 15.33 | 419 |
| H_dota_rtmdet | DOTA-v1.0 | 34383 | 0.0029 | 1.814 | 3.93 | 15.33 | 470 |

## 固定角度敏感性（ar>=2.1）
| cell | dataset | >5deg | >10deg | >15deg | 5deg noise-sensitive |
|---|---|---:|---:|---:|---|
| A | DIOR-R | 0.0725 | 0.0097 | 0.0034 | False |
| B | DIOR-R | 0.0772 | 0.0104 | 0.0036 | False |
| C | DIOR-R | 0.0896 | 0.0191 | 0.0091 | False |
| D | FAIR1M-v1.0 | 0.1088 | 0.0098 | 0.0015 | True |
| E | SODA-A | 0.0854 | 0.0101 | 0.0019 | True |
| F | SODA-A | 0.1079 | 0.0142 | 0.0028 | True |
| G_dota_orcnn | DOTA-v1.0 | 0.0555 | 0.0034 | 0.0005 | False |
| H_dota_rtmdet | DOTA-v1.0 | 0.0503 | 0.0035 | 0.001 | False |



<!-- HUMAN_073_START -->
## 真人双标噪声锚点

三数据集各 200 个独立互盲目标构成 600 个 primary 目标，其中 450 对双方均给出数值角度。180° 周期圆周分歧的均值为 2.3112°（按源图像聚类自助法 95% 区间 1.9970°–2.7854°），中位数为 1.6359°，p90/p95 为 4.4220°/5.9359°；P(>5°)=8.00%，P(>10°)=0.89%。ar≥2.1 子集含 308 对，均值 2.2823°，P(>5°)=6.82%，P(>10°)=0.65%。因此 5° 是有实际意义但对标签噪声敏感的 fine-risk，10° 具有更清楚的 severe-risk 人工噪声余量；SODA-A 的人工分歧尾部较高，固定角度结论需更克制。人工分歧不等于数据集真实 GT error，也不作为从模型误差中扣除的校正项。corner-jitter 只保留为独立 proxy sensitivity，不能替代真人锚点。
<!-- HUMAN_073_END -->

