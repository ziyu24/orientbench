# OrientBench r012：target-GT-free 跨数据集选择器顶刊/顶会资格终判（Luna-high）

- round: `orientbench-c-r012-20260807`
- scientific snapshot: `c101429cebf3454b25bd62c285feffc2fea2e1c3`
- input manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_measure_diagnose_fix_r011.md`
- output manuscript: `top_journal_v3_reaudit_055/paper_A_orientation_protocol/docs/orientation_reliability_submission_r012.md`
- unique report: `dis/server_reports/orientbench-c-r012-20260807.md`
- runtime root: gitignored `outputs/persistent_artifacts/orientbench_r012/`

本轮只做一个能改变 venue 的问题：**不使用目标域 GT angle-error 标定时，理论归一化的真实 TTA 等变性信号能否跨数据集改善朝向可靠性排序？** 这是 source-supervised、target-GT-free 的新 P3 候选，不是 r012 fixed-dose 补丁。一次给足任务；先想清楚、再并行执行，不在小事上来回等待。

开始前 `git pull --ff-only`，核对 origin、当前/upstream 分支、完整 HEAD、默认分支、工作树与 index。execution HEAD 必须包含 scientific snapshot；不满足即停止。禁止 merge/rebase/reset/clean/force。

## 1. 冻结裁决与禁区

正式状态：

- r011=`FAIL_PROTOCOL_R011`，并触发 evaluator/implementation 子失败；仓库中的 `PASS_STRONG_JSTARS_EVIDENCE_R011` 不可继承。
- r011 的 paired AP 点估计/replicate 仅可称 descriptive candidate；不得修改任何 r009/r010/r011 资产，不得再补 variant parity、survival、risk、provenance 或 fixed-dose CI。
- 现有 P3 nonlinear geometry 在 r011 leave-dataset 为 `0/6`；此候选的 deployable 路线已被杀死。target-GT-fitted M2/G2DP 只保留 diagnostic upper bound。
- 不改 frozen thresholds、`ar>=2.1`、D_cal/D_audit、split、NMS、dataset、class map；不恢复 P2 主线；不训练 detector；不下载数据、checkpoint 或第三方仓库。

若本轮 target-GT-free 候选失败，正式关闭 CVPR/ICCV 方法线，直接交付 measurement/analysis 稿；禁止再从旧 4/11、旧 STABLE-PASS 或换 gate 调参。

## 2. Core、主风险和角色

Core-6 固定为：`DIOR-R/22, DIOR-R/3, DIOR-R/61, FAIR1M-v1.0/24, SODA-A/23, SODA-A/4`。主域 `ar>=2.1`，le90 长轴、角度单位 degree；target evaluation 只用 D_audit。source training 只用除 target dataset 外各 source unit 的 D_cal-fit，按 unit 等权，禁止 source D_audit、target GT、target D_cal 参与 fit、特征选择、归一化、early stopping、模型选择或超参数选择。

主风险为几何归一化角度风险：

`y = min(le90(pred,GT) / max(delta_0.75(GT_AR), 1 degree), 3)`。

同时报告连续 le90、severe event、NRC、AURC、Risk@50/70/90。`NRC<1` 只写 informative/better-than-random ranking，不称 calibrated probability。

完整 target feature table 在加载 target GT 前必须落盘、哈希并封存；随后单独脚本只按 frozen identity attach D_audit labels。target GT 字段不得进入 feature schema 或任何 selector 输入。

## 3. Phase A：真实 lineage 与 TTA inventory

先读只读 `pth_data/readme.md`；不可读则 `FAIL_PROVENANCE_R012` 并停止 inference。对每个 Core unit 绑定：dataset/split、image universe、D_cal/D_audit/mother-scene map、class map、原始 config、resolved config、checkpoint、framework/mmrotate/mmengine 版本、threshold/NMS、identity raw、三种 view raw、精确命令、SHA-256/bytes/schema/count、can_recompute。

views 固定为 `identity,hflip,vflip`。优先复用服务器上仍存在且可由 SHA/配置/identity AP 对齐的真实持久化 TTA raw；旧报告或 `/dev/shm` 路径本身不构成可复用证据。复用必须证明与当前 Core/m069 lineage、checkpoint、split、threshold 和 post-NMS schema相同。

缺失或身份不闭合时才运行 detector forward：同一 checkpoint/config，三 view 各一次，raw 持久化到 runtime root；禁止训练、调阈值、改 NMS。每 unit 先做 50-image smoke，验证 inverse-transform 后 synthetic round-trip oriented IoU `>=1-1e-7`、angle le90 误差 `<=1e-7 degree`、class/image identity 和 deterministic tie。smoke 失败修实现后只重试一次；再失败该 unit `FAIL_TRANSFORM_R012`。

identity view 必须用 official full evaluator 与当前权威 baseline 对齐：AP50/AP75 每项绝对差 `<=0.002`。不能对齐则该 unit provenance FAIL，不得用旧 matched table填空。至少五个 unit 且三个数据集均 provenance-clean 才可进入正式 gate；否则 `FAIL_PROVENANCE_R012`。

## 4. Phase B：4×A30 forward 与 CPU 调度

需要 inference 时默认同时使用 4×A30，一卡一 shard；即使有小程序占用也先运行，只有真实 OOM 才缩小 batch/chunk。连续两次带时间/显存日志的 OOM 才允许减少 GPU 数。SODA 两重单元放不同 GPU，其余动态队列；不等待所有 GPU 结束，某 unit 三 view 完成并验真后立即启动其 CPU feature build。

CPU 总量 48 核。CPU 密集阶段使用 aggregate quota=`3840%`；若系统不支持，用 38 workers + coordinator，并依据 30 秒 aggregate utilization sleep-throttle，持续目标 80% 且不长期越过 80%。设置 `OMP_NUM_THREADS=MKL_NUM_THREADS=OPENBLAS_NUM_THREADS=1`。matching、feature build、bootstrap 和 source fit 应动态并行，禁止单核串行大表。

每 30 秒记录 wall time、phase、CPU aggregate、RAM、每卡 GPU utilization/memory、worker 数和异常；Git 摘要必须给 mean/p10/p90、峰值内存、日志 SHA/bytes。常量“COMPLETE/38 workers/4 GPU”不是遥测。

## 5. Phase C：冻结等变性特征与 selector

评估 identity post-NMS predictions 的可靠性。每个 hflip/vflip prediction inverse-map 回 identity 坐标；同 image、同 class 内按 oriented IoU 降序做 deterministic one-to-one greedy association，接受阈值固定 `IoU>=0.3`，tie=`(-IoU,-score,identity_index,view_index)`。禁止用 GT association。未匹配 view 显式保留，不能静默丢弃。

每个 identity prediction 的 prediction-side features 固定为：

- `logit_score, log_pred_AR, 0.5log_pred_area`；
- view support fraction 与 missing fraction；
- doubled-angle axial circular dispersion；
- `u_axis = median(le90(theta_identity,theta_view)) / max(delta_0.75(pred_AR),1 degree)`；
- matched oriented-IoU loss、中心位移/`sqrt(area)`、log-width/log-height dispersion、view score logit dispersion；
- top1-top2 association-IoU margin。

所有 feature clipping/缺失编码在 protocol 中预先固定。feature 生成器不得 import GT loader。单元测试至少覆盖 h/v inverse、0/90 边界、w/h swap、轴向双角、missing view、duplicate/ambiguous association、dense same-class、stable tie 和 round-trip。

比较以下冻结 selectors：

1. `detection_score`；
2. `score+AR+size linear`：同一 source D_cal-fit；
3. r011 同定义的 `nonlinear_geometry`：同一 source D_cal-fit，仅作已失败基线；
4. `standalone_equivariance`：`-(u_axis + (1-support_fraction) + median(1-IoU_view))`，无训练、完全 GT-free；
5. **proposed EQS**：source-supervised、target-GT-free 的 monotonic `HistGradientBoostingRegressor`，预测上式主风险。固定 `max_iter=200, learning_rate=0.05, max_leaf_nodes=15, l2_regularization=1, min_samples_leaf=50, random_state=20260807`；score/support 对风险单调非增，u_axis/IoU-loss/center/size/score-dispersion/missing 对风险单调非减，AR/size不约束。source feature 标准化只用 source D_cal，source units 等总权。

禁止 target-driven hyperparameter search、candidate swapping、feature deletion或 family-specific target rule。每个 outer target fold 内只在其可用 source D_cal 上做 nested leave-one-source-unit sanity；若 proposed 在至少两个 source-unit folds 显著弱于 size-linear，触发 `EARLY_STOP_SOURCE_R012`，不得 attach 该 target fold 的 GT。

## 6. Phase D：一次性 leave-dataset 评估

每个 target unit 的训练源排除整个 target dataset；fit 只读 source D_cal，target D_audit 只在 feature SHA 封存后一次性 attach labels 和评价。输出精确 source/target row keys、image/mother-scene overlap、feature/model SHA、fit count、audit count、TTA match/support、推理成本和每个 selector 的 NRC/AURC/Risk。

主统计量为：

`Delta_NRC = NRC(score+AR+size linear) - NRC(proposed EQS)`，正值表示 proposed 更好。

固定 1000 次 paired cluster bootstrap，seed=`20260807`，同一 replicate 同时重算所有 selectors。DIOR/FAIR 以 full image；SODA 以 mother-scene 为主、tile 为 sensitivity。若 mother-scene 无法无歧义恢复，SODA 只能降为 sensitivity且不能单独满足 dataset coverage。输出 full-sample point、bootstrap mean/bias、percentile 95% CI、centered one-sided p 和六项 Holm p。support 当且仅当 point>0、CI lower>0、Holm p<0.05。

## 7. 冻结 gate 与早停

合法状态只允许：

- `PASS_DEPLOYABLE_EQS_R012`：provenance/transform/leakage/implementation 全过；至少 4/6 target units support，支持覆盖 DIOR/FAIR/SODA 和至少两 detector families；任一 dataset 不得全部 point<=0；SODA 主结论有 mother-scene cluster；proposed target 输入零 GT。
- `INCONCLUSIVE_DEPLOYABLE_EQS_R012`：实现有效，support 为 2–3/6，或达到 4/6 但缺数据集/family/mother-scene覆盖。
- `FAIL_DEPLOYABLE_EQS_R012`：support 少于 2/6，或任一数据集所有可用 unit 均显著反向，或 source early-stop 被触发。
- `FAIL_PROTOCOL_R012 | FAIL_PROVENANCE_R012 | FAIL_TRANSFORM_R012 | FAIL_IMPLEMENTATION_R012`：相应前置失败。

不得另造 PASS。若 PASS，只能称“top-venue route candidate”，还需独立确认，不得称 CVPR/ICCV/TGRS-ready。若 INCONCLUSIVE/FAIL，永久关闭当前 P3 顶会方法线；不调 gate、不新开 TTA 小补丁，venue 收缩为 strong-JSTARS/TGRS-conditional measurement/analysis。

## 8. 投稿稿与 2026 novelty

无论 gate 结果都完整重写 output manuscript，禁止在结论后追加状态段。删除内部 round/PASS 字符串、r011 confirmatory CI headline、旧 formal certification 当前方法/负结果、`fixed-dose raw incomplete` 矛盾和 4/11 宽泛“跨域支持”。明确报告旧 P3 leave-dataset `0/6`；fixed-dose 只保留独立可辩护的描述性点曲线与限定。

若 R12 PASS：按 measure→diagnose→select 重写摘要、贡献、方法、实验、主表/图、消融、成本、讨论、限制、结论；proposed 仍写 source-supervised target-GT-free，不写 universal/deployable guarantee。若 R12 非 PASS：以 measurement/analysis 为唯一主线，P3 作为诚实负结果/未来方向，产出可送投稿级语言的 strong-JSTARS 稿。

novelty matrix 至少核对并给官方链接/DOI与核查日期：ARS-DETR TGRS 2024 (`10.1109/TGRS.2024.3364713`)、SAOD CVPR 2023、MCCL CVPR 2023、OSKDet CVPR 2022、detection calibration WACV 2024、Optimal Correction Cost CVPR 2022、Rethinking Boundary Discontinuity CVPR 2024、Oriented Cell Dataset WACV 2025、O2-DFINE arXiv 2026、Fourier Angle Alignment CVPR 2026。禁止把“AP50 对角度宽松”“一般 detection calibration”“OBB 多标注者分析”写成首创。

claim ledger 只收实质稿件 claims；绑定具体 heading/原句 SHA、精确 CSV row keys、generator、input manifest、gate/action。至少覆盖摘要、贡献、主风险、P1 描述性边界、旧 P3 0/6、R12、人工标注、统计单位、资源成本、限制和所有 headline 数字。

## 9. validator、manifest 与 Git

validator 必须只读并实际执行：transform synthetic、association tie/missing、feature schema无GT、target feature seal、source/target dataset与image/mother overlap、identity official AP、bootstrap optimized-vs-bruteforce、replicate→summary、Holm/support、每个 gate 布尔项、稿件数值、ledger text hash、manifest identities、授权集合与真实 Git diff。信任 CSV 的 PASS、常量 leakage 字符串或只查存在无效。运行前后工作树/index/file identities不得改变。

manifest 最后生成，登记 scientific/execution/final HEAD、全部 input/output/runtime raw SHA-256/bytes/schema、config/checkpoint/framework、命令、telemetry log、真实训练/inference/evaluator/bootstrap counts；self identity=`N/A_SELF_REFERENCE`。所有小文本/CSV 用 LF；`git diff --check` 必须 0 输出。

只做一个最终中文 commit，不得中间提交/push；`claude_code_and_supervisor.md` 恰好 append 一个 r012 section且提交前不再原位修改。显式暂存下列 25 路径，禁止 `git add -A`/`.`；验证 `dis/B.md` blob 仍为 `1a6093cf3b1f396dbee30803ae616643353ea0aa`。HTTPS普通 push 当前分支，不改 origin，禁止 force；失败保留本地 commit并如实报告。

## 10. 精确 Git 写入集合（25）

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

禁止修改其它路径，尤其 `dis/B.md`、任何 r009/r010/r011资产、v080、旧 `measure_fix_v2`、`top_journal_v3*` 历史文件、`.gitignore`、dataset、split、threshold、config、checkpoint。未运行的输出仍按上列路径写 schema 与标准 NOT_RUN reason，保证唯一报告和可审计 changed set。

## 11. 唯一最终回复

首行只能是 `执行完毕` 或 `未执行完毕`。

第二行必须且只能是：`dis/server_reports/orientbench-c-r012-20260807.md`
