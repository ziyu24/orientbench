# Real TTA Non-PSC Extension (046)

> 2026-06-30 15:17:09 CST。补非 PSC detector 的 real TTA（hflip+vflip，shadow farm/read-only，未改 dataset，未调参，未追 mAP，未为正结果改 transform）。

## 设置
- 新增非 PSC：**RTMDet（DIOR farm）+ ORCNN（FAIR1M farm）** = 2 非 PSC family × 2 dataset。4-GPU world_size=4，DumpDetResults→scratch。
- transforms：identity + hflip + vflip（rot90 仅在 inverse sanity 通过时用，本轮未启用）。within-cell D_cal→D_audit（calibration setting，与 044 同口径）。

## 结果（D_audit）
| cell | family | n_audit | tta_match | mean_rtc° | score | sizelin | geo | **realTTA** | beats_sz | beats_geo |
|---|---|---|---|---|---|---|---|---|---|---|
| DIOR-R #61 | RTMDet | (见 csv) | 0.996 | — | — | 0.501 | 0.339 | **0.331** | True | True |
| FAIR1M #5 | ORCNN | (见 csv) | 0.995 | — | — | 0.661 | 0.567 | **0.537** | True | True |
- 数据：real_tta_nonpsc_046.csv。

## 结论
- **非 PSC（RTMDet/DIOR、ORCNN/FAIR1M）real TTA Route-C 均 beat size-linear 且 beat geometry-only**（无目标... 注：within-cell calibration），real TTA consistency 在非 PSC 也提供 geometry 之外增益。**本轮无失败 cell**。
- **real TTA 现覆盖 6 cells / 3 datasets / 3 families**：PSC（DIOR#22/SODA#23/FAIR1M#24）+ ORCNN（DIOR#3/FAIR1M#5）+ RTMDet（DIOR#61）。
- **诚实边界**：① 口径为 within-cell calibration（用本 cell D_cal GT，非 deployable leave-*；deployable 口径见 route_c_dataflow_audit）；② SODA ORCNN #4 因 304k 推理过慢本轮**未完成**（next-step，非失败，是成本）；③ coverage 仍未含全部 family×dataset 组合。
- **未为正结果改 transform / 未调参 / 未追 mAP / 未改原 dataset**。
