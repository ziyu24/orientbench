# 2026-09-19 存储清理恢复入口

本文件对应 `configs/cleanup-20260919.recovery.json` 的十四个已登记历史产物根。它们均为已结束轮次的缓存、预测、检查点、日志或旧报告副本；科学结论已在 `lab/result.md` 与 `lab/failed_methods.md` 入账并推送。清理不删除 `src/`、`configs/`、`doc/`、`lab/`、Git、主机数据集或共享权重。

恢复时先克隆本项目并检出清理清单所记录的 source commit，再使用对应的 `src/orientbench/rNNN/`、`configs/rNNN/` 与主机的 dataset/pth_data 输入。从 `runs/rNNN/RUN.json` 读取历史命令仅用于审计；若未来需要真正重建，必须按当时有效的科学协议另行授权，且不承诺检查点逐位一致。`outputs/`、`top_journal_v3/`、`top_journal_v3_reaudit_055/`、`archives/`、`measure_fix_v2/` 是遗留的项目内副本，不是数据集或通用权重库，不作为后续任务输入。
