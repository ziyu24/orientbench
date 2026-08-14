---
schema_version: 2
dispatch_id: orientbench-b-r034-circularity-decisive-20260814
plan_id: b-r034-circularity-decisive-20260814
initiator: B
plan_path: dis/plans/B/b-r034-circularity-decisive-20260814/sug.md
plan_commit_sha: b50a9b9b3ab4c72e5790273b9adfacb3f70fb5e2
plan_blob_oid: 6894bae2181af4cf5f66caec38249c74b50f784e
plan_sha256: 48cf244e01027bb217e19253f627aa8fce10a04ab3d7c3803c05494a2bd04a02
active_sha256: 48cf244e01027bb217e19253f627aa8fce10a04ab3d7c3803c05494a2bd04a02
dispatch_commit_sha: 0b5a98f27fd24ceab6b8f6d05ea3a0b7fdf98e1a
starting_commit: 0b5a98f27fd24ceab6b8f6d05ea3a0b7fdf98e1a
started_commit: 500b80440e2d85dbb706bccd5a223ba5fc21f8dd
ending_commit: 2c817b24432f4bbf6c956668cf4fcbf512253c20
server_report_path: dis/server_reports/orientbench-b-r034-circularity-decisive-20260814/SERVER_EXECUTION_REPORT.md
execution_status: complete
completion_mode: full_completion
candidate_scientific_state: K1_K2_KILL_STRONG_JSTARS
scientific_outcome: SURVIVAL_FALSE
worker_id: server-primary
---

# r034 服务器执行报告

## 结论

r034 已按 `full_completion` 完整执行、独立复核并推送结果 commit `2c817b24432f4bbf6c956668cf4fcbf512253c20`。冻结判断为 `K1=true`、`K2=true`、`SURVIVAL=false`，12 项 primary family 没有注册 witness，候选科学状态为 `K1_K2_KILL_STRONG_JSTARS`。

这是决定性实验按预注册规则得到的正常科学早停结果，不是执行异常，也不把 candidate state 冒充 B/C 最终裁决。后续不得靠修改 frozen threshold、split、formal 标签或扩大矩阵推翻结果；监督端应从 `audit_bundles/r034/` 独立重放并登记最终 verdict。

## 身份与发布顺序

| 项目 | 结果 |
|---|---|
| pre-pull / post-pull | `14110ce48fcb17e5c937b9a9c480c882f2072d66` → `0b5a98f27fd24ceab6b8f6d05ea3a0b7fdf98e1a`，post-pull 与 dispatch 精确一致 |
| 同步命令 | `git -c http.version=HTTP/1.1 pull --ff-only origin main` |
| plan / active | 同 blob `6894bae...`、同 SHA-256 `48cf244e...` |
| worker | `paper.worker-id=server-primary` |
| pth_data/readme | readable；SHA-256 `eb9ac9a172b49cc8063b91c2332f36829d0b3cf5f3a3667f2617d64258d10c9c` |
| 初始 tracked/index/untracked | clean / clean / empty |
| STARTED | 科学计算前单独提交并推送：`500b80440e2d85dbb706bccd5a223ba5fc21f8dd` |
| result commit | 报告前单独提交并推送：`2c817b24432f4bbf6c956668cf4fcbf512253c20` |

本报告的 `ending_commit` 固定指向前一个 result commit，不以报告自身 commit 自证。

## T1--T3 科学执行

| 阶段 | 状态 | 关键结果 |
|---|---|---|
| T1 object lineage | COMPLETE_WITH_REGISTERED_GAP | A--H 八单元均为 `LINEAGE_GAP(unit)`；`LINEAGE_CONTRADICTION=0`，因此按计划继续 T2 |
| T2 formal audit | COMPLETE | 616,184 行；DIOR-R 5,900 clusters、DOTA 458、FAIR1M 2,142、SODA 576；两套独立实现各做 seed `20260814`、10,000 次 image-cluster bootstrap |
| primary family | COMPLETE | DIOR-R / DOTA × 3 contrasts × `R_norm` / `R_raw`；class-standardized AUGRC；单一 Holm family，共 12 项 |
| T3 diagnostics | COMPLETE | mechanism、class composition、matching、NMS inventory 与三路分解均持久化 |

`R_norm` 的 class-standardized probe−ARonly residual DoD 在 DIOR-R 为 `0.016598`（95% CI `[0.012708, 0.021103]`），在 DOTA-v1.0 为 `0.016077`（95% CI `[0.010314, 0.019015]`）；但两域 eligibility delta 均未构成注册 flip witness。ARonly−conf 的绝对 DoD 分别为 `0.014885` 与 `0.012157`，满足 K1 的 0.8 比例条件；两域 residual probe−ARonly 均无 witness，K2 同时成立。`R_raw` 六项也均无 witness。

因此风险定义变换不能解释主要现象，AR 控制占主导；剩余显著 DoD 不满足冻结 witness 逻辑，不能据此宣称强 circularity-survival。

## 独立复核、故障注入与审计包

- A/B comparator：576 个 hypothesis keys、14,976 个字段比较全部通过；最大绝对差分别为 `5.55e-17`（unit）和 `4.16e-17`（dataset），低于 `atol=1e-10`；40,000 个 cluster multiplicity hash 与数组逐元素一致。
- raw validator：只从 616,184 行 enriched rows 与 bootstrap multiplicities 独立重算 12/12 primary，并复核协议、公式、Holm、witness、K1/K2 和 candidate state；pristine 与 bundle replay 均为 `PASS`。
- mutation：K1 `0.8→0`、estimand `class-standardized→pooled`、raw risk、primary DoD、bootstrap multiplicity、judgment state 六项真实临时副本修改全部被同一 validator 非零拒绝。
- bundle：`audit_bundles/r034/` 共 39 个 manifest objects、229,597,799 bytes；逐文件 SHA-256 通过，单文件均小于 80 MiB，bundle 内 validator 重放通过。
- artifact manifests：persistent 48 项、执行目录 19 项，文件集合、bytes 和 SHA-256 均闭合。

## 资源、边界与偏差

- GPU=0，training=0，detector forward inference=0；正式 bootstrap 使用 96/112 逻辑 CPU，满足 CPU 密集任务规则。
- Implementation A / B wall time 分别约 165.6 秒 / 153.5 秒；资源估算在计划上限内。
- 未修改 frozen threshold、D_cal/D_audit、formal/exploratory 标签、旧冻结产物或第三方源码；未下载、训练或执行 detector inference。
- class-standardized 的实现澄清为：每个 eligibility/bootstrap draw 内对非空官方 class ID 等权平均，不为缺失 class 伪造零曲线；A/B/raw validator 完全一致。
- result push 成功。GitHub 对 bundle 中两份约 55.33 MB 文件给出大于建议 50 MB 的 warning，但未拒绝；所有文件均低于 GitHub 100 MB 硬限制及计划 80 MiB 拆分阈值。

## 产物与后续门控

核心路径：

- `top_journal_v3_reaudit_055/circularity_decisive_r034_20260814/DECISIVE_REPORT.md`
- `outputs/persistent_artifacts/orientbench_circularity_decisive_r034_20260814/`
- `audit_bundles/r034/`
- `top_journal_v3_reaudit_055/circularity_decisive_r034_20260814/validation/validation.json`
- `top_journal_v3_reaudit_055/circularity_decisive_r034_20260814/mutations/mutation_results.json`

建议 B/C post-pull 独立重放并固定最终 verdict。若未发现可审计反证，应按当前项目规则关闭 selector 强顶会/J-STARS survival 路线，收缩为 TGRS/ISPRS benchmark + practical selector；不得由服务器自行改方向或宣称论文最终完成。
