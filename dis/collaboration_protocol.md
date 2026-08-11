# OrientBench 最小跨机器协作协议

## 当前锚点

- state：`READY_FOR_SERVER_FEASIBILITY_RECEIPT`
- round：`orientbench-c-topjournal-feasibility-receipt3-20260811`
- retry of：`orientbench-c-topjournal-feasibility-receipt2-20260810`
- dispatch base：`35358b5fef838b178aff0e16470ebe0117cab687`
- receipt2 report publication commit：`a2da27559dc6eb005f02efb9b3b34584ebed57b8`
- source execution：`cdf764c5a974030739a9992079bedb8b970fb2a7` / `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`
- source numbers/gate：`DESCRIPTIVE_UNVERIFIED` / `FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED`
- scientific cutoff：`a9067fb16d2bbd747dfe69789ac33a5911eb15fe`
- protected B blob：`c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`
- receipt1：`ABNORMAL_PREFLIGHT_FAILURE / NOT_ADJUDICATED / non_reusable`
- receipt2：`ABNORMAL_MANDATORY_REFERENCE_PROVENANCE_FAILURE / NOT_ADJUDICATED / non_reusable`
- receipt2 report：`dis/server_reports/orientbench-c-topjournal-feasibility-receipt2-20260810.md`，blob `8e1407d90f5a7247816c457eddcb60a704291951`
- receipt2 archive：`dis/sug/orientbench-c-topjournal-feasibility-receipt2-20260810-abnormal-reference.md`，blob `25ee36ec83db92364134a66bb44b349ac5f34cf9`
- active instruction：`dis/sug.md`
- receipt3 code：`top_journal_v3_reaudit_055/feasibility_receipt3_20260811`
- receipt3 runtime：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt3_20260811`
- receipt3 reference：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt3_20260811/references/fd-shifts`
- receipt3 future report：`dis/server_reports/orientbench-c-topjournal-feasibility-receipt3-20260811.md`
- receipt3 execution：`NOT_STARTED`；`receipt_only: true`
- current route：`ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC`
- CC：`COMPLETED / CLOSED`；`cc_recommendation: no`

跨机器共享只通过 Git，不写账号、机器标识、凭据、本地绝对路径或 C 侧私有规则。

## 历史 receipt 闭环

receipt1 因 dirty tree 与 writable source runtime 在 preflight 停止，科学 gate 未裁定。receipt2 完成强制 preflight，但本地允许根内不存在 pinned fd-shifts Git identity；当轮无下载权限，因此 mandatory reference provenance 失败。两轮都不是科学失败；receipt1 的 Track M/Track D/joint gate 均未运行，receipt2 的 Track M=`NOT_EMITTED_NOT_RUN` 且 Track D/joint gate 未运行；两轮 round/code/runtime/report 路径均永久消费。

`a2da27559dc6eb005f02efb9b3b34584ebed57b8` 只发布 receipt2 异常报告，不是 receipt2 正常 execution commit。receipt3 不追溯修改任何旧 receipt。

## receipt3 唯一新增权限

`pinned_reference_fetch_authorized: true` 只允许最多三次通过 HTTPS Git 获取 `https://github.com/IML-DKFZ/fd-shifts.git` 的 commit `c4467aec134e99691359da209f811d91283fc1e3` 到新 runtime reference 容器。attempt-01/02/03 使用互不复用的新子目录；失败现场原样保留。每个 Git 命令使用 reference root 内空 hooksPath、禁 submodule，并设置 `GIT_LFS_SKIP_SMUDGE=1`；不使用镜像、替代 commit、setup、hooks、LFS、pip/conda 或安装。一般 download 仍为 false。

身份核验阶段不执行 checkout 代码、setup 或 hook。remote/commit/detached HEAD/clean/tree/blob/bytes 全部闭合后，只允许在禁网隔离进程执行两份固定 blob 的目标 reference functions 或合规 AST adapter。三次网络命令均失败或任一 identity/dynamic behavior 不闭合，必须异常结束且科学 gate 为 `NOT_ADJUDICATED`。

## 角色与写入边界

C 维护 active 合同和状态；服务器只执行 `dis/sug.md`。receipt3 唯一写范围：

1. `top_journal_v3_reaudit_055/feasibility_receipt3_20260811/**`
2. `outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt3_20260811/**`
3. `dis/server_reports/orientbench-c-topjournal-feasibility-receipt3-20260811.md`
4. `claude_code_and_supervisor.md`，仅 append-only

除窄 pinned fetch 外，GPU、一般 download、installation、training、forward、inference、new outcome、annotation content、target-label tuning、manuscript edit、method/new experiment/new protocol 均未授权。

`dis/B.md` 由 B/CC 独占；C 与服务器不得读取内容、创建、修改、格式化、移动、删除、暂存、恢复或提交，只可核验 blob/diff 元数据。上轮 CC 已关闭，本轮不是 CC 邀请。

## 不变科学合同

receipt3 的 §5.1/§5.2/§5.4-§8 与 receipt2 canonical archive 逐字节相同；只有 §5.3 的 pinned reference 获取/provenance 规则变化。Track M 五态、Track D 谓词、joint gate、cohort、公式、bootstrap seed `20260809`、replicate `0..9999`、CI report-only、validator 与四 mutation 均不变。

## 完成、异常与聊天

`正常执行完毕` 仅当全部 receipt phase、validator、四 mutation、恰一个 commit、HTTPS push 与 external receipt 闭合；科学负结果也可以正常。reference 获取/identity/dynamic validation 或任一必做 phase 失败均为 `异常结束`。

服务器聊天严格二选一：

```text
👇👇👇👇👇👇

正常执行完毕

👆👆👆👆👆👆
```

或：

```text
👇👇👇👇👇👇

异常结束

👆👆👆👆👆👆
```

## 当前唯一动作

当前唯一动作是服务器执行 receipt3。禁止新实验、`r020`、rescue、gate substitution、一般下载、安装、训练、forward、推理、新 outcome、annotation 内容读取、改稿或调用 CC。
