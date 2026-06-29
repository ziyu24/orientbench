# p99 Tail-Error 可信度核验

> 2026-06-29 13:19:53 CST

## 代码审计结论：**计算正确，无周期 bug**
- angle_error_rad = `abs(((θp-θg+π/2) % π) - π/2)`，范围 [0,π/2]=[0,90°]，是 OBB 的 **π-周期最短距离**（OBB 有 180° 对称）。
- canonical_longside_theta：w<h 时 +90° 取长边，归一到 [-90,90)；正确解决 (w,h,θ)↔(h,w,θ+90°) 表征对称。
- 即 max 可能误差 = 90°；不存在把周期算错成 90° 假尾部的 bug。

## p99≈90° 的真实来源：**near-square / aspect-ratio 退化（朝向 ill-posed），非 detector 灾难性失败**
- aspect-ratio 分箱证据（reliability_cliff_curve）：p99→90° 仅集中在 **ar<1.3（近方形）**；ar>2 时 p99 降到 ~8-10°。
- 近方形箱内 **median 仍很小（~1-2°）**：多数近方形目标朝向预测正确，只有少数歧义目标翻转 90°。
- 结论：90° 尾部 = **方形目标朝向的不适定性**（哪条是长边未定义），是数据/几何歧义，**不是** detector catastrophic orientation failure。**不得**继续宣称 catastrophic orientation failure。

## 真实 tail risk（well-defined region, ar>2 或 near-square masked）
- masked（去近方形）p99 = **10-16°**（DOTA/DIOR ~10-13°，SODA 小目标 ~15-16°），p95 5-8°，p90 4-6°。
- 这是 well-defined region 的**真实非平凡尾部**（写成真实 tail risk）。

## 可视化
- p99 box-pair 样本图（GT 绿/pred 红）：outputs/bench_core/figures/p99_tail_examples/（14 张，含 DIOR orcnn/lsknet/strip + PSC）。
- reliability cliff 曲线：outputs/bench_core/figures/reliability_cliff/cliff_p99_nrc_vs_aspect_ratio.png。
