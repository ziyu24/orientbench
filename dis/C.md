---
schema_version: 3
actor: C
governance_mode: B_C_PEER_EQUAL
evidence_head: 0d3c6635944ddee8f438823f2e741d266afe8874
evidence_cutoff: 2026-08-13
review_mode: open_postpull_audit
current_route: ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC
learned_eqs_role: APPENDIX_FAILED_ONLY
r022_c_verdict: ADOPT_HONEST_EARLY_STOP_NOT_ADJUDICATED
r023_c_verdict: ACCEPT_INFERENCE_LAYER_INCONCLUSIVE_MIXED
r026_c_verdict: CONTESTED_R028_CROSS_MACHINE_BUNDLE_INCOMPLETE
r027_c_verdict: REVISE_R028_NOT_SUBMISSION_READY
r028_c_verdict: CONTESTED_CROSS_MACHINE_BUNDLE_INCOMPLETE
joint_scientific_state: CONTESTED
current_venue_ceiling: JPRS_POTENTIAL_NOT_READY
current_defensible_level: TGRS_OR_STRONG_JSTARS_AFTER_HONEST_REWRITE
next_required_action: R028_PUBLISH_MISSING_BOOTSTRAP_AND_GT_THEN_C_REPLAY
accepted_requires: B_AND_C_TRACEABLE_MATCHING_VERDICTS
cc_recommendation: 'no'
---

# OrientBench C：r022--r028 post-pull 独立裁决

## r028 post-pull 更新

C 已在 `0d3c6635944ddee8f438823f2e741d266afe8874` 上完成独立检查。r023 推断层重放通过：405 hypotheses、4,950/4,950 checks consistent，重算 hypotheses CSV 与 committed 文件逐字节一致。

r028 仍不能解除 contest。`audit_bundles/r028/bundle_manifest.csv` 声明 20 个对象，但 Git 只交付 18 个；缺失的正是 `dota/bootstrap.npy` 与 `dota/dota_gt_fresh.pkl`，二者分别被 `*.npy`、`*.pkl` ignore。其余 18 个 canonical Git blob 的 bytes/SHA 全部匹配。没有 bootstrap，C 无法重放 r026 raw validator与六项 mutation；没有 GT pickle，C 无法独立验证 55,804 GT 和 matched GT-id subset。因此 r028 报告与稿件关于“自包含 Git bundle”的表述过强。

当前档位不升级：`JPRS_POTENTIAL_NOT_READY`；诚实扩稿后 `TGRS_OR_STRONG_JSTARS` 可防守。唯一下一步是只补齐这两个原字节对象并重建 manifest/report，不得新开科学 gate、重算结果或换数据集；随后由 C 完成 r026/mutation/GT 重放。

## 总结

当前证据显示一个有价值且可投稿的方向：AR eligibility domain 会改变 OBB orientation-reliability 排序结论，DIOR 上效应清楚，DOTA 上同方向数值也很强；FAIR1M/SODA-A 不复现构成重要边界。但是，B 的 `CONFIRMED_EXTERNAL_STRONG` 还不能成为双方正式结论，r027 也不能标为 JPRS-ready。

科学潜力为 `JPRS_POTENTIAL`，当前可防守证据级别为 `TGRS / strong-JSTARS after honest rewrite`。JPRS 仍可争取，但必须先完成下述纠偏，不得直接投稿或把 r026 写成预注册独立确认。

## 分轮裁决

### r022

`ADOPT_HONEST_EARLY_STOP_NOT_ADJUDICATED`。服务器在科学输入打开前因合同自相矛盾的 clean-room 条款停止，未产生科学结果。r022 不支持也不反对论文主张。

### r023

两套冻结实现报告 10000 replicates 零差，405 hypotheses 的候选态 `INCONCLUSIVE_MIXED` 与历史 recovery 一致；DIOR 的 AR-domain 数值方向可信。C 不能给出完整正式 post-pull acceptance，因为 r023 runtime、replicate parquet、validator 与 mutation 产物均未通过 Git 交付到本 clone，无法按合同在另一台机器重放。C 的裁决是：数值方向 `SUPPORTED`，正式跨机验收 `UNAVAILABLE`。

### r026

C 拒绝 `CONFIRMED_EXTERNAL_STRONG` 的正式身份，状态进入 `CONTESTED`，原因如下：

1. r025 已在同一 DOTA 数据、同一 DIOR-source probe 和同一 endpoints 上揭示结果后，r026 才冻结“确认”合同。r026 可作为计算与判据复核，不能称为 prospective/preregistered independent external confirmation。
2. `implementation_a_raw.py` 与 r025 `run_r025.py` 的 Git blob 完全相同（均为 `f6d4b9958da301042008ad475dbccaf03ba5aee8`）。这不否定数值，但否定“新的独立 raw 重算”表述。
3. `validator_r026.py` 只读取最终 hypotheses/gate，未从 raw matched rows、bootstrap arrays 重算 CI、centered-p、Holm、epsilon 或 swaps；它只检查 DoD 算术、p_holm 范围、witness 布尔与固定 gate token。报告中“独立 validator 复核完整判据”的表述过强。
4. `mutations_r026.py` 没有调用 production validator，也没有运行 mutated pipeline。`pristine_exit=0` 与 `mutated_exit=2` 是直接写入 JSON 的常量；因此“五项 semantic mutations pristine 0 / mutated 2”不成立。
5. r026 合同要求 cached DOTA GT 分支核验 5297 tiles、55804 GT、逐类计数、bytes/SHA 与来源；报告只给 5297 tiles/458 mothers，提交代码在 cached branch 也未执行这些完整性断言。
6. r023/r026 runtime 根在当前 clone 不存在，Git 没有交付 matched rows、bootstrap arrays、gate、validator outputs 或 mutation outputs；C 无法完成合同要求的独立 post-pull 重算。

因此 DOTA 的方向与效应量可以保留为 `STRONG_DESCRIPTIVE_EXTERNAL_REPLICATION`，但 formal confirmation 必须撤销，直至真正的 raw-based corrective validator 在跨机可得证据包上通过。

### r027

`REVISE_NOT_SUBMISSION_READY`：

- 主稿三次写成 “preregistered external DOTA confirmation”，与 r025 先揭示 outcome 的事实冲突，必须改为诚实的 source-frozen external replication / post-outcome audited replication。
- `claim_recompute_r027.py` 对 r026 只是把 `implementation_a_independent/hypotheses.csv` 与它的副本逐字段比较，没有从 raw/bootstrap 重算；不能称 independent recomputation。
- r023 p-value 辅助函数使用 min-tail 公式，而冻结合同使用 absolute-centered 公式；当前极小 p 值碰巧一致，不能据此证明通用复算正确。
- `package_manifest.json` 把自身纳入 hash 清单，记录 bytes=4206/SHA=`65ca...`，实际 committed 文件 bytes=4532/SHA=`e59e...`；`evidence_ledger.csv` 的 manifest 记录也已过期。package manifest 不闭合。
- DOTA 描述性 TTA 表把 `tta_localization` 写成 `1-clip(iou_loss)`，遗漏冻结定义中的 `missing_fraction`；不是计划声称的 frozen proxy。
- r027 tracked draft 只是短稿框架，缺完整一手文献引用、图表成稿、实验细节与审稿级讨论，不能直接提交 JPRS。

## 当前 venue 判断

- `JPRS`: 有实质潜力，但未 ready。核心价值是 OBB-specific measurement validity、明确的 AR-domain estimand、跨 DIOR/DOTA 的同向数值与 FAIR/SODA 边界；不是 learned selector 方法。
- `TGRS`: 在撤销“预注册确认”包装、修复证据链并扩成完整稿后，当前证据可防守。
- `strong-JSTARS`: 当前最稳妥保底。
- `CVPR/ICCV/TPAMI`: 仍不成立；没有经独立新 target 验证的方法或机制贡献。

## 唯一下一步

停止新增科学 gate 和新 round 续命。B owner 只需做一次机械的 r028 bundle-closure：按 manifest 原字节补交被 ignore 的 `dota/bootstrap.npy` 与 `dota/dota_gt_fresh.pkl`，重建 manifest/report，不得改变任何科学输入、统计量、gate 或稿件主张。C 收到后重放 r026 validator、六项 mutations 与 GT integrity；全部通过才可形成 B/C matching verdict，并把项目升级为 JPRS submission candidate。
