# S5 —— 写作与可信性基建 (v1)

## 1. 风格重写要求
- 正文删除项目管理词：P1/P2/P3/P4/P5、precise-pass、invalid_pending、裁决、PASS/FAIL、版本号、"本轮"、监督、verifier。改为科学章节叙述（引言/协议/测量/风险控制/机制/下游/局限/结论）。
- claim ledger、forbidden claims、sha256、复现细节 → 附录。
- **Scope and Claims 单独一节**集中写边界与不可外推项。
- NRC<1 用 better-than-random / non-reversed / informative ranking；calibrated 仅限概率/conformal 语境。
- 用 OBB，不用 “OOD” 缩写。

## 2. 章节骨架（重写目标）
1. 引言：mAP 对朝向的几何门控盲区（S1a 真实 evaluator：约束扰动下 AP50 不变、AP75 塌陷、角度 risk 升）。
2. 相关工作（补真实文献，见 §4）。
3. 朝向可靠性测量协议：角度误差（long-side）、GV-obliquity、masked ar≥1.6 主口径、NRC/AURC/risk-coverage、D_fit/D_calib/D_audit。
4. 测量层：mAP 盲区（S1a real evaluator）+ aspect-ratio cliff（冻结 masked 分位）。
5. 有限样本风险控制：LTT 固定序列 + 二项尾部保证 + 有界均值（Hoeffding B=90，诚实标其保守）+ image-clustered CI；score menu（geometry 在弱信息 cell 更优，非普遍默认）；shift 退化如实报告。
6. 机制：masked 下 detection non-reversed、intrinsic phase_mod reverse（confounding 排除、无 aliasing 峰）→ 机制候选。
7. 下游（附录）：角度单位选择性预测，真实但 modest。
8. Scope and Claims + 局限。
9. 结论。

## 3. 需补真实文献（不编造）
- Conformal risk control / RCPS / Learn-Then-Test（LTT）。
- Selective prediction / risk-coverage。
- Detector calibration / D-ECE。
- 角度编码：CSL / DCL / PSC。
- 分布/几何角度损失：GWD / KLD。
- square-like / near-square ambiguity。
- Conformal under distribution shift。
> 正式定稿时补真实出处，占位处标“待补”，不得编造作者/年份/会议。

## 4. NRC 方向示意图
数据：`figures/pre_submission_s1s5_v1/nrc_direction_schematic_v1.csv`。展示 NRC=0 oracle / NRC=1 random / NRC>1 reverse ranking 三档，标注 detection（<1，non-reversed）与 phase_mod（>1，reverse）位置。

## 5. 一键复算脚本
`scripts/reproduce_all_main_tables_s1s5_v1.sh`：从 raw provenance-clean artifact 到全部 S1–S4 主表；只读 frozen assets，运行前后校验 thresholds.yaml sha256 未变、D_cal/D_audit 无 diff；日志入 `logs/repro_*.log`。
