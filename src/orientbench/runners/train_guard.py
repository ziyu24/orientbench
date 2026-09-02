"""Non-bypassable formal-training guard (014 + 014-supplement).

A formal host training MUST use ALL 4 GPUs as a 4-rank DDP job (world_size=4).
Two 4-GPU jobs MAY run concurrently sharing GPUs 0,1,2,3, but they must use
distinct MASTER_PORT and work-dir. LR is linearly scaled from the official
reference global batch; eval/checkpoint policy must be per-epoch val + best
(by the real mAP metric key) + latest. Any violation => REFUSE (not warn).

    effective_global_batch = per_gpu_batch * world_size * gradient_accumulation_steps
    scaled_lr = reference_lr * effective_global_batch / reference_global_batch
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

REQUIRED_WORLD_SIZE = 4
REQUIRED_GPU_IDS = [0, 1, 2, 3]


def compute_effective_batch(per_gpu_batch: int, world_size: int, grad_accum: int) -> int:
    return int(per_gpu_batch) * int(world_size) * int(grad_accum)


def compute_scaled_lr(reference_lr: float, effective_global_batch: int,
                      reference_global_batch: int) -> float:
    return float(reference_lr) * effective_global_batch / float(reference_global_batch)


def _parse_gpu_ids(cuda_visible: Optional[str]) -> List[int]:
    if not cuda_visible:
        return []
    out = []
    for x in cuda_visible.split(","):
        x = x.strip()
        if x:
            try:
                out.append(int(x))
            except ValueError:
                pass
    return out


def validate_formal_training(
    host: str, per_gpu_batch: int, world_size: int, grad_accum: int,
    reference_global_batch: int, reference_lr: float, configured_lr: float,
    auto_scale_lr_enabled: bool, cuda_visible: Optional[str],
    val_interval: int = 1, save_best_metric: Optional[str] = None,
    save_last: bool = False, max_keep_ckpts: Optional[int] = None,
    master_port: Optional[int] = None, work_dir: Optional[str] = None,
    other_master_ports: Optional[List[int]] = None,
    other_work_dirs: Optional[List[str]] = None,
    resume_from_noncompliant: bool = False,
) -> Dict[str, Any]:
    errors: List[str] = []
    gpu_ids = _parse_gpu_ids(cuda_visible)
    other_ports = other_master_ports or []
    other_dirs = other_work_dirs or []

    # --- GPU topology: full 4-GPU per host ---
    if world_size != REQUIRED_WORLD_SIZE:
        errors.append(f"world_size={world_size} != 4")
    if sorted(gpu_ids) != REQUIRED_GPU_IDS:
        errors.append(f"GPU ids={sorted(gpu_ids)} != [0,1,2,3] (must use all 4 GPUs)")

    # --- effective batch + LR linear scaling ---
    eff = compute_effective_batch(per_gpu_batch, world_size, grad_accum)
    if eff <= 0:
        errors.append("effective_global_batch not computable")
    if not reference_global_batch or not reference_lr:
        errors.append("reference_global_batch/reference_lr missing (must come from official config)")
    scaled = compute_scaled_lr(reference_lr, eff, reference_global_batch) if reference_global_batch else float("nan")
    scale_factor = eff / float(reference_global_batch) if reference_global_batch else float("nan")
    if abs(configured_lr - scaled) > 1e-12:
        errors.append(f"configured_lr={configured_lr} != scaled_lr={scaled} (linear scaling violated)")
    manual_scaling_applied = abs(scale_factor - 1.0) > 1e-9
    if auto_scale_lr_enabled and manual_scaling_applied:
        errors.append("double scaling: auto_scale_lr enabled AND manual non-unit scale")

    # --- eval / checkpoint policy ---
    if val_interval != 1:
        errors.append(f"val_interval={val_interval} != 1 (per-epoch validation required)")
    if not save_best_metric:
        errors.append("save_best metric key not set (need real mAP key e.g. dota/mAP)")
    if not save_last:
        errors.append("save_last must be True (keep latest checkpoint)")
    # best + latest must be guaranteed; max_keep_ckpts limits only regular ckpts,
    # best is saved separately -> require save_best set AND save_last True (above).
    if max_keep_ckpts is not None and max_keep_ckpts < 1:
        errors.append("max_keep_ckpts < 1 would drop latest")

    # --- concurrency: distinct port + work-dir ---
    if master_port is not None and master_port in other_ports:
        errors.append(f"MASTER_PORT {master_port} conflicts with concurrent job")
    if work_dir is not None and work_dir in other_dirs:
        errors.append(f"work_dir {work_dir} conflicts with concurrent job")
    if resume_from_noncompliant:
        errors.append("resume from non-compliant checkpoint is forbidden")

    return {
        "host": host, "ok": len(errors) == 0, "errors": errors,
        "world_size": world_size, "gpu_ids": sorted(gpu_ids),
        "gpu_topology": "single_job_4gpu" if (world_size == 4 and sorted(gpu_ids) == REQUIRED_GPU_IDS) else "invalid",
        "per_gpu_batch": per_gpu_batch, "gradient_accumulation_steps": grad_accum,
        "effective_global_batch": eff, "reference_global_batch": reference_global_batch,
        "reference_lr": reference_lr, "lr_scale_factor": scale_factor,
        "scaled_lr": scaled, "configured_lr": configured_lr,
        "auto_scale_lr_enabled": auto_scale_lr_enabled,
        "val_interval": val_interval, "save_best_metric": save_best_metric,
        "save_last": save_last, "max_keep_ckpts": max_keep_ckpts,
        "master_port": master_port, "work_dir": work_dir,
        "batch_proof_valid": eff > 0 and "effective_global_batch not computable" not in errors,
        "lr_scaling_proof_valid": abs(configured_lr - scaled) <= 1e-12 and not (auto_scale_lr_enabled and manual_scaling_applied),
        "eval_policy_valid": val_interval == 1 and bool(save_best_metric) and save_last,
        "checkpoint_policy_valid": bool(save_best_metric) and save_last and (max_keep_ckpts is None or max_keep_ckpts >= 1),
        "formal_eligible": len(errors) == 0,
    }
