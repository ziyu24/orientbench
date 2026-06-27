# Prediction Ingestion Plan

> 生成时间: 2026-06-25 18:21:48 CST
> 分级；bbox_only 一律不能进入正式 orientation risk / angle gate。

- ingestion_status 计数: {'convertible_needs_mapping': 69, 'unsupported': 18, 'synthetic_internal': 5}
- **can_enter_formal_orientation_risk (now): 0**

状态语义: ready_schema=可直接接入; convertible_bbox_only=仅 HBB 不可入正式 angle gate; convertible_needs_mapping=有 OBB 但需 category 映射 + angle 核验; unsupported=非 prediction/不可解析; missing=路径缺失; synthetic_internal=本项目自产 synthetic 不计。

| candidate | dataset | ingestion_status | can_enter_formal | needs_conversion |
|---|---|---|---|---|
| .integrate_summary.json | None | convertible_needs_mapping | False | True |
| .integrate_naood_summary.json | None | convertible_needs_mapping | False | True |
| scalars.json | DOTA-v1.0 | unsupported | False | True |
| 20260516_050858.json | DOTA-v1.0 | unsupported | False | True |
| scalars.json | DOTA-v1.0 | unsupported | False | True |
| 20260516_103933.json | DOTA-v1.0 | unsupported | False | True |
| point2rbox_v2_pseudo_labels.bbox.json | DOTA-v1.0 | convertible_needs_mapping | False | True |
| 20260516_065815.log.json | HRSC2016 | unsupported | False | True |
| point2rbox_v2_pseudo_labels.bbox.json | None | convertible_needs_mapping | False | True |
| scalars.json | DOTA-v1.0 | unsupported | False | True |
| 20260510_103718.json | DOTA-v1.0 | unsupported | False | True |
| 20260516_071627.log.json | DOTA-v1.0 | unsupported | False | True |
| 20260516_084624.log.json | DOTA-v1.5 | unsupported | False | True |
| scalars.json | HRSC2016 | unsupported | False | True |
| 20260515_215613.json | HRSC2016 | unsupported | False | True |
| scalars.json | DIOR-R | unsupported | False | True |
| 20260515_222703.json | DIOR-R | unsupported | False | True |
| scalars.json | DOTA-v1.5 | unsupported | False | True |
| 20260516_132625.json | DOTA-v1.5 | unsupported | False | True |
| dataset_inventory.csv | None | convertible_needs_mapping | False | True |
| baseline_valid_only.csv | None | convertible_needs_mapping | False | True |
| baseline_inventory.json | None | convertible_needs_mapping | False | True |
| dataset_inventory.json | None | convertible_needs_mapping | False | True |
| baseline_inventory.csv | None | convertible_needs_mapping | False | True |
| sources_dota10_train.jsonl | None | convertible_needs_mapping | False | True |
| scores_fair1m_train.jsonl | None | convertible_needs_mapping | False | True |
| sources_fair1m_train.jsonl | None | convertible_needs_mapping | False | True |
| scores_dota15_train.jsonl | None | convertible_needs_mapping | False | True |
| sources_dior_trainval.jsonl | None | convertible_needs_mapping | False | True |
| sources_dota15_train.jsonl | None | convertible_needs_mapping | False | True |
| sources_hrsc_trainval.jsonl | None | convertible_needs_mapping | False | True |
| sources_summary.json | None | convertible_needs_mapping | False | True |
| scores_hrsc_trainval.jsonl | None | convertible_needs_mapping | False | True |
| scores_dota10_train.jsonl | None | convertible_needs_mapping | False | True |
| scores_dior_trainval.jsonl | None | convertible_needs_mapping | False | True |
| gv_obliquity_baseline.csv | None | convertible_needs_mapping | False | True |
| probe_matrix_template.csv | None | convertible_needs_mapping | False | True |
| angle_version_audit.csv | None | convertible_needs_mapping | False | True |
| stress_bucket_summary.csv | None | convertible_needs_mapping | False | True |
| prediction_discovery.csv | None | convertible_needs_mapping | False | True |
