# Collaborator Decision Form

> 生成时间: 2026-06-25 23:45:54 CST
> 所有项默认 pending；cc 不替合作者勾选；裁示后回填。

| id | decision | options | choice | status |
|---|---|---|---|---|
| D1 | 接受 threshold draft (configs/thresholds.draft.yaml)？ | accept / revise / reject | ____ | **pending** |
| D2 | RHINO 处置 | download / train / supply_to_pth_data / approve_substitute / defer | ____ | **pending** |
| D3 | A4 hybrid-encoder frozen host 处置 | supply_path / train / defer | ____ | **pending** |
| D4 | SODA-A / ICDAR-MLT 是否排除出 coverage？ | exclude / supply_path / defer | ____ | **pending** |
| D5 | 是否允许真实 detector 推理 (inference)？ | allow / deny | ____ | **pending** |
| D6 | 是否允许后续训练 (training)？ | allow_after_preconditions / deny | ____ | **pending** |
| D7 | 是否授权某 prediction 转换后用于 ingestion (非正式 gate)？ | allow / deny | ____ | **pending** |
| D8 | 允许 guarded inference dry-run runner 合并 (不执行推理)？ | allow / deny | ____ | **pending** |
| D9 | 在批准 D5 后允许执行真实 baseline inference？ | allow_after_D5 / deny | ____ | **pending** |
| D10 | 在批准 D1 后允许冻结 thresholds.yaml？ | allow_after_D1 / deny | ____ | **pending** |

说明：D5/D6 在 readiness/training_readiness 满足硬前置且本表批准前，cc 不得启动推理或训练。
