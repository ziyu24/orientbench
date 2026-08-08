# OrientBench C：r012 服务器证据裁决与方法线关闭

- round reviewed: `orientbench-c-r012-20260807`
- scientific snapshot: `c101429cebf3454b25bd62c285feffc2fea2e1c3`
- execution base: `ebf8c27eb4ff9c225be920454b7a5f013fbc5099`
- server commit: `d76e3837c43987bfdcf134ceecc5f7ff3ab9f292`
- CC review head: `b959a09c021ade11241aecd970c90060dbbed84f`
- server report: [`orientbench-c-r012-20260807.md`](server_reports/orientbench-c-r012-20260807.md)
- reviewed manuscript: [`orientation_reliability_submission_r012.md`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r012.md)
- server acceptance: **`protocol_drift` overall；其中 `FAIL_PROVENANCE_R012` 科学早停为 `adopt`**
- current venue: **strong-JSTARS potential、尚未 ready；TGRS/ISPRS JPRS 仅在基础事实链修复后重新评估；CVPR/ICCV 当前 EQS 方法线关闭**
- `cc_recommendation: no`：新证据是可直接核验的来源失败与稿件硬错误；先完成 r013 事实修订，再考虑投稿前对抗审查。

## 1. 可采纳的服务器证据

服务器提交的父节点准确为 `ebf8c27...`，变更恰为冻结的25条授权路径，`dis/B.md` blob 保持 `3181a862137918f1dd41677893937c12b3c39c28`，提交内24个非自引用输出的 Git blob bytes/SHA-256 与 manifest 全部一致。未修改 r009/r010/r011 历史资产。

FAIR1M 冻结 val20 有4,362个 image IDs与78,644个 GT；现有 r011 identity/hflip/vflip raw registry 只有3,896个 image rows，identity 为484,332 predictions，缺466个完整 split rows。m069 只留下4,362-image universe与488,194-prediction manifest，没有相应完整 raw dump，无法逐图重算3,862个预测差、建立相同 prediction identity或做无GT三视图 association。按冻结 A0 规则，AP 近似对齐不能替代 universe equality，因此 `FAIL_PROVENANCE_R012` 成立。

SODA 22,994 tiles 到576 mother scenes 的映射为22,994/22,994，unmapped/ambiguous/duplicate 均为0。该通过不能覆盖 FAIR 单元失败。

本轮在 A0 停止，训练、inference、transform smoke、feature build、model fit、target label attach、bootstrap 与 HRSC confirmation 均为0。因此 **没有 EQS 性能结论**；不能把来源失败说成 selector 显著失败或成功。

## 2. 必须修正的服务器表述与实现边界

| 服务器主张 | C 裁决 | 证据与影响 |
|---|---|---|
| `FAIL_PROVENANCE_R012` | `adopt` | FAIR 完整总体硬门被真实原始计数触发，足以停止 Core-6 |
| Core provenance `5/6` | `revise` | FAIR 必败已确定；其它行足以作已有视图身份摘要，但 DIOR 的 `split=fullval` 实际只列5,863行且 expected 由当前 raw 长度导出，不把“5/6”扩写成六单元完整 fullval 法证 |
| 当前 EQS 方法线关闭 | `adopt` | r012 非 PASS 按预注册永久关闭，禁止补一个新 TTA 或换 gate 续命 |
| validator 独立闭合全部来源 | `revise` | 它重读 FAIR live raw 与 split，能复现3,896/4,362；但 `m069_raw_available=false` 在 preflight 中显式设定，validator未独立搜索所有历史 raw |
| 下游实现完整但未运行 | `reject` | 三个入口只是 A0 guard；若 A0 PASS 会直接抛出 `implementation is unavailable`。这不推翻合法早停，但不能称完整方法执行包 |
| “完整投稿稿”已交付 | `reject` | r012 manuscript 仍违反冻结的事实修订要求，见下一节 |

## 3. r012 主稿仍未通过基础事实门

1. §6.5 仍保留被明确要求删除的 instance/tile/mother UCB 数字表（含19,207/2,882与120,925/4,120/417），继续消费已否决的历史认证链。
2. §6.3/§6.4 未明确写出连续风险排序与固定尺寸分箱来自 `D_audit`，仍未解释其 retained n 与 full-validation 容忍角表的估计总体差异。
3. 参考文献仍把2016 RICNN当作 DIOR/DIOR-R来源；没有用 DIOR 基础论文与 AOPG/DIOR-R 一手来源闭合。
4. PSC 参考文献仍写成 `Yu Y, Yang X, Li Q, et al.`，没有修为官方论文的 Yi Yu、Feipeng Da。
5. validator只查禁用 token 与7条 ledger claim，不检查上述四项，因此其通过不能证明投稿事实链合格。

已修复项包括 FAIR本地18,505/4,362划分、DOTA NRC 0.7544/0.7113、leave-dataset 0/6与可识别 leave-detector 4/5分层、固定剂量 descriptive-only 和内部 gate token 删除；这些修复保留。

## 4. 科学与投稿裁决

- 旧 target-GT geometry 仍仅是 diagnostic upper bound；旧 leave-dataset 0/6 是负迁移事实。
- r012 没有评价 EQS，不能以性能失败写摘要；但按预注册非通过规则，当前顶会方法线已关闭，不再重跑或换候选。
- measurement→diagnose 稿仍有可发表价值，但在上述事实链修正与一次投稿级对抗审查之前，只能定位为 strong-JSTARS potential、尚未 ready。
- TGRS/ISPRS JPRS 的真实可达性留待 r013 事实修订稿；不得靠措辞把来源失败升级为方法贡献。

## 5. 唯一下一步

执行 r013 **manuscript-only foundation repair**：不训练、不推理、不复算统计、不重开 EQS，只删除无效 UCB、披露 D_audit、修正 PSC 与 DIOR-R/AOPG 一手引用，并以可执行 validator 锁定。通过后再决定是否进行 CC 投稿前攻击。

## 6. 决策台账

| item | decision | confidence | falsifier / next action |
|---|---|---:|---|
| FAIR full-universe provenance | adopt FAIL | high | 若出现与4,362 rows绑定且可逐图复算的既有 identity raw，需作为新证据而非回改 r012 |
| SODA mother map | adopt PASS | high | 任一 tile 多映射或缺映射会推翻 |
| EQS performance | not evaluated | high | r012 无 fit/label/bootstrap；禁止写正负性能 |
| r012 method route | close | high | 预注册已规定 non-PASS 关闭，不以新 gate 复活 |
| r012 manuscript | reject as submission draft | high | r013 四项硬修全部通过才可升级 |
| next work | r013 manuscript-only repair | high | 只处理事实链，不生成新科学数字 |
