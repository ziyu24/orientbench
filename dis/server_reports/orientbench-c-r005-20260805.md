# A1 scene-functional oracle 支配性修复门

- round: `orientbench-c-r005-20260805`
- scientific snapshot: `6955bbc49094a09696c1025e3034f74b74910857`
- execution HEAD: `896d51127ea2ea3574c26f28a370f913e89c8a0c`
- structure gate: `PASS_SCENE_ENVELOPE_VALID`
- score-cause gate: `INCONCLUSIVE_SCORE_CAUSAL_ATTRIBUTION`
- detector fit/predict, diagnostic regressor fit/predict, download, GPU, RSAR read: `0/0, 0/0, 0, 0, 0`

## 1. 核心裁决

新的 scene-functional attainable envelope 通过全部状态与数值支配检查，结构门为 `PASS_SCENE_ENVELOPE_VALID`。
主分母保持 90 行：conservative score lower witness 为 0/90
(0.000000)，加入 target-GT diagnostic witness 的 sensitivity lower 为
3/90 (0.033333)，
selection/protocol-gap upper bound 为 57/90 (0.633333)。
因此 score 原因既未被保守下界证明占多数，也未被上界排除占多数，科学结论是 `INCONCLUSIVE_SCORE_CAUSAL_ATTRIBUTION`。

## 2. r004 反例与 trace

- actual feasible 但 r004 oracle infeasible：22 行
- 其中 practical：12 行
- 其中 primary：2 行
- 1% 首败：144/144
- 首败后存在更高 coverage pointwise pass：105/144
- primary later-pass：25/36
- 主分母原 r004 oracle-limit 且 later-pass：57/57

r004 的 literal fixed-sequence gate 仍是冻结的 `FAIL_SCORE_LIMIT_DOMINANT`；本轮不覆盖它。上述反例说明其 instance oracle
不支配 conditional scene functional，不能把 r004 的 `0/90` 解释为 score 因果下界。

## 3. 支配 envelope

每个 calibration scene 先取最小 endpoint event，再在全部 scene 中按 `(m_s, stable_scene_id)` 排序；对所有 `n=1..N`
计算冻结 HB UCB 并取最小值。144 个 unit-endpoint-alpha 单元均保存 scene 数、zero/all-event scene、chosen n/mean/UCB
和 `delta=0.05/0.01` 敏感性。状态支配违反 0 行，数值支配违反
0 行；vector/scalar HB 一致性失败 0 个。

该 envelope 使用 calibration outcome 并放松 score、fit threshold、coverage grid、1% entry、fixed-sequence 与 practical policy；
它只给可达性下界，不是 inference-available score，也不是新风险控制协议。

## 4. 状态优先归因

primary 144 行互斥分解为：
{"CERTIFIED_PRACTICAL": 1, "SELECTION_PROTOCOL_GAP": 75, "STRUCTURAL_POWER_LIMIT": 44, "TRIVIAL_BUDGET_INFEASIBLE": 23, "TRIVIAL_FORMAL_CERTIFIED": 1}。
`SELECTION_PROTOCOL_GAP` 混合 score ranking、D_fit 到 calibration transfer、coverage grid、序列顺序和 policy class，
不得改称 `SCORE_RANKING_LIMIT`。target-GT diagnostic witness 不并入 conservative lower。

## 5. 最弱环节、置信度与反证条件

最弱环节是 selection/protocol gap 内部不可由现有冻结证据进一步识别：保守 score witness 太弱，而 relaxed upper 仍大于 50%。
对 envelope 支配性与状态分解的置信度为高，因为 r004 身份、1872 trace、六单元 lineage 和数值支配均闭环；
对“score 是否为多数原因”的结论保持不可判定。只有预先冻结、仍使用 target-GT-free score 的独立设计能收紧上下界。

## 6. 合规

本轮未运行 r004 geometry regressor parity；detector 与 diagnostic regressor 的 fit/predict 均为 0，训练、推理、下载、GPU、
RSAR/其它个人项目读取均为 0，证据类型为 `STATIC_CONTROL_FLOW_AUDIT`。CPU 线程预算 39/48（>=80%）；
分组和 JSONL 装载含串行 I/O，未伪报实际利用率。bounded sanitizer 为 `PASS`；旧 A1/r004 和主稿均未修改。
