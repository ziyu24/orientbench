# Codex 接手 Claude Code：068 后只读交接审计

审计时间：2026-07-14 22:41 CST（2026-07-14 07:41 PDT）

审计范围：只读核对 067、068、冻结资产、科学状态、后台进程和复算入口。本轮未启动训练、推理、评估、bootstrap 或正式 069，也未改动任何科学结果。

## 1. 正式命令编号状态

| 编号 | 交接口径 | 服务器取证结论 |
|---|---|---|
| 067 | 已完成 | K2 full-converged 矩阵完成；PASS、结局 A。 |
| 068 | Claude Code 已执行 | 2026-07-12 18:33:55 PDT 开始，18:44:47 PDT 完成；唯一项目产物是中文论文。 |
| 069 | 本轮尚未执行 | Codex 本轮没有启动 069，必须等待监督员单独执行令。服务器同时存在一轮更早的 `069-REPLACEMENT` 完整运行记录，见第 12 节；因此不能把“069 从未执行过”作为服务器事实。 |

当前操作口径：把既有 `069-REPLACEMENT` 产物标为“post-068、命令编号冲突、待监督员裁定”，不在本轮重跑、采纳、覆盖或删除。

## 2. 068 的真实完成状态

- 原始命令记录：`/home/rspip/.claude/projects/-home-rspip-cqc-pro-study-orientbench/2f5fe955-706f-470f-998e-f4baddcfb761.jsonl`，用户命令时间 `2026-07-13T01:33:55.415Z`。
- 开始时间：2026-07-12 18:33:55.415 PDT（2026-07-13 09:33:55.415 CST）。
- 文件写入时间：2026-07-12 18:43:21.889 PDT。
- 完成汇报时间：2026-07-12 18:44:47.377 PDT（2026-07-13 09:44:47.377 CST）。
- 状态：产物层面已完成；完成汇报存在于 Claude 会话，但此前未写入根目录 `claude_code_and_supervisor.md`。
- 实际动作：读取 K1/K2/K3/K4、conformal、selector 和旧稿；创建输出目录；写一份论文；执行 grep、图片引用、threshold SHA 和 git status 自检。
- 068 未执行训练、推理、评估、bootstrap 或主表复算；未运行 `reproduce_all_main_tables.sh --fast` 或 dry-run。

## 3. 068 产物清单

068 只生成一个项目文件：

- `docs/paper_zh_post_k1k4_068/orientation_reliability_paper_zh.md`
  - 361 行，46,440 bytes。
  - SHA-256：`8104f4c059428cf7330179cc83939049c0a4ff47e37e84bf3fc107e51b0c35b0`。
  - 当前未被 Git 跟踪；与 Claude file-history 快照一致，之后未被改写。

068 没有生成独立 CSV、脚本、图片或项目日志。`top_journal_v3_reaudit_055/reports/068_*` 和 `outputs/logs/reproduce_all_main_tables_068.log` 的时间均晚于 068，属于后续 `069-REPLACEMENT`，不得计入 068。

## 4. 当前权威论文文件

当前 068 时点的权威中文稿：

`docs/paper_zh_post_k1k4_068/orientation_reliability_paper_zh.md`

它 supersede：

- `top_journal_v3_reaudit_055/docs/paper_zh_s1s5_v3_review/orientation_reliability_paper_zh_s1s5_v3_review.md`；
- 更早的 054 reduced-scope 中文稿和 R1 preliminary 机制段。

现有 post-068 M1/M2/M3/M4/PSC 结果尚未写回该稿；本轮按禁令没有修改论文。

## 5. 当前权威结果表

| 主题 | 权威来源 | 当前状态 |
|---|---|---|
| K1 full-val AP | `top_journal_v3_reaudit_055/reports/table1_fullval_final_065.csv` | PASS；六单元 full-val，`dAP50=0`。 |
| K2 angle-coder | `reports/k2_go_no_go_decision_067.csv`、`k2_angle_coder_block_results.csv` | PASS、结局 A；K2 supersede 旧 R1。 |
| K3 GT-noise proxy | `reports/k3_gt_angle_noise_by_dataset.csv` | PARTIAL；corner-jitter refit proxy，非人工双标。 |
| K4 mask threshold | `docs/k4a_mask_threshold_principle.md`、`reports/k4a_*.csv` | derived `ar≈2.1` 分析 PASS。 |
| DOTA clean full-val | `reports/k4b_dota_full_val_metrics.csv` | ORCNN、RTMDet-M 两个 clean 单元；DOTA#20 排除。 |
| 068 conformal | `reports/pre_submission_s1s5_v1/s1c_ltt_conformal_tables_v1.csv` | 068 稿仍用实例级 exact-binomial 主保证；待图像级重构。 |

完整路径与重算入口见 `reports/codex_takeover_authoritative_sources.csv`。

## 6. 当前权威复算脚本

入口：`scripts/reproduce_all_main_tables.sh`，SHA-256 `7fef8f7cc1ac8e27463d72d24f0e8ea4934454a823aea96b82bef54e63668bc7`。

审计结论：

- `bash -n` 静态语法通过。
- 当前版本在 068 后被追加了 069 M1/M2/M3/M4/PSC/human 步骤；即使 `--fast` 也会执行这些步骤，不是 dry-run。
- 当前版本从未端到端运行。最新完整 `--fast` 日志是 2026-07-08 的 `reproduce_all_main_tables_066.log`，早于当前脚本修改。
- `outputs/logs/reproduce_all_main_tables_068.log` 只有两次一致性检查，不是一键复算日志。
- 当前入口仍聚合旧 `r1_eval`，没有直接聚合权威 `k2_eval`；若干步骤只做 presence/assertion 检查，部分 nonzero 被日志吞掉。
- 结论：脚本是当前固定入口，但在监督员裁定 069 冲突前不得运行，也不能称已验证的一键复算链。

第三方复算说明：`docs/third_party_reproduction_log.md`，SHA-256 `ad74ca34a23150661b32eba627fca8b6059f342c8d595fecca2f1180b6517a53`。它描述了有争议的 post-068 产物，不等同于当前脚本已端到端通过。

## 7. 当前后台进程

- 当前没有 orientbench watcher、keeper、torchrun、训练、推理、评估、bootstrap、annotation server、reproduce 或 M069 进程。
- 当前 orientbench CWD 下只有本次交互式 Codex 接手会话及其 code-mode host，不是后台科学任务。
- 既有 M069 keeper 于 2026-07-12 21:21:45 PDT 正常退出。
- 两个 Claude 进程和一个长推理进程属于其他项目；四个 zombie 也属于其他项目，均未处理。
- 未发现可确认的 orientbench 无效残留，因此本轮没有清理或 kill 任何进程。

详见 `reports/codex_takeover_process_audit.csv`。

## 8. 当前冻结资产校验

### thresholds

- `configs/thresholds.yaml` SHA-256：`b7c4e649b1a3de6d0c985a5f20dc5ba70a8fb3e428c3c184e2f86bf96d593fae`。
- 与 release copies 字节一致；mtime 为 2026-06-27；068 和本轮均未修改。

### D_cal / D_audit

- 十个 split 文件 mtime 均为 2026-06-25。
- `outputs/bench_core/splits/splits_summary.json` 仍为 deterministic、intersection=0、`all_mutually_exclusive=true`。
- 精确 SHA-256 已写入 `reports/codex_takeover_artifact_inventory.csv`；068 和本轮均未修改。

### host

- RHINO 当前 checkpoint 与 lock 均为 `55a90abbace429276e593f8e4418fad002240ff1951912172367d997b474f9d9`。
- O2-RTDETR/A4 当前 checkpoint 与 lock 均为 `3e32fa11114ced82c2fb5ecdb25031ff45c1d2815b034a315b1af11ef8487e32`。
- checkpoint mtime 为 6 月 26/27 日；没有 068 或本轮重训。

### formal / exploratory

- `outputs/bench_core/reports/full_matrix_execution_plan.csv` SHA-256 为 `33bf3ddab6374fea807018b8e82ccfc1629a34e735cb2f020daf4fe7fa93ffef`，与 `_020.csv` 一致。
- DOTA 仍为 formal-compatible；DIOR/FAIR1M/HRSC 仍为 cross-dataset exploratory；SODA 在 claim ledger/final matrix 中仍为 exploratory。
- 068 没有改标签文件。

### DOTA#20 与持久化

- `k4b_dota_cell_inclusion_exclusion_066.csv` 仍明确排除 DOTA#20。
- 当前 K1 GT、结果 CSV 和 052 matched tables 均已持久化，因此没有运行时必须读取 `/dev/shm` 的主表文件。
- 但存在重要 provenance 债务：068 的 NRC/conformal/geometry A-F 表仍来自 052 matched dumps。DIOR 三单元的记录来源是现已丢失的 `/dev/shm` GT，只有 5,863 图/35,436 GT；K1 full test 是 11,738 图/124,445 GT。持久化消除了实时文件依赖，没有消除 partial-GT lineage。

## 9. 当前核心科学结论

### K1

PASS。full-val AP50 为 DIOR PSC/ORCNN/RTMDet `0.5368/0.6448/0.6462`、FAIR1M PSC `0.3462`、SODA PSC/ORCNN `0.5991/0.7295`；六单元受约束扰动 `dAP50=0`，AP75 显著下降，角度误差升至约 34-41 度。

### K2

PASS、结局 A。PSC phase_mod 在 DIOR/SODA 的 mean NRC 为 `1.2504/1.1527`，三 seed 的 CI 下界均大于 1；PSC detection score 为 informative/non-reversed。CSL 近随机，DCL 明显 informative。只允许写成充分收敛下可复现的 `PSC-specific phase_mod reverse-ranking`，不能推广为通用 angle-coder failure。

### K3

PARTIAL。ar>=1.6 proxy 均值为 DIOR `3.478`、FAIR1M `5.730`、SODA `7.808` 度；ar>=2.1 为 `3.004/4.455/5.856` 度。均值风险与 5 度尾部必须 label-noise-aware；人工双标仍未完成。

### K4

derived `ar≈2.1` 已进入 068 稿摘要、方法与第 4 节，不再只存在于分析文档。但正文表 4/10 仍是 ar>=1.6，表 5 是 ar>=2.0，DOTA 原表也是 ar>=1.6，尚未真正统一。

### Conformal

068 稿正式保证的实质统计单位仍是 instance-i.i.d.：实例级 exact binomial 承担尾部保证，图像级 cluster bootstrap 仅给区间。图像作为 exchangeable unit 的 bounded-loss UCB 尚未进入 068 稿。

### Geometry score

当前定位仍是用目标域 GT angle error 拟合的 calibration/upper-bound，不是 deployable method。068 稿明确把 fixed-size-bin 和无目标域 GT 版本列为开放问题。

## 10. 已 supersede 的旧结果

- K1 full-val AP supersede 旧 DIOR partial-GT AP：`0.6964/0.7999/0.8866` 已替换为 `0.5368/0.6448/0.6462`。
- K2 full-converged 067 supersede R1 063/064 preliminary；旧 R1 不再单独支持机制结论。
- derived `ar≈2.1` supersede 把 ar>=1.6 当唯一主口径的写法；ar>=1.6/1.3 只能是 sensitivity，但数值迁移尚未完成。
- 两个 K4b clean DOTA full-val 单元 supersede DOTA#20 的 19 图不完整单元。
- masked 结果 supersede 旧 unmasked PSC detection-score 反校准叙事；当前是 detection score informative、PSC native phase_mod 反序。
- 068 中文稿 supersede 065 v3 和更早 reduced-scope 稿。

## 11. 068 留下的 blocker

1. ar>=2.1 只完成叙事迁移，没有完成所有正文候选表的数值迁移。
2. 缺 `score+ar+size` 线性基线与 fixed-size-bin G2_double_prime。
3. 实例级 exact-binomial 仍被当作正式保证，缺图像级 bounded-loss 主保证。
4. 缺明确的 delta/FWER 数值与 n_fit/n_cal/n_audit 完整报告。
5. 人工双标未完成；K3 仍只能是 proxy/PARTIAL。
6. 068 稿把表 8 的 SODA-A ORCNN 低覆盖结果误写成 DOTA ORCNN。
7. 参考文献仍有“精确字段以官方出处为准”的占位式免责声明，且缺 conformal object detection 覆盖。
8. 068 reliability 主表仍有 DIOR partial-GT 052 lineage，不能把六个 reliability 单元全部称为 full-val。
9. 当前一键复算脚本未对其 post-068 版本做端到端验证。

字面检查方面，068 无 TODO/TBD/FIXME/待补、无图片或图片占位，文本自检通过；这不等同于数值与复算链通过。

## 12. 服务器上已存在的 069-REPLACEMENT

取证事实：

- 用户在 Claude 会话于 2026-07-12 20:13:14 PDT 下发 `BEGIN COMMAND 069-REPLACEMENT`。
- `top_journal_v3_reaudit_055/logs/m069/master.log` 记录 20:42:34 启动、21:21:28 结束；keeper 21:21:45 退出。
- 实际运行了两个 DOTA dump/inference、M1、M2、M3、M4、PSC Phase1、human merge/analyze 和 freeze/repro；均记录 rc=0；没有 detector 训练。
- 磁盘结果：M1 PASS；M2 FAIL；M3 PASS；PSC Phase1 branch A/PASS；人工双标 PENDING；最终 NOT_FROZEN。
- M2 FAIL 的现有最小证据：仅 cell B 有至少两个显著 size bins，7/15 bins 显著，未满足至少两个 cells 的通过条件。

这些事实直接冲突于本次交接令的“069 尚未执行”。本审计不自行裁定其科学有效性，也不把它们作为本轮 069 新结果；必须由监督员明确选择“追认现有运行”或“废止并重新编号/命名空间”。

## 13. 069 可直接复用的脚本和产物

### 已有权威输入，不能重复

- K1：`table1_fullval_final_065.csv`、persistent K1 GT、六个 baseline checkpoint/config。
- K2：18 个 `reports/k2_eval/*.json`、K2 block/seed/decision 表和完整 work dirs。
- K3：proxy 表与 `scripts/k3_gt_angle_noise_proxy_audit_066.py`。
- K4a/K4b：derived-ar 表、两个 clean DOTA full-val 表和对应脚本。
- 冻结 thresholds、D_cal/D_audit、host checkpoint locks。

### 已存在但待追认的 post-068 工具

- `scripts/m069_common.py`、`m1_ar21_unify.py`、`m2_g2doubleprime_ar21.py`、`m3_image_level_risk.py`、`m4_risk_events.py`。
- `scripts/psc_phase1.py`、`m_dota_dump.py`、human annotation build/merge/analyze 脚本。
- `scripts/m069_master.py`、`run_m069.sh`、`m069_freeze_and_repro.py`。
- M1/M2/M3/M4/PSC CSV、两份 DOTA per-instance dump、annotation task manifest 和 freeze gate。

注意：现有 sentinels 会让 `run_m069.sh` 直接退出、让 direct master 跳过多数步骤。正式 069 不能盲目重跑；必须先裁定并隔离/命名现有产物。

## 14. 069 的真实执行起点

监督员单独下发 069 后，第一步不是启动脚本，而是处理命令编号冲突：

1. 决定是否追认 2026-07-12 的 `069-REPLACEMENT`。
2. 若追认：不重复 K1/K2/M1-M4/PSC/DOTA dump；先独立验证实现、数据 lineage、CPU 规则和当前复算链，再执行 M2 FAIL 对应的早停/降级裁决，并等待真人双标。
3. 若不追认：先在不覆盖旧产物的前提下建立新命名空间和 sentinel 策略，再从 068 权威输入启动；这需要监督员授权，当前未做。
4. 无论哪条分支，都应先解决 DIOR reliability 表的 partial-GT lineage，并校正当前复算入口；不得修改 thresholds、D_cal/D_audit 或为保留 geometry gain 改 bins/split。

当前真实 blocker：069 编号/追认冲突、现有 M2 FAIL、人工双标未返回、068 reliability 表的 DIOR partial-GT lineage、当前复算脚本未端到端验证。

本轮接手审计已完成，具备接收监督员单独命令的条件；在该命令到达前不执行 069。
