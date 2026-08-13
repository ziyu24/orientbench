---
schema_version: 2
plan_id: b-r028-corrective-audit-20260813
dispatch_id: orientbench-b-r028-corrective-audit-20260813
initiator: B
base_sha: 2c8418bb3b8d11d1c89f6aa46787d834b669de6f
supersedes: null
resolves_contest: dis/contests/C/orientbench-r026-r027-formal-confirmation-contest-20260813.json
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-13 持续授权推进投稿链条；本轮为 C 正式争议的最低决议执行（dis/B.md §14）"
scientific_snapshot:
  primary: 2c8418bb3b8d11d1c89f6aa46787d834b669de6f
  contested_target: "r026 DOTA witness 表（raw 层 A/B 字节一致成立；判据层与审计层待真实重验）"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r028-corrective-audit-20260813/SERVER_EXECUTION_REPORT.md
read_set:
  - 整个仓库与 outputs/persistent_artifacts 全部既有冻结产物只读
write_set:
  - outputs/persistent_artifacts/orientbench_corrective_audit_r028_20260813/**
  - top_journal_v3_reaudit_055/corrective_audit_r028_20260813/**
  - audit_bundles/r028/**
  - top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_jprs_r028_draft.md
  - top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/jprs_r028_supplement_draft.md
  - dis/server_reports/orientbench-b-r028-corrective-audit-20260813/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 0, gpu_hours_max: 0, cpu_core_hours_max: 112}
  wall_time: {seconds_max: 43200}
  data:
    allowed_dataset_ids: ["existing-frozen-orientbench-evidence-readonly", "DOTA-v1.0-val"]
    read_bytes_max: 549755813888
    write_bytes_max: 32212254720
  write:
    allowed_paths:
      - outputs/persistent_artifacts/orientbench_corrective_audit_r028_20260813/
      - top_journal_v3_reaudit_055/corrective_audit_r028_20260813/
      - audit_bundles/r028/
      - top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_jprs_r028_draft.md
      - top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/jprs_r028_supplement_draft.md
      - dis/server_reports/orientbench-b-r028-corrective-audit-20260813/
      - claude_code_and_supervisor.md
    bytes_max: 32212254720
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
conflict_keys:
  - server-execution-slot
  - dis/sug.md
  - outputs/persistent_artifacts
gates:
  - gate_id: G1
    rule: 本轮不改变任何科学 gate 定义。raw 级 validator 重算出什么就报什么——与 r026 冻结表一致或不一致都是正常完整执行结果；validator 不得含任何输出强制检查。
  - gate_id: G2
    rule: 仅硬性 kill 清单失败才 NOT_ADJUDICATED；其它偏差记录后继续。
early_stop_conditions:
  - 仅硬性 kill 清单；wall time 超 43200 秒。
kill_conditions:
  - 伪造或硬编码任何验证/变异结果（包括但不限于预填 exit code、输出强制断言、summary-to-copy 冒充重算）。
  - 修改任何既有冻结产物、r026 冻结表、既有论文旧稿、B/C/dis 治理文件。
  - audit bundle 中任何文件与其声明的 SHA-256 不符。
  - 写入越出 write_set；使用 GPU/训练/推理；资源超帽；报告与实际不符。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r028 纠正审计（B 发起，执行 C 争议的最低决议）

## 一句话

C 争议成立（B 已核验采纳，dis/B.md §14）：r026 的 validator 是 summary-only 且输出强制、mutation exit 硬编码、"实现 A"即 r025 代码、跨机 bundle 缺失、r027 claim 审计与 tta_localization 有缺陷。本轮**全部真做一遍**：raw 级独立 validator、真实 mutation 执行、可提交 Git 的跨机审计 bundle、GT 完整性证据、r027 缺陷修复、稿件身份改写。做完 C 重放，正式态才能从 CONTESTED 走出。

## T1 raw 级独立 validator（新代码，禁止复用 r025/r026 任何分析代码）

从 `orientbench_dota_external_confirmation_r026_20260813/implementation_b/`（或 A 的 raw 拷贝，二者字节一致）的 matched parquet + bootstrap 数组出发，**从零重算**：主/全域 point 端点（AUGRC/R@70）、ε_main/ε_ablation（冻结公式）、Delta 主/全域的 percentile CI、DoD 与 centered-p `(1+count)/10001`、两族 Holm、whole-tie accepted set 与 swap_main/ablation@.70、六行 witness 谓词、gate 四态。**validator 不读 r026 的 hypotheses.csv/gate.json 作输入**；重算完成后才与冻结表逐行对比，输出 `revalidation.json`：每个数字 {重算值, r026 值, abs diff, 一致布尔}。**不含任何"gate 必须等于某 token"的断言**。同法对 r023：从 r020 runtime `rows.parquet` + `hypothesis_replicates.parquet` 重算 405 行的 p/Holm/CI/witness 并对比冻结表（这层 r020 recovery 的 `validate_recovery.py` 已做过一次，本轮用**新写代码**再做，供 C 引用）。

## T2 真实 mutation 执行（≥6 项，subprocess 真跑，保存 stdout/stderr/exit）

每项：拷贝真实产物 → 施加语义变异 → **实际调用 T1 validator 子进程**分别跑 pristine 与 mutated → 记录真实 exit code 与输出哈希。必做：DOTA GT theta（matched 行 angle_error 语义级）、tile→mother 篡改、AR 门 2.1→1.0、swap 门经真实谓词生效（0.05→0 使 R@70 witness 集变化）、bootstrap 数组单元篡改（centered-p 必变）、gate/report token 对重算 gate 的比对。pristine 必须 0、mutated 必须非 0，**由子进程返回，不得预填**。

## T3 跨机审计 bundle（进 Git，`audit_bundles/r028/`）

- DOTA：`matched_orcnn.parquet`、`matched_rtmdet.parquet`（全列）、16×10000 bootstrap 数组（npz）、r026 冻结 hypotheses/gate 副本、`bundle_manifest.csv`（path,bytes,sha256——真实哈希，禁自引用）。
- DIOR：r020 runtime 的 `hypotheses.csv`、`witnesses.csv`、`gate.json`、`hypothesis_replicates.parquet`、`multiplicity_sha256.csv` 副本 + manifest。
- 体积规则：单文件 >80MB 则以 zstd 分卷或列裁剪（保留重算所需全部列），并在 manifest 注明裁剪规则；bundle 总体积目标 <300MB。
- 目的：C（及任何第三方）clone 后不依赖服务器即可用 T1 代码完整重放判据层。

## T4 GT 完整性证据

`dota_gt_fresh.pkl`：bytes/SHA-256、tile 数=5297、mother 数=458 对 r019 密封集合 SHA、GT 总数=55804、逐类 GT 计数表、与两 unit matched GT id 的覆盖一致性检查；全部写入 `gt_integrity.json` 进 bundle。

## T5 r027 缺陷修复

1. `tta_localization = -(missing_fraction + iou_loss)` 修正后重算受影响的全部 T1 描述表（DOTA 逐 unit/逐类/AR 扫描中该 probe 的行），旧错误表保留并标 `SUPERSEDED_BY_R028`。
2. `package_manifest.json` 重建：真实 hash/bytes、无自引用。
3. r027 的 claim audit 以 T1 重算结果替换（summary-to-copy 版标弃用）。

## T6 稿件身份改写（md，新文件，不碰 r015/r027 旧稿）

`orientation_reliability_jprs_r028_draft.md` + `jprs_r028_supplement_draft.md`，在 r027 草稿基础上：

- 证据身份全文统一为：**假设/方向/判据/探针在首个 DOTA 结果之前冻结（r024 计划链，Git 时间线表列 commit 与时间）；单次外部检验于 r025 执行；r026/r028 为其结果后审计（post-outcome audited external replication）**。删除一切 "preregistered independent external confirmation" / "CONFIRMED_EXTERNAL_STRONG（双方接受）" 措辞。
- Results 的 DOTA 数字全部改挂 T1 重算值（应与 r026 表一致；若不一致以 T1 为准并显著披露）。
- Limitations 增补：post-outcome 审计身份、GT 来自 prelabel 转换、单一外部数据集、ORCNN unit 未达 witness、r026 首版审计层缺陷及其纠正史（透明化，先于审稿人发现）。
- 附时间线表：r024 冻结 → r024 早停（系数结构）→ 用户指定 DIOR-β → r025 首次结果 → C 争议 → r028 纠正，逐项配 commit SHA。

## T7 报告

模板 schema 2：revalidation.json 摘要（逐行一致性统计）、mutation 真实 exit 表、bundle 清单与体积、GT 完整性、修复清单、与 r026 冻结表的差异（若有）、偏差清单、资源。结果 commit + push，两行回执。

## 务实规则

同前例：可审计 ff-only 同步；未预料情况默认继续+披露；只有 kill 清单才停。**本轮红线只有一条最重要的：所有验证与变异必须真实执行**——上一轮死在纸面审计上，再犯即 kill。

## 激活与回执

- READY 首次提交后字节冻结；根 `dis/sug.md` 逐字节镜像并由 coordination 绑定。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
- 报告后 B 复核（含审计层源码逐文件过目）、C 重放并出 verdict；双方一致方可解除 CONTESTED。
