---
schema_version: 1
proposal_id: orientbench-c-r038-oerobb-method-proposal-20260815
actor: C
evidence_head: b963f9a8c87009a3e98b3c1b2b5b051918a7560f
status: PROPOSED_FOR_B_OPEN_ATTACK
target_route: ISPRS_JPRS_OR_TGRS_METHOD_CANDIDATE
activation_authorized: false
server_execution_authorized: false
requires_user_review_after_attack: true
---

# OER-OBB：条件正交化的旋转目标方向失效排序

## 0. C 的建议

C 建议把 `OER-OBB`（Orthogonal Equivariance Risk for Oriented Object Detection）作为 Q-SetOD 终止后的唯一新方法候选，交由 B 做 `open_attack`。它不是服务器执行计划，也不授权训练、下载、目标标签读取或修改根 `dis/sug.md`。

推荐理由只有一个：r034 已证明旧结论可被 AR/风险定义循环性解释；r037 又条件性显示，翻转等变特征在 confidence、AR、size 和 class 之后仍保留部分标量方向失效信息，但 source-only 区间/集合校准为 0/8。最合理的下一方法不是复活集合覆盖，而是严格检验这部分**条件残差证据能否成为跨域、跨检测器的标量失效排序器**。

当前论文级别仍是 strong JSTARS / Remote Sensing。OER-OBB 只有通过本文末尾的全部门槛，才可能把项目提升为 JPRS/TGRS 实质候选；本 proposal 不承诺录用，更不承诺 TPAMI/IJCV。

## 1. 研究问题与可证伪主张

主问题是：

> 在排除 detection confidence、预测纵横比、尺寸、类别和 detector family 的可预测贡献后，冻结检测器的多视图等变残差是否仍包含可迁移的方向失效信息？

形式化主张限定为：对冻结 OBB detector，源域交叉拟合得到的条件正交化等变残差，可以在不读取目标域 angle labels 的条件下，提高方向失效的 selective ranking，并跨至少两个目标数据集和两个 detector families 复现。

以下更宽主张禁止使用：

- TTA uncertainty、angle quality、failure recognition 或 self-aware detector 首创；
- 因果识别、完全去混杂或“证明 AR 无影响”；
- coverage guarantee、prediction set validity 或 Q-SetOD set-route 复活；
- 任意单数据集/单 detector 的正结果足以支持 JPRS/TGRS；
- 旧 DOTA、HRSC、Core 或 r037 结果是新方法的前瞻确认。

## 2. 任务、终点与适用域

### 2.1 方向失效目标

主标签使用 AR-independent axial angular error：

\[
Y=d_{\pi}(\hat\theta,\theta^{gt})/90^{\circ},\qquad
d_{\pi}(a,b)=\min_{k\in\mathbb Z}|a-b+k\pi|.
\]

主分析域固定为 identity matched true positives 且 `GT_AR >= 2.1`，用于保证方向语义可辨识；all-AR 只作敏感性分析，不进入主 gate。匹配、类别一致性、IoU 阈值、greedy tie-break、near-square 处理与 mother/scene clustering 必须在任何方法结果揭示前冻结。

主排序指标是 AUGRC；固定 coverage 风险至少报告 70% 和 90%。AURC/NRC 可作兼容性报告，但不能替代 AUGRC。完整检测代价还必须报告 unmatched/FP/FN、mAP/AP75 与推理预算，避免通过丢弃困难检测制造方向可靠性增益。

### 2.2 两个信息通道

对实例定义 nuisance channel：

\[
Z=(\text{detection score},\log \widehat{AR},\log \text{area},\text{class},\text{detector family}).
\]

定义 evidence channel `E`：冻结 detector 在 identity、horizontal flip、vertical flip 下的输出，经逆变换、长边 canonicalization 和 `RP1` 周期等价处理后形成的方向残差、中心/尺度残差、匹配 IoU 损失、score dispersion、missing fraction 与 association ambiguity。默认预算为三次 forward；任何增加视图数的版本必须按相同 forward budget 与基线比较。

`E` 不得包含 GT angle、GT_AR、angle error、D_audit role、目标域标签派生量或目标结果统计量。生产 feature schema、候选关联、缺失 sentinel 与 tie-break 必须逐字段冻结并通过等价微测试。

## 3. OER-OBB 方法

### 3.1 Cross-fitted orthogonalization

只在 source development 数据上做外层 leave-dataset / leave-detector cross-fitting。对每个外层 held-out fold，使用其余 source folds 拟合：

\[
m_E(Z)=\mathbb E[E\mid Z],\qquad
m_Y(Z)=\mathbb E[Y\mid Z].
\]

随后构造：

\[
\widetilde E=E-m_E(Z),\qquad
\widetilde Y=Y-m_Y(Z).
\]

证据模型 `h` 只用 `tilde_E` 预测 `tilde_Y`；最终风险为：

\[
R_{OER}(x)=m_Y(Z(x))+\lambda h(\widetilde E(x)).
\]

`lambda`、模型族、容量、损失、fold、随机种子和停止规则全部在 source 内冻结。目标域不允许重新拟合 `m_E`、`m_Y`、`h`、`lambda`、阈值或归一化器。

正交化只是设计约束，不自动构成“去除混杂”的证据。方法有效性必须由 held-out 条件增量、负控制、消融和外部迁移共同证明。

### 3.2 跨域稳健目标

证据模型优先使用低容量 monotone/linear 或浅层 boosting，并以 source dataset 与 detector-family group 的 worst-group ranking loss 选择容量；不得用目标域表现挑模型。必须同时保留：

1. nuisance-only：`m_Y(Z)`；
2. pure predicted-AR；
3. oracle GT-AR，仅作揭示后的机制诊断；
4. evidence-only：`h(tilde_E)`；
5. full OER：`m_Y(Z)+lambda*h(tilde_E)`；
6. 未正交化的 `Z+E`，用于检验正交化是否真的必要。

若未正交化模型与 OER 等价或更稳，必须删除“orthogonal”方法贡献，不能靠命名保留。

### 3.3 类别与 AR 控制

正式结果同时报告原始总体、equal-class/class-standardized、预注册 AR strata 与 common-support estimand。目标域类别权重只能来自冻结的无标签/结构信息或预注册等权规则，不能按结果选择。

关键负控制是：在 class、AR、size 和 confidence 窄层内置换 `tilde_E`。若置换后收益不变，说明所谓证据增益仍由 nuisance 或实现泄漏驱动，方法立即失败。

## 4. 必须比较的强基线

所有基线使用相同检测、匹配、样本域和 forward budget：

- detector confidence；
- predicted-AR only；
- confidence + AR + size + class；
- oracle GT-AR，仅作非部署机制上界；
- generic TTA localization/angle variance；
- SAOD 或等价 localization-aware confidence；
- detector 原生 AQE/angle-quality/MC-dropout，在架构确实提供时报告；
- 未正交化 `Z+E` 与 evidence-only 消融。

如果 generic TTA variance 或 `confidence+AR+size+class` 在相同预算下匹配或超过 OER，方法级主张失败；不能改称工具箱后继续沿用方法 gate。

## 5. 最小证伪顺序

### 5.1 Stage A：现有 source-only cheap kill

只使用已有冻结 A--H/Core 资产，不新增 detector、不训练 host、不读取新 target labels。独立重建主标签和 features 后完成 nested cross-fitting、pure-AR/oracle 对照、class-standardized/common-support 分析和 feature permutation。

Stage A 只证明是否值得投资，不是外部确认。继续条件必须同时满足：

- 对 strongest deployable baseline 的 `Delta_AUGRC >= 0.005` 且 scene/mother-cluster 95% CI lower bound `> 0`；
- 至少 4/8 unit witnesses；
- witnesses 覆盖至少 2 datasets、2 detector families；
- equal-class 与 common-support 下方向不反转；
- pure-AR、oracle GT-AR 和 permutation 不能解释主要增量；
- leave-dataset 与 leave-detector 两类外层验证均存在正向支持。

任一关键条件失败即 `REJECT_OER_METHOD`，停止方法投入并回到测量型 JSTARS/Remote Sensing 稿件。不得改 floor、换 endpoint、扩大矩阵或复用 Q-SetOD gate 救场。

### 5.2 Stage B：机制与预算验证

仅在 Stage A 通过后执行。目标是解释“为什么 RTMDet/DIOR 可能支持而 ORCNN/FAIR1M/SODA-A 不支持”，而不是事后描述 mixed。预先冻结一个最小干预族：score 语义替换、pre/post-NMS score、association threshold 与 view budget。每个干预必须给出事前预测方向。

若没有一个冻结机制变量能够预测 held-out unit 的方向，或结论随匹配阈值/预算任意翻转，则不能声称发现跨 detector 机制，JPRS/TGRS 方法路线停止。

### 5.3 Stage C：真正未消费端点确认

只有 Stage A+B 通过，才允许做只读资产与 prior-outcome preflight。候选可包括 DOTA-v2.0 或尚未消费的 official split，但不得在资产、许可、baseline、annotation semantics 和历史 outcome 搜索闭合前指定为确认集。

顶刊候选至少需要两个此前未消费方法结果的 target datasets、两个 detector families；模型、代码、source fit、目标 prediction-only features、bootstrap draws 和 gate 必须在首次读取 target angle labels 前远端封存。确认后不允许 target tuning、替补数据集、改 gate 或把旧 DOTA/HRSC/Core 填入失败单元。

## 6. 冻结的 venue gate

目标 unit 定义：

\[
\Delta_u=\operatorname{AUGRC}(\text{strongest deployable baseline})
-\operatorname{AUGRC}(\text{OER}).
\]

使用完整 scene/mother universe、保留 zero-eligible clusters、同步 bootstrap、dataset 内 unit 等权，并对正式 unit family 做 Holm 校正。

只有以下条件全部成立，才将项目升级为 `JPRS_TGRS_METHOD_CANDIDATE`：

1. 两个 target dataset aggregate 均满足 `Delta >= 0.005`、95% CI lower bound `> 0` 和预注册显著性条件；
2. 至少两个 detector families 各有正式 unit witness；
3. AUGRC 与 Risk@70/Risk@90 不发生实质方向冲突；
4. class-standardized、common-support 和 AR strata 结论一致；
5. full-detection guard、mAP/AP75 与延迟/显存预算不出现预注册的不可接受恶化；
6. oracle、pure-AR、generic TTA variance 和 strongest deployable nuisance baseline 均不能解释 OER 增量；
7. source freeze、target zero-label access、独立重算和 mutation tests 全部通过。

完整有效执行但只支持一个 dataset、一个 family 或 CI 跨零，裁决为 `INCONCLUSIVE_NO_VENUE_UPLIFT`；明确被强基线支配或机制负控制失败，裁决为 `FAIL_OER_METHOD`。执行异常独立记为 `ABNORMAL_EXECUTION`，不得包装成科学阴性。

## 7. 新颖性边界

下列工作已经覆盖相邻概念，不能伪造首创：

- AQE：训练期 angle quality 与方向分布建模，TGRS 2023，https://doi.org/10.1109/TGRS.2023.3292111
- TTA-based detection uncertainty，IEEE IV 2023，https://doi.org/10.1109/IV55152.2023.10186713
- SAOD：跨 detector 的 self-aware detection、拒识和校准，CVPR 2023，https://openaccess.thecvf.com/content/CVPR2023/html/Oksuz_Towards_Building_Self-Aware_Object_Detectors_via_Reliable_Uncertainty_Quantification_and_CVPR_2023_paper.html
- Cost-sensitive failure recognition，UAI 2024，https://proceedings.mlr.press/v244/kassem-sbeyti24a.html
- AUGRC 与 selective-risk 评测缺陷，NeurIPS 2024，https://openreview.net/forum?id=2TktDpGqNM
- 旋转等变 OBB 表征与边界不连续性工作已经覆盖 equivariance/periodicity 本身，不能声称这些概念首创。

OER-OBB 可能成立的新颖性只能是窄组合：**针对 OBB 方向失效，把商空间等变残差对 geometry/confidence/class 做 cross-fitted orthogonalization，并验证其 source-only 跨数据集/跨 detector selective ranking。** B 必须优先判断这是否仍只是“residualized TTA uncertainty”的常规拼接；若是，应直接拒绝方法路线。

## 8. 请求 B 严厉攻击

B 应返回 `ADOPT | REVISE | REJECT | CHEAP_KILL_EXPERIMENT`，至少回答：

1. OER-OBB 是否具有方法级新颖性，还是 double machine learning 与 TTA uncertainty 的直接拼接？
2. `m_E/m_Y` 的 cross-fitting 是否足以阻断 AR/class/score shortcut；还缺哪些 identification 或 negative controls？
3. 主标签、`GT_AR >= 2.1` 资格域与 matched-TP estimand 是否又产生新的选择偏差？
4. `Delta_AUGRC >= 0.005`、4/8 source gate 和两个 target datasets 是否过松、过严或事后贴合 r037？
5. 哪个 strongest baseline 最可能杀死方法；如何保证同 forward budget 与公平调参？
6. 当前服务器是否真的存在两个可合法封存、此前未消费方法结果的 target datasets 与至少两个 families？
7. 哪一个不超过一次 source-only 轻量运行的实验最便宜、最有杀伤力？
8. 即使全部通过，该贡献是否足以支撑 JPRS/TGRS，还是仍只是 strong JSTARS/Remote Sensing？

B 不得只润色本 proposal，也不得因为用户目标是顶刊而降低杀死门槛。B 的任务是寻找最强替代解释和最便宜的否证实验。

## 9. 授权边界

本文件和对应 request 只授权 B 做只读批判并写入 B 自有 response path。它不授权服务器执行、GPU/CPU 实验、下载、训练、目标标签读取、根 `dis/sug.md` 修改或 active dispatch 激活。B 返回攻击后，C 与用户必须重新审阅修订版；任何 L2 实验需要新的精确书面规格和用户授权。
