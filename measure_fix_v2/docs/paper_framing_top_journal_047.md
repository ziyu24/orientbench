# Paper Framing — Top Journal Lockdown (047)

> 2026-06-30 16:46:48 CST。锁定论文定位（遥感顶刊级别）。**主稿/摘要/报告不得出现 venue-selling 话术**（顶刊点 / top venue ready / CVPR ready / ICCV ready）。论文只写科学贡献与证据强度。

## 标题方向
> Orientation Reliability: Measuring, Diagnosing, and Selecting Trustworthy Angles in Oriented Object Detection

## 核心贡献（仅四条）
1. **Measure**：提出 NRC / risk-coverage 度量，刻画 OBB angle reliability（near-square-aware）。
2. **Diagnose**：发现 **aspect-ratio reliability cliff** 与 **PSC score-level / phase_mod mechanism candidate**。
3. **Fix**：geometry-aware selector 在**固定 size-bin 内打赢 score+ar+size linear** → 说明**不是 size prior**（G2_double_prime）。
4. **Deployability spectrum**：从 upper-bound → source-supervised target-GT-free → fully GT-free proxy，**系统评估不同监督预算下的 orientation selection**。

## 证据强度口径
- Measure：23 cells/6 datasets；NRC 与 mAP 在可比设置中未检出显著相关（**不主张 strictly independent**）。
- Diagnose：cliff 实证；PSC detection-score（FAIR1M/SODA bootstrap 显著）+ phase_mod（3/3 PSC NRC>1）= **mechanism candidate**（**不写 angle head finally proven broken**）。
- Fix：G2_double_prime 固定 size-bin 内 21/21 cell×bin CI>0。
- Deployability：source-supervised transfer leave-* + fully GT-free proxy（弱）。

## 禁止写（forbidden）
- ❌ final deployable method complete；❌ CVPR ready；❌ ICCV ready；❌ NRC strictly independent；❌ PSC angle head finally proven broken；❌ DOTA #20 validation；❌ full project complete。

## DOTA #20 定位
- **limitation / applicability boundary**：当 detection score 已较良校准（NRC≈0.70）时，selector 边际收益小。**不是 validation**。

## P2/C1 定位
- **附录 / negative result**（OT 未明确打赢 GT-identity）；不恢复主线。
