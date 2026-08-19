---
schema_version: 2
plan_id: b-r047-ahc-obb-clean-formal-stagea-20260818
dispatch_id: orientbench-b-r047-ahc-obb-clean-formal-stagea-20260818
initiator: B
business_instruction: "047"
base_sha: bf8bc69b24f5a34891895c1cfed47e50da07ec0b
supersedes: b-r046-ahc-obb-semantic-heading-stagea-20260818
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-18 在 B 将 r046 判为 INCOMPLETE / PROTOCOL_DRIFT 并说明必须新授权后回复：『继续推进执行。』"
scientific_snapshot:
  current_defensible_level: STRONG_JSTARS_OR_REMOTE_SENSING
  legal_target: TGRS_OR_BETTER
  preferred_target: ISPRS_JPRS
  r046_status: "execution incomplete; invalid confidence/error calibration; official val semantic values consumed; official test semantic values remain unopened"
  new_increment: "clean formal AHC-OBB development plus untouched test-internal calibration/audit wall"
  target_route: AHC_OBB_CLEAN_FORMAL_STAGE_A
review_mode: open
server_report_path: dis/server_reports/orientbench-b-r047-ahc-obb-clean-formal-stagea-20260818/SERVER_EXECUTION_REPORT.md
read_set:
  - "/home/rspip/cqc/pro/study/pth_data/readme.md and exact valid HRSC2016 R50/LSKNet configs, logs and checkpoints, read-only"
  - "/home/rspip/cqc/data/dataset/HRSC2016/**, read-only, subject to the staged official-test semantic wall"
  - "r046 plan, B verdict and code, read-only for failure avoidance; no r046 weights, risks, split or scientific token may be reused"
  - "existing HRSC host prediction/provenance artifacts, read-only"
write_set:
  - experiments/r047_semantic_heading/**
  - outputs/persistent_artifacts/orientbench_semantic_heading_r047_20260818/**
  - audit_bundles/r047/**
  - docs/paper_jprs_r047/**
  - dis/server_reports/orientbench-b-r047-ahc-obb-clean-formal-stagea-20260818/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute: {gpu_count_max: 4, gpu_hours_max: 96, cpu_core_hours_max: 384}
  wall_time: {seconds_max: 86400}
  data:
    allowed_dataset_ids: ["HRSC2016-existing-images-and-original-head-annotations-readonly", "existing-valid-HRSC-baselines-readonly", "repository-and-manifest-pinned-HRSC-artifacts-readonly"]
    read_bytes_max: 1099511627776
    write_bytes_max: 107374182400
  write:
    allowed_paths: ["experiments/r047_semantic_heading/", "outputs/persistent_artifacts/orientbench_semantic_heading_r047_20260818/", "audit_bundles/r047/", "docs/paper_jprs_r047/", "dis/server_reports/orientbench-b-r047-ahc-obb-clean-formal-stagea-20260818/", "claude_code_and_supervisor.md"]
    bytes_max: 107374182400
  network: {allowed: true, allowed_endpoints: ["https://github.com/ziyu24/orientbench.git"]}
conflict_keys: ["server-execution-slot", "dis/sug.md", "gpu-all-four-heading-training", "HRSC2016-test-internal-semantic-wall"]
gates:
  - gate_id: G0_ASSET_PARTITION_AND_IMPLEMENTATION
    rule: "baseline provenance passes; official-test identity-only T_cal/T_audit lists are remotely sealed before any test XML semantic field is read; complete formal code/config and pretrained-backbone mapping pass static/mechanics checks."
  - gate_id: G1_FORMAL_DEVELOPMENT
    rule: "AHC and all three learned baselines finish the frozen four-GPU train/val development contract, with required logs/checkpoints and a remotely visible MODEL_DEVELOPMENT_SEAL before any official-test semantic value is read."
  - gate_id: G2_TCAL_SELECTIVE_SAFETY
    rule: "after the model seal, only T_cal semantics are opened; paired confidence/error rows and independently recomputed finite-sample UCBs produce coverage >=0.70 and risk UCB <=0.15 for GT-box, R50 and LSKNet views; TCALIBRATION_SEAL is pushed before T_audit opens."
  - gate_id: G3_TAUDIT_RECOGNITION
    rule: "on untouched T_audit valid-head GT boxes, AHC accuracy >=0.80 with image-bootstrap 95% lower >0.75 and paired accuracy gain over the sealed strongest learned baseline >=0.02 with 95% lower >0."
  - gate_id: G4_TAUDIT_TWO_HOST_UTILITY
    rule: "on each sealed HRSC host, matched-detection heading accuracy >=0.75; equal-host gain over the sealed strongest baseline >=0.02 with 95% lower >0; AHC AUGRC reduction >=0.01 with 95% lower >0; calibrated coverage >=0.70 and complete-image risk UCB <=0.15; detector AP bytes/values remain unchanged."
  - gate_id: G5_AUDIT_AND_ROUTE
    rule: "independent raw-row recomputation, paired-confidence calibration check, five real mutations, manifest/SHA/access audit and claim-scope review pass. Only G0-G5 all-pass emits PROCEED_AHC_OBB_STAGE_B."
early_stop_conditions:
  - "required HRSC assets or either registered host fail provenance/load/AP parity; official test identity partition cannot be made without semantic access; T_cal or T_audit has <150 images or <300 valid-head instances after its permitted opening."
  - "formal implementation lacks the detector-R50 backbone mapping, HEADPOINT_REG, one of the other baselines, four-rank DDP evidence, best/latest checkpoints, or complete epoch logs; any proxy/tiny substitute is execution failure, not a scientific result."
  - "AHC first formal epoch official-val accuracy <0.60 while a frozen learned baseline is >=0.65; report a valid development early stop without opening official-test semantics."
  - "after complete formal development, no T_cal coverage candidate satisfies the frozen simultaneous safety rule for all three required views; emit valid calibration failure and do not open T_audit."
  - "T_audit primary CI crosses zero or any required two-host/utility condition becomes logically impossible; stop without changing model, partition, threshold, endpoint or gate."
kill_conditions:
  - "read any official-test header_x/header_y, derived heading label or outcome before MODEL_DEVELOPMENT_SEAL is committed and pushed; read any T_audit semantic field before TCALIBRATION_SEAL is committed and pushed."
  - "parse all official-test XML through a generic loader at either wall; use T_audit for model, temperature, threshold, baseline, augmentation, checkpoint or retry choice."
  - "reuse r046 proxy checkpoint, r046 V_fit/V_cal, invalid r046 risk values or its REJECT token; modify HRSC images/XML/original split bytes, registered host weights or prior frozen evidence."
  - "download another dataset, train/fine-tune a detector, relax numeric gates, omit a required baseline, or label a partial/proxy run complete."
  - "claim JPRS/TGRS readiness, physical vessel motion/AIS course, causal heading or novelty over head-point detection from Stage A alone."
completion_mapping:
  full_completion: {execution_status: complete, receipt_first_line: "执行完毕"}
  gated_scientific_early_stop_after_complete_required_stage: {execution_status: complete, receipt_first_line: "执行完毕"}
  implementation_or_asset_failure: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
  partial_or_proxy: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
  protocol_drift: {execution_status: incomplete, receipt_first_line: "未执行完毕"}
---

# r047：AHC-OBB clean formal Stage-A

## 1. 主要矛盾与证据身份

r046 没有裁决方法：它用 tiny proxy 代替正式模型，并在错误配对的 confidence/error 上把经验风险冒充有限样本 UCB。r047 不修补 r046 数值，而是重做完整方法实验。

同时必须承认 official val 的船头语义已在 r046 被完整读取并参与 transform/model 比较，因此 official train/val 从本轮开始均是 **consumed development data**，不能再承担独立 calibration/audit 身份。official test 的 `header_x/header_y` 尚未打开，是唯一清白语义端点。本轮经用户新授权，在 test identity 层先确定性拆分 `T_cal/T_audit`，随后设置两道不可逆信息墙。

## 2. T_cal/T_audit 信息墙

只读取官方 test image-ID 列表，不读取/扫描 XML，按以下字面规则拆分：

```text
h = SHA256("r047-test|" + image_id)
int(h[-2:], 16) % 2 == 0 -> T_cal
otherwise                    -> T_audit
```

`TEST_PARTITION_SEAL.json` 必须记录原 test-list bytes/SHA、两份有序 ID 清单、count/hash、生成脚本/命令，并作为独立 commit 通过 HTTPS 推送。若任一侧少于 150 images，G0 失败且不得看 test XML。

访问顺序固定：

1. `MODEL_DEVELOPMENT_SEAL` 远端可见前，T_cal/T_audit 的所有 XML 与任何缓存 semantic values 均禁止读取。
2. model seal 后只允许打开 T_cal IDs 对应 XML；T_audit XML 继续封闭。
3. `TCALIBRATION_SEAL` 远端可见后，才允许一次打开 T_audit IDs 对应 XML。

不得使用会一次解析整个 test annotation folder 的框架 loader。服务器自行实现 ID allow-list wrapper 和真实文件访问日志；工程实现可灵活，但信息墙不可变。

## 3. 标签、crop 与 formal models

valid-head 定义沿用 r046 且不得按表现修改：header 坐标有限且在图内；center-to-header 距离至少为 GT 长边 0.10；到 canonical 两个长轴 endpoint 的投影差除以长边至少 0.10。更靠近 header 的 endpoint 为 head；其余只进入 coverage disclosure。

共同 rectification：将 OBB long axis 水平化为 `192x64` RGB crop，bilinear interpolation、reflection padding，使用注册 R50 config 的 channel/mean/std；`p_minus/p_plus` 分别为最左/最右 `64x64` patch，中间 64 pixels 不进入 endpoint arms。变换必须用 synthetic arrow 与至少 32 个 real train instances 验证 header endpoint 标签；180° crop rotation 必须交换标签。

共享 backbone 是注册 HRSC Oriented R-CNN R50 checkpoint 的 ResNet-50 stem/layer1-4。必须证明 `backbone.*` 逐 tensor 加载，记录 config/checkpoint SHA、missing/unexpected keys；stem/layer1-3 和 BN stats 冻结，layer4 与 task head 训练。禁止随机 tiny CNN 或 torchvision 随机替代。

四个 formal arms：

1. `AHC`: `l=w^T(f(p_plus)-f(p_minus))`，linear 无 bias；endpoint swap 精确变号，概率互补。
2. `WHOLE_CROP`: 同 backbone 处理完整 rectified crop，linear binary head。
3. `CONCAT_ENDPOINT`: 同一个 shared endpoint backbone，`[f(p_plus),f(p_minus)]` 接 unconstrained linear/MLP binary head；结构不强制 antisymmetry。
4. `HEADPOINT_REG`: 同 backbone 处理完整 crop，回归归一化 center-to-head 2D vector，以其同两个 endpoint 方向的相似度差解码 binary heading。这是 CHP-like baseline，不冒充 CHPDet 原实现。

所有 arms 报告总参数、可训练参数、FLOPs；共同可训练 R50 layer4 使总可训练参数差异须小于 1%，否则用固定无标签 projection 调整，不得削弱 baseline。`RANDOM_POLE=0.5` 只作 sanity，不参与 strongest learned baseline。

## 4. Development 训练合同

- official train 用于训练，official val 用于 checkpoint/model/baseline selection；二者均明确标记 consumed development。
- 共同增强：center jitter `[-5%,5%]`、scale `[0.9,1.1]`、angle `[-10°,10°]`、color jitter，以及概率 0.5 的 180° crop rotation并翻转 label；所有 arm 使用同一增强种子流。
- 四卡 `torchrun --nproc_per_node=4` DDP，global batch 64，AdamW、lr `1e-4`、weight decay `0.05`、1 epoch warmup + cosine、AMP、seed `20260818`，最多 30 epochs。若显存不足可只调每卡 microbatch并用 accumulation保持 global batch，必须记录；不得改科学模型。
- 每 epoch 在 official val 评估 accuracy、error、AUGRC；每 arm 只保留 best-val-accuracy（tie-break AUGRC）和 latest。四 arm 必须同预算，不因中途领先而停掉 baseline。
- 200-iteration 四卡 smoke 只验证 loss/transform/DDP/antisymmetry，不用于任何科学 gate；formal 与 smoke 目录、checkpoint、日志严格分开。

strongest learned baseline 在 val 上按 accuracy、再 AUGRC、再固定顺序 `HEADPOINT_REG > CONCAT_ENDPOINT > WHOLE_CROP` 封存。`MODEL_DEVELOPMENT_SEAL.json` 包含全部代码/config/checkpoint/log SHA、预训练映射、参数/FLOPs、epoch table、best/latest、strongest baseline、test image-only prediction hashes和访问审计；独立 commit/push 后才能进入 T_cal。

## 5. T_cal 校准与有效风险上界

model seal 后，对 T_cal 分别生成 `GT_BOX`、`PRED_BOX_R50`、`PRED_BOX_LSKNET` 三个 view 的完整 raw rows。host matching 固定 class-correct one-to-one rIoU>=0.50；detector predictions不因 heading修改。

AHC probability temperature 仅在 T_cal 拟合，temperature 为正标量。每 view 独立使用 coverage grid `[0.90,0.80,0.70]`，confidence 与 error 必须以同一 `row_id` 成对排序；输出选择前后 row-id SHA，validator 必须逐行确认 pairing。

风险单位是 mother image。对每个 image 计算 retained valid-head instance 的平均 0/1 error；无 retained instance 的 image 记为 0 loss但进入 coverage/accounting。对 bounded image losses计算 one-sided Hoeffding-Bentkus 95% UCB：实现同时给出 Hoeffding tail和 `e * BinomialCDF(floor(sum_loss), n_images, candidate_mean)` 的数值反演，取较紧合法界；以 brute-force/grid reference 验证。三 coverage × 三 view 使用 Bonferroni `alpha=0.05/9`，防止挑 coverage/view 后虚假安全。

从 coverage 由高到低选首个同时满足三 view `realized coverage>=0.70` 且 `UCB<=0.15` 的 coverage；每 view 可有自己的 numeric threshold/temperature，但共同 nominal coverage 必须相同。无共同点则正式终态 `REJECT_AHC_OBB_VALID_TCAL_SAFETY_FAIL`，这是完整 formal calibration 负结果；停止且不打开 T_audit。

`TCALIBRATION_SEAL.json` 记录 row/schema/hash、temperatures、thresholds、nominal/realized coverage、empirical risk、UCB、alpha correction、code/command/log SHA 和 T_audit access=false；独立 HTTPS push 后才进入 audit。

## 6. 唯一 T_audit 评价

seal 后一次打开 T_audit semantic values，报告：

- GT-box：四 arm accuracy/error/AUGRC/Risk@70/80/90，AHC 对封存 strongest baseline 的 paired delta。
- 两 host end-to-end：R50、LSKNet 分别在冻结 matched set 上的同一指标；跨 host 以同一 image-bootstrap replicate 等权平均。
- 10,000 paired mother-image bootstrap，seed `20260818`，percentile 95% CI；完整披露 valid-head coverage、ship size/obliquity/location groups，group eligible n<30 只描述不 gate。
- 按 T_cal seal 原样应用 threshold/temperature，并在 T_audit 独立重算 complete-image HB UCB；不得重新选 coverage。
- detector AP50/AP75 由原始 predictions 重算，并用 bytes/hash 证明 heading plugin 未修改 box/class/score。

G3/G4 按 front-matter 数值逐项裁决。AHC 若打不赢 strongest baseline、收益只在单 host、或 risk-control 失败，均终态 `REJECT_AHC_OBB_METHOD`，禁止调参救 audit。

## 7. 审计、产物与路线

Implementation A 必须持久化 train/val/test raw rows、three-view calibration/audit rows、epoch tables、checkpoint/config、commands/logs、host predictions/matches、metric tables。Validator B 不 import A 的统计/校准函数，从 raw rows重算 pairing、accuracy/AUGRC/coverage/HB/bootstrap/gates；token/code similarity >0.80 必须重写。

五项真实 subprocess mutations至少覆盖：confidence-error row permutation、endpoint label swap、T_cal/T_audit member、sealed threshold、host match key。pristine=0，所有 mutated invocation 非零。manifest 对每个必需对象记录 path/bytes/SHA-256/can_recompute；`/dev/shm` 仅临时。

交付 `docs/paper_jprs_r047/semantic_heading_stagea.md`、`closest_prior_and_scope.md`、`venue_reassessment.md`、完整 `audit_bundles/r047/` 与 schema-2 server report。正文只写 method/evidence/limitation，治理细节进附录。

仅当 G0-G5 全部通过，终态为 `PROCEED_AHC_OBB_STAGE_B`：它只授权下一轮寻找/核验独立真实 head-label 数据并做跨数据集/传感器验证，仍不等于 JPRS/TGRS ready。任一科学 gate 失败，项目维持既有 measurement 稿档位并停止 AHC；任何 proxy/泄漏/部分交付按 `未执行完毕` 返回，不得伪装科学负结果。

用户回执严格两行：第一行按 completion mapping；第二行只给唯一 server report path。服务器仅汇报关键 gate、早停或严重异常。
