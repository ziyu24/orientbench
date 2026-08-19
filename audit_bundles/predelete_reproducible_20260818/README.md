# Pre-delete reproducibility archive

This bundle is a metadata archive only; no payload has been deleted.

## Group A — caches and work directories

Targets: `outputs/bench_core/cache/`, `outputs/bench_core/gt_index/`, and
`work_dirs/` (about 40 MiB total).  They are derived indexes, caches, copied
runtime configs and logs.  Regenerate them by rerunning the recorded scripts
and configs that created the relevant Bench-Core or TTA job; the source
datasets and Git-tracked scripts/configs remain untouched.

## Group B — training checkpoints

Targets: `outputs/training/a4_host/best_dota_mAP_epoch_70.pth` and
`outputs/training/rhino/best_dota_mAP_epoch_35.pth` (about 477 MiB total).
Their exact four-GPU regeneration commands are stored verbatim as
`launcher_command` in the adjacent `manifest.json` files.  Deleting these
checkpoints sacrifices reproducibility-by-reuse and requires retraining; it
does not delete the tracked config, manifest or training provenance.

## Excluded pending a separate lineage audit

`archives/worktrees/orientbench_r032_clean/`, all `outputs/probes/`,
`outputs/predictions/`, and `outputs/persistent_artifacts/` are retained.
They include historical Git provenance, raw predictions, or formal evidence;
they are not safe bulk-clean targets.
