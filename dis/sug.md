---
schema_version: 2
plan_id: b-r029-bundle-closure-20260813
dispatch_id: orientbench-b-r029-bundle-closure-20260813
initiator: B
base_sha: 4ae6e18a166abab1a93f17b3a8179e85a66b872c
supersedes: null
resolves_contest_step: "dis/contests/C/orientbench-r026-r027-formal-confirmation-contest-20260813.json 的最后一个跨机缺口（C r028 复核的最低决议）"
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-13：转达并批准 C 的建议——『B 下发一次纯 bundle 修复，让服务器原字节补交这两个文件并重建 manifest/report；禁止改 gate、改数值或新增实验』"
scientific_snapshot:
  primary: 4ae6e18a166abab1a93f17b3a8179e85a66b872c
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r029-bundle-closure-20260813/SERVER_EXECUTION_REPORT.md
read_set:
  - audit_bundles/r028/**、r028 runtime 原件与本计划；不需要读取任何科学输入
write_set:
  - audit_bundles/r028/dota/bootstrap.npy
  - audit_bundles/r028/dota/dota_gt_fresh.pkl
  - audit_bundles/r028/bundle_manifest.csv
  - dis/server_reports/orientbench-b-r029-bundle-closure-20260813/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 0, gpu_hours_max: 0, cpu_core_hours_max: 2}
  wall_time: {seconds_max: 7200}
  data:
    allowed_dataset_ids: ["repository-tracked-evidence"]
    read_bytes_max: 10737418240
    write_bytes_max: 1073741824
  write:
    allowed_paths:
      - audit_bundles/r028/
      - dis/server_reports/orientbench-b-r029-bundle-closure-20260813/
      - claude_code_and_supervisor.md
    bytes_max: 1073741824
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
conflict_keys:
  - server-execution-slot
  - dis/sug.md
  - audit_bundles/r028
gates:
  - gate_id: G1
    rule: 本轮零科学计算、零数值变化。唯一目标是让 Git 跟踪的 bundle 与 manifest 声明完全一致。
  - gate_id: G2
    rule: 仅硬性 kill 清单失败才停；其它偏差记录后继续。
early_stop_conditions:
  - 仅硬性 kill 清单；wall time 超 7200 秒。
kill_conditions:
  - 任一补交文件与 manifest 声明不符（bootstrap.npy 必须恰为 1,280,128 bytes、SHA-256 6b2e0178ff2ec8507289aa9ede02fef65a7f69d36d3de33b78c6f224e48e8d30；dota_gt_fresh.pkl 必须恰为 2,680,160 bytes、SHA-256 3baa2ca8d2d80c7994db371ff8828a77e90c53521e4c2c187e6f61ee46e0beff）——不符时禁止替换、再生成或重算，如实报告并停。
  - 重算、修改或删除任何科学数值、gate、冻结表或 bundle 其余 18 个对象。
  - 修改 .gitignore 或任何治理/论文文件；写入越出 write_set。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r029 纯 bundle 闭合修复（B 发起，执行 C 的最低决议；零科学变更）

## 一句话

r028 的跨机证据包差两个文件没进 Git（被 `.gitignore` 的 `*.npy`/`*.pkl` 拦下）。本轮服务器把这两个文件按 manifest 声明的**原字节** force-add 进 Git、重建 manifest、写不夸大的报告——仅此而已。

## 步骤

1. STARTED 单文件 commit + push。
2. 定位 r028 runtime 中的原件，逐一核验 bytes 与 SHA-256 恰等于 manifest 声明（见 kill 清单中的精确值）；核验不过 → 停止如实报告。
3. `git add -f audit_bundles/r028/dota/bootstrap.npy audit_bundles/r028/dota/dota_gt_fresh.pkl`（不改 `.gitignore`）。
4. 重建 `audit_bundles/r028/bundle_manifest.csv`：20 个对象全部按 Git canonical blob 实测 bytes/SHA-256，无自引用行按既有约定处理并注明。
5. 报告（模板 schema 2）：只陈述补交了哪两个文件、实测 hash、manifest 差异 diff；不得声称超出本轮范围的任何完成度。
6. 恰一个结果 commit（只含 write_set 路径）+ push；两行回执。

## 交接

推送后 C 立即执行最终重放（r026 raw validator、六项 mutation、GT integrity）。B/C verdict 一致后，contest 按 C 预告收敛为 `AUDITED_EXTERNAL_REPLICATION_ACCEPTED`。

## 激活与回执

- READY 首次提交后字节冻结；根 `dis/sug.md` 逐字节镜像并由 coordination 绑定。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
- 最终对话严格两行：第一行 `执行完毕` 或 `未执行完毕`；第二行唯一报告路径。
