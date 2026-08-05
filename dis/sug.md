# OrientBench 服务器任务：B5 负结论证据链收口

- round: `orientbench-c-r002-20260805`
- scientific snapshot: `8466602330a942c9bb8beff284aa8fc5b952a3b0`
- 前轮报告: `dis/server_reports/orientbench-c-r001-20260805.md`
- 唯一服务器报告路径: `dis/server_reports/orientbench-c-r002-20260805.md`
- 已冻结科学裁决: B=`FAIL_CANDIDATE_GATE`，B6/B7=`STOPPED_NOT_RUN`。

## 1. 单一科学问题

在不训练、不推理、不改变 candidate、endpoint、数据、seed、阈值和既有科学数字的前提下，能否把 r001 的 B3/B4/B5 负结论证据包修补到 publication-grade provenance：所有直接输入均锁定、九个 B3 cache 均可由 raw 输入确定性核验、同一 finite mask 贯穿点估计与 bootstrap、gate 不再混淆 development/confirmatory 数据或暗含未注册成功规则？

本轮只做 evidence-only 收口。不得恢复 B6，不得寻找新 score/seed/threshold/endpoint，不得修改 A 主稿，不得克隆或下载 D7/PCP-OBB、pcbobb、pcbobb_beyond、pcbobb_score_study。

## 2. 前置门

1. 只允许 fast-forward 同步；记录实际完整 HEAD，并证明其 ancestry 包含 scientific snapshot `8466602330a942c9bb8beff284aa8fc5b952a3b0`。工作树不洁净、规则冲突或不能 fast-forward 时停止。
2. 核对 r001 唯一报告、四张 CSV、manifest、两份脚本及其 Git blob/canonical SHA。旧文件必须保持逐字节不变。
3. 核对服务器原有 10 个 split、275 个 persistent-artifact 文件、B3/B4 raw dumps、九个 B3 cache、三份 B4 external manifest/evaluator/matched 文件及 checkpoint。不得重新训练、重新推理或静默替换资产。
4. 两个先前漏记的直接输入必须按 canonical bytes 精确匹配：
   - `top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json`: `80d86a5f72e70405fe4a49db87aad61e6aea20a26af0ad1c5745bfd646d1e5cb`；
   - `top_journal_v3_reaudit_055/shared_forensics/g0/reports/g0_comparison_manifest.csv`: `e038aed06b3aff86818c8663657f074798e90de867ab48ac9d2821c61c191a86`。

任何前置项失败都早停为 `INCONCLUSIVE_PROVENANCE`；`STOP_B6` 保持不变。

## 3. 固定协议

1. 新增 r002 脚本和产物；不得覆盖、删除或格式化任何 r001/冻结文件。候选、endpoint、score 方向、stable tie、cluster unit、seed 和 800 次 paired resample 均保持 r001 不变。
2. manifest 必须记录执行过程中每一个实际打开的输入：相对路径、canonical/raw SHA-256、bytes、用途；不能只列“认为重要”的输入。记录执行源码和测试源码的 Git blob/canonical SHA。科学快照与执行 HEAD 分字段记录；不得用自引用的 result commit 承诺 bitwise 稳定。
3. 对九个 B3 cache 生成 raw→cache lineage。每个 cache 至少记录：raw 源路径/哈希、cache 路径/哈希、key、dtype、shape、行序/实例 ID hash、每个数组的 canonical content hash。必须从 raw 重新构造用于 NRC 的数组并逐元素核验；浮点派生值要求明确的算法与容差，不能仅用行数或压缩文件字节相等代替内容证明。无法确定性重构即 `INCONCLUSIVE_PROVENANCE`。
4. 为 `outputs/persistent_artifacts/` 的 275 个文件生成 path+bytes+SHA-256 inventory 及 aggregate hash。该 inventory 用于冻结今后复算边界；不能把“文件数为 275”写成内容完整性的充分条件。
5. candidate、phase_mod、detection_score 与 endpoint 必须先形成同一个 common finite mask；点估计和所有 bootstrap replicate 只能在同一 mask/universe 上计算。逐单元报告原始行数、剔除数和剔除原因。若 r001 当前单元确为全量 finite，r002 数字应保持不变。
6. `bootstrap_nrc()` 或等价实现必须遍历传入 multiplicity matrix 的实际长度，不得读取全局 `REPLICATES=800` 控制循环。新增非 800 replicate 的回归测试。
7. B1 冻结协议中的 development 只包括 DIOR-R 与 SODA-A；FAIR1M-v1.0 单列为 confirmatory，DOTA/RotatedFCOS 单列为 external。由于旧协议未预注册“4 candidates × 2 endpoints × 多 seed”的 multiplicity/FWER 成功规则，本轮不得新造一个可放行的成功门；只透明列出逐比较证据并保留外部 `0/24` 导致的 `FAIL_CANDIDATE_GATE`。任何未来 PASS 必须在新轮次事先冻结规则。
8. 检测完全重复的 candidate×endpoint 结果并在报告中标为 redundant comparison；不把重复行当成独立支持。
9. 运行正式测试和随机显式展开测试：weighted NRC、oracle/random 权重一致性、stable ties、NaN/common mask、37-replicate 输入、paired resample、candidate duplication、machine-derived final verdict。

## 4. 授权写入范围

服务器只可新增或修改以下本轮文件：

- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/reaudit_b3_b4_r002.py`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/test_b3_b4_reaudit_r002.py`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b3_b4_input_lineage_r002.csv`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b3_b4_persistent_asset_inventory_r002.csv`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b3_candidate_cluster_bootstrap_reaudit_r002.csv`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b4_candidate_external_bootstrap_reaudit_r002.csv`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b5_gate_reaudit_r002.csv`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b3_b4_estimand_equivalence_tests_r002.csv`
- `top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b3_b4_reaudit_manifest_r002.json`
- `dis/server_reports/orientbench-c-r002-20260805.md`

不得触碰 `dis/B.md`，不得修改旧冻结输出、旧 r001 脚本/报告、数据、split、checkpoint、配置或主稿。若需要上述清单以外的路径，停止并在唯一报告中说明，不自行扩权。

## 5. 必须报告的证据

1. r001 文件逐字节未变的哈希核对表。
2. 所有 direct input 及其用途；特别是两项漏记输入的精确哈希。
3. 九个 B3 cache 的 raw→cache lineage 结论和逐单元失败原因（如有）。
4. 275 文件 inventory 的 aggregate hash、总 bytes、重复/缺失/悬空链接情况。
5. common finite mask 的逐单元行数与剔除数。
6. 正式与随机测试数量、seed、最大绝对误差；必须包含 37-replicate 与 NaN 测试。
7. r002 对 r001 的逐列数值 diff。除新增 provenance/gate 标签字段外，NRC、paired delta、CI、universe/resample hash 和外部 `0/24` 应不变；浮点容差至多 `1e-12`。
8. 由数据计算出的 gate；development、confirmatory、external 分列，重复候选标记，不得硬编码 final verdict。
9. 训练次数 `0`、推理次数 `0`、是否读取任何旧项目结果（必须为否）。

## 6. Pass / fail / inconclusive gate

- `PASS_EVIDENCE_CLOSURE`：所有 direct input 已锁定；九个 cache 的 lineage 全部通过；275 文件 inventory 已冻结；测试全过；r002 与 r001 科学数字在 `1e-12` 内一致；external support 仍为 `0/24`；机器 gate 仍为 `FAIL_CANDIDATE_GATE`；旧文件均未变化。该状态只表示负结论证据链收口，不授权 B6。
- `FAIL_EVIDENCE_DRIFT`：修补 finite mask、lineage 或 gate 后，任何科学数字、universe、resample 或外部裁决发生无法解释的变化，或发现 cache 与 raw 不一致。立即停止；保持 `STOP_B6`，列出首个漂移位置。
- `INCONCLUSIVE_PROVENANCE`：缺少原始资产、权限、哈希、lineage 算法、确定性重构条件，或无法证明旧文件未变。立即停止；不得把行数检查包装成 provenance pass。

早停顺序：Git/所有权 → 旧文件不变 → direct-input hash → raw→cache lineage → common-mask/tests → r001/r002 数值 diff → machine gate。没有新证据即停止，不增加事后实验。

r002 只有 `PASS_EVIDENCE_CLOSURE` 后，C 才会另行发布 A6R asset/provenance gate；本轮不得提前下载、推理或计算新单元的风险值。

## 7. 服务器最终回复格式

最终回复必须恰好两行，不加代码围栏、项目符号或第三行：

第一行只能是 `执行完毕` 或 `未执行完毕`。

第二行只能是 `dis/server_reports/orientbench-c-r002-20260805.md`。
