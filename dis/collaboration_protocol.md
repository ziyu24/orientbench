# OrientBench 最小跨机器协作协议

## 当前锚点

- round: `orientbench-c-r011-20260807`
- scientific snapshot: `c62ea3514e98f76baf557c22a5dd0ef812d84ee0`
- manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v080.md`
- C: `dis/C.md`
- B only: `dis/B.md`
- server only: `dis/server_reports/orientbench-c-r011-20260807.md`
- previous server report: `dis/server_reports/orientbench-c-r010-20260806.md`

跨机器共享只通过仓库 `dis/`，不写账号、机器标识、凭据、本地绝对路径或私有 prompt。

## 角色与所有权

C 先审固定 SHA；是否调用 CC 由用户决定，CC 不是裁决者。`dis/B.md` 由 CC/B 独占，C 与服务器均不得创建、修改、格式化、移动、删除、暂存、恢复或提交。服务器只写当轮 `dis/sug.md` 精确授权路径。

CC 阶段一 push 前不得读本轮 `dis/C.md`、`dis/sug.md`、`dis/sug/**`、泄漏 C 判断的状态字段或由历史/diff/转述恢复判断；阶段一只写/push B。阶段二才可读 C 并逐条 `adopt|revise|reject|experiment`，保留阶段一原文，披露独立性损伤。

## 证据与 gate

重大判断绑定生成端/一手证据，记录置信度、最弱环节和 kill condition。可复现 raw/代码/预注册反例高于角色意见。实现检查必须进入最终布尔 gate；常量PASS、自比自身、错误estimand、只查存在、报告披露但不阻断均无效。

r009=`FAIL_PROTOCOL_R009`，r010=`FAIL_PROTOCOL_R010`；其 full-sample AP 点曲线仅为待独立复核的描述性证据。旧 `measure_fix_v2` deployable/STABLE-PASS 不自动继承到当前 Core-6 lineage。C 收到证据只作 `adopt|revise|reject|experiment`。

## Git

开始核对远端、分支/upstream、完整 SHA 与干净树，只允许 fast-forward。各角色仅显式暂存自有文件；HTTPS普通push；禁止 force、merge、rebase、reset、clean、无差别暂存。冲突或失败即停止并如实报告。
