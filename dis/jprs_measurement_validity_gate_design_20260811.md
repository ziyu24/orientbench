---
document_id: orientbench-jprs-measurement-validity-gate-design-20260811
document_status: C_AUTHORED_EXECUTION_SPEC_UNDER_USER_ROUTE_APPROVAL
user_conceptual_approval: true
server_execution_authorized: true
approval_date: 2026-08-11
planning_base: 594654a95d50b1f14b87252698911cc3fc583b03
round_id: orientbench-c-r020-measurement-validity-20260811
route: ISPRS_JPRS_MEASUREMENT_DIAGNOSTIC
risk_class: L1_EXISTING_ASSET_CPU_ANALYSIS
postseal_receipt_root: outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811_postseal_receipt
postseal_receipt_path: outputs/persistent_artifacts/orientbench_measurement_validity_r020_20260811_postseal_receipt/postseal_receipt.json
post_server_required_action: C_POSTPULL_ADJUDICATION
cc_recommendation: 'no'
---

# OrientBench JPRS 测量有效性终门设计

## 1. 决策与边界

用户已批准把 learned EQS 永久降为附录失败探索，唯一主线改为 JPRS-first 的 OBB orientation-reliability measurement-validity paper。本设计只允许一次既有 Core 资产的 CPU-only clean-room 终门；它不恢复 r014/r015/r019/receipt3 的正式身份，不引入新 target，不训练、不 forward、不改稿，也不自动产生 JPRS/TGRS ready 结论。

receipt3 的 Git 发布机械事实成立，但其 validator 在实际 manifest/access log/report 生成前只校验 planned token，且 scientific inputs 未完整进入 frozen manifest；因此正式状态为 `ABNORMAL_EXECUTABLE_AUDIT_FAILURE / PROTOCOL_DRIFT / NOT_ADJUDICATED`。receipt3 报告的 `METRIC_REVERSAL` 只作为本设计的动机，所有 receipt3 派生 rows、metrics、bootstrap、manifest、state 和 gate 均禁止成为科学输入。

## 2. 可证伪候选

```text
candidate:
  problem: 单一 AURC/NRC、实例级推断和未消融的角风险可能给 OBB 可靠性排序造成部署相关的错误结论。
  nearest_primary_work: Traub et al. NeurIPS 2024 的通用 AURC/AUGRC 缺陷；SAOD CVPR 2023 的一般检测可靠性框架。
  material_delta: OBB 长边等价、AR 可辨识域、几何归一化风险和图像/母景交换单位共同改变结论，而非仅把 AUGRC 应用于旋转框。
  minimum_decisive_test: Core A-F 原始密封资产由两个不共享 metric/gate 代码的实现独立重建；固定三端点、固定消融、同步场景 bootstrap 与全局 Holm family。
  kill_condition: 无正式 OBB-specific witness、变化仅为 generic AURC/AUGRC reversal、或任一 provenance/独立性/mutation/发布闭包失败。
  expected_paper_value: PASS 仅授权独立外部确认；FAIL 将顶刊实验路线封顶为 JSTARS scope；INCONCLUSIVE 不允许换 gate 续命。
```

## 3. 冻结总体与输入

正式总体只含冻结 `D_audit` 的六个 evaluation units：A=DIOR-R/PSC、B=DIOR-R/Oriented R-CNN、C=DIOR-R/RTMDet、D=FAIR1M/PSC、E=SODA-A/PSC、F=SODA-A/Oriented R-CNN。membership 只能由各 unit `image_universe.csv` 的 `d_cal_daudit_split_flag == "D_audit"` 决定；matched rows 只有在其 `image_id` 属于该显式 D_audit set 时才能进入，禁止 SHA/MD5 fallback 重分角色、fullval 代替或旧结果表反推。DIOR A/B/C 的 D_audit image universe 必须精确相同，SODA E/F 的 D_audit mother universe必须精确相同；不相同即执行异常。DIOR/FAIR 的完整 cluster universe 是全部 D_audit `image_id`；SODA 的完整 cluster universe 是全部 D_audit tiles 经冻结 `soda_tile_to_mother_r014.csv` 唯一映射得到的 mother scenes。universe 在 eligibility 前形成，必须保留 zero-eligible clusters；flag 缺失/冲突或任一 unmapped/ambiguous/duplicate 映射都使执行异常。数据集聚合为 unit 等权，禁止 pooled rows。

科学输入只能由下列已登记资产及其实际 bytes/SHA/schema 重建：

- `outputs/persistent_artifacts/m069_fullval_reliability/{A..F}/matched_fullval.jsonl`
- `outputs/persistent_artifacts/m069_fullval_reliability/{A..F}/image_universe.csv`
- `outputs/persistent_artifacts/orientbench_r014/features/{A..F}.parquet`
- `outputs/persistent_artifacts/orientbench_r014/scores/{A..F}.parquet`
- `outputs/persistent_artifacts/orientbench_r014/soda_tile_to_mother_r014.csv`
- `top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json`
- 规则、设计、Git 元数据与固定 reference source 只能作为审计输入；不得读取 `reports/069_artifact_manifest.csv`、r014 evidence/provenance/tta inventories 来补写、替代或裁决科学值。

上述 26 个科学输入的 literal identity 固定如下；旧 manifest 只能帮助定位，不能覆盖本表或提供 PASS token：

```text
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
```

每个实现都必须从 `pred_obb/gt_obb` 独立重算 long-side canonical angle、AR 和风险，并逐行核对历史 `angle_error`；不得直接信任旧 gate、旧汇总或旧 risk 列。r011 fixed-dose 只作历史描述，不进入本轮 read-set 或 gate。HRSC、DOTA-r019、EQS 均不得进入正式 family。

## 4. 分数、风险与端点

正式 measurement probes 只有四个：

```text
raw_confidence       = detection_score
linear_source_frozen = score_ar_size_linear
tta_angle            = -u_axis
tta_localization     = -(missing_fraction + iou_loss)
```

正式对比只固定为后三者分别减 `raw_confidence`，共三个 contrasts。`S0=-(u_axis+missing_fraction+iou_loss)` 只作描述性 probe，不进入 hypothesis family 或 gate；learned EQS 列禁止读取。

主风险为：预测与 GT 均先 canonicalize 为 long-side、角度按 180° 周期取差；`AR=max(gt_w,gt_h)/min(gt_w,gt_h)`；主域 `AR>=2.1`；

```text
r_geo = clip(e_can / max(delta_0.75(AR), 1 degree), 0, 3) / 3
```

固定 geometry/AR 消融均只改变一个因素：

1. `NO_LONGSIDE_AR21`：仍用 `AR>=2.1` 和同一 `delta_0.75(AR)`，只把 `e_can` 换为未做长短边交换的 180° raw-theta 差；
2. `NO_GEONORM_AR21`：仍 canonical 且 `AR>=2.1`，只把风险换为 `clip(e_can/90,0,1)`；
3. `NORMALIZED_ALL_AR`：仍 canonical 且使用同一几何归一化，只取消 AR cutoff；
4. `NORMALIZED_AR16`：仍 canonical、使用同一 delta table 与 `r_geo`，唯一变化是 eligibility 改为 `AR>=1.6`；
5. `NORMALIZED_AR13`：仍 canonical、使用同一 delta table 与 `r_geo`，唯一变化是 eligibility 改为 `AR>=1.3`。

另设不进入 270/135 OBB hypothesis family 的 `SCENE_MACRO` 诊断：固定 coverage 下非空 image/mother 等权，空 scene 只进入 nonempty-rate 分母。它只报告 scene-macro point、nonempty rate 与正式 scene-cluster CI，禁止另造 instance-IID bootstrap、`material` flag、category-change 主张或单独形成 OBB-specific witness。

主端点只有 unscaled continuous-loss `AUGRC`、`Risk@70`、`Risk@90`。对每个 whole-tie threshold，`coverage=k/n`，generalized risk 为已接收风险和除以固定总体 `n`，selective risk 为已接收风险和除以 `k`；AUGRC 在包含原点 `(0,0)` 的 unique-threshold generalized-risk 曲线上用 trapezoid 积分。Risk@70/90 使用第一个达到目标覆盖的 whole-tie threshold并报告实际 coverage。coverage 区间固定 `[0,.70]`、`(.70,.90]`、`(.90,1]`；crossing point 与最佳区间仅可描述。AURC/NRC 使用按 `(score desc,row_key asc)` 的冻结兼容实现，只作 legacy diagnostic，永不单独驱动 gate。

## 5. 推断与 formal witness

固定 `seed=20260809`、replicate `0..9999`，数据集顺序与 index 固定为 `DIOR-R=0, FAIR1M=1, SODA-A=2`。cluster id 先按 UTF-8 byte order 排序；每个 dataset 使用 `numpy.random.RandomState(20260809+index)`，按 replicate id 顺序调用一次 `randint(0,n_clusters,size=n_clusters)`，再以 `bincount(...,minlength=n_clusters)` 得到 multiplicity。zero-cluster universe 本身即异常；zero-eligible clusters 正常保留。同一数据集内所有 units、probes、losses、endpoints 共用该 multiplicity；保存每个 replicate 的 multiplicity SHA。39 workers、BLAS threads=1，replicate-to-worker 固定为 `replicate_id % 39`，结果只按 replicate id 确定性合并。

matched、features 与 scores 的唯一行键固定为 `(image_id,pred_id)`，且三份源表各自全表键必须唯一。每个 unit 必须先从 matched JSONL 按原始文件顺序，仅以 `image_universe.csv` 的显式 membership 筛出完整 `D_audit` matched base cohort，冻结完整键序列、排序键集合及二者 SHA；五个 eligibility 定义都只能从该 base cohort 派生。features/scores 先对 base-cohort keys 做 semi-select，再分别以 `validate=one_to_one` left join；base cohort 的 missing/duplicate/drop 必须为 0，连接前后行数与键序列必须相同。features/scores 全表中不属于 base cohort 的合法 extra keys 允许存在，但必须分别记录 count、sorted-key SHA，且永不进入任何 endpoint。`detection_score` 只要求在 features 与 scores 的对应 cohort rows 中逐行 finite 且精确相等；matched 不得被要求存在该字段。正式 probes、GT OBB、membership、cluster 与 eligibility 所需真实字段必须 schema 完整且 finite。任一断言失败即 `NOT_ADJUDICATED`，禁止 inner-join、drop、impute 或各 probe 自行缩小 cohort。

对每个完整 hypothesis key `H=(level,key,contrast,endpoint,ablation_id)`，lower is better，并分别定义 `Delta_main(H)=M_probe_main(H)-M_raw_main(H)`、`Delta_ablation(H)=M_probe_ablation(H)-M_raw_ablation(H)` 与 `DoD(H)=Delta_main(H)-Delta_ablation(H)`。`M_probe_main/M_raw_main` 只能来自 H 的主定义同一 cohort，`M_probe_ablation/M_raw_ablation` 只能来自 H 的指定消融同一 cohort；不得跨 level、unit/dataset、contrast、endpoint、ablation 或 eligibility 复用 operand。两实现均独立按 exact JSON finite grid、稳定排序、`numpy.interp` 与 frozen inverse-AR tail 公式实现 table-driven delta，并达到 `atol=1e-12,rtol=0` parity。实现 B 另在每个 finite grid ar 上以独立 polygon/bisection 重算未四舍五入 direct root；与存储四位小数值的容差固定为 `solve_tolerance_deg + 0.5*10^-4 = 0.00105 degree`，禁止先 round direct root 或拿 off-grid direct root 对插值值套门。row risk、point metric、replicate 与 DoD 的 A/B 数值容差统一为 `atol=1e-10,rtol=0`，keys/count/hash/state 必须精确相等。endpoint effect bands 固定为：

```text
epsilon_AUGRC = max(5e-4, 0.02 * max(abs(M_probe), abs(M_raw)))
epsilon_Risk  = max(1e-3, 0.02 * max(abs(M_probe), abs(M_raw)))
```

对 H，`epsilon_main(H)` 只由 `(M_probe_main(H),M_raw_main(H))` 代入上式，`epsilon_ablation(H)` 只由 `(M_probe_ablation(H),M_raw_ablation(H))` 代入上式；两者都只从各自原始 point estimates 计算一次，bootstrap 内不得重算。percentile CI 固定为排序后线性分位数 0.025/0.975。Holm 将假设按 `(raw_p,hypothesis_key)` 排序，依次计算 `(m-rank+1)*p`、取前缀最大并 clip 到 1；任何 NaN/Inf、缺 hypothesis 或重复 key 都使执行异常。主/消融 contrast CI 只是预声明的保守稳定性过滤，正式 family 推断只由 DoD p 的 Holm 调整承担。

正式 OBB-specific witness 必须同时满足：

- 主定义与固定消融的 supported order 符号相反，且只允许两种精确条件：`PROBE_BETTER_MAIN__RAW_BETTER_ABLATION` 要求 `Delta_main_CI_high < -epsilon_main` 且 `Delta_ablation_CI_low > epsilon_ablation`；`RAW_BETTER_MAIN__PROBE_BETTER_ABLATION` 要求 `Delta_main_CI_low > epsilon_main` 且 `Delta_ablation_CI_high < -epsilon_ablation`；
- `DoD` 的双侧 centered-bootstrap p 精确为 `(1 + count(abs(DoD_b-DoD_hat) >= abs(DoD_hat))) / 10001`，在预声明 family 内 Holm-adjusted `<0.05`，95% cluster CI 排除 0，且 `abs(DoD)>=epsilon_main+epsilon_ablation`；
- whole-tie accepted set 固定为 `A_score,q={row: score>=第一个使实际coverage>=q的unique threshold}`，不得用 row-key 拆 tie。对 H 的主定义与指定消融分别计算 `swap_main_q(H)=|A_probe_main,q symmetric_difference A_raw_main,q|/|A_probe_main,q union A_raw_main,q|` 与 `swap_ablation_q(H)`；Risk@70/90 witness 要求对应 q 的两者都 `>=0.05`。AUGRC 的 main/ablation q=.70/.90 swaps 均报告但不驱动 AUGRC witness。dataset 的每个 swap operand均为 constituent unit 对应 swap fractions 的 equal-unit mean，禁止 pooled set；
- witness 不依赖 S0/EQS，且不是仅有 AURC/NRC 与 AUGRC 反转。

unit family 恰为 `6 units × 3 contrasts × 3 endpoints × 5 geometry/AR ablations=270`；dataset family 恰为 `3 datasets × 3 contrasts × 3 endpoints × 5 geometry/AR ablations=135`。两个 family 分开 Holm，禁止执行后拆 family、挑 coverage、挑 probe 或挑消融。effect-class 映射固定为 `NO_LONGSIDE_AR21 -> ANGLE_EQUIVALENCE`、`NO_GEONORM_AR21 -> GEOMETRY_NORMALIZATION`、其余三个 -> `AR_DOMAIN`。`SCENE_MACRO` 仅按上一节的纯描述合同输出，既不加入或替代 OBB gate，也不得导出 instance-IID 或 material/category-change 结论。

## 6. 唯一四态裁决

- `PASS_TO_EXTERNAL_CONFIRMATION`：全部审计闭合；同一个完整 `(effect_class,ablation_id,contrast,endpoint,supported_direction)` signature 在至少两个 dataset aggregates 形成正式 witness；同一个完整 signature 的 unique unit witnesses 合计至少 4/6、覆盖至少两个 detector families；SODA dataset aggregate 与至少一个 SODA unit 都必须形成该完整 signature 的 witness；effect class 必须属于 ANGLE_EQUIVALENCE、GEOMETRY_NORMALIZATION 或 AR_DOMAIN，scene weighting 不能替代。`supported_direction` 只能是 `PROBE_BETTER_MAIN__RAW_BETTER_ABLATION`（`Delta_main<0<Delta_ablation`）或 `RAW_BETTER_MAIN__PROBE_BETTER_ABLATION`（`Delta_ablation<0<Delta_main`），不得跨相反方向合并。
- `FAIL_GENERIC_OR_NULL`：全量执行闭合且 unit 与 dataset 的正式 OBB-specific witness 均为 0；`generic_only=true` 精确定义为至少存在 legacy AURC/NRC-vs-AUGRC supported reversal、但 formal OBB witness 总数仍为 0，它也归本状态。
- `INCONCLUSIVE_MIXED`：全量执行闭合、至少一个 formal OBB witness，但不满足 PASS，例如仅 1-3 units、单数据集/单 detector family、signature 未在两数据集复现或 SODA 条件不满足。
- `NOT_ADJUDICATED`：任一 input identity、实现独立性、A/B parity、bootstrap、mutation、manifest、scope、Git、push 或 external receipt 失败。

precedence 固定为 `NOT_ADJUDICATED -> PASS_TO_EXTERNAL_CONFIRMATION -> FAIL_GENERIC_OR_NULL -> INCONCLUSIVE_MIXED`；每个 valid execution 必须恰好落入后三者之一。detector family 只按前述 PSC/Oriented R-CNN/RTMDet 三个 unique family identity 计数，unit/dataset 也只按 unique identity 计数。前三种科学结果均可属于正常完整执行；`PASS_TO_EXTERNAL_CONFIRMATION` 只允许另行设计真正独立确认和改稿，不等于 JPRS/TGRS ready，也不自动授权下一轮。不得用 FAIL/INCONCLUSIVE 触发 receipt4、换 gate、换 target 或复活 EQS。

## 7. 独立实现与无环证据

两个生产实现只能共享冻结 protocol constants 与原始输入，禁止共享 helper、metric、gate、replicate multiplicity 或历史实现。A、B、Comparator 和 closure code 必须先在 synthetic fixtures 上完成，随后在任何 scientific input 第一次打开前共同冻结 code-tree bytes/SHA；此后任何代码变化都使本轮异常，不能边看全量结果边修。先运行实现 B，此时实现 A outputs 必须不存在；B 直接从原始输入独立实现 canonicalization、delta root audit、AUGRC、bootstrap、Holm 和 gate。封存 B 后再运行 A；B trace 必须无 A，A trace 必须无 B，二者均不得读取 receipt3 或彼此输出。Comparator C 只能在 A/B 均封存后读取二者，逐 row key、cluster universe、point metric、全部 replicate、CI/p/Holm、witness 和 gate 比较，并执行上一节的冻结容差。

六个 isolated mutation 必须修改真实 copied raw/logic，而非摘要布尔：改变一条 m069 `pred_obb.theta`、改变一条 SODA tile→mother、删除 AUGRC 原点或改 generalized-risk 分母、把 gate 的 two-dataset 改成 one-dataset、从 copied manifest/access trace 删除一个实际科学输入事件、篡改 copied report 的 scientific gate/completion token。前四项在 scientific runtime freeze 前对隔离 copy 执行；第五项只能在真实 manifest 生成且 pristine closure 通过后，由 seal 外 checker 对 manifest/access copy 执行且不得回写 runtime；第六项只能在最终 report bytes 已于内存中确定后，对该 exact pristine byte buffer 与 mutated copy 执行，随后一次性写出与 pristine SHA 相同的 report。每项 pristine copy 先通过，mutated copy 必须由同一阶段的 independent validator/closure checker 非零拒绝并保存 before/after SHA 与语义 witness；post-push external receipt 必须重新 hash 已发布 report并重放第六项，任何不一致即异常。

闭包严格无环并分为两个 seal：

```text
raw inputs -> B/A outputs -> comparator/first-four-mutations -> SCIENTIFIC_RUNTIME_FREEZE
-> runtime_manifest -> pristine closure/manifest-mutation -> planned-report/report-mutation
-> tracked report/supervisor append
-> TRACKED_CONTENT_SEAL -> commit/push -> post-seal external receipt
```

在首个 scientific input open 前，先启动已经 code-sealed 的独立 tracer，并在 synthetic fixture 上证明 `strace` 存在、ptrace 权限正常且能捕获子进程；失败即 `NOT_ADJUDICATED`。每次应用层 scientific read 必须先 append `sequence,phase,pid,path,declared_role,bytes,sha256,monotonic_ns,prev_event_sha,event_sha`，flush+fsync 后才把 bytes 交给 A/B/comparator；全程另以 `strace -ff -e trace=open,openat,statx` 保存 OS-level path trace。事件 hash 链必须从固定 genesis 连续到 freeze，sequence 无缺口。

OS trace 归一化固定为：只把返回值 `>=0` 且 flags 为 read-capable 的 `open/openat` 计作 read event；按记录时 PID 的 cwd/dirfd 解析绝对路径，再做 symlink-resolved realpath；`statx` 只作路径旁证，不计 read。`OS_scientific_relevant` 只含 normalized realpath 精确命中上述 26 个科学输入的事件；A 与 B 各自必须覆盖全部 26 个输入。每个应用事件须在同 phase/process tree/path 至少有一个 OS relevant open，每个 OS relevant open 须映射到恰一个 declared application path/phase，允许同一应用事件对应多次底层 open。对 m069/r014/frozen-delta roots 的任何其它 read-capable open、任何 receipt3 read，均为 forbidden；其它事件必须按互斥 `SEALED_CODE|RULE_OR_GIT_PREFLIGHT|RUNTIME_READ|OUTPUT_WRITE|SYSTEM_LIBRARY` 分类并保存，不能进入 scientific-set 等值比较。closure 对 relevant set 做上述双向 coverage，再将应用事件、A/B traces 与 manifest 的 path/bytes/SHA/phase 全字段核对。禁止任务结束后批量伪造/补写整份 access log，任何未通过 tracer 的 scientific open、链断裂、unclassified open 或双向 coverage 失败即异常。

在 `SCIENTIFIC_RUNTIME_FREEZE` 前关闭 scientific inputs、A/B/comparator/前四项 mutation outputs、command ledger、resource telemetry 与上述 file-access events；freeze 后唯一允许的新 runtime 对象是 manifest。manifest 枚举 freeze 前全部实际 input/code/runtime bytes、SHA、schema、keys，并与 access events 做 path/bytes/SHA/phase 全字段等值比较；大文件必须真实流式计数和取 schema，禁止从 bytes 猜 row count。manifest 自身写 `EXTERNAL_HASH_ONLY`，明确排除未来 report/Git/external receipt。仓库外 closure checker 不回写 runtime，先验证 manifest 无漏项/多报、全部 scientific inputs/access events 和自身 hash并完成第五项 mutation；随后以最终 gate/completion 和前五项结果构造 report exact bytes，在内存完成第六项 pristine/mutated 检验后，才一次性写 tracked report 与 supervisor append。report 自身写 `EXTERNAL_GIT_BLOB_ONLY` 与 `POST_COMMIT_EXTERNAL_RECEIPT`，不得宣称覆盖未来 Git 或 receipt。完成 `TRACKED_CONTENT_SEAL` 后，tracked/runtime 内容绝对零写；Git/push 后的 receipt 只能作为明确的 post-seal external output，并必须解析已发布 report，核对其 gate/completion/manifest identity 与 A/B/comparator 一致并重放 report mutation。

## 8. 资源、停止和投稿后果

服务器只允许新 code root、runtime root、唯一 report、supervisor append，以及 seal 外唯一 `postseal_receipt_root`。该 root 在 scientific runtime freeze 后首次创建，只允许固定 hash-chained command log、atomic `postseal_receipt.json` 与 SHA256 sidecar；post-push checks 后先以 `POSTFREEZE_COMMAND_LOG_SEAL` 封存 log，receipt 只哈希该 sealed prefix，随后 code-sealed writer 以无 shell/subprocess 的固定 syscall protocol写 JSON/sidecar，避免自引用。该 ignored receipt 只决定服务器阶段 normal/abnormal，tracked report 始终 provisional；跨电脑正式科学态必须由 C 拉取 result commit 后独立复核并另写 `dis/` 状态提交。CPU-only；preflight 必须确认 `N=48` logical CPUs，否则异常。固定 39 worker processes、39-core affinity、BLAS threads=1；job CPU 定义为每个完整 30 秒 interval 内该 r020 process tree 的 CPU-time 增量除以 `(30*N)`，coordinator 以可复核 duty-cycle 暂停/恢复把 bootstrap parallel phase 的每 interval job CPU 保持在 `60%<=job_cpu_pct<=80%`。三个连续完整 interval `<60%` 且没有逐 interval 记录 `IO_WAIT|SERIAL_PHASE` 理由，或任一完整 interval `>80%`，均异常；preflight/serial/finalization interval 只需记录 phase/reason，不适用下限。每 30 秒采集真实父子 CPU-time/RSS/affinity、活跃/暂停 worker 数、job_cpu_pct 与 throttle 事件；replicate-to-worker 映射不因 throttle 改变。GPU、一般下载、安装、训练、forward、inference、新 target、dataset annotation root、主稿修改均禁止。

唯一网络例外是在新 runtime 内恰一次 HTTPS fetch `https://github.com/IML-DKFZ/fd-shifts.git` 的 commit `c4467aec134e99691359da209f811d91283fc1e3`；不得换 remote/commit、额外 fetch、执行 hooks/submodule/LFS、安装依赖或消费 receipt3 checkout。detached clean checkout 必须从 `git ls-tree -r --full-tree` 唯一得到 `fd_shifts/analysis/rc_stats.py`（blob `563be2ed8652c730dd940eb241d8642717e25c0d`，raw SHA256 `d7f823c58bae5bbee4af2c0b5296bea41d6494884bd868d859890e9ccac22619`）与 `fd_shifts/analysis/rc_stats_utils.py`（blob `9f99c499f370b587d0ca73e2d9679a358de55e05`，raw SHA256 `a827fcf36d278beccc804e0d1895428f920c746dcc316a19f81bf3f341276b1f`）。必须从这些 exact bytes 动态调用或以 AST-verbatim adapter 构造 `RiskCoverageStats(...).curve_stats_generalized_risk/.augrc`，动态读取 `AUC_DISPLAY_SCALE=1000`，把 display AUGRC 除以 1000 得 unscaled 值，并以 binary/continuous/tie/boundary toys 达到 `atol=1e-12,rtol=0`。wall time 上限 18 小时，新 runtime 上限 30 GB。

来源/hash/代码/审计/Git 失败属于 `FAILURE_EARLY_STOP / NOT_ADJUDICATED`；不利科学中间结果不得早停，A-F 与 10k 必须完成。正常完成模式只能是 `FULL_COMPLETION_POSITIVE`、`FULL_COMPLETION_INCONCLUSIVE`、`FULL_COMPLETION_NEGATIVE`；只有这三种才允许 `sug_genuinely_exhausted: true`。服务器最终聊天必须严格为项目 wrapper 加唯一一句 `正常执行完毕` 或 `异常结束`，无路径、SHA、解释或列表。PASS 使 JPRS measurement-diagnostic 路线具备进入外部确认的资格；FAIL 关闭顶刊实验循环并按 JSTARS scope 收口；INCONCLUSIVE 不换 gate 续命。

执行前必须记录 configured origin/upstream 迁移元数据，但权威远端和全部 network Git 命令只使用显式 `https://github.com/ziyu24/orientbench.git`；不得调用或修改 configured SSH origin。current 与 HTTPS default branch 必须为 main；upstream 可缺失/陈旧但只记录。核验完整 pre-pull/post-pull HEAD、显式 HTTPS remote main、两端 40-hex ahead/behind=0、index/worktree clean、B blob/diff 元数据与所有新路径不存在；只允许显式 HTTPS `pull --ff-only ... main`。服务器把通过 preflight 的 `post_pull_head` 冻结为 `execution_base`；final result commit 前再次要求 HTTPS remote main 仍等于该 `execution_base`。远端移动即异常停止，禁止 merge/rebase/amend/第二 commit。服务器结果提交必须以 `execution_base` 为唯一父提交、恰一个 non-merge commit并只含授权路径；push 后外部 receipt 全部闭合才可回复正常。
