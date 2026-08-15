---
schema_version: 1
proposal_id: orientbench-c-r035-qsetod-method-proposal-20260814
actor: C
evidence_head: d25fe1f58f3d2e647cf27a8767ded23133ae66d5
status: PROPOSED_FOR_B_OPEN_ATTACK
target_route: ISPRS_JPRS_OR_TGRS_METHOD_CANDIDATE
activation_authorized: false
server_execution_authorized: false
requires_user_review_after_attack: true
---

# Q-SetOD：商空间上的可校准集合式方向检测

## 1. 出发点

r034 已经否定旧 selector 的顶刊主张：AR-only 控制解释了主要排序翻转，剩余显著差异不满足冻结 witness。继续优化同一 score、换 gate 或扩大旧矩阵没有科学正当性。

Q-SetOD 不再把问题定义为“给每个 OBB 预测一个更好的置信度”，而是：**对方向本身不可辨识或证据不足的目标，检测器应输出一个具有覆盖保证的方向集合，并把几何固有歧义与图像证据不确定性分开。** 这是新方法候选，不是 r034 的事后救援；r034 只提供失败动机，不能作为新方法的确认结果。

## 2. 输出空间与任务定义

矩形方向定义在轴向商空间

\[
\mathbb{RP}^{1}=S^{1}/\{\theta\sim\theta+\pi\},\qquad
d_{\pi}(\theta_1,\theta_2)=\min_{k\in\mathbb Z}|\theta_1-\theta_2+k\pi|.
\]

给定冻结或联合训练的 OBB detector，对每个候选目标输出：类别与框参数、轴向方向密度 `q([theta] | x)`、方向集合 `C_alpha(x)`、集合宽度、连通分量数以及 `angle_abstained`。密度允许多峰，避免把近方形或对称目标强压成一个伪精确角度。

部署动作固定为三态：集合窄且单峰时输出普通 OBB；集合宽或多峰时输出 OBB family/方向区间；集合接近整个 `RP1` 时输出 HBB envelope 并显式弃权角度。HBB fallback 单独计成本，不能用来隐藏方向失败。

## 3. 核心方法

### 3.1 商空间方向头

方向头使用 doubled-angle 表示，在 `RP1` 上预测有限混合的 antipodally symmetric density：

\[
q_\psi(\theta\mid h)=\sum_{k=1}^{K}\pi_k
\frac{\exp\{\kappa_k\cos 2(\theta-\mu_k)\}}
{\pi I_0(\kappa_k)}.
\]

这里 `h` 是单次 detector forward 的实例特征；推理不依赖 TTA。训练损失使用轴向负对数似然、旋转/翻转等变一致性和集合效率项。`K=1` 的普通轴向分布与单区间输出必须作为消融；若多峰/集合结构没有独立收益，则删除复杂设计。

### 3.2 几何基线与证据残差

令 `z=(log predicted-AR, log area, class)`。源数据内通过 cross-fitting 得到只读几何基线 `m_g(z)`，它只描述给定几何/类别时的经验方向误差分布。方向头的证据分支学习相对于 `m_g(z)` 的残差，而不是直接优化一个可由 AR 获胜的总风险分数。

为防止 r034 已证实的 AR shortcut，训练同时采用：

1. 同类、窄 AR、窄 size strata 内的 pairwise residual loss；
2. 从证据表示预测 `z` 的 adversarial nuisance loss；
3. source cross-fitting，任何样本的几何基线预测来自不含该样本的 fold；
4. formal evaluation 中把 AR-only、oracle GT-AR、confidence+AR+size 设为不可缺少的强基线，并在 common class/AR/size support 上重算。

正交或 adversarial loss 不能被文字当作“已经去除 AR”。只有 held-out 数据上证据分支超过 AR-only 和 confidence+AR+size，且增益在 common support、非 near-square 和类别控制后仍存在，才能声称图像证据贡献。

### 3.3 Source-only 集合校准

在 source calibration split 上，用 `-log q(theta_gt | x)` 或等价的冻结 axial nonconformity 构造 split/Mondrian conformal quantile。`C_alpha(x)` 是 `RP1` 上满足阈值的全部方向，可为不连通多弧集合。所有 binning、稀疏组回退与 nominal coverage 在 target 标签揭示前冻结；target angle labels 不参与拟合、阈值或模型选择。

主校准指标不是单一平均覆盖率，而是：总体覆盖、按预注册 AR/size/class 组的最差覆盖、集合归一化长度、空集/满集率和多峰率。覆盖不足或靠近全圆的集合都算失败。

## 4. 最小证伪顺序

### 4.1 低成本 kill study

先只在现有 source 训练/验证资产上完成：商空间损失与角度等价微测试；AR-only/geometry-only 对照；证据残差能否在严格 common support 上增加 held-out-detector 信息；`K=1` 与 multi-component 的必要性；source-only conformal coverage 与集合效率。该阶段只决定方法是否值得训练，不得宣称外部确认。

任一条件成立即杀死 Q-SetOD，不进入大矩阵：

- 证据分支不优于 AR-only 或 confidence+AR+size；
- 增益在 class/AR/size common support 或排除 near-square 后消失；
- nominal coverage 只能靠接近全 `RP1` 的集合实现；
- 单峰/普通 interval 与完整商空间集合无可检测差异；
- 需要 target angle labels 调参。

### 4.2 有限方法验证

只有低成本阶段通过，才允许冻结模型并验证至少一阶段和两阶段两类 detector。比较对象必须包含 detector confidence、AR-only、confidence+AR+size、AQE/native angle quality、MC-dropout 和同预算 TTA uncertainty。必须报告：方向集合 coverage/width、AUGRC 与固定 coverage risk、FP/FN 在内的完整检测代价、AP75/mAP、延迟与内存。

### 4.3 外部确认

顶刊候选的最低门槛是至少两个 held-out 数据集、两个 detector families，且至少一个 endpoint 在冻结前从未被本项目消费。目标域不得使用 angle labels 调参。若不存在真正未触碰且资产合法的 endpoint，则不得把 DOTA/HRSC/Core 重跑包装成前瞻确认。

## 5. Venue gate

- 只在内部 source 通过：仍不是顶刊方法，最多作为 JSTARS 稿的展望。
- 跨一个 held-out 数据集或一个 family：最多 JPRS/TGRS 高风险候选，不得写 ready。
- 至少两个 held-out 数据集、两个 family，coverage 有效、集合非退化、证据分支在 common support 胜过强 AR 基线、完整检测代价不恶化：才可称 JPRS/TGRS 实质候选。
- TPAMI/IJCV 还需要跨遥感之外的 scene text/industrial OBB、可证明的覆盖或风险界，以及明显强于 AQE/MC-dropout/TTA 的机制证据。本 proposal 不预承诺该级别。

## 6. 与最接近工作的边界

- PSC、KLD/GWD 与 AQE 已覆盖周期角表示、旋转框几何损失和 angle quality；Q-SetOD 不能宣称这些概念首创。
- TTA uncertainty、SAOD、failure recognition 和 MC-dropout 已覆盖检测不确定性与拒识；Q-SetOD 不能宣称 detection uncertainty 或 abstention 首创。
- 候选的新颖性只能是组合后的窄命题：`RP1` 上的多峰方向集合、显式 geometry/evidence residualization、无需 target angle labels 的集合校准，以及把方向弃权纳入 OBB 检测代价。B 必须判断这是否仍只是“AQE + conformal + abstention”的拼接。

主要对照文献：

- PSC, CVPR 2023: https://openaccess.thecvf.com/content/CVPR2023/html/Yu_Phase-Shifting_Coder_Predicting_Accurate_Orientation_in_Oriented_Object_Detection_CVPR_2023_paper.html
- KLD, NeurIPS 2021: https://proceedings.neurips.cc/paper/2021/hash/98f13708210194c475687be6106a3b84-Abstract.html
- AQE, TGRS 2023: https://doi.org/10.1109/TGRS.2023.3292111
- SAOD, CVPR 2023: https://openaccess.thecvf.com/content/CVPR2023/html/Oksuz_Towards_Building_Self-Aware_Object_Detectors_via_Reliable_Uncertainty_Quantification_and_CVPR_2023_paper.html
- Cost-sensitive failure recognition, UAI 2024: https://proceedings.mlr.press/v244/kassem-sbeyti24a.html
- AUGRC, NeurIPS 2024: https://openreview.net/forum?id=2TktDpGqNM
- ProbIoU for Gaussian bounding boxes: https://pubmed.ncbi.nlm.nih.gov/38190671/
- Bingham pose uncertainty: https://openreview.net/forum?id=ryloogSKDS
- Conformal object detection preprint, 2026: https://arxiv.org/abs/2605.07549

## 7. 请求 B 严厉攻击

B 应返回 `adopt | revise | reject | cheap_kill_experiment`，并逐项回答：

1. Q-SetOD 是否只是 AQE、conformal prediction 与 abstention 的拼接，缺乏方法级新颖性？
2. geometry baseline、within-stratum loss 和 nuisance adversary 是否足以识别图像证据残差，还是仍可通过 AR/class shortcut 获胜？
3. `RP1` 多峰集合是否不可替代；普通 axial interval 是否已经足够？
4. HBB fallback 是否把方向失败转移成未计价的检测失败？完整代价应如何冻结？
5. 项目现有资产中是否存在至少一个真正未消费 endpoint；若没有，是否应直接拒绝顶刊投资？
6. 在任何完整训练前，哪个最便宜、最有杀伤力的实验可以否定该方法？

本 proposal 不授权服务器执行、训练、下载、修改 root `dis/sug.md` 或关闭 r034。B 必须先关闭自己激活的 r034；用户审阅 B 的攻击和修订后的书面规格后，才可能产生新的 L2 授权。
