# r018 静态验收终结裁决

## 裁决

r018 独立收据有效，裁决为 `VALID_STATIC_ADJUDICATION_R018`。该 token 只表示本轮静态验收忠实、完整、可复核，不改变 r017 的历史状态：`PROTOCOL_DRIFT_R017 / FAIL_AUDIT_IMPLEMENTATION_R017`。数值证据仍仅采纳为 `EXPLORATORY_CORE_SUPPORT_R015`，不是 confirmatory、deployable 或 venue 结论。

## 数值与来源

- 既有 9,000 行 bootstrap 逐行按 `(level,key,dataset)` 三元组核验；九个合法三元组各含 `0..999`，无缺失、重复、额外、dataset 错配或非有限值。内置错误 dataset 负例被检测。
- support 由 `Delta NRC >= 0.02`、CI 下界大于零、Holm p 小于 0.05 重新计算，不信任旧布尔列。结果为 unit 6/6、dataset 3/3，冻结 gate 全字段一致。
- r016 summary 的 point、CI、p、Holm、support 与 r015 一致。summary 未提供 audit rows、cluster count/SHA、bootstrap reps 和 detector metadata，逐字段记录为 `SOURCE_FIELD_ABSENT`；r015 补充值仅标为 `RECONSTRUCTED_NOT_SUMMARY_COMPARED`。
- canonical MD5 parity 源码位置、六个 target 的 source/forbidden/intersection count 与 sorted SHA 已保存；交集均为零。`R015_SET_AUDIT_ROLE_DRIFT` 保留。

## Feature contract

六单元的 12 个 feature/score Parquet 均保存完整 Arrow schema，禁字段 prefix/contains 扫描通过，prelabel/final seal 的 bytes 与 SHA 均一致。所有行为测试动态调用 r014 production code path。

冻结 sentinel `(3,1,3,3,3,10,0)` 源码与微测试一致，r017 对 sentinel 的负分类被纠正。实际仍有两项实现偏差：单候选 association margin 返回 `1.0` 而非冻结期望 `0.0`；production feature 未实现 doubled-angle axial dispersion，边界合成例的 `u_axis` 为 `3.0` 而非期望 `0.05`。因此 `feature_contract_result=IMPLEMENTATION_DEVIATION`，但该诚实负结果不使 r018 收据失效。

claim ledger 8/8 的文本 SHA、正文唯一命中及最近标题均一致；novelty 的弱来源均保持 `UNKNOWN_EXCLUDED`；正文的探索性、HRSC 跨零、leave-dataset 0/6、fixed-dose descriptive-only、旧数值、内部术语和引用扫描通过。

## Provenance

r017 manifest 与 validator 的 47 条只读输入已按 path、bytes、SHA256、schema、read_only 全字段比较，无差异。Git blob 复核确认 r017 单 commit、父节点、精确 13 条路径、唯一报告、12 个非自引用输出与 manifest 一致；`dis/B.md` 只比较父/子 blob OID，未读取内容。所有读取归入四个互斥类别，输入快照 SHA 同时写入 validator 和 manifest。manifest 最后生成，自引用明确为 `N/A_SELF_REFERENCE`。

本轮未重跑 bootstrap，未训练、推理、重拟合、重打分或修改稿件；无 GPU、pool 或伪资源遥测。
