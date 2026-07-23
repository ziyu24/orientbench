# Real artifact inventory 050

Generated: 2026-07-02 20:14:10 CST

Only verified non-synthetic/non-proxy artifacts are allowed into final evidence. Schema files found only in /dev/shm are classified as scratch/nonpersistent unless an outputs/persistent_artifacts copy exists.

Audited cells: 12. P1-usable persistent raw/schema cells: 5. P3-usable PSC Track A cells: 3; DOTA #20 phase_mod remains unavailable.

| dataset     |   baseline_id | detector   | usable_for_P1   | usable_for_P2   | usable_for_P3   | usable_for_P4   | usable_for_P5   | missing_reason                                                                   |
|:------------|--------------:|:-----------|:----------------|:----------------|:----------------|:----------------|:----------------|:---------------------------------------------------------------------------------|
| DOTA-v1.0   |            20 | psc        | True            | True            | False           | True            | True            | track_a_dump_missing;tta_dump_missing                                            |
| DIOR-R      |            22 | psc        | True            | True            | True            | True            | True            |                                                                                  |
| FAIR1M-v1.0 |            24 | psc        | True            | True            | True            | True            | True            |                                                                                  |
| SODA-A      |            23 | psc        | True            | True            | True            | True            | True            |                                                                                  |
| DIOR-R      |             3 | orcnn      | True            | True            | False           | True            | True            |                                                                                  |
| DIOR-R      |            61 | rtmdet     | False           | True            | False           | True            | True            | schema_only_in_scratch_or_nonpersistent                                          |
| DIOR-R      |            10 | lsknet     | False           | True            | False           | True            | True            | schema_only_in_scratch_or_nonpersistent                                          |
| FAIR1M-v1.0 |             5 | orcnn      | False           | True            | False           | True            | True            | schema_only_in_scratch_or_nonpersistent                                          |
| FAIR1M-v1.0 |            12 | lsknet     | False           | True            | False           | True            | True            | schema_only_in_scratch_or_nonpersistent;tta_dump_missing                         |
| SODA-A      |             4 | orcnn      | False           | True            | False           | True            | True            | schema_only_in_scratch_or_nonpersistent                                          |
| SODA-A      |            11 | lsknet     | False           | True            | False           | True            | True            | schema_only_in_scratch_or_nonpersistent;tta_dump_missing                         |
| HRSC2016    |            13 | lsknet     | False           | False           | False           | False           | False           | schema_only_in_scratch_or_nonpersistent;matched_feature_missing;tta_dump_missing |
