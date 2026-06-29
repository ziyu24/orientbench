# Leave-dataset Hardening (040)

> 2026-06-29 20:55:55 CST。训练源=其它 datasets PSC D_cal，测试=held-out dataset D_audit，**无目标 GT**。

| target | n | NRC_score | NRC_sizelin | NRC_deployed | NRC_oracle | beats_sizelin | retained |
|---|---|---|---|---|---|---|---|
| DOTA-v1.0/20(psc) | 6696 | 0.7035 | 0.7251 | 0.7097 | 0.5481 | False | -0.04 |
| DIOR-R/22(psc) | 10999 | 0.5629 | 0.9224 | 0.4322 | 0.3563 | True | 0.632 |
| DIOR-R/3(orcnn) | 13738 | 0.548 | 0.8064 | 0.5287 | 0.3642 | True | 0.105 |
| DIOR-R/10(lsknet) | 14108 | 0.5478 | 0.7715 | 0.4994 | 0.3501 | True | 0.245 |
| FAIR1M-v1.0/24(psc) | 13796 | 0.896 | 0.7647 | 0.6042 | 0.5185 | True | 0.773 |
| SODA-A/23(psc) | 105343 | 0.9823 | 0.6782 | 0.5156 | 0.389 | True | 0.787 |
| SODA-A/4(orcnn) | 155468 | 0.722 | 0.5939 | 0.5137 | 0.399 | True | 0.645 |

- leave-dataset pass 6/7（唯一 fail = DOTA #20）。
