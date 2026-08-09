---
round_id: orientbench-c-topjournal-feasibility-receipt-20260809
control_base: bc27506f7d7c0e47c4d67b202b9157bd4016a87a
source_execution_commit: cdf764c5a974030739a9992079bedb8b970fb2a7
scientific_data_cutoff: a9067fb16d2bbd747dfe69789ac33a5911eb15fe
source_runtime: outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809
runtime_root: outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt_20260809
server_report_path: dis/server_reports/orientbench-c-topjournal-feasibility-receipt-20260809.md
status: READY_FOR_SERVER_EXECUTION
gpu_authorized: false
download_authorized: false
training_authorized: false
inference_authorized: false
new_target_outcome_authorized: false
manuscript_edit_authorized: false
cc_recommendation: no
---

# OrientBench 顶刊可行性纠偏验收服务器合约

## 1. 唯一问题与不可改写的源状态

本轮是一次 **receipt-only 纠偏验收**，不是新科学实验，也不产生新科学 outcome。唯一问题是：能否从既有只读 feasibility runtime、既有 sealed Core 资产和既有官方取证中，独立重建并验证 Track M、Track D、联合 gate、provenance、validator 与 mutation 的全部证据链。

源执行的永久状态为：

```text
ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809
```

源执行中的全部数字永久标记为：

```text
DESCRIPTIVE_UNVERIFIED
```

无论 receipt 得到正向、负向或缺资产结果，都不得把源执行洗成正常、完整、已验证或正式科学结果。receipt 只裁定本次纠偏验收是否完整闭合，以及既有数字在独立重算后对应哪个预注册可行性状态。

`cc_recommendation: no`，因为本轮只执行已冻结的证据验收，不需要新的模型意见。不得调用 CC，不得把 CC/B 当最终裁决者。

## 2. 权限、只读边界与唯一写范围

服务器在仓库内外只能写入以下四类路径：

1. `top_journal_v3_reaudit_055/feasibility_receipt_20260809/**`
2. `outputs/persistent_artifacts/orientbench_topjournal_feasibility_receipt_20260809/**`
3. `dis/server_reports/orientbench-c-topjournal-feasibility-receipt-20260809.md`
4. `claude_code_and_supervisor.md`，仅 append-only

除此之外全部只读。尤其禁止创建、读取内容、修改、格式化、移动、删除、暂存、恢复或提交 `dis/B.md`；只允许核验其 Git blob/diff 元数据。禁止修改主稿、`dis/C.md`、`dis/sug.md`、`dis/review_state.json`、协作协议、旧报告、原 feasibility 代码 `top_journal_v3_reaudit_055/feasibility_gate_20260809/**`、`source_runtime`、r014/m069 sealed 资产、checkpoint、数据、split、阈值、matching、canonicalization、cluster、seed、score、metric 或 gate。

`source_runtime` 以及全部既有科学资产严格只读：不得删除、清空、覆盖、复用、改名、移动、patch、补写、backfill 或借 hard link/符号链接间接修改。新代码和新 runtime 必须从不存在的路径创建；发生路径碰撞时不得清理或换旁路路径。

禁止使用 GPU、下载数据集/模型/包、安装依赖、训练、forward、推理、打开候选 annotation 内容、计算新 target outcome 或用 target label 调参。网络只允许 HTTPS Git；不得使用 SSH。已存在仓库只允许 `git pull --ff-only`，禁止 merge、rebase、reset、clean、checkout、stash、force push 或改写历史。

## 3. Preflight、失败闭环与真实事件记录

任何科学验收前必须完成以下 preflight；不得用修复工作树或替代路径使其通过：

1. 完整读取所有适用的 `AGENTS.md`、`CLAUDE.md`、本合约、协作/交接规则和 `/home/rspip/cqc/pro/study/pth_data/readme.md`。对每个实际读取文件记录规范路径、bytes、SHA256、真实读取开始/结束时间和读取结果；规则或 readme 缺失/不可读即失败。
2. 核验 `origin` 为 `https://github.com/ziyu24/orientbench.git`，记录当前分支、远端默认分支、upstream、完整 pre-pull HEAD 和 HTTPS remote current branch。只运行 HTTPS `git pull --ff-only`；不能 fast-forward 即失败。pull 后立即冻结 `post_pull_head = git rev-parse HEAD`，并分别解析 `upstream_sha = git rev-parse @{upstream}` 与 `https_remote_current_branch_sha = git ls-remote https://github.com/ziyu24/orientbench.git refs/heads/<current_branch>`；必须满足 `post_pull_head == upstream_sha == https_remote_current_branch_sha`，且此时 index/worktree 干净。任一不等、upstream 缺失或 remote current branch 不存在即失败；不得携带 pre-existing ahead commit 进入本轮。
3. 核验 index 与 worktree 在执行前干净；不得删除、隐藏或恢复任何现有变化。核验 `dis/B.md` 的 Git blob 严格为 `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`，且其普通 diff、staged diff 均为空；不得读取文件内容。
4. 核验 `post_pull_head` 包含本合约。对 `scientific_data_cutoff`、`source_execution_commit`、`control_base` 和 `post_pull_head` 分别运行 `git cat-file -e <sha>^{commit}` 并要求 exit 0，再按下列固定方向运行 ancestry 检查并要求每条 exit 0：

   ```text
   git merge-base --is-ancestor a9067fb16d2bbd747dfe69789ac33a5911eb15fe cdf764c5a974030739a9992079bedb8b970fb2a7
   git merge-base --is-ancestor cdf764c5a974030739a9992079bedb8b970fb2a7 bc27506f7d7c0e47c4d67b202b9157bd4016a87a
   git merge-base --is-ancestor bc27506f7d7c0e47c4d67b202b9157bd4016a87a post_pull_head
   ```

   最后一条执行时必须用已冻结的 40-hex `post_pull_head` 实值替换字面 token。由此固定且只接受 `scientific_data_cutoff -> source_execution_commit -> control_base -> post_pull_head` 的祖先链；任何 object 缺失、方向相反或非祖先均失败。三个 YAML SHA 不是展示字段，还必须与所引用既有 manifests/资产的 source identity 交叉核验。未经验证的事实写 `unknown`，不得套用其它项目路径或状态。
5. 核验 `source_runtime` 是已存在、可读且不可写的目录；核验 `runtime_root`、新 code root 和新报告在启动时均不存在。任一新路径已存在即 collision，禁止删、覆、复用、改名或改用另一目录。
6. 核验四类授权写范围可以精确执行，且任何临时文件、日志、mutation 副本均能留在 `runtime_root` 内；不得使用未登记的 `/tmp`、`/dev/shm` 或仓库旁路目录。

tracked `execution_ledger.csv` 的边界固定为 `tracked_ledger_cutoff: PRE_SEAL_SCIENTIFIC_AUDIT_CLOSURE`：它只登记 preflight 至 tracked seal 之前的 scientific/audit 真实命令（包括失败命令），字段为 `phase, command, cwd, inputs, started_at, ended_at, exit_code, stdout_path, stdout_bytes, stdout_sha256, stderr_path, stderr_bytes, stderr_sha256`。旧称 `PRE_COMMIT_CLOSURE_ONLY` 在本合约中严格等价于这一更早的 pre-seal 截止点，绝不授权记录 seal 后但 commit 前的 Git 命令。时间来自命令 wrapper 在事件发生时记录的墙钟；退出码来自真实子进程。receipt 新事件不得使用文件 mtime、常量、猜测、事后重构或硬编码 `PASS/true/0` 代替。源执行中不存在或无法恢复的旧事件字段必须逐字段写 `SOURCE_FIELD_ABSENT`；不得用 mtime、当前时间、默认零、摘要文本或推断值 backfill。

final `git add`、staged name-status/diff-check、post-seal B/HEAD checks、`git commit`、`git push`、post-commit topology checks、HTTPS `git ls-remote` 和 published-object checks 全部发生在 tracked 内容封存之后，严禁写入或回填 `execution_ledger.csv`、access log、tracked report、runtime、validator、manifest 或 append-only 仓库日志。外层 wrapper 必须把这些事件的真实 command/cwd/start/end/exit/stdout/stderr bytes/SHA256 暂存在仓库外，并且只在 push attempt 结束后形成 `EXTERNAL_RECEIPT_OUTSIDE_REPOSITORY_ONLY`；具体 schema 见第 9 节。

任何 preflight 或后续必做阶段失败都使本次聊天状态为 `异常结束`。只要仓库、受保护文件和报告路径仍可安全写入，就必须先在唯一 tracked `server_report_path` 写入异常报告，列出失败点、已完成/未完成阶段、真实命令与证据；不得仅在聊天说明。若 Git/所有权冲突使报告无法安全落盘或发布，应保持现场不变，并在允许的 append-only 日志中记录失败；绝不能伪造报告、commit、push 或外部回执。

## 4. Receipt 固定产物

实现可自行组织函数与并行方式，但 generator 与 validator 必须是两个独立 entry point。以下 receipt 产物必须全部位于新的 `runtime_root`，文件名固定：

```text
protocol.json
preflight.json
execution_ledger.csv
access_log.csv
resource_telemetry.csv
track_m_source_inventory.csv
track_m_reference_check.json
track_m_metrics.csv
track_m_risk_coverage.csv
track_m_bootstrap_replicates.csv
track_m_bootstrap_comparison.csv
track_m_status.json
track_d_official_sources.csv
track_d_search_runs.csv
track_d_prior_outcome_hits.csv
track_d_asset_inventory.csv
track_d_status.json
joint_gate.json
validator.json
mutations/mutation_index.csv
evidence_manifest.json
protocol_closure.md
```

日志和四个 mutation 的 witness 可在 `runtime_root/logs/**` 与 `runtime_root/mutations/**` 下增加。`access_log.csv` 的定义固定为：

```text
access_log_cutoff: PRE_SEAL_SCIENTIFIC_AUDIT_ONLY
access_log_excludes_self == true
access_log_excludes_evidence_manifest == true
access_log_excludes_tracked_report == true
access_log_excludes_post_seal_external_outputs == true
```

它只登记 seal 前实际 scientific/audit inputs、实际 executed code、已经产生的 runtime outputs 和真实读取事件的规范 path、role、access mode、bytes、SHA256、schema、row keys/row count（适用时）、开始/结束时间与调用阶段。annotation 只能登记 filename/stat，不得打开或 hash 内容。`access_log.csv` 不记录自身的生成/读取，不记录随后生成的 `evidence_manifest.json` 与 tracked report，也不记录 final `git add`、staged checks、B/HEAD checks、commit、push、`ls-remote` 或任何 post-seal/external 输出；这些排除项必须显式写入 manifest classification，不能伪装成未访问。

全部 scientific/audit 计算、独立 validator 和 mutation 完成且文件句柄关闭后，冻结一个只读 snapshot。snapshot 必须把每个对象分类为 `PRE_SEAL_SCIENTIFIC_AUDIT_INPUT`、`PRE_SEAL_EXECUTED_CODE` 或 `PRE_SEAL_RUNTIME_OUTPUT`，并固定实际 path/bytes/SHA256/schema/keys；`access_log.csv` 作为已完成的 runtime output 进入 snapshot。`evidence_manifest.json` 只能从该 frozen snapshot 确定性生成并负责保存这些分类；不得扫描后来变化的 live tree 来补项。manifest 必须包含固定 self entry：

```text
manifest_self_path: evidence_manifest.json
manifest_self_bytes: N/A_SELF_REFERENCE
manifest_self_sha256: N/A_SELF_REFERENCE
manifest_self_classification: SELF_REFERENCE_NOT_INDEPENDENTLY_VALIDATED
```

manifest 还必须显式列出 `access_log.csv` 已覆盖与排除的类别、tracked report 为 `POST_MANIFEST_TRACKED_OUTPUT_EXTERNAL_VALIDATION`、post-seal artifacts 为 `EXTERNAL_RECEIPT_ONLY_NOT_REPOSITORY_EVIDENCE`。不得声称 manifest 预知或证明自身 bytes/SHA256，也不得把 tracked report 或 external receipt 的未来 hash 回填其中。

pre-seal validator 的闭合范围固定为 `pre_seal_validator_scope: FROZEN_SNAPSHOT_AND_PLANNED_OUTPUT`：它必须验证 frozen snapshot 的实际内容，以及由该 snapshot 确定生成的 manifest/report 计划 schema、必需字段、分类、N/A self token、科学状态和 pending external token；不能因 access-log 排除而漏验 manifest/report 的计划内容。随后实际写出的 tracked report 必须声明 `tracked_report_source: FROZEN_SNAPSHOT` 和 `tracked_report_self_validation: EXTERNAL_GIT_BLOB_ONLY`，记录 manifest 的实际 bytes/SHA256，但不得声称对自己的最终 on-disk/Git blob 做了独立验证。最终 tracked report 与其它实际 tracked outputs 由 post-seal external receipt 从发布后的 Git blobs 复核。

## 5. Track M：sealed measurement receipt

### 5.1 固定 Core、来源与字节身份

Core 固定为六个 unit：

```text
A: DIOR-R
B: DIOR-R
C: DIOR-R
D: FAIR1M
E: SODA-A
F: SODA-A
```

对 A–F 每个实际消费的 raw row、score、label/risk、cluster universe 和映射文件，逐项记录 bytes、SHA256、实际 schema、row count、sealed 物理顺序的 ordered row-key sequence SHA、排序后的完整 row-key set SHA、完整 cluster set（包括 zero-eligible cluster）及其排序 SHA。每项身份必须独立对照 **本轮 receipt 创建之前已存在** 的 r014/m069 sealed manifests，包括 `p3_selector/deployable_proxy_r014/reports/tta_inventory_r014.csv`、`provenance_r014.csv`、`evidence_manifest_r014.json` 以及 `outputs/persistent_artifacts/m069_fullval_reliability/{A,B,C,D,E,F}/manifest.json` 中适用的既有记录。还必须核对这些 manifests 自身的 bytes/SHA256 与来源身份。

receipt 生成的 inventory、源 feasibility runtime 的汇总表、服务器报告或 generator 输出都不能作为源资产自证。若既有 manifest 缺字段，写 `SOURCE_FIELD_ABSENT`；若任一 Core unit 的 byte-exact rows、全部固定 score 输入、完整 row keys 或完整 cluster universe不能由既有 sealed manifests 闭合，Track M 必须是 `INSUFFICIENT_ASSETS`。缺失必须用实际 stat/read/hash 错误和访问日志证明，不能从摘要、文件名或预期常量推断。

### 5.2 从 raw sealed rows 独立重算

只允许以下固定 score；不得 refit、替换、挑选或增加候选：

```text
raw_confidence = identity detection score
linear_source_frozen = existing sealed score+AR+size linear output; no refit
tta_angle = -u_axis
tta_localization = -(missing_fraction + iou_loss)
S0 = -(u_axis + missing_fraction + iou_loss)
learned_EQS = descriptive-only comparator; never drives a state or gate
```

从 raw sealed rows 重算，禁止从旧汇总表抄数字。risk 固定为：

```text
risk_cap3 = clip(angle_error / max(delta_theta_0.75(GT_AR), 1 degree), 0, 3)
residual = risk_cap3 / 3
```

不得改变 row eligibility、排序、angle 语义或风险缩放。每个 unit 必须先从 sealed eligibility 与完整 row keys 冻结唯一的 `unit_complete_eligible_row_key_sequence`，再按该序列对 residual 和全部必需 score 做 exact one-to-one join；禁止任一 score 自行定义 cohort。计算前必须同时满足：

```text
cohort_key_alignment_exact == true
cohort_nonfinite_count == 0
all_scores_paired_bootstrap_same_cohort == true
row_drop_policy = NO_ROW_DROP_ALLOWED
```

任一 residual/必需 score 出现 NaN 或 infinity，或任一 key 缺失、重复、额外、错位，Track M 立即为 `INSUFFICIENT_ASSETS`；不得按 score 单独 mask、drop、impute 或缩小 cohort。若底层文件/解析代码损坏到无法安全完成 stat/hash/schema/key 取证，则 execution abnormal，但仍禁止 drop 后继续。所有 score 的 AUGRC、AURC、NRC、完整 generalized risk-coverage curve、`Risk@70%`、`Risk@90%`、paired comparison 与 synchronized bootstrap 必须使用完全相同的 `unit_complete_eligible_row_key_sequence`、行数和 cluster membership。每个 unit、score 和 dataset aggregate 都必须重算并保存这些字段及实际 nonempty coverage。

AUGRC 固定使用 unique score threshold、整组 tie 同时进入、包含 `(coverage=0, generalized_risk=0)` 的未缩放 trapezoidal integration，其中 `GR(t)=(1/N)*sum_i residual_i*I(score_i>=t)`。固定 coverage `q` 只能选择 unique thresholds 中最小的实际 `coverage>=q`，并以该 accepted set 的 mean residual 报 selective risk；不得拆 tie 或看 outcome 后选阈值。DIOR/FAIR cluster 为完整 image；SODA 为 original mother scene；zero-eligible cluster 必须保留。dataset aggregate 必须先逐 unit 计算再 unit-equal 平均，禁止 pooled rows。

### 5.2.1 AURC/NRC 的唯一公式、tie、normalization 与边界

AURC/NRC 与 AUGRC/Risk@70/90 是不同的 sensitivity。AURC/NRC 固定使用下列离散 row-wise 定义，不能改成 trapezoid、unique-threshold curve、tie-group average 或其它 normalization。输入必须是同一 `unit_complete_eligible_row_key_sequence` 上、同 shape 且逐项 finite 的 `score` 与上文 `residual`；shape、key 或 finite precondition 不满足时按上一段 fail closed，绝不清洗或 drop。初始顺序就是已核验 ordered row-key sequence；不得重排来优化 tie。调用既有 sealed implementation 时必须断言并保存 `n_dropped=0`；任何非零值都是 `INSUFFICIENT_ASSETS`，不能消费其输出。

```text
n = number of rows in unit_complete_eligible_row_key_sequence
pi = stable_argsort(-score, kind=stable); equal-score ties retain sealed raw-row order
SR_k = (1/k) * sum_{j=1..k} residual_{pi_j}
AURC_model = (1/n) * sum_{k=1..n} SR_k

r_(j) = residual sorted ascending with stable sort
OR_k = (1/k) * sum_{j=1..k} r_(j)
AURC_oracle = (1/n) * sum_{k=1..n} OR_k
AURC_random = (1/n) * sum_{i=1..n} residual_i
denom = AURC_random - AURC_oracle
NRC = (AURC_model - AURC_oracle) / denom
```

所有中间量用 float64，unit 内不提前 round；AURC/NRC 越低越好且 NRC 不 clip 到 `[0,1]`。`n=0` 时四个 AURC/NRC 值均为 NaN、`degenerate=true`；`abs(denom)<1e-12` 且 `n>0` 时 NRC=NaN、`degenerate=true`；其它边界 `degenerate=false`。逐值比较固定为 `atol=1e-12, rtol=0`。unit 结果仍按 unit-equal arithmetic mean 聚合；禁止 pooled rows。AUGRC 与 Risk@70/90 继续严格采用上一节的 whole-tie unique-threshold 规则，不受此处 row-wise stable-tie 定义影响。

退化不得产生或替换 Track M 第六状态。若 `n=0`、NRC denominator 退化或必需 metric NaN 是因为所需 byte-exact row/score/cluster/fixed-algorithm/replicate evidence 缺失，才适用 `INSUFFICIENT_ASSETS`。若上述证据完整但数学上仍退化、相等边界导致五态无法唯一判定，或 production/validator 无法按冻结定义得到唯一状态，则不得输出任何 Track M 科学状态，必须写 `track_m_state: NOT_EMITTED`、`scientific_gate: NOT_ADJUDICATED`、`receipt_execution: ABNORMAL_EXECUTABLE_AUDIT_FAILURE`；这属于“无法唯一状态=executable-audit failure”，必须异常结束，不得洗成正常、借 CI 判负或更换 gate。

既有 sealed implementation 身份同时固定为：

```text
orientbench/metrics/risk_coverage.py
git_blob=566a3a84b6fffa3315faec606edf20ee9bf3843b
git_blob_bytes=3165
git_blob_sha256=ae9ab7e3c8b745f24b3cc60048dbd143cafd8da89b6a8e779fab37326d2f6aaa

orientbench/metrics/nrc_auc.py
git_blob=fcd55fd7bd99d55d3dc889ae0100c2e99913787c
git_blob_bytes=2774
git_blob_sha256=e99206475b4015b563ccc5107991d326d85c330de346dc2452c4f1738afc52a0
```

服务器必须对 `scientific_data_cutoff`、`source_execution_commit`、`control_base` 和 `post_pull_head` 分别用 `git rev-parse <sha>:<path>`、`git cat-file blob` 动态核验上述两个 blob identity、raw Git bytes 与 SHA256；不得只抄常量。generator implementation A 从 raw sealed rows 调用身份已核验的 sealed implementation；validator implementation B 从 raw sealed rows按上列公式独立实现，禁止 import generator、implementation A 或其 summary。两套实现逐 unit、dataset aggregate 和适用 bootstrap 字段比较；任一差异或 identity 不符均失败，不能自由选择较有利实现。

### 5.3 动态核验 pinned AUGRC reference

必须从服务器已存在的本地 Git object/checkout 或既有 sealed source 证据动态核验：

```text
IML-DKFZ/fd-shifts@c4467aec134e99691359da209f811d91283fc1e3
rc_stats.py
rc_stats_utils.py
```

记录实际仓库路径、remote、`git rev-parse`、commit object、两个源文件的 Git blob/bytes/SHA256 和访问日志；不得下载、联网安装或把字符串常量出现当作身份验证。使用该 pinned source 的真实 reference functions，在独立进程对含 tie 的 binary、continuous 和 boundary vectors 现场生成 reference outputs，再与 receipt 实现以 `atol=1e-12, rtol=0` 比较。reference expected 必须来自该进程的实际输出，不能来自 generator 常量、手抄答案或恒真布尔。pinned 源身份或动态行为无法闭合属于必做 validator/provenance 失败，不能硬编码通过。

### 5.4 完整 bootstrap 重放

bootstrap 固定为：

```text
seed = 20260809
replicates = 0..9999 exactly
CI = percentile 95%
```

每个 unit/dataset 必须从 sealed 完整 cluster universe（含 zero-eligible cluster）重放；同一 replicate 内所有 score 使用完全相同的 synchronized cluster multiplicities。抽样 RNG、cluster 顺序、worker 合并顺序和序列化算法必须从既有 sealed protocol/code 与 source runtime 证据动态恢复并记录 SHA，禁止根据旧数字猜算法。无法唯一恢复时写 `SOURCE_FIELD_ABSENT` 并判 `INSUFFICIENT_ASSETS`，不得另选能接近汇总 CI 的算法。

validator 必须独立生成 replicate `0..9999`，逐 replicate 比较 source runtime 中保存的全部字段，包括 replicate id、unit/dataset、score/baseline、cluster-multiplicity witness/hash、metric/delta 值和适用状态字段；整数/字符串/hash 精确相等，浮点以 `atol=1e-12, rtol=0`。随后独立重算并比较全部 point estimate、percentile CI、Track M 唯一状态和 joint gate。只比较最终 CI、抽样几行或自生成文件自身哈希不算完成。

```text
bootstrap_ci_role: REPORT_ONLY_NOT_STATE_DRIVER
```

paired cluster bootstrap 的全部 replicate、CI 与 source evidence 必须完整重算、逐字段比较并报告；它们是 uncertainty evidence，不参与下节 deterministic feasibility state 的触发、优先级或升级。CI 跨零、CI upper bound 非负或 CI 显著本身都不得自动产生负/正状态。

### 5.5 五个互斥状态

定义所有 loss/risk 指标均为越低越好，固定 equal-budget nonlearned baseline 集合为 `raw_confidence`、`linear_source_frozen`、`tta_angle`、`tta_localization`。对每个 Core dataset aggregate `d`、baseline `b` 和指标 `m` 固定 `delta_m(d,b)=m(S0)-m(b)`；因此 `delta<0` 表示 S0 更好，`delta>0` 表示 baseline 更好，`delta=0` 表示相等。paired 95% CI 另行保存但不进入状态谓词。Track M 必须按下列优先级只输出一个状态：

1. `INSUFFICIENT_ASSETS`：且仅当任一 A–F unit 缺少所需的既有 sealed manifest、byte-exact raw row/score、完整 row keys/cluster universe、固定抽样算法或逐 replicate source evidence，因而无法完成规定重放。资产齐全但 metric 数学退化不属于本状态。
2. `METRIC_REVERSAL`：无更高优先级状态，且存在某个 Core dataset aggregate `d` 与某个 baseline `b`，使 `delta_NRC(d,b)<0 OR delta_AURC(d,b)<0`，同时 `delta_AUGRC(d,b)>0 OR delta_Risk@70(d,b)>0 OR delta_Risk@90(d,b)>0`。即 S0 在 NRC/AURC 看似更好，但同一 equal-budget nonlearned baseline 在至少一个预定主指标上严格更好；相等不算 reversal。
3. `BASELINE_DOMINATED`：无 metric reversal，且存在某个 Core dataset aggregate `d` 与某个 baseline `b` 满足 `delta_AUGRC(d,b)>0`，即该 baseline 的 AUGRC 严格低于 S0；相等不算 dominated。
4. `SENSITIVITY_UNSTABLE`：无以上状态，且在任一源协议预先规定、可由 sealed assets 直接推导的 matching、unmatched、near-square 或 canonicalization sensitivity 中，S0 相对同一 baseline 的 deterministic point-estimate 方向由严格更好 `delta_m(d,b)<0` 翻为严格更差 `delta_m(d,b)>0`。CI 不参与方向或状态判定。
5. `ROBUST_CANDIDATE`：全部 Core 资产完整；对每个 Core dataset aggregate 与四个 baseline 均有 `delta_AUGRC(d,b)<0`；`Risk@70%` 与 `Risk@90%` 从不反转；AURC/NRC 和全部预先规定 sensitivities 从不反转；`learned_EQS` 不参与决定。bootstrap CI 只报告，不参与本状态。

必须用真实或确定性合成的最小 fixture 覆盖上述五个且仅五个分支，并证明每个 fixture 只命中一个状态；测试调用实际 production state function，expected 由上述规则独立声明，禁止复制 production 分支或写恒真断言。实际证据缺失时诚实输出 `INSUFFICIENT_ASSETS`，仍继续完成所有可执行的 Track M 盘点、Track D、gate、validator 和报告，不补造资产。若完整证据无法按上述 deterministic point-estimate predicates得到唯一状态，则按 executable-audit failure 处理，禁止增设状态、用 bootstrap CI 补洞或事后改 gate。

## 6. Track D：official evidence 与资产/污染 receipt

固定审计四个候选，不因前一候选失败而停止：

```text
AI-TOD-R
UAV-OBB
ShipRSImageNet (backup)
ICDAR-MLT (auxiliary only; not a remote-sensing gate dataset)
```

### 6.1 独立事实重建

从 `source_runtime` 已保存的 official body/header/meta 原始文件分别重算 URL、retrieval date、HTTP status、redirect chain、content type、bytes、SHA256、source date、license/use terms、version、split、image/annotation metadata、OBB/angle/vertex-order/clockwise-ignore/difficult 语义。body、header 和 meta 必须相互核对；不得消费 source generator 的 `license_ok`、`angle_ok`、`present`、`eligible`、`contaminated`、`common_family_ok` 或任何 summary/gate bool 作为真相。

官方证据缺失、矛盾或无法支持事实时写 `SOURCE_FIELD_ABSENT`/`unknown` 并保留证据，不得联网补下载数据或猜测。validator 必须从 raw official bytes 和实际搜索/stat/hash 证据独立派生 remote-sensing 身份、license、angle contract、presence、common detector-family set、new-family 条件、target-label-tuning 条件、contamination facts 和候选状态。

### 6.2 真实 prior-outcome 与本地资产搜索

对每个候选名称、别名及其与 `prediction|feature|score|risk|metric|bootstrap|report|endpoint` 的组合，分别执行并保存命令/根目录/排除项/起止时间/退出码/stdout/stderr bytes 与 SHA，以及逐 hit adjudication：

1. Git-tracked text；必须显式排除 `dis/B.md`，不得读取其内容。
2. Git-ignored 与 tracked 的 `outputs/persistent_artifacts/**`；必须使用能覆盖 hidden/ignored 文件的真实搜索，不能让默认 ignore 规则造成假阴性。
3. 项目 manifests、reports 与已登记 artifact indexes。
4. `/home/rspip/cqc/pro/study/pth_data/readme.md`。
5. dataset root 的 filename/stat-only 视图；只记录路径、类型、size、权限与 stat 结果，不打开、decode 或 hash 候选 annotation 内容。

资产存在必须由真实 stat 和适用文件的 bytes/SHA256/schema/兼容环境证据证明；资产缺失必须由覆盖预定根目录的实际枚举/stat failure、命令范围和日志证明。不得把 source inventory 中的 `ABSENT`、空 hit 表、generator bool、路径常量或未搜索到的摘要当作证据。对 config、checkpoint、environment、license/body 等非 annotation 资产记录实际 hash；annotation 仅 filename/stat。

每个候选保留全部事实。generator 只允许保存 raw official body/header/meta、search hits、stat/hash/load witness，不得产出或注入 license/angle/presence/contamination/family/eligible 的判定 bool；以下 primitive 与状态必须由 independent validator 从 raw evidence 派生。

四个 failure 的触发谓词精确冻结为：

```text
CONTAMINATED iff prior_exact_outcome_or_endpoint_evidence_count > 0

LICENSE_BLOCKED iff official_license_evidence_count == 0
  OR stored official license evidence forbids required academic processing or redistribution
  OR stored official use terms are incompatible with the planned research use

INCOMPATIBLE_ANGLE_CONTRACT iff unique_conversion_proven == false

MISSING_ASSET iff dataset_present == false
  OR compatible_exact_config_present == false
  OR compatible_exact_checkpoint_present == false
  OR compatible_exact_environment_present == false
  OR compatible_exact_parser_present == false
  OR any required asset hash preflight or non-inference load preflight failed
```

`prior_exact_outcome_or_endpoint_evidence_count` 是逐 hit adjudication 后的非空 exact evidence 数，扫描域必须全部包含：显式排除 `dis/B.md` 的 Git-tracked text；tracked 与 ignored persistent artifacts；项目 manifests/reports/artifact indexes；`pth_data/readme.md`；dataset root filename/stat-only 视图。任何真实 prediction、feature/score endpoint、risk、metric、bootstrap、report 或 same-endpoint consumption witness 都计数；空表、未覆盖 ignored 文件的搜索或 generator 声明不等于零证据。

`official_license_evidence_count` 只计入 `source_runtime` 中 bytes/SHA256 闭合的 stored official body/header/meta 所直接支持的许可证据；非官方摘要或 generator bool 不计。`unique_conversion_proven` 只有在不打开候选 annotation 的前提下，stored official annotation/format 文档已唯一确定 OBB fields、角度范围与方向、顶点顺序、long-side/canonicalization、near-square/degenerate 和 ignore/difficult 到冻结语义的转换时才为 true；缺失、矛盾或多义一律为 false。dataset 仅以固定根的 filename/stat 证明 presence；exact config/checkpoint/environment/parser 分别要求预定路径、bytes/SHA256、兼容版本及安全的 non-inference load/parse preflight 全部闭合，任一真实缺失或校验失败即命中 `MISSING_ASSET`。

validator 在保存四组原始 true/false predicate 与 evidence paths 后，按以下 precedence 给出唯一状态：

```text
CONTAMINATED > LICENSE_BLOCKED > INCOMPATIBLE_ANGLE_CONTRACT > MISSING_ASSET
```

只有四个 failure predicate 全为 false，且至少三个 detector family 的同一公共集合具备闭合的 exact config/checkpoint/environment/parser/hash 时，状态才是 `ELIGIBLE_CANDIDATE`。失败状态 precedence 只决定最终标签，不得删除较低优先级事实。`ShipRSImageNet` 只能作遥感 backup；`ICDAR-MLT` 仅作 auxiliary，永远不能计入两个独立遥感数据集。

## 7. 联合 gate：固定、互斥且 negative 优先

validator 必须从 Track M raw 重算状态与 Track D raw evidence 派生事实，不得读取 generator 的 joint gate token。三个科学 gate 按以下顺序互斥求值，禁止换 gate、降低门槛或用 execution status 代替科学状态：

1. `FAIL_TO_MEASUREMENT_ONLY`：只要有证据证明任一预指定 negative condition 即成立。negative conditions 为：Track M 是 `METRIC_REVERSAL`、`BASELINE_DOMINATED` 或 `SENSITIVITY_UNSTABLE`；少于两个彼此独立的遥感 OBB 候选是 `ELIGIBLE_CANDIDATE`；两个合格数据集不存在同一组至少三个 detector family；该公共集合没有至少一个未参与 old Core 开发的 family；任一所需 license/angle contract 不闭合；或未来需要任何 target-label tuning。任一 negative 都优先于 inconclusive，并完整记录其它条件的 true/false/evidence path。
2. `INCONCLUSIVE_FEASIBILITY`：仅当 Track M=`INSUFFICIENT_ASSETS`，且 Track D 没有独立证明上列任何 negative condition。它不授权方法研究，默认进入 measurement-only writing。
3. `PASS_TO_METHOD_DESIGN`：当且仅当 Track M=`ROBUST_CANDIDATE`，至少两个彼此独立的遥感 OBB 数据集为 `ELIGIBLE_CANDIDATE`，二者支持同一组至少三个 detector family，该集合至少一个 family 不在 old Core，且不需要任何 target-label tuning。

`PASS_TO_METHOD_DESIGN` 也只允许未来另起协议并再次取得用户批准；不授权下载、训练、推理、label access、改稿或方法实验。若 Track M 因资产齐全但数学退化或其它 executable-audit failure 未能输出五态之一，则三个 joint gate 均不得求值，必须记录 `scientific_gate: NOT_ADJUDICATED` 并 execution abnormal；不得把它改写为 `INCONCLUSIVE_FEASIBILITY`、发明第四个科学 gate 或包装为 PASS。

## 8. 独立 validator 与四个真实 mutation

validator 必须是与 generator 分离的 entry point，不得 import generator module，不得信任或以 generator 的 gate、state、summary、`PASS` 字段、expected hash 表或硬编码布尔为判据。它必须从 sealed raw rows、既有 manifests、保存的 official body/header/meta、真实 search/stat/hash evidence 和 receipt 输出的逐 replicate 明细独立重算 inventory、metrics、五状态、Track D precedence、共同 family/new-family/target-tuning 条件和联合 gate。

在 `runtime_root/mutations/**` 的四个彼此隔离副本中分别做真实 mutation；每个副本都从同一 pristine receipt evidence 建立，sealed source 始终只读，且每次只能改变指定对象：

1. `source_hash`：改变一个既有 source asset 的 expected SHA 字段，不改变源文件。
2. `bootstrap_replicate`：改变一个指定 replicate 的一个 metric/delta 字段。
3. `track_d_evidence_fact`：改变一个由 official/search/stat raw evidence支持的 license、angle、presence、contamination 或 family fact。
4. `joint_gate_clause`：改变一个必要 gate clause 的保存值，例如 common-family/new-family/target-label-tuning 条件，不修改 validator 代码。

四次均必须实际运行同一个独立 validator 并 nonzero exit，且错误必须指向被变异对象；一个 mutation 通过或未执行即 validator phase 失败。每项保存 pristine/mutated path、bytes、SHA256、最小 diff witness、command、cwd、started_at、ended_at、exit code、stdout/stderr 原始日志及 SHA256。不得通过 mock gate token、预设失败 flag、修改 validator、恒真/恒假断言或沿用上一次副本制造非零退出。

## 9. 资源、报告、Git 与 external receipt

本轮不需要 GPU；CPU 只按实际工作量使用并记录 process/child count、CPU、RSS 与 affinity，不得伪造利用率。所有 pre-seal scientific/audit inputs、executed code 与 runtime outputs 都必须有 bytes/SHA256/schema/keys 及按第 4 节截止的 access-log evidence；manifest self、tracked report 和 post-seal/external outputs 必须使用第 4/9 节的显式排除分类与 external verification，不能伪称存在 access-log self coverage。缺字段如实标记。不得覆盖新 runtime，不得生成第二份 tracked report、第二个 report 路径或聊天附件。

唯一 tracked `server_report_path` 必须明确包含：

- 源执行状态 `ABNORMAL_FAILED_EXECUTION_FEASIBILITY_20260809`，以及源数字状态 `DESCRIPTIVE_UNVERIFIED`；
- pre-seal scientific/audit closure（全部 seal 前必做 phase、completed/omitted phase 及 reason、execution failure、technical stop）；tracked report 不得预判 final add/staged checks/commit/push/external receipt；
- Track M 唯一状态、每项 metric/bootstrap/reference/state-test 证据；
- Track D 四候选的全部事实、precedence、状态与搜索/stat/hash 证据；
- 联合 gate 的每个 clause、negative precedence 和唯一结论；
- independent validator 与四个 isolated mutation 的命令、exit、日志和 witness；
- 所有缺失、`SOURCE_FIELD_ABSENT`、`unknown`、失败和 `PROPOSED_DEVIATION`；任何科学含义偏离均未获授权并必须停止；
- 四类授权路径的实际 pre-seal changed/untracked 清单与 planned commit scope、B blob pre-seal 不变、GPU/下载/训练/推理/新 outcome/改稿均未发生；tracked report 不得声称 final `git add`、staged name-status/diff-check、post-seal B/HEAD check、commit 或 push 已发生；
- `sug_genuinely_exhausted: true|false` 只回答截至 `PRE_SEAL_SCIENTIFIC_AUDIT_CLOSURE` 的 scientific/audit 阶段是否逐条穷尽；完整执行状态仍为 `PENDING_EXTERNAL_RECEIPT`，不得以脚本退出零代替逐条证明。

tracked report、manifest 和所有计划提交内容完成后，外层 wrapper 必须先在仓库外捕获这些字节的 seal snapshot，然后宣布唯一截止点 `tracked_seal_point: TRACKED_CONTENT_SEALED_BEFORE_FINAL_GIT_ADD`。同时固定：

```text
final_git_add_phase: FINAL_GIT_ADD_IS_POST_SEAL
post_seal_no_tracked_writes == true
post_seal_artifacts: EXTERNAL_RECEIPT_ONLY
```

seal 后禁止回写、touch、格式化、重算或补齐任何 code/runtime/report/manifest/validator/access-log/append-only 仓库文件。服务器结果必须恰好形成一个 commit。seal 后才可显式运行 final `git add`；不得无差别 stage。随后运行 final `git diff --cached --name-status`、`git diff --cached --check`、授权路径全集、`dis/B.md` staged/unstaged diff 与 blob、当前 HEAD 等于 `post_pull_head` 等检查。上述 final add/check 的真实命令与输出全部只进入 external command ledger，不得回填 tracked report/ledger。commit 后必须在仓库外捕获并核验 `HEAD^ == post_pull_head`，且 `rev-list --count post_pull_head..HEAD == 1`；同时核验 HEAD 只有一个 parent、commit changed paths 完全属于授权范围、B blob 仍等于 preflight 值。任一不满足说明 seal 后改写、携带预存 ahead、产生多 commit/merge commit 或越界，必须异常。push 必须通过 HTTPS 且禁止 force。

tracked report、validator、manifest 或其它 commit 内文件不得声称预知包含自身的 final commit。最终 tracked 内容固定写：

```text
final_commit_sha: POST_COMMIT_EXTERNAL_RECEIPT
git_publish_status: PENDING_EXTERNAL_RECEIPT
```

外层 wrapper 必须为 commit/push/post-commit checks/HTTPS `ls-remote` 的 stdout 与 stderr 捕获独立原始字节；在 push attempt 完成后，只在仓库外生成一份 external receipt，最少包含：

```text
external_receipt_storage: EXTERNAL_RECEIPT_OUTSIDE_REPOSITORY_ONLY
post_pull_head: <40-hex captured before any receipt write>
tracked_seal_snapshot_sha256: <external hash over sealed repository-bound bytes>
post_seal_tracked_snapshot_sha256: <same external hash recomputed after publication>
post_seal_no_tracked_writes: true|false
local_final_head: <40-hex or absent-on-commit-failure>
head_parent: <40-hex or absent>
commit_count_from_post_pull_head: <actual integer or absent>
remote_current_branch_sha: <40-hex or absent>
published_report_bytes_sha256: <actual pair or absent>
published_manifest_bytes_sha256: <actual pair or absent>
publication_complete: true|false
external_receipt_command_ledger:
  - phase, command, cwd, started_at, ended_at, exit_code,
    stdout_bytes, stdout_sha256, stderr_bytes, stderr_sha256
```

`external_receipt_command_ledger` 必须逐项包含真实 seal snapshot、final `git add`、`git diff --cached --name-status`、`git diff --cached --check`、授权 scope、post-seal B/HEAD checks、`git commit`、topology checks、HTTPS `git push`、HTTPS `git ls-remote`、published Git-blob checks 和 post-publication seal-hash comparison；每项记录真实 command/cwd/started_at/ended_at/exit_code/stdout/stderr bytes/SHA256。未执行项写 absent + reason，不得用 tracked ledger 或预期值补齐。成功 push 后从仓库外运行 HTTPS `git ls-remote`，要求 remote current branch SHA 等于 `local_final_head`，并从已发布 Git blobs 复核 tracked report 与所有实际 tracked outputs；对 report 所声明的 runtime manifest hash 另与 sealed local manifest bytes 核对，不得冒充不存在的 remote blob。还必须要求 `post_seal_tracked_snapshot_sha256 == tracked_seal_snapshot_sha256`，否则证明 seal 后发生写入并异常。external receipt 只能保存在不写仓库的外层进程输出/监督通道；不得写入 report、runtime、validator、manifest、`claude_code_and_supervisor.md`，不得追加第二个 commit或制造自引用。

聊天状态只能由这份 external receipt 判定：仅当 `publication_complete=true`、`post_seal_no_tracked_writes=true`、两次 seal snapshot hash 相等、`HEAD^ == post_pull_head`、commit count 恰为 1、remote SHA 等于 local final SHA、published Git-blob checks 闭合，且 tracked pre-seal closure 已完整时，才可选择 `正常执行完毕`；任何 absent、失败或不一致都必须选择 `异常结束`。tracked report 的 `PENDING_EXTERNAL_RECEIPT` 或 generator/validator 的 `PASS` 绝不能决定聊天状态。

科学负结果或真实缺资产可以是完整 receipt；它们不自动等于执行异常。相反，任一必做 phase 缺失、source runtime 不可用、provenance gap 未按规则落为可判定缺资产、reference/validator/mutation 失败、越界写入、commit 数不等于一、HTTPS push 或 external receipt 失败，都使本次执行异常。

## 10. 服务器聊天唯一格式

服务器最终聊天严格只能在以下两个完整模板中二选一。只能有一对 wrapper、一个状态短语；不得添加路径、SHA、解释、列表、前后缀或其它字符。详细证据只写唯一报告。

只有所有 receipt phases、independent validator、四个 mutation、唯一 commit、HTTPS push 和 external receipt 全部闭合时使用；科学结论为负也可以使用：

```text
👇👇👇👇👇👇

正常执行完毕

👆👆👆👆👆👆
```

任一必做项缺失、runtime 不可用、provenance gap、validator/mutation/Git 失败或无法安全发布时使用：

```text
👇👇👇👇👇👇

异常结束

👆👆👆👆👆👆
```
