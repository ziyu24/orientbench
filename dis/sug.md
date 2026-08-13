---
schema_version: 2
plan_id: b-r027-jprs-paper-package-20260813
dispatch_id: orientbench-b-r027-jprs-paper-package-20260813
initiator: B
base_sha: edda635b56ff29d14479249b1f2a5176ff0fc74b
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-13：路线一授权 + 『抓紧向前推进』+ 『给足任务，不要来回拉扯』——本轮把 JPRS 投稿所需的全部剩余分析、证据整合与稿件起草打包为一个派发（dis/B.md §13-§14）"
scientific_snapshot:
  primary: edda635b56ff29d14479249b1f2a5176ff0fc74b
  formal_results:
    - "DIOR r023: INCONCLUSIVE_MIXED（DIOR 内 AR-domain 签名成立：3 unit + dataset 双 endpoint；FAIR1M/SODA 不复现）"
    - "DOTA r026: CONFIRMED_EXTERNAL_STRONG（dataset AUGRC+R@70 双 witness、RTMDet 双 unit witness、swap 0.2304/0.2238）"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r027-jprs-paper-package-20260813/SERVER_EXECUTION_REPORT.md
read_set:
  - 整个仓库与 outputs/persistent_artifacts 全部既有 r014/m069/r019/r020/r023/r025/r026 冻结产物只读
write_set:
  - outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/**
  - top_journal_v3_reaudit_055/jprs_paper_package_r027_20260813/**
  - top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_jprs_r027_draft.md
  - top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/jprs_r027_supplement_draft.md
  - dis/server_reports/orientbench-b-r027-jprs-paper-package-20260813/**
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
      - outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813/
      - top_journal_v3_reaudit_055/jprs_paper_package_r027_20260813/
      - top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_jprs_r027_draft.md
      - top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/jprs_r027_supplement_draft.md
      - dis/server_reports/orientbench-b-r027-jprs-paper-package-20260813/
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
    rule: 本轮不产生任何新的正式 witness/gate。所有新计算一律标注 DESCRIPTIVE；正式主张只引用 r023 与 r026 已封存结果。
  - gate_id: G2
    rule: 仅硬性 kill 清单失败才 NOT_ADJUDICATED；其它偏差记录后继续。
early_stop_conditions:
  - 仅硬性 kill 清单；wall time 超 43200 秒。
kill_conditions:
  - 修改或删除任何既有冻结产物、既有论文文件（含 orientation_reliability_submission_r015.md）、B/C/dis 治理文件。
  - 把任何本轮新计算写成正式 witness/formal claim（G1 违反）。
  - 稿件数字与证据台账（T3）不一致且未标注。
  - 写入越出 write_set；使用 GPU/训练/推理；资源超帽；报告与实际不符。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r027 JPRS 投稿总包（B 发起：补齐分析 + 证据整合 + 全稿起草，一轮完成）

## 一句话

正式实验已经闭环（DIOR r023 + DOTA r026）。本轮把投稿前的**全部**剩余工作打包：审稿人会要的每一张补充分析表、每条主张的证据台账、可复现声明，以及一份完整的 JPRS 结构主稿草稿 + 补充材料草稿。全部新数字均为 DESCRIPTIVE，不动任何正式结论。

## T1 补充分析（全部 DESCRIPTIVE，CSV+JSON 落 runtime，生成脚本进 code root）

从 r026 matched parquets（DOTA）与 r020 runtime `rows.parquet`（DIOR/FAIR1M/SODA，recovery/r023 同源）派生：

1. **r026 欠账**：FAIR1M-source 与 SODA-A-source β 变体（r024 报告系数表）在 DOTA 上的 dataset 级点估计 + 95% cluster CI（AUGRC、R@70，主域与全 AR 域）。
2. **AR 阈值扫描**：cutoff ∈ {1.0,1.1,…,3.0} 下 Delta(probe−raw) 的曲线（点估计+CI），DIOR 三 unit、DOTA 两 unit 与两个 dataset 聚合，AUGRC+R@70——论文核心图的数据。
3. **Risk@90 补全**：DOTA 两 unit 与 dataset 聚合的 Risk@90 两域表（主研究族含 R@90，DOTA 正式族未含，描述性补齐）。
4. **逐类分解**：DOTA 15 类的主域/全域 Delta 表（行数、点估计；类内行数<500 标注低可靠）。
5. **逐 unit 完整表**：DIOR A/B/C、FAIR1M D、SODA E/F、DOTA orcnn/rtmdet 全部 4 probes × 3 endpoints × 主/全域点估计与行数（论文总表数据）。
6. **不确定性披露**：各 dataset 的 cluster 数、非零 eligible cluster 数、bootstrap SE、由 SE 推的 MDE80（方法照 r019 报告的口径，标 DESCRIPTIVE）。

## T2 复算抽验（防抄错，非重新裁决）

用独立脚本从冻结产物重算并核对进稿件的每个正式数字：r023 的 7 witness 行（Delta/DoD/CI/Holm p）与 r026 的 6 hypotheses 全行、swap 值、matched 计数（48,889/51,736）、AP parity 四值。输出 `claim_check.json`：每个数字 = {稿件值, 复算值, 产物路径, 一致布尔}。任何不一致→稿件修正后重跑，直至全一致。

## T3 证据台账（审稿与 B/C 复核的地图）

`evidence_ledger.csv`：论文每条实质主张（编号）→ 支撑轮次 id → 产物路径 → SHA-256 → formal/descriptive 标注 → 生成脚本路径。覆盖：DIOR 签名、DOTA 确认、FAIR1M/SODA 不复现、learned EQS 失败（appendix）、r014/r018/r019 历史负结果引用、探针 per-source 结构（r024 表）、全部 T1 描述性表。

## T4 主稿草稿（新文件，不碰旧稿）

写 `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_jprs_r027_draft.md`——完整 JPRS 结构：

- 标题方向：OBB 方向可靠性结论对 AR 资格域的依赖——跨数据集测量有效性研究。
- Abstract / Introduction（测量有效性框架；与 Traub AURC/AUGRC、SAOD 的关系与 delta）/ Related work。
- Methods：冻结测量协议（long-side canonicalization、δ0.75 表、r_geo、四 probes、AR 域族、cluster bootstrap + Holm + swap + ε 的完整判据；预注册与双实现审计流程本身作为方法学贡献小节）。
- Results：DIOR 正式发现（r023 表）→ DOTA 预注册外部确认（r026 表，含 ORCNN unit 未达 witness 的如实呈现）→ FAIR1M/SODA 边界（不复现，效应非普适）→ T1 描述性图表（AR 扫描曲线为核心图）。
- Discussion：对部署的含义（选择 AR 域=选择结论）；探针 per-source 结构的含义；与 EQS 失败路线的关系（附录）。
- Limitations：DOTA GT 用 prelabel 转换（annfiles 不在迁移机）、DIOR formal 门内 SODA 条件未满足、外部确认仅两检测器族、单一 val split。
- Data availability：指向 T3 台账与 reproduce 脚本。
- 正文每个数字后置 `[L#]` 标签对应台账行。masked 占位仅允许作者名/致谢。

## T5 补充材料草稿

`jprs_r027_supplement_draft.md`：完整判据形式化定义、全部 T1 表、r024 系数表、EQS 失败档案摘要（引 r018/r019/receipt 历史正式状态原文）、各轮审计链摘要（round id → 报告路径）。

## T6 报告

模板 schema 2：各任务产物清单+SHA、claim_check 全一致证明、偏差清单、资源用量。结果 commit（可多个逻辑 commit，但每个只含 write_set 路径）+ push，两行回执。

## 务实规则

同 r023 以来惯例：可审计 ff-only 同步；配置照实记录；未预料情况默认继续+披露；只有 kill 清单才停。顺序建议 T1→T2→T3→T4→T5→T6，T4/T5 允许与 T1 后半并行。稿件是**草稿**：最终定稿与投稿由用户 + B/C 审阅决定，本轮不做任何投稿动作。

## 激活与回执

- READY 首次提交后字节冻结；根 `dis/sug.md` 逐字节镜像并由 coordination 绑定。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
- 报告后 B/C post-pull 复核；C 的 r023/r026 verdict 与对本轮草稿的批注一并欢迎。
