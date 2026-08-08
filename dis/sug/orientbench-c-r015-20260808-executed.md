# OrientBench r015：r014 协议闭合、同步场景重算与投稿稿降级修订

- round: `orientbench-c-r015-20260808`
- execution base: `b60dee50cefd8dee055bef166d2165b22c4490a8`
- immutable r014 report: `dis/server_reports/orientbench-c-r014-20260808.md`
- archived r014 instruction: `dis/sug/orientbench-c-r014-20260808-executed.md`
- input manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r014.md`
- output manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
- unique report: `dis/server_reports/orientbench-c-r015-20260808.md`
- read-only input runtime: `outputs/persistent_artifacts/orientbench_r014/`
- new runtime root: gitignored `outputs/persistent_artifacts/orientbench_r015/`
- mode: **CPU-only protocol closure；不重新创造 confirmatory PASS**

本轮不再训练、不做 detector inference、不重建 TTA、不重新拟合 selector，也不换数据集、selector、阈值或 gate。唯一问题是：在 r014 已经看过 Core/HRSC target 结果后，能否把现有数值链按冻结统计单位重新审计，并把不可恢复的预标签封存缺口与稿件事实错误诚实闭合？

r014 的 FAIR 4,362-row修复、六单元点估计和 HRSC 实际运行可作为待复核证据；但服务器提交的 `FULL_COMPLETION/PASS_DEPLOYABLE_EQS_R014` 当前不被 C 接受。r015 不能把同一批已揭盲 D_audit 重新称为独立确认，也不能通过补写当前时间的 hash 伪造过去已封存。

开始前完整读取所有上级/当前 `AGENTS.md`、`pth_data/readme.md`、本文件、r014报告/代码/manifest和当前协作状态。只用 HTTPS；核对 origin、当前/默认/upstream、完整 HEAD、工作树与 index，只允许 `git pull --ff-only`。execution HEAD 必须包含 `b60dee50...` 与当前控制提交。工作树或 index 不干净、不能 fast-forward、授权路径冲突即首行 `未执行完毕` 并停止；不得 stash、reset、clean、checkout、删除未跟踪文件或触碰既有 `stash@{0}`。

## 1. 固定裁决，不得反向漂移

以下 r014 审计事实直接冻结：

1. `prelabel_seal.json` 只登记 `features/*.parquet`、`models/*.joblib`、`scores/*.parquet`；未登记 `protocol_r014.json` 与五个执行脚本。
2. r014 实现脚本首次进入 Git 的提交为 `b60dee50...`，晚于服务器报告记录的 target 执行；前一提交 `e0b91ea...` 只有协议、占位报告和validator等10条路径。
3. 因此“协议及全部代码在首次 target label access 前封存”没有可恢复的密码学证据。文件mtime、口头说明、最终manifest、当前Git blob或事后新增hash均不能补回历史 seal。
4. r014从 `ac7a524...` 到 `b60dee50...` 有两个commit，不符合单一最终commit契约；CPU telemetry全轮均值 `688.997%`、峰值 `4290.200%`，也不符合固定 `3840%` 配额。
5. r014 Core 数值不能据此改判为性能失败；正式状态固定为 `FAIL_PROTOCOL_R014`，数值最多进入 r015 的 exploratory evidence。
6. HRSC 固定为 `INCONCLUSIVE_INDEPENDENT_HRSC_R014`：Delta_NRC=`0.060167...`，95% CI=`[-0.014323,0.143800]`。不得改写成 PASS/FAIL，不得用另一单元替补。

若发现真正的、在 target label access 前由不可改写外部日志锚定且包含协议与全部代码 SHA/bytes 的已有 seal，只能在报告中列为 `PROPOSED_COUNTEREVIDENCE`，不得由服务器自行推翻上述裁决。

## 2. Phase A：只读 provenance 与 seal 法证

新增独立 `audit_r014_protocol_r015.py`，不得 import r014 validator 的 PASS 逻辑。它必须从 Git、r014 runtime与原始输入动态输出：

- `ac7a524... -> e0b91ea... -> b60dee50...` 的父链、每个commit路径集合、时间与 `dis/B.md` blob；
- r014 prelabel seal 的逐项 path/SHA/bytes及缺失的 protocol/code清单；
- final manifest 29个tracked blob与runtime entries的hash核对，区分“最终存在”与“揭盲前已封存”；
- r014代码真实 label I/O 顺序：`source_data()` 调用 `load_labels()` 时先解析完整 matched file再按role过滤；按 outer target 列出哪些目标数据集标签文件在该目标 scores seal 前已被物理读取；
- r014 validator是重算还是消费CSV：逐项记录 provenance/AP/transform/bootstrap/gate/范围检查的真实证据层级；
- r014全30条最终写入集合、两个commit、受保护blob与工作树状态。

`prelabel_seal_audit_r015.json` 的结论必须为 `FAIL_PROTOCOL_R014_UNRECOVERABLE_PRELABEL_SEAL`；不能因最终hash一致写 PASS。

## 3. Phase B：冻结的同步 full-universe cluster bootstrap 重算

新增 `recompute_shared_cluster_bootstrap_r015.py`。只读取 r014 sealed target scores、原 matched labels、冻结 split/image universe与SODA tile→mother map；禁止修改 r014 runtime，禁止重fit或生成新selector scores。

### 3.1 完整 cluster universe

- DIOR-R与FAIR1M：从冻结 full image universe及既有split role构建全部 `D_audit` image IDs，包括0个eligible matched row的图像。
- SODA-A：先取全部 `D_audit` tiles，再用 r014 的22,994/22,994唯一映射构建 mother-scene universe；含0个eligible matched row的母景。
- 同dataset各unit的完整 audit cluster set必须完全相同；输出set size、sorted-set SHA、missing/extra与最多20个witness。不同即 `FAIL_PROVENANCE_R015`，不得计算dataset gate。

### 3.2 同步抽样

三个dataset分别按固定顺序 `DIOR-R, FAIR1M-v1.0, SODA-A`。第 `d` 个dataset使用 `numpy.random.RandomState(20260807+d)`；每个replicate从其 sorted full audit cluster universe抽取与universe同长度的有放回cluster multiset。恰好1,000 replicates。

同一dataset、同一replicate的cluster multiplicity必须同时施加到全部units和所有selectors；禁止像r014那样给unit使用不同seed再按列平均。unit Delta_NRC仍为 `NRC(linear)-NRC(EQS)`；dataset aggregate在每个同步replicate内对units等权平均。SODA只用mother scene为主结果，tile只允许附带sensitivity且不进gate。

点估计、percentile 95% CI、centered one-sided p与Holm-6/Holm-3公式保持r012/r014不变；0.02最小效应不变。输出全部9,000行replicates及unit/dataset结果。validator必须从原始scores/labels/universe以独立实现重算并逐值比对，不能只数CSV行。

### 3.3 r015 数值状态

即使重算仍满足原门，也只能标：

- `EXPLORATORY_CORE_SUPPORT_R015`：unit support至少4/6、覆盖三数据集/至少两families、FAIR support、dataset 3/3；
- `EXPLORATORY_CORE_INCONCLUSIVE_R015`：完整重算但未满足上述支持，且无明确负门；
- `EXPLORATORY_CORE_NEGATIVE_R015`：少于2/6或任一dataset aggregate CI upper<=0。

禁止输出 `PASS_DEPLOYABLE_EQS_R015`，因为同一 target D_audit 已揭盲，r015不能恢复 confirmatory independence。

## 4. Phase C：集合泄漏与实现偏差审计

对每个outer target从原row keys重建并报告 `source_Dcal_fit, source_Dcal_calib, source_Daudit, target_Dcal, target_Daudit, target_feature_prelabel, target_scores_prelabel` 的row/image/mother set size与SHA。明确区分预期身份重合（target prediction features与其后attached target rows）和禁止重合：

- fit/calib不得包含source D_audit；
- outer fit/calib不得包含target dataset任一label row；
- target feature/score schema不得含GT、angle_error、risk、GT_AR或split role；
- seal后feature/model/score bytes/SHA必须与r014 manifest一致；
- 物理文件读取发生在何时与真正参与fit是两个字段，不得用“过滤后没用”掩盖提前读取。

同时动态检查 r014 feature实现与冻结r012特征契约，包括 doubled-angle axial circular dispersion、`u_axis`、association margin单/零候选、sentinel、tie-break、w/h swap与0/90边界。缺项记 `IMPLEMENTATION_DEVIATION`，不允许事后增加特征并重新评分。

## 5. Phase D：r015 投稿稿

创建新稿，不覆盖r014。必须：

1. 将Core EQS表和同步重算结果明确称为 `exploratory post-audit evidence`，不得写confirmatory、formally validated、deployable proved或跨host普遍迁移。
2. HRSC保留正点估计与跨零CI，称外部检查不确定；不得称独立确认通过。
3. 保留FAIR 18,505/4,362、DOTA 0.7544/0.7113、旧leave-dataset 0/6、identifiable leave-detector 4/5、fixed-dose descriptive-only和target-GT geometry upper bound。
4. 修正DIOR来源：基础DIOR使用 Ke Li, Gang Wan, Gong Cheng, Liqiu Meng, Junwei Han, *Object Detection in Optical Remote Sensing Images: A Survey and A New Benchmark*, ISPRS JPRS 159 (2020) 296–307, DOI `10.1016/j.isprsjprs.2019.11.023`；DIOR-R使用AOPG一手论文 `arXiv:2110.01931`或其准确期刊记录。2016 RICNN不得承担DIOR/DIOR-R出处。
5. PSC作者保持 Yi Yu、Feipeng Da；删除或标unknown/excluded所有只有期刊首页、会议首页、arXiv根页的“verified source”。
6. 披露同步full-universe scene/image bootstrap，且不得继续消费r014错误dataset aggregate CI。
7. 正文不得出现内部round ID、`PASS_*`/`FAIL_*`、validator/authorized path或venue-ready措辞；协议失败只在可复现限制中用学术语言说明“实现未在目标审计前获得完整代码级时间锁，因此结果按探索性证据解释”，不写内部治理流水账。

claim ledger必须绑定r015精确原句SHA、同步重算row keys、生成脚本与gate action。novelty matrix中不准确的一手身份不得以“verified”呈现。

## 6. Phase E：真正独立的 validator

`validate_r015.py` 必须只读、与生成脚本独立实现，并实际完成：

1. Git父链、两个r014 commits、30条r014集合与 `dis/B.md` blob；
2. r014 prelabel seal缺失protocol/code，且不得被final manifest替代；
3. r014 runtime/manifest输入hash；
4. full D_audit cluster universe和同dataset set equality；
5. 用固定seed重新产生1,000个同步multiplicity vectors；
6. 从scores/labels重算全部unit/dataset Delta、CI、p、Holm与状态，逐值比对r015 CSV；
7. SODA mother-scene主抽样、零eligible cluster仍在universe；
8. feature schema、set intersections、seal前后hash与实现偏差；
9. r015稿的exploratory边界、DIOR/DIOR-R/PSC引用、失效UCB与ledger hash；
10. manifest、唯一报告、真实Git diff、单commit要求、授权集合及受保护blob。

不得import生成脚本中的gate函数，不得信任CSV/JSON的PASS字符串，不得只查文件存在。验证日志和每项bool/witness写入 `validator_r015.json`；成功token只能是 `VALID_PROTOCOL_CLOSURE_R015`，它只证明审计闭合，不证明deployable selector PASS。

## 7. 资源与早停

- GPU使用=0，detector inference=0，training=0，selector refit=0，new target score=0。
- CPU密集阶段aggregate quota固定 `3840%`（48核的80%），总worker/BLAS线程计入；无法设置则 `未执行完毕/INCOMPLETE_BLOCKED_R015`，不得用38 workers字符串代替真实利用率。
- 每30秒按phase记录CPU/RAM/worker；只统计CPU密集phase，不能用全轮I/O/GPU均值稀释。
- 任一r014 runtime hash不符、完整cluster universe不可重建、同dataset universe不一致、需要改split/gate/selector/score、或需要重新读取checkpoint/GPU forward，立即早停并报告 `未执行完毕`。
- 发现新缺陷可以追加witness，但不得扩大为新方法、新数据集或新确认门。

## 8. 合法终态与完成语义

本轮唯一审计成功状态是 `PASS_PROTOCOL_CLOSURE_R015`，要求协议法证、同步重算、集合审计、稿件、validator、manifest、单commit和push全部完成。它必须同时保存：

- `r014_formal_verdict=FAIL_PROTOCOL_R014`；
- `r015_numeric_status=EXPLORATORY_CORE_SUPPORT_R015 | EXPLORATORY_CORE_INCONCLUSIVE_R015 | EXPLORATORY_CORE_NEGATIVE_R015`；
- `hrsc_status=INCONCLUSIVE_INDEPENDENT_HRSC_R014`。

若任一必需阶段未完成，使用 `FAIL_AUDIT_IMPLEMENTATION_R015 | FAIL_PROVENANCE_R015 | PROTOCOL_DRIFT_R015 | INCOMPLETE_BLOCKED_R015`，首行 `未执行完毕`。

进程结束不等于完成。最终对话首行只能是 `执行完毕` 或 `未执行完毕`；第二行必须且只能是 `dis/server_reports/orientbench-c-r015-20260808.md`。

唯一报告顶部必须给出：

```text
execution_completion: FULL_COMPLETION | INCOMPLETE_EARLY_STOP | INCOMPLETE_BLOCKED | PROTOCOL_DRIFT
audit_verdict: PASS_PROTOCOL_CLOSURE_R015 | FAIL_AUDIT_IMPLEMENTATION_R015 | FAIL_PROVENANCE_R015 | PROTOCOL_DRIFT_R015
r014_formal_verdict: FAIL_PROTOCOL_R014
r015_numeric_status: EXPLORATORY_CORE_SUPPORT_R015 | EXPLORATORY_CORE_INCONCLUSIVE_R015 | EXPLORATORY_CORE_NEGATIVE_R015 | NOT_EVALUATED
hrsc_status: INCONCLUSIVE_INDEPENDENT_HRSC_R014
last_completed_phase: ...
early_stop_trigger: NONE | ...
unrun_required_phases: [] | [...]
push_status: PUSHED | FAILED
```

## 9. 精确写入集合（19）

只允许创建/修改：

1. `claude_code_and_supervisor.md`（恰好append一个r015 section）
2. `dis/server_reports/orientbench-c-r015-20260808.md`
3. `p3_selector/deployable_proxy_r015/protocol_r015.json`
4. `p3_selector/deployable_proxy_r015/scripts/audit_r014_protocol_r015.py`
5. `p3_selector/deployable_proxy_r015/scripts/recompute_shared_cluster_bootstrap_r015.py`
6. `p3_selector/deployable_proxy_r015/scripts/validate_r015.py`
7. `p3_selector/deployable_proxy_r015/reports/prelabel_seal_audit_r015.json`
8. `p3_selector/deployable_proxy_r015/reports/leakage_and_access_audit_r015.csv`
9. `p3_selector/deployable_proxy_r015/reports/unit_results_r015.csv`
10. `p3_selector/deployable_proxy_r015/reports/dataset_results_r015.csv`
11. `p3_selector/deployable_proxy_r015/reports/bootstrap_replicates_r015.csv`
12. `p3_selector/deployable_proxy_r015/reports/gate_r015.json`
13. `p3_selector/deployable_proxy_r015/reports/validator_r015.json`
14. `p3_selector/deployable_proxy_r015/reports/resource_telemetry_r015.csv`
15. `p3_selector/deployable_proxy_r015/reports/evidence_manifest_r015.json`
16. `p3_selector/deployable_proxy_r015/docs/protocol_closure_r015.md`
17. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r015.md`
18. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r015.csv`
19. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/novelty_matrix_r015.csv`

新中间日志/缓存只能进入 `outputs/persistent_artifacts/orientbench_r015/`。禁止修改r014及更早的代码、报告、稿件、runtime、dataset、split、threshold、config、checkpoint、`.gitignore`和任何其它路径，尤其不得触碰 `dis/B.md`。

只做一个最终中文commit，不得中间commit/push。只显式暂存上述19条；LF；`git diff --check`零输出。manifest最后生成，登记Git blobs与全部r014只读输入/r015 runtime输出SHA/bytes/schema，self=`N/A_SELF_REFERENCE`。使用HTTPS普通push当前分支，不改origin、不force；push失败保留本地commit并首行报告 `未执行完毕`。
