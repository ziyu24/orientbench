---
schema_version: 3
actor: C
governance_mode: B_C_PEER_EQUAL
evidence_head: 657950ac455d4e98e31240a77de8f223b55e2a5f
evidence_cutoff: 2026-08-13
review_mode: r030_open_attack
current_route: ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC
learned_eqs_role: APPENDIX_FAILED_ONLY
r022_c_verdict: ADOPT_HONEST_EARLY_STOP_NOT_ADJUDICATED
r023_c_verdict: ACCEPT_INFERENCE_LAYER_INCONCLUSIVE_MIXED
r026_c_verdict: AUDITED_EXTERNAL_REPLICATION_ACCEPTED
r027_c_verdict: REVISE_NOT_SUBMISSION_READY
r028_c_verdict: AUDITED_EXTERNAL_REPLICATION_ACCEPTED
r029_c_verdict: ARTIFACT_DELIVERY_ACCEPTED_WITH_REPORT_SCHEMA_DEVIATION
joint_scientific_state: R030_MANUSCRIPT_ASSET_REVIEWABLE_EXECUTION_PROTOCOL_DRIFT
current_venue_ceiling: JPRS_CONDITIONAL_NOT_READY
current_defensible_level: STRONG_JSTARS_OR_REMOTE_SENSING
next_required_action: R031_CIRCULARITY_AND_CLASS_ASSET_PREFLIGHT
accepted_requires: B_AND_C_TRACEABLE_MATCHING_VERDICTS
cc_recommendation: 'no'
---

# OrientBench C：r030 主稿严厉验收与顶刊阻断项

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
