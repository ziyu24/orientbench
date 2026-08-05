# OrientBench 服务器任务：A6R 前瞻独立复现实物门控

- round: `orientbench-c-r003-20260805`
- scientific snapshot: `e3ca1ad94d64d202a47b6635490fde439df76868`
- active manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_paper_A_zh_v077.md`
- previous server report: `dis/server_reports/orientbench-c-r002-20260805.md`
- 唯一服务器报告路径: `dis/server_reports/orientbench-c-r003-20260805.md`

## 1. 单一科学问题

在不读取、不生成任何候选单元 target NRC、角度风险、认证前沿或其它 outcome 的条件下，当前服务器是否已经存在至少一个可被冻结为 A6R prospective replication 的完整 detector×head×dataset×split 单元？

本轮只做资产、身份、许可、协议暴露和可复算性门控；训练 `0`、推理 `0`、风险计算 `0`。PASS 只冻结一个候选，不能被描述为原 A6 confirmatory success，也不授权本轮继续推理。

## 2. 不可改写的历史边界

1. 原 [`a6_confirmatory_protocol_frozen.json`](../top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a6_confirmatory_protocol_frozen.json)、`NO_ELIGIBLE_CONFIRMATORY_UNIT` 及其全部既有产物保持逐字节不变。A6R 是在当前 scientific snapshot 后新注册的前瞻复现，不追溯替换原 A6。
2. A=`A_MEASUREMENT_ONLY`；B=`RETIRED_FAIL_CANDIDATE_GATE`。不得恢复 B6/B7，不得把 B 的 common-mask 口径带入 A。
3. A 的 missing-TTA policy 固定为：eligible universe 不变，非有限 TTA 排在全部有限 TTA 之后并披露缺失率；TTA 完全不可得时从该单元 score menu 中删除，不改用 complete-case universe。
4. 主 mask、primary event、absolute alpha、coverage grid、practical thresholds、scene statistics、tile/mother-scene 定义均沿用现有 A1/A6 冻结协议；本轮不得修改。

## 3. 前置与禁读边界

1. 只允许 fast-forward 同步；记录实际完整 HEAD，并证明 ancestry 包含 `e3ca1ad94d64d202a47b6635490fde439df76868`。tracked/index 不洁净、所有权冲突或不能 fast-forward 时停止。
2. 完整读取 A1/A6 冻结协议、A6 provenance audit、迁移交接和现有资产 schema。只可读取候选的文件身份、schema、哈希、配置、日志元数据、许可与 official provenance。
3. 在候选冻结前，禁止打开或计算任何潜在候选的 NRC、angle-risk、severe-event rate、certification、risk frontier 或以这些 outcome 为输入的 selection 文件。可以用路径/manifest 判断“是否已有结果暴露”；一旦确认暴露，立即排除该候选，不读取数值。
4. 禁止下载或读取 D7/PCP-OBB、pcbobb、pcbobb_beyond、pcbobb_score_study。禁止下载新的 dataset/checkpoint 或运行模型；若当前无合格资产，只报告一个最小官方 acquisition proposal，不在本轮获取。
5. Git 共享产物不得包含账号、机器标识、绝对路径或凭据。服务器资产使用稳定逻辑别名和相对路径；外部来源使用官方 URL、版本和公开 checksum。

## 4. 候选单位与污染审计

候选身份必须精确到：dataset/version、split、detector、angle head/coder、backbone、checkpoint、config、framework commit、evaluator、tile/merge/NMS 配置。

每个候选必须检查并报告：

1. checkpoint/config/log 的来源、选择标准、bytes、SHA-256、框架与依赖版本、许可。checkpoint 只能按与 target orientation-risk 无关的既有标准选定；不能在本轮比较 checkpoint。
2. 完整 split 身份：所有图像数、含空 GT 图像、完整 GT、类别映射、角度约定、原图/切片/母景 ID 映射及其 aggregate hash。
3. 可复算输出边界：能否在后续一次冻结推理中持久化 raw head output、pre-NMS、tile merge/pre-final-NMS 和 final predictions；每层保留 class、score、OBB、image/tile/mother-scene ID；完整 evaluator 可确定重跑。
4. 既有暴露：该精确 unit 是否参与 alpha、AR、score direction、endpoint、coverage grid、M1--M3、候选设计或任何 NRC/risk/certification 计算。只要任一为是，排除。
5. overlap：仓库中已有 checkpoint/config/prediction/risk 文件、现有 A6 候选、以及已知内部旧项目导入资产是否同 hash、同来源或同 selection lineage。未知不能写成 clean。
6. TTA 可得性和预计缺失处理，但不得生成 TTA 数值或风险结果。
7. 预计 GPU 小时、磁盘、数据许可和下载来源，仅作为未来 acquisition/inference 规划，不在本轮执行。

独立性分层：

- Tier 1：新 dataset/version 且新 detector/head unit，未参与任何协议设计或 outcome 查看；优先。
- Tier 2：既有 dataset 上的精确新 detector/head unit，未参与任何协议设计或 outcome 查看；只可称 unit-level prospective replication。
- Excluded：partial universe、仅 matched cache、旧风险结果已存在、checkpoint 按风险选、母景身份不可恢复、来源/许可不清或与既有资产重叠。

## 5. 中性冻结顺序

不得按 AP、NRC、风险、预期“好看程度”选候选。对通过硬门的候选按以下顺序确定唯一 selected unit：

1. Tier 1 优于 Tier 2；
2. official/author-released checkpoint + 完整公开来源/许可优于非官方资产；
3. full split、empty images、GT、scene identity 与完整 evaluator 均可验证者优先；
4. 后续 raw→final 全链可持久化者优先；
5. 预计 GPU 小时与新增磁盘更低者优先；
6. 仍并列时按规范化 `dataset|detector|head|checkpoint_sha256` 字典序。

所有 eligible 与 excluded 候选都保留；不得在看到任何 outcome 后换 unit。

## 6. 授权写入范围

服务器只可新增以下文件：

- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a6r_assets_r003.py`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a6r_candidate_asset_inventory_r003.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a6r_overlap_registry_r003.csv`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a6r_asset_gate_r003.json`
- `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a6r_asset_gate_manifest_r003.json`
- `dis/server_reports/orientbench-c-r003-20260805.md`

不得修改任何既有 A/B 文件、主稿、配置、数据、split、checkpoint、旧报告、`dis/B.md` 或本轮 `dis/sug.md`。若需要其它写入，记为 `PROPOSED_DEVIATION` 并停止，不自行扩权。

## 7. 必须生成的证据

1. candidate inventory：上述精确身份、逻辑路径/官方 URL、bytes/hash/license、完整 split/schema/scene identity、TTA 可得性、预计资源。
2. overlap registry：逐候选列出仓库命中、hash/source/selection lineage、协议参与和 prior-outcome 暴露；不得把 unknown 当 clean。
3. machine-readable gate JSON：硬门逐项状态、独立性 tier、中性排序 key、唯一 selected unit 或排除理由。
4. manifest：scientific snapshot、execution HEAD、脚本/输入/输出 canonical Git blob hash、实际命令、训练/推理/风险计算/下载计数，所有计数必须为 `0`。
5. 唯一报告：完整候选表、首个失败点、gate、最弱环节和下一步；若没有本地合格资产，可附一个不含 outcome 的最小官方 acquisition proposal，但不得下载。

## 8. Pass / fail / inconclusive gate

- `PASS_A6R_ASSET_GATE`：至少一个候选通过全部硬门，并按中性顺序冻结唯一 selected unit；资产当前存在、哈希/许可/完整 split/scene identity/evaluator/raw→final 持久化边界全部可验证；无 prior outcome 暴露。该状态只授权 C 设计下一轮一次性推理合同。
- `FAIL_NO_A6R_ASSET`：盘点完整，但所有候选因 partial universe、only matched cache、prior outcome、协议参与、风险选择或已知 overlap 被排除。保留原 `NO_ELIGIBLE_CONFIRMATORY_UNIT`，不得降低标准。
- `INCONCLUSIVE_A6R_IDENTITY`：关键 hash、许可、完整 split、empty-image、母景映射、checkpoint 选择或 overlap 身份无法证明。不得把 unknown 计为 PASS。
- `PROTOCOL_DRIFT`：读取/计算了候选 outcome，发生训练、推理、下载、旧项目读取，改动冻结协议或写出授权范围。立即停止；候选视为受污染，不得继续用作 A6R。

早停顺序：Git/所有权 → 禁读/下载/计算计数 → prior-outcome/协议参与 → checkpoint 与许可 → full-universe/empty/scene identity → evaluator/raw→final 可复算性 → overlap → 中性排序。没有新资产证据即停止。

## 9. 服务器最终回复格式

最终回复必须恰好两行，不加代码围栏、项目符号或第三行：

第一行只能是 `执行完毕` 或 `未执行完毕`。

第二行只能是 `dis/server_reports/orientbench-c-r003-20260805.md`。
