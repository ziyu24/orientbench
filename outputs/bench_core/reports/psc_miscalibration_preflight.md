# PSC 反校准 preflight（轻量归因）

> 2026-06-29 13:19:53 CST

## 当前只能说（Track B）
> **detection-score 作为 orientation selection score 时，在 PSC family 上表现反校准**（NRC>1）。
**不能**说 PSC angle head 本身反校准（需 Track A intrinsic / angle-head control）。

## 数据
- PSC NRC（4 datasets）：DIOR 0.549 / DOTA 1.057 / FAIR1M 1.083 / SODA 1.260。3/4 数据集 NRC>1（mean 1.133）。
- PSC 反校准延伸到 well-defined region：SODA ar 1.6-2.0 NRC=1.18；FAIR1M ar 1.0-1.6 NRC ~1.1-1.17（非仅近方形 artifact）。
- vs ORCNN/LSKNet/RTMDet：同数据集这些 family NRC<1（DOTA orcnn 0.57/lsknet 0.71/strip 0.72），唯 PSC>1。

## 三轨口径
- Track A intrinsic：PSC 有原生 angle classification 置信，但本项目未提取其 native uncertainty → **pending**。
- Track B detection-score proxy：当前 NRC 主口径，PSC 反校准成立。
- Track C post-hoc selector（D_cal→D_audit 上界）：DOTA C1/A4 已用该思路（formal）；PSC-specific 上界 **pending**（可轻量做但本轮未做）。

## 判断
- PSC 反校准在 Track B 下**稳定**（跨 3 数据集 + 延伸到 well-defined region）。
- **足够申请 angle-head control experiment**（确认是 angle head 还是 score head 归因）；但**现在不启动大训练**（边界）。
