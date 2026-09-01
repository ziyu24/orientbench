# 当前状态

- 阶段：`R002_RISK_AUDIT_COMPLETE`
- 阻塞项：`R014_RAW_RUNTIME_AND_MATCHED_FULLVAL_ASSETS_UNAVAILABLE`。
- 唯一下一步：由 B/C 决定恢复 r014 原始 runtime/matched-fullval 资产，或接受当前不可判定结论。
- 当前科学状态：`INCONCLUSIVE_R002_EVIDENCE_UNAVAILABLE`；不接受现有 `KILL_GR_EQS_METHOD`，不得进入 HRSC/RSAR 或 G2。
- 已确认 r002 缺陷：匹配后直接比较原始 rbox 角，未在 `w<h` 时进行长边 +90° canonicalization；修复版 G1 已仅用已有预测在 CPU 重算。
- 已纳入证据：六单元 compact risk rows、18 组 compact scores、180,000 bootstrap replicates、独立重算和真实语义 mutation tests。
- 未完成的四格：r014 runtime 与 matched_fullval 行资产不在服务器，无法生成 r014-data 三格或 D/E/F 逐 key missing/extra/reassigned 列表；该缺失已写入证据，未作填补或伪造。
- 关键证据：r014 与 r002 的 DIOR-R/A 均为 25080 rows、3497 clusters，但 standalone Risk@90 分别为 0.1384735195 与 1.5517958439；同一 `[0,3]` 风险向量在 90% 精确前缀下任意重排的最大均值差仅 0.3333333333，实际差为 1.4133223243。
- 证据缺口：r002 的实际生成/验证代码、sealed scores、risk rows 和 180000 bootstrap 未进入 Git；D/E/F 的 rows/clusters 也与 r014 不同。
- r001 复核：geometry theta 中位 0.2425237894 rad（13.8956°）超过 0.05 rad（2.8648°）门，足以关闭 CMR；shuffle_class/shuffle_box 比较了不受 foreign q 影响的条件似然字段，二者作废但不改变 geometry 负结论。
- 期刊水平：中科院 2025 地球科学大类二区 JSTARS 对标，尚非 TGRS。
- 状态来源：权威 HTTPS 远端 `main` 的 `8c645b3ddae16dc1fc34626c8a8997364fdf11eb`、r001/r014 生产代码与已提交证据、`coordination/STATE.yaml`。
