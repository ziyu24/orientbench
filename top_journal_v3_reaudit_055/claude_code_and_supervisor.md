
## [2026-07-02 23:41:35 PDT] 来源: supervisor 指令 055 (Claude 接手 re-audit)
- 动作: 启动 055 re-audit；建 top_journal_v3_reaudit_055/ 目录树。
- A0 完成（门控项）: NRC 协议漂移法证 = B 正确且更严重。
  - 权威源 052 matched_17field。detection-score masked ar>=1.6: DIOR#22 0.542[0.529,0.556]/FAIR1M#24 0.885[0.865,0.907]/SODA#23 0.914[0.903,0.926] 全部显著校准(NRC<1) → 053/054 的 1.1265/1.5061/1.6733 是 near-square pooling artifact = Codex 执行错误(协议漂移)。
  - measure_fix 的 FAIR1M 1.083/SODA 1.260「masked 反校准」用弱 mask，ar>=1.6 下不成立 → superseded。
  - intrinsic phase_mod masked ar>=1.6 仍显著反校准: DIOR#22 1.129/FAIR1M#24 1.101/SODA#23 1.090 (CI>1) → 幸存机制候选。
  - DOTA#20 = 19图 D_cal subset dump, mAP 0.0132 无意义 → invalid_pending。
- 产物: docs/a0_{protocol_drift_audit,supersedes_memo,dota20_artifact_integrity,evidence_lineage_reconciliation}_055.md; reports/a0_{nrc_masked_unmasked_recompute,masked_nrc_bootstrap_ci,dota20_integrity,evidence_lineage_reconciliation}_055.csv
- pass/fail: A0 = PASS(完成裁决)。未触发停止条件。未改 thresholds/split, 未训练/推理。
- 下一步: A1 conformal 强化 / A2 约束扰动 / A3 测量层身份 / A4 P4 / A5 下游 / A6 写作 / 最终裁决。

## [2026-07-03 00:15:05 PDT] 055 完成
- 全部 A0-A6 + Task0 + 最终裁决 + 验证完成。verify_reaudit_055.py = 45/45 PASS。
- 关键裁决: Codex 执行错误(协议漂移/DOTA#20 subset/均匀扰动)=是; detection-score 反校准作废(pooling artifact); phase_mod 反校准幸存(机制候选); P1 precise-pass; P2 空洞->有效(strict 区); P4 几何选择器(6/6 sig); P5 微弱->附录; 身份=protocol+risk control; 遥感期刊有条件强候选(非顶会 ready)。
- 合规: thresholds.yaml sha256 b7c4e649(未变); D_cal/D_audit 未改; 未训练/未推理/未补 full matrix; git 无 >100MB tracked; 未覆盖 049-054 产物。
- 计算: A0 recompute+bootstrap(mr_dev1x py); A1 conformal; A2 约束扰动(shapely); A4 P4; A5 downstream. logs in top_journal_v3_reaudit_055/logs/.
- 主回执: top_journal_v3_reaudit_055/docs/cc_latest_report.md

## [2026-07-03 01:10:17 PDT] 056 完成: 从 re-audit 重写正式中文论文
- 主交付: docs/orientation_reliability_paper_zh_reaudited.md (正式论文, 12 节 + 图占位 Fig1-9 + 表1-9 + 附录A-I); 配套 coauthor_review_note_056.md + final_claim_ledger_reaudited_056.md。
- 身份: Orientation Reliability Measurement Protocol + Finite-Sample Conformal Risk Control。P1 precise-pass(动机)/P2 主贡献(脊柱)/P4 并入 P2 打分菜单/P3 机制候选边界/P5 附录边界。
- 清除 Codex 错误: 正文不用 unmasked NRC headline(记附录E作废); DOTA#20 invalid_pending 排除主表; 均匀扰动->约束扰动; phase_mod=候选; 下游非成功。去项目化(无 055/监督/verifier/本轮 于正文)。
- 验证: verify_reaudited_paper_056.py 28/28 PASS; pytest 17 passed; thresholds b7c4e649 未变; D_cal/D_audit clean; git 无大文件。未训练/未推理/未新增实验。
- 建议: 交合作者审稿。

## [2026-07-15 19:50:33 -0700] 命令 071 完成：人工双标包物理落盘纠错
- 070 包原位于外层仓库 `annotation_tools/m4_angle_annotation/`，未落在本权威项目根，属于路径口径错误及汇报未明确实际根目录。
- 最终执行包已落盘至 `annotation_tools/m4_angle_annotation/`；A/B 各 1500 项，三数据集各 500 项，工具端到端验证通过。
- 真人结果 A=0、B=0；未伪造，状态保持 HUMAN_BLOCKED。未训练、未推理、未改论文、thresholds 或 D_cal/D_audit。下一编号 072。

## [2026-07-16 01:31:48 -0700] 071 网页交互修订
- 备注已移至底部；导航、图片模糊/ambiguous、skip、保存与导出已移至图片右侧。
- A/B 顺序均已打乱且同位置实例重复为 0；实例集合不变。
- 工具复验 PASS；annotator A 已有 3 条草稿被完整保留，正式导出仍为 0。
- 后续在“下一个”旁增加“放大图片”全屏按钮；草稿、任务顺序及正式输出状态未改，复验 PASS。
- 放大交互再修订为“上一个｜放大图片｜下一个”，使用不改变页面布局的独立图片窗口；窗口内可直接拖画角度，草稿未改。
- 放大交互最终改为“下一个｜放大图片｜还原图片｜上一个”；图片在原 viewer 内镶嵌式放大/还原，仍可直接拖画角度，用户当前草稿完整保留。
- 放大改为每次点击约 1.3 倍（至少 80px）的逐级放大，到区域上限后停止；还原按钮恢复原尺寸，绘图 canvas 同步缩放。

## [2026-07-17 01:40:12 PDT] 人工双标 200 条 pilot 冻结与 B 包交付
- 已冻结 A 前 200 条任务与当前真人草稿快照；B pilot 使用相同 200 个实例、独立匿名 ID 和不同随机顺序。
- 数据分布：DIOR-R=61、FAIR1M=77、SODA-A=62；A 当前为角度 151、ambiguous 27、skip 17、pending 5；B 真人结果为 0。
- B 启动入口：`annotation_tools/m4_angle_annotation/start_annotator_B_pilot_200.sh`；完成后由 `../scripts/run_m4_pilot200_analysis.sh` 计算预先固定的圆周角差和分层指标。
- 未伪造人工结果；状态保持 HUMAN_BLOCKED，未训练、未推理、未改论文或冻结资产。

## [2026-07-17 21:35:00 PDT] 200 条人工双标 pilot 中期核验
- B 当前 202 条来自 full 随机清单，与 A 前 200 条实际只重合 24 条，其中 17 对具有双方有效角度。
- 初步圆周角差：mean=2.1921°（image-cluster bootstrap 95% CI 1.3507°–3.1526°）、median=1.7347°、p90=4.0902°、p95=5.1923°、P(>5°)=5.88%、P(>10°)=0。
- 结论为“值得完成正确的 200 对 pilot”，但当前规模不能作论文 claim，也不足以直接决定扩至 1500。
- 已保留全部 202 条 B 真人草稿，并把重合 24 条带入正确 pilot；B 剩余 176 条，正确服务已在端口 17802 启动。状态仍为 HUMAN_BLOCKED。
- 界面随后纠正为只展示剩余 176 条；已完成的 24 条独立冻结、不再重复展示，最终分析前自动合并为完整 200 对。

## [2026-07-17 22:52:00 PDT] M4 200 对 pilot 完成分析与扩量裁决
- 同 canonical 200 对已完成合并分析，149 对角度可用；DIOR-R=38、FAIR1M=60、SODA-A=51。
- mean=2.0938°（image-cluster bootstrap 95% CI 1.8016°–2.3932°），median=1.7137°，p90=4.5579°，p95=5.5849°，P(>5°)=7.38%，P(>10°)=0。
- ar>=2.1 的 100 对 mean=1.9702°；小目标和 1.6<=ar<2.1 更易分歧，方向支持既有 label-noise-aware 边界。
- 论文门控判定 PASS：建议继续冻结的 500×3 目标；A 的 5 条 pending 需补齐。全量真人结果未完成前仍为 HUMAN_BLOCKED。

## [2026-07-17 23:00:00 PDT] M4 全量剩余 A/B 执行包生成
- A 已有 195 条有效决策被冻结，剩余页面为 1305 条；B 已有 377 条有效决策被冻结，剩余页面为 1123 条。
- 两套剩余清单独立打乱，已完成项目不再展示；pending 自动回到剩余任务，没有伪造或修改真人结果。
- 启动脚本为 `annotation_tools/m4_angle_annotation/start_annotator_A_remaining.sh` 与 `start_annotator_B_remaining.sh`；全量完成后运行 `../scripts/run_m4_full_human_analysis.sh`。
- A/B 启动、图像、数量、集合覆盖和后续合并入口均验证 PASS。
- 后续发现旧标准启动脚本仍会加载 full 清单，导致 B 显示 `202/1500`；A 同样存在该风险。所有 A/B 启动别名现已统一为 `full_remaining`，正确服务核验为 A=1305、B=1123，原真人草稿未改。

## [2026-07-21 20:33:04 CST] 冻结 B 当前 526 条并生成 A 匹配任务
- B 当前 526 条有效决策已冻结（DIOR-R=170、FAIR1M=177、SODA-A=179），B 服务暂停以防集合漂移。
- A 已覆盖其中 195 条，只需补 331 条；新页面仅显示该 331 条并已在 17801 启动，任务集合、图像与空白新状态验证 PASS。
- A 完成后由 `../scripts/run_m4_b526_analysis.sh` 合并并生成与 200 对 pilot 相同的核心与分层指标。

## [2026-07-21 22:15:00 CST] M4 526 对分析与证据充分性裁决
- 526 个同 canonical 目标已完成分析，393 对角度可用；mean=2.3587°（cluster-bootstrap 95% CI 2.0096°–2.8696°），median=1.6435°，p90=4.4043°，p95=5.8572°，P(>5°)=7.63%，P(>10°)=1.02%。
- 方向与 200 对 pilot 一致，足以支撑总体 human-noise anchor；SODA-A 包含全部 4 个 >10° 分歧，其中一个为 84.22°，保留不作事后删除。
- 目标数 DIOR-R=170、FAIR1M=177、SODA-A=179，仍低于预注册每数据集最少 200；最小合规补量为 74 对。若保留正式 class/size/tail 分层 claim，仍需继续至 500×3。状态保持 HUMAN_BLOCKED / NOT_FROZEN。
- 526 条均已完成；393 仅指双方都有数值角度的可用对。排除的 133 对为双方 ambiguous 88、双方 skip 3、单方 ambiguous 30、单方 skip 12，无 pending，非数据丢失。

## [2026-07-21 22:27:39 CST] M4 补至 600 并启动单方未标重检
- 新增同 canonical 双标目标 74 个：DIOR-R=30、FAIR1M=23、SODA-A=21，使总目标恰为每数据集 200。
- 原 526 对中单方有角度、另一方 ambiguous/skip 的 29 个进入互盲重检：A=12、B=17；新匿名 ID、混合随机顺序，不覆盖 primary 原标注。
- A 页面 86 条、B 页面 91 条，17801/17802 服务已启动并验证 PASS；完成后由 `../scripts/run_m4_m600_analysis.sh` 生成主分析和重检次级分析。

## [2026-07-21 23:05:00 CST] M4 600 对最低协议完成与重检分析
- 600 个 primary 目标已完成，三个数据集各 200，无 pending；450 对数值角度可用。
- mean=2.3112°（cluster-bootstrap 95% CI 1.9970°–2.7854°），median=1.6359°，p90=4.4220°，p95=5.9359°，P(>5°)=8.00%，P(>10°)=0.89%；ar>=2.1 的 n=308，方向稳定。
- 29 个单方未给角度的重检中 27 个转为数值角度，2 个仍 ambiguous；重检只作 secondary，不覆盖 primary。
- 最低人工协议判定 COMPLETE。600 已足够支撑总体、dataset 和 ar 边界 claim；仅正式 rare-class/size/extreme-tail 分层仍需 1500。

## [2026-07-21 23:15:00 CST] 命令 072 完成汇报归档
- 072 最终权威结果为 600 primary 双标目标、450 数值角度对及 29 条单方未标重检；最低人工协议 COMPLETE。
- 正式汇报：`../docs/072_completion_report.md`、`../reports/072_completion_status.csv`、`../logs/072_completion.log`。
- 未执行训练/推理，未改论文或冻结资产；全局 submission freeze 未在本命令宣称。下一正式编号 073。
