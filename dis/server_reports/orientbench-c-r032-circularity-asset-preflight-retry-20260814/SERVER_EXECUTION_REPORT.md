---
schema_version: 2
dispatch_id: orientbench-c-r032-circularity-asset-preflight-retry-20260814
plan_id: c-r032-circularity-asset-preflight-retry-20260814
initiator: C
plan_path: dis/plans/C/c-r032-circularity-asset-preflight-retry-20260814/sug.md
plan_commit_sha: 21e8bcde287ff065c96a00a1712a07fba0cce362
plan_blob_oid: 49433296024f01136663f0d051cd5c3ac9654394
plan_sha256: fddcbac05f7f5959618e51b6a9f7eb9473c4a1d47da337153682b5dfb24d2d67
active_sha256: fddcbac05f7f5959618e51b6a9f7eb9473c4a1d47da337153682b5dfb24d2d67
dispatch_commit_sha: a9e1b7f278628962db0ecb82de1fda1a93509a73
starting_commit: a9e1b7f278628962db0ecb82de1fda1a93509a73
started_commit: 239fb3e994890226aab55c696d3724270d973d72
ending_commit: cd621e669556da469582120814e5abed9a974623
server_report_path: dis/server_reports/orientbench-c-r032-circularity-asset-preflight-retry-20260814/SERVER_EXECUTION_REPORT.md
execution_status: complete
completion_mode: full_completion
readiness_status: ASSET_GAP_R032
scientific_outcome: NOT_COMPUTED_ASSET_PREFLIGHT_ONLY
worker_id: server-primary
---

# r032 服务器执行报告

## 结论

r032 已按 `full_completion` 完整执行、独立验证并推送结果 commit `cd621e669556da469582120814e5abed9a974623`。八单元的 8×12 字段矩阵、来源、连接性、四数据集官方标注清单、DOTA GT provenance、稿件支持证据、readiness、quarantine 闭包、artifact manifest 和四项真实 mutation 均已交付。

readiness 合法结果为 `ASSET_GAP_R032`：48/48 个 cohort/source 连接检查全部通过，唯一阻断是 A--H 均没有冻结的“官方原始对象 ID → 当前处理后或切片对象 ID”回连证据。现有 `gt_id` 是评估数据内逐图 ordinal，不能充当官方 raw-object ID。因此本轮完成不等于允许执行 r033；循环性/归因效果审计没有启动。

## 身份与发布顺序

| 项目 | 结果 |
|---|---|
| post-pull HEAD | `a9e1b7f278628962db0ecb82de1fda1a93509a73`，与 dispatch 精确一致 |
| 同步命令 | `git -c http.version=HTTP/1.1 pull --ff-only origin main` |
| plan / active | 同 blob `49433296024f01136663f0d051cd5c3ac9654394`、同 SHA-256 `fddcbac...` |
| worker | `paper.worker-id=server-primary` |
| pth_data/readme | readable；SHA-256 `eb9ac9a172b49cc8063b91c2332f36829d0b3cf5f3a3667f2617d64258d10c9c` |
| 初始 tracked/index/untracked | clean / clean / empty |
| STARTED | 在任何科学资产读取前单独提交并推送：`239fb3e994890226aab55c696d3724270d973d72` |
| result commit | 报告前单独提交并推送：`cd621e669556da469582120814e5abed9a974623` |

本报告的 `ending_commit` 固定指向前一个 result commit，不以报告自身 commit 自证。

## T1--T6 执行结果

| 阶段 | 状态 | 关键结果 |
|---|---|---|
| T1 来源清单 | PASS | 8 units × 5 frozen source roles；真实 path/bytes/SHA/schema/row count 全部记录 |
| T2 字段矩阵 | PASS_WITH_GAPS | 96/96 unit-field 行；状态枚举合法；8 个 `official_annotation_id=MISSING` |
| T3 连接性 | PASS | 48/48 连接通过；duplicate=0，cohort missing/drop=0；extras 单独计数/hash，不进入 cohort |
| T4 官方 GT | PASS | DIOR 11,738 XML、FAIR1M val 3,298 XML、SODA val 576 JSON、DOTA val 458 TXT 均有逐文件 immutable manifest |
| DOTA provenance | PASS_PROVENANCE_ONLY | raw annfiles 与 r028 converted GT、tile map、integrity witness 分开登记；未宣称语义等价 |
| T5 稿件支持 | PASS | 每 unit 定位 unit 名、config/checkpoint、AP50/AP75、matching、split role、risk constant 证据 |
| T6 readiness | ASSET_GAP_R032 | 逐 unit 列出 object-lineage 缺口与未执行的最低恢复动作 |

## 独立验证与 mutation

`validation_r032.json` 为 `PASS`，独立重算并核验：执行身份、全部输入真实 path/bytes/SHA/schema/row count、输出路径集与 manifest、8×12 笛卡尔积、状态证据、真实 cohort key coverage、官方目录 child manifests、quarantine equality 和 readiness 映射。

同一 validator 在四个真实临时副本上均非零退出：

1. 删除一个 unit-field：拒绝，8×12 笛卡尔积不完整；
2. 修改 source SHA：拒绝，真实输入 SHA 不匹配；
3. 制造 cohort/join 重复：拒绝，unit/source_role 键重复；
4. 将 `MISSING` 改为 `DIRECT`：拒绝，缺少 source path/column 证据。

quarantine 在 clean worktree 中为允许的空子集；before/after CSV 逐字节相同。没有读取或消费历史 quarantine 内容。

## 边界与资源

- 未执行 effect size、bootstrap、risk-coverage、witness、科学 PASS/FAIL 或 venue gate。
- 未执行 GPU、训练、forward inference、下载、annotation conversion、repair 或 overwrite。
- 未修改 frozen r014/r019/r023/r026/r028、manuscript、threshold、split、metric、B-owned 路径或第三方源码。
- 全过程为 CPU 只读 inventory/hash/key coverage；在 12 CPU-core-hours、4 小时 wall-time 和读写上限内。
- 首次结果 push 前的 GitHub TLS 连接瞬断；随后用获准的 HTTP/1.1 HTTPS 通道重试成功，不影响内容或提交身份。

## 产物与下一步

必交产物均位于 `reports/r032_circularity_asset_preflight/`，包括 14 个计划指定文件、四个 official child manifests、生成脚本和 mutation receipt。

最低后续动作：由 C 另行签发只读 object-lineage 资产轮，为四数据集建立且独立审计 raw-object-to-evaluation-object immutable mapping。该映射闭合并重新得到 `ASSET_READY_FOR_R033` 前，不得签发或执行循环性/归因效果审计。
