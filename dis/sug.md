# OrientBench r012：EQS 跨数据集方法门与独立确认（Luna-high，CC 后执行前冻结版）

- round: `orientbench-c-r012-20260807`
- protocol revision: `post_cc_pre_execution_v2`
- scientific snapshot: `c101429cebf3454b25bd62c285feffc2fea2e1c3`
- CC review head: `b959a09c021ade11241aecd970c90060dbbed84f`
- input manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_measure_diagnose_fix_r011.md`
- output manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r012.md`
- unique report: `dis/server_reports/orientbench-c-r012-20260807.md`
- runtime root: gitignored `outputs/persistent_artifacts/orientbench_r012/`

本版在任何 r012 服务器结果产生前，根据 B 的两阶段审查和 C 的独立复核冻结。上一版已逐字节归档为 `dis/sug/orientbench-c-r012-20260807-pre-cc.md`。本轮只回答一个会改变 venue 的问题：**selector 不使用 target D_cal/D_audit angle labels 时，按 OBB 几何容忍度归一化的真实 TTA 等变性信号，能否跨数据集改善方向风险排序？**

这不是“GT-free detector”或“无监督域泛化”：host detector 仍由各目标数据集训练集监督训练，TTA 也读取 target images；只有 selector 的拟合、预处理、模型选择与 target inference 不使用 target calibration/audit angle labels。

开始前只允许 `git pull --ff-only`。核对 origin、当前/默认/upstream 分支、完整 HEAD、工作树与 index；execution HEAD 必须同时包含 scientific snapshot 和 CC review head。禁止 merge/rebase/reset/clean/force。

## 1. 已冻结裁决与禁区

- r009/r010/r011 均为 `FAIL_PROTOCOL`。r011 的 paired AP 数字只可称 descriptive candidate；禁止修改或补做任何 r009/r010/r011 fixed-dose、parity、survival、risk、provenance 或 CI 资产。
- 现有 P3 nonlinear geometry 的 leave-dataset 是 `0/6`，五折显著反向；其跨数据集 deployable 路线已被杀死。target-GT-fitted M2/G2DP 仅是 diagnostic upper bound。
- 不改 frozen thresholds、`ar>=2.1`、D_cal/D_audit、split、NMS、class map；不复活 P2；不训练 detector；不下载数据、checkpoint 或第三方仓库。
- Core 主门只用固定 EQS。其它 selector 均为预注册 baseline/secondary，禁止看 target 结果后换主角、删特征、调超参、换 floor 或改 gate。
- r012 非 PASS 时永久关闭当前 CVPR/ICCV 方法线，不从旧 4/11、旧 STABLE-PASS 或任何新 TTA 小补丁续命。

## 2. Core、估计对象和固定角色

Core-6：`DIOR-R/22, DIOR-R/3, DIOR-R/61, FAIR1M-v1.0/24, SODA-A/23, SODA-A/4`。主域为 le90 长轴、degree、evaluation-only `matched identity TP at rIoU>=0.5 and GT_AR>=2.1`。target evaluation 只用 D_audit。

每个 outer target unit 的 source 排除整个 target dataset。fit 只用其它两个数据集的 D_cal-fit；source dataset 各总权 `1/2`，dataset 内 units 等权，unit 内 eligible rows 等权。linear、nonlinear 和 EQS 必须使用完全相同的 rows 与权重。禁止 source D_audit、target D_cal、target D_audit 参与 fit、归一化、特征选择、early stopping、模型选择或超参选择。

主风险：

`y = min(le90(pred,GT) / max(delta_0.75(GT_AR), 1 degree), 3)`。

`1 degree` floor 防止极端长宽比下理论容忍度趋近零时，把有限角度量化/标注分辨率无限放大；cap=3 限制重尾对回归的支配。主 gate 只用 floor=1、cap=3。floor `{0.5,2}` 仅作预注册描述性 sensitivity，不参与任何选择或 gate；逐 source/target unit 报告 floor-active 与 cap-active 数量/比例。

## 3. Phase A0：任何 smoke/GPU/fit 前的硬停止门

先完整读取只读 `pth_data/readme.md`。不可读即 `FAIL_PROVENANCE_R012`。

### 3.1 FAIR1M full-universe join

冻结 val20 必须为 `4362 images / 78644 GT`。把 r011 候选 `3896 unique-image count / 484332 predictions` 与 K1/m069 候选 `4362 images / 488194 predictions` 只视为待核身份，不得预断言 3862 个差异预测来自空图。

在任何 TTA 前输出并由 validator 重算：full split、GT、r011 raw/schema、K1/m069 raw 四个 sorted image-ID set 的 size、SHA-256、missing/extra count、最多20个 witness，以及逐 image prediction count join。每个 view registry 必须恰有4362行，包括 `n_pred=0` 的图像。用同一 official evaluator 直接报告 488194 与 484332 候选的 AP50/AP75 差；AP 对齐 `<=0.002` 不能替代 universe equality。任一 unexplained missing/extra image 或空图语义未闭合，立即 `FAIL_PROVENANCE_R012`，不得启动 FAIR TTA，也不得形成 Core PASS。

### 3.2 SODA mother-scene map

在任何 forward 前核对 frozen `22994` tiles 的存在性。每 tile 必须唯一映射一个 mother scene；输出 `tiles_total/mapped/unmapped/ambiguous/duplicate/mothers_total`、sorted `(tile,mother)` SHA、最多20个 witness。若历史408个断链仍存在，只能修复已有路径/映射，禁止换 split。formal gate 要求 `unmapped=ambiguous=duplicate=0`；否则 SODA 只可 sensitivity，Core PASS 不可能，提前封顶 `INCONCLUSIVE_PROVENANCE_R012`，停止 GPU。

### 3.3 Core lineage 与 runtime evaluator

对六个 unit 绑定 dataset/split、完整 image universe、D_cal-fit/D_cal-calib/D_audit、mother map、class map、原始/解析 config、checkpoint、framework/mmrotate/mmengine 版本、threshold/NMS、identity/hflip/vflip raw、精确命令、SHA-256/bytes/schema/count、can_recompute。

identity 必须用 official full evaluator 与权威 baseline 对齐，AP50/AP75 各绝对差 `<=0.002`。official evaluator 的模块版本、命令、输入 SHA、原始 JSON、完整日志 SHA 均进入 manifest；只保存 endpoint 字符串无效。Core PASS 要求 **6/6 provenance-clean**；5/6 只可完成诊断并封顶 INCONCLUSIVE，缺任一数据集即 provenance FAIL。

### 3.4 views 与 transform smoke

views 固定 `identity,hflip,vflip`。旧 `/dev/shm` 或报告不构成 lineage；只有 SHA/config/checkpoint/split/threshold/schema 与当前 Core 一致的持久化 raw 可复用。否则固定 checkpoint/config 做三 view forward，不训练、不调阈值、不改 NMS。

每 unit 先做50-image smoke：inverse-transform 后 synthetic round-trip oriented IoU `>=1-1e-7`、le90 `<=1e-7 degree`，核对 class/image identity 与 deterministic tie。失败可修实现后重试一次；再失败为 `FAIL_TRANSFORM_R012`。

## 4. Phase B：资源与调度

需要 inference 时默认 4×A30，一卡一 shard；小进程占卡仍先用4卡，只有连续两次带时间/显存日志的真实 OOM 才可减卡。SODA 两重单元分卡，unit 三 view 完成并验真后立即并行 CPU feature build。

CPU 密集阶段使用 aggregate quota=`3840%`；不支持时用38 workers+coordinator，设置 `OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=1`。matching、feature build、bootstrap、source fit 动态并行。每30秒记录 phase、wall time、CPU aggregate、RAM、每卡 GPU utilization/memory、worker数和异常；摘要给 mean/p10/p90、峰值内存、日志 SHA/bytes。常量状态字符串不是遥测。

## 5. Phase C：预处理、association、label attach 与 seal

### 5.1 prediction-side association

h/v prediction inverse-map 回 identity 坐标。同 image/class 内按 oriented IoU 降序做 deterministic one-to-one greedy association，接受 `IoU>=0.3`，tie=`(-IoU,-view_score,identity_index,view_index)`；禁止 GT association。未匹配 view 显式保留。

### 5.2 固定特征与预处理

- `score_clip=clip(score,1e-6,1-1e-6)`；`logit_score=clip(logit(score_clip),-13.815511,13.815511)`。
- `log_pred_AR=clip(log(max(pred_AR,1+1e-6)),0,4.605170)`。
- `0.5log_pred_area=clip(0.5*log(max(pred_area,1e-6)),-6.907755,9.210340)`。
- `support_fraction=matched_aux_views/2`；`missing_fraction=1-support_fraction`。
- doubled-angle axial circular dispersion 与 `u_axis=clip(median(le90(identity,matched_views))/max(delta_0.75(pred_AR),1 degree),0,3)`。
- `IoU_loss=clip(median(1-IoU_view),0,1)`；center shift/`sqrt(area)`、|log-width|/|log-height| dispersion 均 clip `[0,3]`；view score-logit dispersion clip `[0,10]`。
- association margin=`clip(top1_IoU-top2_IoU,0,1)`；只有一个候选时为1，无候选时为0。
- 无匹配 aux view 时固定 sentinel：`u_axis=3, IoU_loss=1, center=3, size_dispersion=3, score_dispersion=10, margin=0`。

monotonic directions：score/support 对风险非增；u_axis、IoU_loss、center、size/score dispersion、missing 对风险非减；AR/area/margin 不约束。feature generator 禁止 import GT loader。测试覆盖 h/v inverse、0/90、w/h swap、轴向双角、missing、duplicate/ambiguous、dense same-class、stable tie 和 round-trip。

### 5.3 label attach 的唯一估计对象

先 seal 全部 identity predictions/features。单独 label 脚本才可加载 GT：同 image/class，identity prediction 按 `(-score,original_index)` 排序，一对一 greedy rIoU `>=0.5`；eligible 仅 matched identity TP 且 evaluation-only `GT_AR>=2.1`。未匹配 identity rows 仍保留在 sealed feature registry，但不进入 orientation-risk estimand。禁止用 pred_AR 替代 GT_AR 定义 evaluation population。

### 5.4 不可逆 seal 顺序

在 target GT 第一次被加载前，依次 seal 并登记 SHA/bytes/schema：

1. protocol JSON 与全部执行代码；
2. 每个 outer fold 的 source rows、权重和五个 fitted source models；
3. 完整 target identity/raw registry 与 target feature table；
4. 五种 selector 对全部 target identity rows 的 scores。

label attach 后上述任一文件变化、重生或出现多个候选版本，立即 `FAIL_PROTOCOL_R012`；禁止挑版。

## 6. Phase D：冻结 selectors 与 source-only early stop

五个 selector：`detection_score`、`score+AR+size linear`、旧 `nonlinear_geometry`、固定公式 `standalone_equivariance`、proposed EQS。主比较仅为 EQS vs source-fitted size-linear；其它均 secondary，不能 candidate swapping。

`standalone_equivariance=-(u_axis + missing_fraction + IoU_loss)`。

EQS 固定 monotonic `HistGradientBoostingRegressor(max_iter=200, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1, min_samples_leaf=50, random_state=20260807)`，预测主风险。不得 target-driven search。

每个 outer target 在 attach target labels 前做两个 nested leave-one-source-dataset folds：在一个 source dataset 的 D_cal-fit 训练，在另一个 source dataset的 D_cal-calib 评价，然后反向。统计量同主比较 `Delta_NRC=NRC(linear)-NRC(EQS)`；1000次 paired image/mother bootstrap，seed=20260807，Holm-2。两折都 `CI upper<0` 才触发 `EARLY_STOP_SOURCE_R012`/FAIL，且禁止 attach target labels；混合结果只记录，不调模型。

## 7. Phase E：一次性 target D_audit 与双层 gate

bootstrap 从完整冻结 D_audit image universe 抽 cluster；SODA 主结果抽 mother scene，tile 仅 sensitivity。相同 replicate multiplicity 同时用于所有 selectors和同 dataset units，必须恰有1000个有效 replicate；禁止 pooled 跨 detector 排序。

unit 统计量：`Delta_NRC = NRC(size-linear)-NRC(EQS)`。support 当且仅当 point `>=0.02`、percentile 95% CI lower `>0`、centered one-sided Holm-6 p `<0.05`。0.02 是相对于 NRC random reference=1 的预注册最小实质收益，禁止以巨大样本下的 tiny significance 通过。

dataset aggregate 在每个 replicate 内先逐 unit 重算 Delta_NRC，再在该 dataset 内 units 等权平均；三个 dataset 分别给 point/CI/p/Holm-3，禁止合池不同 detector predictions。dataset support 同样要求 point `>=0.02`、CI lower `>0`、Holm-3 `<0.05`。

合法主状态：

- `PASS_DEPLOYABLE_EQS_R012`：6/6 provenance、transform/leakage/implementation 全过；unit support `>=4/6`，覆盖三数据集和至少两 detector families；FAIR1M/24 必须 support；dataset aggregate `3/3` support；SODA 使用 mother-scene 主 cluster；target selector 输入零 target D_cal/D_audit angle labels。
- `INCONCLUSIVE_DEPLOYABLE_EQS_R012`：实现有效且至少2个 unit support，但任一 PASS 条件未满足。该状态不是续命出口，仍永久关闭当前方法线。
- `FAIL_DEPLOYABLE_EQS_R012`：少于2/6，source early stop，或任一 dataset aggregate `CI upper<0`。
- `FAIL_PROTOCOL_R012 | FAIL_PROVENANCE_R012 | INCONCLUSIVE_PROVENANCE_R012 | FAIL_TRANSFORM_R012 | FAIL_IMPLEMENTATION_R012`：相应前置失败。

不得另造 PASS。即使主 PASS，也只称 top-venue route candidate，不称 TGRS/CVPR/ICCV-ready。

## 8. Phase F：仅在主 PASS 后做预指定独立确认

唯一候选固定为现有 `HRSC2016/LSKNet` 历史单元；只允许使用 `pth_data/readme.md` 中可完整绑定的既有 config/checkpoint/split，不得按结果换成其它单元。若 checkpoint/config/split/class/真实 detector identity 无法闭合，记录 `NOT_RUN_CONFIRMATION_PROVENANCE_R012`，不得用 DOTA 或其它单元替补。

不训练 detector。必要时4×A30做 identity/h/v fixed forward；用全部 Core 数据集 D_cal-fit 训练已冻结 EQS/linear（dataset各总权1/3），HRSC target feature/scores seal 后一次 attach 已冻结评测 split 的 GT。匹配、`ar>=2.1`、风险、1000次 image-cluster bootstrap和最小效应均沿用主协议。

- `PASS_INDEPENDENT_HRSC_R012`：Delta_NRC point `>=0.02` 且 CI lower `>0`，EQS不弱于 standalone equivariance，并且 provenance/leakage/implementation 全过。
- `FAIL_INDEPENDENT_HRSC_R012`：CI upper `<=0` 或收益只由 target-label/同数据集 source产生；杀死 general-transfer/顶会 claim。
- NOT_RUN/INCONCLUSIVE：主 PASS 仍只是待确认路线候选。

HRSC 单类和域差异必须作为限制；独立确认不回流 Core gate。

## 9. leakage 集合化与 validator

每 outer fold 输出并由 validator 从原始 row keys 重算 `source_Dcal_fit, source_Dcal_calib, source_Daudit, target_Dcal, target_Daudit, target_feature_prelabel` 的 row/image/mother set size、sorted-set SHA、每个非零交集最多20个 witness。必须检查 source/target dataset、source-fit/target labeled row/image/mother、source D_cal/source D_audit、GT字段/feature schema，以及 feature seal前后 SHA。

正式要求的交集必须精确为0；不能只写 PASS 字符串。任一 target label 字段进入 feature/model/selector score，或 seal 后变化，均为 `FAIL_PROTOCOL_R012`。

validator 必须只读并实际执行：transform/association tests、feature schema无GT、FAIR/SODA universe、source层级权重、identity official AP、seal顺序、source early-stop、1000 replicate→summary、Holm-6/Holm-3、minimum-effect、unit/dataset/HRSC gates、稿件数字、ledger text hash、manifest identities、授权集合与真实 Git diff。信任 CSV 的 PASS、常量 leakage 或只查存在无效。

## 10. 投稿稿与 novelty

无论结果都完整重写，不得在结论后追加状态段。删除内部 round/PASS、r011 confirmatory CI、旧 formal certification、无效表1 UCB、`fixed-dose raw incomplete`、宽泛4/11“跨域支持”。旧 P3 必须正面分层为 leave-dataset `0/6`、identifiable leave-detector `4/5`，并解释支持完全依赖 source 含同数据集兄弟单元。

PASS 才写 measure→diagnose→select；非 PASS 只写 measurement→diagnose，P3作为负迁移发现。FAIR 明示冻结本地 train_80/val_20=`18505/4362`，表4/5写 D_audit；DOTA NRC 使用统一 `ar>=2.1` 的 `0.7544/0.7113`；修正 PSC 作者和 DIOR-R/AOPG 出处。固定剂量最多作为 single-evaluator descriptive curves，D轨标 diagnostic upper bound。

novelty matrix 新增 Borji 2022 `arXiv:2206.10107`，并核对 ARS-DETR、SAOD、MCCL、OSKDet、WACV detection calibration、Optimal Correction Cost、Rethinking Boundary、Oriented Cell、AQE、SeqCRC、O2-DFINE、Fourier Angle Alignment。禁止声称首次 AP 扰动、首次 AP50 角度宽松、首次一般 detection calibration、首次 OBB 多标注者分析。可辩护增量仅是 OBB 角剂量/周期角误差、`le90+ar>=2.1` 可辨识域、几何归一化风险、image/scene 统计单位和经验证的跨数据集 selector（若 PASS）。

主稿不得出现 `PASS_*`、`FAIL_*`、round ID、JSTARS/TGRS-ready、authorized paths、validator术语或无证据的“闭环/权威/完整/可部署/因果/统一 knee”。claim ledger 绑定精确 heading/原句 SHA、CSV row keys、generator/input manifest/gate action。

## 11. manifest、Git 与精确写入集合（25）

manifest 最后生成，登记 scientific/execution/final HEAD、全部 input/output/runtime raw SHA/bytes/schema、config/checkpoint/framework、命令、原始 evaluator JSON/日志、telemetry、真实训练/inference/evaluator/bootstrap counts；self=`N/A_SELF_REFERENCE`。LF；`git diff --check`零输出。

只做一个最终中文 commit，不得中间 commit/push。`claude_code_and_supervisor.md` 恰好 append 一个 r012 section且提交前不再原位修改。只显式暂存以下路径：

1. `claude_code_and_supervisor.md`
2. `dis/server_reports/orientbench-c-r012-20260807.md`
3. `p3_selector/deployable_proxy_r012/protocol_r012.json`
4. `p3_selector/deployable_proxy_r012/runtime_registry_r012.json`
5. `p3_selector/deployable_proxy_r012/scripts/inventory_preflight_r012.py`
6. `p3_selector/deployable_proxy_r012/scripts/run_tta_forward_r012.py`
7. `p3_selector/deployable_proxy_r012/scripts/build_equivariance_features_r012.py`
8. `p3_selector/deployable_proxy_r012/scripts/evaluate_leave_dataset_r012.py`
9. `p3_selector/deployable_proxy_r012/scripts/validate_r012.py`
10. `p3_selector/deployable_proxy_r012/reports/provenance_r012.csv`
11. `p3_selector/deployable_proxy_r012/reports/tta_inventory_r012.csv`
12. `p3_selector/deployable_proxy_r012/reports/transform_sanity_r012.csv`
13. `p3_selector/deployable_proxy_r012/reports/feature_summary_r012.csv`
14. `p3_selector/deployable_proxy_r012/reports/source_cv_r012.csv`
15. `p3_selector/deployable_proxy_r012/reports/leave_dataset_results_r012.csv`
16. `p3_selector/deployable_proxy_r012/reports/bootstrap_replicates_r012.csv`
17. `p3_selector/deployable_proxy_r012/reports/gate_r012.json`
18. `p3_selector/deployable_proxy_r012/reports/resource_telemetry_r012.csv`
19. `p3_selector/deployable_proxy_r012/reports/evidence_manifest_r012.json`
20. `p3_selector/deployable_proxy_r012/docs/deployable_proxy_r012.md`
21. `p3_selector/deployable_proxy_r012/docs/deployable_proxy_r012.svg`
22. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r012.md`
23. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/equivariance_selector_r012.svg`
24. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/claim_ledger_r012.csv`
25. `top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/novelty_matrix_r012.csv`

禁止修改其它路径，尤其 `dis/B.md`、任何 r009/r010/r011资产、v080、旧 `measure_fix_v2`、历史 `top_journal_v3*` 文件、`.gitignore`、dataset/split/threshold/config/checkpoint。当前受保护 `dis/B.md` blob 必须保持 `3181a862137918f1dd41677893937c12b3c39c28`。HTTPS普通 push当前分支，不改 origin，不force；失败保留本地 commit并报告。

## 12. 唯一最终回复

首行只能是 `执行完毕` 或 `未执行完毕`。

第二行必须且只能是：`dis/server_reports/orientbench-c-r012-20260807.md`
