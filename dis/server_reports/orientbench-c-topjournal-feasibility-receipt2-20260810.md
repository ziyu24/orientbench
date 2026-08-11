# OrientBench 顶刊可行性纠偏验收 receipt2 异常报告

## 1. 身份与最终执行状态

- round_id: `orientbench-c-topjournal-feasibility-receipt2-20260810`
- retry_of: `orientbench-c-topjournal-feasibility-receipt-20260809`
- dispatch_base: `2a70303e9d74313a15b71e1767b0b6ecdc05d2cc`
- post_pull_head: `6d8892a3793b2efcd8373ce8d509a6cf9872427c`
- receipt_execution: `ABNORMAL_MANDATORY_REFERENCE_PROVENANCE_FAILURE`
- execution_failure: `true`
- technical_stop: `PINNED_FD_SHIFTS_SOURCE_NOT_LOCALLY_AVAILABLE`
- scientific_gate: `NOT_ADJUDICATED`
- track_m_state: `NOT_EMITTED`
- track_d_state: `NOT_RUN`
- sug_genuinely_exhausted: `false`
- full_execution_status: `PENDING_EXTERNAL_RECEIPT`
- final_commit_sha: `POST_COMMIT_EXTERNAL_RECEIPT`
- git_publish_status: `PENDING_EXTERNAL_RECEIPT`

源执行永久保持：

```text
source_execution_status: ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809
source_numbers_status: DESCRIPTIVE_UNVERIFIED
source_reported_gate: FAIL_TO_MEASUREMENT_ONLY_UNVERIFIED
```

receipt1 永久保持：

```text
receipt_execution: ABNORMAL_PREFLIGHT_FAILURE
scientific_gate: NOT_ADJUDICATED
Track M: NOT_RUN
Track D: NOT_RUN
non_reusable: true
```

receipt2 没有产生 Track M/Track D 科学状态，没有验证源数字，也没有重新裁定联合 gate。

## 2. 用户指令与执行边界

- 用户指令：2026-08-11 要求“拉取，执行”。
- 本轮仅执行 active `dis/sug.md` 的 receipt2 mechanical retry。
- GPU、download、installation、training、forward、inference、new target outcome、annotation content、target-label tuning 与 manuscript edit 授权均为 `false`。
- 未调用 CC，未读取 `dis/B.md` 内容，未修改任何旧科学资产、source runtime、threshold、split、稿件或控制文件。

## 3. 已完成的强制 preflight

### 3.1 规则读取

以下文件均完整读取成功，记录为实际读取命令的墙钟：

| canonical path | bytes | SHA-256 | start | end | result |
|---|---:|---|---|---|---|
| `/home/rspip/cqc/pro/study/orientbench/AGENTS.md` | 13,862 | `421b83ddd8b326f187753795be0682974e9b99bdbeb9b0369b7f1b31fd7a4034` | `2026-08-11T11:27:32.793145+08:00` | `2026-08-11T11:27:32.793232+08:00` | `READ_OK` |
| `/home/rspip/cqc/pro/study/orientbench/dis/sug.md` | 47,119 | `fd532c1f12e713e6d9c55d6f37f109fb6d41afbf351ace7801cab6c3e6573e1d` | `2026-08-11T11:27:32.793266+08:00` | `2026-08-11T11:27:32.793368+08:00` | `READ_OK` |
| `/home/rspip/cqc/pro/study/orientbench/dis/collaboration_protocol.md` | 6,980 | `e3af9a71247f84c0b67730a7b8c794ab0221a51c8c7235d49ba9d374747c110c` | `2026-08-11T11:27:32.793429+08:00` | `2026-08-11T11:27:32.793469+08:00` | `READ_OK` |
| `/home/rspip/cqc/pro/study/orientbench/dis/C.md` | 6,177 | `e161b39d73ad51dcd348ed709e8c325c442a683c2ab5f03864f11338a84f1807` | `2026-08-11T11:27:32.793485+08:00` | `2026-08-11T11:27:32.793511+08:00` | `READ_OK` |
| `/home/rspip/cqc/pro/study/orientbench/dis/review_state.json` | 9,358 | `8bafa0bbfd6f22d7f1d12b8054f1cbef4e401b1eed4bb4fcce9ba31eacb2b4e8` | `2026-08-11T11:27:32.793525+08:00` | `2026-08-11T11:27:32.793552+08:00` | `READ_OK` |
| `/home/rspip/cqc/pro/study/orientbench/docs/server_migration_handoff_20260810.md` | 24,870 | `4faffeae34268edf81b88b5e6cb247d2ed4a28b3ef3ca2d005f91d34eb38c818` | `2026-08-11T11:27:32.793570+08:00` | `2026-08-11T11:27:32.793612+08:00` | `READ_OK` |
| `/home/rspip/cqc/pro/study/pth_data/readme.md` | 89,032 | `eb9ac9a172b49cc8063b91c2332f36829d0b3cf5f3a3667f2617d64258d10c9c` | `2026-08-11T11:27:32.793648+08:00` | `2026-08-11T11:27:32.793794+08:00` | `READ_OK` |

项目作用域内没有另一份适用的 `CLAUDE.md`。

### 3.2 HTTPS Git 与 clean tree

- origin: `https://github.com/ziyu24/orientbench.git`
- branch/default/upstream: `main` / `main` / `origin/main`
- receipt2 pre-pull HEAD: `6d8892a3793b2efcd8373ce8d509a6cf9872427c`
- pull command: `git pull --ff-only origin main`
- pull start/end: `2026-08-11T11:28:42.312424616+08:00` / `2026-08-11T11:28:48.349729400+08:00`
- pull exit/result: `0` / `Already up to date.`
- post-pull HEAD/upstream/HTTPS remote main: 三者均为 `6d8892a3793b2efcd8373ce8d509a6cf9872427c`
- post-pull index/worktree: clean

### 3.3 受保护对象、提交链与 receipt1

- `HEAD:dis/B.md` blob 为 `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`；ordinary/staged diff 检查均 exit `0`；未读取文件内容。
- `scientific_data_cutoff`、`source_execution_commit`、`control_base`、`housekeeping_commit/dispatch_base`、`post_pull_head` commit object 均存在。
- 固定祖先链四项检查均 exit `0`：

```text
a9067fb16d2bbd747dfe69789ac33a5911eb15fe
  -> cdf764c5a974030739a9992079bedb8b970fb2a7
  -> bc27506f7d7c0e47c4d67b202b9157bd4016a87a
  -> 2a70303e9d74313a15b71e1767b0b6ecdc05d2cc
  -> 6d8892a3793b2efcd8373ce8d509a6cf9872427c
```

- receipt1 report blob 动态核验为 `4fe331a6a683313150a4fb21cbabd432ffde0f6b`。
- receipt1 canonical contract archive 的 filter-aware blob 动态核验为 `11553a92b05b692a14bf9c4f21898a5c9e10d144`。
- 旧报告仍明确包含 `ABNORMAL_PREFLIGHT_FAILURE`、`NOT_ADJUDICATED` 与 Track M/D `NOT_RUN`，未被 receipt2 修改。

### 3.4 source runtime 与新路径

- source runtime：真实目录，共 79 个对象（74 files、5 directories）、0 symlink、0 unreadable、0 actual-user writable、0 mode write-bit objects。
- canonical absolute-path content-tree SHA-256：`2e9f7eb60b7de427b24faa8c91b0ef2017864d99cbc923b04bfe70b500085b43`，与合同精确一致。
- 曾执行一次使用相对路径的非 canonical 诊断，得到不同的路径敏感聚合值；该值未作为 source identity。随后按 housekeeping 的同一 absolute-path canonical algorithm 重算并通过，source runtime 未发生任何变化。
- receipt2 code root、runtime root 和本报告在启动时均不存在，preflight 无 collision。

## 4. Mandatory pinned reference provenance failure

合同第 5.3 节要求从服务器既有本地 Git object/checkout 或既有 sealed source evidence 动态核验：

```text
IML-DKFZ/fd-shifts@c4467aec134e99691359da209f811d91283fc1e3
rc_stats.py
rc_stats_utils.py
```

真实只读取证结果：

- 在 `/home/rspip/cqc/pro/study` 下枚举到 33 个 Git repositories。
- 对 33 个 repository 分别执行目标 commit object 检查，commit holder count=`0`。
- 在同一允许根下按文件名搜索 `rc_stats.py` 与 `rc_stats_utils.py`，命中数=`0`。
- 在 orientbench 与 `third_party` 中排除 `dis/B.md` 后搜索，只发现 6 个合同、计划或旧 generator 的文本引用；没有 pinned source bytes、Git object 或 checkout。
- 搜索开始/结束：`2026-08-11T11:31:02.075576353+08:00` / `2026-08-11T11:31:23.542066469+08:00`。
- 当前仓库直接执行 `git cat-file -e c4467aec134e99691359da209f811d91283fc1e3^{commit}` 真实失败。

旧 runtime 的 derived toy JSON 或旧 generator 中的 reference 字符串不能证明 pinned Git identity，也不能提供两份要求的 raw source bytes。合同明确禁止把字符串常量、自生成文件或手抄 expected 当作动态核验，并禁止下载、联网安装或补拉外部仓库。因此该必做 provenance/validator phase 无法合法闭合。

## 5. 停止与未执行阶段

该 failure 不是 Track M 的 `INSUFFICIENT_ASSETS`，而是合同明定的 mandatory validator/provenance execution failure。命中后停止以下阶段：

- receipt2 code/runtime 固定产物生成；
- Track M source inventory、raw-row AUGRC/AURC/NRC 与完整 risk-coverage 重算；
- 10,000 次同步 cluster bootstrap 与逐 replicate 比较；
- 五状态 production fixtures；
- Track D 四候选独立重建与 prior-outcome 全扫描；
- independent validator 与四项 isolated mutation；
- joint gate adjudication、manifest、protocol closure 与科学状态发布。

上述阶段均为 `NOT_RUN_DUE_TO_MANDATORY_REFERENCE_PROVENANCE_FAILURE`，不得以旧 summary 或源数字补写。receipt2 的 Track M 状态与 joint gate 均未发出。

## 6. 写入边界与后续要求

- 本轮唯一新增路径是本报告，另按项目规则 append-only 更新 `claude_code_and_supervisor.md`。
- receipt2 code root 与 runtime root 未创建；旧 source runtime 与全部 sealed assets 保持只读、未修改。
- GPU/download/installation/training/forward/inference/new outcome/annotation content/target-label tuning/manuscript edit 均未发生。
- planned commit scope：本报告与 append-only 监督日志。
- tracked report source：真实 preflight 与本地 pinned-source 搜索证据。
- tracked report self validation：`EXTERNAL_GIT_BLOB_ONLY`。
- receipt2 science/audit closure：`INCOMPLETE_DUE_TO_MANDATORY_REFERENCE_PROVENANCE_FAILURE`。

本轮 report path 已消费，禁止删除、覆盖或复用后重跑。若要再次验收，只能在 receipt 外预先把精确 pinned `fd-shifts@c4467...` Git object/checkout 以可核验方式配置到允许的持久路径，再由用户/监督端基于新的 `main` 下发新 round id 与全新 code/runtime/report 路径；不得在本轮下载或临时补造。
