# OrientBench r019 服务器执行报告

- experimental_execution: FULL_COMPLETION
- all_precommit_required_work_completed: true
- git_publish_status: PENDING_EXTERNAL_RECEIPT
- all_required_work_completed: DETERMINED_BY_EXTERNAL_RECEIPT
- early_stop: false
- scientific_verdict: FAIL_EXTERNAL_DOTA_EQS_RC_R019

## Prelabel 时间锁

- prelabel_commit_sha: `7601852f5527b6feaee306bddd21c1784dbc0f95`
- prelabel_remote_main: `7601852f5527b6feaee306bddd21c1784dbc0f95`
- target_label_first_access: `1786266488.3345103`
- prelabel_changed_paths: 24
- target_label_access_before_seal: 0
- final_commit_sha: POST_COMMIT_EXTERNAL_RECEIPT
- final_remote_main: POST_COMMIT_EXTERNAL_RECEIPT

## Source-only LODO 与盲态功效

| held_out_dataset   | train_datasets     |   units |   rows |   clusters | cluster_sha256                                                   |   delta_nrc |   ci_low |   ci_high |   bootstrap_reps |     seed |        se | gate_authority   |
|:-------------------|:-------------------|--------:|-------:|-----------:|:-----------------------------------------------------------------|------------:|---------:|----------:|-----------------:|---------:|----------:|:-----------------|
| DIOR-R             | FAIR1M-v1.0|SODA-A |       3 |  41708 |       3003 | 2d8d45cc9652dd96918c83c27ea948a027922ccb802bf6d558b1e30723f64c11 |    0.178839 | 0.127964 |  0.231137 |            10000 | 20260806 | 0.0266815 | False            |
| FAIR1M-v1.0        | DIOR-R|SODA-A      |       1 |   8460 |       1137 | d06b93f1f855831cf97091b91501a5e12648b2906c7ec8a48fd76d55e74ef56c |    0.240668 | 0.194483 |  0.28721  |            10000 | 20260807 | 0.0237093 | False            |
| SODA-A             | DIOR-R|FAIR1M-v1.0 |       2 |  97155 |        576 | 76ac8199a3faaffc5d713e0d8c43879f45ace7267aa7b797b9932e9e74410ba7 |    0.205316 | 0.12599  |  0.291352 |            10000 | 20260808 | 0.0435176 | False            |

- se_worst: 0.04351764206889742
- power_at_delta_0_02: 0.11795537464528316
- MDE80: 0.10820552299361187

## DOTA 总体与 parity

- tiles: 5297
- tile_set_sha256: `c31918157bedb948bd155155ae1e54af25f8a7d91332f4d3eb45ed4070af2043`
- mothers: 458
- mother_set_sha256: `5b97f43989c2ab1daebe418b3df1293469f55a18b0ae8c7c51736f5a526d3401`
- zero_eligible_mothers: 102
- bootstrap_replicates: 10000

| unit   |   images |    gt |     ap50 |   expected_ap50 |   ap50_abs_diff |     ap75 |   expected_ap75 |   ap75_abs_diff |   tolerance | pass   |
|:-------|---------:|------:|---------:|----------------:|----------------:|---------:|----------------:|----------------:|------------:|:-------|
| orcnn  |     5297 | 55804 | 0.706069 |          0.7061 |     3.11266e-05 | 0.451742 |          0.4517 |     4.15762e-05 |       0.002 | True   |
| rtmdet |     5297 | 55804 | 0.716127 |          0.7161 |     2.71572e-05 | 0.486848 |          0.4868 |     4.79073e-05 |       0.002 | True   |

## Unit 点估计

| unit   |   eligible |   nrc_linear |   nrc_eqs |   nrc_standalone |   delta_linear_eqs |   guard_standalone_eqs |
|:-------|-----------:|-------------:|----------:|-----------------:|-------------------:|-----------------------:|
| orcnn  |      33030 |     0.782669 |  0.698265 |         0.682353 |          0.0844039 |             -0.015912  |
| rtmdet |      34385 |     0.781014 |  0.731046 |         0.695842 |          0.0499673 |             -0.0352039 |

## Delta、区间与检验

|estimand|point|95% CI|raw p|Holm-2|
|---|---:|---:|---:|---:|
|orcnn_delta|0.084403917828|[0.041429336302, 0.127965271649]|0.000299970003|0.0005999400059994001|
|rtmdet_delta|0.049967284557|[0.004090511374, 0.101236012988]|0.027297270273|0.027297270272972702|
|aggregate_delta|0.067185601193|[0.027973644353, 0.111793843284]|0.002499750025||
|orcnn_guard|-0.015911959496|[-0.027594693664, -0.004211530312]|0.994900509949||
|rtmdet_guard|-0.035203940899|[-0.050581799143, -0.021215245488]|1||
|aggregate_guard|-0.025557950198|[-0.037807765000, -0.014126812483]|0.999900009999||

## Gate predicates

- aggregate Delta >= 0.02: True
- aggregate CI_low > 0: True
- aggregate p < 0.05: True
- both units Delta >= 0.02, CI_low > 0, Holm p < 0.05: True
- aggregate and unit standalone guards >= 0: False

## 审计、资源与偏离

- independent validator: PASS
- validator tolerance: atol=1e-12, rtol=0
- complete command/exit/log ledger: `p3_selector/deployable_proxy_r019/results/execution_ledger_r019.csv`.
- telemetry: process-tree RSS/count and nvidia-smi snapshots at 10-second intervals; CPU bootstrap used 38 workers. Peak/aggregation details are in `resource_summary_r019.json`.
- protocol deviations: none affecting the frozen estimand. Before full scores, the absent optional psutil dependency was replaced by procfs telemetry and all tests/smoke were rerun. After the remote time lock, the sealed label-attach entry needed two fail-closed engineering retries: its default annotation parent had no annfiles, then MMEngine serialization cleared `data_list`; the successful replay used the manifest DOTA path and `serialize_data=false` runtime adapter without changing any sealed byte, selector, label, unit, split, gate, or statistic.
- fail-closed triggered: false
- not performed: detector training, threshold/split changes, HRSC rerun, r020, manuscript changes.

## Final Git 预期白名单

- `p3_selector/deployable_proxy_r019/results/**`
- `p3_selector/deployable_proxy_r019/docs/**`
- `dis/server_reports/orientbench-c-r019-20260809.md`
- `claude_code_and_supervisor.md` append only
- expected B blob equality: `c0c2571f3a5c828673b39e6458ceaed5f14c5a6a`

结论：`FAIL_EXTERNAL_DOTA_EQS_RC_R019`。完整科学负结果或不确定结果仍属于完整执行，而不是早停。
