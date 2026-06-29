👇👇👇👇👇👇

# OrientBench — 038 P3 G2′ feasibility-to-method 判定 完成

- **038 完成**。无 detector 训练 / full matrix / Track A forward dump；thresholds(b7c4e649)、P1 D_cal/D_audit 未改；DOTA train/val。
- **G2′ 裁决：PASS（明确、稳健）。**
- **主报告（唯一人读）**：`docs/p3_g2prime_feasibility_report.md`

## primary ar 阈值
- ar ≥ 1.6（near-square 已排除）；sensitivity ar≥1.3 / ar≥2.0 结论一致。

## score-only / score+ar linear / P3 selector 关键指标（pooled ar≥1.6, D_audit）
- score-only NRC 0.838；score+ar **linear NRC 0.626**；**P3 non-linear NRC 0.409**（AURC 1.91→1.60→1.29；p99@70%cov 10.45→9.18→7.80）。

## bootstrap CI 结论（核心判定 DELTA = NRC_linear − NRC_p3）
- **所有 cell + pooled 的 DELTA CI 均 >0**（pooled 0.217 [0.211,0.221]；DOTA 0.150、DIOR 0.314、FAIR1M 0.239、SODA 0.230）→ **P3 非线性 selector 显著优于 score+ar 线性项**。
- feature importance：主导 = box size(w/h/sqrt_area)+GV-obliquity；**log_ar 极小（0.02-0.08）** → 增益非 aspect-ratio、非 near-square trivial。

## 下一步建议
- **pass 分支**：允许进入 P3 G1/G3/G4（泛化/部署性/稳健）+ 启动 Track A forward dump（机制解释）。
- 关键诚实约束：当前 P3 selector 用 D_cal 的 GT angle-error 标签训练，是 **upper-bound post-hoc 估计，非 deployable method**；G1/G3 须做无 GT 的可部署变体。**未声称 P3 已成立/顶会级别**。

## 验证/test/git
- verifier `107_verify_p3_g2prime_038` → VERIFIED 14/14；pytest 264 passed；thresholds/split 未变；git 0 大文件。

👆👆👆👆👆👆
