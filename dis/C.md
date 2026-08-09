# OrientBench C：r018 最终验收与 CC 投稿碰撞启动

- review date: `2026-08-09`
- evidence cutoff: `8ce84331a14c12a5ac41e46cb354ca712286626e`
- r018 control parent: `40679c9e3a5a94de61f4e078e1fad437b2b461b7`
- r018 scientific base: `b349dcbd44685eae66bdabbdf7a795493ccdc08e`
- r018 report: [`orientbench-c-r018-20260808.md`](server_reports/orientbench-c-r018-20260808.md)
- archived r018 instruction: [`orientbench-c-r018-20260808-server-returned.md`](sug/orientbench-c-r018-20260808-server-returned.md)
- server status: `NO_ACTIVE_SERVER_TASK`
- CC round: `orientbench-cc-post-r018-20260809`
- CC status: `READY_FOR_CC_STAGE_1`
- CC review base: `48a770327919aaf3270f802962501689a969653d`
- overall r018 acceptance: **执行轨迹采纳；`VALID_STATIC_ADJUDICATION_R018` 拒绝，正式记为 `PROTOCOL_DRIFT_R018 / FAIL_AUDIT_IMPLEMENTATION_R018`**
- numeric acceptance: **`EXPLORATORY_CORE_SUPPORT_R015`**
- current venue ceiling: **strong-JSTARS potential、尚未 ready；TGRS/ISPRS JPRS 转入投稿级贡献攻击；CVPR/ICCV 不成立**
- `cc_recommendation: recommended_now`；`cc_authorization: user_authorized`：用户已明确授权，按 `dis/B_START_PROMPT.md` 立即启动两阶段投稿级对抗审查。

## 1. “执行完毕”与“结果通过”

r018 服务器确实完整运行 Phase A–C、生成精确 10 项授权产物、单 commit 并通过 HTTPS 推送。远端 `main`、本地 HEAD 均为 `8ce84331...`，工作树干净；因此它**不是早停**，也不是 EQS 性能失败。

但 r018 收据自身仍没有忠实实现预注册验证，故 `FULL_COMPLETION` 只适用于执行轨迹，不能推出 `VALID_STATIC_ADJUDICATION_R018`。正式分层为：

- execution trace：`FULL_COMPLETION`，采纳；
- receipt fidelity：`PROTOCOL_DRIFT_R018 / FAIL_AUDIT_IMPLEMENTATION_R018`；
- scientific performance：未出现新性能失败；
- numeric evidence：保留高置信探索性，不升级为 confirmatory/deployable。

## 2. 可采纳证据

### 2.1 Git 与 provenance

- `8ce84331...` 是 `40679c9e...` 后恰好一个 commit，精确 10 条授权路径；唯一 r018 报告存在；`dis/B.md` 父/子 blob 均为 `3181a862137918f1dd41677893937c12b3c39c28`。
- manifest 含 10 个 tracked outputs、35 个 actual inputs、3 个 executed-code records、12 个 r017 Git blobs、9 个 output-hash reads、0 个 runtime outputs；self 明确为 `N/A_SELF_REFERENCE`。
- r017 manifest/validator 的 47 条记录按 path、bytes、SHA256、schema、read_only 全字段一致；12 个 r017 非 self blobs 与 Git 匹配。
- frozen input snapshot SHA `1b4b61e45361ece2006275b8d8a50321c7c6b9ac9d758ec8c2f37c574c951018` 在 manifest/provenance/validator 一致；9 个 r018 非 self 输出与最终 Git blobs 匹配。

### 2.2 当前正向数值分支

- 既有 bootstrap 恰为 9,000 行，九个 `(level,key,dataset)` 三元组各覆盖 replicate `0..999`，无额外、缺失、重复或非有限值；故意错 dataset 负例可被检测。
- support 确实从 `Delta_NRC>=0.02`、CI lower>0、Holm<0.05 重算为 unit 6/6、dataset 3/3，覆盖三数据集、三 detector families，FAIR unit D 支持；冻结 gate 全条件一致。
- r016 summary 缺少的 audit rows、cluster count/SHA、bootstrap reps、detector metadata 被标为 `SOURCE_FIELD_ABSENT / RECONSTRUCTED_NOT_SUMMARY_COMPARED`，没有冒充已比较。
- 六个 canonical source/forbidden/intersection 集合保存 count 与 sorted SHA，当前交集均为零。

### 2.3 稿件索引的实际内容

独立复核确认当前 claim ledger 8/8 hash、唯一正文命中与标题绑定通过；novelty matrix 的弱根页均为 `UNKNOWN_EXCLUDED`；稿件 exploratory、HRSC 跨零、leave-dataset 0/6、fixed-dose descriptive-only、旧 CI/UCB 排除和核心引用边界仍成立。r018 没有修改稿件。

## 3. 拒绝 VALID 收据的决定性证据

1. **错误的冻结期望。** r012 冻结指令明确规定 association margin“只有一个候选时为 1，无候选时为 0”；r018 脚本却把单候选 expected 写成 0，并用 perfect-IoU actual=1 制造假失败。该项不是 implementation deviation。
2. **混淆两个 feature。** 冻结契约把 doubled-angle axial circular dispersion 与 `u_axis` 并列为两个量。r018 用 `u_axis` 的 actual 对比无来源的 `0.05` 来代替 axial-dispersion 测试；实际六个 sealed feature schema 均没有独立 axial-dispersion 字段。真实偏差是“独立 axial feature 缺失”，不是该 `u_axis` 数值测试。
3. **w/h+90 测试没有覆盖角行为。** 它只比较 `log_pred_ar`，未验证等价框的 angle/`u_axis` 行为；该边界保持 `unknown`。
4. **VALID 没有门控 Phase B 审计质量。** `phase_b_complete` 被无条件写为 true，`receipt_valid` 也不要求 schema/seal/claim/novelty/manuscript 检查有效；即使 Phase B 关键检查失败仍可签 VALID。production contract 可得到负结果，但审计器本身必须正确，这两者被混淆。
5. **负结果完成语义仍写反。** 合约规定被审计对象的 numeric/gate mismatch 可与有效收据并存；实际 `receipt_valid` 直接依赖 `numeric_ok`，负数字分支会错误返回 `FAIL_VALIDATION_R018`。
6. **canonical parity witness 不完整。** 收据只登记 `m069_common.py` 的 MD5 摘要行，漏掉下一行真正定义 `%2` parity 的分支，却签发完整 witness。

因此报告中的 `feature_contract_result=IMPLEMENTATION_DEVIATION` 方向上仍有一个真实依据，但列出的两个失败项只有“独立 doubled-angle axial feature 未实现”成立；single-candidate margin 失败必须撤销。缺必做动态验证且仍签 VALID，满足 r018 自身定义的 protocol drift。

## 4. 对科学 claim 的影响

- 当前 6/6、3/3 来自实际 sealed features/scores，故经验性探索结果不因意图契约缺项而消失；但它只描述**实际实现的 selector**。
- 不得宣称实现了完整 r012 frozen feature contract，不得用 doubled-angle axial dispersion 解释收益；w/h+90 的角等价性仍未知。
- 当前主稿只把 EQS 写成探索性预测等变性信号，没有消费上述细粒度机制，因此不需要在本轮仓促改稿；投稿方法节必须按实际 schema/代码重写或明确限制。
- r014 formal failure、HRSC `0.0602` 且 CI `[-0.0143,0.1438]` 跨零、leave-dataset 0/6、fixed-dose descriptive-only 均不变。CVPR/ICCV 路线继续关闭。

## 5. 投稿候选与最小杀死条件

```text
candidate:
  problem: 面向遥感 OBB 的 orientation reliability 测量、诊断与受限选择
  material_delta: 以 NRC/risk-coverage、跨 detector/dataset 诊断和实际 sealed EQS 探索证据连接 measure→diagnose→fix，但不宣称 deployable 或完整 frozen feature contract
  minimum_decisive_test: 一次投稿级对抗审查，逐条攻击贡献显著性、最近工作差异、实际实现边界、负迁移与外部不确定性
  kill_condition: 去掉 deployability、HRSC 确认和缺失 axial feature 后，若剩余贡献仅是治理流程或已有 calibration/selective-prediction 的重包装，则降为 strong-JSTARS/benchmark
  expected_paper_value: 通过攻击才保留 TGRS/ISPRS JPRS；否则采用 strong-JSTARS fallback
```

本轮采用三个视角：统计/gate、实现/provenance、稿件/创新。当前集体盲区不是更多 hash，而是审稿人是否认可实际科学贡献和读者价值。审计事实置信度高；TGRS/ISPRS 可达性置信度中等，最弱环节是贡献攻击尚未发生。

## 6. 唯一下一步

服务器机械验收循环保持关闭，不生成 r019。用户已经授权；当前唯一下一步是 CC/B 按 `dis/B_START_PROMPT.md` 先完成并推送阶段一独立盲审，再读取 C 完成阶段二对抗复核。C 等待 `dis/B.md` 两个独立 commit，不触碰该文件。

## 7. 决策台账

| item | decision | confidence | falsifier / next action |
|---|---|---:|---|
| r018 execution trace | adopt FULL_COMPLETION | high | 远端、父链、10 路径或 push 反证可推翻 |
| r018 Git/provenance | adopt | high | 任一最终 blob/snapshot/full-record 不一致可推翻 |
| r018 VALID receipt | reject as protocol drift | high | 多项冻结契约和动态 gate 实现反证已定位 |
| exploratory 6/6 + 3/3 | adopt for actual sealed implementation | high | 原始数值或同步 bootstrap 反证可降级 |
| single-candidate margin deviation | reject | high | 冻结契约明确 expected=1 |
| missing doubled-angle axial feature | adopt implementation deviation | high | actual sealed schema/生成代码出现独立 axial 字段可推翻 |
| w/h+90 angle equivalence | unknown | medium | 需正确调用 production angle path 的微测试 |
| current paper index | adopt | high | 投稿攻击发现 claim/novelty/边界错误则修订 |
| next work | authorized CC stage 1 then stage 2 | high | 两阶段必须分别只提交并推送 `dis/B.md`；不下发 r019 |
