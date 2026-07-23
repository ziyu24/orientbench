# A1 风险预算预注册

冻结时间：2026-07-22T14:03:00+08:00。本文件在最终权威 `D_cal` 认证复算之前冻结；此前试运行产物不作为结果。

## 统计对象

- 主风险事件：`angle_error > delta_theta_0.75(aspect_ratio)`，采用 le90 长边角度、IoU=0.75 的共中心同尺度几何阈值和 `ar>=2.1` 主掩码。
- 敏感性事件：角度误差严格大于 5、10、15 度。
- 外层划分保持既有 `D_cal` / `D_audit` 不变；`D_cal` 内按既有确定性哈希分为 `D_fit` 与 calibration。
- 正式 exchangeable unit 优先为 original mother scene。若既有划分无法形成互不重叠的 mother-scene 角色，则该 evaluation unit 降为 tile/image-level，并显式报告限制与 mother-scene overlap sensitivity。
- eligible-scene universe 在任何 score、threshold、alpha 之前固定：仅含至少一个 `ar>=2.1` eligible matched prediction 的原始场景。
- 阈值后无 selected prediction 的 eligible scene 记为 abstained，不以零风险进入条件风险均值。

## 风险预算与候选序列

- 绝对预算：`alpha in {0.001, 0.0025, 0.005, 0.01}`。
- 次级相对预算：`0.5*r_fit` 与 `0.25*r_fit`；`r_fit` 是该 evaluation unit 与 endpoint 在独立 `D_fit` eligible scenes 上、未筛选状态下的条件场景风险。
- coverage grid：`{0.01, 0.025, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.00}`。
- threshold 仅由 `D_fit` score 分位数冻结；同分数按持久化 prediction row index 稳定打破。
- 个别缺失的 TTA circular variance 不改变 eligible universe；其可靠性分数固定置于该 unit 的最末端（低于最小有限分数），并单独披露缺失率。
- 对每个 score-endpoint-alpha，从最低 coverage 到最高 coverage执行 fixed-sequence Learn-Then-Test；首个 calibration failure 后停止拒绝后续假设。
- calibration 条件场景损失使用 bounded-loss Hoeffding-Bentkus 单侧 UCB，`delta=0.10`；固定序列控制每条序列的 FWER。
- co-primary scene event 使用 exact binomial / Clopper-Pearson 单侧 UCB，采用同一固定序列。

## Score menu 与监督边界

1. `detection_score`：推理可得，无额外 GT 拟合。
2. `tta_circular_consistency`：`theta -> 2theta` 圆统计的负 circular variance；目标推理 GT-free。
3. `source_supervised_leave_geometry`：仅以其他数据集的 `D_fit` GT angle error 训练；目标推理不使用目标 GT。
4. `target_gt_nonlinear_geometry_upper_bound`：仅在目标 `D_fit` 上拟合；属于 diagnostic/calibration upper bound，不可部署。

四种 score 使用相同 evaluation unit、eligible universe、risk endpoint、split、coverage grid、LTT、UCB 和 cluster 定义。除上述预注册的 TTA 末位规则外，缺失 score 不以替代分数填充，直接报告不可认证原因。

## 预先冻结的判定

- `TRIVIAL`：alpha 不小于该 unit/endpoint 的 `D_fit` 未筛选 base risk；仍保留结果但不计成功。
- `INFEASIBLE`：冻结 grid 上无可认证非零选择，或 nonempty scene rate 为零。
- `formally certified`：calibration fixed-sequence 通过，audit 仅作独立报告。
- `nontrivial certified`：formally certified 且非 TRIVIAL。
- `practically useful`：nontrivial certified，且 audit nonempty scene rate `>=0.10`、selected-instance coverage `>=0.10`、selected count `>=100`。
- 最小非退化 coverage 为冻结 grid 上满足 nontrivial certification 的最大 coverage；失败 unit、严格 alpha 下的不可行结果以及仅形式成立结果均不得删除。

不得由 `D_cal` 或 `D_audit` 反推 alpha、改变 score direction、改变 coverage grid、改变 eligible universe，或把 target-GT upper bound 写成 deployable score。
