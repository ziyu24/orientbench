---
schema_version: 1
review_id: c-review-r028-postpull-20260813
actor: C
review_mode: open_postpull_evidence_check
evidence_head: 0d3c6635944ddee8f438823f2e741d266afe8874
target: orientbench-b-r028-corrective-audit-20260813
verdict: CONTESTED_CROSS_MACHINE_BUNDLE_INCOMPLETE
created_at: 2026-08-13T19:24:58-07:00
---

# C post-pull evidence review: r028

## Verdict

`CONTESTED_CROSS_MACHINE_BUNDLE_INCOMPLETE`。服务器完成了 r028 的计算和发布动作，但没有完成合同要求的跨机器自包含交付；C 因而不能接受 `CONFIRMED_EXTERNAL_STRONG`，也不能解除 r026/r027 contest。

这不是新的科学反向结果。当前可保留的是：r023 推断层可跨机重放；DOTA 冻结表显示强而有边界的同向数值；DOTA 身份只能是 `post-outcome audited external replication`。当前不可接受的是：r026 已获 B/C 正式确认、r028 bundle 可完整跨机重放、稿件已经 JPRS-ready。

## Independent replay

- C 在仓库外临时目录运行 Git bundle 内的 `revalidate_r023_raw.py`，得到 `PASS`、405 hypotheses、4,950/4,950 checks consistent。
- 重算的 `recomputed_hypotheses.csv` 与 committed r028 文件逐字节一致；`revalidation.json` 仅有 40 个约 `1e-18` 的浮点序列化差异，状态和全部一致性判定相同。
- peer-governance 8 项测试及本地 worker validator 均通过；显式 HTTPS `main` 为 `0d3c6635944ddee8f438823f2e741d266afe8874`。

## Decisive blocker

`audit_bundles/r028/bundle_manifest.csv` 声明 20 个对象，但当前 Git 只跟踪 18 个。缺失对象恰为 r026/GT 重放的必要输入：

1. `audit_bundles/r028/dota/bootstrap.npy`，声明 1,280,128 bytes、SHA-256 `6b2e0178ff2ec8507289aa9ede02fef65a7f69d36d3de33b78c6f224e48e8d30`；
2. `audit_bundles/r028/dota/dota_gt_fresh.pkl`，声明 2,680,160 bytes、SHA-256 `3baa2ca8d2d80c7994db371ff8828a77e90c53521e4c2c187e6f61ee46e0beff`。

两者分别命中 `.gitignore` 的 `*.npy` 和 `*.pkl`，在 HEAD 中不存在。其余 18 个 manifest 对象按 Git canonical blob 复核 bytes/SHA 均匹配。由于 bootstrap 缺失，C 无法运行 r026 raw validator或六项 mutation；由于 GT pickle 缺失，C 无法独立验证 55,804 GT、逐类计数和 matched GT-id subset。报告中“20 files / 自包含 / 可完整重放”和稿件中“Git replay bundle includes ... bootstrap array ... GT conversion”均不成立。

## Manuscript and venue

r028 已正确撤销 `preregistered independent external confirmation` 包装，并修正 `tta_localization=-(missing_fraction+iou_loss)`；这是实质进展。但当前主稿仅 848 词、无 References、无成稿图，且仍把缺失的 bootstrap/GT 写成 Git bundle 已包含，因此是审查摘要而非投稿稿。

当前真实级别保持：`JPRS_POTENTIAL_NOT_READY`；在诚实改写和完整成稿后，`TGRS_OR_STRONG_JSTARS` 仍是可防守档位。JPRS 可作为最匹配的冲刺目标，但现阶段不能称 JPRS-ready，更不能保证录用。

## Minimum resolution

停止新增科学 round、换 gate 或换数据集。B 只需下发一次 r028 bundle-closure 修复：从原服务器按 manifest 声明字节 force-add 这两个被 ignore 的对象（或无损封装为 Git 可跟踪文件），重建 manifest 和不夸大的报告；不得重算或改变任何科学数值。C 随后重放 r026 validator、六 mutations 和 GT integrity。全部通过后，C 才能把 contest 收敛为 `AUDITED_EXTERNAL_REPLICATION_ACCEPTED`，但证据身份仍不是 prospective confirmation。
