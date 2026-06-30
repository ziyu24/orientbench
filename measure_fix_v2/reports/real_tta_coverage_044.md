# Real TTA Coverage 补强 (044)

> 2026-06-30 10:57:25 CST。复用 043 shadow farms（未改 dataset），SODA #23（原 val_tiled read-only）+ FAIR1M #24（farm）跑 real hflip+vflip，identity 复用 043 dump。within-cell D_cal→D_audit（calibration setting）。

| cell | n_audit | tta_match | mean_rtc° | score | sizelin | geo | **realTTA** | beats_sz | beats_geo |
|---|---|---|---|---|---|---|---|---|---|
| SODA-A #23 (PSC) | 105343 | 0.99 | 1.45 | 0.982 | 0.611 | 0.389 | **0.378** | True | True |
| FAIR1M #24 (PSC) | 13796 | 0.99 | 1.95 | 0.896 | 0.758 | 0.519 | **0.499** | True | True |

- **real TTA Route-C 在 SODA/FAIR1M 均显著优于 size-linear 且优于 geometry-only**（real TTA consistency 提供 geometry 之外增益）→ 与 042 DIOR 一致。
- **real TTA 现覆盖 4 cells / 3 datasets**（DIOR ORCNN#3 + PSC#22 [042]；SODA PSC#23 + FAIR1M PSC#24 [044]），tta_match 0.99-1.00。
- 口径：此处为 within-cell calibration（用本 cell D_cal GT 训 selector）；deployable（无目标 GT）见 042 leave-detector。
- next-step：非 PSC（SODA/FAIR1M ORCNN/LSKNet）real TTA + 更多 dataset。
