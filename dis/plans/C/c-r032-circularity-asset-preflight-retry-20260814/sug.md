---
schema_version: 2
plan_id: c-r032-circularity-asset-preflight-retry-20260814
dispatch_id: orientbench-c-r032-circularity-asset-preflight-retry-20260814
initiator: C
activation_authorization:
  mode: owner_only
  delegate: null
  reference: null
closure_authorization:
  mode: owner_only
  delegate: null
  reference: null
base_sha: 223cae5e88397274c2ba82e4abde6da08d280acb
supersedes: c-r031-circularity-asset-preflight-20260813
risk_class: L2
user_authorization:
  required: true
  status: granted
  reference: "用户 2026-08-14：『① 正式关闭上一轮（只有它有权关）；② 签发新一轮资产预检（检查数据字段齐不齐，为循环性对照实验做准备）。以及其它你认为必要的。』"
evidence_cutoff: 2026-08-14T01:03:00-07:00
scientific_snapshot:
  primary: 223cae5e88397274c2ba82e4abde6da08d280acb
  r031_scientific_state: NOT_ADJUDICATED
  current_level: STRONG_JSTARS_OR_REMOTE_SENSING
  conditional_target: ISPRS_JPRS_NOT_READY
server_report_path: dis/server_reports/orientbench-c-r032-circularity-asset-preflight-retry-20260814/SERVER_EXECUTION_REPORT.md
read_set:
  - repository tracked governance, audit bundles, reports, manifests and source code at the dispatch commit
  - /home/rspip/cqc/pro/study/pth_data/readme.md
  - existing read-only persistent r014 and r019 features, scores, matched rows and model inventories
  - existing read-only DIOR-R, FAIR1M-v1.0, SODA-A and DOTA-v1.0 official annotation/index assets
  - exact six pre-existing untracked quarantine roots from r031 for path/bytes/SHA inventory only, never as scientific input
write_set:
  - reports/r032_circularity_asset_preflight/**
  - dis/server_reports/orientbench-c-r032-circularity-asset-preflight-retry-20260814/**
  - claude_code_and_supervisor.md
resource_scope:
  declared: true
  compute:
    gpu_count_max: 0
    gpu_hours_max: 0
    cpu_core_hours_max: 12
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
      - reports/r032_circularity_asset_preflight/
      - dis/server_reports/orientbench-c-r032-circularity-asset-preflight-retry-20260814/
      - claude_code_and_supervisor.md
    bytes_max: 2147483648
  network:
    allowed: true
    allowed_endpoints:
      - https://github.com/ziyu24/orientbench.git
conflict_keys:
  - server-execution-slot
  - dis/sug.md
  - reports/r032_circularity_asset_preflight
gates:
  - gate_id: G0_EXECUTION_IDENTITY
    rule: server must use git pull --ff-only; post-pull HEAD must equal the dispatch commit; worker must be server-primary; tracked worktree and index must be clean; pth_data/readme.md must be readable; a complete committed STARTED.json must be pushed before any asset or quarantine-content read.
  - gate_id: G0Q_EXACT_QUARANTINE
    rule: the only permitted pre-existing untracked entries are a subset of the six exact r031 paths; every present file is inventoried by relative path, bytes and SHA-256 before scientific reads and again after all reads; no seventh entry, byte change, parse/decode consumption, move, delete, stash, add, ignore-rule change or repair is permitted.
  - gate_id: G1_EIGHT_UNIT_SCHEMA
    rule: each of the eight fixed units must have traceable DIRECT, DERIVABLE or MISSING status for predicted AR, GT AR, class id, confidence, predicted width/height, canonical angle error, stable row key, image/mother cluster, split role and official annotation id.
  - gate_id: G2_JOIN_FEASIBILITY
    rule: every fixed unit reports source paths, bytes, SHA-256, schema, row count, key uniqueness, duplicates, finite/missing counts and cohort-to-feature/score/class/cluster key coverage; no outcome contrast is computed.
  - gate_id: G3_OFFICIAL_GT_PROVENANCE
    rule: all four datasets have official annotation roots and immutable inventories; DOTA-v1.0 separately identifies official raw annotations and the persistent converted GT used by r026/r028 without converting, repairing or claiming semantic equality.
  - gate_id: G4_READINESS
    rule: ASSET_READY_FOR_R033 only if all eight units have the complete minimum causal-control field set, stable join keys and official annotation provenance; otherwise ASSET_GAP_R032 with every gap and minimum non-executed recovery action. Either outcome is a valid completed inventory.
early_stop_conditions:
  - post-pull HEAD, worker identity, tracked/index cleanliness, pth_data/readme or committed STARTED identity fails.
  - an untracked path exists outside the six-item quarantine allowlist.
  - a quarantine file changes between before/after manifests or requires modification to continue.
  - an inspected source resolves outside the declared study/data roots or requires destructive repair.
kill_conditions:
  - any model fitting, bootstrap, effect-size, risk-coverage, witness, scientific PASS/FAIL or venue-gate computation is attempted.
  - any detector training, forward inference, download, annotation conversion, asset repair or overwrite is attempted.
  - any manuscript, frozen r014/r019/r023/r026/r028 asset, B-owned path, data split, metric, threshold or core claim is modified.
  - any quarantine content is parsed or consumed as scientific evidence, or missing fields are inferred from filenames.
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

# r032 循环性与类别混杂资产预检：技术重试

## 1. 目的与边界

r031 没有读取科学资产；它因六个历史未跟踪路径停在 G0。本轮不是科学 gate 续命，而是同一资产问题的技术重试：精确隔离既存 quarantine，完成八个固定单元的字段、键、官方标注和稿件支持证据盘点，为后续单独审批的循环性 2×2 对照准备输入。不得计算任何效果量或改写论文结论。

固定单元：

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

## 2. T0：领取、STARTED 与 quarantine

1. 完整读取 `AGENTS.md`、服务器角色、coordination、活动 `dis/sug.md` 和 `pth_data/readme.md`；禁止读取 `dis/B.md` 内容。
2. 只执行 `git pull --ff-only`。保存 pre/post HEAD、origin、branch、upstream、worker、tracked diff、index diff、untracked path set。
3. 在任何 persistent/scientific asset 或 quarantine file content read 前，创建完整 `STARTED.json`，至少含 dispatch/plan id、plan commit/blob/SHA、active blob/SHA、dispatch commit、starting commit、worker id、created_at；只提交 STARTED 并先 push。
4. r031 冻结的六个 quarantine roots：

```text
top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations/
top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations_final/
top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations_v2/
top_journal_v3_reaudit_055/corrective_audit_r028_20260813/r026_raw_revalidation/error.json
top_journal_v3_reaudit_055/measurement_validity_r022_20260813/
top_journal_v3_reaudit_055/measurement_validity_r023_20260813/
```

实际 untracked set 可以为空或为上述集合的子集，但不能有第七项。对存在项只允许二进制 hash stream，不允许结构解析；输出 `legacy_quarantine_before.csv`。全过程不得修改 `.gitignore`、`.git/info/exclude` 或这些路径。

## 3. T1-T4：八单元资产与连接性

### T1 来源清单

生成 `source_inventory.csv`：

`unit,dataset,detector,semantic_role,absolute_path,exists,bytes,sha256,format,schema,row_count,read_only,witness_source`

大型目录生成 sorted `relative_path,bytes,sha256` 子清单并给目录 manifest SHA。不存在必须写 `exists=false`，禁止创建替代资产。

### T2 字段矩阵

生成八 unit × 十二字段的完整 `field_availability.csv`：

`predicted_ar,gt_ar,class_id,confidence,predicted_width,predicted_height,canonical_angle_error,row_key,image_id,mother_scene_id,split_role,official_annotation_id`

每行：`unit,field,status,source_path,source_column,transform_needed,transform_source_path,transform_line,witness`。状态仅 `DIRECT,DERIVABLE,MISSING`；DERIVABLE 只接受已有冻结代码中的可定位变换，不得新发明公式。

### T3 cohort/key 连接

生成 `join_feasibility.csv`。matched cohort、features、scores、class labels、cluster map 各自先验证全表 key 唯一；以既有 matched D_audit cohort 为左表，对其它表 semi-select 后核验 cohort missing/duplicate/drop。右表合法 extras 记录 count 与 sorted-key SHA 且永不进入 cohort。`detection_score` 只在真实拥有该字段的表间核对；禁止臆造三表共有字段。

只允许 schema/count/hash/missingness/key coverage；禁止 risk、AUGRC、Risk@coverage、probe prediction、effect、CI、p、Holm、witness。

### T4 官方标注与 DOTA 来源

生成 `official_annotation_inventory.csv` 和 `dota_gt_provenance.json`。四数据集逐一记录 official root、split、文件数、bytes、manifest SHA。DOTA 明确 official val annfiles、r026/r028 converted GT、来源脚本与已存在 tile/mother/count witness；不得运行转换或宣布等价。

## 4. T5：稿件自足性支持证据

生成 `manuscript_support_inventory.csv`，逐 unit 只定位既有证据：公开 unit 名称映射、config/checkpoint identity、AP50/AP75、匹配阈值/类内一对一算法及实现行、D_cal/D_audit role 算法及实现行、风险常数来源。不存在写 MISSING。本表不参与 ASSET_READY_FOR_R033 gate，但决定下一版稿件是否可自足补全。

## 5. T6：readiness、验证和无环发布

生成 `r033_readiness.json`：

- `ASSET_READY_FOR_R033`：八单元均满足 G1-G3；
- `ASSET_GAP_R032`：列出每个 unit/field/path 缺口及最低恢复动作，恢复动作不执行。

完成 scientific/runtime 输出后再次对 quarantine 做同一 binary hash stream，生成 `legacy_quarantine_after.csv`，before/after 必须逐字节相同。

必交目录 `reports/r032_circularity_asset_preflight/`：

1. `preflight.json`
2. `legacy_quarantine_before.csv`
3. `legacy_quarantine_after.csv`
4. `source_inventory.csv`
5. `field_availability.csv`
6. `join_feasibility.csv`
7. `official_annotation_inventory.csv`
8. `dota_gt_provenance.json`
9. `manuscript_support_inventory.csv`
10. `r033_readiness.json`
11. `execution_ledger.csv`
12. `artifact_manifest.json`
13. `validate_r032.py`
14. `validation_r032.json`

独立 validator 必须从真实文件和表格重算 committed identity、所有输入/输出 path set、bytes/SHA、八 unit × 十二字段笛卡尔积、状态枚举、key coverage、quarantine before/after equality、readiness 映射；不得信任生成端布尔。至少四项临时副本 mutation：删 unit-field、改 source SHA、制造 cohort duplicate、把 MISSING 改 DIRECT；每项必须让同一 validator 非零退出。

无环发布顺序：先提交/push STARTED；再生成全部 runtime/scientific outputs并通过 pristine+mutation；提交/push 结果 commit；最后生成报告，`ending_commit` 写前一个结果 commit 的完整 SHA，再单独提交/push 报告。报告不能自证包含自身的 commit，也不能用占位符。

## 6. 完成和回执

八单元 ready 或有缺口均可 `full_completion`，条件是 T0-T6、STARTED、四 mutation、manifest、报告和全部 push 均闭合。G0/G0Q 合规触发且证据齐全可 `gated_early_stop`。缺 STARTED、必做输出、真实 mutation、quarantine 闭包、报告字段或 push，或使用非冻结同步命令，一律 `failure_early_stop|partial|protocol_drift`。

最终对话严格两行：

1. `执行完毕` 或 `未执行完毕`；
2. `dis/server_reports/orientbench-c-r032-circularity-asset-preflight-retry-20260814/SERVER_EXECUTION_REPORT.md`

禁止增加解释、标题或第三行。
