# OrientBench 最小跨机器协作协议

## 当前锚点

- state：READY_FOR_SERVER_EXECUTION
- round：orientbench-c-r020-measurement-validity-20260811
- planning base：594654a95d50b1f14b87252698911cc3fc583b03
- protected B blob：c0c2571f3a5c828673b39e6458ceaed5f14c5a6a
- route：ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC
- learned EQS：APPENDIX_FAILED_ONLY
- active instruction：dis/sug.md
- design：dis/jprs_measurement_validity_gate_design_20260811.md
- plan：dis/jprs_measurement_validity_dispatch_plan_20260811.md
- r020 code：top_journal_v3_reaudit_055/measurement_validity_r020_20260811
- r020 runtime：outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811
- r020 post-seal receipt：outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811_postseal_receipt/postseal_receipt.json
- r020 future report：dis/server_reports/orientbench-c-r020-measurement-validity-20260811.md
- r020 execution：NOT_STARTED
- CC：COMPLETED_CLOSED；cc_recommendation: no

跨机器共享只通过 Git，不写账号、机器标识、凭据、本地绝对路径或任一角色的私有规则。

## receipt 历史闭环

receipt1 为 ABNORMAL_PREFLIGHT_FAILURE / NOT_ADJUDICATED / non_reusable。receipt2 为 ABNORMAL_MANDATORY_REFERENCE_PROVENANCE_FAILURE / NOT_ADJUDICATED / non_reusable。

receipt3 的执行提交为 594654a95d50b1f14b87252698911cc3fc583b03，唯一报告为 dis/server_reports/orientbench-c-topjournal-feasibility-receipt3-20260811.md，blob 498dd8094f713a4a76339890ffd3a9ec45352344。Git 发布机械闭合，但事后审计确认 validator 只在真实 access log、manifest、report 形成前验证 planned tokens，scientific inputs 也没有完整进入 frozen manifest。正式状态固定为：

- ABNORMAL_EXECUTABLE_AUDIT_FAILURE
- PROTOCOL_DRIFT
- NOT_ADJUDICATED
- track_m formal = NOT_EMITTED
- reported METRIC_REVERSAL = DESCRIPTIVE_UNVERIFIED
- reported FAIL_TO_MEASUREMENT_ONLY = DESCRIPTIVE_UNVERIFIED
- non_reusable = true
- scientific_failure = false

receipt3 的 round/code/runtime/report 路径永久消费，不得重跑、续跑或作为 r020 科学输入。旧 active 合同归档为 dis/sug/orientbench-c-topjournal-feasibility-receipt3-20260811-abnormal-audit.md，filter-aware blob aeb79060e50aeaa615b365065fc087dc7b9e74cc。

## 角色与写入边界

C 维护 active 合同与共享状态。服务器只执行 dis/sug.md，并只可写：

1. top_journal_v3_reaudit_055/measurement_validity_r020_20260811/**
2. outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811/**
3. dis/server_reports/orientbench-c-r020-measurement-validity-20260811.md
4. claude_code_and_supervisor.md，仅 append-only

dis/B.md 由 B/CC 独占；C 与服务器不得读取内容、创建、修改、格式化、移动、删除、暂存、恢复或提交，只可核验 blob/diff 元数据。上轮 CC 已 COMPLETED_CLOSED，本轮不是新邀请。

本轮只授权 existing Core measurement reanalysis、新 protocol 与该 CPU-only r020。GPU、一般下载、安装、训练、forward、inference、新 target outcome、annotation root、主稿与 method experiment 均未授权。唯一网络例外是 dis/sug.md 固定 fd-shifts commit 的一次 HTTPS fetch。

## r020 科学合同

正式总体只含 r014/m069 冻结 Core A-F。双 clean-room 实现顺序为 B_BEFORE_A；Comparator 在 A/B 封存后运行。三端点为 AUGRC、Risk@70、Risk@90；五个单因素 geometry/AR ablations；unit/dataset Holm families 固定 270/135。full signature 必须包含 effect_class、ablation_id、contrast、endpoint、supported_direction。

strict join 以 matched 的显式 D_audit base cohort 为左表；features/scores 只对 cohort semi-select 后 one-to-one left join。cohort missing/duplicate/drop 必须为 0；合法 RHS extras 只记录 count/sorted SHA，不进入 endpoint；detection_score 只在 features 与 scores 的 cohort rows 精确核对。

SCENE_MACRO 纯描述，只报 scene-macro point、nonempty rate 与 scene-cluster CI；禁止 instance-IID bootstrap、material flag、category-change claim 或独立驱动 gate。learned EQS、S0、r011、receipt3 均不得进入 formal family。

四态固定为 PASS_TO_EXTERNAL_CONFIRMATION、FAIL_GENERIC_OR_NULL、INCONCLUSIVE_MIXED、NOT_ADJUDICATED。PASS 只授权未来独立确认，不等于 JPRS/TGRS ready；FAIL 收口 JSTARS；INCONCLUSIVE 不换 gate 续命。

## Git 与执行闭包

服务器开始时仅 HTTPS pull --ff-only，冻结 post-pull HEAD 为 execution_base。final commit 前 HTTPS remote main 必须仍等于 execution_base。最终必须恰一个 direct-child non-merge commit，只含获准 tracked paths；禁止 merge/rebase/reset/clean/amend/second commit/force。

科学输入打开前封印 A/B/Comparator/closure/mutation code。应用层 hash-chain tracer 与 strace OS-open trace同时运行，scientific relevant set 做双向 coverage并与 manifest 等值。六个真实 mutation 按 raw/logic 前四项、manifest 第五项、report exact buffer 第六项的固定顺序执行。SCIENTIFIC_RUNTIME_FREEZE 与 TRACKED_CONTENT_SEAL 后不得逆向写入；tracked report 的科学态保持 provisional。push 后唯一获准的 seal 外 receipt root 先封存 `POSTFREEZE_COMMAND_LOG_SEAL`，再由无子进程的固定 writer 原子写 JSON 与 SHA sidecar；VALID_POSTSEAL_RECEIPT 只闭合服务器阶段并允许正常聊天，不是跨电脑正式科学态。正式态必须由 C 拉取 published commit 后独立复核并另写 `dis/` 状态提交。

## 完成、异常与聊天

FULL_COMPLETION_POSITIVE、FULL_COMPLETION_INCONCLUSIVE、FULL_COMPLETION_NEGATIVE 都是正常完整执行；科学负结果不是异常。source/hash/schema/join/代码/trace/parity/bootstrap/mutation/manifest/scope/Git/push/external receipt 失败为 FAILURE_EARLY_STOP / NOT_ADJUDICATED。

服务器最终聊天严格二选一：

👇👇👇👇👇👇

正常执行完毕

👆👆👆👆👆👆

或：

👇👇👇👇👇👇

异常结束

👆👆👆👆👆👆

聊天不附报告路径、SHA、解释或列表。跨电脑证据只写唯一 tracked report 与 supervisor log；server-local sealed command log/receipt/sidecar 只作运行见证，不能被 C 直接当作共享正式状态。

## 当前唯一动作

服务器 HTTPS fast-forward 到发布 r020 的提交并执行 dis/sug.md。不得选择其它计划、复用 receipt3、调用 CC 或在本轮之后自动发起新实验。服务器回复后 next owner 固定为 `C_POSTPULL_ADJUDICATION`：C 拉取结果提交、独立复核后才发布跨电脑正式状态。
