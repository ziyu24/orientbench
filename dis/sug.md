# OrientBench r010：统计—机制—主稿一次性闭环（Luna-high）

- round: `orientbench-c-r010-20260806`
- scientific snapshot: `73f8814b9d0345bfb6b99c1463a61bb01a555f40`
- source manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v079.md`
- output manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v080.md`
- unique server report: `dis/server_reports/orientbench-c-r010-20260806.md`
- runtime root: gitignored `outputs/persistent_artifacts/orientbench_r010/`
- intended executor: Luna-high

这是一次完整 repair-and-closure campaign，不拆成小轮次。目标不是“再生成一个 PASS 文件”，而是把 r009 可疑但有价值的剂量曲线变成可复算统计证据，并把结论真实写进 v080。服务器先 `git pull --ff-only`；execution HEAD 必须包含上述 scientific snapshot，且工作树和 index 干净。禁止 merge/rebase/reset/clean/force。

## 1. 已冻结裁决与唯一科学问题

正式记：`r009_protocol=FAIL_PROTOCOL_R009`，`r009_mechanism=INCONCLUSIVE_MECHANISM_R009`。不得修改或覆盖任何 r009 产物来洗白历史状态。可复用的只有：Core-6 raw identity 候选、三轨各 48 行 AP 点估计、v079 对主要 certification headline 的初步隔离；复用前必须通过本轮独立验证。

唯一问题：在冻结 full post-NMS predictions 上只改变角度并用完整 classwise evaluator 重新匹配时，AP75 是否跨数据集和 detector family 比 AP50 更早、更强下降；这一差异能否在不挑方向的 symmetric track 中成立，并由固定 baseline TP cohort 的 aspect-ratio survival 解释？本轮不声称训练改善、NMS 效应、causal deployment 或可部署 selector。

## 2. 冻结矩阵、剂量、track 与统计单位

Core-6 不得替换：

| unit | dataset | detector |
|---|---|---|
| `DIOR-R/22` | DIOR-R | rotated RetinaNet PSC |
| `DIOR-R/3` | DIOR-R | Oriented R-CNN |
| `DIOR-R/61` | DIOR-R | Rotated RTMDet-S |
| `FAIR1M-v1.0/24` | FAIR1M-v1.0 | rotated RetinaNet PSC |
| `SODA-A/23` | SODA-A | rotated RetinaNet PSC |
| `SODA-A/4` | SODA-A | Oriented R-CNN |

Extension 只在 Core gate PASS 后运行：`FAIR1M-v1.0/5` Oriented R-CNN、DOTA-v1.0 Oriented R-CNN clean unit、DOTA-v1.0 Rotated RTMDet-M clean unit。必须从已有冻结记录唯一确定 config/checkpoint/split；若身份有歧义则记 `NOT_RUN_AMBIGUOUS_EXTENSION`，不挑方便的替代单元。允许对这三项用本地已有数据、config、checkpoint 做 smoke 后 full inference；禁止训练、微调、换 checkpoint、下载或更改 split。DOTA 固定 train/val，不碰公开 test。

剂量固定为 `0,2,5,10,15,20,25,30` degree；主域 `GT ar>=2.1`；post-NMS；NMS 不重跑。确定性排序固定为 `(-score, image_id, original_prediction_index)`。

三个 track：

- `P`：对主域预测施加 `+dose`。
- `D`：只作 GT-directed diagnostic upper bound。用 dose=0 的确定性 baseline matching 冻结每个 prediction 的方向，同一方向映射用于全部剂量和 bootstrap，不得按剂量重选；未匹配 prediction 的处理规则须在 protocol 中预注册且不得按结果改变。
- `S`：分别计算 `+dose` 与 `-dose` 的完整 evaluator，AP、risk、survival 都保留两分量，并以算术平均定义 symmetric 结果。禁止用 P 代替 S，禁止丢弃分量后只留平均。

主统计单位为 image；能无歧义恢复 mother-scene 时同时以 mother-scene 做 sensitivity analysis。SODA-A tile/mother-scene 交叉无法消除时须明确限制，不得称独立 confirmatory unit。

## 3. Phase 0：真实 provenance 与冻结 protocol

生成不可变 `a4_protocol_r010.json`，记录 dataset/split、class map、angle convention、score tie、matching、GT AR、track、dose、cluster、seed=`20260806`、bootstrap=`1000`、CI/p-value 和 gate 的精确算法。

对每个 Core/有效 extension 记录 GT、image list、class map、tile map、config、checkpoint、framework/version、raw predictions 的逻辑路径、SHA-256、bytes、image/GT/prediction 数、精确生成命令和 `can_recompute`。Git 报告不得写机器名、账号、凭据或绝对路径。必须解释 FAIR1M 报告的 `78,638` 与 r009 track 的 `78,644` GT 差异；也必须解释 DIOR 11,738 split 与部分 track 的 11,732/11,734 image count。不能解释则该 unit provenance FAIL。

禁止新下载、借用其它个人项目、训练 detector、修改历史 K1/r009 脚本。大型 raw 只留 runtime root，Git 只提交 manifest/小表/脚本/文稿。

## 4. Phase 1：两个真正独立的 evaluator

主端使用项目相应官方/原生 DOTAMetric 配置；复核端使用不 import 主端函数、也不 import r009 K1 `eval_cell` 的 clean-room 实现。记录源码身份与版本。不能把两个名称指向同一函数。

Golden 必须由代码实际运行，并保存 input、手算 expected、两端 actual 和 PASS/FAIL，至少覆盖：le90 周期与 0/90°边界、class mismatch、duplicate prediction 一对一 greedy、同分稳定顺序、empty pred/GT/class、单 TP/FP/FN、post-NMS identity。静态填写 PASS 无效。

对 Core-6 dose=0 用两个 evaluator 全量计算 AP50/AP75，每项绝对差 `<=0.002`；同时与冻结 K1 authority endpoint 比较 `<=0.002`。再确定性重算每个 Core 的 dose0、D15、+15、-15，与 r009 相应值逐项比较 `<=0.002`。

若仅 r009 数值复现失败但两端 evaluator parity 通过：不得复用 r009 144 格，必须在本轮用修正 evaluator 一次重算 Core 全部 6×3×8；仍在 r010 内完成，不新开轮次。任一 official-vs-clean-room parity 失败则 `FAIL_EVALUATOR_R010` 并早停科学 gate，但仍生成全部约定文件（未运行填 `NOT_RUN_EVALUATOR`）和仅做进一步 quarantine 的 v080。

## 5. Phase 2：同一 raw 的 baseline 与全剂量表

从同一 full raw/full GT 生成 AP50、AP75、原生支持时的 AP50:95、`ar>=2.1` canonical le90 error、geometry-normalized severe event、detection-score AURC/NRC/Risk@50/70/90。每行记录 unit、dataset、split、统计单位、分母、row key、input identity 和 generator。

生成统一 tracks 表，Core 必须恰有 6×3×8=144 个 `(unit,track,dose)` 行；S 分量表必须恰有 6×2×8=96 行。若 extension 进入，则按每个有效 unit 分别增加 24 与 16 行。所有 dose=0 重复值必须完全一致；P/D/S 不得共享冒充同一文件或哈希。

风险事件表必须覆盖每个有效 unit×P/D/S×8 doses×固定 strata；S 从真实 +/− instance outcomes 求平均并保留分量。严禁 r009 的“每 unit 轮换一个 track”。

## 6. Phase 3：paired AP bootstrap（主证据）

每个有效 unit 使用同一组 1000 次 paired cluster multiplicities，seed 精确为 `20260806`；同一 replicate 同时用于 baseline、D15、+15、-15。必须在每次 resample 后重新计算完整 AP，不能 bootstrap severe-rate、对象行或预先平均的 AP。

逐 replicate 计算：

`T_D=(AP75_0-AP75_D15)-(AP50_0-AP50_D15)`

`T_plus=(AP75_0-AP75_+15)-(AP50_0-AP50_+15)`

`T_minus=(AP75_0-AP75_-15)-(AP50_0-AP50_-15)`

`T_S=(T_plus+T_minus)/2`

P 也按同口径输出。保存全部 replicate 与 point estimate、percentile 95% CI、单侧 bootstrap p；D 与 S 分别在六个 Core unit 内做 Holm 校正。support 当且仅当 point>0、95% CI lower>0 且 Holm-adjusted p<0.05。不能以点估计、severe-rate CI 或跨 unit 平均替代。

## 7. Phase 4：无 survivorship bias 的 AR survival

cohort 固定为 dose=0 时的 baseline IoU75 TP prediction identity—GT pair；此 cohort 和 GT AR bin 此后不变。AR bins 固定为 `[2.1,3)`、`[3,5)`、`[5,+inf)`。对全部 8 doses、D、+、- 分别报告：

1. 原 pair 的 IoU75 same-pair survival；
2. 完整重新匹配后，该 baseline prediction identity 是否仍是 IoU75 TP；
3. numerator/denominator、image/scene paired 95% CI。

S 的每个结果由真实 +/− 两分量平均，保留分量。不得使用“当前 dose TP”作分母。主 gate 固定 dose=15 的 rematched survival，并要求 low-AR ≥ mid-AR ≥ high-AR（允许每个相邻差 `0.01` 的数值容差）；同时公开全部剂量，禁止挑点。

## 8. 冻结 gate 与早停

`PASS_EVALUATOR_R010` 与 `PASS_PROVENANCE_R010` 是硬前置。

`PASS_STRONG_JSTARS_EVIDENCE_R010` 当且仅当：

1. Core-6 全部前置通过；
2. D15 support 至少 4/6，且 DIOR-R、FAIR1M、SODA-A 各至少一 unit support；
3. S15 同样至少 4/6 且覆盖三数据集；
4. D 的 AP75 对 8 doses 的 Spearman `<=-0.9` 且任意相邻恢复不超过 `0.002`，至少 4/6；
5. dose15 baseline-cohort AR survival 有序至少 4/6，且覆盖三数据集；
6. P 不得在任一数据集的全部 units 显示与候选机制相反；
7. baseline、ledger、manifest、只读 validator 与 v080 全部闭环。

点估计支持但 CI/有序性不足：`INCONCLUSIVE_MECHANISM_R010`。D 或 S support 少于 3/6，或任一数据集全反向：`FAIL_UNIFIED_MECHANISM_R010`。协议、seed、track、cohort、授权路径、evaluator 独立性发生事后改变：`FAIL_PROTOCOL_R010`。不得另造状态名，不得降低阈值，不得把实现失败写成普适科学负结果。

只有 Core PASS 后才进入 extension。三项 extension 全部有效，D/S 各至少 2/3 support、DOTA 至少一项 support、AR survival 至少 2/3 有序，才标 `TGRS_BORDERLINE_EVIDENCE_CANDIDATE`；否则 `TGRS_NOT_REACHED`。这仍不是 TGRS-ready。

## 9. Phase 5：v080 论文质量闭环

从 v079 新建 v080，绝不覆盖历史稿。先彻底隔离残留 formal 叙述：LTT/HB/CP 只可作为未验证的历史探索或局限，不得作为当前贡献、本文证据、部署结论或“严格风险认证失败”的科学发现。

若 r010 PASS：在摘要、贡献、A4 方法、结果、讨论、结论中加入经 gate 允许的固定剂量发现；主表至少给出六单元 dose 0/10/15/30 的 AP50/AP75、D/S contrast 与 CI，完整曲线放补充；加入可复算 SVG 图。若 INCONCLUSIVE/FAIL：只写可复核描述性曲线与明确边界，删除统一机制/knee headline。禁止补数字救故事。

必须明确：post-NMS 干预不测 NMS 效应；D 是 GT-directed upper bound；S 才是不挑方向的 falsifier；FAIR1M/24 的 knee 若不可识别就明确写不可识别；不能声称统一 knee、因果机制或 deployable selector。正文强调科学 finding/method/evidence/limitation，manifest、ledger、hash 等治理细节放附录。

真实 ledger 只收实质 claim，不收标题/参考文献。每行：

`claim_id,manuscript_section,line,text,text_sha256,claim_family,dataset,unit,estimand,result_row_keys,generator_script,input_manifest,gate,status,action,reason`

每个 retained/qualified headline 必须绑定具体结果 row keys、生成脚本、input manifest 与 gate；`dis/**` 或旧报告不能作为数字唯一证据。状态只用 `VALID|QUALIFIED|INVALID|UNRESOLVED`，动作只用 `RETAIN|QUALIFY|REMOVE`。

## 10. validator、manifest 与资源纪律

runner 与 validator 是独立入口。validator 默认 `--check`，绝对只读：运行前后对工作树、index 和所有受检文件取身份，任何变化即 FAIL。它必须实际重算/核查 golden、row set、dose/track/bin、parity、r009 deterministic check、bootstrap seed/reps/paired estimand、Holm、survival cohort/顺序、gate 布尔逻辑、ledger、v079→v080 quarantine、精确授权集合和 manifest；禁止仅查文件存在、常量 PASS 或自比自身。

CPU evaluator/bootstrap 使用至少 80% 可用 CPU，记录 worker budget 和利用率。extension inference 如触发，先 2-image smoke，再默认 4×A30 full run。operation counts 分开记录 detector training/inference、evaluator calls、bootstrap replicates、downloads、GPU hours；实际运行计数，不能从源码猜。

manifest 最后生成。记录 scientific/execution/final HEAD、protocol/input/output identity、bytes、SHA-256、规范 Git blob、生成命令、operation counts、授权集合。先完成并 stage 其它文件，再用 `git hash-object --path` 取 blob；manifest 自身 identity=`N/A_SELF_REFERENCE`。跨平台文本以规范 Git blob 为准。

## 11. 精确 Git 写入集合

本轮所有状态只允许以下 24 个路径；未运行的表保留 schema 并填标准 NOT_RUN reason。禁止创建临时 Git 文件或第二报告：

1. `claude_code_and_supervisor.md`（append-only，恰好一个 r010 section）
2. `dis/server_reports/orientbench-c-r010-20260806.md`
3. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/run_a4_closure_r010.py`
4. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/paired_ap_bootstrap_r010.py`
5. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/baseline_cohort_survival_r010.py`
6. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/validate_a4_closure_r010.py`
7. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_protocol_r010.json`
8. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_provenance_r010.csv`
9. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_evaluator_golden_r010.csv`
10. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_evaluator_parity_r010.csv`
11. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_fixed_dose_tracks_r010.csv`
12. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_symmetric_components_r010.csv`
13. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_baseline_metrics_r010.csv`
14. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_risk_event_r010.csv`
15. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_paired_ap_bootstrap_replicates_r010.csv`
16. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_paired_ap_bootstrap_summary_r010.csv`
17. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_baseline_tp_survival_r010.csv`
18. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_baseline_tp_survival_bootstrap_r010.csv`
19. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_mechanism_gate_r010.json`
20. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_claim_ledger_r010.csv`
21. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_evidence_manifest_r010.json`
22. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/a4_statistical_mechanism_r010.md`
23. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/a4_fixed_dose_curves_r010.svg`
24. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v080.md`

禁止修改 `dis/B.md`、任何 r009/历史脚本、v079 及更早稿、`.gitignore`、配置、旧报告。服务器一次性完成后只做一个普通中文 commit；不得中间 push。显式暂存以上 24 路径，禁止 `git add -A`/`.`。先运行只读 validator、JSON 解析、SVG XML 解析、相对路径检查、`git diff --check`、普通/staged diff；验证实际 changed path 集合与 manifest `authorized_changes` 精确相等，且 `dis/B.md` blob 仍为 `1a6093cf3b1f396dbee30803ae616643353ea0aa`。SSH 普通 push；禁止 force。失败保留本地 commit并如实报告。

## 12. 唯一最终回复

服务器最终回复首行只能是 `执行完毕` 或 `未执行完毕`。

第二行必须且只能是：`dis/server_reports/orientbench-c-r010-20260806.md`
