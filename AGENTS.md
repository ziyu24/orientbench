# orientbench 项目特有规则

instruction layout：`HOST_GLOBAL_PLUS_PROJECT_OVERRIDE / v1`。本文件只补充各主机
`~/.codex/AGENTS.md` 的公共角色规则，不复制 B、C 或 SERVER 职责。

任何项目动作前读取 `project.yaml`、`.research_core/PROJECT_LOCK.yaml`、
`coordination/STATE.yaml`、`coordination/NOW.md`、`coordination/DISPATCH.yaml`、
活动 `rNNN` 计划和最近 Git 提交。第一条报告包含当前状态、阻塞项和唯一下一步。
`LOCKED` 时只允许帮助、只读状态、校验、锁状态和用户明确解锁。

- 项目：`orientbench`；创建模式：`NEW_RESEARCH`。
- 权威仓库：`https://github.com/ziyu24/orientbench.git`。
- 科学范围以 `research/BRIEF.md`、模式入口和已激活计划为准。
- 运行时硬约束以 `.research_core/contract.yaml` 和程序校验结果为准。

## 项目特有覆盖

- 当前无额外覆盖。
