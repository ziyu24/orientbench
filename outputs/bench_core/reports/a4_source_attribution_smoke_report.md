# A4 Source-Attribution — Mechanism SMOKE (O2-RTDETR host)

> A4 frozen snapshot sha256=3e32fa11114ced82…; **mechanism smoke**，非完整 A4 gate。background source 在 smoke 中 unavailable（需 raster image）。

| split | n_used | masked | E_layout pc | E_layout HSIC p | score pc | score HSIC p | entropy pc | GV pc |
|---|---|---|---|---|---|---|---|---|
| D_cal | 13327 | 138 | -0.053 | 0.004975124378109453 | -0.1694 | 0.004975124378109453 | 0.1616 | -0.0216 |
| D_audit | 13286 | 106 | -0.0388 | 0.004975124378109453 | -0.143 | 0.004975124378109453 | 0.1355 | -0.0151 |

## 机制原语已实现并跑通
- orientation evidence attribution、partial-corr(控 GV+class)、HSIC(置换 p, 受控抽样 max_samples=800/seed=0)、
  source sanity(GV/layout/score/entropy vs orientation risk)、per-class、bootstrap CI、near-square mask、D_cal/D_audit。
## 可进入 D_cal / 仍 blocked
- 可进入 D_cal 探索: partial-corr / HSIC source-attribution 原语（机制级）。
- **仍 blocked（不可进入 formal A4 gate）**: background source 未算（需 image annulus）；A4 vs GV/entropy/score 的最小 Δ、partial-corr/HSIC 上界 (R8) 未冻结；A-gate-1 source sanity 完整流程 + 批准未做。
## 下一步
- 补 background source（对 A4 frozen host 在 image 上算 annulus 梯度）；扩样本；预注册 A_A4 阈值后冻结并做 D_audit 正式 gate。
