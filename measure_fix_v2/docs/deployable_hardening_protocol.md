# Deployable Hardening 协议（跑前冻结，040）

> SUPERVISOR_APPROVED_040_P3_DEPLOYABLE_HARDENING · measure_fix_v2/ 独立工作区 · P1 frozen 资产只读 · 不改 thresholds/split/formal/frozen tag/claim ledger · 不恢复 P2 · 不补 full matrix · 不追 DOTA mAP · 不重训 host · 不启动 Track A/detector 训练。

## 0. 核心问题
039 Deployable=PARTIAL-PASS 能否升级为 **stable-pass**：无目标域 GT angle-error 标定时，selector 是否可靠优于 score-only 和 score+ar+size linear？

## 1. 数据 / 训练源 / 测试目标
- 复用 measure_fix_v2/artifacts/features/ 的 cached matched feature tables（ar≥1.6 well-defined，P1 frozen split，**不新匹配/不新训练 detector**）。
- cells：PSC #20(DOTA)/#22(DIOR)/#24(FAIR1M)/#23(SODA) + ORCNN #4(SODA)/#3(DIOR) + LSKNet #10(DIOR)。
- **不使用目标域 GT angle-error 训练/调参**（仅用于最终 D_audit 评估）。

## 2. leave-dataset 设置
- 每次 leave one dataset out：训练源 = 其它 datasets 的 PSC cells D_cal；测试 = held-out dataset 的 D_audit。

## 3. leave-detector 设置
- leave one detector family out：PSC→非PSC（ORCNN/LSKNet）、非PSC→PSC。测试 = held-out family 的 D_audit。

## 4. TTA / augmentation consistency proxy（route C）
- 目标：构造**不依赖任何 GT angle-error** 的 deployable proxy。
- 本轮**最小可行 = offline GT-free 一致性 proxy**（local angle-consistency：同图邻近预测的角度离散度），在 4 个代表 cells（FAIR1M PSC、SODA PSC、DIOR ORCNN、DIOR LSKNet）上评估其 NRC（vs GT，仅评估用）。
- 全量 flip/rotation TTA 推理成本高 → 标为 limitation / next-step（本轮不启动大规模 GPU TTA）。

## 5. 评估指标（D_audit）
- NRC-AUC、AURC、Risk@70、Risk@90、p90/p95/p99 after selection（70% cov）、bootstrap CI、oracle gain retained = (NRC_score − NRC_deployed)/(NRC_score − NRC_oracle_within_target)。

## 6. bootstrap
- paired bootstrap 400×（resample D_audit；selector 固定）；DELTA(size_linear − deployed_nl) CI；DELTA(score_only − deployed_nl) CI；CI>0 视为支持。

## 7. 判定规则（跑前冻结）
- **stable-pass（全部满足）**：① unseen cell 中 deployed-nl 显著优于 score+ar+size linear 的比例 **≥75%**；② 平均 retained oracle gain **≥50%**；③ leave-dataset / leave-detector 至少一类达 stable-pass，另一类不得 fail；④ DOTA #20 failure 有明确解释或标为局限；⑤ 不依赖目标域 GT。
- **partial-pass**：多数改善但达不到 stable-pass → P3 仅 deployable candidate，不得称完成。
- **fail**：不能稳定优于 score+ar+size linear → P3 降级 upper-bound/analysis，不做 Track A / detector 训练。

## 8. DOTA #20 failure analysis 计划
- 对比 DOTA #20 vs 其它 cells：样本量；within-target oracle gain（结构强弱）；ar 分布；size 分布；class composition；score↔angle-risk 关系；是否 selector 过拟合其它 datasets。输出诊断表 + 结论（弱结构 vs 分布 shift vs 过拟合）。

## 9. 停止条件
- fail → 停手回报，P3 降级，不启动 Track A / detector 训练。
- 想改 frozen thresholds/split、重训 host、补 full matrix、恢复 P2、启动 Track A/detector 训练 → 停手回报。
