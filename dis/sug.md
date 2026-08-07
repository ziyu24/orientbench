# OrientBench r011：最终 P1 统计修复 + 有界 P3 联合主线复核（Luna-high）

- round: `orientbench-c-r011-20260807`
- scientific snapshot: `c62ea3514e98f76baf557c22a5dd0ef812d84ee0`
- P1 source manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v080.md`
- P3 neutral source: current m069/M2 Core-6 lineage；旧 `measure_fix_v2` PASS 仅作历史输入，不作结论
- output manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_measure_diagnose_fix_r011.md`
- unique report: `dis/server_reports/orientbench-c-r011-20260807.md`
- runtime root: gitignored `outputs/persistent_artifacts/orientbench_r011/`

这是 fixed-dose 机制的最后一次实现修复，同时利用空闲 CPU 对当前 P1+P3 主线做有界复核。不得拆成后续小补丁，不得用旧 PASS 填空。开始前 `git pull --ff-only`，核对 execution HEAD 包含 scientific snapshot，工作树/index 干净。禁止 merge/rebase/reset/clean/force。

## 1. 冻结裁决与目标

正式状态：`r010=FAIL_PROTOCOL_R010`，机制尚未被有效检验。不得修改任何 r009/r010 文件。可复用：Core-6 raw/full-GT 候选、full-sample fixed-dose 点曲线、当前 M2/G2DP 的 m069 lineage；复用前都需本轮身份核验。

P1 问题：正确独立 evaluator、full-GT paired bootstrap 和 fixed baseline cohort 下，AP75 是否比 AP50 对固定角度剂量更敏感，且 S 轨不依赖挑方向？

P3 问题：在当前 Core-6、`ar>=2.1`、source 仅 D_cal 训练、target 仅 D_audit 评估时，prediction-side nonlinear geometry selector 是否在 leave-dataset/leave-detector 中稳定优于 score+ar+size linear？这最多支持 cross-domain diagnostic/source-supervised target-GT-free candidate，不是 deployable method。

## 2. 冻结 Core、变换与统计单位

Core-6：`DIOR-R/22, DIOR-R/3, DIOR-R/61, FAIR1M-v1.0/24, SODA-A/23, SODA-A/4`，不得替换。剂量 `0,2,5,10,15,20,25,30`；post-NMS；不重跑 NMS；main domain `ar>=2.1`；seed=`20260807` 用于 r011 新测试，fixed-dose paired bootstrap 为延续可比性仍固定 seed=`20260806`、1000 reps。

- P：对 prediction AR>=2.1 的预测固定施加 `+dose`。
- D：先用 dose0 IoU50 matching 冻结 prediction→GT；仅扰动匹配且 matched GT AR>=2.1 的 prediction。用 baseline canonical signed residual 冻结方向：residual>0 取 `+`，<0 取 `-`，等于0取 `+`；全部剂量使用同一 mapping。未匹配 prediction 完全不动。
- S：对 prediction AR>=2.1 分别计算真实 `+dose`/`-dose`；AP、risk、survival、bootstrap 均保留分量并取算术平均。禁止用 P 代替 S。

主 cluster 为完整 split image universe，包括无 GT、无 prediction 和 GT-only image。能无歧义恢复 mother-scene 时仅作 sensitivity，不改变主 gate。

## 3. Phase A：provenance 与 executable preflight

对每个 unit 记录 frozen split image-list、GT、class map、tile/mother map、config/checkpoint/framework、prediction raw、生成命令、SHA-256/bytes/schema/count。合法关系应对 frozen split universe 分别验证 `GT image IDs subset universe` 与 `prediction image IDs subset universe`；prediction 文件无空记录时，不要求 GT IDs subset prediction IDs。SODA-A/4 的 extra IDs、FAIR1M 78,638/78,644 和 DIOR 缺 prediction-bearing images 必须逐 identity 解释；不能闭合则该 unit provenance FAIL。

先生成机器可执行 golden，不允许常量表。至少覆盖 le90/w-h swap、0/90边界、class mismatch、duplicate greedy、stable ties、empty pred/GT/class、GT-only image/class、single TP/FP/FN、zero-pred image、post-NMS identity。

paired AP 优化器必须先与显式 brute-force cluster resampling 对照：至少 20 synthetic cases + 每个 Core 10 个真实小规模 draws；AP50/AP75/contrast 绝对误差 `<=1e-12`。它必须携带每 image×class 的 full GT count，recall denominator=`sum multiplicity×GT_count`，包含 GT-only classes/images；point estimate 来自未重采样 full sample，不是 bootstrap mean。preflight 任一失败，先在本轮修复；仍失败则 `FAIL_IMPLEMENTATION_R011`，P1 CI 永久 quarantine，不运行昂贵全量 bootstrap。

## 4. Phase B：真实双 evaluator 与 GPU 调度

端 A 必须调用仓库环境中实际官方/原生 DOTAMetric endpoint；端 B 是不 import 端 A evaluator/AP/matching 函数的 clean-room evaluator，并使用独立 overlap path。两者可共享原始输入 schema，但不得共享计算函数。记录代码版本和精确命令。官方 endpoint 不可用则 `FAIL_EVALUATOR_R011`，不得以自写函数冒充。

在全部 Core dose0、D15、+15、-15 上做双端 full parity，AP50/AP75 每项差 `<=0.002`。若 r010 点曲线与合格端差超过 `0.002`，本轮用端 A 重算全部 6×3×8，不得再开轮次。

GPU：默认同时使用 4×A30，一 GPU 一 evaluator shard；即使发现小程序占用也先运行，只有真实 OOM 才缩小 IoU chunk/batch，仍优先保留 4 卡。连续两次有日志的 OOM 才允许减少 GPU 数，并记录时间、显存和回退。禁止等待“全空闲”后才跑。SODA 两重单元分配到不同 GPU，其余动态队列；每卡 smoke 2 images 后直接 full run。禁止 detector training/inference/download。

## 5. Phase C：正确 paired AP bootstrap 与机制表

对每 unit 用同一 1000 组 image multiplicities同时计算 baseline、P15、D15、+15、-15。每 replicate 从完整 split image universe 有放回抽样，按官方 AP 定义重建 per-class precision/recall 和 class mean。输出 full-sample point、bootstrap mean/bias、percentile 95% CI、centered one-sided bootstrap p；D/S 六项各自 Holm 校正。support 当且仅当 full-sample point>0、CI lower>0、Holm p<0.05。

固定 baseline IoU75 TP prediction identity—GT cohort；GT AR bins=`[2.1,3),[3,5),[5,+inf)`。对 D、+、-、S × 8 doses × 3 bins 同时输出 same-pair IoU75 survival 与“该 prediction identity 完整 rematch 后仍为任一 IoU75 TP”的 survival；S 从真实 +/- replicate-wise 平均。主 gate dose15，low≥mid≥high，容差0.01。禁止用当前 dose TP 作分母或要求原 GT pair才算 rematched。

risk 固定 universe显式含空 stratum；输出 P,D,+,-,S × 8 doses × `all+3 bins`。S 是分量平均。baseline 同一 raw 补 AP50/AP75、le90/severe event、AURC、NRC、Risk@50/70/90、分母和 row key。

## 6. Phase D：并行有界 P3 revalidation

仅用当前 m069/Core-6 lineage重建 `ar>=2.1` prediction-side feature table。冻结 split、D_cal/D_audit、feature definitions、model class/hyperparameters；source 训练只读 source D_cal，禁止 source D_audit/target GT 进入 fit、feature selection、early stopping或超参数选择。target D_audit GT仅用于最终评价。

比较 score-only、score+ar+size linear、nonlinear geometry-aware。运行所有结构上可定义的 leave-dataset 与 leave-detector folds；RTMDet 只有单数据集来源时明确 `NOT_IDENTIFIABLE`，不复制其它 family。1000 次 image-cluster paired bootstrap，报告 NRC delta、CI、训练/目标 row keys、dataset/family覆盖和泄漏检查。

另将不训练的 standalone local-angle consistency proxy 单独报告；不得称 real TTA。旧 039/040/041 的数字只作对照，不进入 gate。P3 PASS 需：无泄漏；至少 60% eligible target folds 的 nonlinear-size-linear NRC delta CI lower>0；覆盖至少2 datasets和2 detector families；任一 dataset/family不得全部反向。否则 `P3_CROSS_DOMAIN_INCONCLUSIVE_R011` 或 `FAIL_P3_TRANSFER_R011`。PASS 仍只写 source-supervised target-GT-free diagnostic candidate。

## 7. CPU 并行与遥测

CPU 总量48核。CPU密集阶段对整个进程组设置 aggregate CPU quota=`3840%`（等价48核的80%），并以动态 worker queue将持续利用率保持在80%目标且不超过80%持续上限。若系统不允许 quota，使用38 workers+轻量 coordinator并每30秒根据 aggregate utilization sleep-throttle；记录实际均值、p10/p90、worker budget与原因。`OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=1`，禁止 nested oversubscription。

GPU evaluator与CPU bootstrap/P3在无数据依赖时并行流水；不要等全部 GPU 完成才启动已就绪的 CPU unit。遥测每30秒记录 phase、wall time、CPU aggregate、RAM、四卡利用率/显存、worker数；runtime full log 留 ignored root，Git 提交摘要及日志身份。资源不足只能改变并行度/批量，不能改变协议。

## 8. 冻结 gate

P1 状态只允许：

- `PASS_STRONG_JSTARS_EVIDENCE_R011`：provenance与双 evaluator全过；D15、S15各≥4/6 support且各覆盖DIOR/FAIR/SODA；D AP75单调条件≥4/6；AR survival有序≥4/6且覆盖三数据集；P无整数据集反向；baseline/ledger/稿件闭环。
- `INCONCLUSIVE_MECHANISM_R011`：实现有效但 CI/有序性不足。
- `FAIL_UNIFIED_MECHANISM_R011`：D或S少于3/6，或任一数据集全反向。
- `FAIL_PROTOCOL_R011` / `FAIL_EVALUATOR_R011` / `FAIL_IMPLEMENTATION_R011`：相应前置失败。

gate 必须逐布尔条件记录，不得从状态字符串大小写推断，不得另造 PASS。P3 使用上一节枚举。joint 状态：P1/P3至少有合法有效结果且 P3 PASS、M2 provenance有效、v081/ledger/manifest闭环，才可 `TGRS_EVIDENCE_CANDIDATE_R011`；否则 `TGRS_NOT_REACHED_R011`。这不是 TGRS-ready。

r011 后无 r012 fixed-dose 实现补丁：若 P1 实现前置再失败，永久删除 fixed-dose CI/统一机制 headline，只保留独立复核过的描述性点曲线。

## 9. Phase E：v081 联合稿

新稿必须在参考文献前完整整合，不得把结果附加在参考文献后。摘要、贡献、定义、实验、主表/图、结果、讨论、限制、结论按真实 gate一致重写。

彻底删除/历史化旧 formal certification：LTT/HB/CP 不得作为当前贡献、当前统计方法、部署失败结论或工具箱 headline。删除“fixed-dose raw不完整”的过期矛盾。P1 PASS才写机制 CI；否则只写合格点曲线/边界。P3 PASS才写 cross-domain diagnostic candidate；禁止 `deployable method`、`fully GT-free selector`、旧 STABLE-PASS、统一 knee、NMS/因果或TGRS-ready。

ledger只收实质 claims，逐条绑定具体 manuscript line/text hash、CSV row keys、generator、input manifest、gate和 action；至少覆盖摘要、贡献、P1、M2、P3、人工标注、统计单位、限制和所有数字 headline。

## 10. validator/manifest/提交纪律

validator绝对只读，运行前后工作树/index/file identities不变。它必须独立重算：golden actual、official-clean parity、bootstrap optimized-vs-bruteforce、full point vs summary、GT denominator、Holm、row universe、D unmatched unchanged、S平均、三AR bins/rematch定义、P1/P3每个 gate、P3 split leakage、ledger、v080→新稿、授权集合、manifest。`ALLOWED` 必须实际使用。常量PASS、自比自身、存在性检查无效。

所有 CSV 用 `lineterminator='\n'`，文本规范LF；提交前 `git diff --check` 必须0输出。一次性完成、只做一个最终中文 commit，不得中间提交/push；root记录恰好append一个r011 section且之后不改。

manifest最后生成，`authorized_changes`与实际33路径精确一致；记录 scientific/execution/final HEAD、全部 input/output SHA-256/bytes/Git blob、生成命令、runtime日志身份、资源遥测与真实 operation counts。self identity=`N/A_SELF_REFERENCE`。

## 11. 精确 Git 写入集合（33）

1. `claude_code_and_supervisor.md`
2. `dis/server_reports/orientbench-c-r011-20260807.md`
3. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/run_joint_closure_r011.py`
4. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/official_evaluator_adapter_r011.py`
5. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/cleanroom_evaluator_r011.py`
6. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/paired_full_ap_bootstrap_r011.py`
7. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/fixed_cohort_mechanism_r011.py`
8. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/p3_cross_domain_r011.py`
9. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/validate_joint_closure_r011.py`
10. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/joint_protocol_r011.json`
11. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/resource_telemetry_r011.csv`
12. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/provenance_r011.csv`
13. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/evaluator_golden_r011.csv`
14. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/evaluator_parity_r011.csv`
15. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/fixed_dose_tracks_r011.csv`
16. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/symmetric_components_r011.csv`
17. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/baseline_metrics_r011.csv`
18. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/risk_event_r011.csv`
19. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/paired_ap_bootstrap_replicates_r011.csv`
20. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/paired_ap_bootstrap_summary_r011.csv`
21. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/baseline_tp_survival_r011.csv`
22. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/baseline_tp_survival_bootstrap_r011.csv`
23. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/p3_cross_domain_results_r011.csv`
24. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/p3_cross_domain_bootstrap_r011.csv`
25. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/p1_gate_r011.json`
26. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/p3_gate_r011.json`
27. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/joint_gate_r011.json`
28. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r011.csv`
29. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/evidence_manifest_r011.json`
30. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/joint_evidence_r011.md`
31. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/fixed_dose_curves_r011.svg`
32. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/p3_cross_domain_r011.svg`
33. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_measure_diagnose_fix_r011.md`

禁止修改其它路径，尤其 `dis/B.md`、所有 r009/r010资产、v080、旧 `measure_fix_v2`、`.gitignore`、split/threshold/config。未运行输出保留schema和标准NOT_RUN reason。显式暂存33路径，禁止 `git add -A`/`.`。验证 `dis/B.md` blob仍为 `1a6093cf3b1f396dbee30803ae616643353ea0aa`。通过 HTTPS 普通 push 当前分支，不改 origin，禁止force；失败保留本地commit并如实报告。

## 12. 唯一最终回复

首行只能是 `执行完毕` 或 `未执行完毕`。

第二行必须且只能是：`dis/server_reports/orientbench-c-r011-20260807.md`
