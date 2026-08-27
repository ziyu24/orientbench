未执行完毕
`dis/server_reports/orientbench-b-r051-cmr-obb-cyclic-marginalized-roi-20260822/SERVER_EXECUTION_REPORT.md`

## r051 G0 execution status

- Worker, precise dispatch commit, active plan blob and SHA256 are verified; `STARTED.json` and the read-only DOTA/valid-baseline inventory were created.
- G0 prior-art collision audit found no exact decoded-proposal cyclic-RoI likelihood-marginalization plus NMS-bound native-risk collision. It is recorded at `docs/paper_jprs_r051/primary_prior_art_audit.md`.
- The DOTA-v1.0 train/val assets and valid Oriented R-CNN/PSC baseline identity records are available. No prohibited endpoint was touched.
- Blocking asset/environment condition: PCI shows four A30 devices, but `nvidia-smi` and the designated `pcp-obb` environment expose only three CUDA A30s. r051 makes four GPUs mandatory for both G1 smoke and any formal training; therefore no GPU task, implementation admission, or scientific gate was started.

## Required recovery

Restore the missing A30 (`a2:00.0`) to the NVIDIA driver/CUDA runtime so both `nvidia-smi -L` and `torch.cuda.device_count()` report four. Then re-run the four-GPU preflight before beginning G1.

## Update: four-GPU restoration and current G1 resource exception

All four A30 devices are now visible to both `nvidia-smi` and PyTorch. The project-local CMR implementation and first four-GPU 20-iteration smoke completed normally before the subsequent candidate-UID packing refresh. The required refresh smoke was started on all four GPUs, as authorized, but GPU 3 had only 8.88 MiB free because an unrelated PID `2343045` already held about 20.23 GiB; the run ended with CUDA OOM on a 56 MiB allocation. No three-GPU fallback, data/split change, or forbidden endpoint was used. The refresh smoke is pending resource release.
