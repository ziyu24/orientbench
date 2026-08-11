# OrientBench 最小跨机器协作协议

## 当前锚点

- state：`READY_FOR_SERVER_FEASIBILITY_RECEIPT`
- round：`orientbench-c-topjournal-feasibility-receipt2-20260810`
- retry of：`orientbench-c-topjournal-feasibility-receipt-20260809`
- dispatch/housekeeping base：`2a70303e9d74313a15b71e1767b0b6ecdc05d2cc`
- planning base：`3a4e86cf435af8b29e63b1668af92a1add7c6dbf`
- receipt control base：`bc27506f7d7c0e47c4d67b202b9157bd4016a87a`
- source execution：`cdf764c5a974030739a9992079bedb8b970fb2a7`
- source completion：`ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`
- source numbers：`DESCRIPTIVE_UNVERIFIED`
- source reported gate：`FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED`
- scientific data cutoff：`a9067fb16d2bbd747dfe69789ac33a5911eb15fe`
- protected B blob：`c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`
- active instruction：`dis/sug.md`
- receipt1 report：`dis/server_reports/orientbench-c-topjournal-feasibility-receipt-20260809.md`，blob `4fe331a6a683313150a4fb21cbabd432ffde0f6b`
- receipt1 contract archive：`dis/sug/orientbench-c-topjournal-feasibility-receipt-20260809-abnormal-preflight.md`，blob `11553a92b05b692a14bf9c4f21898a5c9e10d144`
- receipt2 future report：`dis/server_reports/orientbench-c-topjournal-feasibility-receipt2-20260810.md`
- source runtime：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809`
- source runtime aggregate SHA-256：`2e9f7eb60b7de427b24faa8c91b0ef2017864d99cbc923b04bfe70b500085b43`
- receipt2 code root：`top_journal_v3_reaudit_055/feasibility_receipt2_20260810`
- receipt2 runtime：`outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt2_20260810`
- receipt2 execution：`NOT_STARTED`
- current route：`ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC`
- CC：`COMPLETED / CLOSED`；`cc_recommendation: no`

跨机器共享只通过 Git 仓库，不写账号、机器标识、凭据、本地绝对路径或 C 侧私有规则。receipt2 是相同科学规格的 receipt-only 机械重试，不是新实验或新科学轮次。

## receipt1 终态与 housekeeping 边界

receipt1 永久为 `ABNORMAL_PREFLIGHT_FAILURE`，`scientific_gate: NOT_ADJUDICATED`，Track M/Track D 均 `NOT_RUN`，并标记 `non_reusable: true`。它因 preexisting dirty tree 与 source runtime 可写而在 preflight 停止；这不是科学负结果，也不是 `INSUFFICIENT_ASSETS`。旧 round、code/runtime/report 路径永久消费。

用户在 receipt1 之外授权 housekeeping。提交 `2a70303e9d74313a15b71e1767b0b6ecdc05d2cc` 已发布迁移记录与旧异常报告，并把 source runtime 从可写变为只读；内容树聚合 SHA-256 保持不变。housekeeping 不追溯修改旧 receipt，不补跑科学 phase，不验证旧数字，不改变 gate，也不授予新实验。

receipt2 preflight 必须在 HTTPS pull 后证明 `post_pull_head == upstream == HTTPS remote current branch`、index/worktree clean，且 `2a70303e9d74313a15b71e1767b0b6ecdc05d2cc` 是 `post_pull_head` 祖先。receipt 内禁止 fix、stash、clean、chmod、remote-edit。还必须闭合旧 report/archive blob；核验 source runtime 全树存在、可读、0 symlink、actual user 不可写、全部对象无 write bit、aggregate SHA 精确匹配；不得 write-probe、copy 替代或用 root 身份掩盖。receipt2 code/runtime/report 启动时必须全部不存在；任一创建后本轮路径永久消费。

## 角色、所有权与写入边界

### C

C 维护 `dis/C.md`、`dis/sug.md`、`dis/review_state.json`、本协议与 `dis/B_START_PROMPT.md`，冻结 receipt2 身份、科学规范与证据边界。服务器回报后仍由 C 审计 tracked report 和发布对象；C 不以聊天状态、源数字或 housekeeping 直接裁定科学结论。

### 服务器

服务器只执行 active `dis/sug.md`。receipt2 的唯一写范围是：

1. `top_journal_v3_reaudit_055/feasibility_receipt2_20260810/**`
2. `outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt2_20260810/**`
3. `dis/server_reports/orientbench-c-topjournal-feasibility-receipt2-20260810.md`
4. `claude_code_and_supervisor.md`，仅 append-only

其它全部只读。GPU、download、installation、training、forward、inference、new target outcome、annotation content、target-label tuning 与 manuscript edit 授权全部为 `false`。不得启动新实验、`r020`、rescue 或 gate substitution。

### B / CC

`dis/B.md` 由 B/CC 独占；C 与服务器不得创建、读取内容、修改、格式化、移动、删除、暂存、恢复或提交，只能核验 ordinary/staged diff 为零和固定 Git blob。上轮 CC 已完成并关闭；本轮不是新的 CC 邀请。CC/B 不执行 receipt2、不追加或改写 `dis/B.md`，也不成为最终裁决者。

## 不变的 receipt-only 科学状态

服务器执行健康与科学 outcome 是两条独立轴。active `dis/sug.md` 的 `## 5.` 至 `## 9.` 前与 receipt1 canonical archive 逐字节相同：

1. Track M 仍只允许 `INSUFFICIENT_ASSETS`、`METRIC_REVERSAL`、`BASELINE_DOMINATED`、`SENSITIVITY_UNSTABLE`、`ROBUST_CANDIDATE` 五态；cohort、公式、seed `20260809` 与 bootstrap replicate `0..9999` 不变。
2. Track D 四个 failure predicate、precedence 与 `ELIGIBLE_CANDIDATE` 条件不变。
3. Joint gate 仍只允许 `FAIL_TO_MEASUREMENT_ONLY`、`INCONCLUSIVE_FEASIBILITY`、`PASS_TO_METHOD_DESIGN`，negative 优先。
4. Independent validator 与 `source_hash`、`bootstrap_replicate`、`track_d_evidence_fact`、`joint_gate_clause` 四项真实 mutation 不变。

源执行仍是 `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`，其全部数字仍是 `DESCRIPTIVE_UNVERIFIED`，reported gate 仍是 `FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED`。当前路线保持 `ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC`。

## receipt2 执行完成与异常

`正常执行完毕` 当且仅当 receipt2 全部 phase、independent validator、四项 isolated mutation、恰好一个 commit、HTTPS push 与仓库外 external receipt 全部闭合；科学负结果也可以正常。

任一 preflight 或必做 phase 缺失、source runtime 不符合只读闭合、provenance gap、validator/mutation/Git/发布/external receipt 失败，均为 `异常结束`。详细证据只能进入 receipt2 唯一 report；聊天不得携带路径、SHA 或解释。

## 服务器聊天唯一格式

服务器最终聊天只能在以下两个完整模板中二选一：

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

## 当前唯一动作与禁区

当前唯一动作是 receipt2 receipt-only mechanical retry。禁止新实验、`r020`、DOTA/HRSC/Core rescue、同数据集新 detector 救场、gate substitution、GPU、下载、安装、训练、forward、推理、新 outcome、annotation 内容读取、改稿或重复调用 CC。receipt2 尚未开始；服务器必须先按 active `dis/sug.md` 完成 preflight。
