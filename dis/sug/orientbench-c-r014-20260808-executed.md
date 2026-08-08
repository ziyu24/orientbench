# OrientBench r014：FAIR 全总体修复、EQS 完整执行与 HRSC 独立确认

- round: `orientbench-c-r014-20260808`
- control parent: `61eb65ea4c56e15829031f79e57773b1a370269f`
- frozen scientific design: `dis/sug/orientbench-c-r012-20260807-post-cc-v2.md`
- r012 immutable server evidence: `d76e3837c43987bfdcf134ceecc5f7ff3ab9f292`
- input manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r012.md`
- output manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r014.md`
- unique report: `dis/server_reports/orientbench-c-r014-20260808.md`
- runtime root: gitignored `outputs/persistent_artifacts/orientbench_r014/`

用户已明确报告 HRSC 资产现在可用，并授权在新一轮修复 FAIR 来源后执行原冻结 EQS 与条件式 HRSC 确认。r012 历史结论不得改写：它是来源门触发的预注册早停，不是 EQS 性能失败；本轮是新的证据轮次，不是把 r012 改判为 PASS，也不允许换 selector、换 gate 或用 HRSC 替代 Core。

开始前完整读取所有上级/当前 `AGENTS.md` 与 `pth_data/readme.md`。使用 HTTPS；核对 origin、当前/默认/upstream、完整 HEAD、工作树与 index，只允许 `git pull --ff-only`，禁止 merge/rebase/reset/clean/force。若树不干净、远端不符或不能 fast-forward，按第 1 节报告 `未执行完毕` 后停止。

## 1. “执行完毕”与“早停”的强制语义

进程退出、产生 commit 或触发预注册门，均不自动等于“把 `sug.md` 搞完了”。最终对话第一行只能二选一：

- `执行完毕`：所有无条件任务和实际分支要求的任务均已完成；实现不是 guard/placeholder；Core 已得到可判定科学结论；若 Core PASS，HRSC 已实际完成；若 Core 非 PASS，HRSC 按预注册条件明确记为 `NOT_RUN_CORE_NOT_PASS`；稿件、manifest、validator、报告、范围检查、commit 与 push 均完成。
- `未执行完毕`：在可判定 Core 科学结果前因 provenance、实现、环境、资源、异常、协议漂移或其它原因停下；或者 Core PASS 后未完成 HRSC；或者稿件/validator/commit/push 任一必需步骤未完成。合法早停也必须用这一行，不能把“按规则停了”写成“执行完毕”。

最终对话第二行必须且只能是：`dis/server_reports/orientbench-c-r014-20260808.md`。

唯一报告开头必须逐项给出：

```text
execution_completion: FULL_COMPLETION | INCOMPLETE_EARLY_STOP | INCOMPLETE_BLOCKED | PROTOCOL_DRIFT
scientific_verdict: PASS_DEPLOYABLE_EQS_R014 | INCONCLUSIVE_DEPLOYABLE_EQS_R014 | FAIL_DEPLOYABLE_EQS_R014 | FAIL_PROVENANCE_R014 | FAIL_TRANSFORM_R014 | FAIL_IMPLEMENTATION_R014 | FAIL_PROTOCOL_R014 | NOT_EVALUATED
last_completed_phase: ...
early_stop_trigger: NONE | <精确门、命令、退出码与 witness>
unrun_required_phases: [] | [...]
core_status: PASS | INCONCLUSIVE | FAIL | NOT_EVALUATED
hrsc_status: PASS | FAIL | INCONCLUSIVE | NOT_RUN_CORE_NOT_PASS | NOT_RUN_PROVENANCE | NOT_EVALUATED
push_status: PUSHED | FAILED
```

分类规则不可混淆：

- `FAIL_PROVENANCE` 是数据/模型/split/config/raw lineage 未闭合，不是 selector 性能失败；EQS 必须写 `NOT_EVALUATED`。
- `FAIL_IMPLEMENTATION` 是代码缺失、placeholder、运行异常或复算不一致，不是性能失败。
- `FAIL_PROTOCOL` 是越权、泄漏、改 gate/split/阈值/selector、seal 后改版等。
- `FAIL_DEPLOYABLE_EQS` 只允许在完整有效 estimand 与预注册统计检验已实际完成后使用。
- `INCONCLUSIVE_DEPLOYABLE_EQS` 只允许在完整有效执行后使用，不得用来包装前置失败。

r012 的既有事实应在报告历史栏明确写成：`execution_completion=INCOMPLETE_EARLY_STOP`、`scientific_verdict=FAIL_PROVENANCE_R012`、`r012_eqs=NOT_EVALUATED`、`r012_hrsc=NOT_EVALUATED`。当时没有 HRSC 不是 FAIR A0 失败原因；现在有 HRSC 也不能修复 FAIR 或越过 Core。

## 2. 冻结问题、协议与禁止漂移

科学问题仍是：selector 不使用 target D_cal/D_audit angle labels 时，按 OBB 几何容忍度归一化的真实 TTA 等变性信号，能否跨数据集改善方向风险排序？

Core-6 固定为 `DIOR-R/22, DIOR-R/3, DIOR-R/61, FAIR1M-v1.0/24, SODA-A/23, SODA-A/4`。主 estimand、source 排除整个 target dataset、D_cal-fit/D_cal-calib/D_audit 角色、dataset/unit 权重、views=`identity,hflip,vflip`、association、特征、label attach、seal、五个 selector、EQS 超参、1000 次 cluster bootstrap、Holm-6/Holm-3、`ar>=2.1`、risk floor=1/cap=3、unit 最小效应 0.02 和所有 tie-break 均严格沿用冻结 r012 §2–§9。

禁止修改 dataset、split、threshold、NMS、class map、checkpoint、Core unit、selector、超参、minimum effect、bootstrap 数、显著性阈值或 PASS 条件；禁止训练 detector、下载替代资产、使用 target label 选特征/模型/版本；禁止从旧 P3、r011 fixed-dose 或 HRSC 结果反向改 Core。必要科学变更只能写 `PROPOSED_DEVIATION` 并以 `未执行完毕/PROTOCOL_DRIFT` 停止，等待授权。

## 3. Phase A：先修 FAIR 完整总体，不允许再次用硬编码结论结束

FAIR 冻结 val20 必须为 `4,362 images / 78,644 GT`，每个 view registry 恰有 4,362 image rows，包含 `n_pred=0`。现存 r011 raw 为 3,896 rows/484,332 predictions；m069 只证实 4,362-image/488,194-prediction manifest，不能把缺失 raw 当作存在。

先对 `pth_data/readme.md`、全部历史 manifest、raw 路径、bytes/SHA、schema 与逐图计数做穷尽审计并保存搜索命令、命中/未命中清单和 witness，不能使用 `m069_raw_available=false` 常量代替搜索。若找到与 4,362 split 完整绑定且可逐图重算的既有 raw，做 official evaluator AP50/AP75 parity 后使用。

若完整 raw 不存在，则用冻结 FAIR/24 config、checkpoint、split、threshold/NMS/class map 重新做 identity/h/v 三视图 full forward，生成持久化 runtime raw。允许 4×A30 推理，不训练 detector、不改变任何科学设置。必须完成：

1. full split/GT/r011 raw/m069 manifest/new raw 的 sorted image-ID set size、SHA-256、missing/extra 与最多 20 个 witness；
2. 4,362-row 逐图 prediction count join及 identity 总预测数；
3. new identity 与权威 baseline 的 official AP50/AP75，绝对差均 `<=0.002`；
4. h/v 50-image transform smoke：inverse 后 IoU `>=1-1e-7`、le90 `<=1e-7 degree`；
5. exact config/checkpoint/framework/command/log/raw 的 SHA-256、bytes、schema与 `can_recompute=true`。

本轮目标是修复可修来源，而不是重复证明旧缺失。只有 dataset/config/checkpoint/split 或 official evaluator 确实不可用，且穷尽审计与实际命令已证明无法恢复时，才可 `未执行完毕 + FAIL_PROVENANCE_R014/INCOMPLETE_BLOCKED`。这不是 EQS 性能失败，也不是完整执行。

同时复核 SODA `22,994` tiles 到 mother scene 唯一映射，要求 `unmapped=ambiguous=duplicate=0`；六个 Core unit 的 full universe、split、D_cal/D_audit、config/checkpoint/framework、raw和official AP parity必须全部闭合。任一前置失败都按第 1 节报告，禁止伪称 6/6。

## 4. Phase B：实现与完整执行，不接受 guard/placeholder

可以复用 r012 已验证的来源审计代码，但不得把 r012 三个“通过 A0 即抛出 `implementation is unavailable`”的 guard 当作实现。新 `r014` namespace 必须真正实现并由 validator 动态导入/运行：

1. inverse transform 与 deterministic prediction-only association；
2. 冻结无 GT feature generator；
3. source-only nested CV 与 early-stop 统计；
4. seal 后独立 target label attach；
5. 五 selector fit/score；
6. image/mother cluster bootstrap、Holm-6/Holm-3与 unit/dataset gate；
7. HRSC 条件确认；
8. manifest、稿件数字与 Git 范围复算。

source-only 两折若都满足 `CI upper<0`，记录 `INCOMPLETE_EARLY_STOP + FAIL_DEPLOYABLE_EQS_R014`，target labels 不得 attach；`unrun_required_phases` 必须列出 target/HRSC/manuscript最终化等实际未运行项，首行仍是 `未执行完毕`。混合结果不得调模型。

若 source early stop 未触发，必须继续完成一次性 target D_audit。SODA 主统计以 mother scene bootstrap，tile 仅 sensitivity。必须恰有 1000 个有效 paired replicates，replicate 内跨 selector 同步抽样，禁止 pooled detector 排序。

## 5. Core 双层终判

unit support 当且仅当 `Delta_NRC=NRC(size-linear)-NRC(EQS)` point `>=0.02`、95% CI lower `>0`、centered one-sided Holm-6 p `<0.05`。

dataset aggregate 必须在每个 replicate 内先重算各 unit Delta，再在 dataset 内 units 等权平均；三个 dataset 分别要求 point `>=0.02`、CI lower `>0`、Holm-3 `<0.05`。

- `PASS_DEPLOYABLE_EQS_R014`：6/6 provenance/transform/leakage/implementation 通过；unit support `>=4/6`，覆盖三数据集和至少两 detector families；FAIR/24 support；dataset aggregate `3/3` support；SODA mother-scene；selector 对 target angle labels 零访问。
- `INCONCLUSIVE_DEPLOYABLE_EQS_R014`：完整有效执行且至少 2 个 unit support，但未满足任一 PASS 条件。
- `FAIL_DEPLOYABLE_EQS_R014`：完整有效 target 执行后少于 2/6，或任一 dataset aggregate `CI upper<0`；source-only合法早停另按第 4 节标记未完整执行。

不得另造 PASS。旧 P3 leave-dataset `0/6` 必须保留为负证据；r011 fixed-dose只可描述性使用。

## 6. Phase F：HRSC2016/LSKNet 资产现在可用，但只作独立确认

在 Phase A 只核对 HRSC 资产身份，不读取结果做 Core 决策。必须从 `pth_data/readme.md` 绑定唯一既有 HRSC2016/LSKNet config、checkpoint、frozen split、class map、threshold/NMS、framework与哈希；用户口头“有了”只把状态从 unavailable 改成 `USER_REPORTED_AVAILABLE_TO_VERIFY`，不能代替服务器实证。

仅当 Core=`PASS_DEPLOYABLE_EQS_R014` 时实际运行 HRSC。禁止按结果换 detector/dataset/split；不得用 DOTA 或其它单元替补。必要时 4×A30 做 identity/h/v fixed forward；用全部 Core 数据集 D_cal-fit 训练冻结 EQS/linear，各 dataset 总权 `1/3`，HRSC feature/scores seal 后一次 attach GT。matching、`ar>=2.1`、风险与 1000 次 image-cluster bootstrap沿用 Core。

- `PASS_INDEPENDENT_HRSC_R014`：Delta_NRC point `>=0.02`、CI lower `>0`、EQS不弱于 standalone equivariance，且 provenance/leakage/implementation 全过。
- `FAIL_INDEPENDENT_HRSC_R014`：CI upper `<=0`，或收益依赖 target label/同数据集 source；杀死 general-transfer/顶会 claim。
- 其它完整有效混合结果为 `INCONCLUSIVE_INDEPENDENT_HRSC_R014`。

若 Core 非 PASS，HRSC 不运行，`hrsc_status=NOT_RUN_CORE_NOT_PASS`；这是预注册分支完成，不是“HRSC 缺失”，可在所有其它分支任务完成时归入 `FULL_COMPLETION`。若 Core PASS 而 HRSC 身份/运行未闭合，必须 `未执行完毕 + INCOMPLETE_BLOCKED`。HRSC 永不回流 Core gate。

## 7. 资源与恢复

GPU 推理默认 4×A30，一卡一 shard；小进程也先用 4 卡。只有连续两次有命令、时间、显存证据的真实 OOM 才能减卡。SODA 重单元分卡，完成一个 unit 三视图并验真后立即并行 CPU feature build。

CPU 密集阶段把 aggregate quota 固定为 `3840%`（48核的80%）；这是同时满足上级“不得超过80%”与项目“必须使用>=80%”的唯一交集。总 worker/BLAS线程都计入，不得持续低于或高于该配额；设置 `OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=1`。若运行环境不能设置该精确配额，先记录能力探测并按 `未执行完毕/INCOMPLETE_BLOCKED` 汇报，不得自行选择39 workers越过80%。每 30 秒记录 phase、wall、CPU、RAM、每卡 utilization/memory、worker 与异常，汇总 mean/p10/p90、峰值和日志哈希。

长任务必须可按 manifest/shard 原子恢复。恢复前核对 code/config/checkpoint/input SHA；不相同则不得混用旧 shard。每次异常必须保存命令、退出码、stderr与已完成 shard；不允许吞错后写 PASS。

## 8. 投稿稿、事实门与 validator

无论 Core 科学结果如何，只要执行分支走到可判定结论，就完成 r014 稿与 claim ledger/novelty matrix。PASS 才写 measure→diagnose→select；非 PASS 只写 measurement→diagnose，EQS如实作为负/不确定结果。

必须同时修复 r012 已知基础问题：删除失效 instance/tile/mother UCB 表与认证消费；在 NRC/size-bin 明示 `D_audit` 并区分 full-validation；PSC 作者为 Yi Yu、Feipeng Da；DIOR 与 AOPG/DIOR-R 使用准确一手来源；保留 FAIR `18,505/4,362`、DOTA `0.7544/0.7113`、leave-dataset `0/6` 与 identifiable leave-detector `4/5`。不得伪造首创、TGRS/CVPR-ready或用 HRSC 包装 Core。

只读 validator 必须从 raw/代码/Git 动态复算：FAIR/SODA universe、official AP、transform/association tests、feature schema无GT、层级权重、seal顺序、source early stop、1000 replicates、Holm/minimum effect、unit/dataset/HRSC gate、稿件数字、ledger text hash、manifest、completion分类、授权集合与 `dis/B.md` blob。信任 CSV 中的 PASS、硬编码布尔、只查文件存在或 guard 返回零退出码均无效。

## 9. 精确写入集合（30）

runtime raw、shard、日志与 checkpoint 只进入 gitignored `outputs/persistent_artifacts/orientbench_r014/`。Git 只允许创建/修改以下路径：

1. `claude_code_and_supervisor.md`（恰好 append 一个 r014 section）
2. `dis/server_reports/orientbench-c-r014-20260808.md`
3. `p3_selector/deployable_proxy_r014/protocol_r014.json`
4. `p3_selector/deployable_proxy_r014/runtime_registry_r014.json`
5. `p3_selector/deployable_proxy_r014/scripts/inventory_and_repair_provenance_r014.py`
6. `p3_selector/deployable_proxy_r014/scripts/run_tta_forward_r014.py`
7. `p3_selector/deployable_proxy_r014/scripts/build_equivariance_features_r014.py`
8. `p3_selector/deployable_proxy_r014/scripts/evaluate_eqs_r014.py`
9. `p3_selector/deployable_proxy_r014/scripts/evaluate_hrsc_r014.py`
10. `p3_selector/deployable_proxy_r014/scripts/validate_r014.py`
11. `p3_selector/deployable_proxy_r014/reports/completion_status_r014.json`
12. `p3_selector/deployable_proxy_r014/reports/provenance_r014.csv`
13. `p3_selector/deployable_proxy_r014/reports/fair_universe_join_r014.csv`
14. `p3_selector/deployable_proxy_r014/reports/tta_inventory_r014.csv`
15. `p3_selector/deployable_proxy_r014/reports/transform_sanity_r014.csv`
16. `p3_selector/deployable_proxy_r014/reports/feature_summary_r014.csv`
17. `p3_selector/deployable_proxy_r014/reports/source_cv_r014.csv`
18. `p3_selector/deployable_proxy_r014/reports/unit_results_r014.csv`
19. `p3_selector/deployable_proxy_r014/reports/dataset_results_r014.csv`
20. `p3_selector/deployable_proxy_r014/reports/bootstrap_replicates_r014.csv`
21. `p3_selector/deployable_proxy_r014/reports/hrsc_results_r014.csv`
22. `p3_selector/deployable_proxy_r014/reports/gate_r014.json`
23. `p3_selector/deployable_proxy_r014/reports/resource_telemetry_r014.csv`
24. `p3_selector/deployable_proxy_r014/reports/evidence_manifest_r014.json`
25. `p3_selector/deployable_proxy_r014/docs/deployable_proxy_r014.md`
26. `p3_selector/deployable_proxy_r014/docs/deployable_proxy_r014.svg`
27. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r014.md`
28. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/equivariance_selector_r014.svg`
29. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r014.csv`
30. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/novelty_matrix_r014.csv`

不得修改 `dis/B.md`、r009/r010/r011/r012/r013历史资产、`.gitignore`、dataset/split/threshold/config/checkpoint或任何其它路径。受保护 `dis/B.md` blob 必须保持 `3181a862137918f1dd41677893937c12b3c39c28`。

只做一个最终中文 commit，只显式暂存上述 30 条，LF，`git diff --check` 零输出。manifest 最后生成并登记 input/output/runtime SHA/bytes/schema、命令、真实训练/inference/evaluator/bootstrap counts；self-reference=`N/A_SELF_REFERENCE`。使用 HTTPS 普通 push 当前分支，不修改 origin、不 force；push 失败必须保留本地 commit，第一行仍为 `未执行完毕`，报告 `push_status=FAILED`。
