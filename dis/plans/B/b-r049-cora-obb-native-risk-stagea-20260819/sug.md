---
schema_version: 2
business_instruction: "049"
plan_id: b-r049-cora-obb-native-risk-stagea-20260819
dispatch_id: orientbench-b-r049-cora-obb-native-risk-stagea-20260819
initiator: B
activation_authorization:
  mode: owner_only
  delegate: null
  reference: null
closure_authorization:
  mode: owner_only
  delegate: null
  reference: null
base_sha: 2110269b12613d1d38ba3f2b4a2d83d548225556
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-19：『后续GPU等的不需要授权，都在空着呢，抓紧推进。』"
scientific_snapshot:
  primary: 2110269b12613d1d38ba3f2b4a2d83d548225556
  prior_method_state: "B 已采纳 r048 REJECT_P2C_LIFT_DEVELOPMENT；Q-SetOD、OER/OER-D、SAUR、AHC、P2C 与 HRSC crop-head/selector rescue 均停止"
  joint_state_note: "r048 B verdict 已追踪，B/C 联合 scientific state 仍 PENDING，不能伪称双边 KILLED"
  venue_state: "当前仅 strong JSTARS / Remote Sensing，低于 TGRS-or-better 合法目标"
  target_route: "CORA-OBB detector-native counterfactual orientation-risk alignment"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r049-cora-obb-native-risk-stagea-20260819/SERVER_EXECUTION_REPORT.md
read_set:
  - AGENTS.md
  - dis/governance/roles/SERVER.md
  - dis/coordination.json
  - dis/plans/B/b-r049-cora-obb-native-risk-stagea-20260819/sug.md
  - /home/rspip/cqc/pro/study/pth_data/readme.md
  - /home/rspip/cqc/pro/study/pth_data/**
  - top_journal_v3_reaudit_055/saur_stagea_r043_20260818/**
  - top_journal_v3_reaudit_055/configs/r1_angle_coder/**
  - top_journal_v3_reaudit_055/reports/r1_angle_coder_matrix.csv
  - measure_fix_v2/track_a_pkg/**
  - configs/**
  - orientbench/**
  - scripts/**
  - /home/rspip/cqc/data/dataset/**
write_set:
  - experiments/r049_cora_obb/**
  - configs/r049_cora_obb/**
  - outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/**
  - audit_bundles/r049/**
  - docs/paper_jprs_r049/**
  - dis/server_reports/orientbench-b-r049-cora-obb-native-risk-stagea-20260819/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute:
    gpu_count_max: 4
    gpu_hours_max: 320
    cpu_core_hours_max: 960
  wall_time:
    seconds_max: 259200
  data:
    allowed_dataset_ids:
      - DIOR-R-existing-r043-development-train-val-readonly
      - SODA-A-existing-r043-development-train-val-readonly
      - existing-valid-PSC-baselines-readonly
      - repository-tracked-evidence-readonly
    read_bytes_max: 4398046511104
    write_bytes_max: 536870912000
  write:
    allowed_paths:
      - experiments/r049_cora_obb/
      - configs/r049_cora_obb/
      - outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/
      - audit_bundles/r049/
      - docs/paper_jprs_r049/
      - dis/server_reports/orientbench-b-r049-cora-obb-native-risk-stagea-20260819/
      - claude_code_and_supervisor.md
    bytes_max: 536870912000
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
      - https://github.com/open-mmlab/
      - https://pypi.org/
      - https://files.pythonhosted.org/
      - https://download.pytorch.org/
      - https://repo.anaconda.com/
      - https://conda.anaconda.org/
conflict_keys:
  - server-execution-slot
  - dis/sug.md
  - gpu-all-four-cora-native-training
  - DOTA-v2.0-and-SODA-official-test-sealed
  - outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819
gates:
  - gate_id: G0_ASSET_ENV_AND_BASE_PARITY
    rule: "先读 pth_data/readme.md；若不可读则未执行完毕。复用 r043 的 DIOR-R/SODA-A PSC host 与 development train/val，记录 dataset/split/backbone/schedule/batch/lr/BN/framework/checkpoint sha256；两数据集 identity AP50/AP75 与 valid 归档或同 evaluator authority 的绝对差均 <=0.005 后才训练。普通路径、环境、AMP 和 evaluator 工程问题应修复，不得冒充科学失败。"
  - gate_id: G1_REAL_CORA_AND_SMOKE
    rule: "CORA 必须是 detector-native head：在原生正样本 feature 与 decoded OBB 上输出 periodic orientation distribution 和 orientation-harm distribution；反事实只改变 angle，中心/尺度/类别不变；proper risk loss、counterfactual ranking/alignment 和 no-GT inference 均有真实梯度与 mutation tests。不得退化为 post-hoc selector、crop classifier、detection-score fusion或 val GT 拟合。四卡 200-iteration smoke 有限且 baseline identity 不被结构改写。"
  - gate_id: G2_SEED0_TWO_DATASET_SURVIVAL
    rule: "从同一 checkpoint、同一追加预算运行 CONT、VM-NLL 和 CORA seed0。DIOR-R 与 SODA-A 各自均须：CORA 相对更强的 CONT/VM-NLL AP50 delta >=-0.005、AP75 delta >=-0.005；ar>=2.1 的 native-risk AUGRC absolute reduction >=0.01、Risk@70 reduction >=0.02，且 mean angle error 不增加 >1 degree。任一数据集失败即 REJECT_CORA_METHOD，不补种子、不碰 clean endpoint。"
  - gate_id: G3_THREE_SEED_RELIABILITY_GAIN
    rule: "仅 G2 双通过后补 seed1/2。两个数据集均要求至少2/3 seeds逐项通过G2；三种子 pooled mother-image paired bootstrap 对 strongest baseline 的 AUGRC 与 Risk@70 改善95% CI_low>0；fixed aspect-ratio and size bins 内方向一致，收益不得只来自 near-square/scale；native risk 同时优于 detection score、PSC native magnitude/entropy 与 frozen TTA consistency。"
  - gate_id: G4_STAGE_B_ELIGIBILITY
    rule: "G3 通过后冻结 code/config/checkpoints/native score 和所有温度；参数开销<=3%、端到端 latency增加<=10%，无 target-GT calibration。满足才输出 PROCEED_CORA_STAGE_B；Stage B 另轮才允许第二 detector family、第三数据集和 source-disjoint clean endpoint。"
early_stop_conditions:
  - "任一真实 baseline 在一次合理环境/evaluator修复后仍不能通过 G0，输出 NOT_ADJUDICATED_ASSET_ENV；不用假数据或随机 checkpoint。"
  - "200-iteration smoke 的 NaN/OOM/梯度异常先允许一次不改变科学结构的稳定性修复；仍失败输出 NOT_ADJUDICATED_IMPLEMENTATION。"
  - "seed0 中任一数据集触发 G2 失败立即正常早停；不得靠更多 epoch、seed、阈值、融合 detection score 或修改风险定义续命。"
  - "benefit 仅来自 near-square、固定 size/AR 后消失、risk head 偷用 GT/误差、或 VM-NLL 已解释全部收益，均输出 REJECT_CORA_METHOD。"
kill_conditions:
  - "读取或触碰 DOTA-v2.0 val、SODA-A official test、r047/r048 T_audit semantic fields 或任何本轮未登记 clean endpoint。"
  - "使用目标 val GT 做温度、阈值、候选、loss weight、epoch、seed 或可靠性分数选择；训练期只能用 train proper loss/gradient stability 冻结一次工程超参。"
  - "修改 frozen split、门槛、formal/exploratory 身份，丢弃失败数据集/seed，或把 O2-like angle distribution、OSKDet uncertainty、普通 VM-NLL 包装成 CORA 创新。"
  - "复活 Q-SetOD/OER/SAUR/AHC/P2C/crop-head，或只重排旧框而无 detector-native counterfactual risk learning。"
  - "伪造 GPU、训练、checkpoint、指标、manifest、测试或完成状态。"
completion_mapping:
  full_completion:
    execution_status: complete
    receipt_first_line: 执行完毕
  gated_scientific_early_stop_after_required_stage:
    execution_status: complete
    receipt_first_line: 执行完毕
  asset_environment_or_implementation_failure:
    execution_status: incomplete
    receipt_first_line: 未执行完毕
  partial_or_protocol_drift:
    execution_status: incomplete
    receipt_first_line: 未执行完毕
---

# 049：CORA-OBB 检测器内生反事实朝向风险 Stage A

## 1. 科学主张与最近邻边界

r048 证明继续做 HRSC crop classifier/head 没有顶刊价值。r049 回到唯一联合主线：P1 已测得 detector score 不能可靠排序角度损失；P3 必须让 detector 在一次正常训练后原生输出可信的 orientation risk，而不是事后拿 GT 拟合 selector。

CORA = **Counterfactual Orientation-Risk Alignment**。它不把“角度分布”本身写成创新：Deep Directional Statistics 已使用 von-Mises mixture；OSKDet 已从 keypoint heatmap uncertainty 估计 localization quality；SAOD 已定义 self-aware detector；2026 O2-RT-DETR 又用 angle-distribution refinement 表示旋转不确定性。CORA 只主张尚待实验验证的增量：

> 用保持 `(cx,cy,w,h,class)` 不变、只干预 angle 的检测器内反事实，学习完整 orientation-harm distribution，并把该原生风险用于 selective orientation under domain shift；风险目标与 detection confidence、普通 angle entropy、post-hoc calibration 明确分离。

最近邻一手来源：

- Deep Directional Statistics, ECCV 2018: https://openaccess.thecvf.com/content_ECCV_2018/html/Sergey_Prokudin_Deep_Directional_Statistics_ECCV_2018_paper.html
- OSKDet, CVPR 2022: https://openaccess.thecvf.com/content/CVPR2022/html/Lu_OSKDet_Orientation-Sensitive_Keypoint_Localization_for_Rotated_Object_Detection_CVPR_2022_paper.html
- SAOD, CVPR 2023: https://openaccess.thecvf.com/content/CVPR2023/papers/Oksuz_Towards_Building_Self-Aware_Object_Detectors_via_Reliable_Uncertainty_Quantification_and_CVPR_2023_paper.pdf
- ACM boundary analysis, CVPR 2024: https://openaccess.thecvf.com/content/CVPR2024/papers/Xu_Rethinking_Boundary_Discontinuity_Problem_for_Oriented_Object_Detection_CVPR_2024_paper.pdf
- O2-RT-DETR, TGRS 2026 / arXiv: https://arxiv.org/abs/2603.15497

## 2. 方法冻结：CORA-OBB

宿主固定为 r043 已登记、可复现的 PSC detector；禁止改第三方源码，使用项目内 custom module/config 接入。保持原检测分支，新增轻量 native orientation-risk head：

1. **Periodic orientation distribution**：从原生 angle feature 输出 `q(theta|x)` 或等价 doubled-angle/periodic distribution；VM-NLL arm 只含此项，是 O2-like/distributional uncertainty 的直接内部边界，不得把它叫 CORA。
2. **Harm distribution**：CORA 额外输出 bounded orientation harm `z in [0,1]` 的 ordinal/CDF distribution。主 `z` 为 le90 angle error 归一化；geometry-normalized severe event `angle_error > delta_0.75(GT_AR)` 为共主风险事件。推理只能用预测 feature、box 与分布。
3. **Detector-native counterfactuals**：在 train positives 对 decoded angle 施加冻结干预集合 `±{2,5,10,20,40} degrees`，其余 box/class 字节保持不变；用同一 native feature/angle-conditioned representation 预测各反事实 harm。pairwise 顺序由实际 GT harm 决定，不假设随 `|delta|` 单调。
4. **Proper and alignment losses**：真实预测与反事实均用 proper ordinal/CDF loss；再加 counterfactual pairwise alignment。风险梯度必须进入 orientation feature/head，但使用小权重和明确 gradient norm 防止破坏 detection branch。
5. **Native inference**：最终 reliability 固定为预测 harm distribution 的期望/尾概率；不能融合 detection score，不能在 val/test 上拟合温度或阈值。score fusion 只可作为标注清楚的 secondary 诊断，不参与 gate。

工程上可选择数值稳定的 von-Mises、circular bins、mixture 或 continuous OBB 表达，只要在 formal 前用 train-only smoke 冻结 `METHOD_FREEZE.json`，保留周期 proper distribution、harm distribution、angle-only counterfactual和风险梯度四项本质结构。最多允许两个 train-only loss-weight候选，按 finite loss/gradient balance 冻结；禁止看 val reliability 选权重。

## 3. 数据、对照与统计

本轮只使用 r043 已消费的 DIOR-R 与 SODA-A development train/val；不触碰 DOTA-v2.0、SODA official test 或任何旧 T_audit。两数据集各运行：

- `BASE_ID`: 原 valid checkpoint identity eval；
- `CONT`: 同 checkpoint、同 optimizer/augmentation/global batch/追加预算继续训练；
- `VM_NLL`: detector-native periodic distribution，只用 proper angle NLL；
- `CORA`: VM_NLL + harm distribution + counterfactual alignment；
- ablation `CORA_NO_CF` 仅在 CORA seed0 通过 G2 后运行，不参与 strongest baseline 选择。

顺序为 baseline/seed0 cheap gate → 双数据集通过后 seed1/2。追加预算默认最多3 epochs；若原配置的25% schedule更短则取更短者。每 epoch full-val。训练默认4卡且严格 global batch/lr/BN 对齐。

主评估域是 matched TP、GT aspect ratio `>=2.1`；同时报告完整 AR 与固定 size×AR bins。匹配和 AP 使用已有 full evaluator。可靠性指标包括 NRC、AUGRC、Risk@70/90、Brier/ECE、mean/median angle error；统计以 mother image 为 bootstrap cluster，10,000 replicates，seed `20260819`。比较对象固定为 detection score、PSC native magnitude/entropy、VM-NLL entropy/concentration、frozen TTA consistency 与 strongest learned arm。

## 4. 执行顺序

### Task 0：启动、readme 与真实 parity

- HTTPS fast-forward 到精确 dispatch commit，核验 `server-primary`、plan/blob/SHA、四卡与唯一报告路径；先提交唯一 `STARTED.json`。
- **第一步读取** `/home/rspip/cqc/pro/study/pth_data/readme.md`。解析两个 valid PSC baseline 的全部 AGENTS 字段和 checkpoint SHA。
- 复用真实兼容环境与 evaluator，完成两数据集 BASE identity parity；可修普通依赖/路径问题，但禁止伪装版本。

### Task 1：方法实现、数学测试与四卡 smoke

- 所有实现放进 `experiments/r049_cora_obb/`，config 放进 `configs/r049_cora_obb/`，不改 third_party。
- tests 至少覆盖：pi-periodicity；angle-only intervention 的非角参数逐字节不变；`delta=0` identity；harm/CDF proper target；反事实顺序 mutation；GT inference guard；risk gradient 到达 orientation head 且 detector sensitive ops finite。
- 四卡200-iteration smoke；记录四 rank、loss components、gradient norms、显存、吞吐与初始 AP parity。formal 前提交并推送 `METHOD_FREEZE.json`。

### Task 2：seed0 双数据集生死门

- 先训练/eval CONT 与 VM_NLL，再 CORA；同 checkpoint、预算与 evaluator。
- DIOR-R 过 G2 后才跑 SODA-A CORA；任一数据集失败即正常结束 `REJECT_CORA_METHOD`，不补 seeds。
- 保存 best/latest、每 epoch AP50/AP75、matched raw rows、native score、角误差和 train log；checkpoint 大于95MB时确定性切块并 manifest。

### Task 3：三种子与 Stage-B 资格

- 仅 seed0 双通过后运行 seeds1/2 和必要 ablation。
- 完成固定 AR/size control、image bootstrap、latency/FLOPs/params、independent metric recomputation 与真实 mutations。
- 只有 G3/G4 全过才输出 `PROCEED_CORA_STAGE_B`；否则输出 `REJECT_CORA_METHOD`。本轮任何结果都不打开 clean endpoint。

### Task 4：交付

必交 `asset_inventory.csv`、`METHOD_FREEZE.json`、tests/log、run configs、`training_runs.csv`、`fullval_metrics.csv`、`risk_metrics.csv`、`fixed_bin_controls.csv`、`bootstrap_summary.csv`、`efficiency.csv`、raw-row schema、manifest、independent validator、mutation summary、`gate.json` 与中文决策报告。服务器报告必须说明正常/异常结束、触发门、期刊等级和禁止的后续。

聊天回执严格两行：第一行“执行完毕”或“未执行完毕”；第二行唯一服务器报告路径。

## 5. 顶刊映射

- `PROCEED_CORA_STAGE_B`：项目升为 **TGRS candidate / JPRS potential**；下一轮才允许第二 detector family、第三 dataset 与 source-disjoint clean endpoint。
- `REJECT_CORA_METHOD`：仍为 **strong JSTARS / Remote Sensing**，低于合法目标；CORA 停止，不靠增算力、调阈值或融合 score 救场。
- 技术未裁决：只修资产/实现根因，不改方法本质和门槛；未真正完成必须回执“未执行完毕”。
