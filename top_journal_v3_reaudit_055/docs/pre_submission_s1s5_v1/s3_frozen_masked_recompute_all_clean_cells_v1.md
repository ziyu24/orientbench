# S3 —— 冻结 masked 管线重算所有 provenance-clean cells (v1)

> 数据：`reports/pre_submission_s1s5_v1/s3_all_clean_cells_masked_metrics_v1.csv`。robustness obligation，非补 full matrix。只用 provenance-clean artifact；不重训；不追 public mAP。

## 主表（full-val provenance-clean，masked ar≥1.6，进主结论）
| cell | detector | n | masked NRC(detection) | AURC | R70 | geometry(A) NRC | artifact sha16 | can_recompute |
|---|---|---|---|---|---|---|---|---|
| DIOR#22 | PSC | 24988 | 0.542 | 1.137 | 1.442 | 0.600 | f596a441d14e82a6 | True |
| FAIR1M#24 | PSC | 45740 | 0.885 | 2.284 | 2.386 | 0.617 | d12f35c56132f86e | True |
| SODA#23 | PSC | 267796 | 0.914 | 2.274 | 2.196 | 0.506 | a60cc90cfd733bcb | True |
| DIOR#3 | ORCNN | 26957 | 0.526 | 1.243 | 1.485 | 0.495 | c8031cfb64085d14 | True |
| DIOR#61 | RTMDet | 27382 | 0.407 | 1.188 | 1.437 | 0.404 | 7d27907ec0150199 | True |
| SODA#4 | ORCNN | 331575 | 0.711 | 2.147 | 2.387 | 0.508 | 6e1248798ae6e53c | True |

## 附录（masked-only，无 full-val matched table，不进主表）
| cell | detector | n(masked) | masked NRC | 原因 |
|---|---|---|---|---|
| DIOR#10 | ORCNN+LSKNet | 27097 | 0.548 | 仅 features_v2（预筛 ar≥1.6），无 full-val 17字段匹配表 |
| SODA#11 | ORCNN+LSKNet | 254021 | 0.731 | 同上 |

## 排除（不进任何结论）
| cell | 原因 |
|---|---|
| DOTA#20 | invalid_pending：19-图 D_cal subset dump，masked NRC=1.037 但 scope 不可比 |

## 裁决
- 主表覆盖 **6 个 full-val provenance-clean cell（3 detector family × 3 dataset，PSC/ORCNN/RTMDet × DIOR/FAIR1M/SODA）**，全部 can_recompute。
- masked detection NRC 全部 <1（0.41–0.91）→ **better-than-random / non-reversed risk ranking**（不叫 calibrated）。
- 宽度诚实：**6 主表 cell + 2 附录**，非 full matrix；robustness 足以支撑“测量协议在多 detector×dataset 上一致”，但不足以宣称全面 benchmark。
