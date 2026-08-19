---
schema_version: 2
plan_id: b-r045-prospective-axis-drift-decision-20260818
dispatch_id: orientbench-b-r045-prospective-axis-drift-decision-20260818
initiator: B
business_instruction: "045"
base_sha: 11abe6f63766b5d8114b7fcb6ac80da4b4fd6170
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-18：『给出顶刊的方案，让服务器去执行，开始。』；r044 完成后再次报告『服务器执行完毕。』，授权沿唯一顶刊补强路线继续。"
scientific_snapshot:
  r044_terminal: NOT_JPRS_READY
  r044_reason: "双内部红队 novelty=3/5；缺 prospective held-out remote-sensing decision study 与 domain-shift risk verification"
  current_defensible_level: STRONG_JSTARS_OR_REMOTE_SENSING
  legal_target: TGRS_OR_BETTER
  target_venue: ISPRS_JPRS
  forbidden_rescues: ["new detector head", "selector retry", "extra in-distribution matrix row", "language-only revision", "clean endpoint consumption"]
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r045-prospective-axis-drift-decision-20260818/SERVER_EXECUTION_REPORT.md
read_set:
  - "/home/rspip/cqc/pro/study/pth_data/readme.md and exact valid baseline config/log/checkpoint records, read-only"
  - "existing DIOR-R and HRSC2016 predictions/matched artifacts from r028/r040/r041 and other Git-tracked or manifest-pinned persistent artifacts, read-only"
  - "existing frozen D_cal/D_audit split files only; bytes and SHA-256 are pinned below"
  - "DIOR-R and HRSC2016 existing dataset roots, read-only and only at the staged opening points below"
write_set:
  - experiments/r045_axis_drift/**
  - outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/**
  - audit_bundles/r045/**
  - docs/paper_jprs_r045/**
  - dis/server_reports/orientbench-b-r045-prospective-axis-drift-decision-20260818/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 4, gpu_hours_max: 48, cpu_core_hours_max: 384}
  wall_time: {seconds_max: 86400}
  data:
    allowed_dataset_ids: ["DIOR-R-existing-endpoints-readonly", "HRSC2016-existing-endpoints-readonly", "existing-valid-baselines-readonly", "repository-and-manifest-pinned-artifacts-readonly"]
    read_bytes_max: 2199023255552
    write_bytes_max: 107374182400
  write:
    allowed_paths:
      - experiments/r045_axis_drift/
      - outputs/persistent_artifacts/orientbench_axis_drift_r045_20260818/
      - audit_bundles/r045/
      - docs/paper_jprs_r045/
      - dis/server_reports/orientbench-b-r045-prospective-axis-drift-decision-20260818/
      - claude_code_and_supervisor.md
    bytes_max: 107374182400
  network:
    allowed: true
    allowed_endpoints: ["https://github.com/ziyu24/orientbench.git"]
conflict_keys: ["server-execution-slot", "dis/sug.md", "gpu-all-four-if-reconstruction-needed", "r045-heldout-policy-seal"]
gates:
  - gate_id: G0_ASSET_AND_SPLIT_INTEGRITY
    rule: "pth_data readme readable; at least two and preferably all three frozen common architecture families have valid source/target configs, checkpoints, prediction provenance and AP parity; the four frozen split SHA-256 values match exactly."
  - gate_id: G1_PROSPECTIVE_POLICY_SEAL
    rule: "AP policy, orientation policy, source results, endpoint, risk/coverage/statistical rules and target architecture mapping are committed and pushed in POLICY_SEAL.json before any HRSC D_audit GT or outcome field is opened."
  - gate_id: G2_CONSEQUENTIAL_DECISION
    rule: "orientation policy must change architecture and/or select a nontrivial coverage in [0.70,0.90] relative to the AP-only full-coverage policy; otherwise stop before HRSC audit with NO_DECISION_CHANGE."
  - gate_id: G3_HELDOUT_TARGET_BENEFIT
    rule: "on sealed HRSC D_audit, paired image-bootstrap Delta continuous axis-drift loss = AP-policy minus orientation-policy is >=0.02 with 95% CI lower>0, and severe-event Delta is positive with CI lower>0."
  - gate_id: G4_SHIFT_RISK_AND_UTILITY
    rule: "orientation policy target one-sided 95% image-level UCB for severe risk <=0.10; eligible matched coverage >=0.70; AP50 is no more than 0.02 below AP policy; no target GT participates in threshold or architecture choice."
  - gate_id: G5_SENSITIVITY_AND_AUDIT
    rule: "benefit sign is positive for at least two of q={0.25,0.50,1.00} short-side cross-track thresholds, primary q=0.50 passes, independent recomputation and real mutations pass, and all artifacts persist with manifest/SHA."
early_stop_conditions:
  - "pth_data/readme.md missing or unreadable; any frozen split SHA mismatch; source/target common valid architecture count <2; necessary full predictions or matched geometry cannot be recovered without training."
  - "POLICY_SEAL missing/unpushed, target audit GT/outcome access before seal, or target D_cal access includes any GT/angle/match outcome field."
  - "orientation policy does not change the AP-only decision or selects coverage outside [0.70,0.90]; stop without opening HRSC D_audit outcomes."
  - "primary target benefit CI crosses zero, risk UCB exceeds 0.10, target AP50 survival fails, benefit is near-square-only, or any result requires changing q/risk/coverage/split after outcome access."
kill_conditions:
  - "modify frozen D_cal/D_audit bytes, thresholds from prior rounds, formal/exploratory labels, baseline weights, r044 manuscript/evidence, or any B/C-owned governance file."
  - "train or fine-tune a detector; download a new dataset; touch DOTA-v2.0 val or SODA-A official test; use target HRSC audit GT for fitting, model choice, threshold choice or candidate filtering."
  - "replace the endpoint, candidate set, effect size, bootstrap unit, seed or gate after target outcome access."
  - "write outside write_set, hide failed candidates, or claim theoretical distribution-shift guarantee from an empirical held-out check."
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: "执行完毕"}
  gated_early_stop: {execution_status: complete, receipt_first_line: "执行完毕"}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
  partial: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
  protocol_drift: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
---

# r045：prospective cross-domain axis-drift decision study

## 1. 科学问题

r044 已把论文写完整，但其严格 JPRS gate 正确地停在 novelty `3/5`。本轮只回答一个新问题：

> 在不使用目标域 GT 做选择的前提下，orientation-reliability protocol 能否改变一个真实的架构/阈值决策，并在 DIOR-R → HRSC2016 的遥感域转移中改善独立于 rectangle-IoU 容忍曲线的轴向应用损失，同时保持图像级风险与检测效用？

这不是新 detector、selector 或修复方法。它是 r044 红队指定的最小 prospective downstream decision study。DIOR-R 是 source，HRSC2016 是 sealed target；二者均为项目已消费数据集，不引入新数据或清白 endpoint。

## 2. 冻结应用端点：cross-track tip drift

对 eligible matched pair，令 `e in [0,90°]` 为 axial long-axis error，`a=L/H>=2.1` 为 GT aspect ratio。定义 predicted-axis 对 GT 长轴端点造成的归一化横向漂移：

```text
d_tip = min(1, (a / 2) * sin(e * pi / 180))
Z_q   = 1[d_tip > q]
```

主阈值 `q=0.50`：GT 长轴端点相对预测轴线横向偏移超过半个 GT 短边。敏感性只用 `q={0.25,1.00}`。这直接对应沿预测 OBB 轴线做目标切片、排列或对齐测量时的横向端点漂移；它不是 `delta_0.75(a)`、不是 rotated-IoU event，也不使用 observed pair IoU 定义严重性。

主连续损失为 `d_tip`。主二值风险为 `Z_0.50`。eligible population 固定为 class-correct one-to-one rotated-IoU>=0.5 match 且 GT `a>=2.1`；near-square 不进入主分析。每幅图像的风险为 retained eligible matches 中 `Z` 的均值；没有 retained eligible match 的图像记 0，同时必须满足目标 eligible coverage 下限，防止空选择获利。

必须给出数值非等价表：在冻结 AR 网格上比较 `asin(2q/a)` 的 axis-drift 角阈值与 `delta_0.75(a)`，只证明两 estimand 不相同，不包装成新理论。

## 3. 冻结数据、split 与候选策略

### 3.1 split bytes 不得改变

```text
outputs/bench_core/splits/D_cal_dior_trainval.csv
  sha256 f624a21451de394a35041af35c9a910c3a1bdc11fb5c942d15416e04e0e6f632
outputs/bench_core/splits/D_audit_dior_trainval.csv
  sha256 11c61be3a03c922b5e00e4cf9e866cf73e18eff44bd6b868b53f54612065669b
outputs/bench_core/splits/D_cal_hrsc_trainval.csv
  sha256 bbaf79002ad683893292101744e32e379d711f14ab7c187ae5bad42d2e37bdb0
outputs/bench_core/splits/D_audit_hrsc_trainval.csv
  sha256 55734ae8aa3f49350186fd066a761a54fe1a99921897012c5e59ca1fdf9f6679
```

文件缺失或 hash 不符直接 `NOT_ADJUDICATED_SPLIT_OR_ASSET`；禁止生成替代 split。

### 3.2 预注册 common architecture families

只考虑以下 source/target 都有既有 valid baseline 的 family：

1. `oriented_rcnn_r50_fpn_le90`
2. `oriented_rcnn_lsknet_s_fpn_le90`
3. `rotated_rtmdet_s_fpn_le90`

同 family 在 DIOR-R 与 HRSC2016 使用各自既有训练 checkpoint；本研究评估的是“从 source 选择 architecture family 后部署其 target-domain existing baseline”，不是同一权重零样本迁移。候选必须在 `pth_data/readme.md` 为 valid，且 config/log/pth、split、schedule、batch、lr、BN、mAP、framework、checkpoint SHA 全部登记。任何 family 任一域 AP parity 不通过则整族剔除；剔除只由预注册 asset/parity 规则决定，不得看 `d_tip`。剩余少于 2 族早停。

优先复用 r028/r040/r041 的 manifest-pinned full predictions/matched artifacts。若清理后缺失，可用同一 valid checkpoint/config 只做确定性推理重建；禁止训练/微调。推理重建时最多四卡并行，先做小批 parity smoke，再跑冻结 endpoint。

## 4. T0：pre-outcome asset seal

先提交 `STARTED.json`。随后只允许：

- 读 `pth_data/readme.md`、config/log/checkpoint metadata、prediction manifest/schema/header、split bytes；
- 计算 checkpoint/config/prediction/split SHA；
- 验证候选映射和 AP parity provenance；
- 禁止读取任何 HRSC D_audit GT、angle error、match outcome、risk 或历史新端点结果。

输出 `audit_bundles/r045/ASSET_SEAL.json`、`candidate_inventory.csv`、`access_log_preseal.txt` 并 commit/push。任何重建推理只能输出 predictions，不得打开 target audit GT。

## 5. T1：source DIOR-R policy construction

### 5.1 AP-only policy

以 source DIOR-R 已登记 baseline mAP 为唯一选择量，选择最高 mAP architecture family；tie-break 依次为 AP75、较低计算量、candidate 列表顺序。AP policy 使用 evaluator 原有 score floor，不做 orientation abstention，记 nominal coverage `1.0`。

### 5.2 orientation policy

只使用 detection score，不训练新 selector。对每个 candidate 在 source `D_cal` 上按预测分数选择 coverage grid：

```text
C = [0.90, 0.85, 0.80, 0.75, 0.70]
risk budget rho = 0.10
confidence delta = 0.05
familywise correction = delta / number_of_candidates
```

以完整图像为交换单位，对 `Z_0.50` 用 fixed-sequence Hoeffding-Bentkus one-sided UCB，从 0.90 向下找第一个 `UCB<=0.10` 的 coverage。没有 coverage 通过则该 candidate 不可选。随后在 source `D_audit` 上只报告预选 coverage 的 continuous `d_tip`、severe risk、UCB、eligible coverage 和 AP50；禁止回调 coverage。

orientation policy 从通过者中选择 source D_audit continuous `d_tip` 最低者；tie-break 为更高 coverage、较低 severe risk、较高 baseline mAP、candidate 顺序。AP policy与orientation policy、coverage、score quantile rule、全部 source 数字、代码/hash 必须写入 `POLICY_SEAL.json` 并单独 commit/push。

若 orientation policy 与 AP policy 同 architecture 且 coverage=1，或无 candidate 在 `[0.70,0.90]` 通过，输出 `NO_DECISION_CHANGE` 并停止；不得打开 HRSC D_audit outcome。

## 6. T2：sealed HRSC deployment

在 `POLICY_SEAL` 推送后：

1. 对所需 HRSC family 的 `D_cal` **仅读取全预测的 score/image/prediction id**，禁止读取 GT、match、angle、AR、IoU 或 risk 字段。
2. 用 source seal 的 coverage quantile 在 HRSC D_cal 无标签分数上确定数值 score threshold；AP policy 保持原 evaluator score floor。
3. 写 `TARGET_THRESHOLD_SEAL.json`，包含输入 prediction SHA、score-only column audit、阈值与命令，并单独 commit/push。
4. 只有 threshold seal 推送成功后，才可打开 HRSC `D_audit` GT，执行一次 class-aware matching、`d_tip/Z_q`、image-level risk、full evaluator AP50 与 bootstrap。

严禁 target audit GT 参与 candidate/parity filtering、score threshold、coverage quantile、endpoint/gate 选择。

## 7. T3：统计与唯一 gate

Bootstrap 固定：mother image/scene cluster，10,000 replicates，seed `20260818`；AP policy 与 orientation policy 在共同图像集合 paired resampling。主差：

```text
Delta_cont   = mean_d_tip(AP policy) - mean_d_tip(orientation policy)
Delta_severe = risk_Z0.50(AP policy) - risk_Z0.50(orientation policy)
```

PASS 必须同时满足：

1. 决策改变：architecture 改变或 orientation coverage 在 `[0.70,0.90]`，相对 AP full coverage 非平凡。
2. `Delta_cont >= 0.02` 且 paired 95% CI lower `>0`。
3. `Delta_severe >0` 且 paired 95% CI lower `>0`。
4. orientation policy target image-level `Z0.50` one-sided 95% UCB `<=0.10`。
5. target eligible matched coverage `>=0.70`。
6. orientation target AP50 不低于 AP policy target AP50 超过 `0.02`。
7. `q={0.25,0.50,1.00}` 至少两个点估计 benefit 为正，且主 `q=0.50` 满足全部正式条件。

唯一终态：

- `JPRS_DECISION_STUDY_PASS`：七项全过；只表示新 application evidence 可进入修稿，不能直接宣称 JPRS ready。
- `NO_DECISION_CHANGE`：source 阶段无非平凡策略变化，target audit 保持未打开。
- `APPLICATION_SHIFT_FAIL`：target 已打开但任一正式条件失败；停止顶刊实验扩展，不调 gate。
- `NOT_ADJUDICATED_SPLIT_OR_ASSET`：split/asset/provenance 无法按冻结合同成立。
- `PROTOCOL_DRIFT`：泄漏、越界或 post-outcome 改协议。

## 8. T4：独立复核与审计

- implementation A 产出逐实例/逐图像表、source policy 和 target gate。
- validator B 只读原始 sealed rows/predictions，从公式重新计算 `d_tip/Z`、quantile threshold、image aggregation、UCB、bootstrap CI 与七项 gate；不得读取 A 的中间数值作为输入。
- 比较器要求 key/value 一致：确定性字段 `atol=1e-12`；bootstrap endpoints `atol=1e-10`。
- 至少五项真实 mutation：split member、target threshold、angle error、GT AR、policy token；pristine=0，mutated 非零。
- 生成 access audit，证明 HRSC audit GT 首次访问晚于两个 seal commits；bundle/manifest 包含原始或可重算输入、schema、命令、SHA、can_recompute。

## 9. 论文与档位输出

无论成败均输出：

- `docs/paper_jprs_r045/application_decision_study.md`
- `docs/paper_jprs_r045/venue_reassessment.md`
- `audit_bundles/r045/gate.json`
- 完整 schema-2 server report

PASS 时只写一节可并入 r044 的新实验与限制，不覆盖 r044 冻结稿；下一轮再做 claim-bound revision。FAIL 时明确保持 `STRONG_JSTARS_OR_REMOTE_SENSING`，不得继续试 endpoint/阈值/selector。服务器不得宣称已达到或已投稿 JPRS/TGRS。

## 10. 服务器纪律

1. `STARTED.json` 单独 commit/push 后才开始 T0。
2. `ASSET_SEAL`、`POLICY_SEAL`、`TARGET_THRESHOLD_SEAL` 均须按顺序单独 commit/push；前一 seal 未推送不得进入下一数据权限层。
3. CPU bootstrap/matching 使用 >=80% 的 48 核；若规模太小无法有效并行，记录理由。推理重建仅在缺失时执行，四卡并行并记录完整日志路径。
4. 所有产物只进项目内 write_set；不在 third_party、dataset root、`/dev/shm` 或其它项目落文件。
5. 每阶段只向 supervisor log 报告决策结果、停止条件与产物路径；调试细节留执行日志。
6. 完成后 commit + HTTPS push，按 completion mapping 回执；用户未授权任何 post-outcome rescue。
