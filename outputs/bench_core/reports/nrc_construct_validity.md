# NRC 构造效度（统计补强，措辞修正）

> 2026-06-29 13:19:53 CST。**不写"完全独立"**。

## 措辞（最终）
> 在当前 23-cell 异质矩阵上，**未检测到 NRC 与 mAP 的显著相关**；NRC 提供了**不同于 accuracy 的可靠性信号**。受 n=23 限制，不主张严格独立。

## 数据（n=23）
| 量 | 值 | 95% CI (bootstrap) |
|---|---|---|
| Spearman(NRC,mAP) | -0.0455 (p=0.8368) | [-0.49, 0.481] |
| Pearson(NRC,mAP) | -0.2601 (p=0.2307) | [-0.609, 0.25] |
| partial(NRC,mAP \| dataset) | -0.5669 (df=16) | — |
| partial(NRC,mAP \| family) | 0.1573 (df=12) | — |
| partial(NRC,mAP \| dataset+family) | -0.0051 (df=7) | [-1.0, 1.0] |
| Spearman(NRC, median err) | 0.4002 | — |
| mean rank distance NRC vs mAP | 7.83/23 | — |

## 诚实限制
- Spearman CI 宽（跨 0），n=23 power 有限 → 只能说"未检测到显著相关"。
- partial(ctrl both) df=7（14 个控制 dummy）→ **估计 under-powered，CI 退化([-1,1])，不可作强独立性结论**。
- NRC 与 median orientation error 中度相关（0.4002），符合"NRC 部分反映朝向误差"。

## NRC≠mAP 的最强反例
- **PSC**：DOTA/FAIR1M/SODA 3 数据集 NRC 均>1（mean 1.133，all>1=True），mAP 不弱仍 selection 反校准 → 单点证明 NRC 捕捉了 mAP 看不到的信息。
