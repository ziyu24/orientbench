# OrientBench 顶刊可行性审计服务器执行合约

本文件是本轮服务器唯一有效的活动指令。服务器必须以可复核证据回答一个问题：在不产生任何新目标域结果的前提下，现有密封资产是否同时支持稳定的 Track M 候选和可执行的 Track D 数据集组合，从而仅允许起草下一轮方法协议。任何口头推断、摘要数字或事后改写 gate 都不能替代本合约。

## 固定身份

以下值必须逐字保留在协议、报告和证据清单中：

```yaml
round_id: orientbench-c-topjournal-feasibility-20260809
control_base: f2aeeb2edd177f6eb62c390042ea74068316570d
scientific_data_cutoff: a9067fb16d2bbd747dfe69789ac33a5911eb15fe
status: READY_FOR_SERVER_EXECUTION
server_report_path: dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md
runtime_root: outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809
gpu_authorized: false
download_authorized: false
training_authorized: false
inference_authorized: false
new_target_outcome_authorized: false
cc_recommendation: no
```

`cc_recommendation: no` 的理由是本轮只执行预注册的资产与可行性审计，不需要新的模型意见。

本轮不是 `r020`，不是对 `r019` 的修复，也不是新的科学终点。`r019` 的固定判定为：

```text
INVALIDATED_R019 / PROTOCOL_DRIFT_R019 / FAIL_IMPLEMENTATION_R019 / FAIL_TIMELOCK_R019
```

`r019` 的所有数字只能标记为 `INVALIDATED_R019_DESCRIPTIVE_ONLY`。不得把它们恢复为正式结果、gate 证据或新目标域 outcome；本轮不得修复、续跑或重解释 `r019`。

## 授权边界与禁止事项

`gpu_authorized`、`download_authorized`、`training_authorized`、`inference_authorized` 和 `new_target_outcome_authorized` 均为 `false`，没有隐含例外。不得使用 GPU，不得下载数据集归档或模型，不得安装包，不得训练或推断，不得打开目标标注来计算 outcome，也不得用目标标签调参。为核验 Track D 而读取官方 HTML、README 或 license 文本是允许的证据检索，不构成数据集下载；其取证要求见 Track D。

服务器只可写入以下四类路径，除此之外一律只读：

1. `top_journal_v3_reaudit_055/feasibility_gate_20260809/**`
2. `outputs/persistent_artifacts/orientbench_topjournal_feasibility_20260809/**`
3. `dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md`
4. `claude_code_and_supervisor.md`，仅可 append-only

不得创建第二份报告、临时旁路目录或未登记的日志。进程调度、内部文件名和表格格式可以自行决定；数据、split、seed、baseline、matching、unmatched 处理、canonicalization、near-square 定义、NMS、score、cluster、metric、bootstrap、状态映射和 joint gate 不得漂移。确有必要的变更只能记为 `PROPOSED_DEVIATION`；任何会改变科学含义的变更都必须停手并等待用户授权，不能先执行后补批。

## 启动预检与可完成语义

服务器必须先完成并记录以下预检，未通过时不得进入科学审计：

1. 完整读取所有适用的 `AGENTS.md`、`CLAUDE.md` 和 `pth_data/readme.md`，记录实际读取路径、字节数与 SHA256。
2. Git 只允许通过 HTTPS 执行 `git pull --ff-only`。核验当前分支（current branch）、默认分支、upstream、完整 HEAD、remote main、origin URL，以及 index/worktree 均干净；不得用 merge、rebase、reset、clean、checkout 或 stash 消除问题。
3. 核验受保护文件 `dis/B.md` 的 blob 严格等于 `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`。不得创建、修改、格式化、移动、删除、暂存、恢复或提交该文件。
4. 核验 `runtime_root` 尚不存在。若已存在，禁止删除、清空、覆盖、复用或改名旧目录；该碰撞属于技术早停。
5. 核验本合约四类写路径、只读科学资产、执行程序和访问控制均可审计。

只有仓库/规则冲突、受保护文件异常、runtime collision、访问控制失败或 executable-audit failure 可以触发 `EARLY_STOP_TECHNICAL`。以下情况必须作为已经完成审计的负面可行性发现继续收集证据，不能技术早停：资产缺失、数据污染、指标反转、被基线支配、角度语义不兼容、license 阻塞。负结果或缺资产仍可能构成 `FULL_COMPLETION`。

## Track M：密封测量资产审计

### Core 单元与逐字节资产账本

先做 inventory，再计算任何指标。Core 固定为六个单元：

```text
A: DIOR-R
B: DIOR-R
C: DIOR-R
D: FAIR1M
E: SODA-A
F: SODA-A
```

可同时盘点 `r019` 的 DOTA 单元，但它们必须始终标记为 descriptive-only，不能进入 Core gate。

每个实际消费的 artifact 都必须登记：路径、角色、source commit 或 manifest、字节数、SHA256、schema、row count、unique row-key witness、cluster count、cluster set SHA，以及 actual access log。不得从汇总表、图或报告反推 row-level 数据。如果任一 Core A-F 单元缺少逐字节一致的 row-level risk，或缺少下列全部必要 score 列，则 Track M 必须返回 `INSUFFICIENT_ASSETS`；仍须完成其余可执行盘点与 Track D，不得虚构或拟合缺失行。

固定英文账本字段为：`path, role, source commit/manifest, bytes, SHA256, schema, row count, unique row-key witness, cluster count/set SHA, and actual access log`。

### 固定 score

只允许下列 reliability score；定义与方向不得改变：

```text
raw_confidence = identity detection score
linear_source_frozen = existing sealed score+AR+size linear output; no refit
tta_angle = -u_axis
tta_localization = -(missing_fraction + iou_loss)
S0 = -(u_axis + missing_fraction + iou_loss)
learned_EQS = descriptive-only comparator, never candidate driver
```

`raw_confidence` 必须是 identity detection score。`linear_source_frozen` 必须直接使用已经密封的 score+AR+size linear 输出，禁止 refit。任何缺失 score 都不得通过模型拟合重生；如果逐字节输入列已存在，可以按上述代数式计算 `tta_angle`、`tta_localization` 或 `S0`，但必须记录输入哈希、计算命令、输出哈希和行级一致性核验。`learned_EQS` 只能作 descriptive-only comparator，永远不能驱动候选状态。

### 固定 risk、coverage 与 AUGRC

只可使用 `r014/r019` 已冻结的连续 orientation severity，并仅作下列缩放；不得改变样本排序、eligibility 或角度定义：

```text
risk_cap3 = clip(angle_error / max(delta_theta_0.75(GT_AR), 1 degree), 0, 3)
residual = risk_cap3 / 3
```

用于 AUGRC 的 `residual` 固定在 `[0,1]`。同时必须报告原始 `risk_cap3`，以便与旧结果作 backward comparison。

阈值 `t` 的 generalized risk 固定为：

```text
GR(t) = (1/N) * sum_i residual_i * I(score_i >= t)
```

AUGRC 必须对 unique-threshold generalized-risk/coverage 曲线做未缩放的 trapezoidal integration，并包含 `(coverage=0, risk=0)`。所有同分 tie group 必须整体进入，严禁拆分。binary residual 的 AUGRC 范围是 `[0,0.5]`。

实现必须在 binary toy vector 和 continuous toy vector 上，以 `atol=1e-12, rtol=0` 复现固定官方参考：

```text
IML-DKFZ/fd-shifts@c4467aec134e99691359da209f811d91283fc1e3
rc_stats.py
rc_stats_utils.py
```

运行时不得导入、安装或依赖 floating network package；固定参考只能被本地、可审计地复现。

每个 score、unit 和 dataset aggregate 都必须输出：AUGRC、AURC/NRC sensitivity、完整 risk-coverage 数据、`Risk@70%`、`Risk@90%` 与 nonempty coverage。固定 coverage `q` 只在 unique score thresholds 上求值，选择阈值诱导 coverage 中最小的 `coverage >= q`，报告这个实际 coverage，并以 accepted-set mean residual 计算 selective risk。不得拆分 tie group，也不得看到 outcome 后挑选最低 risk 阈值。

cluster 固定为：DIOR/FAIR 使用 image cluster；SODA/DOTA 使用 original mother-scene cluster；zero-eligible cluster 也必须保留。dataset aggregation 必须先按 unit 计算、再对 unit 等权聚合，禁止 pooled rows。

任何 10,000-replicate paired cluster bootstrap 都必须满足：

```text
seed = 20260809
replicates = 0..9999 exactly
CI = percentile 95%
```

同一 unit/dataset 内各 score 必须使用 synchronized multiplicities。必须保存 replicate 级精确清单，或保存能逐字节验证该清单的哈希与生成证据。CPU-intensive 实现必须使用 48 核中的至少 39 核，并记录实际 child-process CPU、RSS 和 affinity；非密集型串行 inventory 不得伪造利用率。

### Track M 唯一状态

Track M 必须且只能输出下列一个状态，并按列出顺序应用前置条件；不得追加自创状态或多标签代替最终状态：

- `INSUFFICIENT_ASSETS`：任一 Core A-F 单元缺少所需的 byte-exact row/score/cluster 证据。
- `METRIC_REVERSAL`：在不存在更高优先级状态时，`S0` 在 NRC/AURC 看似更好，但在任一 dataset aggregate 的 AUGRC、`Risk@70%` 或 `Risk@90%` 上，比任一 equal-budget nonlearned baseline 更差。
- `BASELINE_DOMINATED`：在没有 metric reversal 时，任一 equal-budget nonlearned baseline 在任一 Core dataset aggregate 上具有低于 `S0` 的 AUGRC。
- `SENSITIVITY_UNSTABLE`：在没有以上状态时，`S0` 相对 baseline 的方向在任一预先规定、且可由 sealed assets 直接推导的 matching、unmatched、near-square 或 canonicalization sensitivity 下翻转。
- `ROBUST_CANDIDATE`：全部 Core 资产完整；`S0` 在每个 Core dataset aggregate 上的 AUGRC 都严格低于 `raw_confidence`、`linear_source_frozen`、`tta_angle` 和 `tta_localization`；`Risk@70%` 与 `Risk@90%` 从不反转；NRC/AURC 和所有预先规定的 sensitivities 从不反转；`learned_EQS` 不参与此决策。

上述状态是 deterministic no-reversal screen。paired cluster bootstrap CI 必须完整报告，但它只是证据，不把本次 feasibility state 升格为 formal scientific confirmation。若实现无法按固定定义得到唯一状态，必须作为 executable-audit failure 如实技术早停，不能改定义补洞。

## Track D：新数据集可行性审计

### 四个固定候选

无论前一个候选是否失败，必须把四个候选全部审计完：

```text
1. AI-TOD-R
2. UAV-OBB
3. ShipRSImageNet (backup)
4. ICDAR-MLT (auxiliary only; cannot satisfy the remote-sensing two-dataset gate)
```

`ShipRSImageNet` 是 backup；`ICDAR-MLT` 仅为 auxiliary，不能满足 remote-sensing two-dataset gate。

每个候选必须提供：official source URL 与 retrieval date；license/use terms；精确 version、split、image 和 annotation metadata；OBB、angle 与 ignore semantics；local path/stat-only presence；以及完全兼容的 config/checkpoint/environment/hash inventory。还必须说明至少三个 detector family 的公共集合能否逐一由精确资产复现。

不得下载 dataset archive，不得安装 package，不得运行 model，不得打开 target annotation 来计算 outcome。允许检索官方 HTML、README 和 license；每次检索必须保存 URL、HTTP status、bytes、SHA256 与 source date。`download_authorized: false` 始终不变。

### 真实 prior-outcome 搜索

必须真实搜索下列范围，而不是只声明“未发现”：

- Git-tracked text；
- OrientBench persistent-artifact tree；
- 已登记的 project manifests/reports；
- `pth_data/readme.md`；
- dataset root 下仅 filename/stat-only 的视图。

搜索词必须覆盖每个候选名称与 aliases，并与 prediction、feature、score、risk、metric、bootstrap、report、endpoint 等术语组合。对每次搜索保存 exact command、cwd、roots、excludes、start/end、exit code、stdout/stderr hashes，并逐条记录 hit adjudication。不得对候选 annotation 内容做 hash、decode 或 outcome 计算。

### Track D 候选状态与 precedence

每个候选必须保留全部事实，并依据下列定义给出状态：

- `ELIGIBLE_CANDIDATE`：license 清晰、local assets 可复现、angle contract 可独立验证、没有 prior outcome，并且一个至少包含三个 detector families 的公共集合具备精确资产。
- `CONTAMINATED`：存在任何真实 prediction、metric、risk、bootstrap 或 same-endpoint consumption。
- `MISSING_ASSET`：data、公共三-family 集合中的任一 config/checkpoint，或 compatible environment 缺失。
- `INCOMPATIBLE_ANGLE_CONTRACT`：conversion 无法被独立且无歧义地验证。
- `LICENSE_BLOCKED`：research use、redistribution 或 access terms 不清晰或不兼容。

多个失败状态同时成立时不得丢弃事实，最终状态 precedence 固定为：

```text
CONTAMINATED > LICENSE_BLOCKED > INCOMPATIBLE_ANGLE_CONTRACT > MISSING_ASSET
```

## 联合 gate

联合 gate 必须逐字实现为：

```text
PASS_TO_METHOD_DESIGN iff Track M=ROBUST_CANDIDATE AND at least two independent remote-sensing OBB datasets are ELIGIBLE_CANDIDATE AND both support the same >=3 detector-family set AND >=1 family was absent from old Core development AND no future target-label tuning is needed.

FAIL_TO_MEASUREMENT_ONLY iff Track M is METRIC_REVERSAL, BASELINE_DOMINATED, or SENSITIVITY_UNSTABLE; OR fewer than two remote-sensing candidates are ELIGIBLE_CANDIDATE; OR no common >=3-family set exists; OR license/angle contracts do not close; OR target-label tuning would be required.

INCONCLUSIVE_FEASIBILITY only when Track M=INSUFFICIENT_ASSETS and Track D has not independently triggered FAIL_TO_MEASUREMENT_ONLY. It never authorizes a method study and defaults to measurement-only writing.
```

`PASS_TO_METHOD_DESIGN` 只授权未来起草一份协议，并再次取得用户批准。它不授权下载、训练、推断、label access 或任何 experiment。不得把 `INCONCLUSIVE_FEASIBILITY` 当成继续方法研究的许可；它默认进入 measurement-only writing。

## 解释与 novelty 边界

正向 feasibility gate is not a scientific confirmation；它不是 venue readiness，也不是 CVPR/ICCV 的证据，至多支持起草未来协议。任务、产物和报告不得宣称首次使用 TTA uncertainty、angle quality、selective prediction、multi-pass angular dispersion 或 cross-detector reliability evaluation。

固定 score 可以称为 `training-free` 或 `no learned parameters`，绝不能称为 `parameter-free`。measurement contribution 仍限定为 detector-agnostic、angle-specific、geometry-equivalence-aware、scene-aware 的 OBB reliability protocol；`learned_EQS` 仅能留在 appendix。

AUGRC 概念来源固定为 Traub et al., *Overcoming Common Flaws in the Evaluation of Selective Classification Systems*, NeurIPS 2024 / arXiv:2407.01032；精确实现参考固定为 `IML-DKFZ/fd-shifts@c4467aec134e99691359da209f811d91283fc1e3` 的 `rc_stats.py` 与 `rc_stats_utils.py`。本轮不授权额外 novelty search，也不授权 manuscript edit。

## generator、validator 与 mutation 合约

generator 与 validator 必须是两个独立 entry point。generator 可以生成审计产物；validator 必须从 raw sealed inputs 独立读取并核验 inventory、hash、row/cluster 证据、metrics、states 和 joint gate，绝不能读取或信任 generator 写出的 gate token 来决定通过。

必须在隔离副本上做真实 mutation test，绝不能修改 sealed source。下列四种 mutation 必须分别单独执行，并且每一次都必须使 validator 以 nonzero exit 退出：

1. 改变一个 score byte；
2. 删除一个 cluster；
3. 插入一个 fake prior-outcome hit；
4. 改变一个 manifest hash。

每个 mutation 都必须记录原始/变异对象哈希、命令、cwd、开始/结束时间、exit code 与 stdout/stderr hash。只写“已测试”或用 mock gate token 触发失败不算真实 mutation。

## 必需证据产物

除唯一 tracked server report 外，下列产物都必须置于 `runtime_root`。`evidence_manifest.json` 仍是必需产物，并必须登记除自身与该唯一报告之外的全部 runtime 必需产物的实际 path、bytes 和 SHA256。

本轮固定保留一条 `evidence_manifest.json` self entry，但它只能使用 `path=evidence_manifest.json`、`bytes=N/A_SELF_REFERENCE`、`sha256=N/A_SELF_REFERENCE`；不得在同一个被验证 manifest 内填写或声称证明 manifest 自身的实际 bytes/SHA256。validator 必须核验这两个固定 N/A token，并且不能把 self entry 当作 manifest 自身完整性的证据。

```text
protocol.json
preflight.json
track_m_asset_inventory.csv
track_m_metrics.csv
track_m_bootstrap.csv or an exact replicate inventory plus hash
track_m_status.json
track_d_candidate_inventory.csv
track_d_official_sources.csv
track_d_prior_outcome_hits.csv
track_d_status.json
joint_gate.json
execution_ledger.csv
resource_telemetry.csv/json
evidence_manifest.json
validator.json
protocol_closure.md
```

`evidence_manifest.json` 完成写入后，唯一 tracked server report 必须独立记录该 manifest 的实际 path、bytes 和 SHA256。post-push external Git receipt 必须再次从已发布对象独立计算 manifest hash，并核验它与报告记录一致；该回执不得回写 `evidence_manifest.json` 或服务器报告，不得追加第二个 commit，也不得制造新的自引用循环。

唯一报告必须写到：

```text
dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md
```

`execution_ledger.csv` 必须能恢复实际命令、cwd、输入、开始/结束、exit code 和日志哈希；`resource_telemetry.csv/json` 必须支持核验 CPU/RSS/affinity；`protocol_closure.md` 必须逐条说明本合约是否已被真正穷尽，而不只是脚本退出成功。

## 报告与完成分类

报告必须且只能从下列三种完成分类中选择一个，并显式回答用户最关心的三个问题：到底是否全做完、是否技术早停、是否执行失败。

- `FULL_COMPLETION`：Track M 与 Track D 已按合约穷尽，四个 Track D 候选均被审计，generator/validator/四项 mutation 和全部可判定 gate 均完成，所有必要证据均落盘。缺资产或负面科学发现可以是 `FULL_COMPLETION`，不得因此伪装成早停。
- `EARLY_STOP_TECHNICAL`：只允许由仓库/规则/受保护文件/runtime collision/access-control/executable-audit failure 触发；必须写明准确触发点、已完成阶段、未执行阶段与最小证据。
- `FAILED_EXECUTION`：执行因不属于允许技术早停的错误而未能按合约完成，或结果/证据无法由 validator 复核；不得把它改写成科学负结果。

报告必须逐项列出每个 completed phase 与 omitted phase、每项 omitted reason，并明确写出 `dis/sug.md` 是否 `genuinely_exhausted`。还必须分别给出以下字段，不能只给一个笼统结论：

```text
completion_class: FULL_COMPLETION | EARLY_STOP_TECHNICAL | FAILED_EXECUTION
all_contract_work_finished: true | false
technical_early_stop: true | false
technical_early_stop_reason: <reason-or-none>
execution_failed: true | false
execution_failure_reason: <reason-or-none>
completed_phases: <explicit list>
omitted_phases: <explicit list>
sug_genuinely_exhausted: true | false
```

报告还必须包含起止 commit、工作树状态、所有实际命令/配置、协议偏差及授权状态、指标与预注册 gate、失败/负结果/缺失证据、产物/日志/checkpoint 路径及必要哈希、计划外观察，以及范围和受保护文件核验。

## Git 发布与外部回执

服务器结果必须形成且仅形成一个 result commit。只能显式 stage 本合约授权的四类路径，不得无差别暂存；`dis/B.md` 不得出现在 unstaged diff、staged diff 或 commit 中。push 必须使用 HTTPS；禁止 force、merge、rebase、reset、clean、checkout、stash。发布前后都必须验证受保护 B blob 仍严格等于 `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`。

被跟踪的服务器报告必须写入以下占位值，因为验证该 commit 的回执发生在 commit 之后：

```text
final_commit_sha=POST_COMMIT_EXTERNAL_RECEIPT
git_publish_status=PENDING_EXTERNAL_RECEIPT
```

push 后必须从远端取得 post-push external Git receipt，核验 remote SHA 与本地 final SHA 相等。该回执不得再写入它所验证的 commit，也不得通过第二个 commit 回填；应在服务器最终回复中提供实际值和核验结果。

## 服务器最终回复的唯一格式

只有 Track M、Track D、独立 validator、四项 mutation、唯一 result commit、HTTPS push 和 post-push external Git receipt 全部完成，最终回复第 1 行才可以严格为：

```text
执行完毕
```

否则第 1 行必须严格为：

```text
未执行完毕
```

第 2 行必须且只能是唯一报告路径：

```text
dis/server_reports/orientbench-c-topjournal-feasibility-20260809.md
```

从第 3 行开始，最终回复必须逐项给出，而不能让用户自行推断：

```text
completion_class: FULL_COMPLETION | EARLY_STOP_TECHNICAL | FAILED_EXECUTION
all_contract_work_finished: true | false
technical_early_stop: true | false
technical_early_stop_reason: <reason-or-none>
execution_failed: true | false
execution_failure_reason: <reason-or-none>
completed_phases: <explicit list>
omitted_phases: <explicit list>
sug_genuinely_exhausted: true | false
actual_final_sha: <40-hex>
actual_remote_sha: <40-hex>
changed_path_count: <integer>
protected_B_blob_equal: true | false
clean_worktree: true | false
```

科学负结果、缺资产、污染、metric reversal、baseline domination、angle incompatibility 或 license blockage，只要两条 track、validator、证据、Git 发布和外部回执均按本合约穷尽，仍可报告 `FULL_COMPLETION` 与 `执行完毕`。任何技术早停或执行失败都必须报告 `未执行完毕`，并把“全做完 / 技术早停 / 执行失败”三项分别说清楚。
