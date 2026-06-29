# Real-TTA Selector 结果 (042)

> 2026-06-29 23:12:03 CST。**REAL TTA**（hflip+vflip 真实推理，shadow farm，未改 dataset）的 consistency feature。leave-detector within DIOR（train 一 detector，test 另一），target D_audit 只评估、**无目标 GT**。

| target | n | score | sizelin | geo | **realTTA** | oracle | beats_sz | beats_geo | retained |
|---|---|---|---|---|---|---|---|---|---|
| DIOR-R/3(orcnn) | 13738 | 0.548 | 0.638 | 0.4377 | **0.3907** | 0.3442 | True | True | 0.772 |
| DIOR-R/22(psc) | 10999 | 0.5629 | 0.5677 | 0.4217 | **0.4191** | 0.3456 | True | False | 0.661 |

- **real TTA Route-C 2/2 显著优于 score+ar+size linear**（deployable，无目标 GT）；real_tta_consistency feature 在 ORCNN #3 优于 geometry-only（beats_geo=True），PSC #22 与 geometry 相当（0.419 vs 0.422，marginal）；mean retained 0.717。
- **与 041 offline proxy 方向一致**（Route-C 优于 size-linear；consistency 在部分 cell 提供 geometry 之外增益）→ real TTA 证实 offline proxy 结论。
- real TTA consistency 强度：mean disagreement ~1.4-2°（match_frac 0.99-1.00）。
