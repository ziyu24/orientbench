---
schema_version: 2
dispatch_id: orientbench-b-r026-dota-external-confirmation-20260813
plan_id: b-r026-dota-external-confirmation-20260813
initiator: B
plan_path: dis/plans/B/b-r026-dota-external-confirmation-20260813/sug.md
execution_status: incomplete
completion_mode: PARTIAL_CONFIRMATION_MISSING_INDEPENDENT_VALIDATOR_AND_MUTATIONS
starting_commit: da282e7c43aa50e9dd1fd2223359bdf6850e3ba9
ending_commit: PENDING_RESULT_COMMIT
---

# 服务器执行报告

## 摘要

r026 已完成 raw layer 的独立两次重算、完整 ε/CI/centered-p/Holm/swap/witness 判据和 comparator；候选态为 `CONFIRMED_EXTERNAL_STRONG`。但在本服务器回合内未完成计划要求的独立 validator 与至少四项 semantic mutations，因此不能回执为完整正式确认。

## 已完成证据

- AP parity：Oriented R-CNN `0.706069/0.451742`，RTMDet `0.716127/0.486848`，均在 0.002 容差内。
- GT：使用 r019 prelabel 阶段 DOTA-v1.0 val tile conversion，5297 tiles / 458 mothers；原始 split tile annfiles 在迁移主机不存在。
- A/B raw rerun：两 unit matched 集合精确相同（Oriented R-CNN 48,889，RTMDet 51,736）；point/bootstrap 与完整 hypotheses/gate 字节相同。
- 完整判据：RTMDet 的 AUGRC、Risk@70 unit witness 成立；DOTA equal-unit 的 AUGRC、Risk@70 dataset witness 均成立（Risk swaps 0.2304 / 0.2238）。候选态 `CONFIRMED_EXTERNAL_STRONG`。

## 未完成与状态

本轮实现 A 的 raw 重算脚本在 r026 根中执行，B 判据层独立运行；但用于最终 predicate 的 A/B criterion code 共用同一 r026 criterion module，未满足“完全不共享代码”的严格表达。此外，独立 validator 与 mutation 还未执行。为避免把部分完成伪装为正式确认，执行状态为 `incomplete`，不发射 JPRS 主张。

## 产物

- `outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/implementation_a_raw/`
- `outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/implementation_a/`
- `outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/implementation_b/`
- `outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/comparator.json`

后续须在新 dispatch 中补独立 criterion/validator 和 ≥4 项 mutation，或由 B/C 将本轮明确接收为 practical confirmation。
