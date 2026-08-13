---
schema_version: 2
dispatch_id: orientbench-b-r021-measurement-validity-20260812
plan_id: b-r021-measurement-validity-20260812
initiator: B
plan_path: dis/plans/B/b-r021-measurement-validity-20260812/sug.md
plan_commit_sha: 60f2eb197dae4d15292f793df86a4dddc989cad9
plan_blob_oid: 9446b5e7f3d3d93003d4e14cf1eb6dc8062b82c8
plan_sha256: e322b15af9765bf10613aedfe413e35f2ac70a58fd427362a71fe76ce63d5d45
dispatch_commit_sha: 90c0037ae49f7ebe21e53a167a04ee8a6fc68d8f
server_report_path: dis/server_reports/orientbench-b-r021-measurement-validity-20260812/SERVER_EXECUTION_REPORT.md
execution_status: incomplete
completion_mode: FAILURE_EARLY_STOP_GOVERNANCE_INTEGRITY
starting_commit: f2fb8553e0565064a1fc7a7c8ec798f291629ee2
ending_commit: PENDING_RESULT_COMMIT
---

# 服务器执行报告

## 摘要

执行在科学输入打开前停止。未产生任何 A/B、bootstrap、metric、witness 或 scientific gate；因此没有科学数字可报告，状态为 `NOT_ADJUDICATED`。

## Dispatch、哈希、授权与资源

- 用户交付的 dispatch、plan path 与 dispatch commit 均匹配。
- `dis/sug.md` 与 B plan blob 都是 `9446b5e7f3d3d93003d4e14cf1eb6dc8062b82c8`，SHA-256 都是 `e322b15af9765bf10613aedfe413e35f2ac70a58fd427362a71fe76ce63d5d45`。
- frozen design blob 为 `0f475aab1995a07485d7fd5d66c6abf90a332c59`。
- local worker 依用户明确指令绑定为 `server-primary`；preflight 发现 `nproc=112`，可成功固定 affinity `0-47`，`strace 5.16` 可用。
- 唯一 STARTED commit 为 `f2fb8553e0565064a1fc7a7c8ec798f291629ee2`，只含 `STARTED.json`，并已 HTTPS push。

## 失败原因

活动派发的治理校验 `dis/governance/validate_peer_governance.py` 失败：它要求 legacy r020 archive 的 SHA-256 为 `74ef9c65eb660aa36fa6c7f5d78043a4f68540bff3d9903a9303ad6603c9abf5`，而当前派发提交中该文件 `dis/sug/orientbench-c-r020-measurement-validity-20260811-server-returned.md` 的实际 SHA-256 为 `aa3d369863843c2548131a6b9f0fd8ff6de4b6e21a73488102a8feb6140a4141`。同一提交的 `dis/governance/MIGRATION.md` 也声明前一个 SHA，故控制面自相矛盾。

该错误发生在 read_set 的治理预检阶段，不是 A-F 科学输入、冻结 split、环境、CPU、soft link、Conda 或网络数据的问题。计划的 G2 要求任一审计/Git 完整性失败为 `NOT_ADJUDICATED`；在这种控制面下继续会违反 r021 的“从零、正确时序、正式可裁决”目标。

## 实际执行

| 任务 | 状态 | 实际命令/配置 | 产物/日志 | SHA-256/标识 |
|---|---|---|---|---|
| T1 dispatch/worker preflight | failed | HTTPS pull、active plan/blob/hash 校验、server-primary binding、governance validator | 本报告 | archive SHA conflict |
| T2 STARTED | complete | one-file commit + HTTPS push | `STARTED.json` | `f2fb8553e0565064a1fc7a7c8ec798f291629ee2` |
| T3--T8 | skipped | no scientific process launched | none | no scientific input opened |

## 协议偏差、Gates、失败与负结果

用户要求不要让旧 archive inconsistency 阻塞；服务器曾短暂把该项视为非科学偏差，但在复核 r021 的 G2、迁移记录和 validator 后，确认它是控制面完整性失败，故未继续进入 code seal 或数据读取。该更正不涉及任何科学计算，也没有改变计划、设计、阈值、split 或 B/C 文件。

## Provenance 与完成映射

工作区在 STARTED 前后均无未提交内容。没有读取 26 个科学输入、r020/recovery 资产、learned EQS 或其它禁读材料；没有创建 r021 code/runtime/postseal roots；没有启动 GPU、安装、训练、forward、inference 或一般下载。

需要 B 发布新的、哈希自洽的 dispatch revision（新 dispatch ID、plan path 和 report root），或明确把 archive validator 的预期值与实际 committed archive 对齐。当前 r021 路径已含 STARTED，不应重用为正式重执行路径。
