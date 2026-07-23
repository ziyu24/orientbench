# R1 —— 角度编码器机制干预矩阵（训练前预注册）

> **本文件是训练前预注册（pre-registration）。058 不启动训练。** 训练后不得据结果反改假设、指标定义、纳入规则或结局判定。任何偏离必须在执行命令中显式登记并说明理由。
> 空表：`reports/r1_angle_coder_matrix.csv`（30 runs，status=pending_preregistered）、`reports/r1_angle_coder_matrix_seed_variance.csv`。

## 1. 目的
判断“相位编码器内在置信度对朝向误差反序（NRC>1）”是 **角度编码机制层面可复现的现象**，还是**特定 checkpoint 的偶然现象**。这是当前论文中相位机制候选（case study）能否升级为机制证据的唯一合法路径。

## 2. 固定项（预注册，不得训练后更改）
- 骨干：统一单一骨干（如 ResNet-50 + FPN），各角度头共享。
- 数据集：DIOR-R 与 SODA-A（各自自跑 train 训练 / val 验证协议，不追公开 mAP）。
- 训练 schedule、数据增广、优化器、batch/lr、评测流水线：各角度头对齐同一设置；4 卡 global batch 线性对齐。
- 评测口径：冻结 masked ar≥1.6 主口径；D_cal/D_audit 规则不变（且不修改其成员）。
- 角度误差、NRC-AUC、AURC 定义冻结。

## 3. 对照组（5 类角度头）
1. PSC（相位编码）。
2. CSL（圆平滑标签）。
3. DCL（密集标签编码）。
4. 直接回归 / le90（direct regression）。
5. KLD / 分布感知角度头（distribution-aware）。

## 4. 设计规模
5 角度头 × 2 数据集 × 3 seeds = **30 runs**。

## 5. native uncertainty 定义（预注册，不得强构等价信号）
- PSC：phase_mod（相位模长）。
- CSL / DCL：角度分类熵 / 最大概率 / margin。
- KLD：预测角度方差 / 分布不确定度。
- 直接回归：**无原生不确定度 → 作为 negative control**；不得为其人为构造等价信号。

## 6. 每模型报告字段
AP50 / AP75；masked 角度误差；native uncertainty 定义；masked NRC；bootstrap 置信区间；跨 seed 方差。

## 7. failed training 规则
若训练崩溃或 mAP 明显异常，标 **failed_training**，**不得**硬纳入机制结论；不得用 mAP 失败模型支持机制。

## 8. 预注册结局（A/B/C，训练后据此判定）
- **A**：仅 PSC 在 3 seeds 稳定 NRC>1 且每 seed 的 CI 下界 >1 → 机制与相位编码特定相关。
- **B**：多种角度编码头均 NRC>1 → 机制与“角度编码/分类式角度头”这一类相关，非 PSC 独有。
- **C**：重训后 PSC 不复现 NRC>1 → 原观察为特定 checkpoint 现象，机制候选被否证。

## 9. 禁止语（预注册）
- 不得用单 seed 下结论。
- 不得用 mAP 失败模型支持机制。
- 不得把 synthetic 不复现当作反证。
- **不得写“PSC angle head proven broken”**；升级为机制证据仅在结局 A 或 B 成立且 CI 稳定时，方可写“机制在该矩阵内可复现”。

## 10. 后续执行表结构（占位，059+ 填充）
- `r1_angle_coder_matrix.csv`：每 run 一行（run_id / angle_head / dataset / seed / status / AP50 / AP75 / angle_error_masked / native_uncertainty_def / masked_NRC / NRC_CI_lo / NRC_CI_hi / failed_training / notes）。
- `r1_angle_coder_matrix_seed_variance.csv`：每 (head×dataset) 一行（mean_NRC / std_NRC / min / max / all_seed_CI_lower_gt1 / reproducible_reverse）。

**058 状态：预注册完成，未启动任何训练。启动 30 runs 需后续命令显式批准。**

## 11 执行状态（本轮）
- run manifest 已生成（`reports/r1_angle_coder_run_manifest.csv`，30 runs）。
- **训练启动被数据准备阻断（honest blocker）**：尝试启动 PSC/DIOR-R/seed0（4×A30 可用、mmrotate 环境可用、config 模板可用），但训练数据要求的 DOTA-txt 训练标注 `DIOR/annfiles_dotaformat/trainval/` **不存在**（DIOR 原生标注为 `annfiles/obb` 的 XML，DOTA 格式转换未保留）。故 0 run 完成、0 run 有效运行。
- 该阻断为**数据格式预处理缺口**，非有效训练崩溃 → 不标 failed_training、不进机制结论。
- 预注册（固定项/对照组/native uncertainty/结局 A/B/C/禁止语）保持不变。
- **phase_mod 仍为机制候选**；矩阵未完成前不升为机制证据。
- 下一步（059+）：先做 DIOR/SODA 的 XML→DOTA-txt 训练标注转换与校验，再按 4 卡队列启动；预计 30×12-epoch 为多日任务。

## 12 执行状态（060：数据解阻 + 四卡训练启动）
- **数据阻断已解除**：DIOR XML→DOTA-txt 转换完成并校验（见 `r1_dataset_preflight_060.md`）；SODA-A 原生 DOTA 格式可用。
- **真实 4 卡训练已启动并验证**：PSC/DIOR-R/seed0 以 torch.distributed.run --nproc_per_node=4 训练（4×A30，~1.2GB/卡，与他项目 D17 共存，Epoch1 正常迭代，loss 收敛中，ETA ~1.5h/run）。
- **队列守护**：`scripts/watch_r1_oom_retry.py`（4 卡强制、OOM 1200s 重试、EADDRINUSE 端口重试、只清理本项目残留、状态落盘 `reports/r1_angle_coder_queue_status_060.csv`）驱动 PSC-DIOR seed0→1→2。
- **配置就绪**：PSC-DIOR（`psc_dior_seed0.py`）、PSC-SODA（`psc_soda_seed0.py`，指向 SODA dota_format_tiled_ss，train-ready）。
- **待授权/待办**：CSL/DCL/KLD/direct-regression 的 config 派生（从同框架 csl/kld 配置 + rotated_retinanet le90 派生）；PSC-SODA 纳入队列需下一轮 watcher 重启。
- **完成/有效运行/failed/排队**：完成 0 / 有效运行 1（PSC-DIOR seed0）/ failed_training 0 / 排队 5+（含 config 待授权）。early rc=1 为端口冲突（EADDRINUSE，他项目占用 29511），已修为端口重试，**非 failed_training、非机制结论**。
- **预注册不变**；**phase_mod 仍机制候选**，矩阵未完成不升机制证据；无单 seed 结论。

## 13 执行状态（061–064：矩阵训练 + 评测 + 收口）

**训练（061–062）**：30 runs 全部终态。18 有效（PSC/CSL/DCL × DIOR-R/SODA-A × 3 seeds，共享冻结协议 12-epoch 训练健康完成）；12 failed_training —— direct_regression_le90 ×6（共享 lr=0.005+AMP 下 direct 5-param 回归 NaN 发散），KLD ×6（GDLoss_v1(kld) 的 linalg.inv 需 fp32，与共享 AMP/fp16 协议不兼容，<30s 崩溃）。均为**失败审计**，不支持机制结论；见 `r1_failed_training_audit_final_064.csv`。加入 epoch-1 健康门控（`watch_r1_oom_retry_062.py`），发散/崩溃早停，0 doomed run 烧满 12ep。

**评测（063）**：instrumented 角度头（`orientbench_ext/instrumented_heads.py`，过 NMS 对齐已验证）提取每检测原生不确定度（PSC phase_mod / CSL softmax margin / DCL bit margin），按 evaluator 同源 GT 旋转 IoU 匹配，masked ar≥1.6 复用冻结 `nrc_auc` + 图像级 bootstrap CI。18/18 完成，自建旋转 AP50 与 val_log max|diff|=0.0005。结果见 `reports/r1_valid_head_blocks_final_064.csv`。

**结局判定（对照 §8 A/B/C）**：**未达完整 A**。原因：(1) 5-head 矩阵未全（KLD/direct_regression failed）；(2) 已训 3 head **结论不一致**——PSC phase_mod 跨 2 数据集×3 seed 稳定反序（NRC>1，全 seed CI 下界>1），DCL native 反而强 informative（NRC 0.20–0.37），CSL ≈随机（0.89–1.00）。故当前最强可写为**受限 A-like、PSC-specific reproducible reverse ranking**，是 **preliminary mechanism evidence / mechanism candidate**，**非机制证明**。

**写法边界**：允许「PSC-specific reproducible reverse ranking across two datasets and three seeds」「DCL native confidence informative（反例）」；**禁止**「PSC angle head proven broken」「angle-coder confidence universally fails」「phase_mod mechanism proven」「full matrix complete」。exploratory rescue（fp32/lr）仅附录、`exploratory_rescue_not_preregistered`，不进主矩阵。phase_mod 仍机制候选。主线仍为 measurement protocol + finite-sample conformal orientation risk control；R1 为机制小节增强。
