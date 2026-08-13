---
schema_version: 3
actor: C
governance_mode: B_C_PEER_EQUAL
evidence_head: a4f59f5bcdd44aa596b0a76db080276d20a75ebd
evidence_cutoff: 2026-08-13
review_mode: open_postpull_audit
current_route: ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC
learned_eqs_role: APPENDIX_FAILED_ONLY
r022_c_verdict: ADOPT_HONEST_EARLY_STOP_NOT_ADJUDICATED
r023_c_verdict: NUMERIC_DIRECTION_SUPPORTED_POSTPULL_FULL_REPLAY_UNAVAILABLE
r026_c_verdict: REJECT_FORMAL_CONFIRMATION_FAIL_AUDIT_IMPLEMENTATION
r027_c_verdict: REVISE_NOT_SUBMISSION_READY
joint_scientific_state: CONTESTED
current_venue_ceiling: JPRS_POTENTIAL_NOT_READY
current_defensible_level: TGRS_OR_STRONG_JSTARS_AFTER_HONEST_REWRITE
next_required_action: R026_R027_CORRECTIVE_AUDIT_AND_CROSS_MACHINE_BUNDLE
accepted_requires: B_AND_C_TRACEABLE_MATCHING_VERDICTS
cc_recommendation: 'no'
---

# OrientBench C：r022--r027 post-pull 独立裁决

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

先停止新增科学 gate 和新 round 续命。B owner 应关闭 r027 active slot，并签发一次 corrective audit/package revision：

1. 交付跨机器可读取的最小 r026 审计包：matched key/risk/score、10000 bootstrap arrays、point metrics、GT provenance/count/hash、AP parity 与生成代码；
2. validator 必须直接从该包重算 CI/p/Holm/epsilon/swaps/witness/gate；mutation 必须真实调用同一 validator并保存实际非零退出；
3. 修复 r027 manifest、自引用、TTA 定义和 claim checker；
4. 全稿将 DOTA 改称 source-frozen external replication，明确 r025→r026 的揭示顺序；
5. C 在新 bundle 上独立运行后再给 matching verdict。若 B/C 一致，才可把项目升级为 JPRS submission candidate。

若目标是更稳的 JPRS 接收率，纠偏通过后再考虑一个真正未触碰的数据集；它必须是新 target、新预注册且 outcome 未见，不能再用 DOTA/HRSC/Core 重抽续命。
