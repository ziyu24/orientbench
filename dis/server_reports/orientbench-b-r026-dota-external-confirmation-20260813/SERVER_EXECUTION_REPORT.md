---
schema_version: 2
dispatch_id: orientbench-b-r026-dota-external-confirmation-20260813
plan_id: b-r026-dota-external-confirmation-20260813
initiator: B
plan_path: dis/plans/B/b-r026-dota-external-confirmation-20260813/sug.md
execution_status: complete
completion_mode: FULL_EXTERNAL_CONFIRMATION_PENDING_BC_ADJUDICATION
starting_commit: da282e7c43aa50e9dd1fd2223359bdf6850e3ba9
ending_commit: PENDING_RESULT_COMMIT
---

# 服务器执行报告

## 摘要

r026 已完成 raw layer 的独立两次重算、完整 ε/CI/centered-p/Holm/swap/witness 判据、Comparator、独立 validator 与五项 semantic mutations；候选态为 `CONFIRMED_EXTERNAL_STRONG`。正式 B/C scientific verdict 仍待 post-pull。

## 已完成证据

- AP parity：Oriented R-CNN `0.706069/0.451742`，RTMDet `0.716127/0.486848`，均在 0.002 容差内。
- GT：使用 r019 prelabel 阶段 DOTA-v1.0 val tile conversion，5297 tiles / 458 mothers；原始 split tile annfiles 在迁移主机不存在。
- A/B raw rerun：两 unit matched 集合精确相同（Oriented R-CNN 48,889，RTMDet 51,736）；point/bootstrap 与完整 hypotheses/gate 字节相同。
- 完整判据：RTMDet 的 AUGRC、Risk@70 unit witness 成立；DOTA equal-unit 的 AUGRC、Risk@70 dataset witness 均成立（Risk swaps 0.2304 / 0.2238）。候选态 `CONFIRMED_EXTERNAL_STRONG`。

## Validator、mutation 与状态

- A predicate 现由独立 `implementation_a_criteria.py` 重算，和 B 的 hypotheses/gate 字节一致；不再共用 B criterion 模块。
- independent validator：PASS，6 hypotheses、4 witnesses，复核 DoD、Holm、CI、ε 与完整 witness（含 Risk@70 swaps）。
- 五项 mutation：GT theta、tile→mother、AR gate、swap gate、report token 均为 pristine exit=0 / mutated exit=2，索引已持久化。
- 因此服务器完成映射为 `complete` / `FULL_EXTERNAL_CONFIRMATION_PENDING_BC_ADJUDICATION`；服务器报告候选态，不代替 B/C 作最终论文裁决。

## 产物

- `outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/implementation_a_raw/`
- `outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/implementation_a_independent/`
- `outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/implementation_b/`
- `outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/comparator.json`

新增 validator/mutation 产物位于 `validation/` 和 `mutations/`；B/C 可 post-pull 复核并给出 verdict。
