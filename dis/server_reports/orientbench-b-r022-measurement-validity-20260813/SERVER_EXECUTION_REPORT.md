---
schema_version: 2
dispatch_id: orientbench-b-r022-measurement-validity-20260813
plan_id: b-r022-measurement-validity-20260813
initiator: B
plan_path: dis/plans/B/b-r022-measurement-validity-20260813/sug.md
plan_commit_sha: db6b061ba266e19334dff301ce3bafa4a2213e74
plan_blob_oid: 9d2c9fb7291cb7b81ef130cb7b6aaf2babeeece8
plan_sha256: 8aef642be5dd4719fc6268f003fac8cff625ddeac6bbfa23fe0badf91d87dcc4
dispatch_commit_sha: 90c0037ae49f7ebe21e53a167a04ee8a6fc68d8f
server_report_path: dis/server_reports/orientbench-b-r022-measurement-validity-20260813/SERVER_EXECUTION_REPORT.md
execution_status: incomplete
completion_mode: FAILURE_EARLY_STOP_CLEAN_ROOM_CONTAMINATION
starting_commit: a34eb59d78e4d14e5bc5b74a99800e333fd24a4c
ending_commit: PENDING_RESULT_COMMIT
---

# 服务器执行报告

## 摘要

本轮未读取 26 项科学输入、未运行 A/B bootstrap、未产生科学数值或候选 gate。执行在 code seal 前停止，原因是服务器执行会话读取了 `claude_code_and_supervisor.md` 中 r020 recovery 的候选态和 witness 信息；r022 Delta-5 禁止该历史 recovery 信息进入 A/B clean-room。继续运行会把时序污染伪装成正式复算，故按 G2 记为 `NOT_ADJUDICATED`。

## Dispatch、哈希、授权与资源

- 服务器身份：`paper.worker-id=server-primary`（SERVER 映射）。
- 初始 HTTPS 同步后执行基线：`db6b061ba266e19334dff301ce3bafa4a2213e74`；STARTED one-file commit：`a34eb59d78e4d14e5bc5b74a99800e333fd24a4c`，已推送。
- plan/active mirror blob：`9d2c9fb7291cb7b81ef130cb7b6aaf2babeeece8`；SHA-256：`8aef642be5dd4719fc6268f003fac8cff625ddeac6bbfa23fe0badf91d87dcc4`；冻结设计 blob：`0f475aab1995a07485d7fd5d66c6abf90a332c59`。
- 治理显式命令均通过：`test_peer_governance.py`（8 tests OK）和 `validate_peer_governance.py . --check-local-worker`（`PEER_GOVERNANCE_OK`）。在线逻辑 CPU=112；48-CPU affinity 与 `/usr/bin/strace` synthetic read capture 已验证。

## 实际执行

| 任务 | 状态 | 实际命令/配置 | 产物/日志 | SHA-256/标识 |
|---|---|---|---|---|
| T1 preflight | complete | HTTPS ff-only、治理校验、CPU/strace 检查 | STARTED 前终端记录 | 见上 |
| T2 STARTED | complete | 单文件 commit + HTTPS push | `STARTED.json` | `a34eb59...` |
| T3 code-seal 前准备 | stopped | 新写 r022 草稿、pinned fd-shifts fetch、synthetic tracer | 未封印草稿（不作为结果） | pinned source hashes matched |
| T4--T8 | not run | 禁止继续 | 无 runtime、无 A/B/comparator/manifest/receipt | 无科学读取 |

## 协议偏差、Gates、失败与负结果

触发：在 pre-seal 阶段错误读取固定记录文件，文件含 r020 recovery 科学候选信息。该文件不是 r022 read-set，且 Delta-5/§7 要求 A/B 不得读取或吸收 recovery 代码/文档/产物；会话污染无法通过之后的重新写代码消除。科学输入零打开不减轻该 clean-room 违反。

因此：`NOT_ADJUDICATED`；无科学四态、无论文 claim、无 B/C verdict。远端 main 在结果提交前复核仍为 execution base `a34eb59...`。

## Provenance 与完成映射

结果提交仅记录本报告、服务器监督记录和未执行原因；r022 code draft 不提交、不作为正式产物。需要 B/监督端签发新的 round id 与全新 code/runtime/report 路径；新的执行会话须在封印前避免读取任何 recovery/receipt 科学内容，之后再从原始 26 输入开始。
