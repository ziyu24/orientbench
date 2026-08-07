# OrientBench C 侧 r010 验收与 r011 最终统计修复/联合主线复核

- round: `orientbench-c-r011-20260807`
- scientific snapshot: `c62ea3514e98f76baf557c22a5dd0ef812d84ee0`
- active manuscript: [`orientation_reliability_paper_A_zh_v080.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v080.md)
- r010 report: [`orientbench-c-r010-20260806.md`](server_reports/orientbench-c-r010-20260806.md)
- formal verdict: `FAIL_PROTOCOL_R010`；scientific mechanism remains `INCONCLUSIVE`
- current venue: **strong-JSTARS candidate / JSTARS plausible but not ready；TGRS evidence not reached**
- `cc_recommendation: no`：r010 的失败由提交代码和 CSV 中的直接反例充分裁决；先让服务器完成有界 r011，之后才需要投稿前全稿对抗审查。

## 1. 已确认事实

可保留：六个 Core 单元确实读取了 persistent raw/full GT，自定义 classwise evaluator 生成了 144 条 P/D/S 剂量曲线与 96 条 S 正负分量；原始 full-sample 点曲线继续显示 AP75 比 AP50 更敏感的候选信号。r010 最终没有越级声称 strong mechanism。

必须拒绝：

1. evaluator parity 是 `clean=base` 自比自身；golden 是常量 PASS，不是可执行测试。
2. paired bootstrap 以 weighted TP 数而非 weighted full-GT 数作 recall 分母，并遗漏 GT-only image/class；其 DIOR-R/22 D contrast 均值约 0.203，而 full-sample 点估计仅约 0.095。
3. Holm 未实现；gate 又把 CSV 的 `True` 与小写 `true` 比较，INCONCLUSIVE 是偶然保守 bug。
4. survival 144 行全部 `ar_bin=all`；没有三个冻结 AR bins。S risk/survival 仍完全等于正向 P 分量。
5. D 错误扰动 baseline 未匹配 predictions；risk 固定键应 576 行而实际 557。
6. provenance 的集合关系和 PASS 被硬编码；DIOR prediction image 数小于 split image 数，SODA/FAIR 身份差异未用 split universe/运行记录闭合。
7. baseline 仅六行 AP；ledger 仅一条；manifest 只列两条授权路径且无输入/输出身份。
8. v080 只在参考文献后追加七行，没有整合摘要—贡献—方法—结果—讨论—限制—结论；正文仍称 fixed-dose raw 不完整，并残留相互矛盾的 formal certification 语言。
9. r010 拆成两个提交并原位修改 root append；`git diff --check` 产生大量 CRLF 报错。
10. bootstrap 默认仅 6 CPU workers、survival 单进程；GPU/CPU 日志与利用率不存在，无法证明资源纪律。

因此 `PASS_PROVENANCE_R010`、`PASS_EVALUATOR_R010`、所有 r010 CI/support 和“统计闭环”均 reject。保守的科学状态仍是 INCONCLUSIVE，不是负结果。

## 2. P1+P3 主线同步裁决

当前可采纳的 P3 只有权威 M2/G2_double_prime：`scripts/m2_g2doubleprime_ar21.py` 基于 m069 Core-6、`ar>=2.1`、prediction-side features、D_cal→D_audit 和 1000 次 image-cluster bootstrap；15 个有效 cell×size-bin 中 11 个支持 nonlinear，定位仅为 target-GT calibration/diagnostic upper bound。

旧 `measure_fix_v2` 039/040/Route-C 的 PASS/STABLE-PASS 不得直接进入当前稿：它们使用旧 `ar>=1.6`/旧 matched lineage、400–500 次 instance bootstrap；039 还把 source D_audit 纳入训练，040 的全单元 retained gain 未过预设 0.5，仅排除 DOTA 后升级；真实 TTA raw 不持久且覆盖有限。r011 只在当前 Core-6 lineage 做一次有界 source-D_cal→target-D_audit 复核，不恢复“deployable method”口径。

## 3. 可证伪候选

| candidate | minimum decisive evidence | kill condition |
|---|---|---|
| P1 fixed-dose sensitivity | official-vs-clean evaluator、真实 full-GT paired AP bootstrap、D/S Holm、三 AR-bin fixed-cohort survival | 任一 evaluator 不等价；D/S 少于 3/6；正确 bootstrap 不保留方向 |
| P3 cross-domain diagnostic | 当前 Core-6、ar>=2.1、source 仅 D_cal、target 仅 D_audit、leave-dataset/detector、image-cluster CI | 泄漏；nonlinear 对 size-linear 支持少于 60%；结果仅由单 dataset/family 驱动 |
| joint measure→diagnose→fix paper | P1/P3 数字均绑定生成端，v081 完整重写且禁止旧 formal/伪 deployable claim | 任一 headline 只能追到旧 PASS、报告自述或不可持久化 raw |

## 4. 决策台账

| item | decision | confidence | next |
|---|---|---:|---|
| r010 144 点曲线 | revise/adopt descriptive | medium | r011 独立 evaluator 复核后才能进稿 |
| r010 parity/bootstrap/survival/provenance | reject | 0.99 | r011 从 raw 重算，不修历史文件 |
| r010 INCONCLUSIVE | revise | high | 保留科学保守性，但正式状态为 `FAIL_PROTOCOL_R010` |
| v080 | reject as completed manuscript | high | 新建 v081，参考文献前整合全文 |
| current M2/G2DP | adopt as diagnostic upper bound | medium-high | 保留，不称部署方法 |
| old 039/040/Route-C PASS | reject for current headline | high | r011 当前 lineage 有界复核 |
| detector training/inference/download | reject | high | r011 全部复用现有 raw/features |

r011 是固定剂量机制的最后一次实现修复。若仍不能通过 executable evaluator/bootstrap preflight，则永久删除统一机制 CI claim，停止 r012 式补丁循环，转描述性结果和联合稿其它可靠证据。

唯一服务器报告路径：[`orientbench-c-r011-20260807.md`](server_reports/orientbench-c-r011-20260807.md)。
