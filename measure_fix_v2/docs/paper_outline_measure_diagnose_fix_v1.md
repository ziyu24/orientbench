# Paper Outline — Measure / Diagnose / Fix (v1)

> 2026-06-30 10:38:46 CST。主线：Orientation Reliability: Measuring, Diagnosing, and Selecting Trustworthy Angles in OBB Detection。P2/C1 入 appendix / negative result（不恢复主线）。

## 1. Introduction
- mAP 不足以刻画朝向可靠性；提出 measure→diagnose→fix 框架。贡献：OrientBench protocol、reliability cliff/NRC 诊断、PSC 反校准发现、deployable reliability-aware selector candidate、PSC angle-coder intrinsic 机制候选。

## 2. OrientBench protocol
- datasets（DOTA train/val 自跑、DIOR/FAIR1M/SODA/HRSC）；detectors；prediction schema；D_cal/D_audit 互斥；formal(DOTA frozen) vs exploratory；NRC-AUC/Risk@k/near-square mask/aspect-ratio curve；selection-score 三轨。

## 3. Measuring orientation reliability
- NRC 构造效度（within-dataset，未检出与 mAP 显著相关）；aspect-ratio reliability cliff（p99 随 ar→1 升至~90°，near-square ill-posedness）；well-defined region tail。

## 4. Diagnosing reliability failure
- PSC detection-score selection 反校准（NRC>1，bootstrap FAIR1M/SODA 显著）；G2_double_prime：固定 size-bin 内 nonlinear>score+ar+size linear → orientation-specific 非线性几何（非 size prior）。

## 5. Reliability-aware selector
- Track C geometry-aware selector（method spec）；risk-coverage objective；为何非简单校准/非 size prior。

## 6. Deployability gate
- leave-dataset/leave-detector（无目标 GT）；Route-C GT-free consistency proxy；real TTA consistency（shadow farm，hflip/vflip）；stable-pass on tested cells；coverage limitation。

## 7. PSC mechanism diagnostic
- Track A instrumented phase_mod dump；phase_mod 反校准 NRC>1（3/3 PSC cells）→ intrinsic angle-coder miscalibration mechanism candidate（克制；phase_mod 为一 intrinsic 信号）。

## 8. Limitations
- real TTA coverage limited；selector 仍 source-GT calibration（非 final method）；DOTA #20 weak-structure negative control；Track A candidate 非定论；P2/C1 negative/appendix。

## 9. Conclusion
- measure→diagnose→fix 框架揭示并初步修复 OBB 朝向可靠性问题；deployable selector 与 PSC 机制为后续主线。
### Appendix list
A. 实验配置/复现；B. 数据覆盖；C. cell manifest+sha256；D. claim ledger；E. P2/C1 negative result；F. forbidden claims；G. shadow farm / TTA adapter。
