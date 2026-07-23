# S1–S5 最终判定 (v1)

> 全部基于真实 provenance-clean artifact，冻结 masked ar≥1.6，未训练/未追 public mAP/未改 thresholds·split。

## 逐项

**S1a 是否通过？** **PASS（完整，6/6 cell）。** 真实 full evaluator（从 raw predictions 重匹配）下，约束角度扰动使 **6/6 provenance-clean cell（DIOR#22/#3/#61 + FAIR1M#24 + SODA#23/#4，跨 PSC/ORCNN/RTMDet × DIOR/FAIR1M/SODA）真实 AP50 完全不变（ΔAP50=0.0000）、FP@0.5 不变**，而 AP75 塌陷、角度 risk 升 ~7×。matched-only mAP=1.000 代理被真实 AP50 取代。无 compute limitation。

**S1b 是否通过？** **QUALIFIED PASS。** selector-fit / conformal-calib 独立性已修复（D_fit/D_calib/D_audit 互斥，guarantee 有效）。但修复后 **geometry selector 非普遍占优**：在 detection 弱信息 cell（FAIR1M/SODA）显著更优，在 detection 已强 cell（DIOR）打平或略差；leave-cell 迁移退化。

**S1c 是否通过？** **QUALIFIED PASS。** LTT 固定序列（二项尾部，FWER 控制）+ 有界均值（Hoeffding B=90）+ image-clustered bootstrap 均实现。但**有效保证 modest**：尾部保证在 detection 强 cell 成立（点估计轻微 overshoot，CI 跨 α），在 detection 弱 cell 以 detection 失败（需 geometry）；**有界均值严格保证过保守、不实用**。

**P1 claim 保留/收缩/失败？** **保留（精确、受门控）**：AP50 对某些几何区朝向误差结构性弱敏感（ar 与 IoU 阈值门控），AP75 敏感。不写“mAP 完全不变”。

**P2 conformal guarantee 是否有效？** **有效但 modest**：有限样本尾部风险控制（indicator + 二项/LTT + image-clustered CI）成立，弱信息 cell 需 geometry selector；均值角度严格保证不实用；跨域退化如实报告。**不再是空洞保证，也不是干净普遍保证。**

**geometry selector 是否仍推荐为默认 score？** **收缩：不写 blanket recommended default。** 写“弱信息 cell 的安全默认（never hurts, helps where detection uninformative）”。

**S2 是否支持 PSC 机制线继续？** **部分。** confounding 排除（NRC>1 跨 class/size/ar 层持续），但无 aliasing 频率峰。仅 1/2 支持 → **phase_mod 保持 case study / mechanism candidate；不启动重训矩阵**。

**S3 clean-cell 宽度是否足够？** **6 个 full-val provenance-clean cell（3 family × 3 dataset）+ 2 附录（masked-only）+ DOTA#20 排除。** 足以支撑“协议在多 detector×dataset 一致”，不足以称全面 benchmark。

**S4 是否有角度单位下游收益？** **真实但 modest、cell-dependent。** SODA#4 geometry R@70 2.35°<detection 2.51°（~6%），FAIR1M（detection 弱）明显改善；DIOR 无改善。可解释（度）但幅度小 → 附录/边界。

**S5 是否完成投稿前写作基建？** **是。** rewrite plan + 真实文献清单（待补出处）+ NRC 方向示意图数据 + 一键复算脚本 + repro log 就绪。

## 综合裁决
- **S1a PASS、S1b/S1c QUALIFIED PASS（非 fail）** → 论文**不降级为技术报告**。
- 但 P2 保证 modest、geometry selector 优势非普遍、机制仅候选、下游微弱、cell 宽度有限 → 论文是 **诚实的“朝向可靠性测量协议 + 有限样本（尾部）风险控制 + 机制候选”**，边界清晰。
- **当前是否可进入中文正式论文稿？** 可以进入 **修订版**中文稿（按 S5 rewrite plan，纳入 S1–S4 真实结果与收缩 claim）；但需先完成 SODA 的 S1a 扰动 pass 收尾与文献补齐。
- **当前是否可讨论英文稿 / 投稿？** **暂不**（S1 修完但 S1b/S1c 为 qualified，且需正式稿定稿 + 文献）。
- **当前期刊级别判断？** 依判定规则：S1a 通过、S1b 未失败 → 可**谨慎恢复 TGRS / ISPRS 强候选的方向性判断**，但因保证 modest 与宽度有限，属**有条件强候选**，**不得宣称 CVPR/TPAMI ready、不得宣称已达强候选定论**。仍缺：SODA S1a 收尾、更多 cell、机制升级实验、文献。
