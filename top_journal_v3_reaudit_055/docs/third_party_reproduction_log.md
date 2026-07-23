# 第三方复算接口审计（不执行完整复算）

> 本轮只审计接口与缺口，不执行完整复算、不启动长任务。

## 1. 是否存在单命令脚本
- **存在**：`top_journal_v3_reaudit_055/scripts/reproduce_all_main_tables_s1s5_v1.sh`（一键从 provenance-clean artifact 复算）。
- 根目录 `scripts/reproduce_all_main_tables.sh`（无版本号）**不存在**；如需固定命名入口，建议后续以符号链接或副本提供，指向上述脚本。

## 2. 能否从 raw / persistent artifacts 生成各主表
| 目标 | 来源脚本/数据 | 状态 |
|---|---|---|
| 表 2（全评测器扰动 AP/risk） | `s1a_full_pipeline_perturb_v1.py`（raw preds + gt） | **覆盖** |
| 表 3（masked NRC/AURC） | `s3` 汇总 + a0 masked 重算（052 匹配表） | **覆盖**（表由 A0 重算 + S1b 汇总派生） |
| 表 4（conformal LTT） | `s1c_ltt_conformal_v1.py` | **覆盖** |
| 表 5（score menu 覆盖） | `s1b_independence_fix_v1.py` | **覆盖** |
| 表 6（phase_mod 机制） | `s2_psc_mechanism_v1.py` + a0 bootstrap | **覆盖** |
| 表 7（角度单位下游） | `s4_downstream_angle_unit_v1.py` | **覆盖** |
| P1 perturbation（dose-response） | `s1a_full_pipeline_perturb_v1.py`（副产 dose-response CSV） | **覆盖** |
| phase_mod tables（NRC/CI/confounding/aliasing） | `s2` + a0 bootstrap | **覆盖** |
| 表 1（单元概览） | 派生自 `full_matched_tables_052.csv`（未由一键脚本单独产出） | **缺口**：需加一步汇总 |
| 表 8 / claim ledger | 文本（`final_claim_ledger_reaudited_056.md`） | 非脚本产物 |
| NRC 方向示意 / IoU-δθ 曲线 | 示意/理论表（静态） | 静态数据 |

## 3. 缺口清单
1. 一键脚本未单独产出**表 1（单元概览）**——需补一步从 `full_matched_tables_052.csv` 汇总。
2. 一键脚本对**表 3** 依赖 A0 重算 CSV（`a0_nrc_masked_unmasked_recompute`）而非在脚本内重跑 A0——需在脚本内显式加入该重算步骤以实现真正“从 raw 到表 3”。
3. 无根级固定命名入口 `scripts/reproduce_all_main_tables.sh`。
4. **SODA 全评测器扰动为长任务**（约 68 万–145 万框），一键脚本会触发；第三方复算需预留算力/时间，非秒级。

## 4. 一致性说明
- 现有脚本从 provenance-clean artifact 生成表 2/4/5/6/7 与 P1 dose-response，运行前后校验 thresholds 校验值不变、标定/审计划分无 diff。
- 表 1 与表 3 的完全自动化尚有缺口（见上）；在补齐前 **不得声称第三方一键复算已完备、不得声称投稿准备完成**。

## 5. 后续命令建议
- 059+：在一键脚本内补“表 1 汇总步骤”与“A0 masked 重算步骤”，并提供根级固定命名入口；再由第三方在干净环境跑一次全链、比对数值一致性。

## 6 本轮更新（root 入口 + 缺口关闭 + dry-run）
- **新增根级固定入口**：`scripts/reproduce_all_main_tables.sh`（只读，运行前后校验 thresholds sha256=b7c4e649…；`--fast` 跳过长任务 S1a）。
- **058 缺口关闭**：
  1. 表 1 汇总步骤已加入（产出 `reports/table1_cell_overview.csv`）。
  2. 表 3 内联 A0 masked 重算（脚本内直接跑 `a0_nrc_recompute_055.py`，不再依赖预生成 CSV）。
  3. 根级固定命名入口已提供。
- **dry-run（--fast）结果**：Table 1/3/4/5/6/7 + Fig 2 全部重算成功；thresholds 未变；Table 2（S1a 全评测器，68 万–145 万框/cell）为长任务，`--fast` 下跳过并打印完整命令，不伪装已完成。
- **一致性**：确定性步骤（A0 masked NRC、conformal、phase_mod、downstream、IoU 曲线）重算数值与既有主表一致。
- **未声称**：第三方一键全链（含长 S1a）已完备、投稿准备完成——文献精确字段仍需最终核对，故不声称可投稿。

## 064 — R1 valid-head blocks entry added to main reproduce chain
- `scripts/reproduce_all_main_tables.sh` 新增 **R1 blocks** 段：从持久化的每-run 评测产物
  `reports/r1_eval/*.json` 复算 block seed-variance（`aggregate_r1_eval_063.py`），并**校验**
  `reports/r1_failed_training_audit_final_064.csv` 记录 12 个 failed_training（direct_regression NaN + KLD AMP/fp16）。
- 复算粒度 = 对 provenance-clean per-run JSON 的聚合；**多小时 4 卡推理本身不入主链**。
- **exploratory rescue 不入主复算链**（附录、`exploratory_rescue_not_preregistered`）。
- Dry-run（`--fast`）：PASS —— eval JSONs 18/18、failed audit OK(12)、thresholds b7c4e649 未变。
  日志：`logs/reproduce_all_main_tables_064.log`。无 blocker。

## 065 — 一致性 dry-run（不重跑长任务）
- `scripts/reproduce_all_main_tables.sh --fast`：PASS。Table 1/3/4/5/6/7 + Fig 2 确定性步骤重算成功；
  R1 blocks 从持久化 per-run 评测产物聚合（eval JSONs 18/18）；R1 failed audit OK（12 runs：直接回归 NaN + KLD 半精度不兼容）；
  thresholds b7c4e649 未变。日志：`logs/reproduce_all_main_tables_065.log`。
- Table 2（S1a 全评测器）为长任务，`--fast` 跳过并打印完整命令，不伪装已完成。
- rescue 不入主复算链。**无不一致、无 blocker**；但仍不声称论文版本可冻结（书目精确字段待终核）。

## 065 — K1 表1 GT 检查入口
- reproduce_all_main_tables.sh 新增 [K1 GT] 段：校验 full-val GT manifest、DIOR n_gt=124445、禁止 /dev/shm 主表 GT。
- dry-run(--fast) PASS：DIOR n_gt=124445, 3 持久化 GT 集, 无 /dev/shm 主表 GT；thresholds b7c4e649 未变。
- 表1 六单元 full-val 重算进行中(非冻结)；不声称可冻结。

## 066 — K1-K4 审计入口
- reproduce_all_main_tables.sh 新增 [066] 段：校验 6 K1 anchor、无 /dev/shm 主表 GT、DIOR n_gt=124445、2 clean DOTA cell(无 D20)、geometry/linear GT-fit=upper-bound 已标记。
- dry-run(--fast) PASS；thresholds b7c4e649 未变。4 持久化 GT 集(DIOR/SODA/FAIR1M val20/FAIR1M val空)。
