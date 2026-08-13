---
schema_version: 2
plan_id: b-r023-measurement-validity-20260813
dispatch_id: orientbench-b-r023-measurement-validity-20260813
initiator: B
base_sha: d7bee4db922db2c8ec4500ea54a894fea05d05c4
supersedes: b-r022-measurement-validity-20260813
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-12 指示派发服务器执行（dis/B.md §6）；用户 2026-08-13 指示程序性命令偏差不作为致命问题、简化合同（dis/B.md §9）"
scientific_snapshot:
  primary: 5e52e0b1e5bd54ea00475c3a9678d47d9c315b6e
  frozen_design_path: dis/jprs_measurement_validity_gate_design_20260811.md
  frozen_design_blob: 0f475aab1995a07485d7fd5d66c6abf90a332c59
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r023-measurement-validity-20260813/SERVER_EXECUTION_REPORT.md
read_set:
  - 整个仓库可读；26 项科学输入见冻结设计 §3 的 literal identity 表
write_set:
  - outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/**
  - top_journal_v3_reaudit_055/measurement_validity_r023_20260813/**
  - dis/server_reports/orientbench-b-r023-measurement-validity-20260813/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 0, gpu_hours_max: 0, cpu_core_hours_max: 112}
  wall_time: {seconds_max: 43200}
  data:
    allowed_dataset_ids: ["existing-frozen-orientbench-evidence-readonly"]
    read_bytes_max: 549755813888
    write_bytes_max: 32212254720
  write:
    allowed_paths:
      - outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/
      - top_journal_v3_reaudit_055/measurement_validity_r023_20260813/
      - dis/server_reports/orientbench-b-r023-measurement-validity-20260813/
      - claude_code_and_supervisor.md
    bytes_max: 32212254720
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
      - https://github.com/IML-DKFZ/fd-shifts.git
conflict_keys:
  - server-execution-slot
  - dis/sug.md
  - outputs/persistent_artifacts
gates:
  - gate_id: G1
    rule: 冻结四态测量有效性 gate（设计 §6）；PASS/FAIL/INCONCLUSIVE 均属正常完整执行，服务器只报告不裁决。
  - gate_id: G2
    rule: 仅下方"硬性 kill 清单"中的失败才导致 NOT_ADJUDICATED 停止；其它一切偏差记录后继续。
early_stop_conditions:
  - 仅硬性 kill 清单；wall time 超 43200 秒。
kill_conditions:
  - 任一 26 项科学输入 bytes/SHA-256 与冻结设计 §3 表不符（管线自带 input_inventory 校验）。
  - 实际执行的 A/B/comparator/validator/mutation 代码与下方钉定 blob 不符且未在报告中如实披露差异。
  - 使用 GPU、训练、推理，或写入越出 write_set。
  - 资源超出头部五类上限。
  - 报告与实际执行不符（伪造、隐瞒偏差、把未完成写成完成）。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r023 测量有效性务实正式重执行（B 发起）

## 一句话

用已在 Git 冻结的 recovery 管线，在全新 runtime 根上从 26 项原始冻结输入完整重跑一遍，产出可供 B/C 双方裁决的正式结果。科学内容与 r020 冻结设计完全相同。

## 与 r021/r022 的区别（为什么这版能跑完）

前两轮死于程序性条款：r021 是治理哈希平台缺陷（已修，commit `99b89b8`），r022 是"操作者不得知晓历史结果"的 clean-room 条款——该条款不可满足（本计划正文就写着预注册期望），已废除。**本合同明确：操作者/会话知晓 r020 recovery 的历史结果不构成污染**；读 supervisor log、memo、计划、recovery 文档都是正常操作。实现独立性是 A/B 两套代码**写作历史**的属性（2026-08-11 已独立写成并由 comparator 零差确证），与谁运行、运行者知道什么无关。

## 执行管线（blob 级钉定，代码已于 2026-08-11 提交，先于本轮任何执行，即真正的 pre-data code seal）

代码根：`top_journal_v3_reaudit_055/measurement_validity_r020_20260811/`（本轮**允许读取和执行**，不允许修改）：

```text
pragmatic_recovery.py      fdb30ef7968521a97caa8b8ba70deb1555f8fceb   实现 A
independent_b.py           2b0458690c68f6a11587ff4c578d12cecb901698   实现 B（不依赖 A）
compare_recoveries.py      f771507fa82d6eeafd0ebb1d6f1c338a25cfa3a4   Comparator（全 replicate，atol=1e-10）
validate_recovery.py       e483c5a905545161faa8be2dddc02ca5ef4ae562   独立结构/gate 验证器
reference_probe.py         f19bb13d17d7edc89600c03fda33f76450af738e   pinned fd-shifts 参考
run_recovery_mutations.py  a622ad0af2113f6977a7ed672aeb8e9312f62149   六项语义 mutation
recovery_closure.py        e87289a2fbbfbba9908658e8f885b450475af885   闭包汇总
```

建议步骤（runtime 根 `outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/`，`--output` 全部指向其子目录；顺序、并行度、环境细节由服务器自定，照实记录即可）：

1. STARTED 单文件 commit + push（按 `dis/governance/STARTED.template.json`）。
2. 实现 A：`pragmatic_recovery.py --output <root>/full_a_r10000 --replicates 10000 --workers 39`。
3. 实现 B：`independent_b.py --output <root>/independent_b_r10000 --replicates 10000 --workers 39`。
4. Comparator：`compare_recoveries.py --a ... --b ... --output <root>/comparator_ab`。
5. Validator：`validate_recovery.py <root>/full_a_r10000 --expected-replicates 10000`。
6. 参考对齐：优先 `reference_probe.py` 现场 fetch pinned commit `c4467aec134e99691359da209f811d91283fc1e3`；网络不便时允许复用 r020 runtime 已存在的 `recovery_reference_probe.json`（SHA-256 `d989c16ddc9b5dc1638e528c4efc22ed6092f253c082266925e9f63aef6d7865`），报告写明用了哪种。
7. Mutations + closure：`run_recovery_mutations.py run ...`、`recovery_closure.py create/check ...`。
8. 写报告（模板 schema 2）：input inventory 结果、A/B gate、comparator、validator、mutation、closure、候选科学态、实际资源用量、**全部偏差列表**。结果 commit（报告 + supervisor append；runtime 留在 outputs/ 不入 Git）+ push。回执两行：`执行完毕`/`未执行完毕` + 报告路径。

## 务实规则（取代旧合同全部程序性条款）

- **Git 同步**：任何可审计的 ff-only 同步到 HTTPS main 都行，命令照实记录。push 冲突就 `pull --ff-only` 后重推，不算失败。
- **CPU**：无硬性拓扑要求。建议 pin ~48 CPU affinity、39 workers（与 recovery 相同），照实记录实际配置即可；不搞 duty-cycle 遥测合同。上限只有头部的 112 core-hours / 12h。
- **strace/tracer/postseal receipt**：不要求。完整性由确定性协议 + 双实现零差 + validator + mutations + manifest（管线自带）承担。
- **遇到未预料情况**：默认"继续执行 + 报告披露"，只有硬性 kill 清单才停。拿不准就继续并记录。
- 唯一网络例外照旧：fd-shifts pinned fetch；不装依赖、不下别的东西。

## 预注册期望（非 gate，仅供 B/C 裁决参考）

确定性协议 + 同 seed/inputs/代码，预期精确复现 recovery：405 hypotheses、5 unit + 2 dataset witnesses（唯一签名 `AR_DOMAIN / NORMALIZED_ALL_AR / linear_source_frozen / RAW_BETTER_MAIN__PROBE_BETTER_ABLATION`）、候选态 `INCONCLUSIVE_MIXED`。偏离不改结果、照实报告，由 B/C 裁决时解释。

## 激活与回执

- READY 首次提交后本文件字节冻结；根 `dis/sug.md` 逐字节镜像并由 coordination 绑定。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
- 报告后 B/C 各自 post-pull 独立核验并给 verdict；ACCEPTED/KILLED 需双方一致。
