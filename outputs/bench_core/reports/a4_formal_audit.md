# A4 Formal Audit — D_audit (same-host source attribution)

> O2-RTDETR frozen sha256 3e32fa11114ced82…; frozen thresholds applied (NOT mutated); D_audit holdout; background_source_enabled=True.
> **scope: same-host A4 source attribution — NO cross-host causal claim.**

## VERDICT: **formal_pass** (within same-host A4 source-attribution scope; no cross-host causal claim)
- significant non-GV sources (HSIC p<=0.05): ['E_layout', 'entropy', 'score']
- n_used(D_audit)=2974; bg_unavailable_ratio=0.0

| source | partial_corr (D_audit) | HSIC p | significant(<=0.05) |
|---|---|---|---|
| E_bg | -0.0521 | 0.7213930348258707 | False |
| E_layout | -0.0233 | 0.024875621890547265 | True |
| score | -0.1675 | 0.004975124378109453 | True |
| entropy | 0.1603 | 0.004975124378109453 | True |
| gv | 0.0295 | 0.004975124378109453 | False |

## 边界
- formal_pass 仅 same-host A4 source-attribution scope；**不得**宣称跨 host 因果；DOTA partial；阈值未调；GV+class 已控；near-square masked。
