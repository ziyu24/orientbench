---
round_id: orientbench-c-r020-measurement-validity-20260811
route: ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC
risk_class: L1_EXISTING_ASSET_CPU_ANALYSIS
planning_base: 594654a95d50b1f14b87252698911cc3fc583b03
user_conceptual_approval: true
server_execution_authorized: true
specification_authorship: C_AUTHORED_UNDER_USER_ROUTE_APPROVAL
protected_B_blob: c0c2571f3a5c828673b39e6458ceaed5f14c5a6a
receipt3_execution_commit: 594654a95d50b1f14b87252698911cc3fc583b03
receipt3_report_path: dis/server_reports/orientbench-c-topjournal-feasibility-receipt3-20260811.md
receipt3_report_blob: 498dd8094f713a4a76339890ffd3a9ec45352344
receipt3_execution_status: ABNORMAL_EXECUTABLE_AUDIT_FAILURE
receipt3_formal_completion_mode: PROTOCOL_DRIFT
receipt3_scientific_gate: NOT_ADJUDICATED
receipt3_track_m: NOT_EMITTED
receipt3_reported_track_m: METRIC_REVERSAL_DESCRIPTIVE_UNVERIFIED
receipt3_reported_gate: FAIL_TO_MEASUREMENT_ONLY_DESCRIPTIVE_UNVERIFIED
receipt3_non_reusable: true
design_path: dis/jprs_measurement_validity_gate_design_20260811.md
plan_path: dis/jprs_measurement_validity_dispatch_plan_20260811.md
code_root: top_journal_v3_reaudit_055/measurement_validity_r020_20260811
runtime_root: outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811
postseal_receipt_root: outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811_postseal_receipt
postfreeze_command_log_path: outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811_postseal_receipt/postfreeze_command_log.jsonl
postseal_receipt_path: outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811_postseal_receipt/postseal_receipt.json
postseal_receipt_hash_path: outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811_postseal_receipt/postseal_receipt.sha256
post_server_required_action: C_POSTPULL_ADJUDICATION
server_report_path: dis/server_reports/orientbench-c-r020-measurement-validity-20260811.md
supervisor_log: claude_code_and_supervisor.md
status: READY_FOR_SERVER_EXECUTION
execution_status: NOT_STARTED
existing_core_measurement_reanalysis_authorized: true
new_protocol_authorized: true
new_experiment_authorized: true
new_target_dataset_outcome_authorized: false
gpu_authorized: false
general_download_authorized: false
installation_authorized: false
training_authorized: false
forward_authorized: false
inference_authorized: false
annotation_root_authorized: false
manuscript_edit_authorized: false
method_experiment_authorized: false
pinned_reference_fetch_authorized: true
pinned_reference_fetch_max_attempts: 1
cc_status: COMPLETED_CLOSED
cc_recommendation: 'no'
---

# r020 JPRS measurement-validity 终门服务器合同

## 0. 唯一任务与裁决边界

只执行本合同，不选择其它计划。用户已批准 JPRS-first measurement-validity 路线并授权服务器执行；本扩展技术规格由 C 在该路线授权下制定，不声称用户逐行审阅。目标是用冻结 Core A-F 原始资产，CPU-only 地裁决 OBB measurement validity 是否存在可复现、跨数据集的正式 witness。本轮不是训练、方法实验、新 target 实验或改稿，也不自动产生 JPRS/TGRS ready 结论。

learned EQS 永久为 APPENDIX_FAILED_ONLY。EQS_FORBIDDEN_SCIENTIFIC_INPUT：不得读取、推断、重建或使用 learned EQS 列、EQS 输出或任何 EQS gate。S0 只可描述；r011 fixed-dose 只可历史描述。receipt3 的 rows、metrics、bootstrap、manifest、state、gate 和代码 checkout 全部禁止成为本轮科学输入。receipt3 正式状态是 ABNORMAL_EXECUTABLE_AUDIT_FAILURE / PROTOCOL_DRIFT / NOT_ADJUDICATED / non_reusable；其 METRIC_REVERSAL 与 FAIL_TO_MEASUREMENT_ONLY 只可标为 DESCRIPTIVE_UNVERIFIED。

正常全量结果恰为 PASS_TO_EXTERNAL_CONFIRMATION、FAIL_GENERIC_OR_NULL、INCONCLUSIVE_MIXED 三者之一；任一技术、provenance、独立性、审计或 Git 闭包失败均为 NOT_ADJUDICATED。PASS 只授权未来另行设计独立确认；FAIL 关闭顶刊实验循环并收口 JSTARS scope；INCONCLUSIVE 不得换 gate、换 target 或复活 EQS。

## 1. 写入范围、只读范围与禁止项

唯一允许新增或修改：

1. top_journal_v3_reaudit_055/measurement_validity_r020_20260811/**
2. outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811/**
3. dis/server_reports/orientbench-c-r020-measurement-validity-20260811.md
4. claude_code_and_supervisor.md，仅 append-only
5. outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811_postseal_receipt/**，仅按 §11 在 scientific runtime freeze 后写固定三个持久 external-receipt 文件及 atomic rename 所需同目录 O_EXCL 临时文件

除上述五项外仓库与旧 persistent artifacts 全部只读。不得读取 dis/B.md 内容；只允许核验其 Git blob 与 staged/unstaged diff 元数据。禁止 GPU、一般下载、安装、训练、forward、inference、新 target、dataset annotation root、主稿、方法实验、旧结果覆盖、threshold/split/formal 标签变化。不得写 receipt3 的 code/runtime/report 路径。

未来报告在开始前必须不存在。code_root、runtime_root 与 postseal_receipt_root 均必须不存在，且 `git check-ignore` 必须证明两个 outputs roots 不会进入 Git；若任一存在或未 ignored，FAILURE_EARLY_STOP / NOT_ADJUDICATED，不清理、不覆盖、不续跑。本 round、code/runtime/report/postseal-receipt paths 一次消费，正常或异常后均不可复用。

## 2. Git preflight、执行基线与唯一结果提交

开始前记录 configured origin（只作迁移元数据）、当前/默认分支、upstream 是否存在及其值、完整 pre-pull HEAD、worktree/index、ahead/behind 与 HTTPS remote main。唯一权威远端固定为显式 `https://github.com/ziyu24/orientbench.git`；所有 network Git 命令只能使用该 HTTPS literal。configured origin 即使仍为 SSH 或 upstream 缺失/陈旧也只记录、不修改、不调用，不能单独造成失败；当前分支和 HTTPS remote default branch 必须都是 `main`。只允许 `git pull --ff-only https://github.com/ziyu24/orientbench.git main`。pull 后 local HEAD 必须等于显式 HTTPS remote main，以两端 40-hex 直接计算 ahead/behind=0/0，index/worktree clean，且 planning base 594654a95d50b1f14b87252698911cc3fc583b03 是其祖先；否则异常停止。

核验 protected B blob 精确为 c0c2571f3a5c828673b39e6458ceaed5f14c5a6a，且 B 普通/staged diff 均为空。只核验元数据，不读取内容。核验 receipt3 report Git blob 为 498dd8094f713a4a76339890ffd3a9ec45352344。

把通过 preflight 的 post_pull_head 原值冻结为 execution_base。执行期间不得 pull/merge/rebase/reset/clean/checkout/amend/force。final result commit 前再次查询 HTTPS remote main，必须仍等于 execution_base；否则异常停止且不 commit/push。

最终服务器结果必须是 execution_base 的唯一直接子提交、恰一个 non-merge commit，只含 code_root、唯一报告和 supervisor append；runtime_root 是持久化审计现场，不进入 Git。显式暂存获准路径，确认 B 与其它路径不在普通或 staged diff，运行 git diff --check 后只 commit 一次并 HTTPS push main。禁止 amend 或第二 commit。push 后外部 receipt 闭合前不得声称完成。

## 3. 前数据代码封印与访问审计

在打开任何科学输入前，必须完成实现 B、实现 A、Comparator C、closure checker、synthetic fixtures 与六项 mutation harness。synthetic pristine 必须通过、synthetic corrupted 必须被拒绝。然后冻结 code-tree 的逐文件 bytes/SHA 与 aggregate SHA；此后任何代码变化均使本轮 NOT_ADJUDICATED，不能看过科学结果后修代码重跑。

执行顺序 token 为 B_BEFORE_A：

1. B 先运行，且 A output 必须不存在。
2. B 封存后再运行 A。
3. A/B 均封存后 Comparator C 才能读取二者。

A/B 只能共享冻结 protocol constants 与原始输入，禁止共享 helper、metric、gate、replicate multiplicity 或历史实现。B trace 不得出现 A，A trace 不得出现 B；两者均不得读取 receipt3 或彼此 output。

在首个 scientific input open 前启动已封印的独立 tracer，并先在 synthetic fixture 证明 strace 存在、ptrace 权限正常且能捕获子进程；失败即 NOT_ADJUDICATED。每次应用层读取必须先 append 并 flush+fsync 下列事件，再把 bytes 交给消费者：

sequence, phase, pid, path, declared_role, bytes, sha256, monotonic_ns, prev_event_sha, event_sha

固定 genesis、连续 sequence、逐事件 hash-chain；禁止结束后批量补写。全程并行保存 strace -ff -e trace=open,openat,statx 的 OS-level 路径记录。

OS trace 归一化固定为：只把返回值 >=0 且 flags 为 read-capable 的 open/openat 计作 read event；按记录时 PID 的 cwd/dirfd 解析绝对路径，再做 symlink-resolved realpath；statx 只作路径旁证，不计 read。OS_scientific_relevant 只含 normalized realpath 精确命中上述 26 个科学输入的事件；A 与 B 各自必须覆盖全部 26 个输入。

每个应用事件须在同 phase/process tree/path 至少有一个 OS relevant open；每个 OS relevant open 须映射到恰一个 declared application path/phase，允许同一应用事件对应多次底层 open。对 m069/r014/frozen-delta roots 的任何其它 read-capable open，以及任何 receipt3 read，均为 forbidden。其它事件必须按互斥 SEALED_CODE、RULE_OR_GIT_PREFLIGHT、RUNTIME_READ、OUTPUT_WRITE、SYSTEM_LIBRARY 分类并保存，不能进入 scientific-set 等值比较。

closure 对 relevant set 做上述双向 coverage，再将应用事件、A/B traces 与 manifest 的 path/bytes/SHA/phase 全字段核对。token ACCESS_EVENT_MANIFEST_EXACT 表示 scientific event 与 manifest 必须全字段等值；任何未通过 tracer 的 scientific open、链断裂、unclassified open、forbidden open 或双向 coverage 失败均为 NOT_ADJUDICATED。

## 4. 冻结总体、membership 与 26 个科学输入

正式 units 恰为：

- A = DIOR-R / PSC
- B = DIOR-R / Oriented R-CNN
- C = DIOR-R / RTMDet
- D = FAIR1M / PSC
- E = SODA-A / PSC
- F = SODA-A / Oriented R-CNN

membership 只能由各 unit image_universe.csv 中 d_cal_daudit_split_flag == "D_audit" 决定。matched row 只有 image_id 属于该显式 set 才能进入。禁止 MD5/SHA fallback、fullval 代替、旧表反推。DIOR A/B/C 的 D_audit image universe 必须完全相同；SODA E/F 的 D_audit mother universe 必须完全相同。

DIOR/FAIR cluster universe 为全部 D_audit image_id。SODA cluster universe 为全部 D_audit tiles 通过冻结 soda_tile_to_mother_r014.csv 唯一映射得到的 mother scenes。universe 在 eligibility 前形成并保留 zero-eligible clusters；zero-cluster universe、membership flag 缺失/冲突、unmapped/ambiguous/duplicate mother mapping 均异常。dataset aggregate 只做 equal-unit mean，禁止 pooled rows。

科学输入只能是下表 26 个 literal identities；必须按实际 bytes、SHA 与 schema 逐项核验。规则、design、Git metadata 与固定 pinned reference 只能作 audit input。旧 manifest 只可定位，不能覆盖本表或提供 gate/pass token；不得用 reports/069_artifact_manifest.csv 或 r014 evidence/provenance/TTA inventories 补写、替代或裁决科学值。

path|bytes|sha256
outputs/persistent_artifacts/m069_fullval_reliability/A/image_universe.csv|1658312|3f1d2ef764c3f6e383e2b9e6285ed947a26f25b9707104bd8d9fb875408d4b0d
outputs/persistent_artifacts/m069_fullval_reliability/A/matched_fullval.jsonl|133273156|00e554fbc45dfd6ab0d964800920e101411bc2ee1e218f575a0eafcfde63761e
outputs/persistent_artifacts/m069_fullval_reliability/B/image_universe.csv|1652313|644ccaa922986d3597049680924a63555975e8a61f8ac26fccf744ff41c5edee
outputs/persistent_artifacts/m069_fullval_reliability/B/matched_fullval.jsonl|132369719|e1772d642990fb45ee00d31a2cc62b8fd468d0e1a99e009e0430e91e51082513
outputs/persistent_artifacts/m069_fullval_reliability/C/image_universe.csv|1655606|52c04690d415a66b59ff9d30d58f97ae836d71d62e543c8e278b707d4565bc77
outputs/persistent_artifacts/m069_fullval_reliability/C/matched_fullval.jsonl|132382835|91d4b372e5340a4849af680d82a3973be0999b2778e89375116067fa6009ea2e
outputs/persistent_artifacts/m069_fullval_reliability/D/image_universe.csv|719167|5cec906c601469dff58a2e6a26293d54613cc7f162c458f6a5abde0cb0f76586
outputs/persistent_artifacts/m069_fullval_reliability/D/matched_fullval.jsonl|86428641|fe2c0b3690e12793f898c0c7a5ce100806567e39f4b3671e9b1e2af5fb8c3bbf
outputs/persistent_artifacts/m069_fullval_reliability/E/image_universe.csv|3348604|75f874fff653e64460d6c91ce0dd07637ad68b55532976fbdca1bd01a4f8b131
outputs/persistent_artifacts/m069_fullval_reliability/E/matched_fullval.jsonl|482776147|337470223fae218aa2969ae8f974a447e6666d22f02830a7a933ea3dadbd72c9
outputs/persistent_artifacts/m069_fullval_reliability/F/image_universe.csv|3340530|0ce7cc5f4d56aceef57faaa85b09115309b961d4e663484ac893731330eef95c
outputs/persistent_artifacts/m069_fullval_reliability/F/matched_fullval.jsonl|528736628|dd7f37b067a569541140a1bad49bf6ae3a5aea7b0f9eff031ef3fe9a9a2c723f
outputs/persistent_artifacts/orientbench_r014/features/A.parquet|106414303|1680039b73ea6419143621ac5776713f2232b1f1bca953d22ba452dae3990800
outputs/persistent_artifacts/orientbench_r014/features/B.parquet|76778217|a4a56429d092ae5f2b99eae5bdbad6033b2bc1d3e9db3cd205534903ccdbabb5
outputs/persistent_artifacts/orientbench_r014/features/C.parquet|90348339|79b8b9299b7e758bbad663f4a55e94eaca186de14337212f8f1542c02fd38e44
outputs/persistent_artifacts/orientbench_r014/features/D.parquet|56298120|3d88592b74e3b6ee51515ab530c9020f07518f26ca74c69a84b90ca408d104af
outputs/persistent_artifacts/orientbench_r014/features/E.parquet|235374169|00e690cd03d5ff00cdd73b87a0c0bec1ad0d1e22889c2da3693975f203252f0b
outputs/persistent_artifacts/orientbench_r014/features/F.parquet|161849746|c3875f572b6c909b39ab4b5797d60963cf097969aca9ca4eb68a3f50c2caad75
outputs/persistent_artifacts/orientbench_r014/scores/A.parquet|14113964|65a38d8dc6e8818f459cb248a9cf90949157010dce2bb11469f5f5b5c161181a
outputs/persistent_artifacts/orientbench_r014/scores/B.parquet|5147240|a7b16608a3495d466de005e998e8ee83803d35bc0222c6c2b398caac9c3b4285
outputs/persistent_artifacts/orientbench_r014/scores/C.parquet|9067953|1724d7bda74542d6f4b02d1ea29e9e1eb19a3880a4c3c2b826acbbeab74e9d67
outputs/persistent_artifacts/orientbench_r014/scores/D.parquet|11574260|1807dc207596f2a26aaee992dd96efd972da36f4bcf7ce82edf1a434c83c8d4a
outputs/persistent_artifacts/orientbench_r014/scores/E.parquet|40344077|e3ef91a92370cbd3cfd2e76fae46f430c8024b73ec9dd56e64c274c531d3e4bd
outputs/persistent_artifacts/orientbench_r014/scores/F.parquet|19765066|fa27f7fed94c410d8bd27a106e96587d6b330d1c38e3f4f0c10986ee3f2367db
outputs/persistent_artifacts/orientbench_r014/soda_tile_to_mother_r014.csv|1418786|7bf9cc5698b0af2796fbb990e387603f3284231e541b1d711fd35c576e8b787f
top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json|12986|80d86a5f72e70405fe4a49db87aad61e6aea20a26af0ad1c5745bfd646d1e5cb

每个实现从 pred_obb/gt_obb 独立重算 long-side canonical angle、AR 和风险，并逐行核对历史 angle_error；不得信任旧 gate、旧汇总或旧 risk 列。

## 5. strict cohort join 与 schema

STRICT_JOIN_MODE: MATCHED_DAUDIT_BASE_COHORT_SEMISELECT_RHS_ONE_TO_ONE_LEFT。

唯一 row key 为 (image_id,pred_id)。matched、features、scores 三份源表各自全表 key 必须唯一。

每个 unit 先按 matched 原始文件顺序，仅用 image_universe 显式 D_audit membership 筛出完整 matched base cohort，冻结其完整 key sequence、sorted-key set 及两者 SHA。五个 eligibility 只从该 base cohort 派生。

features 与 scores 各自先对 base-cohort keys 做 semi-select，再以 validate=one_to_one 分别 left join。base cohort 的 missing=0、duplicate=0、drop=0；连接前后 row count 与 key sequence 必须完全相同。features/scores 全表中不属于 base cohort 的合法 RHS extras 允许存在，但各自必须记录 count 与 sorted-key SHA，且绝不进入 endpoint。

detection_score 只在 features 与 scores 的对应 cohort rows 中逐行 finite 且精确相等；matched 不要求存在 detection_score。正式 probes、GT OBB、membership、cluster、eligibility 所需真实字段必须 schema 完整且 finite。禁止 inner join、drop、impute 或各 probe 自行缩小 cohort；任一断言失败均为 NOT_ADJUDICATED。

## 6. probes、风险、消融与端点

正式 probes 恰为：

- raw_confidence = detection_score
- linear_source_frozen = score_ar_size_linear
- tta_angle = -u_axis
- tta_localization = -(missing_fraction + iou_loss)

正式 contrasts 恰为后三者各自减 raw_confidence，共 3 个。S0=-(u_axis+missing_fraction+iou_loss) 只作描述，不进入 family/gate。

预测和 GT 均 canonicalize 为 long-side；角差按 180 degree 周期。AR=max(gt_w,gt_h)/min(gt_w,gt_h)，主域 AR>=2.1。主风险：

r_geo = clip(e_can / max(delta_0.75(AR), 1 degree), 0, 3) / 3

固定五个单因素 geometry/AR ablations：

1. NO_LONGSIDE_AR21：仍 AR>=2.1 且同一 delta_0.75(AR)，只把 e_can 换为未长短边交换的 180-degree raw-theta 差。
2. NO_GEONORM_AR21：仍 canonical 且 AR>=2.1，只把风险换为 clip(e_can/90,0,1)。
3. NORMALIZED_ALL_AR：仍 canonical 与同一 geonorm，只取消 AR cutoff。
4. NORMALIZED_AR16：仍 canonical 与同一 delta/r_geo，唯一改变 eligibility 为 AR>=1.6。
5. NORMALIZED_AR13：仍 canonical 与同一 delta/r_geo，唯一改变 eligibility 为 AR>=1.3。

SCENE_MACRO 是 family 外纯描述诊断：固定 coverage 下非空 image/mother 等权，空 scene 只进 nonempty-rate 分母。只报告 scene-macro point、nonempty rate 与正式 scene-cluster CI；禁止另造 instance-IID bootstrap、material flag、category-change 主张或单独形成 OBB-specific witness。

主端点恰为 unscaled continuous-loss AUGRC、Risk@70、Risk@90。每个 whole-tie unique threshold：

- coverage = k/n。
- generalized risk = accepted risk sum / fixed total n。
- selective risk = accepted risk sum / k。
- AUGRC 在包含 origin (0,0) 的 unique-threshold generalized-risk curve 上 trapezoid integration。
- Risk@70/90 使用第一个 actual coverage >= q 的 whole-tie threshold并报告 actual coverage。

coverage intervals 固定为 [0,.70]、(.70,.90]、(.90,1]；crossing/best interval 仅描述。AURC/NRC 用 (score desc,row_key asc) 冻结兼容实现，仅 legacy diagnostic，不驱动 gate。

## 7. bootstrap、effect bands、p、Holm 与 accepted-set swap

固定 seed=20260809、replicates=0..9999、dataset index DIOR-R=0, FAIR1M=1, SODA-A=2。cluster id 按 UTF-8 byte order 排序。dataset d 使用 numpy.random.RandomState(20260809+d)，按 replicate id 顺序恰调用一次 randint(0,n_clusters,size=n_clusters)，再 bincount(minlength=n_clusters)。同 dataset 全部 units/probes/losses/endpoints 共用该 multiplicity，保存每个 replicate multiplicity SHA。

固定 39 worker processes，replicate-to-worker=replicate_id % 39，只按 replicate id 确定性合并。zero-eligible clusters 保留；zero-cluster universe 异常。

完整 hypothesis key H=(level,key,contrast,endpoint,ablation_id)，lower is better：

Delta_main(H)=M_probe_main(H)-M_raw_main(H)
Delta_ablation(H)=M_probe_ablation(H)-M_raw_ablation(H)
DoD(H)=Delta_main(H)-Delta_ablation(H)

每个 operand 只能来自 H 对应 level、unit/dataset、contrast、endpoint、ablation、eligibility 的同一 cohort，禁止复用或跨层借数。

epsilon_AUGRC = max(5e-4, 0.02 * max(abs(M_probe),abs(M_raw)))
epsilon_Risk = max(1e-3, 0.02 * max(abs(M_probe),abs(M_raw)))

epsilon_main 只由 main point estimates 计算一次；epsilon_ablation 只由 ablation point estimates 计算一次；bootstrap 内不重算。CI 为排序后 linear quantile 0.025/0.975。

DoD 双侧 centered-bootstrap p：

p = (1 + count(abs(DoD_b-DoD_hat) >= abs(DoD_hat))) / 10001

Holm 按 (raw_p,hypothesis_key) 排序，计算 (m-rank+1)*p，取 prefix max 并 clip 1。NaN/Inf、missing/duplicate key 均异常。主/消融 contrast CI 是保守稳定过滤；正式 multiplicity 只由 DoD p 的 Holm 调整承担。

whole-tie accepted set：

A_score,q = {row: score >= first unique threshold whose actual coverage >= q}
swap_q = |A_probe,q symmetric_difference A_raw,q| / |A_probe,q union A_raw,q|

对 main 与对应 ablation 分别算 swap。Risk@70/90 witness 要求对应 q 的 main 和 ablation swap 都 >=0.05。AUGRC 的 q=.70/.90 四个 swaps 都报告但不驱动 AUGRC witness。dataset swap operand 为 constituent unit swap fractions 的 equal-unit mean，禁止 pooled set。

## 8. formal witness、families 与唯一四态

每个 formal OBB-specific witness 必须同时满足：

1. main 与指定 ablation 的 supported order 符号相反，且 CI 条件按 direction 精确判定：
   - PROBE_BETTER_MAIN__RAW_BETTER_ABLATION 要求 Delta_main<0<Delta_ablation、main_CI_high < -epsilon_main、ablation_CI_low > epsilon_ablation。
   - RAW_BETTER_MAIN__PROBE_BETTER_ABLATION 要求 Delta_ablation<0<Delta_main、main_CI_low > epsilon_main、ablation_CI_high < -epsilon_ablation。
2. DoD Holm-adjusted p<0.05、95% cluster CI 排除 0，且 abs(DoD)>=epsilon_main+epsilon_ablation。
3. Risk endpoint 同时满足对应 main/ablation whole-tie swap>=0.05。
4. 不依赖 S0/EQS，且不是只有 AURC/NRC-vs-AUGRC generic reversal。

unit family 恰为 6*3*3*5=270；dataset family 恰为 3*3*3*5=135。两个 family 分开 Holm，禁止事后拆 family、挑 coverage/probe/ablation。effect class：

- NO_LONGSIDE_AR21 -> ANGLE_EQUIVALENCE
- NO_GEONORM_AR21 -> GEOMETRY_NORMALIZATION
- NORMALIZED_ALL_AR/NORMALIZED_AR16/NORMALIZED_AR13 -> AR_DOMAIN

full signature 恰为 (effect_class,ablation_id,contrast,endpoint,supported_direction)。supported_direction 只能是 PROBE_BETTER_MAIN__RAW_BETTER_ABLATION 或 RAW_BETTER_MAIN__PROBE_BETTER_ABLATION；不得跨 ablation 或相反方向合并。

四态与 precedence：

1. NOT_ADJUDICATED：任一 input identity、schema/join、实现独立性、A/B parity、bootstrap、mutation、manifest、scope、Git、push 或 external receipt 失败。
2. PASS_TO_EXTERNAL_CONFIRMATION：全部审计闭合；同一个 full signature 在至少 2 个 dataset aggregates 形成 witness；同 signature unique unit witnesses >=4/6 且覆盖至少 2 个 detector families；SODA dataset aggregate 与至少 1 个 SODA unit 都有该 signature；effect class 为三种 OBB classes 之一。
3. FAIL_GENERIC_OR_NULL：valid full execution 且 unit 和 dataset formal OBB witness 均为 0。generic_only 定义为存在 legacy AURC/NRC-vs-AUGRC supported reversal、但 formal witness 总数仍为 0，也归此态。
4. INCONCLUSIVE_MIXED：valid full execution，至少 1 个 formal witness，但不满足 PASS。

判定 precedence 固定为 NOT_ADJUDICATED -> PASS_TO_EXTERNAL_CONFIRMATION -> FAIL_GENERIC_OR_NULL -> INCONCLUSIVE_MIXED。valid execution 必须恰落后三态之一。detector/unit/dataset 只按 unique identity 计数。

## 9. 双实现 parity 与冻结 reference

A/B 均从原始 bytes 独立实现 canonicalization、delta、AUGRC、bootstrap、Holm 与 gate，并消费同一冻结 delta JSON。正式风险计算的 delta 算法逐字冻结为：从 JSON `ar/dtheta_075` 取 finite pairs，按 ar 稳定升序且要求严格递增；`ar<first_finite` 返回 infinity；`first_finite<=ar<=grid_max` 使用 `numpy.interp(ar,finite_ar,finite_dtheta)`；`ar>grid_max` 使用 `max(0,min(finite_ar_i*finite_dtheta_i for finite_ar_i>=max(8,grid_max/2))/ar - 2*solve_tolerance_deg)`，其中 `solve_tolerance_deg` 必须从 exact JSON 动态读取为 0.001。A/B 对该 table-driven 算法须 `atol=1e-12,rtol=0` parity。

B 另以独立 polygon/bisection 在冻结 JSON 的每个 finite grid ar 上重算未四舍五入 direct root，只作 source-sanity witness，不替换表值；`abs(direct_root-stored_4decimal_root)` 上限固定为 `solve_tolerance_deg + 0.5*10^-4 = 0.00105 degree`。禁止先 round direct root 再比较，也禁止把 off-grid direct root 与线性插值值用该门比较。

Comparator C 在 A/B 封存后逐 row key、cluster universe、point metric、全部 replicates、CI/p/Holm、witness、gate 比较。row risk、point metric、replicate、DoD 的 tolerance 为 atol=1e-10,rtol=0；keys/count/hash/state 必须 exact equal。

唯一网络例外：新 runtime 内恰一次 HTTPS fetch https://github.com/IML-DKFZ/fd-shifts.git commit c4467aec134e99691359da209f811d91283fc1e3。禁止替代 remote/commit、额外 fetch、hook、submodule、LFS、setup、安装或其它 checkout 代码。固定 blobs：

- fd_shifts/analysis/rc_stats.py Git blob 563be2ed8652c730dd940eb241d8642717e25c0d；raw SHA256 d7f823c58bae5bbee4af2c0b5296bea41d6494884bd868d859890e9ccac22619
- fd_shifts/analysis/rc_stats_utils.py Git blob 9f99c499f370b587d0ca73e2d9679a358de55e05；raw SHA256 a827fcf36d278beccc804e0d1895428f920c746dcc316a19f81bf3f341276b1f

remote/commit/detached clean HEAD/tree/blob/raw bytes identity 必须闭合。只能完整 import 两 blob 或对其 raw source 做可追溯 AST closure adapter；不得改公式或手抄 expected。动态读取 AUC_DISPLAY_SCALE，必须精确为 1000；reference_augrc_unscaled=reference_augrc_display/1000。固定 tie/binary/continuous/boundary vectors 的 generalized-risk curve 与 unscaled AUGRC 必须对 reference 达到 atol=1e-12,rtol=0。reference 只做实现审计，不进入 270/135 gate。

## 10. 六项真实 mutation 与严格时序

六项 token 和对象固定：

1. MUTATION_RAW_THETA：在 isolated copied raw 中改变一条 m069 pred_obb.theta。
2. MUTATION_SODA_MOTHER：在 isolated copied mapping 中改变一条 SODA tile-to-mother。
3. MUTATION_AUGRC_LOGIC：在 isolated copied logic 中删除 AUGRC origin 或改变 generalized-risk denominator。
4. MUTATION_GATE_DATASET_COUNT：在 isolated copied gate logic 中把 two-dataset 条件改为 one-dataset。
5. MUTATION_MANIFEST_ACCESS：从 copied manifest/access trace 删除一个真实 scientific input event。
6. MUTATION_REPORT_TOKEN：篡改 copied report 的 scientific gate 或 completion token。

前四项必须在 SCIENTIFIC_RUNTIME_FREEZE 前执行。每项 pristine copy 先通过，mutated copy 必须被同阶段 independent validator 非零拒绝，保存 before/after SHA 与 semantic witness。

第五项只能在真实 runtime manifest 已生成且 pristine closure 通过后，由 code/runtime 外的 checker 对 manifest/access copy 执行；pristine pass、mutated nonzero reject。

第六项只能在最终 report exact bytes 已于内存中确定后，对该 exact pristine byte buffer 与 mutated copy 执行；pristine pass、mutated nonzero reject。随后 tracked report 必须一次性写出且 SHA 与 pristine buffer 相同。post-push external receipt 重新 hash 已发布 report 并重放第六项。

禁止摘要布尔、恒真 token 或错误时序替代真实 mutation。

## 11. 无环 seals、manifest 与固定产物

闭包顺序不可改变：

raw inputs -> B/A outputs -> comparator/first-four-mutations -> SCIENTIFIC_RUNTIME_FREEZE
-> runtime_manifest -> pristine closure/manifest-mutation -> planned-report/report-mutation
-> tracked report/supervisor append -> TRACKED_CONTENT_SEAL
-> commit/push -> post-seal external receipt

SCIENTIFIC_RUNTIME_FREEZE 前关闭 scientific inputs、A/B/comparator/前四 mutation outputs、resource telemetry、application/OS access traces。runtime command_ledger.csv 只记录 through SCIENTIFIC_RUNTIME_FREEZE 的命令并在 freeze 同时封存。freeze 后唯一允许的新 runtime object 是 runtime_manifest.json；manifest/closure/report/Git/push/post-push verification 命令只进入 postseal_receipt_root 的 append-only、hash-chained `postfreeze_command_log.jsonl`，绝不回写 runtime。该 root 在 freeze 后以 mode 0700 首次创建；command log 以 mode 0600 创建，每个事件含 sequence/command/cwd/start/end/exit/stdout_sha256/stderr_sha256/prev_event_sha/event_sha 并在下一命令前 flush+fsync。

全部 post-push verification 完成且 receipt payload 所需事实已确定后，必须追加最后一个 `POSTFREEZE_COMMAND_LOG_SEAL` 事件、flush+fsync、关闭并 chmod 0400；其 sealed bytes/SHA/chain_head 才能进入 receipt。seal 后禁止再执行需记录的 shell/subprocess 命令。receipt JSON、read-back verification、atomic rename 与 sidecar fsync 是 code-sealed receipt writer 的固定 syscall protocol，明确排除于 command log；它们不得启动 shell/subprocess，也不得改变 sealed log。VALID 只核验该 sealed prefix，从而避免 receipt 对记录自身写入命令的循环依赖。

manifest 枚举 freeze 前全部实际 input/code/runtime bytes、SHA、schema、keys，并与 access events 做 path/bytes/SHA/phase 等值核对；大文件真实流式计数与取 schema，禁止由 bytes 猜 row count。manifest self 标为 EXTERNAL_HASH_ONLY，明确排除未来 report、Git、external receipt。

seal 外 closure checker 不回写 runtime。它先核验 manifest 与第五 mutation，再以内存中的 gate/completion/前五 mutation 构造 report exact bytes并做第六 mutation；之后一次性写 report 和 supervisor append。report self 标为 EXTERNAL_GIT_BLOB_ONLY 和 POST_COMMIT_EXTERNAL_RECEIPT，其 scientific gate/completion 明确是 `PROVISIONAL_PENDING_C_POSTPULL_ADJUDICATION`。TRACKED_CONTENT_SEAL 后 tracked/runtime 零写。

push 后只能在 postseal_receipt_root 完成 server-local external receipt。固定 schema `orientbench-r020-postseal-v1` 必含：`round_id,status,server_local_candidate_state,execution_base,result_commit_sha,result_parent_sha,result_commit_count,non_merge,remote_url,remote_main_sha,changed_paths,protected_B_blob_parent,protected_B_blob_result,report(path,git_blob_oid,bytes,sha256,provisional_gate,provisional_completion),runtime_manifest(path,sha256),code_seal_aggregate_sha256,implementation_a(gate,completion,evidence_sha256),implementation_b(gate,completion,evidence_sha256),comparator(gate,completion,evidence_sha256),mutation6(pristine_exit,mutated_exit,before_sha256,after_sha256,semantic_rejection),postfreeze_command_log(path,bytes,sha256,chain_head),push(command,exit_code,stdout_sha256,stderr_sha256),created_at_utc`。`VALID_POSTSEAL_RECEIPT` 当且仅当：唯一 commit/parent/scope/B、HTTPS remote、published report blob/raw SHA、manifest、A/B/comparator gate+completion、command chain 与 mutation6 pristine=0/mutated!=0 全部闭合；否则 status 必须为 `INVALID_POSTSEAL_RECEIPT` 且 `server_local_candidate_state=NOT_ADJUDICATED`。

receipt JSON 必须以 mode 0600 写到同目录 O_EXCL 临时文件，flush+fsync 后 atomic rename 为唯一 `postseal_receipt.json`；随后写唯一 `postseal_receipt.sha256`，内容精确为 `<json_sha256>  postseal_receipt.json\n`，同样 mode 0600、O_EXCL、fsync。两文件不得覆盖或回填 tracked/runtime；任一写入/hash/permission 失败即异常。该 ignored receipt 只是 server-local publication witness，不是跨电脑正式状态。JSON status=VALID、sidecar hash匹配且全部字段由重新读取的 published bytes 推导，只允许服务器把本阶段标为 `NORMAL_EXECUTION_COMPLETE_PENDING_C_ADJUDICATION` 并回复正常；tracked report 的 provisional gate/completion 仍不得在服务器侧升级为 formal。

服务器回复后，唯一后续 owner 是 C。C 必须 HTTPS fast-forward 拉取 result commit，独立核验 commit DAG/scope/B/report Git blob与raw SHA、报告中的 manifest/A-B-comparator identities、published checker和第六 mutation；随后才可在新的 C-side `dis/` 状态提交中采用 provisional gate，或裁为 `NOT_ADJUDICATED`。在该 C-side post-pull adjudication 发布前，任何跨电脑状态都只能写 `PENDING_C_ADJUDICATION`；不得凭聊天短语或 server-local ignored receipt 宣称正式科学结论。

runtime 固定最低产物：

- protocol.json
- preflight.json
- input_inventory.csv
- code_seal.json
- command_ledger.csv
- file_access_events.jsonl
- os_open_trace/**
- resource_telemetry.csv
- implementation_b/rows.parquet
- implementation_b/metrics.csv
- implementation_b/replicates.parquet
- implementation_b/witnesses.csv
- implementation_b/gate.json
- implementation_a/rows.parquet
- implementation_a/metrics.csv
- implementation_a/replicates.parquet
- implementation_a/witnesses.csv
- implementation_a/gate.json
- comparator.json
- unit_hypotheses.csv
- dataset_hypotheses.csv
- scene_macro_diagnostic.csv
- mutations/pre_freeze_mutation_index.csv，仅含前四项
- runtime_manifest.json

第五项 manifest/access mutation 的实际结果只进入 tracked report，不生成新 runtime 对象。第六项的固定 mutation identity 与待重放 token进入 report exact buffer；其对 exact pristine report bytes 的实际检验和 push 后重放结果只进入外部 receipt，不能为了回填结果改写 report。

唯一 tracked report 必须记录 execution_base、code/runtime/report identity、26 inputs、join/extras、cluster universes、A/B parity、reference、270/135、all hypotheses、witness/signatures、SCENE_MACRO、前四项 runtime mutation、第五项 closure mutation、预声明第六项 identity、resource telemetry、manifest/seals、四态、provisional completion、negative evidence与 deviations。tracked report 的 Git 字段只能写 git_publish_status=PENDING_EXTERNAL_RECEIPT、scientific_state=PROVISIONAL_PENDING_C_POSTPULL_ADJUDICATION、report self=EXTERNAL_GIT_BLOB_ONLY 和 POST_COMMIT_EXTERNAL_RECEIPT，不得声称未来 commit/push/remote/published-blob 已闭合；真实 Git closure与第六 mutation结果只在 push 后固定 external receipt 核验并形成 server-local candidate state，跨电脑 formal state 仍须 C post-pull adjudication。

## 12. 资源与停止语义

CPU-only；preflight 必须确认 N=48 logical CPUs，否则异常。固定 39 worker processes、39-core affinity；OMP/MKL/OpenBLAS/NumExpr threads=1。job CPU 定义为每个完整 30 秒 interval 内该 r020 process tree 的 CPU-time 增量除以 (30*N)。coordinator 以可审计 duty-cycle pause/resume，使 bootstrap parallel phase 的每个完整 interval 满足 60%<=job_cpu_pct<=80%。

三个连续完整 interval 的 job_cpu_pct<60% 且没有逐 interval 记录 IO_WAIT 或 SERIAL_PHASE 理由，或任一完整 interval job_cpu_pct>80%，均为异常。preflight、serial、finalization interval 只需记录 phase/reason，不适用下限。每 30 秒记录完整 process-tree 的 CPU-time、RSS、affinity、active/paused worker 数、job_cpu_pct 与 throttle events；throttle 不改变 replicate-to-worker。

wall time 上限 18 小时；新 runtime 上限 30 GB。不得因不利科学中间结果早停，A-F 与 10000 replicates 必须全量完成。只有 source/hash/schema/join/code/trace/parity/bootstrap/mutation/manifest/scope/Git/push/external-receipt 缺陷可 FAILURE_EARLY_STOP / NOT_ADJUDICATED。

正常 completion mode 只能是：

- FULL_COMPLETION_POSITIVE
- FULL_COMPLETION_INCONCLUSIVE
- FULL_COMPLETION_NEGATIVE

只有这三者允许 sug_genuinely_exhausted: true。异常只能 FAILURE_EARLY_STOP / NOT_ADJUDICATED，sug_genuinely_exhausted: false。不得把科学 FAIL/INCONCLUSIVE 写成异常，也不得把技术早停写成科学失败。

## 13. 最终聊天硬合同

所有细节只写唯一报告和 supervisor log。服务器最终聊天严格使用以下二选一 exact project wrapper，无报告路径、SHA、解释或列表：

👇👇👇👇👇👇

正常执行完毕

👆👆👆👆👆👆

或

👇👇👇👇👇👇

异常结束

👆👆👆👆👆👆

PASS、FAIL 或 INCONCLUSIVE 的 provisional result 只有在全协议、唯一 commit、push 与固定 server-local receipt 的 `VALID_POSTSEAL_RECEIPT`+sidecar 闭合后，才回复正常执行完毕；该短语仅表示服务器阶段正常并等待 C post-pull adjudication。任何 technical/provenance/audit/publication/receipt defect 均回复异常结束。
