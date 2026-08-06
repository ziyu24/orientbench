# OrientBench C 侧 r007 验收与 r008 裁决

- round: `orientbench-c-r008-20260806`
- scientific snapshot: `426d47855eb91d5af947e8bdf9e06d035a95ebf0`
- evidence cutoff: `2026-08-06`
- active manuscript: [`orientation_reliability_paper_A_zh_v077.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md)
- r007 report: [`orientbench-c-r007-20260805.md`](server_reports/orientbench-c-r007-20260805.md)
- formal state: structure=`FAIL_SPLIT_FST_VALIDITY_R007`; development=`INCONCLUSIVE_DEVELOPMENT_R007`; C2-R method route=`KILLED`; RSAR=`FORBIDDEN`; submission=`NOT_READY`
- innovation potential / venue ceiling: **strong JSTARS；TGRS-borderline only conditionally**
- current evidence maturity: **JSTARS plausible, NOT_READY；TGRS/ISPRS JPRS high-risk**
- `cc_recommendation: no`：当前裁决由可定位的实现反例决定；再做意见审稿不能修复证据。投稿前全稿审查时再考虑 CC。

## 1. 结论

r007 不能采纳为有效的 split-FST 科学检验。服务器正确报告了 formal gate fail，但其 108/108 FWER fail、96 个 taint mismatch 和 2866 个 frontier parity mismatch 主要由新审计器自身错误产生，不能解释成统计协议、理论或科学假设被证伪。

可采纳的 r007 证据限于：提交路径与大部分已登记产物身份闭合；A–F 的 fit/calibration/audit 三组交集为 0；主 frontier 仍给出 14 rows、12 个唯一 context、A/B/C、DIOR-R-only 的描述性线索。后者不是 formal certification、prevalence、跨数据集广度或 deployment guarantee。

C2-R 不再作为 TGRS 方法贡献继续：即使修复审计器，LTT/fixed-sequence/Holm 仍是标准工具；现有非平凡线索又仅覆盖一个数据集。停止 RSAR acquisition，不以新增数据事后救援。项目回到 orientation-specific measurement 与协议失效分析主线。

## 2. r007 证据裁决

| item | decision | evidence | implication |
|---|---|---|---|
| 10 条 commit 路径与授权集合 | adopt | r007 commit 路径闭合；`dis/B.md` blob 未变 | 提交范围合规 |
| 8 个 manifest 非自指输出 | adopt-with-limit | commit bytes/size/SHA-256/blob 一致 | 只证明已登记产物身份 |
| 完整 provenance | reject | append 后根记录未作为最终 output 登记；服务器原始资产本机不可复哈希 | 不能称全链闭合 |
| operation count `12/12` | reject | 根记录追加了两条 r007 记录，至少完整执行两次，commit 级至少 `24/24` | 单次计数不是本轮总计 |
| exact scalar/vector gate | reject | family 行比较的是旧 bounded scalar 与 integer exact；gate 又读取不存在的 `match` 字段 | reported failures=0 无效 |
| boundary test | reject | 混合 CSV schema 丢弃 boundary 专属字段 | 无可复核证据 |
| 108/108 split-FST/Holm fail | reject-as-science | vector 对 `k/n>=alpha` 返回 0 而非 1；`k=0` 产生 NaN | 是实现失败，不是 FWER 反例 |
| 96/1152 taint mismatch | reject-as-science | 扰动排序误用循环残留 `cov`，且未执行预注册三类扰动 | 不证明 outcome leakage |
| 2866 frontier mismatch | reject-as-science | 比较旧 schema 缺失字段并使用 `bool("False")` | 不证明 primary 结果变化 |
| split disjoint | adopt | A–F 三组两两交集均为 0 | split 前提局部通过 |
| 14 rows / 12 contexts / DIOR-R-only | revise | 主 bounded-loss 路径未使用上述坏 vector；仅能作描述性线索 | 禁止 formal/breadth/prevalence 表述 |

## 3. 可定位的决定性反例

1. [`audit_a1_split_fst_r007.py`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a1_split_fst_r007.py) 的 scalar `hb_p_exact` 已含正确单侧 guard；vector `pvec_exact` 却令 `r>=alpha` 的 divergence 保持 `inf`，随后得到 p=0，而非 p=1；`r=0` 还会进入 `0*log(0)`。
2. 7,488 个 family 行实际比较不同 estimand，只有 5,968 行标为 match；gate 的 `failures=0` 来自错误字段读取。
3. 864 个 boundary row 在内存中生成，但写入 CSV 时沿用 family schema，关键字段全部丢失。
4. taint 的 perturbed 排序使用外层残留常量而非候选自己的 coverage，96 个 mismatch 因而不能归因于数据泄漏。
5. parity 把 CSV 字符串 `"False"` 当作真值，并比较新表不存在的旧字段，2866 个 mismatch 没有科学含义。

置信度：高。最弱环节是 18 个服务器原始输入无法在本机重哈希；但上述拒绝均由仓库代码、表结构和提交记录直接决定，不依赖这些原始输入。

## 4. 候选、最强攻击与 kill condition

| candidate | 实质差异 | 最强攻击 | 最低判别证据 | kill condition / state |
|---|---|---|---|---|
| C2-R：OBB split-FST 方法贡献 | OBB scene risk 与 matched/full-output 边界 | 标准统计工具非 novelty；formal 实现连续不可信；描述性正例仅 DIOR-R | 正确 reference unit test 只能确认复现性，不能创造 novelty | **killed**；不恢复、不启动 RSAR |
| C4：orientation measurement + protocol failure analysis | 几何归一化风险、AP 阈值敏感性、scene-unit 纠正、人工标注边界的组合证据 | 删除 certification 后可能只剩零散观察；matched-only 部署外推过强 | r008 逐条 claim-to-generation-source 对账和保守主稿副本 | 若删掉 certification 后不能形成完整 orientation-specific 论证，降为技术报告/工具箱 |

## 5. 期刊级别：创新潜力与当前成熟度分开

- **创新潜力/期刊上限：strong JSTARS。** r007 淘汰的是 C2-R/LTT 方法副线，没有直接证伪原有 OBB measurement 组合创新；TGRS-borderline 只能作为满足多数据集、多架构、完整机制与部署边界后的条件上限。
- **当前证据成熟度：JSTARS plausible、NOT_READY；TGRS/ISPRS JPRS 高风险。** 现阶段没有可信的新方法贡献；标准 LTT 不能算首创，单数据集探索线索也不足以支撑广泛遥感结论。
- 若 r008 显示核心价值主要依赖无效 certification，期刊上限需再降，优先技术报告或工具型产物。

## 6. 下一步与决策台账

下一轮不是扩实验，也不是第三次修同一统计门，而是 r008 主稿 claim 隔离：从 v077 生成保守 v078，建立摘要—贡献—结果—局限—结论的 claim ledger；撤掉 r006/r007 formal pass、FWER、taint、parity 与 certification headline；保留内容逐项绑定数字生成端。r008 不训练、不推理、不下载、不改历史证据。

| decision | reason | next gate |
|---|---|---|
| r007 formal result 不采纳为科学结论 | 审计器违反 r007 契约 | 在主稿中隔离 |
| 不再修复 C2-R 以争 TGRS 方法线 | 修对标准工具也不构成 novelty；只有一数据集描述性广度 | kill |
| 不下载 RSAR | 会形成 post-hoc rescue，且不解决 novelty | forbidden |
| 保留 measurement-only 主线 | 仍可能有 OBB-specific 测量与边界价值 | r008 claim reconciliation |
| 当前不调用 CC | 无待意见裁决的不确定代码问题 | 投稿前全稿审查再评估 |

r008 gate 只判断 claim 隔离是否完整，不宣称论文已达到 TGRS。服务器唯一报告路径为 [`orientbench-c-r008-20260806.md`](server_reports/orientbench-c-r008-20260806.md)。
