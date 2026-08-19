---
schema_version: 2
plan_id: b-r046-ahc-obb-semantic-heading-stagea-20260818
dispatch_id: orientbench-b-r046-ahc-obb-semantic-heading-stagea-20260818
initiator: B
business_instruction: "046"
base_sha: 1b659ea0e8a0190211b6f451b85bdaf0b0ec149d
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-18 在 r045 早停且 B 明确说明新标签/新方法需要重新授权后回复：『授权，抓紧进行下一步。』"
scientific_snapshot:
  current_defensible_level: STRONG_JSTARS_OR_REMOTE_SENSING
  legal_target: TGRS_OR_BETTER
  preferred_target: ISPRS_JPRS
  prior_failures: "post-hoc selector/r034, Q-SetOD/r036-r037, OER/r042, SAUR/r043, prospective axis-drift model choice/r045"
  new_increment: "HRSC2016 ship-head point labels define a real directed semantic-heading task rather than another axial-IoU proxy"
  closest_prior_boundary: "HRSC2016 supplies head locations; CHPDet predicts center-to-head points. r046 tests a plug-in antisymmetric endpoint comparator plus selective finite-sample risk control, not a claim that ship-heading prediction itself is new."
  target_route: AHC_OBB_SEMANTIC_HEADING_STAGE_A
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r046-ahc-obb-semantic-heading-stagea-20260818/SERVER_EXECUTION_REPORT.md
read_set:
  - "/home/rspip/cqc/pro/study/pth_data/readme.md and exact valid HRSC2016 R50/LSKNet baseline configs, logs and checkpoints, read-only"
  - "/home/rspip/cqc/data/dataset/HRSC2016/**, read-only, with staged semantic-label access below"
  - "existing repository-tracked r040/r045 HRSC provenance, predictions, splits and evaluation code, read-only"
  - "registered detector checkpoint tensors needed to initialize a frozen image encoder, read-only"
write_set:
  - experiments/r046_semantic_heading/**
  - outputs/persistent_artifacts/orientbench_semantic_heading_r046_20260818/**
  - audit_bundles/r046/**
  - docs/paper_jprs_r046/**
  - dis/server_reports/orientbench-b-r046-ahc-obb-semantic-heading-stagea-20260818/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 4, gpu_hours_max: 48, cpu_core_hours_max: 384}
  wall_time: {seconds_max: 64800}
  data:
    allowed_dataset_ids: ["HRSC2016-existing-images-and-original-head-annotations-readonly", "existing-valid-HRSC-baselines-readonly", "repository-and-manifest-pinned-HRSC-artifacts-readonly"]
    read_bytes_max: 1099511627776
    write_bytes_max: 107374182400
  write:
    allowed_paths: ["experiments/r046_semantic_heading/", "outputs/persistent_artifacts/orientbench_semantic_heading_r046_20260818/", "audit_bundles/r046/", "docs/paper_jprs_r046/", "dis/server_reports/orientbench-b-r046-ahc-obb-semantic-heading-stagea-20260818/", "claude_code_and_supervisor.md"]
    bytes_max: 107374182400
  network: {allowed: true, allowed_endpoints: ["https://github.com/ziyu24/orientbench.git"]}
conflict_keys: ["server-execution-slot", "dis/sug.md", "gpu-all-four-heading-training", "HRSC2016-semantic-heading-test-seal"]
gates:
  - gate_id: G0_HEADING_ASSET_AND_HOST
    rule: "original HRSC train/val XML has valid header_x/header_y supervision at the frozen minimum counts; official split identity is recoverable; two registered HRSC detector families pass provenance/AP parity; test semantic values remain unopened."
  - gate_id: G1_ANTISYMMETRIC_MECHANICS
    rule: "AHC logit obeys l(p_plus,p_minus)=-l(p_minus,p_plus) to <=1e-6, 180-degree crop rotation complements the probability to <=1e-6, crop/label transforms pass synthetic and real smoke tests, and detector geometry is unchanged by the heading plug-in."
  - gate_id: G2_SEALED_TEST_RECOGNITION
    rule: "on sealed HRSC test valid-head instances, AHC GT-box heading accuracy >=0.80 with image-bootstrap 95% lower >0.75 and paired improvement over the strongest frozen learned baseline >=0.02 with 95% lower >0."
  - gate_id: G3_END_TO_END_TWO_HOSTS
    rule: "for both R50 and LSKNet class-correct rIoU>=0.50 matched detections, heading accuracy >=0.75; equal-host paired improvement over the strongest baseline >=0.02 with 95% lower >0; AHC AUGRC reduction >=0.01 with 95% lower >0; detector AP50/AP75 bytes and values are unchanged because AHC only adds a directed-heading output."
  - gate_id: G4_SELECTIVE_UTILITY
    rule: "the val-only sealed heading threshold yields test coverage >=0.70 and one-sided 95% complete-image Hoeffding-Bentkus heading-error UCB <=0.15 on each host; no eligible location group with >=30 instances has point accuracy below 0.60."
  - gate_id: G5_AUDIT_AND_ROUTE
    rule: "independent raw-input metric recomputation, five real mutations, manifest/SHA and access audit pass. Only G0-G5 all-pass emits PROCEED_AHC_OBB_STAGE_B; otherwise REJECT_AHC_OBB_METHOD."
early_stop_conditions:
  - "train has <500 or val has <150 valid non-ambiguous head labels; official split cannot be recovered; fewer than two valid HRSC host detector families; required images/XML/checkpoints absent."
  - "test header_x/header_y or derived heading outcomes are opened before MODEL_AND_THRESHOLD_SEAL is committed and pushed."
  - "step-zero/smoke mechanics fail, nonfinite loss occurs, or first formal epoch validation accuracy is <0.60 for AHC while a frozen learned baseline is >=0.65."
  - "G2 primary CI crosses zero or any required two-host/utility condition becomes logically impossible; stop without adding data, changing endpoint or relaxing the gate."
kill_conditions:
  - "modify HRSC images/XML/splits, frozen r040-r045 evidence, baseline weights, prior thresholds or formal/exploratory labels."
  - "read HRSC test semantic head coordinates before the model/temperature/selection threshold/checkpoint are sealed and remotely visible."
  - "use test head labels for epoch choice, architecture, augmentation, threshold, temperature, filtering, checkpoint selection or retry."
  - "download or introduce FGSD/another dataset in r046; Stage B external data is authorized only after PROCEED_AHC_OBB_STAGE_B and a new dispatch."
  - "claim JPRS/TGRS readiness, physical vessel motion, AIS course, causal heading, or novelty over CHPDet from Stage A alone."
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: "执行完毕"}
  gated_early_stop: {execution_status: complete, receipt_first_line: "执行完毕"}
  failure_early_stop: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
  partial: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
  protocol_drift: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
---

# r046：AHC-OBB 舰船 semantic-heading Stage-A 生死门

## 1. 主要矛盾与新科学增量

r045 证明 AP-based 与 orientation-risk-based architecture choice 在 HRSC axial drift 上没有应用收益。继续改变 axial endpoint、阈值或 selector 是 post-outcome rescue，禁止执行。

r046 改变的不是统计口径，而是任务信息：普通 OBB 只给 `theta mod pi` 的无向长轴；HRSC2016 原始标注另有船头点，可定义 `phi mod 2pi` 的有向 semantic heading。目标是一个插件式方法：不修改 detector box/class/score，判断预测长轴的两个端点中哪一个是船头，并对该判断给出可选择的可靠性分数。

方法名暂定 **AHC-OBB (Antisymmetric Heading Comparator for OBB)**。Stage A 只判断该方法是否有真实、跨 host、held-out application value。通过只授权 Stage B 外部数据验证，不等于顶刊 ready。

## 2. 已知近邻与不得夸大的 novelty

- HRSC2016 数据论文已说明部分舰船具有 ship-head location；该标签来源不是本项目贡献。
- CHPDet/center-head-point 类工作已证明直接预测船头点可行；“预测舰船头尾”本身不是新任务。
- AHC-OBB 的待验证增量是：对任意既有 OBB detector 的 **plug-in** endpoint-pair comparator；通过结构保证 180° endpoint-swap antisymmetry；输出独立 heading reliability；用 source val 封存阈值后在 target test 做 complete-image finite-sample risk control。
- 若 AHC 不能同时打赢 parameter-matched unconstrained classifier 与 head-point regression baseline，本方法没有足够创新/效用，直接终止。

## 3. 数据、监督与信息墙

### 3.1 特殊 split（用户已授权）

HRSC 本轮显式使用：

```text
official train -> heading-head training only
official val   -> deterministic V_fit/V_cal; checkpoint/model selection on V_fit, temperature and selection threshold on V_cal
official test  -> one sealed audit after MODEL_AND_THRESHOLD_SEAL
```

这是 semantic-heading 新任务的特殊协议，不沿用 r045 的 trainval 内部 D_cal/D_audit，也不改变任何既有 split bytes。V_fit/V_cal 以 `SHA256("r046|" + image_id)` 最低位确定，先写清单/hash 再打开 val heading values。

### 3.2 valid-head instance

冻结定义：XML 中 `header_x/header_y` 均为有限图内坐标；船头点到 OBB center 的距离至少为 GT 长边的 0.10；其到两个 canonical long-axis endpoint 的距离差除以 GT 长边至少为 0.10。label 是更接近 header point 的 endpoint。其余实例标 `HEAD_AMBIGUOUS_OR_MISSING`，进入覆盖披露，不进入主训练/风险分母。不得按模型表现改过滤规则。

### 3.3 test access wall

在 `MODEL_AND_THRESHOLD_SEAL.json` 推送前，test 只允许读取 image bytes、image ID、尺寸和 detector inference 所需非语义内容；禁止解析或扫描 `header_x/header_y` 数值、派生 endpoint label、heading outcome 或任何既有缓存。若框架 XML loader 无法字段级限制，先生成 image-only test dataset wrapper。

## 4. Host 与输入

正式 end-to-end hosts 固定为 HRSC valid baselines：

1. `oriented_rcnn_r50_fpn_le90`
2. `oriented_rcnn_lsknet_s_fpn_le90`

先按 `pth_data/readme.md` 核对 dataset/split/backbone/schedule/batch/lr/BN/mAP/framework/checkpoint SHA。优先复用已有 test image-only predictions；缺失时用登记 config/checkpoint 四卡确定性推理，不训练 detector。两 host 任一无法 parity，G0 失败，不替换第三 host。

训练 AHC 使用 GT OBB rectified crops，以 detector-R50 backbone checkpoint初始化共享图像 encoder；encoder 资产与加载映射必须写 SHA。为避免 GT-crop 到 predicted-crop 落差，训练时冻结增强为 center jitter `[-5%,5%]`、log-scale jitter对应 `[0.9,1.1]`、angle jitter `[-10°,10°]`，以及 180° crop rotation并翻转 endpoint label。不得在 test 结果后改变增强。

## 5. AHC-OBB 与冻结 baselines

### 5.1 Rectification

每个 OBB 按 canonical long axis 采样为 `192 x 64` RGB crop，定义右端 `p_plus`、左端 `p_minus`，各取 `64 x 64` endpoint patch；出界使用 reflection padding。颜色归一化与插值规则写入 protocol 并在所有方法共用。

### 5.2 AHC-OBB

共享 encoder `f` 分别编码两端，唯一有向 logit：

```text
l(p_plus,p_minus) = w^T [ f(p_plus) - f(p_minus) ]
p_plus_is_head = sigmoid(l)
heading_confidence = abs(2*p_plus_is_head - 1)
```

linear comparator 无 bias。交换 endpoint 必须精确使 logit 变号；概率互补。训练用 BCE；不反传至 detector，不改变 OBB、class 或 detection score。允许服务器自行处理 DDP、缓存、混合精度和 dataloader，只要不改变公式/数据/预算。

### 5.3 强 baselines（同训练图像、split、encoder初始化与预算）

1. `WHOLE_CROP`: whole rectified crop feature + linear binary classifier。
2. `CONCAT_ENDPOINT`: `[f(p_plus),f(p_minus)]` + parameter-matched MLP，无 antisymmetry 结构。
3. `HEADPOINT_REG`: whole crop feature回归归一化二维 center-to-head vector，按与两个 endpoint 的方向相似度解码；这是 CHP-like 最邻近 baseline，不冒充 CHPDet 全实现。
4. `RANDOM_POLE`: 0.5 参考线，仅作任务 sanity，不算 strongest learned baseline。

不得增加模型菜单或事后挑 architecture。strongest baseline 在 V_fit 上按 heading accuracy、再按 AUGRC、再按固定顺序选择，并写入 seal；test 只比较该封存 baseline。

## 6. 训练、校准和封印

- 先做 200-iteration 四卡 smoke；有限 loss、反对称测试和 real-crop transform test 通过后才正式训练。
- 所有 learned arms 相同 optimizer、global batch、最多 30 epochs；每 epoch 评估 V_fit；只保留 best-V_fit 与 latest。首正式 epoch触发冻结早停条件则停止。
- checkpoint 选择只看 V_fit；temperature 只在 V_cal 拟合。
- selection coverage grid 固定 `[0.90,0.80,0.70]`，从高到低选第一个 complete-image heading-error Hoeffding-Bentkus UCB `<=0.15` 的 confidence threshold；无点通过则 G4 已不可能，仍封存 `NO_SAFE_THRESHOLD` 并早停，不打开 test head values。
- `MODEL_AND_THRESHOLD_SEAL.json` 必须包含模型/基线、checkpoint/config/script SHA、split hashes、temperature、numeric threshold、nominal/realized V_cal coverage、risk/UCB、训练日志和 test image-only prediction hashes；单独 commit/push 后才能进入 T3。

## 7. 唯一 target audit 与指标

seal 推送后只打开一次 official test semantic head values。报告两层结果：

1. `GT_BOX_RECOGNITION`：GT OBB crop，隔离纯 head/stern recognition。
2. `PRED_BOX_END_TO_END`：分别对 R50、LSKNet class-correct one-to-one rIoU>=0.50 matched detections使用 predicted OBB crop；固定 identity matching后比较 heading，不因 heading 输出重匹配。

主指标：directed heading accuracy、binary error risk、AUGRC、Risk@70/80/90、coverage。辅助：360° angular error、按 ship-size/obliquity/location 分组、valid-head label coverage。detector AP50/AP75 从未修改的原 predictions重算并做字节/数值不变检查。

统计固定：mother image 为交换单位，paired 10,000 bootstrap，seed `20260818`；两 host 同 replicate 使用同一 image multiplicity，再等权平均。置信区间 percentile 95%。selective absolute risk 使用 complete-image one-sided 95% Hoeffding-Bentkus UCB。零 eligible image 保留为零风险并同时受 coverage gate 约束。

## 8. 决策表

| 终态 | 条件 | 后续 |
|---|---|---|
| `PROCEED_AHC_OBB_STAGE_B` | G0-G5 全过 | 新 dispatch 获取/核验 FGSD 或另一真实 head-label 数据，做跨数据集/传感器外部验证与正式方法消融 |
| `REJECT_AHC_OBB_METHOD` | 任一科学 gate 失败 | 停止 AHC，不改 test split、标签过滤、模型、阈值或 gate；项目仍低于合法投稿线 |
| `NOT_ADJUDICATED_HEADING_ASSET` | G0 资产/数量/host 不成立 | 保留最小资产表，不把资产缺失写成科学负结果 |
| `PROTOCOL_DRIFT` | test 语义泄漏、事后调参、split/label修改或越界 | `execution_status=incomplete`，不得给科学裁决 |

## 9. 审计与交付

- implementation A 输出 instance/image rows、三模型测试结果、两 host end-to-end 表与 gate。
- validator B 不 import A 的统计代码，从 sealed rows 重算 accuracy/AUGRC/coverage/HB/bootstrap/gate；代码相似度高于 0.80 必须报告并重写，不得以复制实现冒充独立。
- 五项真实 subprocess mutation：endpoint swap label、test split member、sealed threshold、host match key、gate token；pristine=0，mutated 非零。
- 持久化 raw/derived rows、schema、commands、logs、manifest path/bytes/SHA/can_recompute；`/dev/shm` 仅临时。
- 输出：`docs/paper_jprs_r046/semantic_heading_stagea.md`、`docs/paper_jprs_r046/closest_prior_and_scope.md`、`audit_bundles/r046/gate.json` 和完整 schema-2 server report。
- 用户回执严格两行：第一行按 completion mapping；第二行唯一 report path。服务器只报告关键 gate/异常，不刷训练碎片。
