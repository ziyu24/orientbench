# OBB Angle Contract v1

> 生成时间: 2026-06-26 09:50:10 CST
> normalization_version=longside_v1  metric_version=orientation_risk_v1

## 问题
le90 表示二义性：(w,h,θ) 与 (h,w,θ+π/2) 描述同一物理矩形。真实 prediction 与 GT 对长短边标注不同，导致 naive angle error ≈88°（实际朝向亚度级精确）。

## 规范化层（非静默改 angle-error 定义）
- 在不变的 π 周期 angle-error 之上加 **long-side canonical orientation** 归一化层（`orientbench/metrics/angle_contract.py`）。
- 规则：long side 方向为准；π 周期；(w,h,θ)↔(h,w,θ+π/2) 等价归零；near-square（长短比 ≤ 1.10）方向不稳定 → near_square mask；退化/非有限 → NaN。
- 双审计字段：`angle_error_raw_le90`（诊断）、`angle_error_canonical_longside`（**正式 orientation risk**）。带 metric_version/normalization_version，不覆盖历史版本。

## 回归测试（tests/test_angle_contract.py, test_orientation_angle.py）
- 等价 polygon / 交换宽高 → canonical ≈0；
- **真实 30° 差异不被压成 0**（canonical=30°）；
- 40×20 @0° vs @90°（垂直）→ canonical ≈90°（真实差异保留）；
- near-square 标记；边界角 π 周期；退化 NaN；真实样本有限性。12 用例全过。

## 结论
canonical long-side 结果作为正式 orientation risk；不会把几何不同方向错误压零。
