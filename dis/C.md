---
schema_version: 3
actor: C
governance_mode: B_C_PEER_EQUAL
evidence_head: f086e8609d060dd94fdfa09248bca57e2ad8912a
evidence_cutoff: 2026-08-15
review_mode: r037_postpull_protocol_drift
current_route: QSETOD_SET_ROUTE_REJECTED
learned_eqs_role: APPENDIX_FAILED_ONLY
r022_c_verdict: ADOPT_HONEST_EARLY_STOP_NOT_ADJUDICATED
r023_c_verdict: ACCEPT_INFERENCE_LAYER_INCONCLUSIVE_MIXED
r026_c_verdict: AUDITED_EXTERNAL_REPLICATION_ACCEPTED
r027_c_verdict: REVISE_NOT_SUBMISSION_READY
r028_c_verdict: AUDITED_EXTERNAL_REPLICATION_ACCEPTED
r029_c_verdict: ARTIFACT_DELIVERY_ACCEPTED_WITH_REPORT_SCHEMA_DEVIATION
r034_c_verdict: ACCEPT_K1_K2_KILL_STRONG_JSTARS_JOINT_FINAL
r036_c_verdict: CONTESTED_BASELINE_AND_CALIBRATION_SEMANTICS
r037_c_verdict: REJECT_FULL_COMPLETION_PROTOCOL_DRIFT_CONDITIONAL_G_SET_FAIL
joint_scientific_state: R037_REPORTED_C_PROTOCOL_DRIFT_PENDING_B
current_venue_ceiling: TGRS_OR_JPRS_ONLY_IF_NEW_METHOD_SURVIVES
current_defensible_level: STRONG_JSTARS_OR_REMOTE_SENSING
next_required_action: CLOSE_R037_INCOMPLETE_THEN_STOP_QSETOD_SET_ROUTE
accepted_requires: B_AND_C_TRACEABLE_MATCHING_VERDICTS
cc_recommendation: 'no'
---

# OrientBench C：r037 post-pull 裁决

r037 的计算与持久化已经跑完，但不能验收为 `full_completion`。A/B 代码只差 4 行实现标签，raw validator 与 A 的行序列相似度为 0.930769，并共享全部主要计算路径；三条链不是独立实现。C 因此把执行裁决定为 `INCOMPLETE / protocol_drift`，科学状态保持 PENDING。

已提交表格的门控算术本身清楚：T2 为 4/8 witnesses，T3 为 0/8 set witnesses。条件性解释是 TTA 特征还有标量诊断信息，但 Q-SetOD 集合/覆盖路线失败，不能训练、不能升档。当前真实级别仍为 strong JSTARS / Remote Sensing；JPRS/TGRS 未 ready。详细证据见 `dis/reviews/C/orientbench-r037-postpull-protocol-drift-review-20260815.md`。

下一步不是重跑 r037 或换 gate，而是关闭该槽并终止 Q-SetOD set-route。若继续冲 JPRS/TGRS，必须另立真正的新方法与清白 endpoint 计划。

# OrientBench C：r036 争议与 r037 纠错性服务器计划

r036 的执行完整性可以接受，但候选科学状态不能直接接受。`KILL-E=false` 的 evidence 模型同时加入 `detection_score` 与 TTA 特征，没有隔离 TTA 相对于 `confidence+AR+size` 的独立增量；`KILL-C=true` 的四个触发项全部是覆盖率高于名义值，代码却用绝对偏差把保守覆盖当作有效性失败；T4 又只校准 geometry-q75 代理，而非 evidence-q75。多峰结论使用非标准近似 dip test，只能描述性保留。

C 已登记实质 contest，并冻结 r037 CPU-only 纠错计划。r037 不训练神经网络、不使用 GPU、不读取两个清白 endpoint 的标签，只在 r036 冻结行上完成三层嵌套基线、单侧覆盖、区间评分与严格重放。若 TTA 独立增量失败，Q-SetOD 终止并按 strong JSTARS 收稿；若通过，也只取得后续小规模方法验证资格，不自动升档。

当前 r036 仍是 B-owned active dispatch。B 应先按 `COMPLETED / CONTESTED` 关闭，再依据 r037 冻结计划中的 delegated activation 启动新轮；C 不越权覆盖根 `dis/sug.md`。

# OrientBench C：r034 后的新方法候选与唯一下一步

r034 已完整执行，并把旧 selector 路线判死：`K1=true`、`K2=true`、`SURVIVAL=false`，12 个冻结主假设没有一个 witness。C 接受该否定结果；当前可辩护级别仍是 strong JSTARS / Remote Sensing，不因审计包完整而升档。B 仍是 r034 owner，必须由 B 关闭 active dispatch。

C 不再修改旧 gate、扩大旧矩阵或用 HRSC/DOTA 续命。唯一候选是新方法 **Q-SetOD**：在轴向商空间输出可校准的方向集合，显式分离几何固有歧义与图像证据不确定性，并用 source-only conformal calibration 给出覆盖保证。完整候选规格在 `dis/reviews/C/orientbench-c-r035-qsetod-method-proposal-20260814.md`；对 B 的请求在 `dis/review_requests/C/orientbench-c-r035-qsetod-method-open-attack-20260814.json`。

这只是方法候选和 `open_attack` 请求，不是服务器合同。B 攻击完成、用户审阅修订后的书面规格并另行批准前，禁止激活服务器、禁止生成新的根 `dis/sug.md`、禁止训练或下载数据。

# OrientBench C：一个月未升档的复盘与 r033 候选提升路线

## 为什么投入很多，级别仍停在 JSTARS / Remote Sensing

结论不是“什么都没做”，而是此前大部分工作产生了**排除性证据**，没有产生足以升档的正向科学证据。项目依次确认：learned EQS 的 leave-dataset 为 0/6；r019 失去前瞻身份且固定 standalone 优于 learned EQS；核心 measurement signature 在 DIOR-R 较强、FAIR1M/SODA-A 不复现；DOTA 只有 RTMDet 单元形成正式 witness，Oriented R-CNN 不形成；主稿又暴露 GT-AR 风险归一化与 predicted-AR probe 的循环性，以及类别—AR 混杂。诚实保留这些结果是必要的，但它们只缩窄 claim，没有扩大可迁移贡献半径。

C 的管理失误也必须记录：过多轮次优化了 protocol、manifest、receipt 和 validator 的闭合，却没有把“本轮是否能改变 venue”设为首要门槛；若干服务器合同需要后续修复，形成审计债务；在 learned-selector 路线已经实质失败后，主线收缩得不够快；把资产 ready、可重放和论文科学升档混为了一谈。迁移和服务器差异解释了部分执行失败，但不能解释论文没有新机制、新外部确认和新可部署方法。后续任何计划都必须按信息增益排序，而不是按审计完整度排序。

## r033 候选路线：先判循环性，再决定是否继续冲顶刊

这不是可执行服务器计划；它是提交给 B 的 `open_attack` 候选路线。B 批判完成、用户批准精确 L2 规格前，不激活、不生成根 `dis/sug.md`。

### 阶段 1：一次性决定性循环性与类别控制

固定现有 A--H cohort，不增数据集、不增 detector、不训练、不改 split/threshold。只允许先闭合官方 raw-object lineage，且不得改变 cohort。随后统一重算：

1. 两种风险定义：当前 GT-AR-normalized risk 与 AR-independent canonical raw-angle risk；
2. 两个 eligibility domain：all-AR 与 AR≥2.1，形成 risk × eligibility 的 2×2；
3. 四个排序基线：detector confidence、predicted-AR-only、oracle GT-AR-only、confidence+predicted-AR；
4. 原始总体估计与 class-standardized/equal-class 估计；
5. 相同 scene/mother-cluster 同步 bootstrap，并冻结有限 primary endpoints 和 multiplicity family。

阶段 1 的 headline 不是“某 probe 赢了”，而是分解三部分：风险定义带来的机械效应、AR 信息本身带来的效应、预测 AR 质量与 detector score 的剩余效应。

**杀死条件：**若 pure-AR/oracle 基线解释主要翻转，或换成 AR-independent risk / class-standardized estimand 后信号不再跨至少两个数据集和两个 detector family 保持，则停止顶刊提升路线；主张降为“评测定义性后果的定量刻画”，直接按 JSTARS / Remote Sensing 成稿，不再追加服务器 gate。

**升档条件：**只有当剩余效应同时跨至少两个数据集、两个 detector family，并且不是单一类别、near-square 比例或 oracle GT-AR 驱动，才进入阶段 2。

### 阶段 2：解释 mixed，而不是扩大矩阵

只针对阶段 1 保留下来的效应，比较 RTMDet 与 Oriented R-CNN、DIOR-R 与 FAIR1M/SODA-A 的边界。先使用既有产物诊断 score entropy、AR 分布、类别组成、匹配率和 NMS 前后 score 语义；只有这些证据提出可证伪机制后，才授权一个最小干预，例如固定框与匹配、仅替换 score definition 或 pre/post-NMS score。禁止先补 8--10 detector 矩阵。

**杀死条件：**若 mixed 只能用事后叙事解释，或干预结果随数据集/阈值任意翻转，则不声称机制，维持中档 measurement paper。

**升档条件：**预先声明的机制变量能够解释正、负和 mixed 单元，并在留出单元上预测方向，才进入阶段 3。

### 阶段 3：最小修复与真正外部验证

只在阶段 1+2 通过后，设计一个无目标域 angle-error 调参的最小修复，例如源数据冻结的分域 score 选择/校正。目标必须是此前未消费该 endpoint 的数据集或 detector；冻结模型、规则和 gate 后再揭示标签。不得用 DOTA/HRSC/Core 旧结果冒充前瞻确认。

**最终分档：**阶段 1 失败即 JSTARS/Remote Sensing；阶段 1 通过但无机制，最多 JPRS 高风险候选；阶段 1+2 通过可成为 JPRS/TGRS 实质候选；再有阶段 3 的有效外部确认、工具箱和完整自足稿件，才具备较可信的 JPRS/TGRS 冲刺资格。任何阶段都不预先承诺 TPAMI/IJCV。

## B 需要重点攻击的问题

1. 2×2 是否真的识别循环性，还是换一种方式重复定义？
2. official raw-object lineage 对 primary estimand 是硬前提，还是仅 provenance 附加项？
3. 最小 primary endpoints、effect floor、multiplicity 和跨数据集复现 gate 应如何冻结，才能避免事后挑选？
4. 哪个明确结果必须立即终止顶刊投入？
5. 阶段 2 的最小机制干预是否足以区分一阶段/两阶段、score 语义与类别/AR 混杂？

---

# OrientBench C：r032 资产预检验收与当前级别

## 当前裁决

r032 完成了资产清单与 join 预检，但没有执行循环性、类别混杂、effect、bootstrap 或 venue gate。96 个 unit-field 条目中 8 个缺口全部是 `official_annotation_id`；其它表级字段与 48 个 join 检查报告齐备。因此它只证明下一实验接近可做，不构成论文证据升级。

C 接受其保守的 `ASSET_GAP_R032`，但不无保留接受服务器的独立验证范围：validator 没有动态验证 DIRECT/DERIVABLE 字段语义，也没有从 official roots 重建 child manifests。执行以 `COMPLETED_WITH_VALIDATION_SCOPE_DEVIATION_R032` 关闭，科学状态保持 `PENDING/NOT_ADJUDICATED`。

当前可辩护级别仍是 strong JSTARS / Remote Sensing。JPRS 是条件目标且未 ready；TGRS、TPAMI/IJCV、CVPR/ICCV 均未达到。唯一能改变该级别的下一证据是：闭合不可变 official-object lineage 后，在固定 A--H cohort 上一次性完成 risk definition × AR eligibility 的 2×2 循环性对照、纯 predicted-AR/oracle GT-AR 对照和 class-standardized 分析。不得靠新增模型矩阵、恢复 learned EQS 或继续审计仪式升级 venue。

---

# OrientBench C：r031 资产预检回执裁决

## 当前裁决

r031 因六个历史未跟踪路径在 G0 停止，未读取科学资产，科学状态为 `NOT_ADJUDICATED`。停止方向诚实，但缺失必需 `STARTED.json`、报告 `ending_commit` 自引用且同步命令偏离冻结合同，故执行按 `PROTOCOL_ABORTED_R031` 关闭，不能包装成正常完成。

下一步是 r032 同目标技术重试：不删除或移动历史产物，把六个既存路径冻结为只读 quarantine，只允许 hash/bytes 清单且禁止作为科学输入；tracked tree/index 必须 clean，任何第七项脏路径即停。之后才执行八单元字段/键/官方标注预检。

---

# 历史：r030 主稿严厉验收与顶刊阻断项

## 当前裁决

r030 产出了可审阅稿件，但服务器执行存在冻结 completion/STARTED/report schema 漂移；C 以 `PROTOCOL_DRIFT_R030` 关闭执行槽，科学状态保持 `PENDING`，不代替 B 作最终稿件裁决。

主稿当前未排除最强替代解释：几何归一风险依赖 GT aspect ratio，而 probe 含 predicted aspect ratio，可能形成定义诱导的排序优势；类别—AR 混杂和 mixed 数据集/检测器边界也未闭合。因此当前真实级别降为 strong-JSTARS/Remote Sensing，JPRS 仅为有条件目标且尚未 ready。

唯一下一步是 r031 只读资产预检；在资产闭合并冻结 2×2 循环性/类别标准化协议前，不运行新效果量、不扩模型矩阵、不恢复 learned EQS。

---

# 历史：r029 最终跨机重放裁决

## 结论

C 在 `fe9d0ea5172c864d0abcecb126f530242a84c7ed` 上完成最终跨机重放，正式裁决为 `AUDITED_EXTERNAL_REPLICATION_ACCEPTED`。此前 r026/r028 contest 已满足最低解决条件并由 C 解除。

这个裁决只接受 DOTA 结果为 `post-outcome audited external replication`。它不是 prospective、preregistered 或独立新 target confirmation；稿件不得恢复这些表述，也不得把 learned EQS 重新升为主线。

## 最终重放证据

- r029 提交只新增 manifest 缺失的 `dota/bootstrap.npy` 和 `dota/dota_gt_fresh.pkl`，并更新 supervisor/report；未改变其余科学 bundle 对象。
- `audit_bundles/r028/bundle_manifest.csv` 的 20 个对象全部存在，20/20 canonical Git blob bytes 与 SHA-256 匹配。
- C 从 bundled raw、bootstrap、tile-to-mother map 和冻结 delta source 运行 `revalidate_r026_raw.py`：状态 `PASS`，96/96 checks consistent；候选 gate 重算为 2 个 unit witnesses、2 个 dataset witnesses，重算 gate JSON 与 committed 文件逐字节一致，6 行 hypotheses 的所有数值与离散字段均一致。
- 六项真实 mutation 均调用 production validator；pristine/mutated exit 分别为 GT_THETA `0/2`、TILE_MOTHER `0/2`、AR_GATE `0/2`、BOOTSTRAP_CELL `0/1`、SWAP_GATE `0/1`、REPORT_TOKEN `0/3`。重算 mutation index 与 committed 文件逐字节一致。
- C 独立读取 Git-tracked GT pickle：5,297 tiles、458 mother scenes、55,804 GT，15 类计数逐项一致。ORCNN 的 48,889 个、RTMDet 的 51,736 个 matched GT-id 均为 GT universe 子集，对应比例分别为 0.8760841517 和 0.9271019999。
- r023 推断层此前已由 C 跨机重放：405 hypotheses、4,950/4,950 checks consistent，重算 hypotheses CSV 与 committed 文件一致。其科学状态仍是 `INCONCLUSIVE_MIXED`：DIOR 信号强，FAIR1M/SODA-A 不复现。
- r027 package manifest 的 17 个对象全部闭合，修正后的 TTA 定义已包含 `missing_fraction`；旧的五个描述性文件已明确标记为 `SUPERSEDED_BY_R028`。

## r029 执行报告偏差

r029 的 artifact delivery 可以验收，但服务器报告本身不完全符合冻结合同：`STARTED.json` 和最终报告缺少合同要求的若干 plan/dispatch/command/resource 字段，且 `completion_mode: PURE_BUNDLE_CLOSURE` 不在冻结 completion 枚举中。因此 C 记录 `R029_REPORT_SCHEMA_DEVIATION`，不把该报告宣称为完全合规。

该偏差不推翻科学 bundle：上述裁决来自 C 对 canonical Git blobs 和 production replay 的独立核验，而不是信任报告中的布尔或完成声明。无需为补写报告再开服务器 round；B 应如实关闭 r029 并给出可追踪的 matching verdict。

## 证据含义

DOTA 的正式可用结果是：AR eligibility domain 会实质改变 OBB orientation-reliability 排序结论。两个 dataset endpoints 均为 witness；RTMDet 的 AUGRC 与 Risk@70 两个 unit endpoints 也为 witness，ORCNN 同方向但不满足 unit witness。结合 r023，这支持一个有明确边界的 measurement-validity/diagnostic 论文，而不是 learned-selector 方法论文。

## 当前期刊级别

- 科学证据：`JPRS_SUBMISSION_CANDIDATE`，但不是录用保证。
- 当前稿件：`NOT_READY`。现有主稿约 848 词、无完整 References、无成稿图表，本质上仍是审计摘要。
- 最匹配冲刺目标：ISPRS Journal of Photogrammetry and Remote Sensing，主线必须是 OBB measurement validity / diagnostic。
- 更稳妥档位：完整成稿后 TGRS 或 strong-JSTARS；TGRS 的方法契合度弱于 JPRS 的测量/诊断 framing。
- CVPR、ICCV、TPAMI：当前证据仍不支持。

## 唯一下一步

停止新增科学 gate、DOTA 重跑、换数据集续命和重复调用 CC。B owner 先关闭 r029并发布与 C 一致、可追踪的 `AUDITED_EXTERNAL_REPLICATION_ACCEPTED` verdict；随后单独立项完成 JPRS 全稿：完整正文、相关工作与一手引用、主图/表、实验细节、限制、claim-to-evidence ledger 和投稿时间线。只有全稿完成并再审后，项目才可从 `JPRS_SUBMISSION_CANDIDATE_NOT_READY` 升为 submission-ready。
