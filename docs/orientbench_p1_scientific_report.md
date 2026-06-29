# OrientBench P1 — 科学有效性报告（深度核验版）

> SUPERVISOR_APPROVED_035 · 无训练 · 无 GPU 实验 · 不追 DOTA 公开 mAP · thresholds 冻结 b7c4e649 未变 · D_cal/D_audit split 未变。
> DOTA 口径：**train 训练 / val 验证**（非 trainval/test）；val mAP 低于公开论文属正常。
> 唯一人读报告（已不再拆多文件）。数据来自 outputs/bench_core/reports/ 与 figures/。

---

## 1. 当前阶段结论
- current approved scope 完成并冻结；full project 未完成（partial）。
- P1 经深度核验后结论：**NRC 构造效度成立（克制）、reliability cliff 成立、PSC 反校准（Track B）成立**；但 033 的"catastrophic orientation failure"措辞**已纠正**（见 §3）。

## 2. 禁止事项遵守情况
- ✅ 未追 DOTA 公开 mAP；✅ 未因 val 精度低重训 host；✅ 未改 thresholds.yaml / D_cal-D_audit split；✅ 未把 exploratory 改 formal；✅ 未补 full 9-detector matrix 掩盖效度；✅ 未声称 full project complete / C1 genuine multi-view / A4 cross-host causal；✅ 未启动 PSC angle-head 大训练。

## 3. p99 tail-error 可信度核验（第一优先级）
- **代码正确**：angle error = `abs(((Δθ+π/2)%π)-π/2)` ∈[0,90°]，OBB π-周期最短距离；canonical long-side 正确解决表征对称。**无周期 bug**。
- **p99≈90° 的真实来源 = near-square / aspect-ratio 退化（朝向 ill-posed），非 detector 灾难性失败**：
  - aspect-ratio 分箱：p99→90° 仅集中在 **ar<1.3**；ar>2 时 p99 ~8-10°。
  - 近方形箱 median 仍小（~1-2°）→ 多数预测正确，仅少数歧义目标 90° 翻转。
- **纠正**：不再宣称 catastrophic orientation failure（033 措辞）。
- **真实 tail（well-defined region）**：masked p99 = **10-16°**（非平凡）。详见 p99_tail_error_verification.md / p99_tail_error_table.csv。

## 4. p99 样本可视化
- outputs/bench_core/figures/p99_tail_examples/（14 张 GT(绿)/pred(红) box-pair，含 DIOR orcnn/lsknet/strip + PSC）。
- 代表性结论：高误差样本多为近方形或长边歧义目标；well-defined 长条目标 pred 与 GT 朝向基本一致。

## 5. masked/unmasked CDF 与 p90/p95/p99 表
| 分组 | p90 | p95 | p99 |
|---|---|---|---|
| masked (well-defined, ar≥~1.1) | 4-6° | 5-8° | **10-16°** |
| unmasked (含 near-square) | — | — | **88-90°**（near-square 主导） |
- 完整 per-cell：tail_risk_analysis_v2.csv / p99_tail_error_table.csv。

## 6. near-square / aspect-ratio reliability cliff（核心动机图）
- **cliff 成立**：p99 angle error 随 ar：3.0+ ~5-7° → 2-3 ~8-10° → 1.6-2 ~11-45° → **<1.3 ~84-90°**。
- NRC 随 ar：well-defined(ar 2-3) ~0.47-0.49（selection 有效）；near-square ~0.93-0.97（歧义区 selection 无效）。
- 图：figures/reliability_cliff/cliff_p99_nrc_vs_aspect_ratio.png；数据：reliability_cliff_curve.csv。
- 含义：可靠性诊断必须 aspect-ratio aware；这是 P1/P3 核心动机。

## 7. NRC 构造效度（相关/偏相关/CI/rank distance）
- **措辞（最终）**：在当前 23-cell 异质矩阵上**未检测到 NRC 与 mAP 的显著相关**；NRC 提供**不同于 accuracy 的可靠性信号**。**不主张严格独立 (strict independence)**（n=23）。
- Spearman(NRC,mAP) = **-0.046**（p=0.84，CI95 [-0.49,0.48]）；Pearson -0.26。
- partial(NRC,mAP | dataset+family) = -0.005，**df=7，CI95 退化[-1,1] → under-powered，不可作强独立性结论**。
- Spearman(NRC, median err) = 0.40（NRC 部分反映朝向误差）；rank distance 7.83/23。
- 最强反例：**PSC**（DOTA/FAIR1M/SODA NRC>1，mean 1.133）。详见 nrc_construct_validity.md。

## 8. PSC 反校准 preflight（Track A/B/C）
- **Track B（detection-score proxy，当前主口径）**：PSC 反校准成立——DIOR 0.55 / DOTA 1.06 / FAIR1M 1.08 / SODA 1.26；3/4 数据集>1；延伸到 well-defined 区（SODA ar1.6-2 NRC 1.18）。同数据集 orcnn/lsknet/rtmdet 均<1。
- **Track A（intrinsic native uncertainty）**：pending（未提取 PSC 原生角度不确定性）。
- **Track C（post-hoc upper bound）**：pending（DOTA C1/A4 已用 D_cal→D_audit 思路；PSC-specific 未做）。
- **只能说**：detection-score 作 selection 时在 PSC family 反校准；**不能说** PSC angle head 本身反校准（需 control experiment）。
- 判断：Track B 稳定，**足够申请 angle-head control experiment**；现在不启动大训练。详见 psc_miscalibration_preflight.md。

## 9. P1 是否具备 TGRS / ISPRS JPRS 继续推进价值
- **有希望**（前提：p99/cliff/NRC 构造效度严谨写）：① NRC≠accuracy 信号；② aspect-ratio reliability cliff 真实；③ PSC 反校准跨数据集。三者构成扎实的诊断基准叙事，适合遥感顶刊 benchmark/analysis。

## 10. 为什么现在还不够 CVPR / ICCV / TPAMI
- 现有结果是 **benchmark 表格 + 诊断**，非 mechanism 发现。
- 要进 CVPR/ICCV/TPAMI，需把 **PSC 反校准做成机制发现**（angle-head control experiment 证明归因）或把 **reliability cliff 做成方法贡献**（如 degeneracy-aware selection/training），而非仅评测表。当前两者均 pending。

## 11. P2 / P3 边界
- **P2（C1）**：P1 只提供 Bench-Core + RHINO host + augmentation-view evidence；不能替代 genuine C1；不能证明 OT-dustbin 机制（OT 与 GT-identity 接近打平）。
- **P3（reliability）**：P1 的 reliability cliff + well-defined tail（p99 10-16°）+ PSC 反校准 = P3 前置证据**成立** → P3 值得作为后续主线（非收缩情形）。

## 12. 可宣称结论
- NRC 与 mAP 在 23-cell 上无显著相关，提供不同于 accuracy 的可靠性信号。
- orientation reliability 随 aspect-ratio→1 断崖（near-square ill-posedness）；well-defined region p99 10-16°（真实非平凡尾部）。
- PSC detection-score selection 跨数据集反校准（Track B）。
- DOTA formal gates（C1 augmentation-view / A4 same-host）已冻结 + D_audit formal_pass。

## 13. 禁止宣称结论
- ❌ catastrophic orientation failure（90° 为 near-square ill-posedness）。
- ❌ NRC 完全独立于 mAP（n=23 under-powered）。
- ❌ PSC angle head 已证明反校准（仅 Track B / score-level）。
- ❌ full project complete / all datasets covered / 9-detector matrix complete。
- ❌ C1 genuine physical multi-view solved / A4 cross-host causal proved / ARS-DETR=RHINO / DOTA SOTA。

## 14. 后续最小行动
- （需批准）PSC angle-head control experiment（机制归因）。
- （轻量）Track C PSC-specific post-hoc upper bound（D_cal→D_audit）。
- （图）补 masked/unmasked CDF、NRC-vs-mAP scatter、PSC family bar（figures_required_for_top_tier.md）。
- （写作）论文骨架 paper_outline_v0.md，核心结论标 pending 直到 sign-off。

## 15. 关键产物路径
- 本报告：docs/orientbench_p1_scientific_report.md
- p99 核验：outputs/bench_core/reports/p99_tail_error_verification.md, p99_tail_error_table.csv；figures/p99_tail_examples/
- cliff：reliability_cliff_analysis.md, reliability_cliff_curve.csv；figures/reliability_cliff/
- 构造效度：nrc_construct_validity.{md,csv,json}
- PSC：psc_miscalibration_preflight.{md,csv}
- 论文骨架：paper_outline_v0.md, claim_ledger_for_paper.md, figures_required_for_top_tier.md
- 持久化：outputs/persistent_artifacts/orientbench_v2/（gitignored）+ persistent_prediction_manifest_v2.json（⚠️ /dev/shm 非持久）
- thresholds：configs/thresholds.yaml（b7c4e649 FROZEN）
