#!/usr/bin/env python3
"""44_sequential_host_training.py — guarded SEQUENTIAL 4-GPU host training.

RHINO first (4 GPU, world_size=4), then — only after RHINO completes and its
checkpoint verifies — A4 (4 GPU). Each host passes the non-bypassable
train_guard (world_size=4, single-job-4gpu, effective-batch + LR linear-scaling
proof). Run detached (setsid). Resumable via --resume. Clean restart from
official pretrain (NOT continuing the superseded 2-GPU runs).
"""
from __future__ import annotations

import glob
import json
import os
import subprocess
import sys
import time

ORIENT = "/home/rspip/cqc/pro/study/orientbench"
CLONE = "/home/rspip/cqc/pro/study/ai4rs_clone"
PY = "/home/rspip/anaconda3/envs/ai4rs_train/bin/python"
sys.path.insert(0, ORIENT)
sys.path.insert(0, CLONE)              # so this process can Config.fromfile ai4rs configs
os.environ["PYTHONPATH"] = CLONE + ":" + os.environ.get("PYTHONPATH", "")
from orientbench.runners.train_guard import validate_formal_training  # noqa: E402

D10 = "/home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10"
D15 = "/home/rspip/cqc/data/dataset/dota/dota1.5/split_ss_dota15"

HOSTS = [
    {"key": "rhino", "host": "RHINO", "route": "C1/B",
     "config": "projects/RHINO/configs/rhino_phc_haus_4scale_r50_2xb4_36e_dota.py",
     "data_root": D10 + "/", "per_gpu_batch": 2, "ref_global_batch": 8, "ref_lr": 1e-4,
     "port": 29541, "epochs": 36},
    {"key": "a4_host", "host": "O2-RTDETR", "route": "A4",
     "config": "projects/rotated_rtdetr/configs/o2_rtdetr_r18vd_4xb1_72e_dotav15.py",
     "data_root": D15 + "/", "per_gpu_batch": 1, "ref_global_batch": 4, "ref_lr": 5e-5,
     "port": 29542, "epochs": 72},
]


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S %Z")


def _auto_scale_enabled(config):
    from mmengine.config import Config
    cfg = Config.fromfile(os.path.join(CLONE, config))
    asl = cfg.get("auto_scale_lr") or {}
    return bool(asl.get("enable", False))


def _has_checkpoint(work_dir):
    for p in ["best_*mAP*.pth", f"epoch_*.pth", "last_checkpoint"]:
        if glob.glob(os.path.join(work_dir, p)):
            return True
    return False


def run_host(h):
    work_dir = os.path.join(ORIENT, "outputs", "training", h["key"])
    os.makedirs(work_dir, exist_ok=True)
    world_size = 4
    grad_accum = 1
    auto_scale = _auto_scale_enabled(os.path.join(CLONE, h["config"]))
    eff = h["per_gpu_batch"] * world_size * grad_accum
    scaled_lr = h["ref_lr"] * eff / h["ref_global_batch"]

    report = validate_formal_training(
        host=h["host"], per_gpu_batch=h["per_gpu_batch"], world_size=world_size,
        grad_accum=grad_accum, reference_global_batch=h["ref_global_batch"],
        reference_lr=h["ref_lr"], configured_lr=scaled_lr, auto_scale_lr_enabled=auto_scale,
        cuda_visible="0,1,2,3", allow_existing_jobs=0)

    cmd = [PY, "-m", "torch.distributed.run", "--nproc_per_node=4",
           f"--master_port={h['port']}", "tools/train.py", h["config"],
           "--launcher", "pytorch", "--work-dir", work_dir, "--resume",
           "--cfg-options",
           f"optim_wrapper.optimizer.lr={scaled_lr}",
           f"train_dataloader.batch_size={h['per_gpu_batch']}",
           "train_dataloader.num_workers=4",
           f"train_dataloader.dataset.data_root={h['data_root']}",
           "train_dataloader.dataset.ann_file=train/annfiles/",
           "train_dataloader.dataset.data_prefix.img_path=train/images/",
           f"val_dataloader.dataset.data_root={h['data_root']}",
           "val_dataloader.dataset.ann_file=val/annfiles/",
           "val_dataloader.dataset.data_prefix.img_path=val/images/",
           f"test_dataloader.dataset.data_root={h['data_root']}",
           "test_dataloader.dataset.ann_file=val/annfiles/",
           "test_dataloader.dataset.data_prefix.img_path=val/images/",
           "randomness.seed=42"]

    manifest = {
        "host": h["host"], "route": h["route"], "config": h["config"],
        "config_sha256": subprocess.run(["sha256sum", os.path.join(CLONE, h["config"])],
                                        capture_output=True, text=True).stdout.split()[0],
        "env": "ai4rs_train", "dataset_root": h["data_root"], "epochs": h["epochs"],
        "world_size": world_size, "gpu_ids": [0, 1, 2, 3], "gpu_topology": report["gpu_topology"],
        "per_gpu_batch": h["per_gpu_batch"], "gradient_accumulation_steps": grad_accum,
        "effective_global_batch": eff, "reference_global_batch": h["ref_global_batch"],
        "reference_lr": h["ref_lr"], "lr_scale_factor": report["lr_scale_factor"],
        "scaled_lr": scaled_lr, "configured_lr": scaled_lr, "observed_initial_lr": None,
        "auto_scale_lr_status": "disabled" if not auto_scale else "ENABLED",
        "backbone_lr_mult": 0.1, "batch_proof_valid": report["batch_proof_valid"],
        "lr_scaling_proof_valid": report["lr_scaling_proof_valid"],
        "reference_source": "official ai4rs config (auto_scale_lr.base_batch_size + optimizer.lr)",
        "launcher_command": " ".join(cmd), "formal_eligible": report["formal_eligible"],
        "a4_snapshot_rule": "best val mAP (official val); D_audit NOT consulted; hash-lock after",
        "clean_restart_from_official_pretrain": True, "seed": 42, "angle": "le90",
        "launch_time": _now(), "guard_report": report,
    }
    with open(os.path.join(work_dir, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)

    print(f"[{_now()}] {h['host']} guard: ok={report['ok']} world_size={world_size} "
          f"eff_batch={eff} ref_batch={h['ref_global_batch']} scale={report['lr_scale_factor']} "
          f"scaled_lr={scaled_lr} auto_scale={'disabled' if not auto_scale else 'ENABLED'}")
    if not report["ok"]:
        print(f"[REFUSE] {h['host']} guard failed: {report['errors']}")
        return 99
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="0,1,2,3", PYTHONPATH=CLONE)
    log = os.path.join(ORIENT, "outputs", "logs", f"{h['key']}_train_4gpu.log")
    print(f"[{_now()}] launching {h['host']} (blocking): {' '.join(cmd)}")
    with open(log, "a") as lf:
        rc = subprocess.run(cmd, cwd=CLONE, env=env, stdout=lf, stderr=subprocess.STDOUT).returncode
    print(f"[{_now()}] {h['host']} finished rc={rc}; checkpoint_present={_has_checkpoint(work_dir)}")
    return rc if _has_checkpoint(work_dir) else (rc or 98)


def main():
    print(f"[{_now()}] SEQUENTIAL 4-GPU host training start (RHINO -> A4)")
    rc_rhino = run_host(HOSTS[0])
    if rc_rhino != 0:
        print(f"[{_now()}] RHINO did not complete cleanly (rc={rc_rhino}); A4 NOT started.")
        return rc_rhino
    print(f"[{_now()}] RHINO complete + checkpoint verified; releasing GPUs, starting A4.")
    time.sleep(10)
    rc_a4 = run_host(HOSTS[1])
    print(f"[{_now()}] sequence done: rhino_rc={rc_rhino} a4_rc={rc_a4}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
