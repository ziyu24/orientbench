# OrientBench 最小跨机器协作协议

## 1. 当前共享锚点

- round: `orientbench-c-r010-20260806`
- scientific snapshot: `73f8814b9d0345bfb6b99c1463a61bb01a555f40`
- manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v079.md`
- C report: `dis/C.md`
- CC/B only report: `dis/B.md`
- server only report: `dis/server_reports/orientbench-c-r010-20260806.md`
- previous server report: `dis/server_reports/orientbench-c-r009-20260806.md`

跨机器共享只通过仓库 `dis/`；禁止账号、机器标识、凭据、本地绝对路径或私有 prompt。

## 2. 角色与所有权

C 先对固定 SHA 独立审查，维护 `dis/C.md`、`dis/review_state.json`、`dis/sug.md`、本协议与 `dis/B_START_PROMPT.md`。是否调用 CC 由用户决定；CC 不是裁决者，也不能替代服务器证据。`dis/B.md` 由 CC/B 独占，C 与服务器均不得创建、修改、格式化、移动、删除、暂存、恢复或提交它。服务器只写当轮 `dis/sug.md` 精确授权的路径。

## 3. CC 两阶段独立性

阶段一盲审 push 成功前，CC 及其子代理不得读取当轮 `dis/C.md`、`dis/sug.md`、`dis/sug/**`、泄漏 C 判断的状态字段，或从 Git 历史/diff/缓存/转述恢复这些判断。阶段一只写和 push `dis/B.md`。阶段二才可读 C 判断并逐条 `adopt|revise|reject|experiment`；必须完整保留阶段一原文。若盲审受污染，必须明示。

## 4. 证据与裁决

重大判断绑定仓库相对路径或核查过的一手链接，并记录置信度、最弱环节、反证和 kill condition。没有新证据就停止争论，转最小实验、证明、反例或一手核查。不能以多数票或角色身份裁决。

实现检查必须真正进入最终布尔 gate。静态 PASS、常量状态、同一路径伪装成双 evaluator、自比自身、错误 bootstrap estimand、只在报告披露但不阻断的 mismatch 均不能支持通过。validity 非 pass 时，依赖它的发展 gate 必须 inconclusive；描述性结果与正式 gate 分层保存。

r009 已冻结为 `FAIL_PROTOCOL_R009 / INCONCLUSIVE_MECHANISM_R009`；允许保留其 AP 点估计作待复核描述性证据，禁止把 `PASS_R009_EVIDENCE_CLOSED` 当当前状态。C 收到 B 或服务器报告后只给 `adopt|revise|reject|experiment`。

## 5. Git 交换

开始时核对 origin、分支/upstream、完整 SHA 与干净工作树，只允许 fast-forward 同步。各角色只显式暂存自己拥有的文件，普通 push；禁止 force、merge、rebase、reset、clean 和无差别暂存。脏树、非 fast-forward、远端不符、所有权冲突或 push 失败时停止并如实报告。
