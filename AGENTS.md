# orientbench 项目特有规则

instruction layout：`HOST_GLOBAL_PLUS_PROJECT_OVERRIDE / v2`。本文件只补充各主机
`~/.codex/AGENTS.md` 的公共角色规则，不复制 B、C 或 SERVER 职责。

任何项目动作前读取 `project.yaml`、`.research_core/PROJECT_LOCK.yaml`、
`coordination/STATE.yaml`、`coordination/NOW.md`、活动 `rNNN` 科学计划和最近 Git
提交。第一条报告包含当前状态、阻塞项和唯一下一步。`STATE`、`DISPATCH`、旧journal
和分支显示冲突时，以有效科学计划、主机`cqc-fabric run status`和远端结果ref为准，
不得让旧状态文件阻止SERVER执行。
`LOCKED` 时只允许帮助、只读状态、校验、锁状态和用户明确解锁。

- 项目：`orientbench`；创建模式：`NEW_RESEARCH`。
- 权威仓库：`https://github.com/ziyu24/orientbench.git`。
- 科学范围以 `research/BRIEF.md`、模式入口和已激活计划为准。
- 科学边界以有效计划为准；SERVER工程执行统一使用主机全局
  `/home/rspip/.local/bin/cqc-fabric run`。
- 项目内旧`dispatch`、execution guard、claim、多层journal和`main`吸收状态只作历史
  兼容，不构成训练启动或机器完成门。

## 项目特有覆盖

- 当前无额外覆盖。
