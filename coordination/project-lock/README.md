# 项目操作锁

`UNLOCKED` 允许项目继续运行；`LOCKED` 停止除帮助、只读状态、校验、锁状态和解锁以外的
全部项目操作。锁由用户自然语言触发，Codex调用受控命令，不要求用户编辑YAML。

当前状态见 `.research_core/PROJECT_LOCK.yaml`；每次变化追加到 `events/LNNNNNN.yaml`。
工厂和项目自身都可以调用同一入口，但工厂写入现有Pi仍必须服从工厂请求、预览与批准门。
项目锁变化、敏感权限变化和SERVER领取检查共享Git-common-dir中的跨平台OS advisory锁；
锁文件长期保留，进程退出由内核释放，严禁按mtime删除仍存活事务的锁。
