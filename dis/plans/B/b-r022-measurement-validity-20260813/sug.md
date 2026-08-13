---
schema_version: 2
plan_id: b-r022-measurement-validity-20260813
dispatch_id: orientbench-b-r022-measurement-validity-20260813
initiator: B
base_sha: f225948844163bcf425a434a08b66df7e4a9278e
supersedes: b-r021-measurement-validity-20260812
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户会话指令 2026-08-12（B 机）：『是的，开始吧。你搞完直接让服务器执行。』记录于 dis/B.md PEER_ERA_B_MEMO_20260812 §6（memo commit c0843ac770079d06c70527347f6a8b821e94d2c9）；r021 因治理完整性早停后由同一授权延续为本 revision，见 dis/dispatch_history/orientbench-b-r021-measurement-validity-20260812.json"
scientific_snapshot:
  primary: 5e52e0b1e5bd54ea00475c3a9678d47d9c315b6e
  frozen_design_path: dis/jprs_measurement_validity_gate_design_20260811.md
  frozen_design_blob: 0f475aab1995a07485d7fd5d66c6abf90a332c59
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r022-measurement-validity-20260813/SERVER_EXECUTION_REPORT.md
read_set:
  - outputs/persistent_artifacts/m069_fullval_reliability/A/image_universe.csv
  - outputs/persistent_artifacts/m069_fullval_reliability/A/matched_fullval.jsonl
  - outputs/persistent_artifacts/m069_fullval_reliability/B/image_universe.csv
  - outputs/persistent_artifacts/m069_fullval_reliability/B/matched_fullval.jsonl
  - outputs/persistent_artifacts/m069_fullval_reliability/C/image_universe.csv
  - outputs/persistent_artifacts/m069_fullval_reliability/C/matched_fullval.jsonl
  - outputs/persistent_artifacts/m069_fullval_reliability/D/image_universe.csv
  - outputs/persistent_artifacts/m069_fullval_reliability/D/matched_fullval.jsonl
  - outputs/persistent_artifacts/m069_fullval_reliability/E/image_universe.csv
  - outputs/persistent_artifacts/m069_fullval_reliability/E/matched_fullval.jsonl
  - outputs/persistent_artifacts/m069_fullval_reliability/F/image_universe.csv
  - outputs/persistent_artifacts/m069_fullval_reliability/F/matched_fullval.jsonl
  - outputs/persistent_artifacts/orientbench_r014/features/A.parquet
  - outputs/persistent_artifacts/orientbench_r014/features/B.parquet
  - outputs/persistent_artifacts/orientbench_r014/features/C.parquet
  - outputs/persistent_artifacts/orientbench_r014/features/D.parquet
  - outputs/persistent_artifacts/orientbench_r014/features/E.parquet
  - outputs/persistent_artifacts/orientbench_r014/features/F.parquet
  - outputs/persistent_artifacts/orientbench_r014/scores/A.parquet
  - outputs/persistent_artifacts/orientbench_r014/scores/B.parquet
  - outputs/persistent_artifacts/orientbench_r014/scores/C.parquet
  - outputs/persistent_artifacts/orientbench_r014/scores/D.parquet
  - outputs/persistent_artifacts/orientbench_r014/scores/E.parquet
  - outputs/persistent_artifacts/orientbench_r014/scores/F.parquet
  - outputs/persistent_artifacts/orientbench_r014/soda_tile_to_mother_r014.csv
  - top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json
  - dis/jprs_measurement_validity_gate_design_20260811.md
  - dis/plans/B/b-r022-measurement-validity-20260813/sug.md
  - dis/sug.md
  - dis/coordination.json
  - dis/governance/**
write_set:
  - top_journal_v3_reaudit_055/measurement_validity_r022_20260813/**
  - outputs/persistent_artifacts/orientbench_measurement_validity_r022_20260813/**
  - outputs/persistent_artifacts/orientbench_measurement_validity_r022_20260813_postseal_receipt/**
  - dis/server_reports/orientbench-b-r022-measurement-validity-20260813/**
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
      - top_journal_v3_reaudit_055/measurement_validity_r022_20260813/
      - outputs/persistent_artifacts/orientbench_measurement_validity_r022_20260813/
      - outputs/persistent_artifacts/orientbench_measurement_validity_r022_20260813_postseal_receipt/
      - dis/server_reports/orientbench-b-r022-measurement-validity-20260813/
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
  - top_journal_v3_reaudit_055
gates:
  - gate_id: G1
    rule: 冻结四态测量有效性 gate（设计 §6）——PASS_TO_EXTERNAL_CONFIRMATION / FAIL_GENERIC_OR_NULL / INCONCLUSIVE_MIXED 三者均属正常完整执行；服务器只报告，不裁决论文 claim。
  - gate_id: G2
    rule: 审计闭包 gate——任一 input identity、实现独立性、A/B parity、bootstrap、mutation、manifest、tracer/strace 闭包、资源边界、Git、治理校验或 receipt 失败即 NOT_ADJUDICATED，禁止发射科学数字。
early_stop_conditions:
  - 仅允许技术/provenance/审计失败早停（G2）；不利科学中间结果不得早停，A-F 六 unit 与 10000 replicate 必须完成。
  - wall time 超过 43200 秒。
kill_conditions:
  - 任一 26 项科学输入 bytes/SHA-256 与冻结表不符。
  - 读取任何禁读材料（receipt3 任何产物、r020 runtime 根含 recovery 输出、learned EQS 列、r011/HRSC/DOTA-r019 资产）。
  - 实现 A/B 独立性或 B-before-A 时序被破坏；comparator 容差外差异。
  - 六项 mutation 任一 pristine 未过或 mutated 未被非零拒绝。
  - Git 同步/执行基线/push 不变量失败；写入越出 write_set；资源超出本头部五类上限。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r022 测量有效性正式重执行（B 发起，r021 revision）

## 科学问题、证据与 unknown

可证伪问题与 r020 完全相同（冻结设计 §2）：OBB 长边等价、几何归一化、AR domain 与 scene cluster 是否实质改变 Core A-F 冻结资产上的 orientation-reliability 结论。本计划**不改变任何科学内容**——同 26 输入、同 4 probes/3 contrasts/3 endpoints/5 ablations、同 270/135 Holm 族、同 seed=20260809 与 replicate 0..9999、同四态 gate。

revision 历史：r020 正式合同因两项 preflight 环境错配早停；用户授权的 pragmatic recovery 得到候选态 `INCONCLUSIVE_MIXED` 但时序性密封无法事后重建；r021（`dis/plans/B/b-r021-measurement-validity-20260812/sug.md`）在治理预检阶段因控制面 CRLF 哈希矛盾早停（`dis/dispatch_history/orientbench-b-r021-measurement-validity-20260812.json`），未打开任何科学输入。本 r022 为 r021 的逐字节等价 revision（仅 id/路径/base/授权链更新），在治理修复落地后执行。r021 的 report 根已消费，不复用。

已知证据：recovery 双独立实现 A/B 全 replicate 零差（≤1e-10 硬保证）、validator PASS、六 mutation 语义正确（B 代码级审计见 `dis/B.md` PEER_ERA_B_MEMO_20260812 §2）。unknown：服务器环境自 2026-08-11 后是否变化；r022 是否精确复现 recovery 数字（见下方预注册期望）。

**预注册一致性期望（非 gate，仅供裁决）**：确定性协议下 r022 应精确复现 405 hypotheses、5 unit + 2 dataset witnesses（唯一签名 `AR_DOMAIN / NORMALIZED_ALL_AR / linear_source_frozen / RAW_BETTER_MAIN__PROBE_BETTER_ABLATION`）与候选态 `INCONCLUSIVE_MIXED`。服务器不得据此改动计算或结果；任何偏离必须原样报告，由 B/C 在裁决中作为红旗单独解释。

## 固定协议与实现自由度

**科学协议整体引用冻结设计文档** `dis/jprs_measurement_validity_gate_design_20260811.md`（Git blob `0f475aab1995a07485d7fd5d66c6abf90a332c59`，以 blob 字节为准）：其 §3（冻结总体、membership、26 输入 literal identity 表、strict 1:1 join）、§4（probes/风险/端点/消融/SCENE_MACRO 描述合同）、§5（bootstrap、multiplicity、operand/epsilon/swap/witness 谓词、Holm）、§6（四态裁决与 precedence）、§7（双 clean-room B-before-A、comparator、六 mutation、无环双 seal、tracer + strace 双向闭包、manifest、report/receipt 语义）、§8 中除下列 delta 外的全部条款（wall/runtime 上限从本计划头部、CPU 合同见 Delta-2、pinned fd-shifts fetch 的 remote/commit/blob/raw-SHA/AST-adapter 条款原样有效）对本计划**全文约束**。

**Token 重映射**：设计文档中 round_id `orientbench-c-r020-measurement-validity-20260811` 与 r020 的 code root、runtime root、postseal receipt root、report path，一律替换为本计划头部对应 r022 值；`C_POSTPULL_ADJUDICATION` 一律替换为 `B_AND_C_POSTPULL_ADJUDICATION`。r020 与 r021 各路径永久消费，禁止复用或读取。

**Delta-1（Git 同步方法，修复 r020 缺陷一）**：权威远端仍是显式 `https://github.com/ziyu24/orientbench.git`。允许下列任一同步方法，命令逐字记录并附前后 HEAD 与 reflog：
1. `git pull --ff-only https://github.com/ziyu24/orientbench.git main`；
2. `git fetch https://github.com/ziyu24/orientbench.git main` 后 `git merge --ff-only FETCH_HEAD`；
3. 当且仅当 `git remote get-url origin` 精确等于上述 HTTPS URL（记录输出）时，`git fetch origin main` 后 `git merge --ff-only origin/main`。
不变量：同步后 HEAD 必须等于 `git ls-remote https://github.com/ziyu24/orientbench.git refs/heads/main`；worktree/index clean；派发 commit 必须是同步后 HEAD 的祖先或本身。SSH 形式的 origin 禁止参与任何网络命令。

**Delta-2（CPU 拓扑，修复 r020 缺陷二）**：preflight 要求在线逻辑 CPU ≥ 48（记录 `nproc`、`lscpu`、cgroup cpuset）。服务器为整个 r022 进程树固定一个显式 48 逻辑 CPU 亲和集并记录集合成员；定义 `N := 48`（授权 job CPU 集大小），telemetry 分母为 `30*48`。39 worker processes、BLAS threads=1、replicate-to-worker `replicate_id % 39` 不变。bootstrap 并行阶段每完整 30 秒 interval 的 job CPU 占比须由 duty-cycle 节流保持在 `[60%, 80%]`；连续三个完整 interval <60% 且无逐 interval `IO_WAIT|SERIAL_PHASE` 理由、或任一完整 interval >80%，均异常。preflight/serial/finalization interval 只记 phase/reason，不适用下限。每 30 秒采集进程树 CPU-time/RSS/affinity、活跃/暂停 worker 数与节流事件。

**Delta-3（服务器提交协议）**：服务器核验通过后，先提交并推送唯一 STARTED 记录（`dis/server_reports/orientbench-b-r022-measurement-validity-20260813/STARTED.json`，按 `dis/governance/STARTED.template.json`，该 commit 只含此一个文件），并把该 STARTED commit 冻结为 `execution_base`。执行结束后恰一个 non-merge 结果 commit，父 commit 必须是 `execution_base`，只含 write_set 内 tracked 路径；final commit 前须核验 HTTPS remote main 仍等于 `execution_base`，远端移动即异常停止，禁止 merge/rebase/amend/force。push 后按设计 §8 完成 post-seal external receipt 才可回执。

**Delta-4（回执协议）**：服务器最终对话严格两行——第一行 `执行完毕` 或 `未执行完毕`，第二行唯一报告路径 `dis/server_reports/orientbench-b-r022-measurement-validity-20260813/SERVER_EXECUTION_REPORT.md`。三种科学四态（PASS/FAIL/INCONCLUSIVE）+ 完整协议 + 有效 receipt 均属 `执行完毕`；任何技术/provenance/审计/发布缺陷属 `未执行完毕`。报告按 `dis/governance/SERVER_EXECUTION_REPORT.template.md` schema_version 2。

**Delta-5（禁读扩展）**：除设计原有禁读外，`top_journal_v3_reaudit_055/measurement_validity_r020_20260811/**`（含全部 recovery 代码与文档）、`outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811*/**`（含 recovery runtime）、receipt1/2/3 全部产物，均为禁读科学输入；r022 的 A/B/comparator 实现必须全新书写，不得复制、import 或读取 r020/recovery 代码文件。tracer/strace 中出现对上述路径的 read-capable open 即异常。

**Delta-6（裁决归属）**：服务器报告与 postseal receipt 只表示执行完整性。正式科学态由 B 与 C 各自 post-pull 独立核验并给出可追溯 verdict 后按协议 §6 生效（ACCEPTED/KILLED 需双方 verdict，分歧进入 CONTESTED）。服务器不冒充 B/C，不写 verdict。

**Delta-7（治理预检显式化，回应 r021 早停）**：T1 preflight 必须在服务器 checkout 上运行 `dis/governance/test_peer_governance.py` 与 `dis/governance/validate_peer_governance.py . --check-local-worker` 并全部通过、记录输出哈希；任何治理校验失败即 `未执行完毕`，不得绕过或本地改写治理文件。

**实现自由度**（不改变科学含义，须在报告披露）：进程亲和与 duty-cycle 的具体机制；流式哈希与 manifest 生成机制；若环境缺 `loguru` 导致 fd-shifts 全量 import 失败，按设计 §8 使用 AST-verbatim adapter 并保留 exact-function-span 证据；A/B 实现的内部代码组织（在满足独立性与冻结常量的前提下）。

## 任务、Gate 与反证

| 任务 | 必需产物 | Gate | Early stop | Kill condition |
|---|---|---|---|---|
| T1 preflight（Git/CPU/路径/授权/治理校验） | preflight 记录（runtime root） | 全部不变量成立且治理校验通过 | 任一不变量失败→未执行完毕 | 见头部 kill 列表 |
| T2 STARTED 提交与 execution_base 冻结 | STARTED.json commit+push | commit 只含单文件且被推送 | push 失败 | 远端不符 |
| T3 synthetic fixtures + code seal | code root 密封清单 | 首个科学输入打开前完成 | seal 后代码变化 | 时序违反 |
| T4 实现 B（raw→10k bootstrap→封存） | B 输出 bundle | trace 无 A、无禁读 | — | 独立性破坏 |
| T5 实现 A（同上，B 封存后） | A 输出 bundle | trace 无 B、无禁读 | — | 独立性破坏 |
| T6 Comparator C + 前四项 mutation | comparator 与 mutation 记录 | 全 replicate 容差内一致；mutation pristine=0/mutated≠0 | — | 容差外差异 |
| T7 runtime freeze→manifest→第五/六项 mutation→report | manifest、报告 exact bytes | 双向 access 闭包成立 | — | 闭包失败 |
| T8 结果 commit+push+postseal receipt | 结果 commit、receipt | remote main==execution_base；receipt 闭合 | 远端移动 | 发布失败 |

## 激活与回执

- 本文件 READY 首次提交后字节永久冻结；实质变化必须新建 revision/id。
- 激活时根 `dis/sug.md` 必须与本文件 committed blob 逐字节相同，并由 `dis/coordination.json` 绑定 plan path、plan commit、blob OID、SHA-256、dispatch id、risk、资源与唯一报告路径。
- 本计划只有在治理修复（archive 哈希 blob 级化）合入 main 之后才可激活；激活前 B 须在本机确认修复后的治理校验通过。
- 服务器只接受用户交付的精确 `dispatch_id + plan_path + dispatch_commit_sha`，不扫描候选。
- L2 授权 reference 见头部；授权仅覆盖本计划一次执行，不延展。
- 最终对话严格两行：第一行 `执行完毕` 或 `未执行完毕`；第二行唯一报告路径。
