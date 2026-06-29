# P1 Claim Ledger (final)

> 2026-06-29 15:18:48 CST

## allowed (with current evidence)
- 在 23-cell 异质矩阵上未检测到 NRC 与 mAP 的显著相关；NRC 提供不同于 accuracy 的 reliability signal（不主张严格独立）。
- aspect-ratio reliability cliff：p99 angle error 随 ar→1 升至 ~84-90°（near-square 朝向 ill-posed）；well-defined region (ar>2) p99 ~8-10°；masked p99 10-16°。
- PSC detection-score proxy 在 DOTA/FAIR1M/SODA 反校准（NRC>1，Track B）。
- DOTA frozen scope formal gates（D2/host/C1 augmentation-view/A4 same-host）+ thresholds 冻结。

## pending (need experiment / sign-off)
- NRC 严格独立性（n=23 under-powered）。
- PSC angle-head 因果归因（需 Track A vs Track B control experiment）。

## forbidden
- 90° p99 = detector catastrophic failure（实为 near-square ill-posedness）。
- full project complete / all datasets / 9-detector matrix complete。
- C1 genuine physical multi-view solved / A4 cross-host causal proved / ARS-DETR=RHINO / DOTA SOTA。
