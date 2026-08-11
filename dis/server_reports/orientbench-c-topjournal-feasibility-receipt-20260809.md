# OrientBench 顶刊可行性纠偏验收异常报告

## 1. 身份与最终执行状态

- round_id: `orientbench-c-topjournal-feasibility-receipt-20260809`
- contract_status_at_start: `READY_FOR_SERVER_EXECUTION`
- receipt_execution: `ABNORMAL_PREFLIGHT_FAILURE`
- execution_failure: `true`
- technical_stop: `PREFLIGHT_DIRTY_WORKTREE_AND_WRITABLE_SOURCE_RUNTIME`
- scientific_gate: `NOT_ADJUDICATED`
- track_m_state: `NOT_EMITTED`
- sug_genuinely_exhausted: `false`
- full_execution_status: `PENDING_EXTERNAL_RECEIPT`
- final_commit_sha: `POST_COMMIT_EXTERNAL_RECEIPT`
- git_publish_status: `PENDING_EXTERNAL_RECEIPT`

源执行的永久状态保持：

```text
ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809
```

源执行中的全部数字保持：

```text
DESCRIPTIVE_UNVERIFIED
```

本轮没有独立重算 Track M 或 Track D，因此没有产生、恢复或验证任何科学结论，也没有重新裁定原 `FAIL_TO_MEASUREMENT_ONLY`。

## 2. 用户指令与适用边界

- 用户指令：2026-08-11 要求“现在拉取，执行sug.md”。
- 实际执行边界：只允许 HTTPS Git；禁止 GPU、下载、安装、训练、forward、推理、新 target outcome、annotation 内容读取、稿件修改以及对旧 sealed runtime 的任何修改。
- 本报告是合同允许的唯一 `server_report_path`。除本报告和 `claude_code_and_supervisor.md` 的 append-only 记录外，没有创建其它 receipt code/runtime/output。

## 3. 已完成 preflight

### 3.1 规则与交接文件读取

以下文件均真实读取成功；时间为读取命令当时实际返回的墙钟记录：

| canonical path | bytes | SHA-256 | read start | read end | result |
|---|---:|---|---|---|---|
| `/home/rspip/cqc/pro/study/orientbench/AGENTS.md` | 13,862 | `421b83ddd8b326f187753795be0682974e9b99bdbeb9b0369b7f1b31fd7a4034` | `2026-08-10T18:32:11.104743-07:00` | `2026-08-10T18:32:11.105251-07:00` | `READ_OK` |
| `/home/rspip/cqc/pro/study/orientbench/docs/server_migration_handoff_20260810.md` | 24,870 | `4faffeae34268edf81b88b5e6cb247d2ed4a28b3ef3ca2d005f91d34eb38c818` | `2026-08-10T18:32:11.105268-07:00` | `2026-08-10T18:32:11.105362-07:00` | `READ_OK` |
| `/home/rspip/cqc/pro/study/pth_data/readme.md` | 89,032 | `eb9ac9a172b49cc8063b91c2332f36829d0b3cf5f3a3667f2617d64258d10c9c` | `2026-08-10T18:32:11.105370-07:00` | `2026-08-10T18:32:11.105635-07:00` | `READ_OK` |
| `/home/rspip/cqc/pro/study/orientbench/dis/sug.md` | 41,577 | `160466f61732b0a28f4a98e82618d35ee9cf01e8970b1cc631a84d88e891109c` | `2026-08-10T18:32:11.105644-07:00` | `2026-08-10T18:32:11.105765-07:00` | `READ_OK` |

项目根及其父目录没有另一份适用于本仓库的 `CLAUDE.md`；`AGENTS.md` 的首行标题虽为 `CLAUDE.md`，实际规范文件路径仍为上表所列 `AGENTS.md`。

### 3.2 HTTPS Git 拉取与拓扑

- origin: `https://github.com/ziyu24/orientbench.git`
- current branch: `main`
- HTTPS remote default branch: `main`
- upstream: `origin/main`
- pre-pull HEAD: `9588a095cc459acbd5de54d756343ad7db945956`
- pre-pull HTTPS remote main: `9588a095cc459acbd5de54d756343ad7db945956`
- pull command: `git pull --ff-only origin main`
- pull start/end: `2026-08-11T09:33:25.490958779+08:00` / `2026-08-11T09:33:27.118070049+08:00`
- pull exit: `0`; stdout/stderr result: `Already up to date.`
- post-pull HEAD: `9588a095cc459acbd5de54d756343ad7db945956`
- upstream SHA: `9588a095cc459acbd5de54d756343ad7db945956`
- post-pull HTTPS remote main: `9588a095cc459acbd5de54d756343ad7db945956`
- SHA equality: `true`

本地 `refs/remotes/origin/HEAD` symbolic ref 不存在，首次本地 symbolic-ref 命令真实 exit `128`；随后通过授权的 HTTPS `git ls-remote --symref ... HEAD` 动态解析远端默认分支为 `main`，exit `0`。该失败命令未被隐藏。

### 3.3 受保护文件与提交链元数据

- `HEAD:dis/B.md` Git blob: `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`。
- `dis/B.md` unstaged diff: empty，检查 exit `0`。
- `dis/B.md` staged diff: empty，检查 exit `0`。
- 未读取 `dis/B.md` 内容。
- `post_pull_head` 包含本合同，`HEAD:dis/sug.md` blob 为 `11553a92b05b692a14bf9c4f21898a5c9e10d144`。
- `scientific_data_cutoff`、`source_execution_commit`、`control_base`、`post_pull_head` 四个 commit object 均存在。
- 固定祖先链三项动态检查均 exit `0`：

```text
a9067fb16d2bbd747dfe69789ac33a5911eb15fe
  -> cdf764c5a974030739a9992079bedb8b970fb2a7
  -> bc27506f7d7c0e47c4d67b202b9157bd4016a87a
  -> 9588a095cc459acbd5de54d756343ad7db945956
```

### 3.4 新路径碰撞与 source runtime

检查时：

- source runtime `outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/`：存在、可读、对当前执行用户可写。
- 新 runtime root `outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt_20260809/`：不存在。
- 新 code root `top_journal_v3_reaudit_055/feasibility_receipt_20260809/`：不存在。
- 本报告路径：启动时不存在。

## 4. 强制失败点

### 4.1 post-pull index/worktree 不干净

`git pull --ff-only` 后的真实 `git status --porcelain=v1 --untracked-files=all` 为：

```text
 M claude_code_and_supervisor.md
?? docs/server_migration_handoff_20260810.md
```

两项变化均在本轮 receipt 启动前已经存在。合同第 3.2、3.3 条要求 pull 后立即满足 index/worktree 干净，并明确禁止删除、隐藏、恢复、stash、clean 或以替代路径使其通过。因此本轮不能修复该状态，preflight 必须失败。

### 4.2 source runtime 不满足不可写要求

对 `outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/` 的真实权限检查返回 `readable=true, writable=true`。合同要求该既有 source runtime 已存在、可读且不可写，并禁止 chmod、复制替代或修改旧 runtime 以绕过。因此这是第二个独立 preflight failure。

## 5. 已停止及未执行阶段

在上述失败后，以下阶段全部未执行：

- Track M sealed source inventory、raw-row metric/AUGRC/AURC/NRC 重算；
- pinned fd-shifts 动态 reference；
- 10,000 次同步 cluster bootstrap；
- 五状态 production fixtures；
- Track D 四候选 official evidence 重建及完整搜索；
- independent validator；
- 四项 isolated mutation；
- joint gate adjudication；
- receipt generator、runtime、manifest、access log、execution ledger、resource telemetry 和 protocol closure；
- manuscript edit、训练、推理、GPU、下载、安装、新 target outcome 或 annotation 内容访问。

这些阶段不是 `INSUFFICIENT_ASSETS` 的科学结果，而是因不可绕过的启动条件失败而 `NOT_RUN`。不得根据源摘要补写结果，也不得把本轮包装为完整 receipt。

## 6. 写入范围、停止条件与后续

- pre-seal changed/untracked 集合：上述两项既有变化，加上本轮授权创建的本报告。
- planned commit scope：仅本报告；append-only 日志保留在工作树中，因为其 diff 含本轮开始前的既有记录，不能在本合同中伪装成干净启动资产。
- `dis/B.md` pre-seal blob 保持不变。
- GPU/下载/安装/训练/推理/forward/新 outcome/改稿：均未发生。
- scientific/audit closure: `INCOMPLETE_DUE_TO_PREFLIGHT_FAILURE`。
- execution status: `ABNORMAL_PREFLIGHT_FAILURE`。
- 下一步只能由用户/监督员在本轮之外先处置既有工作树变化和 source runtime 权限，再下发具有新 round id、新 code/runtime/report 路径的正式合同；本轮路径已被异常报告占用，禁止删除、覆盖或复用后重跑。

