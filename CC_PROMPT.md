# OrientBench 兼容启动入口

本文件只保留旧 Claude Code 启动路径兼容性，不包含固定 B 身份或本轮科学任务。

1. 先读取根 `CLAUDE.md` 与 `AGENTS.md`。
2. 用 `git config --local --get paper.worker-id` 恢复当前 clone 的长期角色。
3. 再读取 `dis/PEER_START.md`、公开角色合同、协作协议和 coordination。

缺失或无效的 `paper.worker-id` 必须 fail closed。B/C 由独立 clone 分别绑定，双方权力对等；客户端和账号不产生身份。
