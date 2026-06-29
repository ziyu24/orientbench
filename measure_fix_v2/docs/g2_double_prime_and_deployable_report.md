# G2_double_prime + Deployable 报告（measure_fix_v2）

> SUPERVISOR_APPROVED_039_V2_MEASURE_FIX_G2_DOUBLE_PRIME · 无 detector 训练 · 无 full matrix · 无 Track A forward dump · DOTA train/val 不追公开 mAP · P1 thresholds(b7c4e649)/D_cal-D_audit/formal 标签/frozen tag **未改**。
> 唯一人读主报告。数据：measure_fix_v2/reports/。所有 v2 新增产物在 measure_fix_v2/ 下。

## 1. 新阶段主线
> Orientation Reliability: Measuring, Diagnosing, and Selecting Trustworthy Angles in Oriented Object Detection
- P1 = measure+diagnose；**P3 = fix（reliability-aware orientation selection）**；P2/C1 降为附录/消融/负结果。
- 本轮门控：G2_double_prime（排除 box-size prior 替代解释）→ Deployable（无目标域 GT 标定）。

## 2. 禁止事项遵守
- ✅ 未追 DOTA 公开 mAP（train/val）；未重训 host；未补 full matrix；未改 thresholds/split/formal 标签/frozen tag；未篡改 claim ledger；未恢复 P2 主线；未声称 full project complete / C1 multi-view / A4 cross-host / P3 顶会级别；未用 near-square trivial gain 包装；未把 Track C upper-bound 称 deployable method（下文严格区分）。

## 3. G2_double_prime protocol（跑前冻结）
见 measure_fix_v2/docs/g2_double_prime_protocol.md。核心问题：**固定 box-size 分箱内，nonlinear geometry-aware selector 是否仍显著优于 score-only 和 score+ar+size 线性基线？**

## 4. 数据 split
- cells：PSC #20(DOTA)/#22(DIOR)/#24(FAIR1M)/#23(SODA) + 非 PSC sanity ORCNN #4(SODA)/#3(DIOR)、LSKNet #10(DIOR)，共 7 cells。
- P1 frozen `assign_split` 确定性 md5，**D_cal/D_audit 互斥**；selector 只在 D_cal 训练，判定只看 D_audit。

## 5. well-defined 区域
- primary **ar≥1.6**；sensitivity ar≥1.3 / ar≥2.0。near-square 排除（非主贡献）。

## 6. fixed box-size bins
- D_cal 上 `log(sqrt(area))` 三分位 → small/medium/large，边界应用到 D_audit（冻结）。

## 7. 三类 selector + nonlinear
- score-only [score]；score+ar linear；**score+ar+size linear**（关键控制，含 box size 线性项）；nonlinear GBM[score,log_ar,log_sqrt_area,gv_obb_needed,w,h]（seed 固定）。
- 标签：continuous angle error（risk）；binary τ=5° sensitivity。

## 8. NRC（D_audit，primary ar≥1.6，overall）
| cell | score-only | score+ar lin | **score+ar+size lin** | **nonlinear** |
|---|---|---|---|---|
| DOTA #20 psc | 0.704 | 0.698 | 0.643 | **0.548** |
| DIOR #22 psc | 0.563 | 0.669 | 0.571 | **0.356** |
| FAIR1M #24 psc | 0.896 | 0.760 | 0.758 | **0.519** |
| SODA #23 psc | 0.982 | 0.618 | 0.611 | **0.389** |
| SODA #4 orcnn | 0.722 | 0.585 | 0.579 | **0.399** |
| DIOR #3 orcnn | 0.548 | 0.743 | 0.636 | **0.364** |
| DIOR #10 lsknet | 0.548 | 0.749 | 0.610 | **0.350** |

## 9. bootstrap CI — 核心判定 DELTA = NRC(size_linear) − NRC(nonlinear)，>0 表示 nonlinear 更优（overall, primary）
| cell | DELTA | 95% CI | nl 显著更优 |
|---|---|---|---|
| DOTA #20 | 0.095 | [0.081, 0.111] | 是 |
| DIOR #22 | 0.215 | [0.192, 0.239] | 是 |
| FAIR1M #24 | 0.239 | [0.219, 0.260] | 是 |
| SODA #23 | 0.222 | [0.215, 0.228] | 是 |
| SODA #4 orcnn | 0.180 | [0.176, 0.184] | 是 |
| DIOR #3 orcnn | 0.270 | [0.245, 0.303] | 是 |
| DIOR #10 lsknet | 0.260 | [0.239, 0.283] | 是 |

## 10. fixed-size bin 内结果（核心控制：排除 box-size prior）
- **每个 cell × 每个 size bin（small/medium/large）的 DELTA(size_linear − nonlinear) CI 均 >0**（primary ar≥1.6，21/21 size-bin × cell 组合显著）。
- ar sensitivity：ar≥1.3 内 20/21、ar≥2.0 内 21/21 size-bin 显著。
- → **gain 在固定 size bin 内仍存在 → 非 box-size prior，而是 orientation-specific 非线性几何结构**（GV-obliquity importance 0.2–0.25，朝向相关）。

## 11. G2_double_prime 裁决：**PASS（明确、稳健）**
五条件全满足：① nonlinear 显著优于 score+ar+size linear（所有 cell CI>0）；② well-defined 区域成立；③ ≥2 cell 方向一致（全 7 cell，含 3 非 PSC sanity）；④ **fixed-size bin 内 gain 持续**；⑤ 非 near-square 驱动（ar≥1.6）。

## 12. Deployable 门控（仅 G2DP pass 后执行）：**PARTIAL-PASS**
> 核心问题：无目标域 GT angle-error 标定时 selector 是否仍工作？路线 A leave-dataset + 路线 B leave-detector（**目标域不用 GT 重标定**）。
- **9/11 unseen-cell 评估**：nonlinear 在未见 dataset/detector 上**显著优于 score-only 且优于 size-linear**（无目标 GT），**保留 within-target oracle gain 的 ~69%**（median）。
- leave-dataset：DIOR/FAIR1M/SODA ✓（3/4），DOTA ✗。
- leave-detector PSC→非PSC（ORCNN/LSKNet）：3/3 ✓（near-oracle，如 SODA-ORCNN nl 0.419 vs oracle 0.399）。
- leave-detector 非PSC→PSC：DIOR/FAIR1M/SODA ✓（3/4），DOTA ✗。
- **唯一例外 = DOTA #20 PSC**（within-target oracle 0.548 最弱、masked 未显著反校准；结构最少，迁移失败有据）。
- 数据：deployable_results_039.csv。

## 13. P1 硬债修订建议
见 measure_fix_v2/docs/p1_hard_debt_patch_notes.md：NRC 改 within-dataset/comparable-setting headline；PSC 推断限 detector×dataset-level；正文补 GV-obliquity 定义；related work 补 D-ECE/selective prediction/square-like/GWD-KLD/angle uncertainty；持久化检查；治理内容下沉附录。

## 14. P2 / P3 边界
- **P3 主线推进**：G2DP pass（orientation-specific 非线性几何可靠性结构真实，非 box-size prior）+ Deployable partial-pass（跨 dataset/detector 无目标 GT 仍多数有效，retain ~69% oracle gain）。
- **严格区分**：G2DP 的 selector 用 D_cal GT angle-error 训练 = **upper-bound / calibration setting**；Deployable 的 leave-dataset/detector 变体**不使用目标 GT** = 趋向 deployable。当前**不**声称 fully deployable（DOTA 例外 + 仅 source-trained 迁移），亦**不**称 upper-bound 为 deployable method。
- P2/C1 维持附录/负结果，未恢复主线。

## 15. 下一步裁决（需合作者/监督员）
- **G2DP=PASS，Deployable=PARTIAL-PASS** → 支持 **deployable reliability-aware selector** 叙事，但**不**自动判定顶会级别（DOTA 例外 + 需更广 leave-dataset/detector + TTA-proxy 路线 C 验证）。
- 建议（待批准）：① 扩 leave-dataset/leave-detector 覆盖 + 路线 C（TTA/augmentation consistency，无 GT proxy）巩固 deployable；② 之后再考虑 Track A forward dump（机制支线，本轮未启动）。
- **未触发停止条件**（G2DP 未 fail；Deployable 非 fail）。**未**声称 CVPR/ICCV ready。
