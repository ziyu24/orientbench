# OrientBench 最小跨机器协作协议

## 1. 共享锚点

每轮必须绑定：round ID、完整 scientific snapshot SHA、active manuscript 和唯一报告路径。跨机器共享内容只通过仓库 `dis/`；不得写入账号、机器标识、凭据、本地绝对路径或私有提示词。

当前轮：

- round: `orientbench-c-r002-20260805`
- scientific snapshot: `8466602330a942c9bb8beff284aa8fc5b952a3b0`
- manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`
- C report: `dis/C.md`
- CC/B only report: `dis/B.md`（r001 已完成；r002 不启动新 CC）
- server only report: `dis/server_reports/orientbench-c-r002-20260805.md`
- previous server report: `dis/server_reports/orientbench-c-r001-20260805.md`

## 2. 角色与文件所有权

- C 先对固定 SHA 独立审查，维护 `dis/C.md`、`dis/review_state.json`、`dis/sug.md`、本协议与 `dis/B_START_PROMPT.md`。
- 是否调用 CC 由用户决定。CC 不是裁决者，也不能替代服务器证据。
- `dis/B.md` 由 CC/B 独占。C 不创建、修改、格式化、移动、删除、暂存、恢复或提交它。
- 服务器只在当轮 `dis/sug.md` 明确授权的路径写入；不得触碰 `dis/B.md`。

## 3. CC 两阶段独立性

阶段一是盲审。CC 及其子代理不得读取当轮 `dis/C.md`、`dis/sug.md`、`dis/sug/**`、会泄漏 C 判断的状态字段，也不得从 Git 历史、diff、缓存或转述恢复这些判断。阶段一只写 `dis/B.md`，只显式暂存该文件并先 push 成功。

阶段二只能在阶段一 push 成功后开始。CC 才可读取 C 的本轮判断，逐条对抗复核，并把内容追加到 `dis/B.md`；阶段一原文必须完整保留。CC 记录独立性是否受损、证据路径、置信度、最弱环节、与 C 的分歧和最小裁决实验。

若阶段一意外接触禁读内容，CC 必须在 `dis/B.md` 标记独立性受损；不得把受污染意见描述为盲审。

## 4. 证据与决策

所有重大判断必须绑定仓库相对路径或核查过的一手链接，并记录：结论、置信度、最弱环节、反证/杀死条件。无新证据时停止争论，转最小实验、证明、反例或一手核查。

C 收到 `dis/B.md` 或服务器报告后，对每项只给出：

- `adopt`：证据充分，纳入状态；
- `revise`：方向成立但口径/强度需改；
- `reject`：与固定证据冲突；
- `experiment`：现有证据不能裁决，执行最小判别实验。

任何角色都不得通过多数票或身份作裁决。改变论文主 claim、协议、数据 split、seed、selection、matching、tile/NMS、指标或 headline 数字的决定，必须先更新 round 与 evidence gate。

## 5. Git 交换

开始时确认远端、分支、upstream、完整 SHA 和干净工作树，只允许 fast-forward 同步。每个角色只显式暂存自己拥有的文件，普通 push，禁止 force、merge、rebase、reset、clean 和无差别暂存。遇到脏树、非 fast-forward、远端不符、所有权冲突或 push 失败时停止并如实报告。
