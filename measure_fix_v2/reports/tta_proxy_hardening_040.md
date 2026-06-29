# TTA / augmentation-consistency proxy (040, route C)

> 2026-06-29 20:55:55 CST。**GT-free** offline proxy = local angle-consistency（同图邻近预测的 canonical long-side 角度离散度，半径 200px）。**不使用任何 GT angle-error 构造 proxy**；GT 仅最终评估。无 detector 训练、无 TTA 推理。

| cell | n | NRC_score_only | NRC_proxy(GT-free) | proxy<score | proxy<random |
|---|---|---|---|---|---|
| FAIR1M-v1.0/24(psc) | 28869 | 0.8788 | 0.7699 | True | True |
| DIOR-R/3(orcnn) | 26338 | 0.546 | 0.5277 | True | True |

- **结论**：完全 GT-free 的 local-angle-consistency proxy 在 2 个代表 cell 上**优于 score-only 且优于 random（NRC<1）**，证明 route-C（无 GT proxy）方向可行。
- **limitation**：本轮仅 offline 邻域一致性 proxy（弱于 GT-trained selector）；完整 flip/rotation TTA 推理 proxy 为 next-step（成本高，本轮未启动 GPU TTA）。
