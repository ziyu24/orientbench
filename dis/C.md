# OrientBench C 侧 r004 裁决与 r005 支配性修复门

- round: `orientbench-c-r005-20260805`
- scientific snapshot: `6955bbc49094a09696c1025e3034f74b74910857`
- evidence cutoff: `2026-08-05`
- active manuscript: [`orientation_reliability_paper_A_zh_v077.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md)
- evidence index: 本文件；r004 服务器原报告为 [`orientbench-c-r004-20260805.md`](server_reports/orientbench-c-r004-20260805.md)
- 当前科学状态: A=`A_MEASUREMENT_ONLY`；原 A6=`NO_ELIGIBLE_CONFIRMATORY_UNIT_FROZEN`；B=`RETIRED_FAIL_CANDIDATE_GATE`；r004 程序门=`FAIL_SCORE_LIMIT_DOMINANT_LITERAL`；r004 因果归因=`INCONCLUSIVE_ORACLE_NOT_DOMINATING`；submission=`NOT_READY`。
- 当前投稿上限: **strong JSTARS；TGRS high-risk borderline，尚不 credible/ready**。
- `cc_recommendation: no`

CC 已完成 r001。当前争议已由代码反例和可复算统计门定位；再次文字审稿不能替代 r005 的支配性检验。等 power-aware 协议与前瞻包冻结后，投稿前再考虑 CC。

## 1. 本文实际在讲什么

本文不是新 detector，也不是对所有检测输出的部署保证。当前可守对象是：在旋转目标检测已经与 GT 匹配、且场景至少含一个 eligible matched instance 的条件下，把朝向误差、几何可辨识性、推理时可用 score、scene-level 有限样本风险界和 practical coverage 放在同一可复算协议中，测量哪些 orientation reliability claim 能或不能被认证。

负结果可发表的前提不是“失败很多”，而是失败边界能被严格定位、可复算、并改变方法设计。r004 证明现有 `142/144 infeasible` 只是状态计数，不能直接写成“现有分数质量导致 142/144 失败”；但 r004 尚未给出有效因果分解。论文潜在贡献应修订为 **power-aware scene-level selective certification 的测量与边界**，不能把当前 `0/90` 包装成分数没有 headroom。

## 2. r004 独立裁决

服务器结果提交为 `6955bbc49094a09696c1025e3034f74b74910857`，执行基线为 `2ad7e0111595607983f749099c26fe6e9fdfeb3c`，scientific snapshot 为 `cb0a259f81d9d0cd3af27f514a9e94c75ddf9cbd`。

### 2.1 可以采纳的证据

- 提交相对 parent 只改变 10 个 r004 授权路径；旧 A1/A6、r003 输出和 `dis/B.md` 均未变化。
- 576/576 identity parity，duplicate/missing/extra/field mismatch 均为 0；六单元 lineage 与 reproduction hash 通过。
- 9 个非自引用输出的 bytes、SHA-256 与 Git blob 和结果提交一致；36 个输入唯一。18 个本机可得 tracked 输入可直接复核，其余 18 个服务器原物身份与 r002 已登记 inventory 交叉一致。
- zero-loss HB/CP、三档 delta sensitivity、144 个结构性功效判定和预注册 attribution 代码的字面算术成立。
- r003 源码中的服务器绝对路径已移除，旧 r003 产物没有重跑或改写。

### 2.2 不能采纳的 headline 解释

r004 的 `SCORE_RANKING_LIMIT=0/90` 只是冻结实现的字面输出，不是可信因果结论：

1. 144 个独立 `unit × endpoint × alpha` oracle 全部在 `coverage=0.01` 首点失败，故全部后续点被 fixed-sequence 关闭；但其中 105/144 在后续 coverage 的 HB 检验会通过，主 endpoint 为 25/36，主分母的 57/57 个 oracle 行全部存在后续通过点。
2. r004 oracle 用 instance event 排序，再用持久化全局行号打破同值。它不优化 conditional scene functional，也不会优先把安全实例分散到更多场景，不能称 scene-risk upper bound。
3. 全部 576 行里有 22 行 `actual_feasible=True` 而 `oracle_primary_feasible=False`；其中 20 行被 precedence 错标为 `ORACLE_DATA_OR_GRID_LIMIT`，12 行实际 practical，另 2 行是 trivial feasible。主 endpoint 也存在 target-GT diagnostic score 在 70% coverage practical、oracle 却失败的直接支配性反例。
4. 因而 primary `76/44/24` 是对 144 个全部状态行的标签，不是 142 个 failure 的原因分解。正确状态分区是：75 个 oracle/sequence 未决 infeasible、44 个 structural infeasible、23 个 trivial-budget infeasible、1 个 nontrivial practical、1 个 trivial formal，共 144。

结论：r004 数值资产和 literal gate 为 `adopt`；“data/grid 而非 score 是主因”为 `reject`；C2 科学方向为 `revise`，不是被杀死。主分母目前只确定 33/90 是结构性 scene-count 功效界；其余 57/90 是 1% 入场、候选顺序、policy class、scene allocation、事件支持和 score 的混合边界。

### 2.3 合规计数需修订

r004 没有 detector 训练、detector 推理、下载或 GPU 使用；但 parity 重建明确执行了 12 次冻结诊断回归器 `.fit` 和 12 次 `.predict`。因此报告中的统一 `training/inference=0/0` 不成立。该矛盾来自 r004 同时要求重建 geometry score 又笼统要求训练/推理为 0；本轮不据此抹掉科学产物，但记为 `DIAGNOSTIC_REPRO_FIT_PREDICT_UNCOUNTED`。以后必须分别报告 detector 操作与 diagnostic reproduction 操作。

## 3. TGRS 级最强攻击

[TGRS 官方范围](https://www.grss-ieee.org/publications/transactions-on-geoscience-remote-sensing/)要求 novel methodological advancement、significant research，并要求实验数据和条件完整（核查于 `2026-08-05`）。当前至少有六个硬问题：

1. estimand 只覆盖 GT-matched orientation 和 eligible nonempty scenes，排除了 FP、FN 与真正空场景；不得称 full-output deployment guarantee。
2. r004 的 oracle/fixed-sequence 设计让结论在“字面主门 0/90”和“忽略首败后的 any-grid 57/90”之间翻向，说明 headline 对候选顺序高度敏感。
3. AP@0.5 零下降部分由 IoU 0.50 边界内的扰动构造保证；缺完整固定剂量 full-evaluator 曲线。
4. 原 A6 无合格前瞻单元、固定剂量 raw prediction 不全、第三标注者/仲裁未完成。
5. [SeqCRC](https://arxiv.org/abs/2505.24038)、[EAV-DETR](https://hub.hku.hk/handle/10722/372539) 与[航空/卫星检测 conformal 工作](https://proceedings.mlr.press/v230/copley24a.html)已覆盖检测中的 matching、空预测、联合/条件风险或 OBB conformal。本文不能声称首个角度不确定性或首个遥感 conformal。
6. 冻结协议把缺失 TTA 排到末位并保留 eligible universe，正文却写“NaN 不进入指标”；后续必须披露 DIOR-R `298/48282=0.617%`、SODA-A `2104/193045=1.090%`。

## 4. 可证伪候选与最低 gate

| 候选 | 最近一手工作与实质差异 | 最低判别实验 | 杀死条件 |
|---|---|---|---|
| C2-R：power-aware scene-level LTT | [SeqCRC](https://arxiv.org/abs/2505.24038)处理检测匹配、空预测和联合风险；本文只保留 OBB orientation、mother-scene grouping、finite-scene power 与候选顺序的实质差异 | r005 先构造严格支配实际 selection 的 scene-functional attainable envelope，分开 formal fixed-sequence、any-grid sensitivity 与 relaxed oracle；随后只允许用 fit-only 信息预注册新候选顺序，并在外部单元前瞻验证 | 新 oracle 仍出现 actual feasible / oracle infeasible；或改进只能用 calibration/audit outcome 调序；或错误率控制后无非平凡 practical 点 |
| C3：RSAR × S2ANet 前瞻外部复现 | [RSAR CVPR 2025 论文](https://openaccess.thecvf.com/content/CVPR2025/papers/Zhang_RSAR_Restricted_State_Angle_Resolver_and_Rotated_SAR_Benchmark_CVPR_2025_paper.pdf)与[固定官方实现](https://github.com/zhasion/RSAR/tree/6594e685de1e592bd66bff5451763380d0d36c53)提供未参与协议设计的 SAR 域；差异是把冻结的 orientation/power 协议带到新域，不是复用旧个人项目结果 | r005 通过后做独立 acquisition/provenance gate；再只运行一次 raw/pre-NMS/final、固定剂量、NRC、conditional scene 与 full-output sensitivity | 许可/身份不清、8467 val 图像与 16860 instances 不闭环、split overlap、母景不可恢复、checkpoint 严格载入失败、raw→final 不可持久化或前瞻方向反转 |
| C1-R：matched-only 到 full-output estimand bridge | [Copley et al.](https://proceedings.mlr.press/v230/copley24a.html)已将 conformal 用于航空/卫星检测；本文的剩余差异只能是 orientation-specific conditional risk 与全输出 joint risk 的显式桥接 | 六单元与 RSAR 同时报 matched conditional 和包含 FP/FN/空场景的 joint-risk sensitivity | 两种 estimand 方向冲突，或主结论只能靠排除 FP/FN/空场景成立 |

RSAR 候选仍固定为 official commit `6594e685de1e592bd66bff5451763380d0d36c53`、validation × S2ANet-R50-FPN-le90；但在 r005 前不下载、不推理。RSAR val 的规模并不会自动修复 1% 首点功效问题。

## 5. 决策台账

| 决策 | 状态 | 理由 | 下一步 |
|---|---|---|---|
| r004 文件边界、hash、parity、zero-loss 数值 | adopt | 独立结构和算术复核通过 | 作为不可改写历史资产保留 |
| `FAIL_SCORE_LIMIT_DOMINANT` | revise | 仅保留为 frozen 1%-entry fixed-sequence literal gate | 不进入论文因果 headline |
| `ORACLE_DATA_OR_GRID_LIMIT=57/90` | reject | oracle 不支配实际 selection，57/57 后续 grid 有通过点 | r005 改为 scene-functional attainable envelope |
| r004 统一 training/inference `0/0` | revise | detector 为 0/0，但诊断复算至少 fit/predict 12/12 | r005 分开计数并留下静态证据 |
| 立即做 RSAR acquisition/inference | reject-now | 当前协议—功效归因未修复；扩域可能重演首点必败 | r005 通过后再开独立 acquisition round |
| 恢复 B 或下载其它个人项目 | reject | 不创造前瞻独立性，也不修复统计门 | 保持停止 |
| 再次调用 CC | reject-now | 当前有可执行、可证伪的统计反例 | 新协议与前瞻包冻结后投稿前再审 |

## 6. r005 gate、置信度和最弱环节

r005 只做已有证据的零 GPU scene-functional oracle repair，唯一任务见 [`sug.md`](sug.md)。它必须先把 r004 的支配性反例复算为机器可读证据，再构造对任意实际 selected subset 都不劣的 calibration attainable envelope。若仍出现一条 actual feasible 而 envelope infeasible，立即 inconclusive；不得继续做因果归因。

- 置信度：提交/哈希/schema `0.99`；r004 literal 算术 `0.98`；oracle 不支配反例 `0.99`；C2-R 仍可能成为 TGRS 方法贡献 `0.72`。
- 最弱环节：新的 power-aware 规则是在观察 A–F 后提出，存在事后设计风险；只能靠冻结规则后的 RSAR 前瞻单元消除，不能靠更多内部表格消除。
- 反证条件：若严格 dominating envelope 仍不能稳定分开 structural、empirical-support 与 selection-protocol gap，或任何新顺序需要 calibration/audit outcome 才成立，则 C2-R 不足以支撑 TGRS，论文按 strong JSTARS 收敛。

即使 r005、RSAR、full-output bridge 和实验完整性全部通过，也只是把 TGRS 从“高风险 borderline”提升为“可认真尝试”，不保证录用。
