# G0 host-baseline parity

Runtime: `pcp-obb` (Python 3.10, PyTorch 2.4.1+cu124, mmrotate 1.1.1).
The historical PSC checkpoints encode NumPy objects under `numpy._core`; this
runtime exposes the same implementation as `numpy.core`. The local
`runtime_compat/sitecustomize.py` provides only that module-path alias during
checkpoint deserialization. It does not alter a package, model, config, or
checkpoint.

| host | checkpoint SHA-256 | archived AP50 | replay AP50 | replay AP75 | AP50 difference | result |
|---|---|---:|---:|---:|---:|---|
| DIOR trainval -> test | `613ca496fa84f95b94ecb37c992aef8bed0dd7e38b66dd179b4e833bfed8d6e6` | 0.5368 | 0.5370 | 0.3500 | 0.0002 | PASS |
| SODA-A train -> val | `47aac3fd0f266fa75de7aa73aea874c2384e1f6fd41744d6f8c1de726867fe24` | 0.5991 | 0.5990 | 0.2730 | 0.0001 | PASS |

The acceptance tolerance is absolute 0.005. Neither evaluation accesses a
prohibited endpoint: DIOR uses the established historical test evaluation;
SODA-A uses the established validation endpoint, never the official test set.

Logs:

- `outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g0/dior_base_retry/test.log`
- `outputs/persistent_artifacts/orientbench_cora_obb_r049_20260819/g0/soda_base_retry/test.log`
