---
schema_version: 2
plan_id: b-r048-p2c-lift-directed-obb-stagea-20260819
dispatch_id: orientbench-b-r048-p2c-lift-directed-obb-stagea-20260819
initiator: B
business_instruction: "048"
base_sha: c49dcce2bbe9a10cddc5c04fb5548d456ca28991
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-19 在 B 明确 r047 不重跑、下一步必须是科学上完全不同的新方法或任务后回复：『推进下一步吧。』"
scientific_snapshot:
  current_defensible_level: STRONG_JSTARS_OR_REMOTE_SENSING
  legal_target: TGRS_OR_BETTER
  preferred_target: ISPRS_JPRS
  stopped_routes: "post-hoc selector, Q-SetOD, OER/OER-D, SAUR, axis-drift policy, AHC endpoint comparator"
  preserved_clean_endpoint: "r047 T_audit, 228 official HRSC test images, semantic fields unopened"
  new_increment: "probabilistic projective-to-circular lift that factorizes axial residual, bow/stern pole and intrinsic orientation reliability"
  target_route: P2C_LIFT_DIRECTED_OBB_STAGE_A
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r048-p2c-lift-directed-obb-stagea-20260819/SERVER_EXECUTION_REPORT.md
read_set:
  - "/home/rspip/cqc/pro/study/pth_data/readme.md and exact valid HRSC R50/LSKNet configs, logs and checkpoints, read-only"
  - "/home/rspip/cqc/data/dataset/HRSC2016 official train/val and r047 T_cal semantics as consumed development data; T_audit subject to the seal below"
  - "r047 partition IDs, development rows, execution verdict and existing image-only host artifacts, read-only"
  - "official CHPDet paper/code and ShipRSImageNet metadata for scope comparison only; no external dataset download in r048"
write_set:
  - experiments/r048_p2c_lift/**
  - outputs/persistent_artifacts/orientbench_p2c_lift_r048_20260819/**
  - audit_bundles/r048/**
  - docs/paper_jprs_r048/**
  - dis/server_reports/orientbench-b-r048-p2c-lift-directed-obb-stagea-20260819/**
  - /home/rspip/cqc/pro/study/third_party/orientbench_p2c_env/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 4, gpu_hours_max: 120, cpu_core_hours_max: 512}
  wall_time: {seconds_max: 172800}
  data:
    allowed_dataset_ids: ["HRSC2016-existing-readonly", "existing-valid-HRSC-baselines-readonly", "r047-consumed-development-artifacts-readonly", "r047-unopened-T_audit-sealed"]
    read_bytes_max: 1649267441664
    write_bytes_max: 161061273600
  write:
    allowed_paths: ["experiments/r048_p2c_lift/", "outputs/persistent_artifacts/orientbench_p2c_lift_r048_20260819/", "audit_bundles/r048/", "docs/paper_jprs_r048/", "dis/server_reports/orientbench-b-r048-p2c-lift-directed-obb-stagea-20260819/", "/home/rspip/cqc/pro/study/third_party/orientbench_p2c_env/", "claude_code_and_supervisor.md"]
    bytes_max: 161061273600
  network:
    allowed: true
    allowed_endpoints: ["https://github.com/ziyu24/orientbench.git", "https://github.com/open-mmlab/", "https://pypi.org/", "https://files.pythonhosted.org/", "https://download.pytorch.org/", "https://repo.anaconda.com/", "https://conda.anaconda.org/"]
conflict_keys: ["server-execution-slot", "dis/sug.md", "gpu-all-four-p2c-training", "HRSC-r047-T_audit-semantic-seal"]
gates:
  - gate_id: G0_FORMAL_ENVIRONMENT_AND_ASSET
    rule: "dedicated compatible environments load the registered R50 and LSKNet hosts without version-string spoofing; exact backbone mapping, AP parity on consumed data, T_audit unopened status and all required method/baseline implementations pass before training."
  - gate_id: G1_CONSUMED_DEVELOPMENT_SUPERIORITY
    rule: "after val-only model selection, the single frozen P2C-Lift model beats the strongest learned baseline on both official val and consumed T_cal by accuracy delta >=0.02, baseline-minus-P2C AUGRC >=0.01 and baseline-minus-P2C mean circular error >=3 degrees, while retaining gains under frozen 5/10/15-degree axis jitter; otherwise stop without opening T_audit."
  - gate_id: G2_MODEL_AND_POLICY_SEAL
    rule: "model, baselines, intrinsic confidence, host inference, T_cal threshold, code/config/checkpoints/logs and audit inputs are committed and remotely visible before T_audit semantics open."
  - gate_id: G3_TAUDIT_DIRECTED_HEADING
    rule: "on untouched T_audit GT boxes, P2C-Lift accuracy >=0.88, paired gain over the sealed strongest learned baseline >=0.02 with image-bootstrap 95% lower >0, baseline-minus-P2C mean circular error >=3 degrees with 95% lower >0, and baseline-minus-P2C AUGRC >=0.01 with 95% lower >0."
  - gate_id: G4_TAUDIT_TWO_HOST_RELIABILITY
    rule: "on both registered hosts, matched-detection heading accuracy >=0.82; equal-host paired accuracy gain >=0.02 and AUGRC reduction >=0.01 with 95% lower >0; val/T_cal-sealed Risk@70 complete-image UCB <=0.15 on each host; detector AP50/AP75 bytes and values unchanged."
  - gate_id: G5_AUDIT_NOVELTY_AND_ROUTE
    rule: "independent raw-row metric recomputation, transformation-group tests, six real mutations, complete artifact manifest and closest-prior review pass. Only all-pass emits PROCEED_P2C_LIFT_STAGE_B; Stage B still requires source-disjoint FGSD2021/ShipRSImageNet external validation."
early_stop_conditions:
  - "no honest compatible environment can load either registered host and reproduce consumed-data AP parity; version-guard spoofing or untracked runtime patch is forbidden."
  - "P2C-Lift does not pass every G1 relative gain on both consumed development partitions; stop before T_audit and do not tune against the failed component."
  - "first formal epoch is <0.60 heading accuracy while strongest baseline is >=0.65, nonfinite loss occurs, transformation laws fail, or the method collapses to a whole-crop classifier with no axial/pole distribution."
  - "after the remotely visible seal, any G3 primary CI crosses zero or any G4 host/reliability condition becomes logically impossible; stop without changing method, split, confidence or gate."
kill_conditions:
  - "open any r047 T_audit header_x/header_y, derived heading or outcome before MODEL_AND_POLICY_SEAL is committed and pushed; use T_audit for architecture, checkpoint, threshold, temperature, environment, retry or baseline choice."
  - "reuse r047 AHC checkpoints, revive AHC endpoint-comparator claims, or present feature concatenation alone as P2C-Lift."
  - "download FGSD2021, ShipRSImageNet or any new dataset in r048; external data belongs only to a post-pass Stage-B dispatch."
  - "modify HRSC XML/images/split/partition bytes, registered detector weights, prior frozen evidence or numeric gates; train/fine-tune a host detector."
  - "claim physical motion, AIS course, JPRS/TGRS readiness, novelty of 360-degree ship heading itself, or novelty over CHPDet before source-disjoint Stage B."
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: "执行完毕"}
  gated_scientific_early_stop_after_complete_required_stage: {execution_status: complete, receipt_first_line: "执行完毕"}
  environment_or_asset_failure: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
  partial_proxy_or_protocol_drift: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
---

# r048：P2C-Lift reliable directed OBB Stage-A

## 1. 新方法与最近邻边界

普通 OBB 的长轴角属于投影圆 `RP1`，即 `theta == theta + pi`；舰船语义航向属于圆 `S1`，需要区分 bow/stern。r048 的核心不是再比较两个 endpoint，而是学习从轴向分布到完整方向分布的 **probabilistic projective-to-circular lift**：

```text
axial state:     theta0 + delta  (mod pi)
pole sheet:      s in {0, 1}
full heading:    phi = theta0 + delta + s*pi  (mod 2*pi)
p(phi|I,B) = q_axis(delta|I,B) * q_pole(s|delta,I,B)
```

CHPDet 已经用 center/head point 做 360°舰船检测，所以“预测船头”和“把角度扩到 360°”不是本项目创新。P2C-Lift 待验证的贡献是：对任意既有 OBB host 的 plug-in double-cover factorization、轴/极性不确定性分解、严格几何变换一致性和 intrinsic orientation-risk ranking。若它只等价于 whole-crop/concat classifier，或打不赢 direct-S1/headpoint baseline，就没有顶刊方法贡献。

Stage-B 首选外部资源是 CHPDet 官方 FGSD2021，或 ShipRSImageNet 中排除 HRSC来源并按源图去重的子集。ShipRSImageNet 含 HRSC和FGSD重标数据，禁止把重叠样本当独立外部验证。r048 不下载这些数据。

## 2. 数据身份与 T_audit 墙

- training: official HRSC train。
- model/config selection: official HRSC val；最多三个预先声明 capacity 配置，只按 val 选择一个。
- consumed confirmation: r047 T_cal；只对 val 选出的单一 final candidate 和所有 baselines 评价一次，不据 T_cal 改模型。
- sealed audit: r047 `T_audit_ids.txt` 的 228 images；semantic fields 仍未打开。

official val 与 T_cal 均标注为 consumed development，不形成独立统计 claim。只有 G1 完整通过，才允许写并推送 `MODEL_AND_POLICY_SEAL.json`，随后一次打开 T_audit。服务器先生成 `STARTED.json` 和 access log；若发现任何既有 T_audit semantic cache/value，执行不完整并停止。

## 3. P2C-Lift architecture

共同 backbone 使用注册 HRSC Oriented R-CNN R50 权重，逐 tensor 映射并记录。GT/predicted OBB rectification 统一为 `192x64`；全局 crop token `g`、左右 `64x64` endpoint tokens `e_minus/e_plus`，以及 `sum=e_plus+e_minus`、`diff=e_plus-e_minus` 进入一个轻量 cross-token transformer。方法必须同时保留 global appearance 与 signed local evidence，不施加 r046/r047 AHC 的 hard antisymmetry。

输出三部分：

1. axial residual distribution：在 doubled angle 上预测 mean direction 与 concentration `kappa_axis`，用 von-Mises NLL 表达 `delta mod pi`；
2. conditional pole distribution：预测 `q_pole(s)`，用 Bernoulli proper loss区分 bow/stern；
3. auxiliary normalized center-to-head 2D vector：只作训练辅助和可解释性，不替代 pole distribution。

full heading distribution 按上述 lift 组合。点估计由 circular Bayes action给出；intrinsic confidence 固定由 axial concentration 与 pole posterior共同导出，不使用 detection score。对 horizontal flip、vertical flip、90/180/270° rotation，full distribution 必须按解析 group action变换；训练加入 distribution-level equivariance KL，但不强制内部 feature逐元素相等。

损失权重只允许三个预声明 capacity/config候选，具体优化、缓存、AMP和microbatch可由服务器在 global batch不变前提下自决。所有最终公式、config菜单和随机种子必须在任何 formal run 前写入 `METHOD_FREEZE.json`；之后只能修复不改变输出的机械 bug。

## 4. 强 baselines与公平预算

同一 backbone初始化、crop、增强、epoch/global batch和可训练参数量 `±2%`：

1. `WHOLE_CROP_BINARY`；
2. `CONCAT_ENDPOINT_BINARY`；
3. `HEADPOINT_2D`：真实 normalized center-to-header vector regression；
4. `DIRECT_S1_VM`：whole-crop直接预测 full-heading von-Mises distribution，不做 projective/pole factorization；
5. P2C ablations：去 equivariance、去 axial uncertainty、去 global token，只用于拆贡献，不参与 strongest baseline菜单。

strongest learned baseline 只按 val accuracy、AUGRC、mean circular error和固定顺序选择。必须报告参数/FLOPs/latency；不得把不完整 CHPDet 复现当 baseline。CHPDet 使用官方论文/代码结果界定任务近邻，Stage B 再决定是否运行官方实现。

## 5. 训练、环境和 consumed-development gate

为两个 host 创建或复用**真实兼容**专用环境，记录 Python/PyTorch/CUDA/MMCV/MMDet/MMRotate及安装来源；禁止修改 `__version__` 绕 guard。先在 consumed val/T_cal 做 host AP parity，失败则环境/资产失败，不进入科学训练。

训练默认四卡 DDP，200-iteration smoke 后正式最多 30 epochs，每 epoch评估 val；保存 best/latest，日志记录命令、四 rank、lr schedule、loss components、accuracy、circular error、NLL/Brier/ECE/AUGRC。大于 GitHub 单文件上限的 checkpoint 必须压缩或确定性切成 `<95 MB` chunks并随 manifest推送，不能只在 server seal中引用不存在的文件。

G1 使用 val选出的唯一模型在 T_cal 一次确认。P2C-Lift 必须相对同一个 strongest baseline同时满足：

- val 和 T_cal accuracy delta 各 `>=0.02`；
- val 和 T_cal AUGRC reduction 各 `>=0.01`；
- val 和 T_cal mean circular error reduction 各 `>=3°`；
- frozen axis jitter `5°/10°/15°` 下三个档位方向均正，且至少两个档位 accuracy delta `>=0.02`。

任一不满足，终态 `REJECT_P2C_LIFT_DEVELOPMENT`，不打开 T_audit。通过后封存模型、strongest baseline、所有 temperatures、T_cal Risk@70 thresholds、两个 host image-only predictions及 metric code。

## 6. T_audit唯一正式评价

seal 远端可见后只打开一次 T_audit semantic fields。GT-box 与 R50/LSKNet class-correct one-to-one rIoU>=0.50 matched views均报告：heading accuracy、360° mean/median angular error、NLL、Brier、ECE、AUGRC、Risk@70/80/90、coverage及 valid-label coverage。

统计单位是 mother image；paired 10,000 bootstrap，seed `20260819`，两 host同 replicate image multiplicity并等权平均。T_cal封存的 threshold/temperature原样应用；complete-image bounded loss的 one-sided Hoeffding-Bentkus UCB按 r048 独立实现与 validator复算。无 retained/eligible instance images按协议显式进入 coverage/accounting，不静默删除。

G3/G4 按 front matter逐项判定。P2C confidence还必须在相同 heading predictions上打赢：detection score、softmax max、direct-S1 concentration和strongest baseline confidence；否则不得称 intrinsic reliability。

## 7. 独立审计与路线映射

Implementation A 输出全部 per-instance/per-image raw rows。Validator B 不 import A 的 model-selection、metric、HB/bootstrap函数，从 raw predictions重算；代码相似度 `<=0.80`。六项真实 subprocess mutations至少覆盖：projective sheet、group-action label、confidence/error pairing、T_audit member、sealed threshold、host match key；pristine=0且 mutated全非零。

manifest记录所有代码/config/log/checkpoint chunks/raw rows/predictions/seals的 path/bytes/SHA/can_recompute。最终报告必须是 schema-2，列明每个 gate、执行状态和科学状态；用户回执仍严格两行。

终态：

- `PROCEED_P2C_LIFT_STAGE_B`：仅 G0-G5 全过；下一 dispatch 获取 FGSD2021或ShipRS来源去重子集，做跨数据/传感器、leave-dataset无GT再标定验证及CHPDet比较。
- `REJECT_P2C_LIFT_DEVELOPMENT`：G1失败，T_audit保持未开，停止方法。
- `REJECT_P2C_LIFT_METHOD`：T_audit任一核心门失败，停止且不调参救场。
- `INCOMPLETE`：环境、资产、partial、proxy、信息泄漏或协议漂移；不得伪装科学负结果。

即使 Stage A 全过也只能恢复 **JPRS/TGRS potential**，不能声称 ready；只有 source-disjoint Stage B 和完整论文证据闭合后才重新评档。
