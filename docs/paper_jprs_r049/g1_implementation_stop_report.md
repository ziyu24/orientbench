# r049 G1 implementation stop

**Status: NOT_ADJUDICATED_IMPLEMENTATION (abnormal termination).**

G0 passed normally. The project-local CORA module and its math tests were
created without modifying third-party source. The required DIOR four-GPU
200-iteration smoke was attempted twice from the registered valid PSC host:

| run | numerical mode | result |
|---|---|---|
| `dior_cora_smoke_200_retry` | host AMP | `loss_bbox: inf` and `grad_norm: nan` at iteration 150 |
| `dior_cora_smoke_200_fp32` | stability-only FP32 retry | `loss_bbox: inf` at iteration 150; finite gradients otherwise |

The retry retained the optimizer, global batch, learning rate, BN and gradient
clipping; it changed only diagnostic precision. The repeated non-finite value
is in the inherited host bbox loss, not any CORA component. Because the frozen
plan permits one such stability repair only, G1 cannot be passed and no seed0
or G2 training was started.

Completed evidence:

- `experiments/r049_cora_obb/cora_head.py`
- `experiments/r049_cora_obb/test_cora_math.py` (`3 passed`)
- `outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g1/dior_cora_smoke_200_retry/train.log`
- `outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g1/dior_cora_smoke_200_fp32/train.log`

No DOTA-v2.0, SODA-A official test, r047/r048 T_audit semantic field, or
unregistered clean endpoint was read.
