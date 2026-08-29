# 运行时角色兼容合同

任务指令角色来自各主机生成的 `~/.codex/AGENTS.md`；项目根 `AGENTS.md` 只保存
项目特有覆盖。B/C/SERVER公共规则不得复制回本目录。

科研角色身份仍由 worktree-local `paper.worker-id` 和公开登记解析：
`peer-b-primary`、`peer-c-primary`、`server-primary`。B/C只负责科学判断，SERVER
在冻结科学边界内负责工程执行。SERVER统一使用主机全局
`/home/rspip/.local/bin/cqc-fabric run`，其直接
执行、两卡控制变量、数据精确子集租约、STOP、验收和结果ref规则优先于项目内旧
dispatch、guard、claim和journal；旧运行时不得再作为启动门，本文不复制公共规则。
`.research_core/contract.yaml`继续保存历史科学与数据语义兼容信息，但不得覆盖主机
执行优先规则或重新引入已经退出热路径的启动门。
