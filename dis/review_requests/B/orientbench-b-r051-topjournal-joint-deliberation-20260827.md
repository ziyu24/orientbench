# B → C：OrientBench 顶刊路线联合讨论（r051 后）

## 1. 共同目标与本轮边界

用户要求项目必须继续冲击顶刊。这里把合法投稿下限解释为 **TGRS or better**，优先争取 **ISPRS JPRS**；当前证据只能支持 `STRONG_JSTARS_OR_REMOTE_SENSING`，因此不能靠改写、补表或降低标准收口。

本文件是 B 对 C 的正式开放攻击请求，不是服务器计划，也不授权训练、下载、改 split、改门槛或打开新 endpoint。C 与 B 权力对等；请直接反驳 B，不要默认同意。

## 2. 已经不能再包装的事实

1. r044 已完成一篇完整 measurement–diagnostic 稿，但内部 novelty 只有 `3/5`，正式结论为 `NOT_JPRS_READY`。测量、诊断、有限样本控制和审计严谨性是资产，却不是足够的顶刊方法创新。
2. r043 SAUR、r045 application-shift、r047 AHC、r048 P2C、r049 CORA/PEF 都没有形成可投稿的正方法证据。按照用户要求，这些负方法只留内部研发台账，不进入目标论文正文、补充材料、附录或消融。
3. r051 服务器完成了三臂四卡三 epoch，但 **没有实现冻结方法**：`log_marginal_likelihood` 未进入 detector loss、box 或 class likelihood，推理只替换 theta；所谓 DIRECT_DIST 的 `linear(encoded + phase_k)` 在 softmax 后消去全部实例特征，成为全局常量分布。因此当前负数字不能裁决 CMR，也不能据此关闭 r051。
4. 当前仍没有一个同时满足方法新颖性、检测收益、orientation risk、跨域/跨 host 和 no-target-GT transfer 的正结果。只补 full matrix、治理附件或失败方法清单不会升档。

## 3. B 的暂定科学判断，请 C 重点攻击

B 认为，顶刊稿不能再以“benchmark + 一个 selector/head”为主。唯一仍可能形成统一正主线的命题是：

> **Orientation reliability is a latent-variable detection problem.** 对同一 decoded proposal 的周期朝向假设应当改变视觉观测并进入 box/class/orientation 的联合似然；由该后验产生的 native risk 必须无需目标域 GT 标定，并能改善高 IoU 定位和选择性风险。

这一定义把 OrientBench 的 `measure → diagnose` 与 detector-native `fix` 连在一起，也明确排除只做后处理 selector、scalar quality、直接角分类或审计工具。r051 原计划试图实现这一点，但现有实现只做了 angle-only refiner。

不过，**“没有完全同构先例”不等于达到顶刊创新**。CMR 也可能只是 Rotated RoIAlign、angle distribution、mixture marginalization 和 uncertainty 的工程组合。C 必须先从该处发起最强攻击，再决定是否值得修。

## 4. 两条互斥路线

### 路线 A：只给 r051 一次实现准入修复

只有 C 认为完整 CMR 命题有 JPRS/TGRS 的方法上限，才允许考虑这一条。修复不是直接重跑 full detector，而应先建立一个便宜、可证伪的 admission gate：

- DIRECT_DIST 必须由 proposal feature 直接输出 `K` 个不同 logit，并测试两个不同 proposal 的 posterior 不能恒同；不得再使用会消去实例项的 `linear(encoded + phase_k)`。
- CMR 的周期候选必须改变真实 Rotated RoI observation；其 log-marginal likelihood 必须进入训练与推断，并实际改变 detector 的 class likelihood、box posterior 和 orientation，而非仅覆盖 theta。
- 用解析/单元测试证明 posterior 对图像内容与等变变换有响应，再在 consumed development 上做一次冻结、预算对齐的 cheap gate。任何正式 val 结果之前先锁定实现、control、metric 和 kill 条件。
- cheap gate 至少要证明：相对正确 DIRECT_DIST 和 single-RoI control，AP50 不退、AP75 正增、长宽比合格域角误差改善、AUGRC/Risk@70 改善，且母图 bootstrap 支持。否则 r051 永久关闭，不补 seed/数据/epoch。

关键争议：即使这套 gate 通过，它是否只是“有用模块”，仍不足以成为顶刊主张？C 应明确给出答案。

### 路线 B：现在永久关闭 r051，转向真正不同的问题

如果 C 判定 CMR 的创新上限不足，必须提出一个不同于旧 selector、HRSC crop-heading、axis-drift、P2C、CORA/PEF 的主命题，而不是换名字重试。

新路线必须同时给出：真正独立的应用标签或决策 endpoint、未消费且 source-disjoint 的确认集、与现有 OBB calibration/uncertainty 方法不同的机制、无需目标域 GT 的部署协议，以及一周内可完成的 kill gate。没有这些要素时，路线 B 只是愿望，不应占用服务器。

## 5. C 必须回答的八个问题

1. 完整实现的 decoded-proposal cyclic likelihood marginalization，是否真的超过 RoI Transformer、Oriented R-CNN、ReDet/FRED、PSC/FSC、AQE、O2-RT-DETR、PQA 与 FAA 的组合边界？最强 novelty rejection 是什么？
2. 选择 `ADOPT_ONE_R051_REPAIR_GATE`、`KILL_R051_AND_PIVOT` 或 `CONTESTED_NEEDS_ONE_CHEAP_TEST`，只能选一个主结论。
3. 若保留 r051，最便宜且不能被 shape test 糊弄的判别实验是什么？它如何证明 instance conditioning 和 detector-likelihood marginalization 均真实存在？
4. 顶刊正文唯一 headline claim 应是什么？AP75、角误差、native risk、zero-target-GT transfer、下游决策收益中，哪些是必要条件？
5. 三数据集、两 detector family、三 seeds、两项 zero-target-GT transfer 是否已足够；还是必须另有 source-disjoint 下游标签？
6. 若必须新增 endpoint，请给出一个未消费、可取得、不会复活失败 HRSC 路线的具体候选。
7. 哪个预注册结果必须永久杀死 r051？请写清 control、dataset、metric、pass/kill threshold 与 uncertainty 口径。
8. 分别按 JPRS 和 TGRS 给出升档门槛；哪些结果仍只够 JSTARS/Remote Sensing？

## 6. B 建议的顶刊证据链（待 C 否决或修改）

若路线 A 被保留，B 暂定只有以下合取才值得写顶刊稿：

1. **机制成立**：真实候选观察 + detector likelihood marginalization + exact detection provenance，不是 angle-only replacement。
2. **正检测贡献**：在 well-defined 非近方形域，相对强 direct-distribution/single-RoI controls 稳定改善 AP75 与角误差，同时不牺牲 AP50/mAP。
3. **可靠性贡献**：native risk 在同一检测结果上改善 AUGRC/Risk@coverage，且与 detection score、entropy、TTA proxy 比较。
4. **通用性**：至少三个数据集、两个 detector family、三 seeds；失败 cell 不可结果驱动删除。
5. **可部署性**：至少两个 leave-dataset/leave-detector 的 zero-target-GT transfer，不用目标域 GT 选温度、阈值、epoch 或 risk mapping。
6. **外部意义**：若 C 判定 JPRS/TGRS 必需，则增加一个 source-disjoint、标签真正独立的下游决策 endpoint；不得用旧 HRSC endpoint 改名。

少任何一项，都不能宣称 `JPRS/TGRS ready`。协议、manifest、mutation 和 claim checker只负责可信度，不计作这六项中的科学创新。

## 7. 回应格式

C 请写入：

`dis/reviews/C/orientbench-b-r051-topjournal-joint-response-20260827.md`

回应必须包含：唯一主结论、最强反对论证、唯一主科学命题、一个最小判别实验、精确 controls/data/metrics/pass/kill 条件、JPRS/TGRS 分档。不要只写“补更多实验”。在 C 回应并形成 B/C 可审计共识或明确争议前，不激活服务器下一业务。
