# OrientBench C 侧 r009 验收与 r010 统计—机制—主稿闭环

- round: `orientbench-c-r010-20260806`
- scientific snapshot: `73f8814b9d0345bfb6b99c1463a61bb01a555f40`
- active manuscript: [`orientation_reliability_paper_A_zh_v079.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v079.md)
- r009 report: [`orientbench-c-r009-20260806.md`](server_reports/orientbench-c-r009-20260806.md)
- r009 formal verdict: `FAIL_PROTOCOL_R009`；mechanism=`INCONCLUSIVE_MECHANISM_R009`
- current venue level: **strong JSTARS 潜力，但尚非 evidence-ready；TGRS 未达到**
- conditional ceiling: r010 Core 严格通过后可称 **strong JSTARS evidence-ready**；三项 extension 也闭环后才是 **TGRS-borderline evidence candidate**，仍不能称 TGRS-ready
- `cc_recommendation: no`：r009 的争议已被三路独立代码/统计/主稿审计以可复核反例裁决；当前最有效动作是让 Luna-high 完成 r010。CC 保留到 r010 后的全稿对抗审查，除非用户明确提前调用。

## 1. r009 裁决

### 可采纳

三个 fixed-dose track 是不同文件，均有 Core-6 × 8 doses 的完整 AP 点估计。15° 时 P、D、S 三轨的 `drop(AP75)-drop(AP50)` 均为 6/6 正值；D 的 AP75 在 6/6 单元随剂量近似单调。这是有价值、值得修复的信号，不是科学核心被证伪。

### 必须拒绝

1. r009 突破精确授权路径并多次追加根记录，触发预注册 global kill。
2. manifest 中 17 个非自身 output 仅 3 个仍与 HEAD 相符，不能证明最终产物身份。
3. bootstrap 实际为 severe-rate 的 500 次、`9000+dose`，不是 seed=`20260806`、1000 次的 dose-15 paired AP contrast。
4. risk/bootstrap/survival 每个 unit 只覆盖一个轮换 track，不是 6×3；S 的 instance-level risk 直接使用 P 正向曲线。
5. survival 以每个 dose 重新匹配的 TP 为分母，存在 survivorship bias，且没有三 AR bins。
6. evaluator 只有同一 K1 路径；golden 是静态 PASS；validator 只查存在性并硬编码通过。
7. baseline 表仍为 36/36 `NOT_RUN_PROVENANCE`；operation counts 互相矛盾。
8. v079 早于最终计算，仍称 fixed-dose raw 不完整；ledger 与 manifest 均过期。

因此拒绝 `PASS_RISK_EVENT_BOOTSTRAP_R009` 与 `PASS_R009_EVIDENCE_CLOSED`。r009 只能作为“描述性点估计 + 待独立复核 raw inventory”的历史输入，不得进入 headline。

## 2. 主稿最致命问题

v079 虽删除了 576/20/68/554/142 和表 6 的主要 certification headline，但隔离并不彻底：仍以当前工具箱/结论口吻残留 LTT/HB/CP 与 formal certification 断言；同时它没有纳入 r009 的固定剂量信号，反而继续写“证据未完成”。因此当前稿件既承受旧 formal 证据未闭环的风险，又没有利用最新、最能抵抗“协议诱导”攻击的结果。

## 3. 可证伪候选

| candidate | 实质差异 | 最低判别实验 | kill condition |
|---|---|---|---|
| C4-R：fixed-dose orientation sensitivity | 在冻结 full post-NMS predictions 上只改角度，用完整 evaluator 重新匹配；D 是 GT-directed 上界，S 是不挑方向的 GT-free falsifier | Core-6、三轨、8 doses；独立 evaluator parity；dose-15 paired image/scene-cluster AP bootstrap；baseline-cohort AR survival | D 或 S 支持少于 3/6；任一 track 无法覆盖三数据集；独立 evaluator 不等价 |
| C5-R：geometry-linked reliability measurement | 把 AP75 的更早下降与固定 baseline TP cohort 的 AR 条件 survival 绑定，而不是从 matched-only 样本推断 | `[2.1,3) / [3,5) / [5,+inf)` 三 bin，15° 下 survival 按 AR 递减，至少 4/6 且覆盖三数据集 | 有效 Core 中少于 4/6 有序，或结果由 dose 后重匹配/幸存者偏差解释 |
| C6-R：recomputable claim chain | 每个正文数字绑定 row key、独立生成端、输入 manifest 与只读 gate；治理只放附录 | v080、真实 ledger、最终 manifest、非硬编码 validator 同时闭环 | 任一 retained headline 只能追到旧报告、`dis/**` 或自报 PASS |

## 4. r010 gate

- `PASS_EVALUATOR_R010`：实际 golden expected 全过；官方/项目原生 evaluator 与 clean-room evaluator 在 Core-6 dose=0 的 AP50/AP75 差均 `<=0.002`；确定性重算与 r009 的 dose0、D15、+15、-15 差均 `<=0.002`。否则修正后同轮重算 144 格；仍失败则早停。
- `PASS_STRONG_JSTARS_EVIDENCE_R010`：D15、S15 各自至少 4/6 的 paired AP contrast 95% CI 下界大于 0、Holm 单侧 `p<0.05`，并且各自覆盖三数据集；D 单调至少 4/6；baseline-cohort AR survival 有序至少 4/6 且覆盖三数据集；provenance、baseline、ledger、v080 同时闭环。
- 点估计一致但 CI/survival 不足：`INCONCLUSIVE_MECHANISM_R010`。D 或 S 少于 3/6：`FAIL_UNIFIED_MECHANISM_R010`。不得降低门槛。
- 只有 Core PASS 后才运行 extension。三项 extension 全部 provenance/evaluator/机制闭环，D/S 各至少 2/3 支持且 DOTA 至少一项支持，才可标 `TGRS_BORDERLINE_EVIDENCE_CANDIDATE`；不等于 TGRS-ready。

## 5. 决策台账

| item | decision | confidence | weakest link / counterevidence | next |
|---|---|---:|---|---|
| r009 AP 点估计 | revise/adopt-descriptive | medium | 尚未独立 evaluator 复核 | r010 确定性 parity 后方可进稿 |
| r009 provenance/evaluator/gate | reject | high | manifest 陈旧、路径越权、validator 硬编码 | 正式记 `FAIL_PROTOCOL_R009` |
| r009 risk/bootstrap/survival | reject | high | track 缺失、seed/reps/estimand 错、S 复用 P | r010 从 raw 重算 |
| v079 quarantine | revise | high | formal 残留且新结果未入稿 | 新建 v080，不改历史稿 |
| detector 重训/下载/借其它项目 | reject | high | 不解决当前统计闭环 | r010 禁止 |
| r010 Core closure | experiment | high | Luna-high 需证明 evaluator 与 raw identity | 执行 [`sug.md`](sug.md) |

唯一服务器报告路径：[`orientbench-c-r010-20260806.md`](server_reports/orientbench-c-r010-20260806.md)。
