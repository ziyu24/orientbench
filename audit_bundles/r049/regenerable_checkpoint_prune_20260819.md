# Regenerable r049 G1 checkpoint prune

Disk capacity reached 100% before repaired full-validation output could be
created. The retained configs/logs make these non-formal smoke checkpoints
reproducible. Their SHA-256 values were recorded before removal.

| run | SHA-256 | regeneration config |
|---|---|---|
| host continuation diagnostic | `47701a37821836d9189abf245c99ba0b55b6f23bdacd394cb46af178d76e5d5a`, `293aa4b8cf34048f19f4be94ebba9e2e73a8724ef0eb1716bb41889fc894811b` | `dior_host_continuation_diag_200.py` |
| filtered host diagnostic | `721224f660626f83843938c696cb46f747e1a52fe7cdac5475c74898bb56a1e2`, `eec3b8400483b852700fcc2123ee33ef02fe3219d39b7f50661c9c92158f0b1f` | `dior_host_continuation_diag_200_degenerate_filter.py` |
| failed AMP CORA | `949432ff64cb27fd3fe72dd41f3ab62af088a1f5ae298eb505465b36f74d2417`, `0b8b01a715be3db056f6437bd04fc378561498ef3a4c1e34c8f2adc433c42f4c` | superseded by repaired smoke |
| failed FP32 CORA | `39bbd6c43e448cfe20ba957a27952c33ca7f2975f753213235afba4e1e078d8b`, `34843b7684cd87c83fae6c710b15deddb0086f93e45926d391cffd80373d9a3d` | superseded by repaired smoke |
| repaired no-val CORA | `c1297cb8781f48519675f5b673c606b03f7579ac044b8d83a88b7105df40fa14`, `53a969d904728b881258c122273db719bf871634c68cc7e5fde51ac03030f9d9` | `dior_cora_smoke_200_degenerate_repair.py` |

Regenerate with `pcp-obb`, four GPUs, and the matching config; all train logs
are retained under `outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g1/`.
