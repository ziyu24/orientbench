---
schema_version: 1
project_id: OrientBench
plan_id: b-r052-cmr-functional-admission-20260828
dispatch_id: orientbench-b-r052-cmr-functional-admission-20260828
business_id: "052"
owner: B
status: READY
risk_class: L2
authorization_ref: "用户 2026-08-28：『批准，进行吧。』"
base_sha: e1b2c3456db9860436ed9ee81132247e5bbefe38
scientific_snapshot_sha: e1b2c3456db9860436ed9ee81132247e5bbefe38
server_report_path: dis/server_reports/orientbench-b-r052-cmr-functional-admission-20260828/SERVER_EXECUTION_REPORT.md
read_set:
  - AGENTS.md
  - dis/governance/**
  - dis/plans/B/b-r052-cmr-functional-admission-20260828/sug.md
  - dis/reviews/B/orientbench-r051-postexecution-review-20260827.md
  - dis/reviews/C/orientbench-b-r051-topjournal-joint-response-20260827.md
  - dis/reviews/B/orientbench-c-r051-topjournal-joint-adjudication-20260827.md
  - dis/dispatch_history/orientbench-b-r051-cmr-obb-cyclic-marginalized-roi-20260822.json
  - /home/rspip/cqc/pro/study/pth_data/readme.md
  - /home/rspip/cqc/pro/study/pth_data/**
  - /home/rspip/cqc/data/dataset/dota1.0/**
  - /home/rspip/cqc/pro/study/third_party/**
  - experiments/r051_cmr_obb/**
  - configs/r051_cmr_obb/**
  - audit_bundles/r051/**
write_set:
  - experiments/r052_cmr_admission/**
  - configs/r052_cmr_admission/**
  - outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/**
  - audit_bundles/r052/**
  - dis/server_reports/orientbench-b-r052-cmr-functional-admission-20260828/**
  - claude_code_and_supervisor.md
resource_scope:
  compute:
    gpu_count_max: 4
    gpu_hours_max: 384
    cpu_core_hours_max: 1200
  wall_time:
    seconds_max: 432000
  data:
    allowed_dataset_ids:
      - DOTA-v1.0-train-val
      - existing-valid-Oriented-RCNN-baseline-readonly
      - repository-tracked-evidence-readonly
    read_bytes_max: 3298534883328
    write_bytes_max: 549755813888
  write:
    allowed_paths:
      - experiments/r052_cmr_admission/
      - configs/r052_cmr_admission/
      - outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828/
      - audit_bundles/r052/
      - dis/server_reports/orientbench-b-r052-cmr-functional-admission-20260828/
      - claude_code_and_supervisor.md
    bytes_max: 549755813888
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
      - https://github.com/open-mmlab/
      - https://arxiv.org/
      - https://openaccess.thecvf.com/
      - https://ieeexplore.ieee.org/
      - https://pypi.org/
      - https://files.pythonhosted.org/
      - https://download.pytorch.org/
      - https://repo.anaconda.com/
      - https://conda.anaconda.org/
conflict_keys:
  - server-execution-slot
  - dis/sug.md
  - gpu-all-four-r052-cmr-admission
  - outputs/persistent_artifacts/orientbench_r052_cmr_admission_20260828
gates:
  - gate_id: G0_ASSET_PARITY_AND_DELTA_COLLISION
    rule: "先读 pth_data/readme.md，登记 valid DOTA-v1.0 Oriented R-CNN 的 config/log/checkpoint/split/backbone/schedule/global batch/lr/BN/mAP/framework/sha256，并复核 train->val identity parity。只做针对 joint proposal-conditioned cyclic visual marginalization 的一手文献 delta audit；若发现同一完整机制与 native risk 已存在，则 STOP_PRIOR_ART_COLLISION，不启动 GPU。"
  - gate_id: G1_FUNCTIONAL_ADMISSION
    rule: "只用 DOTA-v1.0 train 构造精确1024个确定性正 proposal，完成 DIRECT_DIST_V2、SINGLE_ROI_JOINT、CMR_FULL 的共享 joint-likelihood API、真实 autograd、候选观察、等变与反事实测试。任一已执行功能合取失败即 KILL_CMR_IMPLEMENTATION_PRINCIPLE，不进入 G2；环境或资产导致无法执行则 NOT_ADJUDICATED_ASSET_ENV。"
  - gate_id: G2_CONSUMED_DEVELOPMENT_KILL
    rule: "仅 G1 全过后，DOTA-v1.0 train->val，同一 frozen Oriented R-CNN、同初始化、同三 epoch、四卡、每 epoch full-val，运行 CONT、DIRECT_DIST_V2、SINGLE_ROI_JOINT、CMR_FULL。最终 epoch 一次揭示；CMR 必须分别打赢两个 joint controls 的全部 AP75、角误差、AUGRC、Risk@70 合取且 AP50/mAP 非劣，否则 KILL_CMR_PERMANENT。通过仅输出 PASS_CMR_ONE_ADMISSION，不得称 TGRS/JPRS ready。"
early_stop_conditions:
  - "G0 发现完整机制的一手 collision：正常早停，不启动 GPU。"
  - "G1 任一功能合取失败：永久停止 CMR，不进入 G2，不开第二次修复。"
  - "G2 任一主合取对任一 joint control 失败：永久停止 CMR，不补 seed、数据、epoch、K、loss、threshold 或较弱 control。"
  - "candidate/proposal/class UID 无法精确贯穿 train、decode、NMS、raw export：G1 fail。"
  - "读取任何未登记 endpoint、修改 frozen split/metric/threshold 或用 val 选配置：协议 kill。"
kill_conditions:
  - "读取 DOTA-v2.0 val、SODA-A official test、HRSC semantic fields/T_audit 或任何新数据集。"
  - "修改 third_party 源码，或覆盖/改写 r051 的历史代码和产物。"
  - "用 DOTA val 选择 K、loss weight、temperature、risk mapping、checkpoint、epoch、control 或 threshold。"
  - "将 r043-r051 或本轮失败结果写入目标论文正文、补充、附录或消融。"
  - "伪造训练、checkpoint、proposal provenance、指标、bootstrap、manifest、测试或完成状态。"
completion_mapping:
  pass_cmr_one_admission:
    execution_status: complete
    receipt_first_line: 执行完毕
  gated_scientific_early_stop_after_g0_g1_or_g2:
    execution_status: complete
    receipt_first_line: 执行完毕
  asset_environment_or_unexecuted_implementation_failure:
    execution_status: incomplete
    receipt_first_line: 未执行完毕
---

# 业务 052：CMR 单次功能准入与开发集淘汰门

## 1. 唯一目标

本业务不是重放或修补业务 051。051 已以 `INCOMPLETE / PROTOCOL_DRIFT / PENDING` 关闭；其 angle-only refiner、input-independent DIRECT_DIST 与负数字不裁决完整 CMR。

052 只回答一个问题：

> proposal-conditioned cyclic visual marginalization 是否真实进入 detector joint likelihood，并在一次冻结的 consumed-development 实验中同时改善高 IoU 定位、轴向角误差与 selective orientation risk？

这是一次性淘汰门。通过只取得后续完整顶刊方法验证资格；失败永久关闭 CMR。当前期刊级别在执行前后均不得自动上调。

## 2. 科学命题与拒稿边界

唯一潜在 headline：

> Proposal-conditioned cyclic visual marginalization produces a detector-native orientation posterior that jointly improves high-IoU localization and selective orientation reliability without target-domain angle labels.

最强拒稿意见必须保留：CMR 可能只是 rotated-RoI、有限群 pooling、mixture-density inference 与 uncertainty score 的工程合取。没有完全同构先例只表示没有逐字 collision，不等于顶刊创新。只有 joint detector likelihood、native risk、跨域正证据的完整合取才可能越过该边界。

## 3. G0：资产、parity 与最小文献增量核查

1. 必须先读取 `/home/rspip/cqc/pro/study/pth_data/readme.md`；不可读则报告 `NOT_ADJUDICATED_ASSET_ENV` 并停止。
2. 固定 DOTA-v1.0 `train->val`，使用登记 valid 的 Oriented R-CNN baseline。记录 dataset/split/backbone/schedule/global batch/lr/BN/framework/config/log/checkpoint/mAP/checkpoint SHA-256。
3. 复跑 identity val；与登记 mAP 的差异超过既有 parity 容忍且无法由口径解释时停止，禁止以重训 host 修复。
4. 复用 r051 G0 audit，只增量核查 `decoded proposal + K candidate visual observations + shared posterior + joint class/full-box/orientation mixture likelihood + no-GT risk` 的完整合取。普通相邻组件不构成 collision；发现同构一手实现才早停。

G0 只服务创新边界和合法资产，不得扩写成论文贡献或长期审计任务。

## 4. G1：功能准入

### 4.1 确定性样本

- 数据严格限于 DOTA-v1.0 train；禁止读取 val。
- 用固定 baseline 生成 decoded proposals，并在生成时赋予 immutable proposal UID。
- positive 定义冻结为：预测类别与匹配 GT 类别一致、rotated IoU `>=0.5`。每张图按 proposal UID 升序最多取四个。
- image ID 按 `SHA256(UTF8(image_id))`、再按原 image ID 打破哈希并列的顺序遍历，持续收集至**恰好 1,024** 个 positive proposals。若全 train 仍不足 1,024，输出 `NOT_ADJUDICATED_ASSET_ENV`，不得改 N、IoU 或每图上限。
- 保存 image/proposal/GT match manifest、生成命令与 SHA-256。

### 4.2 共享 joint-likelihood API

三个新增 arms 必须调用同一个 integration API。每个 latent candidate `k` 至少输出：

- posterior logit `a_k` 与 `q_k=softmax(a)_k`；
- categorical class log-probability；
- `cx,cy,logw,logh` 四个非角度条件位置分布参数；
- axial angle conditional；
- immutable proposal/class/candidate UID。

训练 loss 必须显式包含：

`L_joint = -logsumexp_k(log q_k + log p_class,k + log p_box4,k + log p_angle,k)`。

分布族直接冻结：class 使用 categorical log-softmax；`cx,cy,logw,logh` 使用 factorized Laplace，`b=softplus(raw_b)+1e-3` 且 `log(b)` 裁剪到 `[-5,3]`；axial angle 使用 `pi`-periodic von-Mises，`kappa=clamp(softplus(raw_kappa)+1e-3,max=100)` 并稳定计算正规化常数。四维 box log-density 先取维度均值，再与 class、angle log-density 等权相加。三个 arms 完全相同，任何 val 读取前写入 config，禁止替换分布族、裁剪或 scaling。

推断必须真实执行 posterior marginalization：class score 为候选 class likelihood 的加权和；`cx,cy,logw,logh` 为同一 posterior responsibility 下的边缘估计；theta 用 axial circular mean；native risk 由同一 posterior 的冻结 tail expectation 产生。禁止只覆盖 theta 或用 host score 冒充 marginal class likelihood。

### 4.3 三个 arm 的唯一区别

- `DIRECT_DIST_V2`：从 host 的 single-RoI proposal feature 经两层非线性 MLP 直接输出 centered K=12 logits 与 joint conditionals；禁止 `linear(encoded + phase_k)`。
- `SINGLE_ROI_JOINT`：只执行 proposal 当前角度的一次完整 7x7 Rotated RoIAlign；用带真实 feature×phase interaction 的共享 scorer 形成 K 个 latent conditionals，不改变 observation operator。
- `CMR_FULL`：同一 decoded proposal 的 K=12 个 `pi`-periodic 候选角分别执行完整 7x7 Rotated RoIAlign，shared encoder/scorer 形成 posterior 与 joint conditionals。

三者额外参数量差必须 `<=5%`，共用 host、integration API、loss、risk 和 NMS/provenance 路径。可以用宽度调整做一次参数匹配，但必须在任何 val 读取前冻结。

### 4.4 必须通过的真实测试

1. **DIRECT_DIST instance conditioning**：1,024 proposals 中至少 95% 满足至少一个 `k` 的 `||d(log q_k-log q_0)/d feature||_F > 1e-6`；feature permutation 后 posterior median L1 change `>0.05`。
2. **candidate observation**：CMR 至少 95% proposals 的 across-k candidate-feature variance `>1e-6`。
3. **索引等变**：在同一 image/proposal 上把 candidate angle/observation 顺序精确 cyclic roll 一格，q 必须对应 roll 一格，median aligned L1 error `<=0.05`。
4. **几何等变**：图像和 proposal 同步旋转一个 ring step 时，posterior 在 proposal-relative candidate index 上应保持不变，median aligned L1 error `<=0.05`；最终 global theta 应同步旋转一格。不得错误要求 relative q 自行平移。
5. **joint consumption**：至少 95% proposals 中，最终 class likelihood、至少一个非 theta box posterior 分量和 theta 对 candidate evidence 的 autograd norm 各 `>1e-6`；实际 detector loss graph 中必须出现 joint `logsumexp`。
6. **detach counterfactual**：`detach(q)` 的前向 loss 必须保持数值相同；正常路径 evidence-head gradient norm `>1e-6`，detach 后该路径 gradient norm `<=1e-12`。若声称 detach 改变前向 loss，测试判错。
7. **shuffle counterfactual**：跨 proposal shuffle q 后，total loss、final class likelihood 与至少一个非 theta box posterior 的绝对变化均 `>1e-6` 于至少 95% proposals；仅 theta 改变判失败。
8. **provenance/mutation**：proposal/class/candidate UID 从生成、loss、decode 到 NMS/raw export 一一对应；删除、交换、重复、篡改 flat NMS mapping 的 mutation 均须非零拒绝。
9. **finite/gradient**：全部关键 loss、posterior、risk、梯度有限；候选 scorer 与四个非角度分量均收到非零梯度。

先做最小四卡 smoke，再在固定 1,024 proposal 集上执行正式 G1。若工程路径、显存或依赖异常，可在新目录内自主修复并重跑；但一旦提交正式 G1 token，任何功能合取失败即 `KILL_CMR_IMPLEMENTATION_PRINCIPLE`，不准第二轮修复或修改阈值。

## 5. G2：唯一 consumed-development 经验淘汰门

仅 G1 全过后执行。

### 5.1 协议

- dataset：DOTA-v1.0 train->val；不得触碰其它 dataset/endpoint。
- host：同一 valid Oriented R-CNN，原 host 参数冻结；新增 joint modules 训练三 epochs。
- arms：`CONT`、`DIRECT_DIST_V2`、`SINGLE_ROI_JOINT`、`CMR_FULL`。
- CONT 只作冻结 host reference；三个新增 arms 同初始化、同 global batch/lr/augmentation、同 joint loss、同训练预算。
- 严格四卡。因外部占用 OOM 时先顺序运行各 arm；仍 OOM 可降低 per-GPU batch，并用 gradient accumulation 保持冻结 global batch。不得改为少于四卡。
- 每 epoch full-val，但 final epoch 才能用于唯一裁决；禁止 best-checkpoint picking。
- K=12、7x7、loss scaling、temperature、risk definition/mapping、NMS、epoch 和 controls 在首次 val 前冻结。禁止用 val 调参。

### 5.2 指标与统计

- mAP、AP50、AP75；
- matched TP 中 `GT_AR>=2.1` 的 axial mean angle error；
- 同一最终 detections 的 AUGRC 与 Risk@70；
- 完整 mother-image universe；B=10,000 同步 mother-image bootstrap、95% percentile CI；
- bootstrap/匹配/风险计算使用至少 40 CPU cores，完整记录命令与日志；
- CMR 必须**分别**与 DIRECT_DIST_V2、SINGLE_ROI_JOINT 比较，禁止事后选择较弱 control。

### 5.3 唯一 PASS 合取

`PASS_CMR_ONE_ADMISSION` 当且仅当 CMR 相对两个 controls 分别全部满足：

- `delta AP50 >= -0.003`；
- `delta mAP >= -0.003`；
- `delta AP75 >= +0.005` 且 AP75 mother-bootstrap `CI_low > 0`；
- `GT_AR>=2.1` mean angle error relative reduction `>=5%`；
- AUGRC relative reduction `>=10%` 且 improvement `CI_low > 0`；
- Risk@70 relative reduction `>=10%` 且 improvement `CI_low > 0`；
- UID/provenance、finite、mutation、资源和 split 全部无漂移。

任一项失败即 `KILL_CMR_PERMANENT`。禁止补 seed、换 dataset、加 epoch、改 K/loss/threshold/risk、删 control 或把负数字写入目标稿件。

## 6. 通过后的含义

G2 通过只证明值得新建完整方法计划，不改变当前 venue。后续顶刊下限另行预注册：

- TGRS candidate：至少 3 datasets、2 detector families、3 seeds、2 zero-target-GT transfers，AP75/角误差/AUGRC/Risk@70 稳定同向且 AP50/mAP 非劣；
- ISPRS JPRS candidate：再给出可检验的遥感几何规律；若 AP75 仅接近最低门槛，必须增加 source-disjoint 独立决策收益。

本业务无权打开新 endpoint，也无权自动进入上述扩展。

## 7. 工程自主权与产物

科学合同、数据边界、controls、指标和门槛不可改；其余工程事项由服务器自主处理，无需因路径、环境、worker、AMP、activation checkpointing、串行 arm、日志格式或小型兼容修复反复请示。第三方源码只读，所有适配写入 r052 新目录。

必须持久化：完整 config/commands/env/log、checkpoint hash、1,024 proposal manifest、raw predictions、full q/joint outputs/native risk、exact UID provenance、matched rows、bootstrap samples/summary、参数量/显存/耗时、G0/G1/G2 tokens、manifest/SHA-256、schema、can_recompute 和真实 mutation outputs。

服务器报告只汇报决策结果、异常和精确产物路径。回执严格两行：第一行 `执行完毕` 或 `未执行完毕`；第二行唯一报告路径。
