# Route-C TTA/consistency proxy 结果 (041)

> 2026-06-29 21:42:47 CST。selector=source-trained（source GT），target D_audit 只评估、**无目标 GT**。consistency feature = **GT-free offline local-angle-consistency**（real flip-TTA 推理被 annfile plumbing 阻塞，见 tta_proxy_manifest_041.json）。

## non-DOTA cells（leave-dataset + leave-detector）
| target | mode | n | score | sizelin | geo_sel | **routeC** | oracle | beats_sz | beats_geo | retained |
|---|---|---|---|---|---|---|---|---|---|---|
| FAIR1M-v1.0/24(psc) | L-dataset | 13796 | 0.896 | 0.7647 | 0.6062 | **0.6063** | 0.5131 | True | False | 0.756 |
| SODA-A/23(psc) | L-dataset | 105343 | 0.9823 | 0.6782 | 0.5034 | **0.4557** | 0.3648 | True | True | 0.853 |
| DIOR-R/22(psc) | L-dataset | 10999 | 0.5629 | 0.9224 | 0.445 | **0.4068** | 0.3441 | True | True | 0.713 |
| DIOR-R/3(orcnn) | L-dataset | 13738 | 0.548 | 0.8064 | 0.5423 | **0.4331** | 0.3483 | True | True | 0.576 |
| DIOR-R/10(lsknet) | L-dataset | 14108 | 0.5478 | 0.7715 | 0.5182 | **0.4288** | 0.3319 | True | True | 0.551 |
| DIOR-R/3(orcnn) | L-detector_psc2nonpsc | 13738 | 0.548 | 0.7596 | 0.4308 | **0.3964** | 0.3483 | True | True | 0.759 |
| DIOR-R/10(lsknet) | L-detector_psc2nonpsc | 14108 | 0.5478 | 0.7335 | 0.401 | **0.376** | 0.3319 | True | True | 0.795 |
| FAIR1M-v1.0/24(psc) | L-detector_nonpsc2psc | 13796 | 0.896 | 0.7743 | 0.6621 | **0.639** | 0.5131 | True | True | 0.671 |
| SODA-A/23(psc) | L-detector_nonpsc2psc | 105343 | 0.9823 | 0.7976 | 0.4806 | **0.4519** | 0.3648 | True | True | 0.859 |
| DIOR-R/22(psc) | L-detector_nonpsc2psc | 10999 | 0.5629 | 0.5676 | 0.4254 | **0.4215** | 0.3441 | True | False | 0.646 |

- **non-DOTA: routeC 10/10 优于 score+ar+size linear；GT-free consistency feature 在 8/10 优于 geometry-only selector**（即 consistency 提供 geometry 之外的可部署增益）。mean retained 0.718 / median 0.734。

## DOTA #20 negative control
| target | mode | n | score | sizelin | geo_sel | **routeC** | oracle | beats_sz | beats_geo | retained |
|---|---|---|---|---|---|---|---|---|---|---|
| DOTA-v1.0/20(psc) | L-dataset | 6696 | 0.7035 | 0.7251 | 0.7061 | **0.59** | 0.4982 | True | True | 0.553 |
| DOTA-v1.0/20(psc) | L-detector_nonpsc2psc | 6696 | 0.7035 | 0.6524 | 0.7967 | **0.6648** | 0.4982 | False | True | 0.189 |

- leave-dataset：routeC 0.59 **beats sizelin**（consistency feature 改善了 040 中失败的 DOTA leave-dataset）；leave-detector nonpsc→psc：仍 0.665 不及 sizelin（弱结构 negative control，符合预期）。
