# OrientBench C 侧 r006 裁决与 r007 有效性修复门

- round: `orientbench-c-r007-20260805`
- scientific snapshot: `8e93291b75b34ddfb7b74a7592e1573407603f88`
- evidence cutoff: `2026-08-05`
- active manuscript: [`orientation_reliability_paper_A_zh_v077.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md)
- r006 report: [`orientbench-c-r006-20260805.md`](server_reports/orientbench-c-r006-20260805.md)
- current state: r006 provenance=`PASS`；reported structure pass=`REJECTED`；C structure=`FAIL_SPLIT_FST_VALIDITY_IMPLEMENTATION`；formal development=`INCONCLUSIVE_PENDING_R007`；descriptive breadth=`3 units / 1 dataset only`；submission=`NOT_READY`
- venue ceiling: **strong JSTARS；TGRS/ISPRS JPRS 尚不 credible/ready**
- `cc_recommendation: no`：当前分歧由确定代码反例和最小重算裁决，不需要再次意见审稿。

## 1. 结论先行

r006 不能采纳 `PASS_SPLIT_FST_VALIDITY`。其来源链、提交范围、主 frontier 行数以及“合格行只来自 DIOR-R”可信，但两个预注册结构检查没有被正确实现，且错误 exact p-value 被用于 FWER simulation。因此按原 gate 必须记为 validity fail；development 正式状态随之为 inconclusive，而不是正式 breadth fail。

即便如此，使用正确冻结 bounded-loss `hb_pvalue` 生成的描述性 frontier 仍只有 14 个 qualifying rows、12 个唯一 `unit×endpoint×alpha` context，覆盖 A/B/C 和唯一数据集 DIOR-R。FAIR1M/SODA-A 的 nominal pass 均为 `alpha>=r_fit` 的 trivial guarantee。修复后跨数据集广度仍失败的概率高，当前禁止进入 RSAR acquisition。

## 2. r006 证据审计

### 2.1 采纳的 provenance 与数字

- 服务器结果提交：`8e93291b75b34ddfb7b74a7592e1573407603f88`；execution HEAD：`7d067f44240b8790f5bc3cb346d6f866d09ce97e`。
- 9 个提交路径与 manifest 授权集合一致；8 个非自指输出的 commit bytes、size、SHA-256 与 Git blob 闭环；`dis/B.md` 未变化。
- manifest 的 48 个输入中，30 个仓库内输入可独立核对且一致；18 个服务器 raw 资产本机不可重哈希，是 provenance 最弱环节。
- 7,488=`576×13` order rows、2,304 frontier rows、108 simulation rows、144 witness rows，唯一键完整。
- primary 描述性合格行 14，唯一 context 12；units=`A,B,C`，dataset=`DIOR-R`。这是 3/6 units 但仅 1/3 datasets，未达到 2 datasets。

### 2.2 拒绝 reported structure pass 的确定反例

1. [`audit_a1_split_fst_r006.py`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a1_split_fst_r006.py) 的 `hb_p_exact`/`pvec_exact` 缺少单侧条件 `k/n >= alpha => p=1`。在 7,488 行中，5,242 行满足 `k/n>=alpha` 却得到 exact `<1`，其中 4,373 行错误达到 `<=0.1`，会把高风险观测误写成“安全可拒绝”。
2. 同一脚本的 outcome-taint 检查是 `hash(serial)==hash(serial)`，恒真；没有置换 D_cal/D_audit outcome，576/576 pass 不是执行证据。
3. exact 对照有 6,762/7,488 mismatch，但 `valid` 条件没有包含该检查。
4. 108 个 FWER simulation 调用错误的 vector exact p-value；其 CP upper 数值虽可重算吻合，测量的却不是合法单侧程序，不能支撑 super-uniform 或 strong FWER sanity。

主 frontier 使用冻结且含正确单侧 guard 的 bounded-loss scalar `M.hb_pvalue`，所以 14 行的描述性方向大概率不受上述 bug 影响；但正式 gate 必须经 r007 重新裁决。

## 3. 论文含义与最强审稿攻击

split-FST/LTT 是已有统计工具，不是 OrientBench novelty。现有数据最多支持：“在 OBB matched-orientation 的场景级风险中，合法非平凡 target-free certification 可能存在，但目前只在 DIOR-R 出现；固定绝对风险预算还会在低 base-risk 数据上制造 nominal/trivial pass。”

最强攻击仍是：

- matched-only estimand 排除了 FP、FN 与真空场景，不是 full-output deployment guarantee；
- A–F 已暴露，全部是 retrospective protocol development；
- 单数据集成功不足以形成 TGRS 级普适方法贡献；
- 统计工具已有，遥感实质增量必须来自 orientation-specific measurement、失败机制与可复核反例，而不能来自换检验顺序。

主稿在 r007 前不得把 r004 的 `142/144 infeasible` 当作当前协议总括，也不得把 r006 的 reported structure pass 写入正文。最终应分层保留历史 literal gate 与修正后的协议结果。

## 4. 可证伪候选

| candidate | nearest primary work / material delta | minimum decisive test | kill condition |
|---|---|---|---|
| C2-R：OBB scene-level split-FST 失败边界 | 最近工具基线是 [Learn then Test](https://arxiv.org/abs/2110.01052)；差异只可能是 OBB 场景功效、matched/full-output 边界与跨数据域反例 | r007 修正单侧 exact HB、真实 outcome permutation、split disjoint 与 108 个 FWER simulation；再按原 3 units/2 datasets 门重算 | validity 任一失败；或 validity pass 后仍只覆盖 DIOR-R。后一情况终止其 TGRS 方法贡献与 RSAR acquisition |
| C4：measurement + protocol failure analysis | LTT 已给通用风险控制；实质差异必须是遥感旋转检测中 base-risk、scene power、coverage 和 trivial certification 的系统关系 | r007 后做一次主稿 claim-to-evidence 对账，所有 headline 同时报 base risk、相对 alpha、有效 scene 数、practical coverage 与 dataset 去重 | 删除标准 LTT 后没有 orientation-specific finding；或结论只剩单数据集案例和治理流程 |

## 5. 决策台账

| item | decision | evidence / reason | next |
|---|---|---|---|
| r006 commit scope、manifest、row counts、14-row descriptive breadth | adopt | commit 与 manifest 闭环；CSV 独立计数一致 | 作为 r007 输入保留，不修改历史文件 |
| `PASS_SPLIT_FST_VALIDITY` | reject | one-sided exact p-value 错误、FWER simulation 调错程序、taint 恒真 | 执行 r007 最小修复审计 |
| `FAIL_NO_BROAD_TARGET_FREE_DEVELOPMENT` 作为正式 gate | revise | 按预注册逻辑 validity 非 pass 时 development 应为 inconclusive | r007 validity pass 后再判 breadth；描述性 1-dataset failure 保留 |
| 立即下载 RSAR | reject | r006 早停与描述性 breadth 都未达门；此时下载是 post-hoc rescue | r007 后若仍 1 dataset，关闭 C2-R acquisition |
| 修改 r006 历史 script/report | reject | 破坏 provenance | r007 只新增修复资产 |
| 再调用 CC | reject-now | 已有确定代码反例，意见不会改变 gate | 投稿前全稿审查再考虑 |

## 6. r007 gate 与置信度

r007 只修复有效性实现，不新增数据、不改主稿、不扩矩阵。必须做到：合法单侧 scalar/vector exact HB 全候选零 mismatch；真实改变 D_cal/D_audit outcome 后 order bytes 不变；fit/cal/audit scene ID 交集为零；正确程序下 108 个 FWER CP95 upper 全部 `<=0.105`。

若结构通过但仍只有 DIOR-R，则 C2-R 按预注册 kill，停止 RSAR；转向 measurement-only + protocol failure analysis 的主稿对账。当前置信度：r006 structure fail `0.999`；14-row/DIOR-R-only 描述性事实 `0.99`；修复后 breadth 仍 fail `0.95`；TGRS 当前不 ready `0.97`。最弱环节是 18 个服务器 raw 输入不能在本机重哈希，以及尚无独立前瞻域。
