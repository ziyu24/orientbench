# 不确定性基线恢复（066）

> 恢复无 GT / 弱监督不确定性基线，供打分菜单公平对照。**所有角度方差必须用 θ→2θ 圆统计**（避免 π 周期上
> 朴素线性 std 的 90° 伪误差）。

## 基线清单
1. **TTA circular variance**（已用）：水平/垂直/对角翻转推理的角度一致性；离散度用 θ→2θ 圆方差
   `1 - |mean(exp(i·2θ))|`。**完全无 GT 后备打分**（数据 `tta_circular_variance_full_052.csv`）。
2. **MC-dropout**（如模型支持）：多次 dropout 前向的角度圆方差；当前 PSC/ORCNN/RTMDet 推理默认无 dropout，
   **列为条件项**（需模型含 dropout 层；本轮不启用，记为 pending）。
3. **checkpoint ensemble**（如 K2 产出可用）：多 seed/多 checkpoint 的角度圆方差；**待 K2 full-converged
   多 seed 产出后可用**，本轮记 pending（不依赖 R1 半成品）。

## 圆统计要求
- 角度方差一律 θ→2θ：`R = |(1/N)Σ exp(i·2θ_k)|`，circular variance = `1 − R`；离散度越大→越不确定。
- 禁止在 π 周期上用朴素线性 std（会在 ±90° 边界产生伪 90° 误差）。

## 对照定位
- TTA circular variance = 完全无 GT；几何感知打分 = 源域监督+目标域无 GT 的诊断候选（且当前实现拟合用目标域
  GT → upper-bound，见几何打分泄漏审计）。二者均非最终可部署方法。
- MC-dropout / checkpoint ensemble 为条件/后续项，本轮 pending，不空缺、不伪造。
