---
schema_version: 2
dispatch_id: orientbench-b-r023-measurement-validity-20260813
plan_id: b-r023-measurement-validity-20260813
initiator: B
plan_path: dis/plans/B/b-r023-measurement-validity-20260813/sug.md
plan_commit_sha: 2244d224d969cc8051e22a8ad175a49bac7aa8a7
plan_blob_oid: debf5cf99606a0142b04f6c5f90d501283f8abe7
plan_sha256: 044cc2539fa6ec1e28a9ad46e121753bc0e389efdf723bf2ce1a4f415e205af5
dispatch_commit_sha: 2244d224d969cc8051e22a8ad175a49bac7aa8a7
server_report_path: dis/server_reports/orientbench-b-r023-measurement-validity-20260813/SERVER_EXECUTION_REPORT.md
execution_status: complete
completion_mode: FULL_PRACTICAL_RERUN_PENDING_BC_ADJUDICATION
starting_commit: 3e00eb35ff7d386f9ab61c6adad21c50d7a029f3
ending_commit: PENDING_RESULT_COMMIT
---

# 服务器执行报告

## 摘要

本服务器在全新 r023 runtime 根上完成 26 项冻结输入的两套独立实现、各 10,000 cluster bootstrap、全量比较与结构验证。候选科学态为 `INCONCLUSIVE_MIXED`；服务器不裁决 B/C 的正式 scientific verdict。

## Dispatch、哈希、授权与资源

- 执行身份：`paper.worker-id=server-primary`。
- 计划、镜像和 coordination 绑定一致：blob `debf5cf99606a0142b04f6c5f90d501283f8abe7`，SHA-256 `044cc2539fa6ec1e28a9ad46e121753bc0e389efdf723bf2ce1a4f415e205af5`。
- STARTED 单文件提交并已 HTTPS 推送：`3e00eb35ff7d386f9ab61c6adad21c50d7a029f3`。
- 实际资源：CPU-only；`taskset -c 0-47`，39 workers，BLAS threads=1；未使用 GPU、训练或推理。

## 实际执行

| 任务 | 状态 | 配置 | 产物 |
|---|---|---|---|
| A | complete | 10,000 replicates / 39 workers | `full_a_r10000` |
| B | complete | 10,000 replicates / 39 workers | `independent_b_r10000` |
| Comparator | PASS | all replicates, atol=1e-10 | `comparator_ab` |
| Validator | PASS | expected replicates=10000 | stdout recorded in execution logs |
| fd-shifts reference | PASS | pinned `c4467aec...`; 4 vectors | `reference_probe.json` |
| Mutation / closure | PASS | six semantic mutations + closure validator | `mutations_final/`, `closure.json` |

## 结果与披露

- 26 项 input inventory 校验通过。
- A/B 10,000 replicate unit 与 dataset arrays 最大绝对差均为 `0.0`；405 hypotheses、point metrics、CI、p、Holm、swaps、witness 均为零差。
- candidate scientific state: `INCONCLUSIVE_MIXED`；unit witnesses=5，dataset witnesses=2，passing signatures=[]。
- r023 依计划复用了 Git blob 钉定的 r020 recovery 管线；该务实合同明确允许此复用并允许执行者知晓历史 recovery 信息。正式科学 verdict 仍由 B/C post-pull 独立作出。
- Mutation：六项均 pristine accept / mutated reject；closure=`VALID_RECOVERY_CLOSURE`，closure SHA-256=`36b1602e6a7531ff46691db3a4313df264edb7e9e534546363ecce8a6cdc02f7`。
- 偏差披露：首次 mutation 调用发生在报告尚无 token 时，留下 `mutations/` 的不完整临时检查目录；没有覆盖或作为证据使用。随后因报告 token 位置不符合 validator literal 要求，`mutations_complete/` 被拒绝；最终有效证据唯一为 `mutations_final/`。这些目录均保留以便审计。

## Provenance 与完成映射

runtime 根：`outputs/persistent_artifacts/orientbench_measurement_validity_r023_20260813/`。所有 r023 要求的实际计算、比较、参考、mutation 与 closure 已完成；本报告提交推送后，由 B/C post-pull 独立裁决。
