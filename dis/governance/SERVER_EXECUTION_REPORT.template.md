---
schema_version: 2
dispatch_id: REPLACE
plan_id: REPLACE
initiator: B_OR_C
plan_path: dis/plans/ACTOR/PLAN_ID/sug.md
plan_commit_sha: FULL_COMMIT_SHA
plan_blob_oid: FULL_GIT_BLOB_OID
plan_sha256: SHA256
dispatch_commit_sha: FULL_COMMIT_SHA
server_report_path: dis/server_reports/DISPATCH_ID/SERVER_EXECUTION_REPORT.md
execution_status: REPLACE_complete_or_incomplete
completion_mode: REPLACE_completion_mode
starting_commit: FULL_COMMIT_SHA
ending_commit: FULL_COMMIT_SHA
---

# 服务器执行报告

## 摘要

记录尝试、完成范围和 completion mode。服务器不裁决竞争路线或论文 claim。

## Dispatch、哈希、授权与资源

核验 plan/active committed blob、SHA-256、commit、L2 授权、五类资源、冲突键与唯一报告路径。

## 实际执行

| 任务 | 状态 | 实际命令/配置 | 产物/日志 | SHA-256/标识 |
|---|---|---|---|---|
| REPLACE | complete/failed/skipped | REPLACE | REPLACE | REPLACE |

## 协议偏差、Gates、失败与负结果

逐项记录预注册规则、观测证据、pass/fail/inconclusive、偏差、early-stop/kill 与计划外发现。

## Provenance 与完成映射

记录起止工作树、变更路径、B/C 独占路径核验、环境、数据/split、seed、checkpoint 和 hash。最终回执严格两行，第二行只能是本报告路径。
