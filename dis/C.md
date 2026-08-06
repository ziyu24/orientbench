# OrientBench C 侧 r008 验收与 r009 evidence closure

- round: `orientbench-c-r009-20260806`
- scientific snapshot: `c51c9f826028e083633edbaaa7ad32d1178a5744`
- active manuscript: [`orientation_reliability_paper_A_zh_v078.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v078.md)
- r008 report: [`orientbench-c-r008-20260806.md`](server_reports/orientbench-c-r008-20260806.md)
- formal state: r008 provenance=`ADOPT`; hygiene=`FAIL_CLAIM_QUARANTINE_R008`; measurement core=`INCONCLUSIVE_CORE_EVIDENCE`; submission=`NOT_READY`
- innovation potential / venue ceiling: **strong JSTARS；TGRS-borderline conditional**
- current evidence maturity: **JSTARS plausible, NOT_READY；TGRS high-risk**
- `cc_recommendation: no`：当前分歧由服务器 full-evaluator 实验与只读 validator 裁决；完成 r009 后再考虑投稿前 CC 全稿攻击。

## 1. r008 裁决

r008 的 7 个提交路径、manifest 授权集合、除自指 manifest 外的输入/输出 Git blob、唯一 append marker 和 `dis/B.md` 不变均可采纳。但两个科学 gate 必须拒绝。

- v078 与 v077 的 commit blob 完全相同；正文没有实际 quarantine 修改。
- 215-row ledger 中 42 行只是标题；215/215 target 与 source 相同。
- 所有 215 行复用完全相同的三条 evidence paths；177/215 dataset 为 `multiple_or_not_explicit`，unit 与 estimand 都是一个泛化字符串。
- 186 行被自动标 `VALID/RETAIN`、29 行 `QUALIFIED/QUALIFY`，没有 invalid/unresolved/remove。
- validator 的 `SUFFICIENT_FOR_MEASUREMENT_REVISION` 实际只检查 `len(ledger)>=3`，没有执行三类 claim、两数据集、两 detector units、机制闭环或禁用 formal evidence 的 gate。
- validator 默认会重写 gate；Windows CRLF checkout 又改变 bytes/SHA，不能称跨平台只读验收器。

因此：`hygiene_gate=FAIL_CLAIM_QUARANTINE_R008`；`measurement_core_status=INCONCLUSIVE_CORE_EVIDENCE`。这仍是实现/证据失败，不是 measurement 科学核心被证伪。

## 2. 主稿即时风险

v078 虽强调 measurement-only，但摘要、§6.3、表 6、讨论和结论仍把 576 rows、20 nontrivial、68 trivial、554 infeasible、142/144 infeasible、fixed-sequence LTT 与风险保证作为 headline。r006/r007 没有给出可信 formal implementation closure，故这些内容必须从当前证据层隔离。

可保留但需重新绑定真实生成端的候选核心：

1. canonical le90 与 geometry-normalized orientation severity；
2. Core-6 full-evaluator AP50/AP75 干预与经验/理想容忍度；
3. 多单元 NRC/AURC 和固定 size-bin 的非线性诊断上界；
4. 三数据集两真人标注的 label-noise boundary；第三标注员仍未完成；
5. image/tile/mother-scene 统计单位边界与无独立 confirmatory unit。

最强审稿攻击是：历史 AP50 不变由“推到仍位于 IoU50 边界内”的自适应构造诱导；它不是固定剂量的独立机制证据。其次，现有 formal certification 未闭环却占据主稿 headline。

## 3. 建设—攻击—综合

| candidate | 建设候选 | 最强攻击 | 最低判别证据 | kill condition |
|---|---|---|---|---|
| C4-R：orientation intervention measurement | 完整 post-NMS raw 上仅改 theta，用 full evaluator 比较 AP75/AP50，并以 ar-bin survival 解释几何机制 | matched-only、partial GT、自适应边界或 GT-directed 选方向可制造差异 | Core-6 三数据集多 head、八固定剂量、positive/GT-directed/symmetric 三 track、独立 evaluator parity、cluster CI | Core 少于 6；evaluator 不等价；D/S 少于 3/6 支持或任一数据集全反向 |
| C5-R：可复算 measurement protocol | 同一 raw 同时生成 AP、NRC/AURC、角度风险和干预曲线，claim 逐行绑定 row key/脚本/manifest | 只是工具拼装，缺少统一机制或 confirmatory unit | r009 真实 claim ledger 与 v079；所有 headline 绑定生成端 | 隔离 certification 后只剩零散观察，或 r009 机制 fail |

综合：保留 C4-R/C5-R 作为一次性 r009 campaign；永久停止 C2-R/split-FST 方法路线与 RSAR acquisition。r009 不训练 detector，仅在 Core raw 缺失时用 frozen checkpoint/config 重新 full inference。

## 4. r009 gate 与投稿级别

- Core-6 provenance、双 evaluator、dose=0 parity 任一失败：早停，保持 JSTARS plausible/NOT_READY。
- Core-6 的 GT-directed 与 GT-free symmetric 证据、AP75 单调性及 ar-bin survival 达预注册门：`PASS_STRONG_JSTARS_EVIDENCE_R009`，才可称 strong JSTARS evidence-ready。
- 只有在上述通过后，FAIR1M ORCNN 与两个 DOTA clean extension 也全部闭环、覆盖四数据集和三 detector families，才可讨论 TGRS-borderline；仍不能称 TGRS-ready。
- r009 fail 不包装成普适负结果；只删除统一机制/knee claim，保留可复核的 unit-level measurement。

## 5. 决策台账

| item | decision | next |
|---|---|---|
| r008 commit scope/provenance | adopt | 保留历史产物，不修改 |
| r008 hygiene PASS | reject | v079 强制隔离旧 certification headline |
| r008 core SUFFICIENT | reject→inconclusive | 用 r009 同一 raw 生成端重算 |
| 再修 split-FST | reject permanently | 不再进入服务器任务 |
| 新 detector training/RSAR/其它项目下载 | reject | r009 仅允许 frozen inference |
| full-evaluator fixed-dose closure | experiment | 执行 [`sug.md`](sug.md) 的完整 r009 |

唯一服务器报告路径：[`orientbench-c-r009-20260806.md`](server_reports/orientbench-c-r009-20260806.md)。
