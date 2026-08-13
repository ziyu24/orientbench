---
schema_version: 2
plan_id: REPLACE
dispatch_id: REPLACE_UNIQUE_REVISION
initiator: B_OR_C
base_sha: FULL_COMMIT_SHA
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: pending
  reference: null
scientific_snapshot:
  primary: FULL_COMMIT_SHA
review_mode: open
server_report_path: dis/server_reports/DISPATCH_ID/SERVER_EXECUTION_REPORT.md
read_set:
  - REPLACE_REPO_RELATIVE_PATH
write_set:
  - REPLACE_REPO_RELATIVE_PATH
resource_scope:
  declared: false
  compute: {gpu_count_max: null, gpu_hours_max: null, cpu_core_hours_max: null}
  wall_time: {seconds_max: null}
  data: {allowed_dataset_ids: [], read_bytes_max: null, write_bytes_max: null}
  write: {allowed_paths: [], bytes_max: null}
  network: {allowed: false, allowed_endpoints: []}
conflict_keys:
  - REPLACE_RESOURCE_OR_PATH_KEY
gates:
  - gate_id: G1
    rule: REPLACE_PASS_FAIL_INCONCLUSIVE_RULE
early_stop_conditions:
  - REPLACE_CONDITION
kill_conditions:
  - REPLACE_CONDITION
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# 不可变候选计划

## 科学问题、证据与 unknown

只写一个可证伪问题；绑定 claim、生成端实现、数字来源与最近一手工作。

## 固定协议与实现自由度

冻结数据/split、信息边界、baseline、seed、matching/tile/NMS/selection、指标、预算和禁止漂移项。服务器可自行决定不改变科学含义的实现细节，并在报告中披露。

## 任务、Gate 与反证

| 任务 | 必需产物 | Gate | Early stop | Kill condition |
|---|---|---|---|---|
| REPLACE | REPLACE | REPLACE | REPLACE | REPLACE |

## 激活与回执

- READY 后本文件字节永久冻结；实质变化创建新 revision/id。
- active `dis/sug.md` 必须与 committed plan 逐字节相同并由 coordination 绑定 hash。
- L0/L1 不得超过项目五类资源政策；未配置层级按 L2。L2 必须有用户授权 reference。
- 最终对话严格两行：第一行“执行完毕”或“未执行完毕”；第二行唯一报告路径。
