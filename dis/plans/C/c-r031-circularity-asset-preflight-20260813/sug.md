---
schema_version: 2
plan_id: c-r031-circularity-asset-preflight-20260813
dispatch_id: orientbench-c-r031-circularity-asset-preflight-20260813
initiator: C
activation_authorization:
  mode: owner_only
  delegate: null
  reference: null
closure_authorization:
  mode: owner_only
  delegate: null
  reference: null
base_sha: 9adbcc45d1d69131adece7226804ab0b1a3528aa
supersedes: null
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-13：『你给服务器下达指令。』"
evidence_cutoff: 2026-08-13T22:36:00-07:00
scientific_snapshot:
  primary: 9adbcc45d1d69131adece7226804ab0b1a3528aa
  current_level: STRONG_JSTARS_OR_REMOTE_SENSING
  conditional_target: ISPRS_JPRS_NOT_READY
server_report_path: dis/server_reports/orientbench-c-r031-circularity-asset-preflight-20260813/SERVER_EXECUTION_REPORT.md
read_set:
  - repository tracked governance, audit bundles, reports, manifests and source code at the dispatch commit
  - /home/rspip/cqc/pro/study/pth_data/readme.md
  - existing read-only persistent r014 and r019 features, scores, matched rows and model inventories
  - existing read-only DIOR-R, FAIR1M-v1.0, SODA-A and DOTA-v1.0 official annotation/index assets
write_set:
  - reports/r031_circularity_asset_preflight/**
  - dis/server_reports/orientbench-c-r031-circularity-asset-preflight-20260813/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute:
    gpu_count_max: 0
    gpu_hours_max: 0
    cpu_core_hours_max: 8
  wall_time:
    seconds_max: 14400
  data:
    allowed_dataset_ids:
      - repository-tracked-evidence
      - existing-frozen-orientbench-evidence-readonly
      - DIOR-R-existing-readonly
      - FAIR1M-v1.0-existing-readonly
      - SODA-A-existing-readonly
      - DOTA-v1.0-existing-readonly
    read_bytes_max: 549755813888
    write_bytes_max: 2147483648
  write:
    allowed_paths:
      - reports/r031_circularity_asset_preflight/
      - dis/server_reports/orientbench-c-r031-circularity-asset-preflight-20260813/
      - claude_code_and_supervisor.md
    bytes_max: 2147483648
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
conflict_keys:
  - server-execution-slot
  - dis/sug.md
  - reports/r031_circularity_asset_preflight
gates:
  - gate_id: G0_IDENTITY
    rule: post-pull HEAD must equal the dispatch commit; worktree and index must be clean; worker must be server-primary; pth_data/readme.md must be readable before any asset inspection.
  - gate_id: G1_EIGHT_UNIT_SCHEMA
    rule: each of the eight fixed units must have traceable fields or an explicit missing result for predicted AR, GT AR, class id, confidence, predicted size, canonical angle error, stable row key, image or mother cluster, split role and official annotation provenance.
  - gate_id: G2_JOIN_FEASIBILITY
    rule: for every fixed unit, report source paths, bytes, SHA-256, schema, row count, key uniqueness, duplicate count, finite/missing counts and cohort-to-feature/score key coverage without fitting or computing an outcome contrast.
  - gate_id: G3_OFFICIAL_GT_PROVENANCE
    rule: report the existing official annotation roots and immutable file inventory for all four datasets; for DOTA-v1.0 separately identify the official raw annotation source and the persistent converted GT source used by r026/r028, without overwriting or repairing either.
  - gate_id: G4_READINESS
    rule: ASSET_READY_FOR_R032 only if all eight units have the complete minimum field set, stable join keys and official annotation provenance; otherwise ASSET_GAP_R031 with every missing field/path listed. Either scientific outcome is a valid full inventory result.
early_stop_conditions:
  - post-pull HEAD differs from the dispatch commit or the worktree/index is dirty.
  - worker identity is not server-primary.
  - /home/rspip/cqc/pro/study/pth_data/readme.md is absent or unreadable.
  - any inspected source path resolves outside the declared study/data roots or is writable only through a destructive repair.
kill_conditions:
  - any model fitting, bootstrap, effect-size, risk-coverage, witness or venue-gate computation is attempted.
  - any detector training, forward inference, download, annotation conversion, asset repair or overwrite is attempted.
  - any manuscript, frozen r014/r019/r023/r026/r028 asset, B-owned path, data split, metric, threshold or core claim is modified.
  - results are selected after inspecting target outcomes, or missing fields are inferred from filenames rather than reported missing.
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

# r031 循环性与类别混杂审计：只读资产预检

## 1. 唯一问题

当前稿件的最强反证是：几何归一风险使用 GT aspect ratio，而线性 probe 使用 predicted aspect ratio，现有排序翻转可能是定义诱导的算术结果；类别组成也可能与 AR eligibility domain 混杂。本轮不回答科学效应，只判断既有服务器资产是否足够支撑下一轮冻结的 2×2 循环性审计与类别标准化。

固定八个单元：

| Unit | Dataset | Detector |
|---|---|---|
| A | DIOR-R | Rotated RetinaNet PSC |
| B | DIOR-R | Oriented R-CNN |
| C | DIOR-R | Rotated RTMDet-S |
| D | FAIR1M-v1.0 | Rotated RetinaNet PSC |
| E | SODA-A | Rotated RetinaNet PSC |
| F | SODA-A | Oriented R-CNN |
| G | DOTA-v1.0 val | Oriented R-CNN |
| H | DOTA-v1.0 val | Rotated RTMDet-M |

## 2. 必做任务

### T0：执行身份与只读边界

完整读取仓库 `AGENTS.md`、服务器角色、活动 `dis/sug.md`、coordination、pth_data/readme。保存 post-pull HEAD、branch、upstream、origin、worker id、普通/staged status。只允许 `git pull --ff-only`；冲突、非快进或脏树按早停处理。不得修改或读取 B 私有 memo 的内容。

### T1：来源清单

从 tracked manifests、r014/r019 persistent assets 和官方 annotation/index roots 建立 `source_inventory.csv`：

`unit,dataset,detector,semantic_role,path,exists,bytes,sha256,format,schema,row_count,read_only,witness_source`

所有 source path 必须是真实绝对路径；不存在写 `exists=false`，不得创建替代文件。大型目录用确定性 sorted file manifest 与 manifest SHA-256，禁止只写目录存在。

### T2：字段可用性矩阵

生成 `field_availability.csv`，每个 unit × 每个必需字段恰一行：

`predicted_ar,gt_ar,class_id,confidence,predicted_width,predicted_height,canonical_angle_error,row_key,image_id,mother_scene_id,split_role,official_annotation_id`

每行至少记录：`unit,field,status,source_path,source_column,transform_needed,transform_source_path,transform_line,witness`。`status` 仅允许 `DIRECT,DERIVABLE,MISSING`。`DERIVABLE` 必须有已存在且可定位的冻结变换；不得在本轮发明公式。

### T3：键与 cohort 可连接性

对 matched cohort、features、scores、class labels 和 cluster map 分别核验全表 key 唯一性。以既有 matched D_audit cohort 为左表，仅对 features/scores/class/cluster 表做 semi-select 后核验：cohort missing、duplicate、drop 必须逐项记录；右表合法 extras 允许但需 count 和 sorted-key SHA，并明确不进入 cohort。若字段名不同，必须给出真实映射证据，禁止臆造同名列。

本任务只允许 schema、count、hash、missingness 和 key coverage；禁止生成任何 risk、AUGRC、Risk@coverage、probe prediction、effect、CI、p 值、Holm 或 witness。

### T4：官方标注与 DOTA 转换来源

为四个数据集记录官方原始标注 root、split、文件数、总 bytes、sorted relative-path/bytes/SHA manifest。DOTA-v1.0 额外列出：

- official val annotation root；
- r026/r028 persistent converted GT path；
- 两者各自来源脚本、bytes/SHA、tile/mother count witness；
- 下一轮做 semantic equality replay 所缺的任何 parser、mapping 或字段。

本轮不得运行转换或宣布两者语义等价。

### T5：下一轮可执行性裁决

生成 `r032_readiness.json`，只能是：

- `ASSET_READY_FOR_R032`：八个 unit 全部满足 G1-G3；或
- `ASSET_GAP_R031`：列出 unit、字段、路径和缺失原因。

不得输出 PASS/FAIL 科学效应，不得建议换 dataset、换 detector、改风险定义或缩小到有利 unit。缺资产时只报告缺口和最低恢复动作；恢复动作不在本轮执行授权内。

## 3. 必交产物

固定目录 `reports/r031_circularity_asset_preflight/`：

1. `preflight.json`
2. `source_inventory.csv`
3. `field_availability.csv`
4. `join_feasibility.csv`
5. `official_annotation_inventory.csv`
6. `dota_gt_provenance.json`
7. `r032_readiness.json`
8. `execution_ledger.csv`
9. `artifact_manifest.json`
10. `validate_r031.py`
11. `validation_r031.json`

独立 validator 必须从各 CSV/JSON 与实际文件重算 path set、bytes/SHA、schema、状态枚举、八 unit × 十二字段完整笛卡尔积、key coverage 断言和 readiness 映射；不得信任生成端汇总布尔。至少做四个真实复制品 mutation：删一条 unit-field、改一个 source SHA、制造一个 cohort duplicate、把 MISSING 改成 DIRECT；每个 mutation 必须让 validator 非零退出。mutation 只作用于临时副本，不修改真实资产。

唯一服务器报告必须使用冻结模板字段，明确 `completion_mode`、readiness 状态、资产缺口、实际命令、起止 commit、plan/active hashes、资源和偏差。报告存在不等于科学结论成立。

## 4. 完成语义

八单元完整或存在缺口都可以 `full_completion`，前提是 T0-T5、validator、四 mutation、manifest、报告和 push 全部完成。只有身份/只读前提的预注册早停且证据完整时才是 `gated_early_stop`。脚本失败、缺必做任务、伪造 read/access、越界写或先宣称完成后补证，一律 `failure_early_stop|partial|protocol_drift`。

## 5. 服务器最终回执

最终对话严格两行：

1. `执行完毕` 或 `未执行完毕`；
2. `dis/server_reports/orientbench-c-r031-circularity-asset-preflight-20260813/SERVER_EXECUTION_REPORT.md`

不得增加解释、标题或第三行。
