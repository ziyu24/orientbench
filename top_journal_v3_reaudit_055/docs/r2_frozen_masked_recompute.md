# R2 —— 冻结 masked 管线宽度重算审计（准备）

> 只做 provenance-clean 审计与可复算清单；不重训、不追公开 mAP、不补全矩阵、不启动长任务。
> 日志：`reports/r2_cell_inclusion_exclusion_log.csv`（15 行）。

## 1. 纳入规则
- 只纳入 provenance-clean artifact（真实检测器前向 + 匹配 + checkpoint 校验值）。
- partial / invalid dump 不进主结论；不保留半残证据。
- 不重训 detector。

## 2. 当前可达性（诚实）
| 类别 | cell | 状态 |
|---|---|---|
| **主表（6，clean full-val）** | DIOR#22/#3/#61、FAIR1M#24、SODA#23/#4 | 已纳入，可复算 |
| **masked-only（4，附录/需升级）** | DIOR#10、SODA#11（LSKNet）、FAIR1M#5（ORCNN）、FAIR1M#12（LSKNet） | 仅有 masked 特征表（ar≥1.6），**无 full-val 17 字段匹配表** → 只能算 masked 指标；升级为主表需 full-val 前向+匹配（未来命令） |
| **invalid（1）** | DOTA#20 | 19 图 D_cal 子集，mAP 异常 → 仅候选，需 full-val provenance-clean dump 方可转正；不保留半残 |
| **候选族（需前向推理，非 058）** | Strip、ARS-DETR(DETR 族)、DOTA-v1.0/v1.5 更多 cell、HRSC 真实检测器 | pth_data 有有效 checkpoint，但**无 provenance-clean dump**；HRSC 现仅 synthetic proxy |

## 3. 从 6 扩到 12–15 的可行性（如实记录）
- 通过“masked-only 4 cell 升级 + DOTA#20 转正”最多可达约 11 个，前提是对这 5 个做 **full-val 前向+匹配**（需检测器推理）。
- 达到 12–15 还需前向 dump 若干 checkpoint-only 检测器（Strip / ARS-DETR / 更多 DOTA / HRSC 真实）。
- **blocker：以上均需检测器前向推理，属长任务，不在 058 范围。** 058 只登记可达性与命令建议，不启动。

## 4. 可安全短时复算的部分（命令建议，不擅自启动长任务）
- 6 主表 cell 的 masked NRC / AURC / score menu / conformal 可由现有 provenance-clean 匹配表短时复算（一键脚本已存在，见第三方复算记录）。
- masked-only 4 cell 的 masked NRC 可由 features 表短时复算（仅 masked 指标，不进主表）。

## 5. inclusion/exclusion log 字段
cell_id、dataset、detector、artifact_path、artifact_sha256、provenance_status、dump_status、can_recompute、included_main、exclusion_reason、next_action。（见 CSV）

## 6. 结论
当前 provenance-clean 主表宽度为 **6 cell（3 检测族 × 3 数据集）**。扩到 12–15 是路线目标，但受限于“需新前向 dump”，本轮如实标为 blocker，不虚报宽度、不将 partial/invalid 计入主结论。

## 7 本轮复算结果
- 6 主表 cell 的 masked NRC/AURC/Risk@70/90 已复算（`reports/r2_all_clean_cells_masked_metrics.csv`），全部可复算、NRC 0.41–0.91（非反序）。
- 4 masked-only 特征 cell（DIOR#10/SODA#11/FAIR1M#5/FAIR1M#12）masked NRC 已算（附录性质，不进主表）。
- conformal 尾部表与 score menu 已归档（`reports/r2_conformal_tail_tables.csv`、`r2_score_menu.csv`）。
- **当前 clean full-val 主表宽度仍为 6**；扩到 12–15 需新前向 dump（检测器推理，长任务，非本轮）。DOTA#20 仍 invalid（19 图子集），未转正。

## 8 060 状态（前向队列准备，未抢占 R1）
- clean full-val 主表宽度仍 **6**；本轮未新增（R1 4 卡训练占用，按指令 R1 优先，避免与 R1 + 外部 D17 抢卡）。
- 候选族前向 dump（Strip / ARS-DETR / 更多 DOTA / HRSC 真实）**命令与资源估计已备**（`logs/r2_frozen_recompute_060.log`），排在 R1 队列之后执行；每 cell 需 pth_data checkpoint + full-val 4 卡推理 + 匹配 → provenance-clean dump。
- DOTA#20：仍 invalid（19 图子集），未转正；需 clean full-val dump 方可计入。
- masked-only 附录 cell（DIOR#10/SODA#11/FAIR1M#5/FAIR1M#12）masked 指标已在 `reports/r2_all_clean_cells_masked_metrics.csv`。

## 9 061 状态（R1 训练占卡，R2 不抢占）
- clean full-val cells 仍 **10（6 主 + 4 附录）**；本轮**未新增**。原因：R1 4 卡训练本轮实际在跑
  （PSC/DIOR-R seed1 已从 epoch8 恢复并训练，队列继续 seed2→SODA→CSL/DCL/KLD/regression），
  R2 候选族 dump 需 full-val 4 卡推理，会与 R1（+外部 D17）抢卡；按指令 **R1 优先**，故 R2 不启动。
- DOTA#20：状态不变，仍 invalid（19 图 D_cal 子集，mAP 异常），未转正；需 provenance-clean full-val
  前向 dump 方可考虑（GPU 资源被 R1 占用，本轮不做）。**未保留 19 图半残证据进主结论**。
- 无新增 masked-only 附录 cell。R1 训练完成、GPU 空出后再推进 R2 候选族 dump。
