# Leave-detector Hardening (040)

> 2026-06-29 20:55:55 CST。PSC↔非PSC（ORCNN/LSKNet），**无目标 GT**。

| target | n | NRC_score | NRC_sizelin | NRC_deployed | NRC_oracle | beats_sizelin | retained |
|---|---|---|---|---|---|---|---|
| SODA-A/4(orcnn) | 155468 | 0.722 | 0.5817 | 0.4166 | 0.399 | True | 0.946 |
| DIOR-R/3(orcnn) | 13738 | 0.548 | 0.7596 | 0.4343 | 0.3642 | True | 0.619 |
| DIOR-R/10(lsknet) | 14108 | 0.5478 | 0.7335 | 0.3976 | 0.3501 | True | 0.76 |
| DOTA-v1.0/20(psc) | 6696 | 0.7035 | 0.6596 | 0.8549 | 0.5481 | False | -0.974 |
| DIOR-R/22(psc) | 10999 | 0.5629 | 0.6914 | 0.4364 | 0.3563 | True | 0.612 |
| FAIR1M-v1.0/24(psc) | 13796 | 0.896 | 0.7519 | 0.6442 | 0.5185 | True | 0.667 |
| SODA-A/23(psc) | 105343 | 0.9823 | 0.6449 | 0.4176 | 0.389 | True | 0.952 |

- leave-detector pass 6/7（唯一 fail = DOTA #20 nonpsc→psc）。
