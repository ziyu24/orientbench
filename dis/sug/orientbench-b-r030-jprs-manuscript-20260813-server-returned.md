---
schema_version: 2
plan_id: b-r030-jprs-manuscript-20260813
dispatch_id: orientbench-b-r030-jprs-manuscript-20260813
initiator: B
base_sha: 0b36d344865d9a3121df5933b3274a3515396c80
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-13：『如果要搞论文，先搞md的，要求除了图片不在文档中，其他该有的都必须有，并且不该有的不能有……稿件内容要完整、科学、规范。』"
scientific_snapshot:
  primary: 0b36d344865d9a3121df5933b3274a3515396c80
  joint_scientific_state: "AUDITED_EXTERNAL_REPLICATION_ACCEPTED（B/C 一致，contest RESOLVED，见 dis/B.md §16 与 dis/reviews/C/orientbench-r029-final-replay-review-20260813.md）"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r030-jprs-manuscript-20260813/SERVER_EXECUTION_REPORT.md
read_set:
  - 整个仓库只读；数字来源限定为 audit_bundles/r028/**、既有冻结 runtime 产物与各轮正式报告
write_set:
  - top_journal_v3_reaudit_055/paper_A_orientation_protocol/manuscript_r030/**
  - outputs/persistent_artifacts/orientbench_jprs_manuscript_r030_20260813/**
  - dis/server_reports/orientbench-b-r030-jprs-manuscript-20260813/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 0, gpu_hours_max: 0, cpu_core_hours_max: 24}
  wall_time: {seconds_max: 43200}
  data:
    allowed_dataset_ids: ["repository-tracked-evidence", "existing-frozen-orientbench-evidence-readonly"]
    read_bytes_max: 549755813888
    write_bytes_max: 5368709120
  write:
    allowed_paths:
      - top_journal_v3_reaudit_055/paper_A_orientation_protocol/manuscript_r030/
      - outputs/persistent_artifacts/orientbench_jprs_manuscript_r030_20260813/
      - dis/server_reports/orientbench-b-r030-jprs-manuscript-20260813/
      - claude_code_and_supervisor.md
    bytes_max: 5368709120
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
conflict_keys:
  - server-execution-slot
  - dis/sug.md
gates:
  - gate_id: G1
    rule: 零新科学计算。正式数字只能取自既有冻结产物/bundle；描述性数字只能取自既有 r027/r028 修正表；每个进稿数字必须通过 T4 的 claim-check。
  - gate_id: G2
    rule: 诚实红线（见"禁止出现"清单）任何一条违反即 kill；其它偏差记录后继续。
early_stop_conditions:
  - 仅硬性 kill 清单；wall time 超 43200 秒。
kill_conditions:
  - 稿件出现"禁止出现"清单中的任何内容。
  - 任何进稿数字未通过 claim-check 或引用不存在的产物。
  - 修改任何既有冻结文件、旧稿、治理文件；写入越出 write_set。
  - 引文含捏造的字段（不确定的 DOI/页码宁缺毋滥，禁止编造）。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r030 完整稿件包（B 发起；md 优先，完整、科学、规范）

## 一句话

科学已闭环（联合态 `AUDITED_EXTERNAL_REPLICATION_ACCEPTED`），本轮产出**可供作者定稿的完整 md 主稿 + 补充材料 + 成图资产 + 逐数字证据校验**。图片不嵌入 md（文件另存、md 内路径引用），一切不实内容零容忍。

## T1 主稿 `manuscript_r030/orientation_reliability_manuscript.md`

**必须包含（该有的都有）**：

1. Title（面向测量有效性贡献的正式标题）＋ 作者块**明示占位**（`[作者与单位：由项目所有者定稿填写]`——不得编造姓名/单位/邮箱/ORCID）。
2. Abstract（200-300 词）＋ Keywords（5-7 个）。
3. §1 Introduction：问题（单一 AURC/AUGRC 与未声明 AR 资格域可能翻转 OBB 方向可靠性结论）、贡献列表（逐条、可核验措辞）。
4. §2 Related work：selective classification 与 AURC/AUGRC（Traub 等）、检测可靠性（SAOD）、OBB 检测器（Oriented R-CNN、RTMDet、PSC）与数据集（DOTA、DIOR-R、FAIR1M、SODA-A）、方向表示与长边等价问题。只引真实存在的工作。
5. §3 Evidence base：冻结资产（m069/r014 六 unit、DOTA val 5297/458/55804）、matching、GT 来源（含 prelabel 转换的如实说明）、per-source 线性探针系数结构（r024 表）。
6. §4 Measurement protocol：canonical 长边角、δ0.75 表与 r_geo、四 probes、AR 域与五消融、AUGRC/R@70/R@90 端点、mother/image cluster bootstrap、ε/swap/Holm/witness 完整判据、四态 gate——公式齐全，符号规范。
7. §5 Results：5.1 DIOR 正式结果（r023：7 witnesses 表、`INCONCLUSIVE_MIXED` 按其跨数据集门的含义）；5.2 DOTA 外部复现（r026/r028/r029：6 hypotheses 全表、数值 gate 输出与 **`POST_OUTCOME_AUDITED_EXTERNAL_REPLICATION`** 身份声明并列，ORCNN unit 未达 witness 如实呈现）；5.3 FAIR1M/SODA 不复现边界；5.4 描述性分析（AR 扫描、β 敏感性、R@90、逐类——全部标 DESCRIPTIVE）。
8. §6 Audit and reproducibility：双实现/comparator/raw 重验/真实 mutation/跨机 bundle；**含 r026 首版审计缺陷与纠正史的透明披露**；预注册与结果揭示时间线表（round → commit SHA → 日期）。
9. §7 Discussion 与 §8 Limitations（至少含：post-outcome 身份、GT 转换来源、单一外部数据集、两检测器族、EQS 失败附录归属）。
10. §9 Conclusion；Data and code availability（指向仓库与 `audit_bundles/r028/`，只写真实可用的获取方式）；References（编号制，全部真实文献；不确定的 DOI/卷页宁缺毋滥）；Figure captions 一节（每图：文件相对路径 + 完整题注）。

**禁止出现（不该有的不能有）**：任何期刊投稿状态字样（"Submitted to/待投/在审/manuscript ID"）；编造的作者/单位/邮箱/基金号/致谢；捏造或不可核验的引文字段；"preregistered independent confirmation"或以 `CONFIRMED_EXTERNAL_STRONG` 作为证据身份的措辞；任何未经 claim-check 的数字；夸大的可用性承诺；嵌入图片（base64 或二进制内嵌）。

## T2 补充材料 `manuscript_r030/supplement.md`

判据完整形式化、全部描述表、r024 系数表、EQS 失败档案（引历史正式状态原文）、逐轮审计链索引（round → 报告路径 → 关键 SHA）、bundle 重放指南（C 已验证的命令序列）。

## T3 成图资产 `manuscript_r030/figures/`

从 bundle/修正表生成正式图文件（SVG+PNG 双格式）+ 每图一个可重跑脚本 + `figure_manifest.csv`（文件、来源数据路径、SHA-256）。至少：AR 阈值扫描主图、DIOR/DOTA witness 效应量-CI 图、风险定义示意（δ0.75 曲线）、bootstrap 分布图。md 只引路径不嵌图。

## T4 逐数字 claim-check `manuscript_r030/claim_check.json`

脚本扫描主稿与补充材料中的每个数值 token（表格与正文），映射到源产物路径并程序化比对；输出 {数字, 稿件位置, 来源, 比对值, 一致}，**全部一致才允许收尾**；报告附统计。引用文献另出 `reference_list.json`：每条 {条目, 项目内依据（如冻结设计/报告中已引用）, 置信说明}。

## T5 报告

模板 schema 2（严格全字段）：产物清单+SHA、claim-check 统计、禁止清单自查表（逐条声明未出现）、偏差、资源。结果 commit + push，两行回执。

## 务实规则

同前例；本轮唯一红线是 G2 诚实清单。文风要求：正式学术英文（主稿与补充材料英文成稿，题注与正文一致）；md 表格规范、公式用 LaTeX 内联记法；章节编号连续。

## 激活与回执

- READY 首次提交后字节冻结；根 `dis/sug.md` 逐字节镜像并由 coordination 绑定。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
- 报告后 B 复核（含 claim-check 抽验与禁止清单核查）、C 审阅；定稿与投稿由用户决定。
