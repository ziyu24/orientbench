---
schema_version: 1
review_id: c-review-r029-final-replay-20260813
actor: C
review_mode: independent_postpull_raw_replay
evidence_head: fe9d0ea5172c864d0abcecb126f530242a84c7ed
target: orientbench-b-r029-bundle-closure-20260813
scientific_verdict: AUDITED_EXTERNAL_REPLICATION_ACCEPTED
execution_receipt_verdict: R029_ARTIFACT_DELIVERY_ACCEPTED_WITH_REPORT_SCHEMA_DEVIATION
joint_scientific_state: PENDING_B_MATCHING_VERDICT
created_at: 2026-08-13T20:02:15-07:00
---

# C final post-pull replay: r029

## Verdict

`AUDITED_EXTERNAL_REPLICATION_ACCEPTED`。

r029 补齐了此前阻塞 C 跨机重放的两个原始对象。C 不依赖服务器报告的完成声明，从 Git canonical blobs、bundled raw data 和 production replay 独立复核后，解除 r026/r028 contest。

证据身份固定为 `POST_OUTCOME_AUDITED_EXTERNAL_REPLICATION`，不得写成 prospective/preregistered independent confirmation。B 尚未发布 r029 后与 C 匹配的正式 verdict，因此 joint state 仍为 `PENDING_B_MATCHING_VERDICT`。

## Git and bundle closure

- evidence HEAD 与显式 HTTPS remote `main` 均为 `fe9d0ea5172c864d0abcecb126f530242a84c7ed`，工作树在验收开始时 clean。
- r029 result commit 相对前一提交只涉及两个缺失 binary、supervisor log 和唯一 r029 report；未改其余科学 bundle 对象。
- `bundle_manifest.csv` 声明 20 个对象；20/20 Git canonical blob bytes/SHA-256 均与 manifest 相同。
- 新补对象：`bootstrap.npy` 为 1,280,128 bytes / `6b2e0178ff2ec8507289aa9ede02fef65a7f69d36d3de33b78c6f224e48e8d30`；`dota_gt_fresh.pkl` 为 2,680,160 bytes / `3baa2ca8d2d80c7994db371ff8828a77e90c53521e4c2c187e6f61ee46e0beff`。

## Independent r026 replay

C 在仓库外临时目录运行 bundle 中的 `revalidate_r026_raw.py`，输入为 bundled raw、bootstrap、tile map 和冻结 delta source：

- validator status `PASS`；96/96 checks consistent；
- 10,000 mother-scene bootstrap replicates 由 production replay 消费；
- gate 重算为 `CONFIRMED_EXTERNAL_STRONG`、2 unit witnesses、2 dataset witnesses；
- 重算 gate JSON 与 committed 文件逐字节一致；
- 6 行 hypotheses 的点估计仅有不超过 `1.01e-16` 的浮点序列化差异，其余数值与全部离散字段一致。CSV 另受 Windows checkout CRLF 影响，不构成科学数据差异。

正式稿件不得直接消费 `CONFIRMED_EXTERNAL_STRONG` 作为证据身份；该 token 是冻结数值 gate 的输出，科学身份仍受先揭示事实限制。

## Real mutation replay

六项 mutation 均通过真实 subprocess 调用 production validator，而非硬编码退出码：

| mutation | pristine exit | mutated exit |
|---|---:|---:|
| GT_THETA | 0 | 2 |
| TILE_MOTHER | 0 | 2 |
| AR_GATE | 0 | 2 |
| BOOTSTRAP_CELL | 0 | 1 |
| SWAP_GATE | 0 | 1 |
| REPORT_TOKEN | 0 | 3 |

重算 mutation index 与 committed 文件逐字节一致。

## GT integrity

C 独立读取 exact Git-tracked GT pickle并复核：

- 5,297 tiles，458 mother scenes，55,804 GT；
- 15 类计数为 `[4449, 358, 785, 212, 10579, 8819, 18537, 1512, 266, 4740, 251, 275, 4167, 732, 122]`；
- ORCNN 48,889 个 matched/unique GT-id，全部属于 GT universe，比例 0.8760841517；
- RTMDet 51,736 个 matched/unique GT-id，全部属于 GT universe，比例 0.9271019999；
- tile map 的 canonical Git blob SHA-256 为 `c76833d1d9470f1846af3ecc9b5040f8c8d6a285c8b6793b377a9d6f199fe3a1`。工作树 CRLF 不用于 canonical blob 裁决。

## Prior layers and package

- r023 已由 C 重放：405 hypotheses，4,950/4,950 checks consistent；其状态仍为 `INCONCLUSIVE_MIXED`。
- r027 rebuilt package manifest 的 17 个对象均与 Git canonical blobs一致；corrected TTA 代码明确计算 `-(missing_fraction+iou_loss)`，旧描述文件已标为 `SUPERSEDED_BY_R028`。
- corrected TTA 描述表所需 target feature parquets 未包含在 bundle，无法在 C 机从最底层完全再生；该分支为 descriptive-only，不进入正式 gate，故不是 contest blocker。

## r029 report deviation

r029 的实际 Git 交付成立，但 `STARTED.json` 和最终报告不满足冻结报告 schema 的全部字段，且 `PURE_BUNDLE_CLOSURE` 不是冻结 completion 枚举。因此记录 `R029_REPORT_SCHEMA_DEVIATION`。该偏差不影响由 C 独立验证的二进制、manifest、raw replay 和 mutation 事实；也不值得再开服务器 round 修补文字。

## Scientific and venue consequence

正式可用主张是：AR eligibility domain 对 OBB orientation-reliability 排序具有可复核、跨 DIOR/DOTA 同方向且带 FAIR1M/SODA 边界的 measurement-validity 影响。DOTA 是 post-outcome audited replication；learned EQS 只保留为失败迁移附录。

科学证据已达到 `JPRS_SUBMISSION_CANDIDATE`，但主稿约 848 词、无完整 References 与成稿图表，所以项目仍是 `JPRS_SUBMISSION_CANDIDATE_NOT_READY`。下一步不是新实验，而是 B 给出 matching verdict并关闭 r029，然后完成 JPRS 全稿和 claim-to-evidence 审核。
