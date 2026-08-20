---
schema_version: 2
business_instruction: "049"
plan_id: b-r049-rev2-pef-multidata-multihost-20260819
dispatch_id: orientbench-b-r049-rev2-pef-multidata-multihost-20260819
initiator: B
activation_authorization:
  mode: owner_only
  delegate: null
  reference: null
closure_authorization:
  mode: owner_only
  delegate: null
  reference: null
base_sha: 60e82f77bac1fbf3c07e6df9aeb1a56d533b2de3
supersedes: b-r050-pef-obb-periodic-evidence-stagea-20260819
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-19：『授权业务049的新数据与四卡detector训练，负结果搞你妈的附录啊？浪费版面费？』"
scientific_snapshot:
  primary: 60e82f77bac1fbf3c07e6df9aeb1a56d533b2de3
  r049_v1_state: "B_REJECT_EXECUTED_CORA_V1_JOINT_PENDING"
  r050_state: "WITHDRAWN_BEFORE_START"
  venue_state: "当前仅 strong JSTARS / Remote Sensing，低于 TGRS-or-better 合法目标"
  target_route: "PEF-OBB full-detector multi-data multi-host positive-contribution route"
publication_policy: "失败方法及负结果仅保留内部研发台账；目标论文正文、补充材料、附录和消融表均不纳入 CORA-v1、SAUR、AHC、P2C、OER、Q-SetOD 等失败线。PEF 未达到正贡献门则不形成该方法稿。"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r049-rev2-pef-multidata-multihost-20260819/SERVER_EXECUTION_REPORT.md
read_set:
  - AGENTS.md
  - dis/governance/roles/SERVER.md
  - dis/coordination.json
  - dis/plans/B/b-r049-rev2-pef-multidata-multihost-20260819/sug.md
  - /home/rspip/cqc/pro/study/pth_data/readme.md
  - /home/rspip/cqc/pro/study/pth_data/**
  - top_journal_v3_reaudit_055/**
  - experiments/r049_cora_obb/**
  - configs/r049_cora_obb/**
  - audit_bundles/r041/**
  - configs/**
  - orientbench/**
  - scripts/**
  - /home/rspip/cqc/data/dataset/**
write_set:
  - experiments/r049_rev2_pef_obb/**
  - configs/r049_rev2_pef_obb/**
  - outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/**
  - audit_bundles/r049_rev2/**
  - docs/paper_jprs_r049_rev2/**
  - dis/server_reports/orientbench-b-r049-rev2-pef-multidata-multihost-20260819/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute:
    gpu_count_max: 4
    gpu_hours_max: 1400
    cpu_core_hours_max: 3200
  wall_time:
    seconds_max: 1209600
  data:
    allowed_dataset_ids:
      - DOTA-v1.0-train-val
      - DIOR-R-existing-trainval-test
      - FAIR1M-v1.0-existing-trainval-test
      - SODA-A-existing-train-val
      - existing-valid-PSC-and-Oriented-RCNN-baselines-readonly
      - repository-tracked-evidence-readonly
    read_bytes_max: 8796093022208
    write_bytes_max: 2199023255552
  write:
    allowed_paths:
      - experiments/r049_rev2_pef_obb/
      - configs/r049_rev2_pef_obb/
      - outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819/
      - audit_bundles/r049_rev2/
      - docs/paper_jprs_r049_rev2/
      - dis/server_reports/orientbench-b-r049-rev2-pef-multidata-multihost-20260819/
      - claude_code_and_supervisor.md
    bytes_max: 2199023255552
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
  - gpu-all-four-r049-rev2-full-detector-training
  - outputs/persistent_artifacts/orientbench_r049_rev2_pef_obb_20260819
gates:
  - gate_id: G0_ASSET_DATA_AND_CONFIG_FREEZE
    rule: "第一步读取 pth_data/readme.md。确认 DOTA-v1.0 train/val、DIOR-R trainval/test、FAIR1M trainval/test、SODA-A train/val 的真实路径、标注、类表和 evaluator；登记 PSC 与 Oriented R-CNN 的 valid config/checkpoint、backbone、schedule、global batch、lr、BN、framework、mAP 与 sha256。任一目标数据不存在可跳过该扩展 cell，但 DOTA-v1.0 + PSC 主 cell 不成立则未执行完毕。"
  - gate_id: G1_REAL_PEF_AND_FULL_DETECTOR_SMOKE
    rule: "PEF 必须对固定 center/size/class 的 pi-periodic candidate angles 执行共享权重的真实 rotated RGB/FPN feature sampling 与 scoring，输出完整 q(theta|x,B)、refined angle 和 native risk；不得是 affine delta、scalar harm head、post-hoc selector、score fusion 或 GT inference。完成结构/mutation tests和四卡全参数 detector 500-iteration smoke；梯度须到达 backbone/neck/orientation head/sampler/scorer且全部有限。普通工程问题自主修复。"
  - gate_id: G2_DOTA_PSC_FULL_TRAIN_PRIMARY
    rule: "在 DOTA-v1.0 train->val 上，从同一合法初始化、标准完整 schedule、四卡相同 global batch/lr/BN/augmentation，完整训练 CONT、DIRECT_DIST(AQE/O2-like equal-budget)、SCALAR_QUALITY 与 PEF；每 epoch full-val。PEF 必须相对 strongest control 同时满足：mAP/AP50 delta >=-0.003，AP75 absolute gain >=0.010，AR>=2.1 mean angle error relative reduction >=10%，native-risk AUGRC 与 Risk@70 relative reduction均>=15%，mother-image bootstrap improvement CI_low>0。失败即 REJECT_PEF_METHOD，不扩数据/架构。"
  - gate_id: G3_MULTIDATA_MULTIHOST_REPLICATION
    rule: "仅 G2 通过后，按资源可用性完成预登记六个 full-detector cells：DOTA/PSC、DOTA/Oriented-RCNN、DIOR/PSC、DIOR/Oriented-RCNN、FAIR1M/PSC、SODA/Oriented-RCNN；各 cell 的 CONT/DIRECT_DIST/PEF 同 schedule 四卡全参数训练。至少5/6 cells须 AP75 gain>=0.005、AUGRC与Risk@70 relative reduction>=10%、mean angle error下降>=5%，且所有 cells mAP/AP50 delta>=-0.005；两个 detector family和至少三个 datasets都必须有通过 cell。否则不得称普适方法。"
  - gate_id: G4_NO_TARGET_GT_AND_THREE_SEEDS
    rule: "仅 G3 通过后，在 DOTA/PSC、DIOR/Oriented-RCNN 两主 cells 补 seeds1/2，并冻结 source-trained PEF scorer 做 leave-dataset或leave-detector零目标GT迁移。主 cells 至少2/3 seeds逐项过门，pooled image bootstrap CI_low>0；零GT迁移至少两个独立target cells的AUGRC/Risk@70均改善>=5%、AP50/AP75不降>0.005。参数增加<=5%、latency<=15%。全过才输出 PROCEED_PEF_PAPER_AND_CLEAN_CONFIRMATION。"
early_stop_conditions:
  - "DOTA-v1.0 + PSC 真实资产或标准四卡训练配置在合理修复后仍不成立：NOT_ADJUDICATED_ASSET_ENV。"
  - "PEF 不依赖 candidate-aligned visual evidence、周期平移测试失败、梯度不到 detector 主干与 scorer、或退化为 scalar/affine/post-hoc：NOT_ADJUDICATED_IMPLEMENTATION。"
  - "G2 主 cell 未形成同时改善 AP75、角误差与 native risk 的正贡献：REJECT_PEF_METHOD，立即停止其余 full trainings。"
  - "G3 未跨架构/跨数据复现：停止顶刊方法稿，不以单数据集正结果包装普适性。"
kill_conditions:
  - "读取 DOTA-v2.0 val、SODA-A official test、旧 T_audit semantic fields 或任何未在本 revision 登记的数据端点。新数据授权不等于允许偷开这些 clean endpoints。"
  - "使用 val/test GT 选择 K、loss weight、risk definition、temperature、epoch、seed、threshold 或发布 cell。"
  - "修改 frozen split、门槛、metric、formal/exploratory 身份，丢弃失败 cell/seed，或把 AQE/O2 direct distribution、PQA scalar quality、FRED generic equivariance当成 PEF 创新。"
  - "重跑 CORA-v1/SAUR/AHC/P2C/OER/Q-SetOD，或把任何失败方法/负结果写入目标论文正文、补充材料、附录或消融表。"
  - "伪造数据、GPU、训练、checkpoint、指标、manifest、测试或完成状态。"
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

# 049 修订版：PEF-OBB 新数据、多架构、四卡完整 detector 训练

## 1. 执行目标

用户已明确授权新数据和四卡 detector 训练。本 revision 不再把项目限制在 DIOR/SODA 的三 epoch continuation，也不再用 frozen-head 小实验代替方法验证。目标是形成一条只由**正贡献**构成的 JPRS/TGRS 方法论文证据链：

> PEF-OBB 通过对候选角度逐一重采样真实视觉证据，构建完整 `theta mod pi` 周期能量场；该场同时修正角度并输出无需目标域 GT 标定的 native orientation risk。

CORA-v1 已经结束；失败配置、失败方法和负结果不进入目标论文任何版面。内部 Git 记录仅服务于研发止损和避免重复浪费，不构成投稿内容。

## 2. 科学增量与最近邻

PEF 的不可替代结构是 **candidate-conditioned visual evidence**：候选角改变 rotated sampling grid，scorer 权重跨候选共享，得到可多峰、可非单调的周期 q。主风险来自 q 的尾部质量/期望偏差，不能使用 detection score 或另训 scalar harm 作为主分数。

必须诚实对照：

- AQE（TGRS 2023, DOI `10.1109/TGRS.2023.3292111`）和 O2-RT-DETR（TGRS 2026 / arXiv `2603.15497`）已经做直接角度分布；PEF 必须由 equal-budget DIRECT_DIST 对照证明“候选视觉重采样”的额外价值。
- PQA（AAAI 2026, DOI `10.1609/aaai.v40i16.38411`）已经做 pixel-level scalar localization quality；PEF 的 claim 只能是完整 orientation evidence field 与 native risk。
- FRED（AAAI 2024, DOI `10.1609/aaai.v38i4.28069`）已经做全检测器旋转等变；PEF 不宣称一般 equivariant detector。

## 3. 数据与 detector

### 主开发与训练

- DOTA-v1.0：严格 train 训练、val 验证；不追公开 trainval/test mAP。
- 主架构：valid PSC Rotated RetinaNet，标准完整 schedule、四卡全参数训练。

### 扩展验证

- DIOR-R、FAIR1M-v1.0：按现有已登记 trainval/test 口径。
- SODA-A：沿用项目已登记 train/val 口径，不碰 official test。
- 第二架构：valid Oriented R-CNN；若某数据集只有另一已登记两阶段 config，可在不改变 detector-family claim 的前提下采用并记录。

所有方法臂必须从同一合法初始化出发，按各自 valid baseline 的原始 schedule/global batch/lr/BN 对齐；不能拿 continuation 和 from-scratch 结果混比。训练默认四卡，首轮 smoke 后全参数更新 backbone、neck 与 detection heads。

## 4. PEF 冻结结构

服务器可以自主选择数值稳定的实现，但以下本质结构固定：

1. 对每个正样本/候选 box 固定 `(cx,cy,w,h,class)`，在 `theta mod pi` 上生成统一候选环；K 和采样分辨率只按 train-only 显存/数值 smoke 冻结。
2. 候选角必须真实改变 rotated RGB/FPN sampling grid；共享 scorer 不读取 candidate index、GT、detection score。
3. q 使用 circular softmax/proper likelihood训练；允许 coarse-to-fine residual，但不能用独立 scalar harm head替代 q。
4. refined angle 来自 q 的 circular mode/mean；native risk 来自 q 的固定 tail mass或expected deviation。定义写入 `METHOD_FREEZE.json` 后不可根据 val 改动。
5. 同时导出 original angle、refined angle、完整 q、native risk，分别核验 correction、ranking 与 AP，避免 NMS/score fusion掩盖因果来源。

## 5. 执行顺序

### Task 0：启动、数据/资产核验

- HTTPS fast-forward 到精确 dispatch commit；核验 `server-primary`、plan commit/blob/SHA、四卡和唯一报告路径，先写唯一 `STARTED.json`。
- 第一动作读取 `/home/rspip/cqc/pro/study/pth_data/readme.md`，生成 dataset/config/checkpoint inventory。
- 对 DOTA/PSC 与后续计划 cells 完成 baseline identity parity；路径/evaluator/AMP/非法零面积标注等工程问题由服务器自主修复。

### Task 1：实现与四卡全参数 smoke

- 项目内实现 PEF、DIRECT_DIST 和 SCALAR_QUALITY；禁止修改 third_party。
- tests 至少覆盖：pi-periodicity、旋转一 bin 的 energy circular shift、非角字段不变、candidate feature mutation、candidate collapse、q 归一化、no-GT inference、risk 对分布展宽单调、梯度到 backbone/neck/orientation head/sampler/scorer、finite sensitive ops。
- 用 DOTA/PSC 完成四卡500 iter全参数 smoke，记录每项 loss、各模块梯度范数、吞吐与显存，冻结方法。

### Task 2：DOTA/PSC 标准完整训练

- 完整训练 CONT、DIRECT_DIST、SCALAR_QUALITY、PEF；每 epoch full-val，保存 best/latest。
- 只以冻结 G2 判定是否有同时改善高 IoU 精度、角误差和 native risk 的正方法贡献。G2 失败就正常结束，不再扩展；结果不进论文或附录。

### Task 3：多数据、多架构复现

- 仅 G2 通过后运行六个预登记 cells；服务器可按资源串并行，但单次训练必须四卡对齐。
- 每个 cell 保存 raw q/native risk/matched rows、AP、angle error、risk curve、fixed AR×size bins 和完整 provenance。

### Task 4：三种子、零目标GT与效率

- 仅 G3 通过后补主 cells seeds1/2、source-trained scorer transfer、bootstrap与效率。
- 只有 G4 全过才允许下一业务打开新的 clean confirmation endpoint 并写正结果方法稿；本 revision 不消费 DOTA-v2.0/SODA official test。

## 6. 交付与投稿过滤

必交 `asset_inventory.csv`、`METHOD_FREEZE.json`、configs/tests/logs、training runs、full-val AP/angle/risk 表、raw q schema、matched rows、bootstrap/fixed-bin/efficiency、manifest/sha256、validator、mutation summary、gate 与中文决策报告。

服务器可以为真实运行自主修复非本质工程问题，不必在路径、依赖、AMP、监督器和 evaluator 小事上停下来请示；不得改科学结构、数据口径、对照、门槛或信息墙。

投稿过滤是硬规则：只有通过门控的 PEF 正结果、必要强基线和机制消融可进入论文；历史失败线和本轮失败结果均不进入正文、补充或附录。

聊天回执严格两行：第一行“执行完毕”或“未执行完毕”；第二行唯一服务器报告路径。

## 7. 期刊映射

- `PROCEED_PEF_PAPER_AND_CLEAN_CONFIRMATION`：**JPRS candidate / strong TGRS route**，下一业务完成 clean confirmation 后才可称投稿候选。
- `REJECT_PEF_METHOD`：不形成 PEF 论文，不拿负结果凑附录；项目仍未达到合法期刊目标。
- 技术未裁决：必须回执“未执行完毕”，只修真实资产/实现后继续同一 revision。

