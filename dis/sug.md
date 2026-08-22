---
schema_version: 1
project_id: OrientBench
plan_id: b-r051-cmr-obb-cyclic-marginalized-roi-20260822
dispatch_id: orientbench-b-r051-cmr-obb-cyclic-marginalized-roi-20260822
business_id: "051"
owner: B
status: READY
risk_class: L2
authorization_ref: "用户 2026-08-19：『后续GPU等的不需要授权，都在空着呢，抓紧推进。』"
base_sha: f567b3dfb5fbb3350e705ff9d4d959cf4bde866e
scientific_snapshot_sha: f567b3dfb5fbb3350e705ff9d4d959cf4bde866e
server_report_path: dis/server_reports/orientbench-b-r051-cmr-obb-cyclic-marginalized-roi-20260822/SERVER_EXECUTION_REPORT.md
read_set:
  - AGENTS.md
  - dis/governance/**
  - dis/plans/B/b-r051-cmr-obb-cyclic-marginalized-roi-20260822/sug.md
  - /home/rspip/cqc/pro/study/pth_data/readme.md
  - /home/rspip/cqc/pro/study/pth_data/**
  - /home/rspip/cqc/data/dataset/dota1.0/**
  - /home/rspip/cqc/data/dataset/dior/**
  - /home/rspip/cqc/data/dataset/soda-a/**
  - /home/rspip/cqc/pro/study/third_party/**
  - experiments/r049_rev2_pef_obb/**
  - audit_bundles/r049_rev2/**
write_set:
  - experiments/r051_cmr_obb/**
  - configs/r051_cmr_obb/**
  - outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/**
  - audit_bundles/r051/**
  - docs/paper_jprs_r051/**
  - dis/server_reports/orientbench-b-r051-cmr-obb-cyclic-marginalized-roi-20260822/**
  - claude_code_and_supervisor.md
resource_scope:
  compute:
    gpu_count_max: 4
    gpu_hours_max: 1200
    cpu_core_hours_max: 3000
  wall_time:
    seconds_max: 1209600
  data:
    allowed_dataset_ids:
      - DOTA-v1.0-train-val
      - DIOR-R-existing-trainval-test
      - SODA-A-existing-train-val
      - existing-valid-PSC-and-Oriented-RCNN-baselines-readonly
      - repository-tracked-evidence-readonly
    read_bytes_max: 8796093022208
    write_bytes_max: 1649267441664
  write:
    allowed_paths:
      - experiments/r051_cmr_obb/
      - configs/r051_cmr_obb/
      - outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822/
      - audit_bundles/r051/
      - docs/paper_jprs_r051/
      - dis/server_reports/orientbench-b-r051-cmr-obb-cyclic-marginalized-roi-20260822/
      - claude_code_and_supervisor.md
    bytes_max: 1649267441664
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
  - gpu-all-four-r051-cmr-full-detector-training
  - outputs/persistent_artifacts/orientbench_r051_cmr_obb_20260822
gates:
  - gate_id: G0_PRIOR_ART_ASSET_AND_PARITY
    rule: "先读 pth_data/readme.md，登记 valid DOTA-v1.0 Oriented R-CNN 与 PSC baseline 的 config/log/checkpoint/split/backbone/schedule/global batch/lr/BN/mAP/framework/sha256。对 2019-2026-08 一手文献做精确 novelty collision audit，至少覆盖 RoI Transformer、Oriented R-CNN、ReDet/FRED、PSC/FSC、AQE/O2-RT-DETR、PQA 与 FAA。若已存在同一 decoded-proposal cyclic RoI likelihood marginalization + native orientation risk，则 STOP_PRIOR_ART_COLLISION，不启动 GPU。合法 baseline identity parity 失败则 NOT_ADJUDICATED_ASSET_ENV。"
  - gate_id: G1_EXACT_PROPOSAL_CYCLIC_EVIDENCE_AND_CHEAP_SIGNAL
    rule: "实现 CMR-OBB：以实际 decoded proposal B=(cx,cy,w,h,class) 为唯一干预单元，固定 cx/cy/w/h/class，仅令 theta 在 K=12 的 pi-periodic ring 上变化；对每个候选执行 batched Rotated RoIAlign 7x7、共享 encoder 与 shared evidence head，形成 q；以 circular marginalization 输出 refined angle/box/class likelihood，以 q 的冻结尾部期望输出 no-GT native risk。必须在 decode/NMS 前生成不可丢失 candidate_uid，并将 exact level/cell/anchor-or-proposal id、完整 q、original/refined box、risk 随最终检测保留，禁止 NMS 后按 box 几何反猜。结构/mutation/equivariance/finite-gradient tests 全过后，冻结 host 只训练 CMR/强 controls 3 epochs，DOTA train->val 四卡每 epoch full-val。相对 strongest DIRECT_DIST/SINGLE_ROI_QUALITY 同时满足 AP50 delta>=-0.003、AP75 gain>=0.005、AR>=2.1 angle-error reduction>=5%、AUGRC与Risk@70 relative reduction>=10%，两项 mother-image bootstrap CI_low>0；否则 REJECT_CMR_CHEAP_SIGNAL，停止。"
  - gate_id: G2_DOTA_ORCNN_FULL_DETECTOR
    rule: "仅 G1 通过后，从同一合法初始化在 DOTA-v1.0 train->val 四卡完整训练 CONT、DIRECT_DIST、SINGLE_ROI_QUALITY、CMR，标准 schedule/global batch/lr/BN/augmentation，每 epoch full-val并以最终 epoch 一次裁决。CMR 相对 strongest control 必须同时满足 mAP/AP50 delta>=-0.003、AP75 absolute gain>=0.010、AR>=2.1 angle-error relative reduction>=10%、native-risk AUGRC与Risk@70 relative reduction>=15%、两项 mother-image bootstrap CI_low>0。失败即 REJECT_CMR_METHOD，不扩展。"
  - gate_id: G3_MULTIDATA_MULTIHOST
    rule: "仅 G2 通过后完成 DOTA/Oriented-RCNN、DOTA/PSC、DIOR-R/Oriented-RCNN、SODA-A/PSC 四个正式 cells 的 CONT/DIRECT_DIST/CMR 同预算训练。至少3/4 cells逐项满足 AP75 gain>=0.005、angle-error下降>=5%、AUGRC与Risk@70下降>=10%、mAP/AP50 delta>=-0.005，且两个 host family、三个 datasets 均有通过 cell；否则不得称通用修复。"
  - gate_id: G4_SEEDS_TRANSFER_AND_EFFICIENCY
    rule: "仅 G3 通过后在 DOTA/Oriented-RCNN 与 DIOR-R/Oriented-RCNN 补 seeds1/2；再冻结 source-trained CMR scorer，做至少两个 leave-dataset或leave-detector zero-target-GT transfer，不在 target 用 GT 调 K、temperature、risk、threshold或epoch。主 cells 至少2/3 seeds逐项过门，pooled image-bootstrap CI_low>0；两个 transfer 的 AUGRC/Risk@70均改善>=5%且AP50/AP75不降>0.005；参数增加<=7%、端到端 latency增加<=25%。全过才输出 PROCEED_CMR_PAPER。"
early_stop_conditions:
  - "精确 prior-art collision：停止，不能靠改名包装。"
  - "q/risk 无法精确绑定产生最终 detection 的 candidate_uid：NOT_ADJUDICATED_IMPLEMENTATION。"
  - "候选角不改变实际 Rotated RoIAlign 观察、共享权重不成立、旋转一 bin 后 q 不循环平移、或任何关键梯度非有限：NOT_ADJUDICATED_IMPLEMENTATION。"
  - "G1 cheap signal 失败：停止所有 full detector 训练。"
  - "G2 未同时改善高 IoU、角误差与 native risk：REJECT_CMR_METHOD，停止 G3/G4。"
kill_conditions:
  - "读取 DOTA-v2.0 val、SODA-A official test、旧 HRSC T_audit semantic fields 或任何未登记 clean endpoint。"
  - "用 val/test GT 选择 K=12、7x7、loss weight、temperature、risk definition、epoch、seed、threshold、cell或模型。"
  - "修改 frozen split、指标、门槛、formal/exploratory 身份，或丢弃失败 cell/seed。"
  - "修改 third_party 源码；所有适配必须在 orientbench 内。"
  - "把 r049/本轮失败结果写入正文、补充、附录或消融。"
  - "伪造 candidate provenance、训练、checkpoint、指标、manifest、测试或完成状态。"
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
---

# 业务 051：CMR-OBB 解码 proposal 周期边缘化

## 1. 目标与主要矛盾

r049 已证明 anchor-template 的四点采样不足以改善高 IoU 朝向精度，并且其 NMS 后 q provenance 不可信。业务 051 不修 PEF，不重跑负配置；它把观测单元改为真实 decoded proposal，并让周期候选证据直接参与 proposal likelihood 与 box/angle marginalization。

核心方法 **Cyclic Marginalized RoI for OBB (CMR-OBB)**：

1. 对实际 proposal `B=(cx,cy,w,h,class)` 构造 `theta mod pi` 的 K=12 候选环；
2. 每个候选用完整 7x7 Rotated RoIAlign 读取对象内部与边界证据，不再用 anchor 四角近似；
3. 共享 encoder/scorer 输出可多峰周期 posterior `q(theta|x,B)`；
4. 以 circular marginal likelihood 联合 refined angle、box/class likelihood，而非后处理 selector；
5. posterior tail expectation 直接给出 no-GT native orientation risk；
6. 从 proposal 生成起携带不可变 `candidate_uid` 穿过 decode/NMS，保证最终 q/risk 与检测框精确同源。

论文潜在主线仍是 `measure -> diagnose -> fix`：OrientBench 给出 detection score 与 orientation reliability 的缺口；CMR 用 proposal-level visual intervention 修复。只有正结果才进入论文。

## 2. 创新边界

不得把以下已有成分单独写成创新：Rotated RoIAlign、角度分类/分布、周期编码、旋转等变、feature alignment、scalar localization quality、普通 cascade refinement。

一手最近邻边界：

- RoI Transformer / Oriented R-CNN：单一对齐 RoI 与常规 refinement；
- PSC / FSC / AQE / O2-RT-DETR：角度编码或直接分布，不对同一 decoded proposal 改变 observation operator；
- ReDet / FRED / FAA：旋转等变或 canonical feature alignment，不产生 proposal-specific cyclic posterior 与 native risk；
- PQA：pixel-level scalar localization quality，不是完整 orientation posterior。

CMR 只有在 **exact decoded proposal intervention + cyclic likelihood marginalization + native risk** 三者合取，并打赢等预算 direct distribution 与 single-RoI quality 后才构成方法增量。G0 必须用一手论文再次核查；检出同构先例立即停止。

## 3. 实现纪律

- 第三方源码只读；配置复制到项目内。
- 训练默认四卡；任何正式训练先做小样本与 AMP/gradient smoke。
- 首 epoch 明显偏低立即停止报告；每 epoch full-val；只保留 best 与 latest/final，清理 checkpoint 前保留 manifest、sha256、config、log和再生命令。
- DOTA 固定 train->val，不追公开 test mAP；DIOR-R 固定 trainval->test；SODA-A 固定 train->val，禁止 official test。
- K、RoI size、loss、risk与所有门槛在打开正式 val/test前冻结；禁止结果驱动调参。
- q/risk provenance validator 必须真实改变/删除 candidate_uid、交换 level/cell/anchor、重复候选与篡改 NMS mapping，并全部非零拒绝。shape check或恒等断言不算 mutation。

## 4. 强对照

- `CONT`：原 host；
- `DIRECT_DIST`：同 proposal feature、同参数量的 K-way residual angle distribution，不做候选 RoI intervention；
- `SINGLE_ROI_QUALITY`：单一 host-angle Rotated RoI + scalar orientation quality；
- `CMR`：K-way candidate Rotated RoI + shared scorer + likelihood marginalization；
- `CMR_SHUFFLED_GRID`：仅作机制消融，候选 observation 与角索引打乱，不能进入主控制选择。

所有主对照同初始化、schedule、global batch、lr、BN、augmentation和最终 epoch口径。不能靠参数量、score fusion或更长训练取胜。

## 5. 产物

每个正式 cell 保存：完整 config、环境、命令、每 epoch log、final/best checkpoint hash、raw predictions、exact candidate provenance、完整 q/native risk、matched rows、AP50/AP75、角误差、AR×size bins、risk-coverage、mother-image bootstrap、参数/延迟、manifest、schema、sha256、can_recompute 与独立 validator/mutations。

失败结果只留内部研发记录，不进入目标论文、补充、附录或消融。服务器回执严格两行：第一行“执行完毕”或“未执行完毕”，第二行唯一报告路径。

## 6. 期刊映射

- `PROCEED_CMR_PAPER`：具备 **JPRS candidate / strong TGRS route**，仍需整合主稿与外部红队后才称投稿候选；
- G2 通过但 G3/G4 失败：方法不具备跨域/跨架构顶刊主张，不投稿负稿；
- G1 或 G2 失败：CMR 路线关闭，项目仍为 `STRONG_JSTARS_OR_REMOTE_SENSING`，低于合法目标。
