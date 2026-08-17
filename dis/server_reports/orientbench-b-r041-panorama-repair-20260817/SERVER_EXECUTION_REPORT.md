---
schema_version: 2
dispatch_id: orientbench-b-r041-panorama-repair-20260817
plan_id: b-r041-panorama-repair-20260817
initiator: B
plan_path: dis/plans/B/b-r041-panorama-repair-20260817/sug.md
plan_commit_sha: eff4d731020112335efbb021c8d18bac1116257d
plan_blob_oid: 51aceb1e142ef60fbf552b1321dbd8bf08f5fad2
plan_sha256: 9afc676f6f962fdb0ea47b0507ee6d3f0261710d7f0dd70b6a47ab7e9f46fc85
dispatch_commit_sha: 20a8fb26937439cb0ae10d9be95c5a2c218f3023
server_report_path: dis/server_reports/orientbench-b-r041-panorama-repair-20260817/SERVER_EXECUTION_REPORT.md
execution_status: incomplete
completion_mode: failure_early_stop
scientific_outcome: NOT_ADJUDICATED
starting_commit: 20a8fb26937439cb0ae10d9be95c5a2c218f3023
ending_commit: 9a7bfea
---

# r041 服务器执行报告

## 摘要

**异常结束。** r041 在任何模型推理、AP parity、三视图、训练、下载或数据写入之前触发硬禁条件，已停止。无科学裁决。

## 核验、授权与资源

- worker：`server-primary`；用户交付的 dispatch、路径与提交均已核验。
- 活动计划与 `dis/sug.md` 的 SHA-256 均为 `9afc676f6f962fdb0ea47b0507ee6d3f0261710d7f0dd70b6a47ab7e9f46fc85`。
- 已确认 L2 用户授权、2 GPU / 120 GPU-hour / 48-hour 边界及 r041 write set。
- 已读取只读权威基线清单：`/home/rspip/cqc/pro/study/pth_data/readme.md`；没有修改其任何文件。

## 停止点与异常原因

| 项目 | 实际状态 |
|---|---|
| 停止单元 | 首个 DOTA-v1.0 PSC AP parity 前的布局核验；尚未启动 unit |
| 异常原因 | 为确认迁移后 annfiles 位置执行了过宽的目录递归检查，检查命令访问到 `dota/dota2.0/split_ss_dota20/` 的目录元数据 |
| 硬禁条件 | 触发：计划禁止读取或推理 DOTA-v2.0 的任何 split |
| 已完成单元 | 无 |
| 推理 / AP parity / 三视图 | 均为 0 |
| 训练、微调、下载、pth_data 写入 | 均未发生 |

虽未打开 DOTA-v2.0 图像或标注、未运行模型且未生成预测，目录元数据访问仍按计划的严格措辞视为禁触并停止，不能包装为正常结束。

## AP 对齐表

| 单元 | 目标 readme mAP | 实测 mAP | 状态 | 原因 |
|---|---:|---:|---|---|
| 无 | — | — | NOT_STARTED | 硬禁条件在首个 parity 前触发 |

## 禁触端点与产物

| 端点 / 限制 | 状态 |
|---|---|
| DOTA-v2.0 | **触碰目录元数据；已触发停止；无图像/标注读取、无推理** |
| SODA-A official test | 未触碰 |
| 任意 official test 标注 | 未触碰 |
| r040 HRSC 七单元产物 | 未重跑、未改动 |

唯一 r041 产物为启动记录：`dis/server_reports/orientbench-b-r041-panorama-repair-20260817/STARTED.json`。无有效分析资产、无 AP 表数据、无需产生 audit bundle。

## 监督 041-S 结论

本轮为**异常结束**，不是正常结束；已完成单元清单为空，AP 对齐表如上，禁止端点状态已完整披露。后续若要重新执行，需新 dispatch；新轮应避免广域递归，直接在指定 DOTA-v1.0 路径核验 `annfiles/` 与 `images/`。
