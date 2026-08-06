# OrientBench C 侧 r005 裁决与 r006 split-FST 发展门

- round: `orientbench-c-r006-20260805`
- scientific snapshot: `60142448ff1f461531ad1eb2cd0c17785e782350`
- evidence cutoff: `2026-08-05`
- active manuscript: [`orientation_reliability_paper_A_zh_v077.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md)
- r005 server report: [`orientbench-c-r005-20260805.md`](server_reports/orientbench-c-r005-20260805.md)
- 当前科学状态: A=`A_MEASUREMENT_ONLY`；原 A6=`NO_ELIGIBLE_CONFIRMATORY_UNIT_FROZEN`；B=`RETIRED_FAIL_CANDIDATE_GATE`；r005 structure=`PASS_SCENE_ENVELOPE_VALID`；score cause=`INCONCLUSIVE_SCORE_CAUSAL_ATTRIBUTION`；C2-R=`EXPERIMENT_NOT_CONTRIBUTION`；submission=`NOT_READY`。
- 当前投稿上限: **strong JSTARS；TGRS high-risk conditional route，尚不 credible/ready**。
- `cc_recommendation: no`

CC 已完成 r001。r005 的剩余分歧只能由控错证明、模拟和冻结后的前瞻单元收紧；再次文字审稿不会缩小 score 因果区间。

## 1. 当前论文对象

本文不是新 detector，也不是全检测输出的部署保证。当前可守对象是：在旋转检测 prediction 已与 GT 匹配、且场景至少含一个 eligible matched instance 的条件下，测量 orientation error、geometry identifiability、inference-available score、scene-level finite-sample risk、coverage 和 practical feasibility 的关系。

r005 把一个错误因果故事修正为可证边界：`142/144 infeasible` 是冻结协议的状态，不等于“现有 score 导致 142/144 失败”；但修正归因本身还不是方法贡献。论文只有在标准风险控制工具能形成有广度的 target-GT-free practical 结果，并在新域前瞻复现后，才可能走 TGRS。

## 2. r005 独立裁决

结果提交为 `60142448ff1f461531ad1eb2cd0c17785e782350`，parent/execution HEAD 为 `896d51127ea2ea3574c26f28a370f913e89c8a0c`，scientific snapshot 为 `6955bbc49094a09696c1025e3034f74b74910857`。

### 2.1 provenance 与执行

- 结果提交的 9 个路径与 `sug.md`、manifest 授权集合完全一致；旧 A1/r003/r004、主稿和 `dis/B.md` 均未变化，监督日志只追加一条。
- manifest 的 8 个非自身输出在结果提交中的 bytes、SHA-256、Git blob 全部一致；28 个本机可访问输入一致。另 18 个服务器 raw/universe 输入本机不能重哈希，但与既有持久化 inventory 18/18 对上。
- 576 identity、144 envelope、1872=`144×13` coverage trace 均唯一完整；JSON/CSV schema 和主计数闭环。
- 未见 detector 或 diagnostic regressor fit/predict、训练、推理、下载、GPU、RSAR 或其它个人项目读取。该结论是源码静态控制流审计，不是系统调用级遥测。

### 2.2 采纳的数学结论

对每个 calibration scene 取最小 endpoint event `m_s`，再对全部 `n=1..N` 选择最小的 n 个 `m_s` 并最小化冻结 HB UCB。对任一实际 selection，在相同非空 scene 数 n 下，该构造的 scene-loss mean 不大于实际 mean；HB UCB 对 mean 单调，因此 relaxed envelope 必不劣于实际 selection。

独立精确整数重算确认：

- 72/72 个 `unit×endpoint×delta` envelope 的最优点均为全部 zero-risk scenes，chosen n、UCB 与 feasibility 0 个错误；最大舍入差 `4.98e-7`。
- 22 个 actual-feasible 行（其中 practical 12、primary 2）均被 envelope 状态和数值支配；最小 UCB margin 为 `0.004105`。
- primary 144 的状态优先分区为：1 certified practical、75 selection/protocol gap、44 structural、23 trivial infeasible、1 trivial formal。
- 主分母 90 行为 33 structural、57 selection/protocol gap；score 保守下界 `0/90`，加入 target-GT diagnostic witness 为 `3/90`，上界 `57/90`。因此 `INCONCLUSIVE_SCORE_CAUSAL_ATTRIBUTION` 必须采纳。

r005 script 有一个不改变本轮结果的加固点：vector HB 用 `ceil(n*float_mean)` 恢复整数事件数，极少数非零 k 可因浮点上翻一位；当前所有最优点 k=0，精确整数重算确认 gate 不变。历史 r005 文件不修改；r006 新实现直接保留累计整数 k 并全候选交叉验证。

## 3. 三层证据不能混写

| 层次 | 结果 | 合法解释 |
|---|---|---|
| formal r004/A1 | 主风险 `142/144` infeasible；literal gate=`FAIL_SCORE_LIMIT_DOMINANT` | 只描述冻结 score/grid/1%-entry/fixed-sequence 程序状态，不是原因 |
| any-grid diagnostic | 1% 首败 `144/144`；之后 pointwise pass `105/144`；primary `25/36`；主分母 oracle-limit `57/57` later-pass | 证明结论对序列起点敏感；没有多重检验控制，不能称认证 |
| r005 relaxed envelope | 主分母 33 structural、57 selection/protocol gap | 33 行在 scene-count 下硬不可达；57 行在完全 target-aware、放松 score/grid/sequence/practical 后存在形式 headroom；不证明 score、部署或 practical |

`90` 行不是 90 个独立科学证据，而是 30 个 `unit×alpha` 情境各复制三个 score：真实情境分解为 11/30 structural、19/30 gap。diagnostic `3/90` 只来自同一个 `C × relative_0.5_r_fit` 情境。论文不得把行比例写成跨任务 prevalence。

r005 envelope 通过“每个 scene 选一个 GT 已知安全实例”取得最小 UCB，并未约束 `≥10%` scene rate、`≥10%` instance coverage 和 count `≥100`。它是因果审计用 relaxed lower envelope，不是 selector 或新 protocol。

## 4. novelty 约束与 TGRS 最强攻击

[Learn then Test 官方作者版](https://people.eecs.berkeley.edu/~angelopoulos/publications/downloads/ltt.pdf)已经把风险控制写成 multiple testing，并明确包含 fixed-sequence、Bonferroni 和用额外 split 学习检验图/顺序的 split fixed-sequence testing（核查于 `2026-08-05`；[arXiv 入口](https://arxiv.org/abs/2110.01052)）。因此 r006 的 D_fit-learned ordering 是标准 LTT 工具，不能申报方法首创。

可守增量只能是：OBB orientation、scene/tile exchangeable unit、coverage-dependent effective scene power、matched-only/full-output 边界，以及在遥感旋转检测上的系统反例和前瞻验证。当前 TGRS 攻击仍然成立：

1. matched-only estimand 排除 FP、FN 和真正空场景；不是 deployment guarantee。
2. 现有负结果混合 power、order、policy 和 score，score 因果仍未识别。
3. AP@0.5 零下降部分受 IoU 边界内扰动构造影响；固定剂量 full evaluator 仍不完整。
4. 原 A6 无合格前瞻单元、第三标注者/仲裁未完成。
5. split-FST 本身不是 novelty；若只能靠换检验顺序得到少数行，最多是协议修补。

## 5. 可证伪候选

| 候选 | 最近一手工作与实质差异 | 最低判别实验 | 杀死条件 |
|---|---|---|---|
| C2-R：power-aware scene-level orientation LTT | 最近工具基线是 [Learn then Test](https://arxiv.org/abs/2110.01052)；实质差异不在 split-FST，而在 OBB orientation 的 scene-power measurement、tile/mother-scene 边界和 score/policy 反例 | r006 冻结标准 split-FST：D_fit 只学顺序，D_cal 只检验，D_audit 只描述；理论 FWER + 模拟通过，且 A–F 发展集至少 3/6 units、覆盖至少 2/3 datasets 出现 nontrivial target-GT-free certified-practical 且 audit risk 方向一致 | 需要 D_cal/D_audit outcome 调序；FWER 超标；无 practical headroom；或 breadth 未达 3 units/2 datasets |
| C3：RSAR × S2ANet 前瞻验证 | [RSAR 官方实现](https://github.com/zhasion/RSAR/tree/6594e685de1e592bd66bff5451763380d0d36c53)提供未参与当前设计的新 SAR 域；差异是冻结协议的一次性外部验证，不是多一张表 | C2-R protocol/code hash 全部冻结后，先做 acquisition/provenance，再一次性 raw→final、固定剂量、NRC、conditional/full-output | 资产身份、严格载入、split/mother-scene、持久化失败，或前瞻方向反转 |
| C1-R：matched-only/full-output bridge | [Copley et al.](https://proceedings.mlr.press/v230/copley24a.html)已在航空/卫星检测使用 conformal；剩余差异是 orientation conditional risk 与含 FP/FN/空场景 joint risk 的显式桥接 | 六单元与 RSAR 同时报两种 estimand，并检查方向一致性 | 方向冲突，或主结论只能靠排除 FP/FN/空场景成立 |

## 6. 决策台账

| 决策 | 状态 | 理由 | 下一步 |
|---|---|---|---|
| r005 provenance、envelope 支配性、状态分区 | adopt | 提交、manifest、数学与独立整数重算闭环 | 作为因果审计证据保留 |
| `INCONCLUSIVE_SCORE_CAUSAL_ATTRIBUTION` | adopt | score 下界 0，上界 57/90，跨越 50%；且行非独立 | 禁止正反两种 score 主因 headline |
| 把 57/90 称 practical 或 deployable headroom | reject | relaxed envelope 未约束 coverage/count，且直接使用 calibration outcome | r006 单列 zero-event practical witness 与实际 target-free split-FST |
| 把 split-FST 称 OrientBench 新方法 | reject | LTT 一手论文已有 split fixed-sequence | 只作标准、受控 protocol baseline |
| 立即下载/推理 RSAR | reject-now | 新 protocol 尚未冻结；先看外部标签/结果会破坏最后前瞻门 | r006 通过后开独立 acquisition round |
| 修改历史 r005 script | reject | 会破坏 manifest 与结果提交身份 | r006 新脚本用精确整数实现并登记 hardening check |
| 再次调用 CC | reject-now | 当前由证明、模拟和机器 gate 裁决 | 前瞻包冻结或投稿前再审 |

## 7. r006 与停止条件

r006 见 [`sug.md`](sug.md)。primary procedure 固定为 score-family 内的 LTT split-FST：阈值和候选顺序只从 D_fit 生成，再在 D_cal 按该顺序 fixed-sequence；Holm 只作预注册 sensitivity，原 1% ascending sequence 作历史 baseline。A–F 明确是已暴露的 retrospective development evidence，不能再称 confirmatory。

- validity gate：理论 FWER 前提闭环，预注册 global-null 模拟的 95% CP upper 不超过 `0.105`，且无 D_cal/audit 调序。
- development breadth gate：primary endpoint 下至少 3/6 units、至少 2/3 datasets 有 nontrivial target-GT-free formal certification，同时满足原 audit practical thresholds，且 audit empirical conditional risk 不高于 alpha。
- fail：validity 不通过、breadth 不足，或只有 target-GT diagnostic/near-trivial 结果。
- pass 也只允许随后冻结协议并获取 RSAR；不直接宣称 TGRS ready。

置信度：r005 provenance `0.99`；envelope dominance `0.98`；score 因果不确定 `0.97`；C2-R 能达到 r006 breadth `0.58`。最弱环节是新顺序受 A–F 结果启发且标准 LTT 已有，只能靠冻结后的 RSAR 一次性验证消除事后设计与 novelty 风险。
