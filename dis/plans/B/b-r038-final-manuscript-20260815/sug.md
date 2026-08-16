---
schema_version: 2
plan_id: b-r038-final-manuscript-20260815
dispatch_id: orientbench-b-r038-final-manuscript-20260815
initiator: B
base_sha: 096e8afa2ef6230e32ab33122e24ed8330182789
supersedes: b-r030-jprs-manuscript-20260813
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-15：『现在什么期刊水平……水平可以降低，不要死扛面子。同时给出服务器下一步计划。』——授权按 STRONG_JSTARS/Remote Sensing 档位完成最终成稿包"
scientific_snapshot:
  primary: 096e8afa2ef6230e32ab33122e24ed8330182789
  joint_terminal_states:
    - "r034: K1_K2_KILL——旧测量主张=评测定义性后果的定量刻画（B/C 终局）"
    - "r036/r037: Q-SetOD 集合路线终止、多峰主张删除；QSETOD_EVIDENCE_SCORE_ONLY 仅作描述性诊断（B/C 一致）"
    - "清白 endpoint（DOTA-v2.0 val、SODA-A official test）未消费，本轮禁触"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r038-final-manuscript-20260815/SERVER_EXECUTION_REPORT.md
read_set:
  - 整个仓库与全部冻结产物/bundle 只读；数字来源限定为 audit_bundles/r028、r034、r036、r037 与各轮正式报告
write_set:
  - top_journal_v3_reaudit_055/paper_A_orientation_protocol/manuscript_r038/**
  - outputs/persistent_artifacts/orientbench_final_manuscript_r038_20260815/**
  - dis/server_reports/orientbench-b-r038-final-manuscript-20260815/**
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
      - top_journal_v3_reaudit_055/paper_A_orientation_protocol/manuscript_r038/
      - outputs/persistent_artifacts/orientbench_final_manuscript_r038_20260815/
      - dis/server_reports/orientbench-b-r038-final-manuscript-20260815/
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
    rule: 零新科学计算、零新 gate。正式数字只取冻结产物；每个进稿数字过 T3 固定 claim-id 校验；触碰清白 endpoint 即 kill。
  - gate_id: G2
    rule: 诚实红线（正文禁止清单）任何一条违反即 kill；其它偏差记录后继续。
early_stop_conditions:
  - 仅硬性 kill 清单；wall time 超 43200 秒。
kill_conditions:
  - 稿件出现禁止清单内容（投稿状态字样、编造作者/基金/引文、prospective/preregistration 语汇、把 QSETOD_EVIDENCE_SCORE_ONLY 或已终止路线包装成方法贡献、隐瞒 r026/r037 审计事故史）。
  - 任何数字未过 T3 claim-check；读取或使用 DOTA-v2.0 val / SODA-A official test。
  - 修改冻结产物/治理文件；写入越出 write_set；报告与实际不符。
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: 执行完毕}
  gated_early_stop: {execution_status: complete, receipt_first_line: 执行完毕}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  partial: {execution_status: incomplete, receipt_first_line: 未执行完毕}
  protocol_drift: {execution_status: incomplete, receipt_first_line: 未执行完毕}
---

# r038 最终成稿包（B 发起；目标 IEEE JSTARS / Remote Sensing，诚实档位，不再升格）

## 一句话

科学到此收口：把 r023/r026/r034/r036/r037 的全部终局结果写成一篇完整、诚实、投得出去的 md 论文。定位是**测量学/评测方法论文**：证明 OBB 方向可靠性评测在五要素未声明前不适定，量化"资格域选择翻转结论"主要是定义性后果，并给出社区可用的报告清单与诊断协议。

## T1 主稿 `manuscript_r038/orientation_reliability_final.md`（英文，md，图片不嵌入）

在 r030 骨架上重建，结构必备：Title；作者块明示占位；Abstract+Keywords；Introduction（贡献=①方向可靠性评测五要素不适定性的系统证明与报告清单；②资格域效应的三元分解——定义机械成分/AR 信息成分/剩余成分的量化（r034 全表）；③跨 DIOR/DOTA 的诊断协议与全链可重放审计基础设施；④TTA 证据信息与集合校准迁移失败的负结果档案（r036/r037，描述级））；Related work（补齐外部审稿人指出的 GWD/KLD 方形不可辨识、CSL/DCL、H2RBox、selective prediction；NO_LONGSIDE/NO_GEONORM 稳健性正结果明写）；Data & setup（八单元全公开、AP 数字、匹配规则全文、探针 per-source 系数、floors/阈值出处）；Measurement protocol（公式全）；Results（r023 DIOR 表→r026 DOTA 外部复现表→**r034 三元分解为全文高潮**：AR-only 解释 ≥80% 翻转、R_raw 下消失、剩余 DoD 正但不达 witness→FAIR1M/SODA 边界→r036/r037 证据与校准负结果）；实用产出（五要素报告清单+评测工具箱指引）；Audit & reproducibility（bundle 重放指南；**r026 与 r037 两次审计事故及纠正史如实入正文附录**，先于审稿人自曝）；Discussion；Limitations；Conclusion；Data availability；真实 References（不确定字段宁缺毋滥）；图题清单（文件路径引用）。

**语言红线**：全稿使用"frozen sensitivity-analysis framework"级别的标准统计语言；禁止 prospective/preregistered independent confirmation 语汇；禁止投稿状态字样；禁止把已终止路线或 EVIDENCE_SCORE_ONLY 写成方法贡献；作者/基金/致谢只留明示占位。

## T2 补充材料 + 成图

`supplement.md`：判据形式化、全部轮次结果表、r024 系数表、EQS 失败档案、审计链时间线（round→commit→结论）、bundle 重放命令。成图（SVG+PNG+脚本+manifest）：三元分解瀑布图（核心图）、AR 扫描曲线、DIOR/DOTA 效应量-CI 图、覆盖迁移失败图、实例示意图数据。

## T3 claim-check 重写（按 C 对 r030 的批评）

固定 claim-id 清单：每个进稿数字一条 {claim_id, 稿件位置, 源文件, 字段/行键, 变换, 容差}；校验器逐条精确比对，**禁止最近值匹配**；全部一致才许收尾。输出 `claim_check.json` + 引文核查表。

## T4 审计与报告

双人复核不适用于纯写作轮，但 T3 校验器代码必须独立于稿件生成代码书写；报告（模板 schema 2 严格全字段）：产物+SHA、claim-check 统计、禁止清单逐条自查、偏差、资源。结果 commit + push，两行回执。

## 务实规则

同既定惯例。本轮之后：投稿与否、作者信息、目标刊最终选择（JSTARS vs Remote Sensing）由用户决定；若用户将来授权"新方法构建 + 清白 endpoint 验证"的 GPU 投资，另立新计划，与本稿互不阻塞。

## 激活与回执

- READY 首次提交后字节冻结；根 `dis/sug.md` 逐字节镜像并由 coordination 绑定。
- 服务器只接受用户交付的 `dispatch_id + plan_path + dispatch_commit_sha`。
- 报告后 B 复核（claim 抽验+禁止清单）、C 审阅；B/C verdict 一致即为项目科学阶段收口。
