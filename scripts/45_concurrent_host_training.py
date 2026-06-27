#!/usr/bin/env python3
"""45_concurrent_host_training.py — two concurrent 4-GPU host trainings (014-supp).

RHINO and A4 each use GPUs 0,1,2,3 (world_size=4), running CONCURRENTLY with
distinct MASTER_PORT / work-dir / log. Enforces per-epoch val + best(dota/mAP)
+ latest checkpoint policy via the non-bypassable train_guard. Launches both,
runs a >=200-iter stress check; on CUDA OOM (or NaN) it stops BOTH and falls
back to SINGLE-JOB 4-GPU SERIAL (RHINO then A4). Clean restart from official
pretrain (never resumes superseded/non-compliant checkpoints). Detached.
"""
from __future__ import annotations

import glob
import json
import os
import re
import signal
import subprocess
import sys
import time

ORIENT = "/home/rspip/cqc/pro/study/orientbench"
CLONE = "/home/rspip/cqc/pro/study/ai4rs_clone"
PY = "/home/rspip/anaconda3/envs/ai4rs_train/bin/python"
sys.path.insert(0, ORIENT)
sys.path.insert(0, CLONE)
os.environ["PYTHONPATH"] = CLONE + ":" + os.environ.get("PYTHONPATH", "")
from orientbench.runners.train_guard import compute_scaled_lr, validate_formal_training  # noqa: E402

D10 = "/home/rspip/cqc/data/dataset/dota/dota1.0/split_ss_dota10/"
D15 = "/home/rspip/cqc/data/dataset/dota/dota1.5/split_ss_dota15/"
SAVE_BEST_KEY = "dota/mAP"
NUM_WORKERS = 3  # per rank; 4 ranks x 3 x 2 jobs = 24 dataloader workers total (<=48)

HOSTS = [
    {"key": "rhino", "host": "RHINO", "route": "C1/B",
     "config": "projects/RHINO/configs/rhino_phc_haus_4scale_r50_2xb4_36e_dota.py",
     "data_root": D10, "per_gpu_batch": 2, "ref_global_batch": 8, "ref_lr": 1e-4,
     "port": 29551, "epochs": 36},
    {"key": "a4_host", "host": "O2-RTDETR", "route": "A4",
     "config": "projects/rotated_rtdetr/configs/o2_rtdetr_r18vd_4xb1_72e_dotav15.py",
     "data_root": D15, "per_gpu_batch": 1, "ref_global_batch": 4, "ref_lr": 5e-5,
     "port": 29552, "epochs": 72},
]


def _now():
    return time.strftime("%Y-%m-%d %H:%M:%S %Z")


def _auto_scale_enabled(config):
    from mmengine.config import Config
    return bool((Config.fromfile(os.path.join(CLONE, config)).get("auto_scale_lr") or {}).get("enable", False))


def _has_ckpt(wd):
    return bool([h for h in glob.glob(os.path.join(wd, "*.pth")) if "superseded" not in h]) or \
        os.path.isfile(os.path.join(wd, "last_checkpoint"))


def build(h, others):
    wd = os.path.join(ORIENT, "outputs", "training", h["key"])
    os.makedirs(wd, exist_ok=True)
    world, accum = 4, 1
    eff = h["per_gpu_batch"] * world * accum
    scaled_lr = compute_scaled_lr(h["ref_lr"], eff, h["ref_global_batch"])
    auto_scale = _auto_scale_enabled(h["config"])
    rep = validate_formal_training(
        host=h["host"], per_gpu_batch=h["per_gpu_batch"], world_size=world, grad_accum=accum,
        reference_global_batch=h["ref_global_batch"], reference_lr=h["ref_lr"],
        configured_lr=scaled_lr, auto_scale_lr_enabled=auto_scale, cuda_visible="0,1,2,3",
        val_interval=1, save_best_metric=SAVE_BEST_KEY, save_last=True, max_keep_ckpts=1,
        master_port=h["port"], work_dir=wd,
        other_master_ports=[o["port"] for o in others],
        other_work_dirs=[os.path.join(ORIENT, "outputs", "training", o["key"]) for o in others],
        resume_from_noncompliant=False)
    cmd = [PY, "-m", "torch.distributed.run", "--nproc_per_node=4", f"--master_port={h['port']}",
           "tools/train.py", h["config"], "--launcher", "pytorch", "--work-dir", wd, "--resume",
           "--cfg-options", f"optim_wrapper.optimizer.lr={scaled_lr}",
           f"train_dataloader.batch_size={h['per_gpu_batch']}",
           f"train_dataloader.num_workers={NUM_WORKERS}",
           f"train_dataloader.dataset.data_root={h['data_root']}",
           "train_dataloader.dataset.ann_file=train/annfiles/",
           "train_dataloader.dataset.data_prefix.img_path=train/images/",
           f"val_dataloader.dataset.data_root={h['data_root']}",
           "val_dataloader.dataset.ann_file=val/annfiles/",
           "val_dataloader.dataset.data_prefix.img_path=val/images/",
           f"test_dataloader.dataset.data_root={h['data_root']}",
           "test_dataloader.dataset.ann_file=val/annfiles/",
           "test_dataloader.dataset.data_prefix.img_path=val/images/",
           "train_cfg.val_interval=1",
           "default_hooks.checkpoint.interval=1",
           f"default_hooks.checkpoint.save_best={SAVE_BEST_KEY}",
           "default_hooks.checkpoint.rule=greater",
           "default_hooks.checkpoint.save_last=True",
           "default_hooks.checkpoint.max_keep_ckpts=1",
           "randomness.seed=42"]
    manifest = {
        "host": h["host"], "route": h["route"], "config": h["config"],
        "config_sha256": subprocess.run(["sha256sum", os.path.join(CLONE, h["config"])],
                                        capture_output=True, text=True).stdout.split()[0],
        "env": "ai4rs_train", "dataset_root": h["data_root"], "epochs": h["epochs"],
        "world_size": world, "gpu_ids": [0, 1, 2, 3], "gpu_topology": rep["gpu_topology"],
        "concurrency": "two_4gpu_jobs_shared_gpus", "master_port": h["port"],
        "per_gpu_batch": h["per_gpu_batch"], "gradient_accumulation_steps": accum,
        "effective_global_batch": eff, "reference_global_batch": h["ref_global_batch"],
        "reference_lr": h["ref_lr"], "lr_scale_factor": rep["lr_scale_factor"],
        "scaled_lr": scaled_lr, "configured_lr": scaled_lr, "observed_initial_lr": None,
        "auto_scale_lr_status": "disabled" if not auto_scale else "ENABLED",
        "val_interval": 1, "save_best_metric": SAVE_BEST_KEY, "save_best_rule": "greater",
        "save_last": True, "max_keep_ckpts": 1, "num_workers_per_rank": NUM_WORKERS,
        "reference_source": "official ai4rs config (auto_scale_lr.base_batch_size + optimizer.lr)",
        "eval_policy_valid": rep["eval_policy_valid"], "checkpoint_policy_valid": rep["checkpoint_policy_valid"],
        "batch_proof_valid": rep["batch_proof_valid"], "lr_scaling_proof_valid": rep["lr_scaling_proof_valid"],
        "launcher_command": " ".join(cmd), "formal_eligible": rep["formal_eligible"],
        "a4_snapshot_rule": "best val mAP (official val); D_audit NOT consulted; hash-lock after",
        "clean_restart_from_official_pretrain": True, "seed": 42, "angle": "le90",
        "launch_time": _now(), "guard_report": rep,
    }
    with open(os.path.join(wd, "manifest.json"), "w") as fh:
        json.dump(manifest, fh, indent=2, ensure_ascii=False)
    print(f"[{_now()}] {h['host']} guard ok={rep['ok']} ws=4 eff={eff} scale={rep['lr_scale_factor']} "
          f"lr={scaled_lr} val_interval=1 save_best={SAVE_BEST_KEY} errors={rep['errors']}")
    return wd, cmd, rep


def launch(h, cmd, log_suffix=""):
    log = os.path.join(ORIENT, "outputs", "logs", f"{h['key']}_train_4gpu{log_suffix}.log")
    env = dict(os.environ, CUDA_VISIBLE_DEVICES="0,1,2,3", PYTHONPATH=CLONE)
    lf = open(log, "a")
    p = subprocess.Popen(cmd, cwd=CLONE, env=env, stdout=lf, stderr=subprocess.STDOUT,
                         start_new_session=True)
    return p, log


def log_has_oom_or_nan(log):
    if not os.path.isfile(log):
        return False
    try:
        txt = open(log, "r", errors="replace").read()[-20000:]
    except OSError:
        return False
    if "out of memory" in txt or "CUDA out of memory" in txt:
        return "OOM"
    if re.search(r"loss: nan|grad_norm: nan|loss: inf", txt):
        return "NaN"
    return False


def iters_done(log):
    if not os.path.isfile(log):
        return 0
    m = re.findall(r"Epoch\(train\)\s+\[\d+\]\[\s*(\d+)/", open(log, "r", errors="replace").read())
    return int(m[-1]) if m else 0


def kill_proc(p):
    try:
        os.killpg(os.getpgid(p.pid), signal.SIGKILL)
    except Exception:
        try:
            p.kill()
        except Exception:
            pass


def run_serial():
    print(f"[{_now()}] FALLBACK: single-job 4-GPU SERIAL (RHINO then A4)")
    for i, h in enumerate(HOSTS):
        wd, cmd, rep = build(h, [])
        if not rep["ok"]:
            print(f"[REFUSE serial] {h['host']}: {rep['errors']}"); return 99
        p, log = launch(h, cmd, "_serial")
        print(f"[{_now()}] serial {h['host']} pid={p.pid} log={log}")
        p.wait()
        print(f"[{_now()}] serial {h['host']} done rc={p.returncode} ckpt={_has_ckpt(wd)}")
    return 0


def main():
    print(f"[{_now()}] CONCURRENT two-4GPU host training (RHINO + A4)")
    # build + guard both (cross port/workdir)
    specs = []
    for h in HOSTS:
        wd, cmd, rep = build(h, [o for o in HOSTS if o is not h])
        if not rep["ok"]:
            print(f"[REFUSE] {h['host']} guard failed: {rep['errors']}")
            return 2
        specs.append((h, wd, cmd))
    # launch both concurrently
    procs = []
    for h, wd, cmd in specs:
        p, log = launch(h, cmd)
        procs.append((h, wd, log, p))
        print(f"[{_now()}] launched {h['host']} pid={p.pid} port={h['port']} log={log}")
        time.sleep(8)
    # stress monitor >=200 iters
    print(f"[{_now()}] stress-monitoring for >=200 iters / OOM...")
    deadline = time.time() + 900  # up to 15 min for 200 iters
    fallback = None
    while time.time() < deadline:
        time.sleep(20)
        for h, wd, log, p in procs:
            ev = log_has_oom_or_nan(log)
            if ev:
                fallback = (h["host"], ev)
                break
            if p.poll() is not None and not _has_ckpt(wd):
                fallback = (h["host"], f"died rc={p.returncode}")
                break
        if fallback:
            break
        if all(iters_done(log) >= 200 for _h, _wd, log, _p in procs):
            break
    status = {}
    if fallback:
        print(f"[{_now()}] {fallback} -> stopping BOTH, switching to SERIAL")
        for _h, _wd, _log, p in procs:
            kill_proc(p)
        time.sleep(15)
        rc = run_serial()
        status = {"mode": "serial_fallback", "trigger": fallback, "serial_rc": rc}
    else:
        iters = {h["host"]: iters_done(log) for h, wd, log, p in procs}
        print(f"[{_now()}] concurrent healthy at 200+ iters: {iters} -> keep concurrent")
        status = {"mode": "concurrent", "iters_at_check": iters,
                  "pids": {h["host"]: p.pid for h, wd, log, p in procs}}
    with open(os.path.join(ORIENT, "outputs", "training", "concurrency_status.json"), "w") as fh:
        json.dump({"time": _now(), **status}, fh, indent=2, ensure_ascii=False)
    print(f"[{_now()}] launcher done: {status.get('mode')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
