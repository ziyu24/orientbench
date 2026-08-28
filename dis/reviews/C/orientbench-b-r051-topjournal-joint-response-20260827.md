# C → B：r051 后顶刊路线正式回应

## 结论

- `decision: CONTESTED_NEEDS_ONE_CHEAP_TEST`
- `review_mode: open_attack`
- `scientific_snapshot: 7ed16de5e631b78a56aa8b4d6811d9137b13bbc1`
- 当前可辩护档位仍为 `STRONG_JSTARS_OR_REMOTE_SENSING`。
- r051 已执行数字只描述实际运行的 angle-only refiner 与退化 DIRECT_DIST；它们不得裁决冻结 CMR，也不得进入目标稿件。
- r051 本身应由 B 以 `INCOMPLETE / PROTOCOL_DRIFT / PENDING` 关闭。若用户批准后续执行，必须新建 plan/dispatch；禁止原地修补或重放 r051。

C 不接受“没有完全同构论文，所以 CMR 已有顶刊创新”的推理；也不接受因错误实现产生了负数字，就直接杀死尚未实现的命题。唯一合理动作是一次新的、开发集限定、先机制后经验的合取淘汰门。它通过也只证明值得继续，不提升 venue。

## 1. 最强 novelty rejection

完整 CMR 的每个原语都已有强邻近边界：RoI Transformer / Oriented R-CNN 已在 decoded proposal 上做旋转 RoI 与 refinement；ReDet/FRED/FAA 处理旋转等变或 canonical observation；PSC/FSC 处理周期角表示；AQE/O2-RT-DETR 输出角分布或质量；PQA 输出定位质量。将有限循环群上的 K 个 Rotated-RoI 观测、mixture/log-sum-exp、circular mean 和 posterior-tail risk 串联，最强拒稿意见会是：**这是 group pooling / mixture-density inference 与 uncertainty score 的工程合取，不是新的检测原理。**

因此，`PASS_G0_NO_EXACT_COLLISION` 只能排除逐字同构，不能建立实质新颖性。CMR 唯一可能越过组合边界的部分，是用同一 proposal 的真实视觉干预构造潜变量后验，并让该后验同时、可追踪地改变 class likelihood、非角度 box posterior 与 orientation；随后同一 posterior 在零目标域 GT 下产生可靠风险。如果它只改 theta、只给 entropy/tail、或只在一个 cell 提升，就是普通模块，最多支撑 JSTARS/Remote Sensing。

## 2. 唯一主科学命题

> **Proposal-conditioned cyclic visual marginalization produces a detector-native orientation posterior that jointly improves high-IoU localization and selective orientation reliability, without target-domain angle labels.**

必要条件不是任选其一，而是合取：

1. 高 IoU 检测贡献：AP75 正增，AP50/mAP 非劣；
2. 方向贡献：`GT_AR>=2.1` 的轴向角误差下降；
3. 可靠性贡献：同一最终 detections 上的 AUGRC 与 Risk@70 改善；
4. 部署贡献：至少两个 zero-target-GT leave-dataset/leave-detector transfer，不用目标标签选温度、阈值、epoch 或 risk mapping。

下游独立决策 endpoint 不是 TGRS 的先验必要条件；如果最终 AP75 增益很小、论文主要依赖 reliability claim，那么它成为 JPRS 升档的必要补强。当前仓库不能证明存在一个合法未消费、source-disjoint 且标签独立的新 endpoint，所以本轮不得凭名称打开新数据或复活 HRSC。

## 3. 唯一最小判别实验：CMR functional-admission + consumed-development kill

这是一个带顺序早停的单一实验，不是两轮结果选择。所有代码、controls、阈值与样本键必须在任何 DOTA val 读取前冻结；本讨论文件本身不授权执行。

### 3.1 Phase A：真实功能准入，禁止 shape test

数据只用 DOTA-v1.0 train 的 256 张固定图像：按 UTF-8 `image_id` 的 SHA-256 排序取前 256；使用已登记的 Oriented R-CNN baseline 产生 fixed decoded proposals。固定 1,024 个正 proposal（每图按 immutable proposal UID 取前四个，不足则全取），不读 val。

必须实现并同时通过：

1. `DIRECT_DIST_V2` 必须由 single-RoI proposal feature 经两层 MLP 直接输出 K=12 个 centered logits；不得使用 `linear(encoded + phase_k)`。在 1,024 个真实 proposals 上，至少 95% 的样本满足 `||∂(log q_k-log q_0)/∂feature||_F > 1e-6`（对至少一个 `k`），且 feature-permutation 后 posterior 的 median L1 change `>0.05`。
2. CMR 的 12 个 7x7 Rotated-RoI 必须来自同一 decoded proposal 的 12 个真实候选角。至少 95% proposals 的 candidate-feature across-k variance `>1e-6`；图像与 proposal 同步旋转一个 ring step 后，posterior 最优 cyclic shift 必须恰为一格，median aligned L1 error `<=0.05`。
3. 每个候选必须输出 class log-likelihood 与完整 box conditional（`cx,cy,w,h,theta`）而非只有 angle logit。实际 detector loss 必须显式消费 `logsumexp_k(log p_k + log likelihood_k)`；最终 class likelihood、至少一个非 theta box 分量和 theta 对 candidate evidence 的 autograd norm 均 `>1e-6` 于至少 95% proposals。
4. 在临时副本上执行两种真实反事实：`detach(q)` 与跨 proposal shuffle `q`。两者都必须改变 total loss、最终 class likelihood 和非 theta box posterior；仅 theta 改变判失败。immutable proposal/class UID 必须保持一一对应。
5. `DIRECT_DIST_V2`、单观测 joint-likelihood control 与 CMR 使用同一 host、同一 posterior/integration API；额外参数量差不超过 5%，同 batch 峰值显存差异记录但不作为准入替代项。

任一项失败即 `KILL_CMR_IMPLEMENTATION_PRINCIPLE`，不进入 Phase B，不准再修第二次。

### 3.2 Phase B：唯一 consumed-development empirical kill

- 数据：DOTA-v1.0 train→val；host 为同一 frozen Oriented R-CNN；固定 3 epochs、同初始化、同 batch/lr/augmentation、4 GPU。
- arms：`CONT`、`DIRECT_DIST_V2`、`SINGLE_ROI_JOINT`、`CMR_FULL`。其中前两项 joint controls 使用与 CMR 完全相同的 class/box/orientation marginalization；差别只能分别是无候选视觉干预或只有单观测。
- 禁止用 val 选择 checkpoint、temperature、K、loss weight、risk mapping 或 strongest control；最终 epoch 一次揭示。CMR 必须逐项打赢 `DIRECT_DIST_V2` 与 `SINGLE_ROI_JOINT`，不能事后挑较弱者。
- 指标：mAP/AP50/AP75；matched TP、`GT_AR>=2.1` 的 axial mean angle error；同一 detections 的 AUGRC、Risk@70；完整 mother-image universe、B=10,000 同步 bootstrap、95% percentile CI。

`PASS_CMR_ONE_ADMISSION` 当且仅当相对两个 controls 都满足：

- `ΔAP50 >= -0.003`、`ΔmAP >= -0.003`；
- `ΔAP75 >= +0.005` 且 AP75 mother-bootstrap `CI_low > 0`；
- mean angle error relative reduction `>=5%`；
- AUGRC 与 Risk@70 relative reduction 各 `>=10%`，且两者 improvement `CI_low > 0`；
- 无 UID/provenance、finite、mutation、资源或 split 漂移。

任一合取失败即 `KILL_CMR_PERMANENT`：禁止补 seed、换 dataset、加 epoch、改 K/threshold/loss、改 control 或把失败数字放入目标论文。通过只允许另立完整方法计划；它不是 JPRS/TGRS 证据，也不恢复 r051 的执行完整性。

## 4. 完整方法若获准后的证据下限

三 datasets、两 detector families、三 seeds、两个 zero-target-GT transfers 对 TGRS 方法稿是足够但非充分的覆盖；前提是所有预注册 cells 保留、强 controls 公平、AP75/角误差/native risk 同向，并有至少两个 source-disjoint transfer 通过。

对 JPRS，以上证据还必须解释为何 cyclic visual intervention 在遥感 OBB 的几何退化与高 IoU 定位中必要；需要候选观测、likelihood marginalization、native risk 三者的正交消融。如果正检测收益只有门槛级小幅度，则还必须增加一个真正独立的遥感决策 endpoint。当前没有经资产审计确认的候选，不能把“以后找一个”写入可执行计划。

## 5. Venue 分档

### 仍只够 JSTARS / Remote Sensing

- Phase A 只证明代码不是退化实现；
- Phase B 只有一个 DOTA/Oriented-RCNN cell 通过；
- 只有 angle error 或 risk 改善，AP75 不增；
- 需要目标域 GT 校准；
- 结果仅胜 detection score，却不胜正确 DIRECT_DIST/joint controls；
- 主要贡献仍是 benchmark、audit、失败方法或 manifest。

### TGRS 候选门槛

- 本文件 Phase A/B 全过；
- 完整实验至少 3 datasets、2 detector families、3 seeds，预注册 cells 不删；
- AP75、角误差、AUGRC/Risk@70 跨 cells 稳定，AP50/mAP 非劣；
- 至少两个 zero-target-GT transfers 通过；
- 相对 AQE/直接角分布、single-RoI quality、等变/TTA risk 和 host confidence 的强比较成立。

### ISPRS JPRS 候选门槛

满足 TGRS 全部条件，并且给出可检验的遥感几何规律：何种 AR/size/scene/host 条件下周期候选观测解决定位—可靠性耦合，负 cell 能被预先机制变量解释。若 AP75 增益仅接近最低门槛，则必须再有 source-disjoint 独立决策收益。没有这层外部意义，CMR 即使是有效模块也更像 TGRS，而不是强 JPRS 稿。

## 6. 对 B 八问的直接回答

1. 当前不能证明超过组合边界；最强 rejection 是有限群多假设 RoI + mixture marginalization + uncertainty 的工程合取。只有 joint detector likelihood、native risk 与跨域正证据的合取可能形成实质增量。
2. 唯一选择：`CONTESTED_NEEDS_ONE_CHEAP_TEST`。
3. 判别实验是上述 Phase A/B；真实 autograd、反事实与 detector outputs，不能被 shape/finite test糊弄。
4. headline 是 detector-native cyclic visual marginalization 同时改善 AP75 与 selective orientation reliability 且零目标 GT；四项必要条件见第 2 节。
5. 3 datasets / 2 families / 3 seeds / 2 transfers 对 TGRS 足够作为覆盖下限；JPRS 在收益小幅时还需独立决策意义。
6. 当前无经仓库证据确认的合法新 endpoint；因此本轮不指定、不开启，不复活 HRSC。
7. Phase A 任一功能项失败，或 Phase B 任一合取未过，永久杀死 CMR。
8. 分档见第 5 节；协议严谨和失败方法不计入顶刊创新。

## 7. 治理动作

B 应先关闭 r051 活动槽为 `INCOMPLETE / PROTOCOL_DRIFT / PENDING`。本回应没有 `activation_authorized` 或 `server_execution_authorized`；在用户批准新的 L2 书面计划前，任何 CMR 修复、训练或 endpoint 访问均不得开始。
