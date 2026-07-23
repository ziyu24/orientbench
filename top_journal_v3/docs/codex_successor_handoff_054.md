# Codex 后续交接文件 054

生成时间：2026-07-03 12:36:14 CST

适用对象：后续接手 OrientBench / Orientation Reliability 项目的 Codex、Claude Code 或合作者。

本文件目的：集中记录当前 agent 接手前后的项目状态、执行方式、真实证据结果、当前论文定位、关键产物路径、禁区和建议下一步。后续不应从零开始，也不应把 053/054 的收缩裁决改写成强主张。

## 1. 必须先读的规则与总边界

后续接手第一步仍应读：

- `AGENTS.md`
- `项目执行文件_v2_measure_fix.md`
- `top_journal_v3/docs/codex_latest_report.md`
- `top_journal_v3/docs/top_journal_evidence_decision_053.md`
- `top_journal_v3/docs/final_reduced_scope_paper_plan_054.md`
- 本交接文件：`top_journal_v3/docs/codex_successor_handoff_054.md`

硬禁区仍然有效：

- 不修改 `thresholds.yaml`。
- 不修改 D_cal / D_audit split。
- 不修改 formal / exploratory 标签。
- 不重训 host。
- 不追 DOTA public mAP。
- 不补 full matrix。
- 不把 proxy/synthetic 写成 final evidence。
- 不把 P1 partial 写成 pass。
- 不把 P3/P4 partial 或 P5 fail 包装成方法成功。
- 不声称 PSC mechanism proven。
- 不声称 downstream utility proven。
- 不声称 NRC strictly independent from mAP。
- 不声称 broader top-tier ready、detector leaderboard 或 full project complete。

当前路线已经确定为：

`Orientation Reliability Benchmark + Conformal Risk Control`

P2 是当前最稳正贡献；P1 是 partial 测量证据；P3/P4/P5 是边界、负结果和未来工作。

## 2. 我接手前是什么状态

项目在 049-052 之间经历了从“顶刊证据升级”到“真实 artifact 恢复”的转向。

049 的状态：

- 生成了一个 partial evidence package。
- 问题是部分证据仍含 proxy/synthetic 或不完整 artifact，不允许写成顶刊证据。
- 049 的 P1/P2/P3/P4/P5 不能作为最终真实 detector evidence。

050 的状态：

- 监督指令要求先补齐 non-synthetic / non-proxy real detector artifacts。
- 重点变为 real artifact inventory、raw/schema/matched tables、PSC Track A dump 和 TTA circular artifacts。
- 核心结论：问题不是科学主线彻底失败，而是真实 evidence artifacts 不完整。

051 的状态：

- 要求新 Codex 不从零开始，先做交接定位。
- 重点查找 `top_journal_v3/`、`measure_fix_v2/`、`docs/`、`outputs/persistent_artifacts/`、`outputs/predictions/` 等目录。
- 产物包括交接地图、artifact locator、real cell status 和 gap plan。

052 的状态：

- 进入真实重建，不再只做 inventory。
- 已补齐 052 real artifacts：
  - DOTA #20 phase_mod forward dump。
  - 7 个关键 cell full matched 17-field tables。
  - 4 个 PSC cell per-matched phase_mod full table。
  - 7 个 TTA circular variance full tables。
- 关键真实 artifact 目录：
  - `outputs/persistent_artifacts/orientbench_real_052/`
  - `outputs/persistent_artifacts/manifest_052.json`
  - `top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv`
  - `top_journal_v3/reports/tta_circular_variance_full_052.csv`
  - `top_journal_v3/reports/full_matched_tables_052.csv`

052 之后，项目具备真实 artifact 复跑 P1-P5 的条件。

## 3. 我接手后做了什么

### 3.1 053：真实证据 P1-P5 复跑收口

接手时，`top_journal_v3/scripts/run_053_real_evidence_p1_p5.py` 已经开始运行，并处于 P1 raw/schema 扰动重匹配阶段。我没有重启脚本，而是持续监控进程、heartbeat 和文件读取位置，等待其完成。

运行脚本：

```bash
python top_journal_v3/scripts/run_053_real_evidence_p1_p5.py 2>&1 | tee top_journal_v3/logs/run_053_real_evidence_p1_p5.log
```

该脚本做了：

- P1：只使用 052 real raw/schema artifacts，在 raw predictions 上注入 angle / reverse perturbation，重新匹配并重新计算 mAP、AP75、NRC、AURC、Risk@70、Risk@90。
- P2：使用 052 full real matched tables 和 frozen D_cal / D_audit 做 within-cell conformal risk control，并做 shift audit。
- P3：使用 052 per-matched phase_mod full table 做 DOTA #20 negative control、aliasing histogram 和 confounding check。
- P4：使用 052 TTA circular variance full table；角度方差使用 theta -> 2theta circular statistics。
- P5：使用 052 real matched predictions 做 angle-induced rIoU drop 下游任务。

我随后新增并运行 verifier：

- `top_journal_v3/scripts/verify_real_evidence_p1_p5_rerun_053.py`

053 验证结果：

- `verify_real_evidence_p1_p5_rerun_053.py`：PASS。
- `pytest -q tests/test_bench_core0.py`：17 passed。
- `thresholds.yaml` / D_cal / D_audit protected diff：clean。
- tracked git big-file check：clean。

053 最终裁决：

- P1 = partial。
- P2 = pass。
- P3 = partial。
- P4 = partial。
- P5 = fail。
- `top_journal_discussion_level = false`
- `remote_sensing_journal_ready = possible`
- `broader_top_tier_claim = insufficient`
- 不建议申请 PSC 重训矩阵。

关键结果数值：

- P1：30 deg angle perturbation 下 mean |Delta angle risk| = 26.4883 degrees，但 mean |Delta mAP@0.5| = 0.1810，因此构造性解耦不能写 pass。
- P2：七个关键 cell within-cell conformal audit violation rate 均为 0，coverage 约为 0.93-0.95，alpha=15 degrees。
- P3：三项 PSC 免费机制测试仅 1/3 支持，PSC 保持 mechanism candidate / case study。
- P4：mean geometry NRC=0.9579，mean TTA circular NRC=0.9478，geometry-aware selector 未稳定打赢 TTA circular baseline。
- P5：mean risk improvement vs score-only=-0.0018，vs size-linear=-0.0016，downstream benefit fail。

053 主产物：

- `top_journal_v3/docs/top_journal_evidence_decision_053.md`
- `top_journal_v3/docs/p1_constructive_decoupling_experiment.md`
- `top_journal_v3/docs/p2_conformal_orientation_risk_control.md`
- `top_journal_v3/docs/p3_psc_free_mechanism_tests.md`
- `top_journal_v3/docs/p4_uncertainty_baselines_circular_stats.md`
- `top_journal_v3/docs/p5_downstream_selective_orientation_task.md`
- `top_journal_v3/docs/writing_sync_patch_053.md`
- `top_journal_v3/reports/p1_angle_perturb_dose_response.csv`
- `top_journal_v3/reports/p1_reverse_perturb_decoupling.csv`
- `top_journal_v3/reports/conformal_within_cell_risk_control.csv`
- `top_journal_v3/reports/conformal_shift_violation_audit.csv`
- `top_journal_v3/reports/psc_dota20_phase_mod.csv`
- `top_journal_v3/reports/uncertainty_baselines_nrc.csv`
- `top_journal_v3/reports/downstream_selective_orientation.csv`

### 3.2 054：收缩版中文论文定稿

053 裁决确认后，监督指令要求停止追 broader top-tier claim，停止继续硬拗 P3 方法成功，停止补大实验，进入收缩版真实证据论文定稿。

我没有新增实验、没有训练、没有改 thresholds、没有改 D_cal / D_audit。只做写作、claim 收缩和 verifier。

054 新论文定位：

`Orientation Reliability Benchmark + Conformal Risk Control`

054 写作产物：

- `top_journal_v3/docs/final_reduced_scope_paper_plan_054.md`
- `top_journal_v3/docs/orientation_reliability_reduced_scope_paper_zh.md`
- `top_journal_v3/docs/negative_results_and_boundaries_054.md`
- `top_journal_v3/docs/conformal_risk_control_main_claim_054.md`
- `top_journal_v3/docs/final_claim_ledger_reduced_scope_054.md`
- `top_journal_v3/scripts/verify_reduced_scope_paper_054.py`

054 中文正式论文稿：

- 路径：`top_journal_v3/docs/orientation_reliability_reduced_scope_paper_zh.md`
- 内容包括：
  - 标题、摘要、关键词。
  - 1-12 节正式论文结构。
  - P1 partial、P2 pass、P3/P4 partial、P5 fail 的如实写入。
  - 8 个图占位。
  - 8 个表格 / 表格清单。
  - A-G 附录。
  - forbidden claims 下沉到 claim ledger。

054 verifier：

```bash
python -m py_compile top_journal_v3/scripts/verify_reduced_scope_paper_054.py
python top_journal_v3/scripts/verify_reduced_scope_paper_054.py
pytest -q tests/test_bench_core0.py
```

054 验证结果：

- `verify_reduced_scope_paper_054.py`：PASS。
- `pytest -q tests/test_bench_core0.py`：17 passed。
- py_compile：PASS。
- `thresholds.yaml` / D_cal / D_audit protected diff：clean。
- tracked git big-file check：clean。
- 未使用 GPU。
- 未训练。
- 未新增实验。

054 latest report：

- `top_journal_v3/docs/codex_latest_report.md`

## 4. 当前真实证据该怎么写

允许写：

- 本文建立 orientation reliability benchmark / analysis。
- mAP 未充分刻画 OBB angle reliability。
- P1 提供 partial evidence，不是强解耦。
- P2 within-cell conformal orientation risk control 成立，是当前主正贡献。
- Shift audit 只报告 degradation，不承诺严格 shift guarantee。
- P3/P4/P5 是边界和负结果。
- 052 artifacts 支撑 artifact-governed reproducibility。

必须限定写：

- NRC 提供 mAP 未充分覆盖的 reliability signal，但不严格独立于 mAP。
- Geometry-aware selector 可作为分析参照或候选 score，但不是 validated deployable method。
- PSC phase_mod 可作为 mechanism candidate，不是 mechanism proof。
- P5 下游任务当前失败，不能外推为下游收益。

禁止写：

- P3 方法成功。
- PSC 机制已证明。
- 下游实用性已证明。
- NRC 与 mAP 严格独立。
- broader top-tier ready。
- full project complete。
- detector leaderboard 或 DOTA public mAP claim。
- conformal 是普通 selection score。
- shift setting 下有严格 conformal guarantee。

## 5. 当前目录和产物怎么用

### 5.1 论文写作主入口

- 中文正式论文稿：`top_journal_v3/docs/orientation_reliability_reduced_scope_paper_zh.md`
- 收缩版论文计划：`top_journal_v3/docs/final_reduced_scope_paper_plan_054.md`
- P2 主贡献说明：`top_journal_v3/docs/conformal_risk_control_main_claim_054.md`
- 负结果边界：`top_journal_v3/docs/negative_results_and_boundaries_054.md`
- Claim ledger：`top_journal_v3/docs/final_claim_ledger_reduced_scope_054.md`

### 5.2 真实证据裁决

- 053 总裁决：`top_journal_v3/docs/top_journal_evidence_decision_053.md`
- 054 latest report：`top_journal_v3/docs/codex_latest_report.md`
- 053 heartbeat：`top_journal_v3/reports/heartbeat_053.json`

### 5.3 P1-P5 报告

- P1：`top_journal_v3/docs/p1_constructive_decoupling_experiment.md`
- P2：`top_journal_v3/docs/p2_conformal_orientation_risk_control.md`
- P3：`top_journal_v3/docs/p3_psc_free_mechanism_tests.md`
- P4：`top_journal_v3/docs/p4_uncertainty_baselines_circular_stats.md`
- P5：`top_journal_v3/docs/p5_downstream_selective_orientation_task.md`

### 5.4 P1-P5 数据表

- P1 dose response：`top_journal_v3/reports/p1_angle_perturb_dose_response.csv`
- P1 reverse perturb：`top_journal_v3/reports/p1_reverse_perturb_decoupling.csv`
- P2 within-cell：`top_journal_v3/reports/conformal_within_cell_risk_control.csv`
- P2 shift audit：`top_journal_v3/reports/conformal_shift_violation_audit.csv`
- P3 phase_mod：`top_journal_v3/reports/psc_dota20_phase_mod.csv`
- P3 aliasing：`top_journal_v3/reports/psc_phase_mod_aliasing_hist.csv`
- P3 confounding：`top_journal_v3/reports/psc_phase_mod_confounding_check.csv`
- P4 uncertainty：`top_journal_v3/reports/uncertainty_baselines_nrc.csv`
- P5 downstream：`top_journal_v3/reports/downstream_selective_orientation.csv`

### 5.5 052 real artifacts

- Manifest：`outputs/persistent_artifacts/manifest_052.json`
- Persistent root：`outputs/persistent_artifacts/orientbench_real_052/`
- Full matched tables summary：`top_journal_v3/reports/full_matched_tables_052.csv`
- PSC full per-matched phase_mod：`top_journal_v3/reports/psc_phase_mod_permatched_full_052.csv`
- TTA circular full table：`top_journal_v3/reports/tta_circular_variance_full_052.csv`

### 5.6 Verifiers

- 052 real dump verifier：`top_journal_v3/scripts/verify_real_dump_matched_tables_052.py`
- 053 real evidence verifier：`top_journal_v3/scripts/verify_real_evidence_p1_p5_rerun_053.py`
- 054 reduced paper verifier：`top_journal_v3/scripts/verify_reduced_scope_paper_054.py`

## 6. 当前 git / 工作区情况

工作区仍有既有 modified / untracked 文件，这是项目历史状态，不要清理、不要 revert、不要删除未跟踪文件。

最近检查：

- `thresholds.yaml` / `configs/thresholds.yaml` / `*D_cal*` / `*D_audit*` protected diff clean。
- tracked git big-file check clean。
- `pytest -q tests/test_bench_core0.py`：17 passed。

已知 `git status --short` 仍会显示：

- `claude_code_and_supervisor.md` modified。
- 若干 `outputs/bench_core/reports/...` modified。
- `top_journal_v3/` untracked。
- 多个历史 cache / gt_index / outputs untracked。

这些不是本轮需要清理的问题。后续若要提交，需要先由监督员决定提交范围和大文件策略。

## 7. 后续建议

优先做文字定稿，不做实验扩张：

1. 合作者审稿中文稿：重点看 P2 guarantee 表述、P1 partial 的语气、P3/P4/P5 负结果是否过重或过轻。
2. 补正式参考文献 bib：使用真实论文，不编造作者、年份、会议或页码。
3. 根据 CSV 生成正式图，而不是新增实验：
   - 图2：IoU(delta theta; aspect ratio)。
   - 图3：P1 dose-response。
   - 图4：P2 coverage / violation。
   - 图5：shift audit。
   - 图6：P3 mechanism tests。
   - 图7：P4 TTA circular baseline。
   - 图8：P5 negative downstream。
4. 将中文稿转成英文稿或投稿模板时，保持 claim ledger 不变。
5. 每次改稿后运行：

```bash
python top_journal_v3/scripts/verify_reduced_scope_paper_054.py
pytest -q tests/test_bench_core0.py
git diff --name-only -- thresholds.yaml configs/thresholds.yaml '*D_cal*' '*D_audit*'
git ls-files -z | xargs -0 -r du -b 2>/dev/null | awk '$1>100000000{print}' | sort -nr | head -20
```

## 8. 不建议后续继续做的事

- 不建议继续补 full matrix。
- 不建议启动 PSC 重训矩阵。
- 不建议继续找一个下游任务硬凑 success。
- 不建议把 P2 写成和 score-only / geometry-aware selector 并列的 score。
- 不建议为了好看改 D_cal / D_audit 或 thresholds。
- 不建议引用 DOTA public mAP。

## 9. 一句话当前状态

项目已经从“broader top-tier evidence upgrade”收缩为“Orientation Reliability Benchmark + Conformal Risk Control”。真实证据中 P2 within-cell conformal risk control 是主正贡献；P1/P3/P4/P5 的 partial/fail 已经写入中文正式稿和 claim ledger。下一步应该交合作者审稿并做引用、图表和语言定稿，而不是继续扩实验。

## 10. 交接文件路径

本文件路径：

`top_journal_v3/docs/codex_successor_handoff_054.md`
