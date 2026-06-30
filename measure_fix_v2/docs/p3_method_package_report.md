# P3 Method Package + TTA Coverage 报告 (044)

> SUPERVISOR_APPROVED_044_P3_METHOD_PACKAGE_AND_TTA_COVERAGE · measure_fix_v2/ · 原始 dataset 未修改 · 未改 thresholds(b7c4e649)/D_cal-D_audit · 未训练 detector · 未补 full matrix · 未恢复 P2 · 未追 DOTA mAP。
> 唯一人读主报告。本轮整合 paper-ready method package + 补强 real TTA coverage。

## 1. 当前门控状态
- G2_double_prime = **PASS**；Deployable hardening = **STABLE-PASS**；Route-C real TTA = **STABLE-PASS on tested cells**（覆盖补强见 §4）；Track A = **intrinsic angle-coder miscalibration candidate SUPPORTED**。P3 method development **继续**。P2/C1 = appendix/negative。

## 2. G2_double_prime 结果
- 固定 box-size bin 内 nonlinear 显著优于 score+ar+size linear（primary ar1.6：21/21 bin×cell ΔNRC CI>0；ar1.3/2.0 20-21/21）→ orientation-specific 非线性几何，**非 box-size prior**。data: fig_g2doubleprime_size_control.csv。

## 3. Deployable / Route-C 结果
- Deployable hardening：非 DOTA unseen 12/12 beat size-linear（无目标 GT），retained mean 0.645；DOTA #20 documented limitation。
- Route-C offline proxy：非 DOTA 10/10 beat size-linear，retained 0.718。
- data: fig_deployable_leave_dataset_detector.csv, fig_route_c_real_tta.csv。

## 4. real TTA coverage 补强结果（本轮）
- 复用 043 shadow farms（未改 dataset），SODA #23 + FAIR1M #24 跑 real hflip+vflip（4-GPU world_size=4，scratch dump）。
- **real TTA Route-C 在 SODA/FAIR1M 均 beat size-linear 且 beat geometry-only**（SODA NRC 0.378、FAIR1M 0.499；tta_match 0.99）→ real TTA consistency 提供 geometry 之外增益。
- **real TTA 现覆盖 4 cells / 3 datasets**（DIOR ORCNN#3+PSC#22 [042]、SODA PSC#23+FAIR1M PSC#24 [044]）。coverage 仍未含非 PSC SODA/FAIR1M + 更多 dataset = next-step。data: real_tta_coverage_044.{md,csv}。

## 5. Track A 机制诊断结果
- PSC intrinsic phase_mod 在 3/3 PSC cell 显著 NRC>1（DIOR 1.156 / SODA 1.117 / FAIR1M 1.121）→ **intrinsic angle-coder miscalibration mechanism candidate（supported by phase_mod evidence）**。Track A 非唯一决定性证据、非门控 P3。Track C geometry 最佳 selector（0.36-0.52）。data: fig_track_a_psc_mechanism.csv。

## 6. P3 selector 方法定义
- 见 p3_selector_method_spec.md：problem def、features、Track A/B/C、deployable Route-C feature、training（D_cal→D_audit）、leave-dataset/detector、real TTA usage、inference pipeline、risk-coverage objective、why-not-calibration、why-not-size-prior、limitations。
- **克制**：当前 selector = reliability-aware selector **candidate**（训练用 source GT = calibration/upper-bound）；**非** final production method、**非** detector retraining。

## 7. 核心图表清单
- Fig 1-4 + Table 1-3（fig_*.csv / table_*.csv）+ caption drafts（fig_table_captions_044.md）。每项含 caption / data path / takeaway / cannot-claim。

## 8. claim ledger 摘要
- 见 claim_ledger_measure_fix_v1.md。allowed：G2″ passed / Deployable stable-pass on tested / Route-C real TTA supported on tested / Track A supports candidate。forbidden：P3 final complete / top venue ready / PSC angle head definitively broken。

## 9. 当前是否允许进入方法写作
- **允许进入方法写作**（method spec + 图表 + claim ledger + paper outline 已就绪）。所有核心结论已有可复算 artifacts。

## 10. 还缺什么才能进入最终论文定稿
- real TTA 全覆盖（非 PSC + 更多 dataset）；DOTA #20 Track A negative control（不调参）；更多 intrinsic 信号佐证 Track A；deployable 的 few-shot/TTA-only 变体收尾；（需新批准）controlled angle-head 实验确证机制。
- venue 判断交合作者（**不声称顶会 ready**）。

## 11. 下一步最小行动
- 补非 PSC real TTA（复用 farm）；写方法正文 §3-§7（依 paper_outline_measure_diagnose_fix_v1.md）；扩 Track A negative control。
- **未声称**：P3 最终完成；顶会 ready；PSC angle head 最终证明反校准（仅 candidate）。
