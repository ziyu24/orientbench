---
schema_version: 2
business_instruction: "050"
plan_id: b-r050-pef-obb-periodic-evidence-stagea-20260819
dispatch_id: orientbench-b-r050-pef-obb-periodic-evidence-stagea-20260819
initiator: B
activation_authorization:
  mode: owner_only
  delegate: null
  reference: null
closure_authorization:
  mode: owner_only
  delegate: null
  reference: null
base_sha: 9f20680c1b094bc029614fe7be3e0b9b4d13abc7
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-19：『后续GPU等的不需要授权，都在空着呢，抓紧推进。』"
scientific_snapshot:
  primary: 9f20680c1b094bc029614fe7be3e0b9b4d13abc7
  prior_method_state: "B 已拒绝 executed CORA-v1；Q-SetOD、OER/OER-D、SAUR、AHC、P2C、CORA-v1 与 HRSC crop-head rescue 均停止"
  joint_state_note: "r049 只有 B verdict，B/C 联合 scientific state 仍 PENDING"
  venue_state: "当前仅 strong JSTARS / Remote Sensing，低于 TGRS-or-better 合法目标"
  target_route: "PEF-OBB candidate-conditioned periodic evidence field"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r050-pef-obb-periodic-evidence-stagea-20260819/SERVER_EXECUTION_REPORT.md
read_set:
  - AGENTS.md
  - dis/governance/roles/SERVER.md
  - dis/coordination.json
  - dis/plans/B/b-r050-pef-obb-periodic-evidence-stagea-20260819/sug.md
  - /home/rspip/cqc/pro/study/pth_data/readme.md
  - /home/rspip/cqc/pro/study/pth_data/**
  - top_journal_v3_reaudit_055/saur_stagea_r043_20260818/**
  - experiments/r049_cora_obb/**
  - configs/r049_cora_obb/**
  - measure_fix_v2/track_a_pkg/**
  - configs/**
  - orientbench/**
  - scripts/**
  - /home/rspip/cqc/data/dataset/**
write_set:
  - experiments/r050_pef_obb/**
  - configs/r050_pef_obb/**
  - outputs/persistent_artifacts/orientbench_pef_obb_r050_20260819/**
  - audit_bundles/r050/**
  - docs/paper_jprs_r050/**
  - dis/server_reports/orientbench-b-r050-pef-obb-periodic-evidence-stagea-20260819/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute:
    gpu_count_max: 4
    gpu_hours_max: 360
    cpu_core_hours_max: 1200
  wall_time:
    seconds_max: 345600
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
      - experiments/r050_pef_obb/
      - configs/r050_pef_obb/
      - outputs/persistent_artifacts/orientbench_pef_obb_r050_20260819/
      - audit_bundles/r050/
      - docs/paper_jprs_r050/
      - dis/server_reports/orientbench-b-r050-pef-obb-periodic-evidence-stagea-20260819/
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
  - gpu-all-four-pef-native-training
  - DOTA-v2.0-and-SODA-official-test-sealed
  - outputs/persistent_artifacts/orientbench_pef_obb_r050_20260819
gates:
  - gate_id: G0_ASSET_ENV_AND_BASE_PARITY
    rule: "先读 pth_data/readme.md；复用 r043 DIOR-R/SODA-A PSC host 与已消费 development train/val。两 host identity AP50/AP75 与 valid authority 绝对差均 <=0.005。环境、路径、AMP、非法零面积标注等普通工程问题须修复，不能冒充方法失败。"
  - gate_id: G1_REAL_PERIODIC_EVIDENCE_AND_FROZEN_HEAD_FEASIBILITY
    rule: "PEF 必须对固定 center/size/class 的 K 个 pi-periodic candidate angles 分别执行共享权重的 rotated feature sampling/scoring，形成 image-conditioned energy field q(theta|F,B)；禁止用 affine delta、单个 scalar harm head、GT inference、detection-score fusion 或 val calibration 冒充。先冻结 host，仅训练相同预算的 DIRECT_DIST、SCALAR_QUALITY 与 PEF heads。DIOR-R seed0 上 PEF 相对 strongest native baseline 的 matched-TP AUGRC 与 Risk@70 relative reduction 均 >=10%，AP50/AP75 delta 均 >=-0.005，mean angle error 不增加 >0.2 degree，才进入 SODA-A；SODA-A 同门。任一失败即 REJECT_PEF_METHOD，不做端到端训练。"
  - gate_id: G2_END_TO_END_TWO_DATASET_SEED0
    rule: "仅 G1 双通过后，从同一 checkpoint、同一三 epoch上限、同 optimizer/augmentation/global batch/BN 运行 CONT、DIRECT_DIST、SCALAR_QUALITY、PEF。两个数据集各自均要求 PEF 对 strongest arm：AP50/AP75 delta >=-0.005；AUGRC 与 Risk@70 relative reduction 均 >=10% 且 mother-image paired bootstrap improvement CI_low>0；mean angle error relative reduction >=5%。此外至少一个数据集 AP75 absolute gain >=0.005。任一失败即 REJECT_PEF_METHOD，不补 seed。"
  - gate_id: G3_NO_TARGET_GT_TRANSFER
    rule: "仅 G2 双通过后，冻结 DIOR-trained PEF head 直接评 SODA-A、冻结 SODA-trained head 直接评 DIOR-R；目标域不得重训、温度、阈值或用 GT 选 checkpoint。两个方向均须 AP50/AP75 delta >=-0.005，native-risk AUGRC 与 Risk@70 relative reduction 均 >=5%，且方向一致；失败则不得称 deployable。"
  - gate_id: G4_THREE_SEED_AND_STAGE_B_ELIGIBILITY
    rule: "仅 G2/G3 通过后补 seeds1/2。两个数据集至少2/3 seeds逐项通过G2，pooled mother-image bootstrap CI_low>0，fixed AR x size bins 不由 near-square/scale 驱动；参数增加 <=5%、端到端 latency增加 <=15%。全部通过才输出 PROCEED_PEF_STAGE_B。"
early_stop_conditions:
  - "G0 在一次合理环境/evaluator修复后仍失败：NOT_ADJUDICATED_ASSET_ENV。"
  - "PEF energy 不依赖 candidate-aligned feature、候选平移不满足周期/旋转变换、risk 梯度不到达 sampler/scorer、或退化成 affine delta/scalar head：NOT_ADJUDICATED_IMPLEMENTATION。"
  - "G1 任一数据集不打赢 DIRECT_DIST/SCALAR_QUALITY/VM-like native boundary：REJECT_PEF_METHOD，禁止端到端训练。"
  - "G2 任一数据集失败：REJECT_PEF_METHOD，禁止补 seed、跨域门与 clean endpoint。"
  - "G3 任一方向完全失败：停止 deployable claim；不得在目标域拟合后改口。"
kill_conditions:
  - "读取或触碰 DOTA-v2.0 val、SODA-A official test、r047/r048 T_audit semantic fields 或未登记 clean endpoint。"
  - "使用目标 val GT 做温度、阈值、候选角数量、loss weight、epoch、seed 或风险分数选择。"
  - "修改 frozen split、formal/exploratory 身份、门槛或风险定义，丢弃失败数据集/seed，或把 AQE/O2 式直接角度分布、PQA 式 scalar quality、FRED 式一般旋转等变包装成 PEF 创新。"
  - "复活 CORA-v1 affine head、Q-SetOD/OER/SAUR/AHC/P2C/crop-head，或只对旧预测做 post-hoc 重排。"
  - "伪造训练、checkpoint、指标、manifest、测试或完成状态。"
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

# 050：PEF-OBB 周期证据场 Stage A

## 1. 核心创新与边界

r049 的真实负结果说明：从同一 feature 直接回归一个 scalar harm，或用 `base+slope*delta` 构造反事实，不足以形成可信角度风险。r050 不修补 CORA-v1，而是改变可观测量：

> **Periodic Evidence Field (PEF)** 对同一预测实例构造覆盖 `theta mod pi` 的候选角环。每个候选角都真正改变 rotated sampling grid，并从 detector feature/image evidence 重新取样；共享 scorer 输出整条周期能量曲线。曲线的 mode/局部期望用于角度修正，mode 周围概率质量与尾部概率直接作为 native orientation risk。

创新点不在“角度分布”四个字，而在 **candidate-conditioned visual evidence**：风险来自不同候选方向对实际像素/feature alignment 的解释力，不来自 detection confidence、GT-conditioned post-hoc selector 或与候选无关的标量头。共享 scorer 与 circular shift 结构保证同一视觉证据旋转时能量场相应平移；它能够表达多峰、V形和周期结构，不受 r049 affine 参数化限制。

最近邻边界必须在实现报告中逐项对照：

- AQE, TGRS 2023（DOI `10.1109/TGRS.2023.3292111`）：已做 angle distribution 与 angle quality；PEF 必须证明 candidate feature resampling 相对 equal-budget direct distribution 的增量。
- FRED, AAAI 2024（DOI `10.1609/aaai.v38i4.28069`）：已做全检测器旋转等变；PEF 不宣称一般 equivariant detector，只主张 orientation evidence likelihood 与 reliability。
- PQA, AAAI 2026（DOI `10.1609/aaai.v40i16.38411`）：已做 pixel-level scalar localization quality；PEF 必须区分完整 orientation candidate field 与 scalar IoU quality。
- O2-RT-DETR, TGRS 2026 / arXiv `2603.15497`：已做 angle-distribution refinement；PEF 不把 distribution/refinement 本身当创新。

## 2. 方法冻结

宿主固定为 r043 valid PSC detector，第三方源码只读。工程细节允许服务器按真实接口调整，但以下科学结构不可变：

1. 对每个正样本/保留候选固定 `(cx,cy,w,h,class)`，构造统一 `K` 个 `theta mod pi` candidates；K、局部残差表示与采样分辨率只能用 train-only finite/coverage smoke 冻结，不能看 val reliability 选择。
2. 每个 candidate 使用同一权重 rotated sampler 在 FPN/regression feature 上取 candidate-aligned grid/tokens；scorer 对每个 candidate 独立共享，不能直接读取 candidate index 或 detection score。
3. energies 经 circular softmax 得到 `q(theta|F,B)`；GT 只用于 train proper circular likelihood/soft target。允许一个连续 residual decoder，但不能另挂用 GT harm 训练的 scalar risk head作为主分数。
4. native risk 固定为 q 的 circular tail mass/expected deviation，由 train-only 选择一个并写入 `METHOD_FREEZE.json`；推理无 GT、无目标域 calibration、无 score fusion。
5. 主输出同时包含原 angle、PEF refined angle、完整 q/native risk；以便分别验证 correction 与 selection，而不是靠 NMS 混在一起。

必须实现 equal-budget `DIRECT_DIST`（相同输入 feature，直接输出 periodic bins但不重采样）和 `SCALAR_QUALITY`（相同 feature 预测 angle harm/quality）两个强边界；VM-NLL 与 detection score 作为已有边界。若官方 PQA/AQE 代码可在允许 third_party 范围内可靠获得，可加为 secondary baseline，但不能为等代码无限等待或以不忠实复现冒充官方结果。

## 3. 数据与统计口径

只使用已消费的 DIOR-R 与 SODA-A development train/val，延续 r043 的 split/evaluator/checkpoint。DOTA-v2.0 val、SODA official test 与旧 T_audit 全部密封。

主域为 class-aware rotated-IoU>=0.5 matched TP 且 GT AR>=2.1；同时报告 all-AR 与 fixed size x AR bins。orientation harm 固定为 le90 long-side angle error/90。AUGRC/Risk@70 使用同一 whole-tie实现；门槛使用相对改善 `(baseline-method)/baseline`，避免 r049 的量纲错误。bootstrap 以 mother image 聚类、10,000 replicates、seed `20260819`。

## 4. 执行顺序

### Task 0：启动与 parity

- HTTPS fast-forward 到精确 dispatch commit；核验 `server-primary`、plan/blob/SHA、四卡、唯一报告路径，先写唯一 `STARTED.json`。
- 第一动作读取 `pth_data/readme.md`，登记两个 valid PSC host 的 dataset/split/backbone/schedule/batch/lr/BN/framework/checkpoint sha256。
- 完成 DIOR-R/SODA-A identity AP50/AP75 parity。

### Task 1：真实 PEF、结构测试与冻结头 cheap gate

- 实现只放项目内 `experiments/r050_pef_obb/` 与 `configs/r050_pef_obb/`。
- tests 至少覆盖：pi-periodicity/circular shift；rotate-one-bin 后 energy vector 对应平移；非角 box/class 字节不变；candidate-aligned feature mutation 确实改变对应 energy；把所有 candidate feature 置同后 field 失去辨别力；q 归一化；no-GT inference；risk 对人工展宽分布严格变大；梯度到 sampler/scorer；finite sensitive ops。
- 先冻结 host，只训练相同参数/step 的 DIRECT_DIST、SCALAR_QUALITY、PEF heads。四卡 smoke 通过后冻结 `METHOD_FREEZE.json`；DIOR 过 G1 才跑 SODA G1。

### Task 2：端到端 seed0 双数据集门

- 只有 G1 双过才运行共同预算的 CONT/DIRECT_DIST/SCALAR_QUALITY/PEF；每 epoch full-val，保存 best/latest、raw q/native risk/matched rows。
- 严格执行 G2；任何一数据集失败即正常早停，不补 seeds、不调风险定义。

### Task 3：无目标域 GT transfer 与三 seeds

- 只有 G2 双过才做两个方向冻结 transfer；目标域零训练、零 calibration。
- G3 通过后才补 seed1/2、fixed bins、效率与完整 bootstrap。通过 G4 才进入另轮第二 detector family 与 clean endpoint Stage B。

### Task 4：交付

至少交付 method freeze、configs、tests、训练/评估日志、每臂 full-val 表、raw q schema、matched rows、risk/AP/angle-error表、cross-transfer表、bootstrap/fixed-bin/efficiency（若到对应门）、manifest、sha256、独立 validator、mutation summary、`gate.json` 与中文决策报告。大 checkpoint 可按既有规则登记为服务器持久化可再生资产，不得伪称跨机已闭合。

服务器可自主修复普通路径、依赖、AMP、evaluator、进程监督和非法标注问题；只要不改变上述方法本质、数据、对照、门槛和信息墙，不需要为小工程问题停下来请示。科学结构、split、门槛、clean endpoint 与 claim 边界不得自行更改。

聊天回执严格两行：第一行“执行完毕”或“未执行完毕”；第二行唯一服务器报告路径。

## 5. 期刊映射

- `PROCEED_PEF_STAGE_B`：恢复 **JPRS candidate / strong TGRS route**；仍需下一轮第二 detector family、第三域或 sealed clean endpoint 才能称 ready。
- `REJECT_PEF_METHOD`：维持 **strong JSTARS / Remote Sensing**，低于合法目标；PEF 停止，不靠调阈值、补 epoch/seed 或 score fusion 续命。
- 技术未裁决：只修资产/实现；没有真正完成就必须回执“未执行完毕”。

