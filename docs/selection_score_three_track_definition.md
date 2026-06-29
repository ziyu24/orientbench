# Selection Score — 三轨定义（v2）

> 修正此前把 intrinsic score 与 unified proxy 混成横向排名的表述。NRC/Risk 报告须按轨标注。

## 背景问题
- 之前的 cross-detector NRC 排名隐含用了**不可比的 selection score**：有的 detector 用原生 angle confidence，有的用通用 proxy。直接横向排名会把“信号来源差异”误读成“detector 能力差异”。

## 三轨

### Track A — intrinsic（原生）
- 定义：detector **原生输出**的 angle quality / angle entropy / native orientation uncertainty。
- 适用：仅当 detector 有原生角度不确定性输出（如 PSC 的相位置信、DETR 的 query score、角度分类熵）。
- 用途：评估该 detector **自身**的 orientation self-knowledge。
- 限制：不同 detector 的 intrinsic 不可直接横向比较（来源异构）。

### Track B — unified proxy（统一代理）
- 定义：**所有 detector 都能算**的统一 selection proxy。
- 候选：detection score、GV-obliquity、aspect ratio、layout/background source proxy（near-square 风险代理）。
- 用途：**公平横向比较** orientation-reliability（同一 proxy，跨 detector）。
- 本项目当前 NRC matrix 主要基于 **detection score** proxy（Track B），应如此标注，**不得**当作 intrinsic 能力排名。

### Track C — post-hoc upper bound（后验上界）
- 定义：在 **calibration split (D_cal)** 学一个 selector（用可得特征），在 **audit split (D_audit)** 验证。
- 用途：给出 orientation selection 的**可达上界**。
- **必须标 upper bound**；不是 detector intrinsic ability；不得写成 detector 自身可靠性。

## 报告修正要求
- 现有 cross-detector NRC（final_matrix_summary）= **Track B (detection-score proxy)**；标注为统一代理横向比较，非 intrinsic 排名。
- PSC 反校准结论在 Track B 下成立（统一 proxy 横向可比）；若要归因到 PSC angle-coder intrinsic，需 Track A 的原生不确定性分析（angle-head control experiment，待批准）。
- C1/A4 的 selection score 定义（GV/NRC/selection score）**不得修改**（R1-R8 冻结）；本三轨是**报告口径分层**，非重定义。

## 当前状态
- Track B：已完成（23 cells NRC/Risk，detection-score proxy）。
- Track A：未做（需原生角度不确定性提取 + angle-head control）。
- Track C：DOTA C1/A4 已用 D_cal→D_audit upper-bound 思路（formal，frozen）；cross-dataset 未做。
