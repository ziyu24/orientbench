---
schema_version: 2
business_instruction: "043"
plan_id: b-r043-saur-obb-stagea-20260818
dispatch_id: orientbench-b-r043-saur-obb-stagea-20260818
initiator: B
activation_authorization:
  mode: owner_only
  delegate: null
  reference: null
closure_authorization:
  mode: owner_only
  delegate: null
  reference: null
base_sha: d062235a13dfa64f1bb06f83cb23f903414c613f
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-18：『给出顶刊的方案，让服务器去执行，开始。』"
scientific_snapshot:
  primary: d062235a13dfa64f1bb06f83cb23f903414c613f
  prior_method_state: "r042 ACCEPT_EXECUTION/KILLED/REJECT_OER_METHOD；旧 selector、Q-SetOD、OER/OER-D 不得复活"
  venue_state: "当前 strong-JSTARS/Remote-Sensing；只有全新检测器内生方法取得跨数据集正向证据才保留 TGRS/JPRS 路线"
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r043-saur-obb-stagea-20260818/SERVER_EXECUTION_REPORT.md
read_set:
  - AGENTS.md
  - dis/governance/roles/SERVER.md
  - dis/coordination.json
  - dis/plans/B/b-r043-saur-obb-stagea-20260818/sug.md
  - top_journal_v3_reaudit_055/configs/r1_angle_coder/**
  - top_journal_v3_reaudit_055/reports/r1_angle_coder_matrix.csv
  - top_journal_v3_reaudit_055/reports/k2_angle_coder_seed_results.csv
  - top_journal_v3_reaudit_055/docs/k2_angle_coder_go_no_go_report_067.md
  - measure_fix_v2/track_a_pkg/instrumented_psc_head.py
  - top_journal_v3_reaudit_055/paper_B_psc_mechanism/**
  - configs/**
  - orientbench/**
  - scripts/**
  - /home/rspip/cqc/pro/study/pth_data/**
  - /home/rspip/cqc/data/DIOR-R/**
  - /home/rspip/cqc/data/SODA-A/**
write_set:
  - outputs/persistent_artifacts/orientbench_saur_stagea_r043_20260818/**
  - top_journal_v3_reaudit_055/saur_stagea_r043_20260818/**
  - audit_bundles/r043/**
  - dis/server_reports/orientbench-b-r043-saur-obb-stagea-20260818/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute:
    gpu_count_max: 4
    gpu_hours_max: 192
    cpu_core_hours_max: 448
  wall_time:
    seconds_max: 172800
  data:
    allowed_dataset_ids:
      - DIOR-R-train-val-readonly
      - SODA-A-train-val-readonly
      - existing-PSC-checkpoints-and-configs-readonly
      - repository-tracked-evidence-readonly
    read_bytes_max: 4398046511104
    write_bytes_max: 536870912000
  write:
    allowed_paths:
      - outputs/persistent_artifacts/orientbench_saur_stagea_r043_20260818/
      - top_journal_v3_reaudit_055/saur_stagea_r043_20260818/
      - audit_bundles/r043/
      - dis/server_reports/orientbench-b-r043-saur-obb-stagea-20260818/
      - claude_code_and_supervisor.md
    bytes_max: 536870912000
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
conflict_keys:
  - server-execution-slot
  - dis/sug.md
  - gpu-all-four
  - outputs/persistent_artifacts/orientbench_saur_stagea_r043_20260818
gates:
  - gate_id: G0_REAL_ASSET_AND_HOST
    rule: "DIOR-R 与 SODA-A 的 PSC baseline checkpoint/config/dataset 必须真实存在；identity evaluator 必须在任一训练前复现各自归档 AP50，绝对差<=0.02。路径、config import、AMP 与 launcher 等工程问题允许现场修复并继续，不得把可修工程问题当科学早停。"
  - gate_id: G1_METHOD_IS_REAL
    rule: "SAUR 必须在检测头内部新增独立 residual mean 与 concentration 输出；训练使用 axial proper loss 与连续 symmetry identifiability，不得退化为旧 OER/几何特征重排、GT-at-inference、仅改 score 或对结果表离线拟合。"
  - gate_id: G2_STAGE_A_SURVIVAL
    rule: "相对 baseline 与 budget-matched continuation 中较强者，SAUR 在 DIOR-R、SODA-A 两个 development val 均须满足：AP50下降<=0.002；AP75提升>=0.005；matched-TP mean le90 angle error 相对下降>=5%；以 SAUR 原生 orientation reliability 排序的 normalized AUGRC 相对下降>=10%，且 mother/image-cluster bootstrap 的平均改善95% CI_low>0。两数据集全部满足才输出 PROCEED_SAUR_STAGE_B；否则完整执行后输出 REJECT_SAUR_METHOD。"
early_stop_conditions:
  - "任一真实 baseline 在完成合理路径/config/evaluator 修复后仍无法复现 AP parity，输出 NOT_ADJUDICATED_ASSET_HOST 并停止；不得用假数据替代。"
  - "100-iteration smoke 出现 NaN/OOM 时先按训练稳定性常规修复一次（fp32 sensitive op、grad clip、batch/accumulation等价调整）；仍失败才输出 NOT_ADJUDICATED_TECHNICAL。"
  - "DIOR-R 与 SODA-A 完整 Stage A 得到 REJECT_SAUR_METHOD 后停止，不扩 DOTA/FAIR1M/更多架构、不调 gate。"
kill_conditions:
  - "读取或触碰 DOTA-v2.0、SODA-A official test、任何 test label 或新增数据集；本轮只准 DIOR-R/SODA-A train+val。"
  - "把 val angle error、val GT、目标实例身份、旧 r042 label/预测作为训练特征、超参选择或可靠性分数输入。"
  - "复活 selector/Q-SetOD/OER/OER-D，修改冻结门槛，挑 seed、丢弃负数据集，或用更多训练预算替代 budget-matched control。"
  - "伪造训练、推理、GPU、指标、checkpoint、manifest 或完成状态。"
completion_mapping:
  full_completion:
    execution_status: complete
    receipt_first_line: 执行完毕
  gated_early_stop:
    execution_status: complete
    receipt_first_line: 执行完毕
  failure_early_stop:
    execution_status: incomplete
    receipt_first_line: 未执行完毕
  partial:
    execution_status: incomplete
    receipt_first_line: 未执行完毕
  protocol_drift:
    execution_status: incomplete
    receipt_first_line: 未执行完毕
---

# 043：SAUR-OBB 检测器内生方向分布头 Stage A 生死门

## 1. 主要矛盾

r042 已决定性否决事后 OER。当前项目缺的不是更多审计，而是一个能同时改善**角度本身**与**原生方向可靠性**的检测器级正向方法。

本轮只回答一个问题：

> 在不使用目标 val/test 标签调参的前提下，显式区分几何不可辨识性与图像证据不确定性的方向分布头，能否在 DIOR-R 与 SODA-A 上同时改善 AP75、角度误差和风险排序？

过门只取得 Stage B 多架构/三种子/清白端点资格，不自动宣称 JPRS/TGRS ready；不过即终止本方法，不准换阈值续命。

## 2. 方法冻结：SAUR-OBB

SAUR = Symmetry-Aware Uncertainty and Refinement。宿主固定为已有 PSC detector；保留中心、尺度、类别与现有主检测分支，在 angle branch 的正样本特征上增加轻量 residual-distribution head：

1. 输出 axial residual mean vector `(cos 2delta, sin 2delta)`，修正最终方向；
2. 独立输出 concentration `kappa>0`，作为原生方向证据不确定性；
3. 训练使用 doubled-angle circular proper likelihood；
4. 用无阈值连续 identifiability `g=(w-h)^2/(w^2+h^2+eps)` 分解几何歧义：`g` 高时拟合方向似然，`1-g` 高时约束分布趋向低 concentration；训练用 GT 尺度，推理必须只用 predicted `w,h`；
5. 原生 reliability 只能由预测 `kappa` 与 predicted-geometry `g_pred` 组成，主结果不得混入 detection score；score fusion 仅可作 secondary；
6. 输出修正框而不是仅重排旧框。新增参数量、FLOPs、延迟必须报告。

若实现中 exact Bessel/von-Mises 在 AMP 下不稳，可用数值稳定的 axial proper scoring 等价实现；服务器可自行修复工程细节，但不得删除 residual correction、独立 concentration 或 symmetry decomposition 三项科学结构。辅助 loss 权重只能依据 train loss/gradient stability 确定一次，禁止查看 val risk 后调参。

## 3. 对照与数据

固定两个数据集：DIOR-R train/val、SODA-A train/val。禁止 test。

每个数据集使用同一归档 PSC 起点，运行三个 budget-matched arm，seed=0：

- `BASE`: 原始归档 checkpoint，只重放 identity eval；
- `CONT`: 原 PSC 按与 SAUR 相同的追加迭代、optimizer、augmentation、global batch 继续训练；
- `SAUR`: 从同一 checkpoint 初始化，按同预算训练 SAUR；
- `NAIVE` 可作为不增加总预算的必要消融：保留 residual distribution，但令 `g=1`，用于判断收益是否来自 symmetry decomposition；它不参与 G2 的最强 baseline 选择。

默认4卡 global batch按原配置线性对齐；优先复用 `/home/rspip/cqc/pro/study/pth_data` 的 checkpoint/config。服务器先选择与归档 K2/PSC 配置基本一致且能复现 AP 的真实资产，不重新从零训练整个 detector。追加预算以3个epoch或原1x schedule的25%两者较小者为上限，并对 CONT/SAUR 完全一致。

## 4. 执行任务

### Task 0：启动与资产核验

- HTTPS fast-forward 到精确 dispatch commit；核验 `server-primary`、coordination、plan/mirror hash、四卡资源。
- 写唯一 `STARTED.json` 后执行。
- 定位 DIOR-R/SODA-A 的真实 PSC config、checkpoint、dataset root、环境与 evaluator；记录绝对路径和 SHA-256。
- 两个 BASE identity eval 过 G0 后才训练。

### Task 1：实现与 smoke

- 所有新增代码/config 放在 `top_journal_v3_reaudit_055/saur_stagea_r043_20260818/`，通过 `custom_imports` 或等价非侵入方式接入宿主。
- 写最小单元测试：双角周期、`w/h` swap 对 `g` 不变、near-square 低 concentration 方向、无 GT inference、梯度有限。
- DIOR-R 100 iteration 四卡 smoke；合理修复 NaN/OOM/config/path 后继续，不因普通工程问题停止。

### Task 2：真实训练与评估

- 依次完成 DIOR-R 的 CONT/SAUR（及 NAIVE 必要消融）和 SODA-A 同构运行；GPU空闲时始终使用4卡。
- 保存训练日志、环境、config、checkpoint、每轮 eval；不得只报最好 checkpoint，主结果固定最后 checkpoint，best 仅描述。
- full-val evaluator 输出 AP50/AP75；同时生成 matched TP 表，计算 le90 angle error、native reliability 的 normalized AUGRC、Risk@70/90。
- bootstrap 单位为原图/母场景，不把实例视为独立样本；计算 SAUR 相对更强 baseline 的 paired improvement CI。

### Task 3：裁决与交付

必交：

- `method_spec.md`、实现代码、tests、四个主 run config；
- `asset_inventory.csv`、`training_runs.csv`、`fullval_metrics.csv`、`risk_metrics.csv`、`bootstrap_summary.csv`；
- `gate.json`，唯一 token 为 `PROCEED_SAUR_STAGE_B`、`REJECT_SAUR_METHOD` 或技术未裁决 token；
- checkpoint/大表保存在 persistent root，Git audit bundle 只提交小表、代码、配置、manifest；
- 服务器报告明确写正常结束或异常结束、两数据集逐项门槛、当前期刊等级与下一步。

最终提交并通过 HTTPS push。聊天回执严格两行：第一行“执行完毕”或“未执行完毕”；第二行唯一服务器报告路径。

## 5. 顶刊后续映射

- `PROCEED_SAUR_STAGE_B`：下一轮扩到至少3 detector families、3 seeds、FAIR1M/DOTA，并在全部方法冻结后才揭示清白 endpoint；目标 JPRS，TGRS 为次选。
- `REJECT_SAUR_METHOD`：当前仍低于 TGRS，不投稿低档期刊；停止本方法，重新寻找科学机制。
- 技术未裁决：只允许针对明确资产/实现根因修复一次，不改变方法或 gate。

