👇👇👇👇👇👇

# 056 覆盖版执行回执 (OR_PRE_SUBMISSION_S1S5_V1)

**056 覆盖版：完成（SODA 的 S1a 扰动 pass 后台收尾中，不影响结论）。** 全部基于真实 provenance-clean artifact，冻结 masked ar≥1.6，未训练/未推理/未追 public mAP/未改 thresholds(b7c4e649)·D_cal·D_audit/未补 full matrix。

## S1a 是否通过
**PASS。** 从 raw predictions 跑真实 full evaluator：约束角度扰动下 **4/4 已完成 cell（DIOR#22/#3/#61 + FAIR1M#24，跨 PSC/ORCNN/RTMDet）真实 AP50 完全不变（ΔAP50=0.0000）、FP@0.5 不变**，AP75 塌陷、角度 risk 升 ~7×。matched-only mAP=1.000 代理已被真实 AP50 取代。SODA#23/#4 扰动 pass 后台计算（成本）。

## S1b 是否通过
**QUALIFIED PASS。** selector-fit / conformal-calib 独立性修复（D_fit/D_calib/D_audit 互斥，guarantee 有效）。但 **geometry selector 非普遍占优**：在 detection 弱信息 cell（FAIR1M/SODA）显著更优，在 detection 已强 cell（DIOR）打平/略差；leave-cell 迁移退化 → **不写 blanket recommended default**。

## S1c 是否通过
**QUALIFIED PASS。** LTT 固定序列（二项尾部，控 FWER）+ 有界均值（Hoeffding B=90）+ image-clustered bootstrap 均实现。**有效保证 modest**：尾部保证在 detection 强 cell 成立（轻微 overshoot，CI 跨 α），弱信息 cell 需 geometry；**有界均值严格保证过保守、不实用**。

## S2 是否支持机制线
**部分（1/2）。** confounding 排除（phase_mod NRC>1 跨 class/size/ar 层持续 9/9,9/9,8/9），但**无 aliasing 频率峰**。→ phase_mod 保持 **case study / mechanism candidate；不启动重训矩阵**。DOTA#20 仅 artifact limitation。

## S3 clean cells 数量
**6 个 full-val provenance-clean cell（3 detector family × 3 dataset）进主表 + 2 masked-only 附录（DIOR#10/SODA#11）+ DOTA#20 排除。** masked detection NRC 0.41–0.91（better-than-random / non-reversed ranking，不叫 calibrated）。

## S4 下游任务结果
角度单位选择性预测（真实方向类，HRSC 仅 synthetic 故改用 ship/harbor/vehicle）：**真实但 modest、cell-dependent**（SODA#4 geometry R@70 2.35°<detection 2.51°，~6%；DIOR 无改善）。→ 附录，不写 utility proven。

## S5 写作基建
完成：rewrite plan（去项目化章节骨架 + Scope and Claims 单列 + 真实文献清单待补出处）+ NRC 方向示意图数据（oracle/random/reverse）+ 一键复算脚本 `reproduce_all_main_tables_s1s5_v1.sh`（校验 frozen 不变）+ repro log。

## 当前是否可进入中文正式论文稿
**可进入修订版中文稿**（按 rewrite plan 纳入 S1–S4 真实结果与收缩 claim）；建议先收尾 SODA 的 S1a pass 与补文献。

## 当前是否可讨论英文稿/投稿
**暂不。** S1 已修但 S1b/S1c 为 qualified，需正式稿定稿 + 文献补齐后再议。

## 期刊级别判断
S1a 通过、S1b 未失败 → 论文**不降级**；可**谨慎恢复 TGRS/ISPRS 方向性判断（有条件强候选）**，因保证 modest 与宽度有限。**不宣称 CVPR/TPAMI ready、不宣称已达强候选定论。**

## 仍缺什么
SODA 的 S1a 扰动 pass 收尾；更多 provenance-clean cell；PSC 机制升级实验（需批准）；真实 HRSC detector 预测；正式文献。

## 关键产物路径
- 决策：`docs/pre_submission_s1s5_v1/s1_s5_final_decision_v1.md`
- S1a/S1b/S1c：`docs/pre_submission_s1s5_v1/s1a_full_pipeline_perturbation_v1.md` / `s1b_conformal_independence_fix_v1.md` / `s1c_ltt_conformal_fix_v1.md`
- S1sync/S2/S3/S4/S5：同目录 `s1_sync_..._v1.md` / `s2_..._v1.md` / `s3_..._v1.md` / `s4_..._v1.md` / `s5_manuscript_rewrite_plan_v1.md`
- 表格：`reports/pre_submission_s1s5_v1/*_v1.csv`；复算：`scripts/reproduce_all_main_tables_s1s5_v1.sh`

## verification / test / git
- `scripts/verify_pre_submission_s1s5_v1.py`（见运行结果）。thresholds.yaml sha256=b7c4e649…（未变）；D_cal/D_audit 无 diff；git 无 >100MB tracked；未训练/未推理。

👆👆👆👆👆👆
