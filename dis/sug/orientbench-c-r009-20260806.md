# OrientBench r009：Orientation Intervention Evidence Closure

- round: `orientbench-c-r009-20260806`
- scientific snapshot: `c51c9f826028e083633edbaaa7ad32d1178a5744`
- source manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v078.md`
- output manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v079.md`
- unique server report: `dis/server_reports/orientbench-c-r009-20260806.md`
- runtime raw root: gitignored `outputs/persistent_artifacts/orientbench_r009/`

本任务是一次完整 evidence-closure campaign。不得拆成后续“小修轮次”，不得回到 split-FST/C2-R，不得只做文稿或 ledger。服务器先 `git pull --ff-only`，记录实际 execution HEAD；它必须包含 scientific snapshot 且工作树/index 干净。

## 1. 唯一科学问题

在冻结的完整 post-NMS 检测输出上只干预角度、随后用完整 classwise evaluator 重新匹配时，AP@0.75 是否跨数据集与 detector head 比 AP@0.5 更早、更强响应；这种差异是否与长宽比/几何可辨识性一致，而不是 matched-only、partial-GT 或协议构造假象？同一批 raw 必须同时闭合 baseline AP、角度风险排序、固定剂量干预和主稿 headline 的生成端。

r008 的提交范围/provenance 可保留，但两个科学 gate 均被 C 拒绝：

- `hygiene_gate = FAIL_CLAIM_QUARANTINE_R008`
- `measurement_core_status = INCONCLUSIVE_CORE_EVIDENCE`

原因是 v078 与 v077 字节相同，215-row ledger 没有 claim-level 证据语义，validator 的 sufficient 仅由 `len(ledger)>=3` 产生。r009 不修补 r008 文件，不把该失败写成论文负结果。

## 2. 冻结矩阵与禁止替换

### 2.1 Core-6（主 gate，缺一不可）

| unit | dataset | detector |
|---|---|---|
| `DIOR-R/22` | DIOR-R | rotated RetinaNet PSC |
| `DIOR-R/3` | DIOR-R | Oriented R-CNN |
| `DIOR-R/61` | DIOR-R | Rotated RTMDet-S |
| `FAIR1M-v1.0/24` | FAIR1M-v1.0 | rotated RetinaNet PSC |
| `SODA-A/23` | SODA-A | rotated RetinaNet PSC |
| `SODA-A/4` | SODA-A | Oriented R-CNN |

不得因结果、缺资产或运行方便替换 unit/checkpoint/split。Core 缺失不能由 extension 补位。

### 2.2 Extension（仅 Core 完成后运行）

- `FAIR1M-v1.0/5` Oriented R-CNN；
- DOTA-v1.0 Oriented R-CNN clean unit；
- DOTA-v1.0 Rotated RTMDet-M clean unit。

仅在各自 frozen config、checkpoint、正确 full-validation split、full GT 与完整 raw identity 全部闭合时进入。DOTA 只用本地 train/val baseline，不比较公开 test mAP。extension 失败不改变 Core gate，也不得选择其它 unit 替代。

## 3. 固定资产与允许的计算

1. 优先使用服务器持久化的完整 post-NMS raw predictions；必须覆盖完整评测 universe，并保留 image ID、class、score、cx、cy、w、h、theta 与 prediction identity。
2. Core raw 缺失时，允许用仓库/只读 `pth_data` 已登记的 frozen config 与 checkpoint，对正确 full-validation split 做一次 detector inference 并持久化到 runtime raw root。先检查 `pth_data/readme.md`；不可读则停止。
3. 禁止训练、微调、换 checkpoint、改 split、下载新权重/数据、借用其它个人项目结果、追 DOTA 公开 mAP或补 full 9-detector matrix。
4. 记录 dataset/split、GT、class map、tile/mother-scene mapping、config、checkpoint、framework/version、raw 的 SHA-256、bytes、图像/GT/预测数与精确命令。报告使用逻辑路径或 repo-relative path，不写机器名、账号或本机绝对路径。
5. matched-only、partial-GT、旧 partial universe、缺 prediction identity 的表不能替代 full raw；历史 K1 数字仅用于 dose=0 parity。
6. inference 默认使用 4×A30；先每 unit 2 images smoke test，再正式 full inference。若框架/config/checkpoint 不匹配，标 INVALID 并早停，不自行迁移模型。

## 4. Phase 0：preflight、协议冻结与幂等性

- 所有 r009 Git 输出、runtime raw 目录和根记录 round marker 在首次运行前必须不存在；存在即停止，不覆盖、不重复 append。
- 从 `a4_protocol_frozen.json` 继承：dose=`0,2,5,10,15,20,25,30` degree，主域 `ar>=2.1`，post-NMS 干预，NMS 不重跑，完整 evaluator 重新匹配。
- 冻结 evaluator、class map、score tie rule、angle convention、GT aspect ratio、image/scene cluster unit、seed=`20260806`、bootstrap=`1000`。
- 生成 `a4_fixed_dose_protocol_r009.json` 后不得修改协议。任何科学性偏离写 `PROPOSED_DEVIATION` 并停止。

## 5. Phase 1：独立 evaluator gate

主生成端使用项目对应的官方 DOTAMetric/等价配置；仓库 K1 evaluator 走独立代码路径复核。不得让两个名字调用同一函数后声称独立。

Golden cases 至少覆盖：

- le90 周期等价和 0/90°边界；
- class mismatch；
- 重复 prediction 的一对一 greedy matching；
- 同分稳定排序；
- 空 prediction、空 GT、空 class；
- 单 TP、单 FP、单 FN；
- post-NMS identity 保持。

`PASS_EVALUATOR_R009` 当且仅当全部 golden cases 符合手算 expected result，并且两个 evaluator 在每个 Core dose=0 的 AP50/AP75 绝对差均 `<=0.002`；重算 dose=0 与冻结 K1 权威端点绝对差也均 `<=0.002`。任一失败即 `FAIL_EVALUATOR_R009`，停止科学实验；仍生成全部预注册小产物，未运行表填 `NOT_RUN`，v079 只完成 formal claim 隔离。

## 6. Phase 2：同一 raw 的 baseline 重算

对全部有效 Core-6，从同一 full post-NMS raw + full GT 生成：

- AP50、AP75，并在 evaluator 原生支持时报告 AP50:95；
- `ar>=2.1` matched TP 的 canonical le90 angle error、geometry-normalized severe event；
- detection-score risk–coverage、AURC、NRC、Risk@50/70/90；
- image 或可恢复 mother-scene cluster bootstrap 1000 次；SODA-A 的母景角色交叉必须如实标记，不能伪称 confirmatory；
- image count、GT count、prediction count、matched count、retained count 与统计单位。

AP 使用 full evaluator；matched TP 只用于 orientation estimand，不能代替 AP。所有结果必须有稳定 row key `unit|track|dose|iou|ar_bin|metric`。

## 7. Phase 3：三条固定剂量 full-evaluator track

共同规则：只改 final post-NMS prediction 的 theta；score、class、cx、cy、w、h、prediction identity 全冻结；`ar<2.1` prediction 不动；NMS 不重跑；每个 dose 都用 full GT 重新 classwise greedy matching 和 AP。不得声称测量了 NMS 效应。

### Track P：冻结 positive-dose 主协议

按 `a4_protocol_frozen.json`，对每个 `ar>=2.1` prediction 加正 dose。它是与历史 A4 连续的预注册主曲线，不得因结果改方向。

### Track D：GT-directed diagnostic intervention

仅对 dose=0 时 class-correct、IoU50 matched 且 `ar>=2.1` 的 prediction，在 `+dose/-dose` 中选择使其相对 matched GT 的 le90 error 更大的方向，tie 固定为正；其它 prediction 不动。明确标为使用 GT 的诊断上界，不是部署方法或自然扰动。

### Track S：GT-free symmetric falsifier

分别完整运行全体 `ar>=2.1` prediction 的 `+dose` 与 `-dose` 两条曲线，并报告两者及预先定义的算术平均；不得挑较差方向作为结果。

同时计算 frozen-pair surrogate，但它只能与 full evaluator 的差异一起报告，不能写成 AP。

## 8. Phase 4：几何机制与不确定性

- GT aspect-ratio bins 固定为 `[2.1,3)`、`[3,5)`、`[5,∞)`；不事后合并。
- 对 baseline TP 报 IoU50/IoU75 survival 随 dose 的变化、每 bin 样本数和 scene-cluster paired CI。
- 每 unit 单独计算；跨 unit meta-summary 以 unit 为层级，禁止池化实例伪造样本量。
- 对 dose=15° 的 `drop_AP75-drop_AP50` 做 paired cluster bootstrap 95% CI；P、D、S 分开。
- AP75 单调性仅对 Track D 判定：相邻允许数值容差 `0.002`，并报告 Spearman rho。
- knee 固定定义为首个 `AP75 drop>=0.05` 且之后不恢复超过 `0.002` 的 dose；不满足写 `NOT_IDENTIFIED`，禁止插值。

## 9. 预注册 gate 与 kill condition

### 9.1 Provenance

- `PASS_PROVENANCE_R009`：Core-6 全部 full raw/full GT/config/checkpoint/split/hash/命令闭合，dose=0 universe 完整。
- `INCONCLUSIVE_PROVENANCE_R009`：允许的重新 inference 后仍缺任一 Core，或身份不能闭合。extension 不得补位，科学实验早停。

### 9.2 Mechanism

`PASS_STRONG_JSTARS_EVIDENCE_R009` 要求同时满足：

1. provenance 与 evaluator 均 pass，Core-6 三 track×八剂量全部完成；
2. Track D 在 15° 时至少 4/6 units 且三个数据集各至少一个 unit 的 `drop_AP75-drop_AP50>0`，paired 95% CI 下界 `>0`；
3. Track S 的 `(+/-)/2` 在同一 4/6 与三数据集门上方向一致且 CI 下界 `>0`，证明结论不只来自 GT-directed 选方向；
4. Track D 至少 4/6 units 的 AP75 随 dose 近似单调：Spearman `<=-0.9` 且相邻恢复不超过 `0.002`；
5. IoU75 TP survival 满足 `[2.1,3) >= [3,5) >= [5,∞)` 的有序敏感性至少 4/6，并覆盖三个数据集；
6. Track P 完整报告且没有某一数据集全部出现相反方向；不要求其每个 unit 单调。

若主要方向一致但 CI、数量或某个次级条件不足，记 `INCONCLUSIVE_MECHANISM_R009`。若 D/S 任一主证据少于 3/6 支持，或某数据集全部稳定反向，记 `FAIL_UNIFIED_MECHANISM_R009`，从主稿删除统一 AP75 机制和统一 knee claim。

### 9.3 TGRS 条件上限

只有 strong-JSTARS gate pass 后才运行/解释 extension。若三 extension units 全部 provenance/evaluator/八剂量闭合，覆盖总计至少四数据集、三 detector families，且 Track S 与 Core 同方向，记 `PASS_TGRS_BORDERLINE_EVIDENCE_R009`；否则记 `NOT_REACHED_TGRS_BORDERLINE_R009`。即便 pass 也只能称 TGRS-borderline evidence，不得称 TGRS-ready；无独立 confirmatory unit 和第三标注员缺失仍是限制。

### 9.4 全局 kill

事后修改 unit/dose/bin/checkpoint/split/seed/gate，使用 matched-only/partial-GT 冒充 AP，把 GT-directed 写成部署，把 post-NMS 写成 NMS 效应，挑 `+/-` 较差方向，或使用其它项目结果，任一发生即 `FAIL_PROTOCOL_R009`。

## 10. v079 与真实 claim ledger

无论 r009 pass/fail/inconclusive，都从 v078 新建 v079，不覆盖历史文件，并先完成以下强制 quarantine：

- 从摘要、贡献、主结果表、讨论和结论移除 576/20/68/554/142、formal certification/practical certification、严格风险保证和“可部署分数基本不可认证”等尚未通过独立 formal 验收的 headline；
- 表 6 删除或替换为“历史探索性审计，formal implementation 未闭环，不作为本文证据”；
- LTT/HB/CP 只可作为历史探索工具或局限，不能作为本稿贡献或负结果；
- 不把 r006/r007/r008 实现失败写成科学发现。

随后按 r009 gate 写结果：PASS 如实加入；FAIL 删除统一机制；INCONCLUSIVE 只增加边界。禁止补数字救故事。

新 ledger 只收实质 claim，不收标题和参考文献；至少覆盖下列固定 claim families：measurement definition、full-evaluator AP、fixed-dose intervention、empirical-vs-ideal geometry、NRC/AURC、size-conditioned diagnostic、statistical-unit boundary、human annotation boundary、confirmation status、historical certification quarantine。每行必须包含：

`claim_id,manuscript_section,line,text,text_sha256,claim_family,dataset,unit,estimand,result_row_keys,generator_script,input_manifest,gate,status,action,reason`

每个 retained/qualified headline 必须绑定具体 CSV row key、生成脚本、input manifest 与 gate；v079 或 `dis/**` 不能作为数字的唯一证据。`status=VALID|QUALIFIED|INVALID|UNRESOLVED`；`action=RETAIN|QUALIFY|REMOVE`。

## 11. 实现、validator 与资源要求

- runner 与 validator 必须是独立入口；validator 默认 `--check` 绝对只读，不得创建、覆盖或格式化任何文件。需要生成 gate 只能由 runner 显式执行，validator 只比较仓库内容并 stdout 返回状态。
- validator 必须检查协议 JSON、Core/extension 身份、golden expected results、row keys、dose/track/bin 集合、baseline parity、bootstrap seed/reps、gate 逻辑、ledger 证据角色、v078/v079 diff 和授权路径。跨平台文本身份以 Git blob/规范 LF 为准，不以 checkout CRLF bytes 作科学差异。
- runner 先写临时文件再原子替换。CPU 密集 evaluator/bootstrap 使用至少 80% 可用 CPU；记录 worker budget 与实际利用率。inference 记录 4-GPU 资源与 smoke/full 次数。
- operation counts 分开报告 detector training/inference、score-regressor fit/predict、evaluator calls、bootstrap replicates、GPU hours、download；不得用静态源码审计冒充运行时计数。
- large raw 只进入 gitignored runtime raw root；Git 只提交小型代码、表、JSON、memo、v079、server report 与根记录。

## 12. 精确 Git 写入集合

所有状态都生成以下 18 个小型路径；未运行的表保留 schema 并写 `NOT_RUN`，不得缺文件或制造第二报告：

1. `claude_code_and_supervisor.md`（append-only 恰好一条）
2. `dis/server_reports/orientbench-c-r009-20260806.md`
3. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/run_a4_fixed_dose_r009.py`
4. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/validate_a4_fixed_dose_r009.py`
5. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_fixed_dose_protocol_r009.json`
6. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_raw_prediction_inventory_r009.csv`
7. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_evaluator_golden_r009.csv`
8. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_baseline_recompute_r009.csv`
9. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_fixed_dose_positive_r009.csv`
10. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_fixed_dose_gt_directed_r009.csv`
11. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_fixed_dose_symmetric_r009.csv`
12. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_geometry_survival_r009.csv`
13. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_cluster_bootstrap_r009.csv`
14. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_claim_ledger_r009.csv`
15. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_evidence_gate_r009.json`
16. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a4_evidence_manifest_r009.json`
17. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/a4_orientation_intervention_evidence_r009.md`
18. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v079.md`

禁止修改其它路径，尤其 `dis/B.md`、`dis/C.md`、`dis/sug.md`、`dis/review_state.json`、v077/v078、r004–r008 资产和 `.gitignore`。

生成顺序：完成全部非 manifest 输出→根记录 append 一次→显式 stage manifest 以外的 17 个路径→用 `git hash-object --path` 记录规范 Git blob→最后生成并 stage manifest（自身 SHA/blob=`N/A_SELF_REFERENCE`）→运行只读 validator、JSON 解析、`git diff --check`、普通/staged diff。manifest `authorized_changes` 与实际 18 路径必须精确一致。

普通中文 commit；SSH push；禁止 force/merge/rebase/reset/clean。push 失败保留 commit 并如实报告。

## 13. 最终回复

服务器最终回复首行只能是 `执行完毕` 或 `未执行完毕`。

第二行必须且只能给出：`dis/server_reports/orientbench-c-r009-20260806.md`
