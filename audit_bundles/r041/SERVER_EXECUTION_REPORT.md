---
schema_version: 2
dispatch_id: orientbench-b-r041-panorama-repair-20260817
plan_id: b-r041-panorama-repair-20260817
initiator: B
plan_path: dis/plans/B/b-r041-panorama-repair-20260817/sug.md
dispatch_commit_sha: 20a8fb26937439cb0ae10d9be95c5a2c218f3023
server_report_path: dis/server_reports/orientbench-b-r041-panorama-repair-20260817/SERVER_EXECUTION_REPORT.md
execution_status: complete
completion_mode: user_authorized_resumption_after_historical_protocol_drift
scientific_outcome: NOT_ADJUDICATED
starting_commit: 20a8fb26937439cb0ae10d9be95c5a2c218f3023
ending_commit: final r041 completion commit containing this report
---

# r041 服务器执行报告

执行完毕

## 摘要

本轮资产修复在用户授权恢复后正常收尾：3 个 DIOR-R 单元通过 AP parity 并完成三视图统一匹配，合计 281,804 行；ARS-DETR 因框架不支持 TTA 跳过，Strip-RCNN 因 AP parity 不通过跳过三视图。DOTA 指定切片布局缺少 `annfiles/`，未以替代布局推理；ICDAR-MLT 不在盘，未下载。无科学裁决。

首次执行时曾发生一次 DOTA-v2.0 目录元数据访问并已按当时规则停止；用户随后明确授权恢复。该历史事件保留在 `STARTED.json`、原早停报告历史与 `RESUMED_BY_USER.json` 中。恢复后未再次触碰禁止端点。

## AP 对齐表

| 单元 | 参考 mAP | 实测 mAP | 结果 | 后续 |
|---|---:|---:|---|---|
| PSC / DIOR-R | 0.5368 | 0.5368 | PASS | 三视图与 matched rows 完成 |
| LSKNet / DIOR-R | 0.7187 | 0.7187469 | PASS | 三视图与 matched rows 完成 |
| RTMDet-S / DIOR-R | 0.5489 | 0.5489 | PASS | 三视图与 matched rows 完成 |
| ARS-DETR / DIOR-R | 0.4158 | 0.4157512 | PASS | hflip 技术失败，跳过 |
| Strip-RCNN / DIOR-R | 0.4467 | 0.1940329 | AP_MISALIGNED | 跳过三视图 |
| DOTA-v1.0 全架构 | — | — | LAYOUT_UNAVAILABLE | 指定切片根缺少 `annfiles/`，未替代 |
| DOTA-v1.5 | — | — | LAYOUT_UNAVAILABLE | 对应切片布局未可用，未替代 |
| ICDAR-MLT | — | — | DATA_ABSENT | 未下载、未替代 |

## 有效资产与审计

- 有效分析池：PSC、LSKNet、RTMDet-S 三个 DIOR-R 单元。
- 合并 rows：`outputs/persistent_artifacts/orientbench_panorama_r041_20260817/normalized/matched_rows_r041_dior.csv`，281,804 行、97,843,463 bytes；因大于 80 MB 不入 Git，保留在服务器持久化 artifact 目录并由 manifest 记录真实 SHA-256。
- 独立验证器：`outputs/persistent_artifacts/orientbench_panorama_r041_20260817/code/validate_r041.py`；验证通过，schema、预测键/GT 匹配唯一性、IoU 不变量、证据有限性与 provenance 均通过。
- 真实 subprocess mutation：重复预测键、IoU 越界、非有限证据均被验证器拒绝；结果位于 `outputs/persistent_artifacts/orientbench_panorama_r041_20260817/mutations/`。
- 审计 bundle：`audit_bundles/r041/`，含 manifest、validator、副本 provenance、AP 表、单元汇总、rows 抽样和 mutation 回执。

## 禁触端点、资源与偏差

| 项目 | 状态 |
|---|---|
| DOTA-v2.0 | 历史首次检查曾触碰目录元数据；恢复后零访问 |
| SODA-A official test | 未触碰 |
| 任意 official test 标注 | 未触碰 |
| r040 HRSC 七单元 | 未重跑、未改动 |
| 训练 / 微调 / 权重更新 / 下载 / pth_data 写入 | 均未发生 |
| GPU | 每次单元推理单卡，未超过 2 卡并发上限 |

偏差均依冻结门控处理：DOTA/DOTA-v1.5 无可用指定布局、ARS-DETR TTA 不支持、Strip-RCNN AP 不对齐；没有以替代数据、重训或伪造产物绕过。

## 监督 041-S 结论

恢复后各已启动单元均为正常结束；异常/失败单元已给出停止点、原因、AP 对齐和禁止端点状态。此次为资产轮，输出不构成 detector、门控或科学结论。
