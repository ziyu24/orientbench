---
schema_version: 2
dispatch_id: orientbench-b-r036-qsetod-kill-study-20260814
plan_id: b-r036-qsetod-kill-study-20260814
initiator: B
plan_path: dis/plans/B/b-r036-qsetod-kill-study-20260814/sug.md
plan_commit_sha: 724f6b689dee09e4050565262ed75973b3f72b18
plan_blob_oid: 1d4ee8b61fa3b56ffc07aedd0539e89845db7ca9
plan_sha256: 3e501418eb0adc09f4edd224bc3120d2a9761a9efb686a72df6b6d1051822b28
active_sha256: 3e501418eb0adc09f4edd224bc3120d2a9761a9efb686a72df6b6d1051822b28
dispatch_commit_sha: ffab54d8babe7041f87131ef08723456b6011f25
starting_commit: ffab54d8babe7041f87131ef08723456b6011f25
started_commit: f4b5af91ffd78d621e8ee6abcf44f25deb419540
ending_commit: 46066a298ec143584b8b64330c009ebb58cd83d0
server_report_path: dis/server_reports/orientbench-b-r036-qsetod-kill-study-20260814/SERVER_EXECUTION_REPORT.md
execution_status: complete
completion_mode: full_completion
candidate_scientific_state: QSETOD_EVIDENCE_ONLY_KEEP_M
scientific_outcome: KILL_C_TRUE
worker_id: server-primary
---

# r036 服务器执行报告

## 结论

r036 已按 `full_completion` 完整执行、双实现复算、独立验证并推送结果 commit `46066a298ec143584b8b64330c009ebb58cd83d0`。冻结门控结果：`KILL-E=false`、`KILL-C=true`、`PRUNE-M=false`，候选状态为 `QSETOD_EVIDENCE_ONLY_KEEP_M`。

含义是：现有 TTA 图像证据确实在 5/8 个 held-out 配置中提供几何之外的稳定增量，多峰结构的行数占比也超过保留阈值；但 source-only 集合校准在跨数据集目标上不能稳定满足冻结的 ±5 个百分点覆盖容差。因此 Q-SetOD 不具备进入 §4.2 集合式有限训练的资格，只能降格为 evidence/质量分数改进候选。该结果不触碰 r034 联合终局，也不授权任何 GPU 训练。

这是正常的预注册科学 kill 结果，不是 execution failure。最终 claim/verdict 仍须 B/C post-pull 独立重放后一致登记。

## 身份与发布顺序

| 项目 | 结果 |
|---|---|
| pre-pull / post-pull | `d25fe1f58f3d2e647cf27a8767ded23133ae66d5` → `ffab54d8babe7041f87131ef08723456b6011f25`，post-pull 与 dispatch 精确一致 |
| 同步命令 | `git -c http.version=HTTP/1.1 pull --ff-only origin main` |
| plan / active | 同 blob `1d4ee8b...`、同 SHA-256 `3e501418...` |
| worker | `paper.worker-id=server-primary` |
| pth_data/readme | readable；SHA-256 `eb9ac9a172b49cc8063b91c2332f36829d0b3cf5f3a3667f2617d64258d10c9c` |
| 初始 tracked/index/untracked | clean / clean / empty |
| STARTED | 科学资产处理前单独提交并推送：`f4b5af91ffd78d621e8ee6abcf44f25deb419540` |
| result commit | 报告前单独提交并推送：`46066a298ec143584b8b64330c009ebb58cd83d0` |

本报告的 `ending_commit` 固定指向前一个 result commit，不以报告自身 commit 自证。

## T1 endpoint 消费审计

七类候选 endpoint 均登记历史 read/fit/adjudication、服务器资产和合法性：

- DOTA-v1.5、DIOR-R official test、HRSC2016 已被历史轮消费；
- FAIR1M official test labels 和遥感外 OBB 资产缺失；
- DOTA-v2.0 val annotations 与 SODA-A official test labels 在盘且未发现此前科学消费，记为两个清白候选。

这只是只读清白度 inventory，不构成后续使用、训练或推理授权。因为并非“无一清白”，本轮不触发纯 endpoint 原因的 venue 上限下调；实际方法门控仍由 KILL-C 否决。

## T2 证据增量

- 输入为 A--H 八单元 616,184 行；冻结 TTA 特征、预测面积和原始 OBB 全部零丢失连接，签名轴向残差的绝对值与 `e_can` 最大差低于 `2e-5°`。
- 三个 source 规格 A、BC、ABC 均按 image/mother cluster 做 5-fold cross-fitting；target angle labels 只在预测冻结后用于评测，8/8 fit guard 的 target-label fit count 均为 0。
- 每个配置使用 source-defined semantic class × AR quintile × size quintile common support；模型固定为 200-iteration、15-leaf、lr=0.05 的 CPU HistGradientBoosting mean/0.75-quantile regressors。
- A/B 各用 seed `20260814` 做 10,000 次 held-out cluster bootstrap。

8 个配置中 5 个满足冻结 evidence witness：A→B、BC→A、ABC→E/F/G。A→C 因 quantile loss 变差失败，ABC→D 增量 CI/下限失败，ABC→H 同时低于 Spearman/AUGRC 下限。故 `KILL-E=false`。

泄漏线性探针的 cross-fitted R²：A source 的 log-AR/log-area/class-onehot 分别约 `0.143/0.139/0.035`；BC 为 `0.051/0.084/0.024`；ABC 为 `0.077/0.098/0.027`。证据特征含部分几何信息，已完整披露，不用训练侧“去混杂”文字替代 held-out gate。

## T3 多峰存在性

536 个 class × AR-bin × unit strata 覆盖全部 616,184 行；dip `p<0.01` 且双成分 axial von Mises 相对单成分 `ΔBIC>10` 的 strata 共 39 个，行数加权占比 `0.144760`。该值高于 10% 阈值，因此 `PRUNE-M=false`，多峰机制不因本轮数据占比被删除。

冻结 conda 环境没有 `diptest` 包，且本轮网络不允许下载依赖。T3 因此采用披露的 deterministic 128-bin Hartigan-style dip projection 与渐近 uniform-null p 上界；两套独立实现逐字段一致。这是正式偏差，限制 T3 机制结论的强度，但不影响独立的 KILL-E/KILL-C 判定。

## T4 source-only 集合校准

16 个 configuration × alpha 结果中 4 个触发冻结 kill：

- ABC→D：alpha 0.1 / 0.2 覆盖分别约 `0.9535 / 0.8701`，偏差 `+5.35 / +7.01` 个百分点；
- ABC→E：alpha 0.2 覆盖约 `0.8675`，偏差 `+6.75` 个百分点；
- ABC→F：alpha 0.2 覆盖约 `0.8627`，偏差 `+6.27` 个百分点。

失败不是近全圆退化造成：所有配置中位集合宽度约 `5.65°–16.04°`，远低于 120° kill 阈值。失败性质是 source-only coverage transfer 不成立，因此 `KILL-C=true`。

## 双实现、validator、mutation 与 bundle

- A/B comparator：T2、T3、T4、泄漏表及 80,000 bootstrap rows 共 244,794 字段检查通过；最大绝对差 `1.01e-16 < 1e-10`，multiplicity 数组与 judgment 完全一致。
- raw validator：从 prepared rows、source OOF、target predictions 和确定性 multiplicities 重导 8 个 T2 配置、16 个 T4 rows、536 个 T3 strata、24 个原始 bootstrap spot checks 和最终门控，`PASS`；`validator_output_forcing=false`。
- mutation：KILL-E 下限、common-support 定义、coverage nominal、dip 阈值、judgment token、target-label fit guard 六项真实 subprocess 修改全部被同一 validator 非零拒绝。
- bundle：`audit_bundles/r036/` 共 54 个 manifest objects、190,356,681 bytes；逐文件 SHA-256 通过，最大文件 66,044,758 bytes，小于 80 MiB；bundle 内 reproduction entry point 和 raw replay 均 `PASS`。
- manifest：persistent 48 项、执行目录 29 项，文件集合、bytes 与 SHA-256 已闭合。

## 资源与边界

- GPU=0，neural training=0，detector forward/inference=0，下载新数据=0。
- 两套正式 bootstrap 均使用 96/112 逻辑 CPU，A/B wall time 分别约 494.1 秒与 485.1 秒；总资源在 112 CPU-core-hours、43,200 秒和读写帽内。
- 未修改 frozen threshold、D_cal/D_audit、formal 标签、r034 判定、旧 selector claim、第三方源码或旧冻结产物。
- result push 成功。GitHub 对一份约 62.99 MB multiplicity 文件给出大于建议 50 MB 的 warning，但未拒绝；文件低于 GitHub 100 MB 硬限制和计划 80 MiB 拆分阈值。

## 关键路径与下一步

- `top_journal_v3_reaudit_055/qsetod_kill_study_r036_20260814/DECISIVE_REPORT.md`
- `outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814/`
- `audit_bundles/r036/`
- `top_journal_v3_reaudit_055/qsetod_kill_study_r036_20260814/validation/validation.json`
- `top_journal_v3_reaudit_055/qsetod_kill_study_r036_20260814/mutations/mutation_results.json`

B/C 应从 `audit_bundles/r036/` post-pull 独立重放并登记最终 verdict。若接受当前结果，应停止 Q-SetOD 集合校准/有限训练路线，只保留 evidence/质量分数候选讨论；任何 GPU 训练、校准规则修改或新 endpoint 使用均需用户另行授权和新 dispatch。
