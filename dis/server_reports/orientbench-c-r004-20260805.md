# A1 不可行性的功效--分数归因门

- round: `orientbench-c-r004-20260805`
- scientific snapshot: `cb0a259f81d9d0cd3af27f514a9e94c75ddf9cbd`
- execution HEAD: `2ad7e0111595607983f749099c26fe6e9fdfeb3c`
- final gate: `FAIL_SCORE_LIMIT_DOMINANT`
- training / inference / download / GPU: `0 / 0 / 0 / 0`

## 1. 决策结论

冻结协议下，主分母为 geometry-normalized severe endpoint、三个 target-GT-free score、nontrivial 且现有表 infeasible 的行。
`SCORE_RANKING_LIMIT` 为 0 / 90 = 0.000000；主门为 `FAIL_SCORE_LIMIT_DOMINANT`。
因此，只有当该比例严格超过 50% 时，才能保留“现有可部署分数是多数不可认证的主因”。当前结论按本门实际比例执行，
不修改 alpha、coverage grid、split、score direction 或原 A1/A6 结果。该旧归因不能保留：主分母中 33 行是
`STRUCTURAL_POWER_LIMIT`，57 行是 `ORACLE_DATA_OR_GRID_LIMIT`，0 行是 `SCORE_RANKING_LIMIT`。

## 2. 576 行 parity 与 lineage

- identity rows: 576 existing / 576 rebuilt
- duplicate / missing / extra: 0 / 0 / 0
- compared-field mismatches: 0
- parity: `PASS`
- six-unit lineage: `PASS`

| unit | matched rows | ar>=2.1 eligible | calibration scenes | audit scenes | matched SHA-256 | universe SHA-256 |
|---|---:|---:|---:|---:|---|---|
| A | 87224 | 49502 | 1794 | 3494 | `00e554fbc45d` | `3f1d2ef764c3` |
| B | 95169 | 54297 | 1870 | 3641 | `e1772d642990` | `644ccaa92298` |
| C | 94961 | 53671 | 1877 | 3690 | `91d4b372e534` | `52c04690d415` |
| D | 54768 | 31801 | 646 | 1221 | `fe2c0b3690e1` | `5cec906c6014` |
| E | 309218 | 197529 | 1858 | 4076 | `337470223fae` | `75f874fff653` |
| F | 376754 | 235428 | 1886 | 4120 | `dd7f37b067a5` | `0ce7cc5f4d56` |

## 3. 互斥归因

| attribution | primary 144 | primary target-GT-free 108 | diagnostic upper bound 36 |
|---|---:|---:|---:|
| `ORACLE_DATA_OR_GRID_LIMIT` | 76 | 57 | 19 |
| `STRUCTURAL_POWER_LIMIT` | 44 | 33 | 11 |
| `TRIVIAL_BUDGET` | 24 | 18 | 6 |

全部 576 行的互斥归因见 failure-attribution 表；power envelope 给出 `n_max` 及零损失 HB/CP UCB，oracle 表给出
fit threshold、calibration fixed-sequence、首失败点和 chosen coverage。主门只使用 `delta=0.1`；`delta=0.05/0.01` 仅为敏感性。

## 4. 对 142/144 的正确改写

原“主风险 142/144 infeasible”是状态计数，不是原因计数。主风险 144 行的互斥分解为：
{"ORACLE_DATA_OR_GRID_LIMIT": 76, "STRUCTURAL_POWER_LIMIT": 44, "TRIVIAL_BUDGET": 24}。
原状态层仍是 142 行 infeasible、1 行 nontrivial practical、另 1 行 trivial formal certification；本轮不覆盖这些状态。
由于冻结 oracle 是 instance oracle，而正式风险是 conditional scene functional，oracle 在 1% 起始 coverage 的首失败会关闭后续序列，
所以按预注册顺序得到的 data/grid attribution 不是“oracle 在所有意义上劣于实际 score”，而是该 oracle 与 scene estimand/grid 的边界。
target-GT upper bound 单独作为 diagnostic headroom，不进入 target-GT-free 多数门。trivial budget 不算方法成功，
zero-loss 下也过不了的行归于结构性功效，不归于 score；oracle 仍过不了的行归于 data/grid boundary。

## 5. 最弱环节、置信度与反证条件

最弱环节是有限 calibration scene 数与冻结 fixed-sequence/grid 的联合功效，而不是 GPU 或训练质量。
本轮对“当前冻结证据的归因”置信度为高，条件是六单元 lineage 和 576 行 parity 均通过；它不是 full-output deployment guarantee。
若未来在不改协议的更大独立 scene universe 上，zero-loss envelope 明显下降且 target-GT-free score 的 oracle gap 消失，
则可反证当前功效/排序占比；该检验需要 C 另行冻结资产与 acquisition contract，本轮不授权获取。

## 6. 合规

计算只读取既有六单元持久化 matched/universe 原物；训练、推理、下载、GPU 和 RSAR 读取均为 0。
CPU 并行线程预算为 39/48（>=80%）；原物 JSONL 装载与 fixed-sequence 循环含串行 I/O，未伪报利用率。
共享输出 sanitizer 为 `PASS`。旧 A1/A6 表、主稿、冻结协议和 r003 输出均未重写。
r003 审计源代码已移除服务器绝对 dataset 路径，并将运行计数证据标为 `STATIC_CONTROL_FLOW_AUDIT`；历史 r003 产物保持不变。
