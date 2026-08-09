# OrientBench r019：修正型 EQS 在 DOTA 上的单次前瞻外部端点验证

- `round_id`: `orientbench-c-r019-20260809`
- `control_base`: `f53bb670dea92dca9c0056e20c0cd338d0e52c14`
- `scientific_data_cutoff`: `8ce84331a14c12a5ac41e46cb354ca712286626e`
- `status`: `READY_FOR_SERVER_EXECUTION`
- `server_report_path`: `dis/server_reports/orientbench-c-r019-20260809.md`
- `runtime_root`: `outputs/persistent_artifacts/orientbench_r019`
- `prelabel_remote_commit_required`: `true`
- `final_response_first_line`: `执行完毕` 或 `未执行完毕`

## 0. 任务身份与唯一问题

本轮只回答一个问题：在 r019 模型/selector 与全部 target scores 封存前不读取 DOTA 标签、全程不用 DOTA 结果选模型的前提下，仅用 Core-6 三个源数据集的 `D_cal-fit` 拟合，修正后的 `EQS-RC-R019` 能否在固定的 DOTA-v1.0 Oriented R-CNN 与 Rotated RTMDet-M 两个单元上，优于固定的 `score + AR + size` 线性基线？

这不是 r012 HRSC 的替补，不是对 r015 的追溯性确认，也不是两个独立数据集确认。DOTA 在本项目别处已有 detection/angle 描述性结果；本轮的新信息仅是此前未计算、且须在揭示标签前封存的 `EQS-RC-R019 vs linear` 端点。两个单元共享同一 DOTA 数据集、同一 5,297 个 tile 和同一 mother-scene universe，只能称为“一个外部数据集上的两个 detector-family 单元”。两个 family 在源数据中均已出现，因此不能写成 unseen-family transfer。

r015 的 Core 6/6、dataset 3/3 只保留为开发期 exploratory evidence。r014 HRSC `Delta_NRC=0.0602, 95% CI [-0.0143, 0.1438]` 已揭盲且跨零，只能原样引用为历史 sensitivity；严禁重跑、扩样、换 bootstrap 或进入 r019 gate。旧 DOTA `33,029/34,383` 是另一过滤口径的 matched rows，不是独立样本量、功效依据或 r019 eligible 数。

## 1. 开始前的硬停止条件

服务器先完整读取仓库根及上级所有适用 `AGENTS.md`、仓库适用 `CLAUDE.md`、`dis/collaboration_protocol.md`、本文件，以及 `/home/rspip/cqc/pro/study/pth_data/readme.md`。后者缺失、不可读或与资产冲突即停止；不得猜测 checkpoint、config、数据集或环境。

随后逐项完成并落盘 preflight：

1. 使用 HTTPS 拉取 `main`，确认包含本轮 `dis/sug.md`；记录完整 HEAD、origin、默认/当前分支、upstream、工作树。已有仓库只允许 `git pull --ff-only`。工作树脏、不能 fast-forward、远端不符或规则冲突即停止。
2. 确认 `dis/B.md` 的 Git blob 仍为 `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`；只读，绝不能修改、暂存、恢复或提交。
3. `outputs/persistent_artifacts/orientbench_r019` 必须尚不存在。若已存在，不删除、不覆盖、不另起同义目录，按 `FAIL_PROVENANCE_R019` 停止并报告。
4. 读取并逐字段核验 `reports/069_dota_clean_artifact_manifest.csv`。固定单元只有：
   - `DOTA-v1.0/orcnn`：config SHA256 `5076fefbcdb8763e68888abff9f9c39efa2b49881b4450c3f6240446a7898792`，checkpoint SHA256 `f988b9a6b3d3662b22f2499679269bb00164417801957017082f6acdc9cf314c`；
   - `DOTA-v1.0/rtmdet`：config SHA256 `d764820e7934f97ac1ab2a0f8e09a24ea3a126cd25e38bf5c2230bb59786fbe7`，checkpoint SHA256 `fba480d7bd1172ee41fd2b89b314fb48a4e5c0e3b455815c838781b0127954ee`。
   固定 full-val 身份是 5,297 tiles、55,804 GT、DOTA#20 excluded。路径必须以 readme 和 manifest 的实际值为准；不得自动找“相近”权重代替。
5. 核验 r014 Core A–F 的 identity/hflip/vflip 原始预测、label、cluster universe 及其哈希，来源以 `p3_selector/deployable_proxy_r014/reports/tta_inventory_r014.csv` 和 `provenance_r014.csv` 为准。本机缺失任一必需服务器资产时停止，不能用汇总 CSV 或重构伪原始资产代替。
6. 在服务器持久化目录和仓库中搜索这两个精确 DOTA 单元既有的 identity/hflip/vflip raw、修正型 feature、修正型 score、`EQS-RC-R019 vs linear` 数值或 gate。搜索只能读取仓库代码/报告及明确非标签的 prediction-only 路径；必须排除真实 `val/annfiles/**`、旧 matched JSONL 和任何标签承载文件的内容。对已知标签路径只复制 committed manifest 中的既有记录，prelabel 前不得 open/stat/hash/decode/grep；对发现但标签身份不明的文件只记父目录与 basename 后即 fail closed，不得为分类而打开。明确非标签文件才可记录 path/bytes/SHA256/mtime。若本协议提交前已有相同端点数值被生成或消费，记 `FAIL_PRIOR_OUTCOME_EXPOSURE_R019`，DOTA 不得称为前瞻确认，也不得继续揭示标签。

## 2. 冻结的算法、数据和 estimand

### 2.1 固定目标单元与数据

- `DOTA-v1.0/orcnn`：manifest 指定 Oriented R-CNN config/checkpoint。
- `DOTA-v1.0/rtmdet`：manifest 指定 Rotated RTMDet-M config/checkpoint。
- 输入只能是固定的 DOTA-v1.0 `split_ss_dota10/val` 全部 5,297 tiles。不得训练 detector、改权重、改 split、改测试尺度、改 score threshold、删困难图、加入 DOTA#20 或换数据集。
- 首次接触标签前，用全部 5,297 个 image stem 生成 image-only registry 和 mother map。候选规则为 `stem.split('__', 1)[0]`，但必须用全量文件名与 split 元数据实证闭合：5,297/5,297 唯一映射，unmapped=0、ambiguous=0、duplicate tile=0；两个单元的 sorted tile set 和 sorted mother set/count/SHA256 完全相同。零 eligible 的 mother 也必须保留。若该规则不能闭合，技术早停；禁止把 5,297 tiles 偷换成主 bootstrap cluster。

### 2.2 修正型 `EQS-RC-R019`

本轮 primary 是明确修正过的 selector，不是 r014 实际实现。修正项在读 DOTA 标签前固定；不得在 target 结果出现后回退、换版或双候选择优。

每个 OBB 先唯一规范化为：

```text
long = max(w, h)
short = min(w, h)
theta_long = wrap_mod_pi(theta + pi/2 if h > w else theta)
```

全部角度、宽高和尺度相关特征均使用这一 long-side canonical 表示。identity 与每个逆变换回 identity 坐标系的 auxiliary view，在同类候选间以 rotated IoU 全局贪心一对一匹配，接受阈值固定 `rIoU >= 0.3`；稳定排序固定为 `(-IoU, -view_score, identity_original_index, view_original_index)`。任何并列必须由该顺序唯一解开。

association margin 的唯一语义按 `identity prediction × auxiliary view` 分开计算：在 global greedy 之前，收集该 identity 在该 view 的全部同类 `rIoU>=0.3` 候选；0 个候选时 margin=0，恰好 1 个时 margin=1，至少 2 个时为 `clip(top1_IoU - top2_IoU, 0, 1)`。global greedy 完成后，只为该 identity 实际取得 match 的 view 保留对应 pre-greedy margin；两个 view 都 matched 时取两者 median，仅一个 matched 时取该值，两个都未 matched 时总 sentinel=0。不得在 greedy 后把“至多一个 match”误当候选集合，也不得沿用 r014 “单候选返回 top1 IoU”的实际偏差。

独立 doubled-angle axial dispersion 固定为：

```text
clip(1 - abs(mean(exp(2j * theta_long_k))), 0, 1)
```

角集合包含 identity 与所有已接受 auxiliary matches。没有 auxiliary match 时 sentinel 固定为 1，同时 `missing_fraction=1`。该字段必须独立存在；不得拿 `u_axis` 改名或复制公式替代。

其余逐 view 与跨 view 聚合也固定如下，不能由服务器自行解释：score 先 clip `[1e-6,1-1e-6]`，logit 后 clip `[-13.815511,13.815511]`；`pred_ar=long/max(short,1e-6)`，`log_pred_ar=clip(log(max(pred_ar,1+1e-6)),0,4.605170)`；`area=max(long*short,1e-6)`，`half_log_pred_area=clip(0.5*log(area),-6.907755,9.210340)`。`support_fraction=matched_view_count/2`，`missing_fraction=1-support_fraction`。对每个已匹配 view，angle 是 canonical `theta_long` 的 mod-pi 最小夹角（degree）；`iou_loss=1-rIoU`；center 是中心欧氏距离除以 identity `sqrt(area)`；long/short dispersion 分别是对应 canonical 边长比的 absolute log；score dispersion 是 clipped-logit 的 absolute difference。跨 matched views 全部取 median；`u_axis=clip(median(angle)/max(delta_theta_0.75(pred_ar),1 degree),0,3)`，`iou_loss` clip `[0,1]`，center/long/short clip `[0,3]`，score dispersion clip `[0,10]`。没有 matched view 时固定 `(u_axis,iou_loss,center,long_disp,short_disp,score_disp,margin)=(3,1,3,3,3,10,0)`。除本节明确修正的 long-side canonicalization、axial dispersion 和 margin 外，其余数值语义沿用并动态调用 r014 production 定义；r019 protocol 必须保存对应 source path/line 与代码 SHA256。

固定 13 维 feature 顺序：

```text
[logit_score, log_pred_ar, half_log_pred_area,
 support_fraction, missing_fraction, axial_dispersion,
 u_axis, iou_loss, center_dispersion,
 long_side_dispersion, short_side_dispersion, score_dispersion,
 association_margin]
```

固定 HGB：构造器只传 `max_iter=200, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1.0, min_samples_leaf=50, random_state=20260807` 与 `monotonic_cst`，其余参数使用被 seal 的 sklearn 版本默认值；固定 monotonic vector 为 `[-1,0,0,-1,1,1,1,1,1,1,1,1,0]`。拟合 target 是 source risk，EQS reliability score 固定为 regression prediction 的负值。若当前 sklearn 不支持该合约，技术早停，不能静默换 estimator。

固定 linear baseline：只用前三项 `[logit_score, log_pred_ar, half_log_pred_area]`，无额外 constructor kwargs 的 `StandardScaler + LinearRegression`，拟合 source risk，reliability score 同样为 prediction 的负值。固定 standalone sensitivity：`-(u_axis + missing_fraction + iou_loss)`；它不是替代 primary 的第二次机会。

### 2.3 源端拟合与泄漏隔离

- 训练源仅限 Core 三数据集 DIOR-R、FAIR1M-v1.0、SODA-A 的 canonical `D_cal-fit` rows；复用 `m069_common.split_role` 的 MD5 parity。必须动态调用实际 production function/code path并保存 source path、line witness、row keys/count/sorted SHA256。
- 总权重按 dataset 各 `1/3`，dataset 内 unit 等权、unit 内 row 等权。不得因行数让某 dataset 或 detector 支配。
- 严禁使用 Core `D_audit` 的 feature/label/risk、r014/r015 target score、bootstrap、unit/dataset result 或 gate 来训练、归一化、调参、选择 feature、选 seed 或选 early stop。若 D_cal 与 D_audit 物理共存于同一 JSONL，允许流式读取 routing key/image_id 并先按冻结 MD5 role 丢弃 D_audit；D_audit row object 的 feature/label/risk 不得 materialize、缓存、聚合或进入任何模型/功效计算，须由 taint/access audit 证明。
- 在 prelabel 阶段完成三折 leave-one-source-dataset-out：每折仅用另两个 dataset 的 `D_cal-fit` 拟合，在 held-out dataset 的完整 `D_cal-calib` 上评估，dataset 内 unit 等权、禁止 pooled rows；DIOR/FAIR 用完整 image cluster，SODA 用完整 mother-scene cluster，零 eligible cluster 保留。同一 fold 内各 unit 使用同步 multiplicity，固定 `B=10,000`、seed=`20260806 + fold_ordinal`（fold ordinal 按 DIOR-R、FAIR1M-v1.0、SODA-A 为 0、1、2）、95% percentile CI。LODO 只作方向诊断，任何结果都没有早停、换模型、调参或换 gate 的权力。
- 同一 prelabel 阶段做盲态功效/MDE 审计：仅使用上述三个 source `D_cal-calib` LODO aggregate 的 centered cluster-bootstrap 标准差，取三者最大值 `se_worst`；固定 one-sided alpha=0.05，`power_at_Delta_0.02 = Phi(0.02/se_worst - 1.6448536269514722)`，`MDE80=(1.6448536269514722+0.8416212335729143)*se_worst`。报告每 fold 的 cluster/unit/row 数、SE、最坏 fold、假设与公式。不得读取 DOTA label/旧 matched risk，不得因此改变 B、selector、unit、gate 或是否执行 DOTA；低预测功效只预警 INCONCLUSIVE 风险，禁止 target 后报告 post-hoc achieved power。

### 2.4 标签附着后的固定 estimand

- identity raw 与 DOTA GT 进行同类一对一贪心匹配，固定 `rIoU >= 0.5`：prediction 按 `(-prediction_score, prediction_original_index)` 依次处理；对当前 prediction 的尚未使用同类 GT 候选按 `(-rIoU, gt_original_index)` 取唯一第一名，低于阈值则不匹配。必须从封存的 identity raw 新鲜重建，不能把旧 matched JSONL 当 raw。
- eligible 仅为 matched identity TP 且 `GT_AR >= 2.1`。不再使用旧口径的 pred-AR near-square 排除；不得加任何 target 后过滤。
- risk 定义、`delta_theta_0.75`、floor=1°、cap=3 沿用冻结 m069/r014 production 定义并动态调用；不得手抄近似公式。
- 单元主 estimand：`Delta_u = NRC(linear) - NRC(EQS-RC-R019)`，正值表示修正 EQS 更好。
- DOTA 主 estimand：`Delta_DOTA = (Delta_orcnn + Delta_rtmdet) / 2`，两个 unit 等权；禁止 pooled-row aggregate。
- standalone guard：`G = NRC(standalone) - NRC(EQS-RC-R019)`，正值表示 learned EQS 不弱于 standalone。

## 3. 两阶段时间锁：标签前必须先推远端

### Phase A：实现、动态微测和无标签前向

新建独立目录 `p3_selector/deployable_proxy_r019/`；禁止修改 r014/r015/r016/r017/r018。所有测试必须动态调用 r019 的实际 production function/code path，禁止在 validator 中复制公式后自测。

在 r019 受控进程/actual-input manifest 首次访问任何 DOTA GT、annotation 内容或旧 matched JSONL 前，必须让 production microtests 全部通过并保存 expected/actual/tolerance/seed/trace。项目历史上已经使用过这些标签，报告只能声称“r019 受控访问为零”，不得声称项目首次读取：

1. horizontal/vertical inverse 及 double-flip roundtrip；
2. 0°/90°、`(w,h,theta)` 与 `(h,w,theta+90°)` 的全 13 字段等价；
3. doubled-angle axial dispersion 的同向、轴向等价、分散与 no-aux sentinel；
4. association margin 的 0/1/2/multi-candidate 正例和错误 top1-IoU 负例；
5. missing、duplicate、ambiguous、dense candidate、stable tie 与 class mismatch；
6. transformed coordinate inverse 后 box/angle/score/identity index roundtrip；
7. feature/score schema 逐字段无 `GT`、`ground_truth`、`angle_error`、`risk`、`GT_AR`、`split`、`role` 或其大小写/前缀/contains 变体；
8. fail-closed 测试：任一非 finite、重复 key、未知 view、缺 image、错误 unit 或 schema drift 必须非零退出。

随后每单元先跑固定 50-image、identity/hflip/vflip 的 production GPU smoke。DOTA forward 必须使用由 5,297 个 image filenames 生成的 runtime image-only registry 与自定义 image-only loader，或 runtime 空 annotation dataset；禁止实例化会解析真实 annotation 的 DOTADataset。prelabel file-access guard 必须拦截 `open/openat/stat/scandir/glob/hash` 对真实 `val/annfiles/**`、旧 matched JSONL 和其它 DOTA label-bearing paths 的任何访问，命中一次即 `FAIL_TIMELOCK_R019`。config 中出现 annotation path 字符串不等于访问，但不得触发 dataset initialization。只允许在未生成 full target scores 且 r019 target-label access count 仍为 0 时，修正“实现未满足本节冻结语义”的代码错误；每次修正必须写入 changelog并重跑全部微测与 smoke。不得依据预测分布、source LODO 好坏或任何 target label 修改设计。

微测与 smoke 通过后：

1. 在 Core A–F 原始三视图资产上重建修正型 features，做冻结的源端 LODO 与盲态 power/MDE，随后仅用全部 Core `D_cal-fit` 按固定权重拟合唯一 HGB 与 linear；保存 source row sets、weights、model bytes/SHA256、环境和 deterministic replay witness。
2. 使用固定 config/checkpoint，对两个 DOTA 单元各做全 5,297 images 的 identity/hflip/vflip 新鲜前向。可用 4×A30，但两个单元顺序执行；不得训练 detector。原始输出必须保存 score、class、canonical/raw box、original index 和 view，不能只存 matched rows。
3. 仅用预测和 image-only registry 构建 DOTA features、两个冻结 selector scores 与 mother map。此时 target-label access count 必须为 0。
4. 固定 bootstrap `B=10,000`、seed=`20260809`，在完整 mother universe 上预生成恰好 10,000 组 mother multiplicity；同一 replicate 的同一 multiplicity 将同步用于两个 detector、linear/EQS/standalone。保存 draw file 的 bytes、SHA256、replicate/mother 完整性。

### Phase B：prelabel seal commit/push

在 r019 受控进程/actual-input manifest 第一次允许访问 DOTA GT 前，必须生成机器可验的 prelabel seal，至少封存：本协议 blob；全部 r019 代码/测试；production microtest 与 smoke；源 row universe/MD5 roles/weights；LODO 与 power/MDE；唯一 HGB/linear model；DOTA 5,297-tile 与 mother universe；六份 raw view inventories；prediction-only features/scores；bootstrap draws；config/checkpoint/data/readme/env；实际 file-access log；所有文件 bytes/SHA256/schema/row count/key uniqueness。

原始预测、Parquet、model bytes 和 draw arrays 等大资产必须只存入 Git-ignored `outputs/persistent_artifacts/orientbench_r019/**` 并保持只读；prelabel commit 只提交其逐文件 inventory/bytes/SHA256/schema/count/key witness 和可复放代码，禁止把大二进制塞入 Git。远端 commit 中的 canonical prelabel manifest SHA256 是这些 runtime bytes 的时间锁；final validator 必须再次从同一 runtime bytes 重算并逐项相等。

prelabel seal 只能写入：

- `p3_selector/deployable_proxy_r019/protocol_r019.json`
- `p3_selector/deployable_proxy_r019/scripts/**`
- `p3_selector/deployable_proxy_r019/tests/**`
- `p3_selector/deployable_proxy_r019/prelabel/**`
- `claude_code_and_supervisor.md`（仅 append r019 命令与结果）

显式暂存上述精确路径，形成独立 prelabel commit，并通过 HTTPS push 到 `main`。再从远端 HTTPS 获取并确认 remote `main` 精确等于该 commit；记录 commit、parent、remote SHA、精确 changed paths、`dis/B.md` parent/head blob equality、工作树。由于 commit SHA 不能自引用，prelabel manifest 内固定写 `prelabel_commit_sha=POST_COMMIT_RUNTIME_RECEIPT`；push 后的只读 receipt 只写 runtime，最终 result commit 再收录并由 validator 核验。若 push 或远端确认失败，记 `FAIL_TIMELOCK_R019` 并停止。

从 prelabel commit 形成到最终报告期间，协议、代码、测试、source sets、models、raw、features、scores、mother map 和 draws 不得改变一个字节。若改变，记 `FAIL_TIMELOCK_R019`，DOTA 结果不得进入科学裁决；禁止重新 seal 一个有利版本。

### Phase C：唯一一次标签揭示、复算和统计

只有远端 prelabel seal 已确认后，独立 label-attach 程序才可成为 r019 actual-input manifest 中第一个访问 DOTA GT 或旧 matched JSONL 的受控进程。先从封存 identity raw 新鲜匹配并附着 label/risk。旧 `DOTA_orcnn.jsonl` 与 `DOTA_rtmdet.jsonl` 只能在此后做 secondary lineage/parity，不得决定 inclusion、模型或 gate。这里的“first access”只约束 r019 受控执行；不得抹去项目历史上已经访问 DOTA 标签的事实。

先做 official detection parity：两个单元均为 5,297 images/55,804 GT；AP50 分别对 0.7061、0.7161，AP75 分别对 0.4517、0.4868，绝对差各 `<=0.002`。任何不通过均为 `FAIL_PROVENANCE_R019`，主端点无效；不能改 threshold 后再试。

主 bootstrap 必须：

- 在完整 DOTA mother universe 有放回抽取与 universe 等长的 mother multiset；零 eligible mother 保留在 universe；
- 每个 replicate 用封存的同一 mother multiplicity 同步作用于两 unit 及 linear/EQS/standalone；先分别重算 NRC/Delta，再做 unit 等权 aggregate；
- 恰好 10,000 个 finite replicate，replicate id 完整为 0…9999，不得丢坏 replicate 后补抽；
- 95% percentile CI；one-sided centered p 固定为 `(1 + count((Delta_b - Delta_point) >= Delta_point)) / 10001`；
- 两个 unit p 做 Holm-2；唯一 DOTA aggregate 使用 raw p、不做 Holm；
- tile/image bootstrap、旧 r014 actual selector、旧 matched-only 口径只能列为明确标注的 secondary sensitivity，不能替换主结果或进入 gate。

## 4. 唯一科学 gate 与失败语义

### 4.1 硬前提

Git/provenance、readme/asset hashes、prior-exposure search、production microtests、source/target 隔离、target-label-zero-access、remote prelabel seal、time lock、5,297-tile mother map、official AP parity、10,000 同步 replicates 和独立 validator 必须全部通过。任一失败分别归类 `FAIL_PROTOCOL_R019`、`FAIL_PROVENANCE_R019`、`FAIL_IMPLEMENTATION_R019`、`FAIL_PRIOR_OUTCOME_EXPOSURE_R019` 或 `FAIL_TIMELOCK_R019`；此时写 `DOTA_EQS=NOT_EVALUATED` 或 `INVALIDATED`，不能写科学性能 FAIL/INCONCLUSIVE。

### 4.2 `PASS_EXTERNAL_DOTA_EQS_RC_R019`

当且仅当以下全部成立：

1. `Delta_DOTA >= 0.02`、aggregate `CI_low > 0`、aggregate one-sided `p < 0.05`；
2. 两个 unit 2/2 各自 `Delta_u >= 0.02`、`CI_low > 0`、Holm-2 adjusted `p < 0.05`；
3. standalone guard 的 aggregate 与两个 unit 点估计均 `G >= 0`。

### 4.3 `FAIL_EXTERNAL_DOTA_EQS_RC_R019`

完成全部有效执行后，若 aggregate `Delta` 的 `CI_high <= 0`，或任一 unit 的 `Delta` `CI_high <= 0`，或 aggregate standalone guard `G` 的 `CI_high < 0`，则为明确科学失败。

### 4.4 `INCONCLUSIVE_EXTERNAL_DOTA_EQS_RC_R019`

完成全部有效执行但既不满足 PASS、也没有上述明确负证据时，一律为 INCONCLUSIVE；包括仅 1/2 unit 支持、CI 跨零、point `<0.02` 但仍不能排除正效应、Holm 未通过、或 standalone guard 只有不精确的点值失败。禁止把 INCONCLUSIVE 包装成 PASS。

完整揭示后跑出 PASS、FAIL 或 INCONCLUSIVE，均是 `experimental_execution=FULL_COMPLETION`，不是早停。只有第 1 节、Phase A 或 Phase B 的硬阻塞可记 `EARLY_STOP`；source LODO/功效结果没有早停权。见 target 标签后没有 efficacy early stop，必须算完两 unit、aggregate、guard 和 validator。

r019 后禁止自行改 gate、换 selector、换 cluster、换 unit、用 HRSC 救场、加入第三个 target、重抽 seed 或发起 r020 续命。PASS 只证明一个 DOTA 外部数据集上两个已见 family 的新 `EQS-RC-R019` 前瞻端点，能显著增强 TGRS/ISPRS JPRS/strong-journal 路线，但不自动等于 venue-ready，更不能追溯修复 r014/r015 的时间锁。严禁把 r015 actual-EQS 的 6/6 与 r019 合池、meta-analysis，或包装成同一算法的“发现—确认”；旧 Core 结果只能是开发证据。FAIL/INCONCLUSIVE 后停止服务器实验循环，转入如实改稿和定位收缩。

## 5. 独立 validator

生成端与 pre-final scientific/artifact validator 必须是两个独立入口。validator 不得 import 生成端的 gate 布尔值、汇总表或 PASS token；必须从封存 raw、GT、scores、mother map 和 draws 重算：

1. 两个完整 tile/mother universes、零 eligible mothers、eligible keys、matching、risk；
2. 每个 unit 与 aggregate 的全部 10,000 replicates、point/CI/p/Holm/guard/gate；
3. prelabel/final manifest 中每个输入输出的 bytes、SHA256、schema、row/key/replicate 完整性；
4. r019 target-label first-access 相对 remote prelabel commit 的时间顺序；
5. prelabel commit 的 Git DAG、精确 changed paths、remote `main` 与 `dis/B.md` blob equality；
6. 生成端结果逐字段 expected/actual/max_abs_error，数值 tolerance 固定 `atol=1e-12, rtol=0`。

validator 必须含真正的负例：改一个 draw multiplicity、删一个零 eligible mother、交换一个 unit、改一个 score、伪造一行 PASS、改一个 prelabel byte，均应非零退出。不得硬编码“当前结果应 PASS”，也不得把 production feature 的负结果当 validator 失败；审计是否正确与科学结果正负是两个维度。

final commit SHA/remote 状态不能由将被该 commit 收录的 validator 或 report 自证。全部 tracked 产物完成后先运行 pre-final validator，再显式 stage 并用只读命令检查 final staged path whitelist、parent=prelabel commit、B blob 不变和 `git diff --cached --check`。final commit/push 后另运行**不写仓库**的 external Git receipt，核验 final 单父 DAG、精确 changed paths、remote `main == final HEAD`、B blob parent/head equality、工作树/index clean。该 receipt 只进入服务器对用户的最终回复并由 C 拉取后独立复核；validator/report 不得声称已经在自身字节内验证未来 commit。

## 6. 资源、遥测与运行纪律

- 允许使用 4×A30 做固定 detector 三视图前向；两个 unit 顺序跑，避免资源争抢。CPU worker 数依据 readme/服务器实际安全上限，建议不超过 38。
- 不训练 detector，不请求新标注，不下载新数据，不修改全局环境。优先使用既有 `/home/rspip/anaconda3/envs/mr_dev1x/bin/python`，但必须以实际 config 可加载和 smoke 为准。
- 每个阶段记录命令、cwd、开始/结束时间、exit code、stdout/stderr 日志 SHA256。每 30 秒以内采样 r019 进程及全部子进程 aggregate CPU/RSS、GPU utilization/memory、真实 worker count；不得用全机 CPU、父进程 RSS 或硬编码 worker 冒充。
- BLAS/OpenMP 限制必须在 import numpy/pandas/sklearn 前设置并验证。记录 affinity 及每个子进程观察值。
- 禁止覆盖任何既有目录；临时文件只放 `runtime_root`，保留到 C 验收。不得用 `/dev/shm` 作为唯一证据位置。

## 7. 授权写路径与 Git 合约

除下列路径外，服务器一律只读：

- `p3_selector/deployable_proxy_r019/**`
- `outputs/persistent_artifacts/orientbench_r019/**`（Git ignored runtime，只登记，不提交大文件）
- `dis/server_reports/orientbench-c-r019-20260809.md`
- `claude_code_and_supervisor.md`（只允许 append r019 命令、阶段状态与结果）

严禁修改或暂存：`dis/B.md`、`dis/C.md`、`dis/sug.md`、`dis/review_state.json`、`dis/collaboration_protocol.md`、`dis/B_START_PROMPT.md`、任何主稿、r014–r018、旧报告/数据/模型、阈值和 split。

正常路径必须恰好两个服务器 commit：

1. prelabel seal commit：只含第 3 节 Phase B 授权路径；
2. final result commit：只含 `p3_selector/deployable_proxy_r019/results/**`、`p3_selector/deployable_proxy_r019/docs/**`、唯一 server report，以及对 `claude_code_and_supervisor.md` 的追加。

若在允许的标签前条件早停，允许单一 failure commit，内容仅为已实现 protocol/scripts/tests/prelabel diagnostics、唯一 report 和 supervisor log 追加；不得制造空 PASS 文件。每个 commit 均显式暂存精确文件，通过 HTTPS 正常 push，禁止 force、merge、rebase、reset、clean、覆盖式 checkout 或全量 `git add`。

evidence manifest 必须逐条列出 tracked outputs、actual read-only inputs、executed code、Git blob reads、runtime outputs。manifest 自身使用 `bytes=N/A_SELF_REFERENCE, sha256=N/A_SELF_REFERENCE`，最后一次写出且同一 validator 不回读自证；输出 hash read 与科学输入 read 必须分类型记录。

## 8. 必交产物与唯一服务器报告

`p3_selector/deployable_proxy_r019/` 至少提交：

- `protocol_r019.json`；
- production scripts 与 tests；
- preflight、prior-exposure、microtest、smoke、source universe/LODO/model、DOTA raw/feature/score inventories、mother map、bootstrap draw 与 prelabel seal；
- label attach、official parity、unit/dataset/guard results、10,000 replicate inventory、independent validator、resource telemetry、evidence manifest；
- 一份 protocol closure 文档，逐项映射本文件 0–8 节。

唯一仓库内回执必须是 `dis/server_reports/orientbench-c-r019-20260809.md`。它记录截至 final commit 前已可验证的执行事实；最终 commit/push 由不自引用的 external Git receipt 补齐。报告至少逐字段给出：

1. `experimental_execution = FULL_COMPLETION | EARLY_STOP | FAILED`；
2. `all_precommit_required_work_completed = true | false`；
   同时固定写 `git_publish_status=PENDING_EXTERNAL_RECEIPT` 与 `all_required_work_completed=DETERMINED_BY_EXTERNAL_RECEIPT`，禁止预填 PUSHED/true；
3. `early_stop = true | false`，若 true 列出发生阶段、第一失败条件和未执行项；
4. `scientific_verdict = PASS_EXTERNAL_DOTA_EQS_RC_R019 | FAIL_EXTERNAL_DOTA_EQS_RC_R019 | INCONCLUSIVE_EXTERNAL_DOTA_EQS_RC_R019 | DOTA_NOT_EVALUATED | INVALIDATED`；
5. 是否真的完成本文件每个 Phase，而不是“脚本退出 0”；
6. source LODO、盲态 power/MDE、两 unit 和 aggregate 的 eligible rows/mothers、linear/EQS/standalone NRC、Delta/G、CI、raw/adjusted p、每条 gate predicate；
7. 5,297 tile/mother counts/SHA、零 eligible mother、10,000 replicate completeness、AP parity；
8. r019 target-label first-access 时间、prelabel commit/remote SHA 与 changed paths；final 两字段必须原样写 `final_commit_sha=POST_COMMIT_EXTERNAL_RECEIPT`、`final_remote_main=POST_COMMIT_EXTERNAL_RECEIPT`，并列 expected final path whitelist 和 B blob expected equality；
9. 全部 commands、exit codes、日志、资源实际峰值/聚合方式；
10. 未做事项、协议偏离和是否触发 fail-closed。

报告中的 `experimental_execution=FULL_COMPLETION` 只有在全部科学/审计阶段和 pre-final validator 都完成时才能写；它本身不声称未来 final push 已完成。服务器最终回复首行只有在 external Git receipt 也全部通过后才可写 `执行完毕`。缺必做验证却声称完成，一律 `PROTOCOL_DRIFT_R019`。完整科学 FAIL/INCONCLUSIVE 不得写成 early stop；标签前硬失败也不得写成科学性能失败。

最终 Git push 后运行 external Git receipt。服务器与用户对话首行必须严格为 `执行完毕` 或 `未执行完毕`，第二行必须是 `dis/server_reports/orientbench-c-r019-20260809.md`；随后用一句话明确“是真的完成全部阶段，还是在哪个阶段早停/失败”，并给出 final commit、remote `main` SHA、精确 changed-path count、B blob equality 与 clean-worktree 结果。只有 `experimental_execution=FULL_COMPLETION` 且 external receipt 全过才可写 `执行完毕`；科学 FAIL/INCONCLUSIVE 仍可满足此条件。除此之外不要粘贴长日志。

## 9. 停止条件

提交并推送唯一报告后立即停止，等待 C 验收。不得自行改稿、宣布投稿、声称“顶刊已达成”、调用 CC、启动 r020 或继续搜索有利 gate。
