# 主要失败路线

## COI / 干预式轴向可辨识响应（r004）

- 状态：r005 已以同一 global theta-free matcher 完成 correction-only 复核，当前仍是
  `INCONCLUSIVE_R004_PROTOCOL_VALIDITY`，不是正式失败路线。
- 已核实：16 个 split×detector×condition 独立复算的 key 差集为 0、逐行最大绝对差为 0；八个
  test `DeltaY` 点估计都不大于 0.02，最大 0.017158，且八个非坍塌界限均通过。
- 未成立的前提：真实 HRSC G/P/N Holm-32 中八个 `clean-high>0.20` 格（J_eff/M15、两模型、
  两 corruption）均失败；这属于前三类操纵失败，不能转写为 KILL 或失败路线。
- B 独立复算已确认上述八个点估计，但 N 臂 noise scale 未统一复用 clean-G，ORCNN bootstrap
  又在 434 张有对象图的点估计外加入零填充图并使用 437 分母；相关 envelope、CI 与 p 不得
  作为正向证据。这些缺陷不改变保守的 inconclusive token。
- 禁止重入：不得以重推理、重选 test 剂量、删除对象、pooled/global 平均、替换 detector family
  或降低标准化效应阈值来挽救或关闭该路线。

## CMR

- 状态：关闭。
- 触发事实：r001 geometry theta中位`0.2425237894 rad`超过`0.05 rad`门。
- 证据限制：shuffle_class与shuffle_box作废，但不改变geometry负门。
- 禁止重入：不得换shuffle字段、阈值或措辞继续同一条件混合路线。

## GR-EQS

- 状态：负向冻结，不是正式KILL。
- 触发事实：三个数据集风险非劣均失败；18组`lambda=0`，fusion与raw恒等；正式r002又因
  FAIR1M-D cohort从15199/1231漂移到15148/1222而`FAILED_ACCEPTANCE`。
- 证据限制：不能把缺失的51行补写，也不能外推为所有风险控制无效。
- 禁止重入：不得换数据、缩cohort或修改gate挽救同一融合定义。

## 已消费的历史路线

项目历史已经将Q-SetOD、OER、SAUR、AHC、P2C、CORA与PEF列为失败或已消费路线；其中
Q-SetOD的r037集合门没有witness。精确代码、指标和裁决从`doc/ARCHIVE.md`登记的父提交读取。
后续不得只换名称、阈值、数据子集或追加同类消融重新进入；新候选必须改变核心可观测量、
干预或推断对象。

PSC 的 H1/H3 局部解码/调制响应只保留为 bounded mechanism evidence；更晚权威重审在外部
RotatedFCOS-PSCD 上得到 0/24 候选同时胜过 phase modulation 与 detection score，并给出
`FAIL_CANDIDATE_GATE / STOP_B6`。不得把 unit phase、独立 concentration、axial von-Mises
或 AQE-like quality branch 重新包装成 B6 repair；除非未来提出改变推断对象且能正面超过同预算
VM-NLL/AQE 强基线的新机制，否则这条 repair 路线保持停止。

外部专家全量复审后，所有以“比 detection score 多赢一点”为目标的小型 selector、额外角度
quality head、TTA 标量融合及仅换相似 OBB 数据集的增量实验统一停止。后续不得换名恢复这些
路线；未来唯一允许验证的是既有方向误差是否造成独立下游决策损失，以及直接的方向扰动是否
能识别该决策风险，不得扩展为新的角误差预测器菜单。

## 非失败项

AIRO/COI的r003从未执行，不能写入失败路线。它仅作为`lab/discussion.md`中的未决候选保留。

r006 为 `INCONCLUSIVE_R006_EXECUTION_VALIDITY`，不是 TAL 科学失败。ORCNN stride 8 的 y 轴
若干 shift 未达到冻结总体 90% 保留率，因此不得改变执行门或重开同一 HRSC official test；其
结果也不得外推为不存在任何 translation-to-angle leakage。

r007 已只读确认主机固定数据根不存在 RSDD-SAR 与 SAR-AIRcraft 候选，状态为
`ASSET_UNAVAILABLE_R007`。这是资产不可用，不是 SAR 科学失败；本项目内暂停 SAR。若未来
恢复，必须作为独立的传感器物理问题重新立项，不能直接重跑原 r007。

## r010 更正：不是失败路线

旧 `ASSET_UNAVAILABLE_R010` 的 component 理由已撤销。官方 metadata CSV 有 26 行 raw `cat_id`
被科学计数法破坏，直接使用后把无关地点伪合并；经 `image_id` 后缀、GeoJSON CAT 与影像键三方
约束的规范恢复后，footprint 合并前为 102 个 component，而非 83。旧 split 及“83<100 已关闭
RarePlanes”的表述全部失效。

当前状态为 `INCONCLUSIVE_R010_ASSET_AUDIT_INVALID`：真实 COG footprint 合并、对象 lineage、
模型 config/build/state-dict 兼容性和独立验证仍未闭合。FRED 也尚未形成合格的独立资产结论。
因此本项既不是方法失败，也不授权训练或最终验证；只能由 r011 做一次不读取科学 outcome 的证据链
修复。不得通过换 seed、拆 component、替代模型或改类别门来制造 READY。

## r011 资产阻断（非科学失败）

r011 已修复 r010 的 CAT/COG/lineage/分割证据链，数据门通过；但实际模型 build/load 仍被三项
可复核的资产条件阻断：ARS-DETR 的 MMCV 1.7.2 与其 `<=1.6.0` 要求冲突，O2-RTDETR 的 MMCV
2.3.4 与 bundled mmrotate 1.0.0rc1 的 `<=2.2.0` 要求冲突，FRED 无可用的官方实现及合法初始化。
唯一状态为 `ASSET_UNAVAILABLE_R011`，不是方法失败或正式 KILL。不得用替代实现、代理模型或下载外部
资产绕开该结论；在新的明确授权前不得启动任何性能实验。
