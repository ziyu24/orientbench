# Non-PSC Deployable Leave-* (047)

> 2026-06-30 17:39:11 CST。**source-supervised selector + target GT-free inference**（leave-dataset / leave-detector，target 不用 GT，仅评估）。补 046 的非 PSC 短板（046 是 within-cell calibration）。**未调参、未追 mAP、未改 dataset。**

## 三种口径严格区分
1. **within-cell calibration**（用本 cell D_cal GT）→ **不能称 deployable**（044/046）。
2. **source-supervised + target GT-free inference**（source GT 训练，target 无 GT）→ **deployable candidate**（本表）。
3. **fully GT-free standalone proxy**（local-angle-consistency 直接作 selection，不训练）→ **fully GT-free**（较弱，下表 proxy 列）。

## 结果（D_audit，source-supervised，无 target GT）
| held-out | target | family | score+ar+size lin | geometry | **source-sup** | standalone proxy(GT-free) | beat size-lin |
|---|---|---|---|---|---|---|---|
| rtmdet | DIOR #61 | RTMDet | 0.659 | 0.781 | **0.699** | 0.572 | **False** |
| orcnn | DIOR #3 | ORCNN | 0.701 | 0.427 | **0.379** | 0.547 | True |
| orcnn | SODA #4 | ORCNN | 0.582 | 0.411 | **0.380** | 0.534 | True |
| orcnn | FAIR1M #5 | ORCNN | 0.663 | 0.596 | **0.581** | 0.821 | True |
| lsknet | DIOR #10 | LSKNet | 0.670 | 0.385 | **0.367** | 0.577 | True |
| lsknet | SODA #11 | LSKNet | 0.563 | 0.402 | **0.379** | 0.544 | True |
| lsknet | FAIR1M #12 | LSKNet | 0.679 | 0.601 | **0.589** | 0.827 | True |
| FAIR1M(LD) | FAIR1M #5 | ORCNN | 0.664 | — | **0.588** | — | True |
| FAIR1M(LD) | FAIR1M #12 | LSKNet | 0.680 | — | **0.596** | — | True |

（LD=leave-dataset；其余为 leave-detector）

## 通过标准逐项
- 多数 cell beat size-linear：**8/9（88.9%）** ✅
- ≥2 非 PSC family 成立：**ORCNN + LSKNet** ✅
- ≥2 dataset 成立：**DIOR + SODA + FAIR1M（3）** ✅
- 失败 cell 完整报告：**RTMDet #61**（leave-detector，src 0.699 未及 size-linear 0.659；geometry-only 0.781 更差 → RTMDet/DIOR 的 geometry-reliability 关系不同，单一 family 失败）✅
- 未调参追正结果 ✅
- standalone GT-free proxy：beat score、< random（如 ORCNN#3 0.547、LSKNet#10 0.577），但**弱于 source-supervised**（如实报告）。

## 裁决：**non-PSC deployable leave-* PASS**
- source-supervised + target GT-free inference 在 **2 非 PSC family × 3 dataset** 上多数 beat size-linear。
- **诚实边界**：① 口径为 source-supervised（非 fully GT-free）；② **leave-dataset SODA-held-out + DIOR-held-out folds 因大 SODA cell（304k/254k）bootstrap 计算过重，进程被 kill = compute-cost limitation，已报告未跳过**（next-step：降 bootstrap/分批）；③ RTMDet 单 family 失败。
