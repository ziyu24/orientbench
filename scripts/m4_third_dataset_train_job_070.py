#!/usr/bin/env python3
"""Run one frozen Command-070 four-GPU training job and its full evaluation."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

import torch

ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
PY = Path("/home/rspip/anaconda3/envs/mr_dev1x/bin/python")
TRAIN = Path("/home/rspip/cqc/pro/study/ai4rs_clone/tools/train.py")
CONFIGS = ROOT / "configs/m4_third_dataset_070"
LOGS = ROOT / "logs/m4_third_dataset"
STATUS = ROOT / "reports/m4_third_dataset_job_status"
PERSIST = ROOT / "outputs/persistent_artifacts/m4_third_dataset_070/checkpoints"
TMP_ROOT = Path("/dev/shm/orientbench_m4_070_work")
for path in (LOGS / "pilot", LOGS / "final", STATUS, PERSIST, TMP_ROOT):
    path.mkdir(parents=True, exist_ok=True)


def read(path: Path) -> str:
    return path.read_text(errors="ignore") if path.is_file() else ""


def terminal_nan(text: str) -> bool:
    lines = [line.lower() for line in text.splitlines() if "epoch(train)" in line and "loss:" in line]
    recent = lines[-30:]
    bad = sum("loss: nan" in line or "loss: inf" in line for line in recent)
    return bool(recent) and bad >= max(3, len(recent) // 2)


def parse_last(pattern: str, text: str):
    values = re.findall(pattern, text)
    return float(values[-1]) if values else None


def kill_group(process: subprocess.Popen) -> None:
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except ProcessLookupError:
        pass


def train_attempt(args, work_dir: Path, log_path: Path, fp32: bool, port: int) -> tuple[str, int]:
    options = [
        f"randomness.seed={args.seed}",
        f"optim_wrapper.optimizer.lr={args.lr}",
        f"train_cfg.max_epochs={args.epochs}",
    ]
    if fp32:
        options.append("optim_wrapper.type=OptimWrapper")
    env = dict(
        os.environ,
        CUDA_VISIBLE_DEVICES="0,1,2,3",
        PYTHONPATH=f"{ROOT / 'top_journal_v3_reaudit_055'}:{ROOT}:{os.environ.get('PYTHONPATH', '')}",
        TORCH_NCCL_HEARTBEAT_TIMEOUT_SEC="3600",
        NCCL_TIMEOUT="3600",
        PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True",
        OMP_NUM_THREADS="6",
    )
    command = [
        str(PY), "-m", "torch.distributed.run", "--nproc_per_node=4",
        f"--master_port={port}", str(TRAIN), str(CONFIGS / f"fair1m_{args.head.lower()}.py"),
        "--launcher", "pytorch", "--work-dir", str(work_dir), "--cfg-options", *options,
    ]
    with log_path.open("a") as handle:
        handle.write(f"\n[{time.strftime('%F %T %z')}] LAUNCH run={args.run_id} GPUs=0,1,2,3 "
                     f"lr={args.lr} epochs={args.epochs} mode={'fp32' if fp32 else 'amp'}\n")
        handle.flush()
        process = subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT,
                                   preexec_fn=os.setsid, env=env)
    while process.poll() is None:
        text = read(log_path)
        if "linalg.inv: Low precision" in text or terminal_nan(text):
            kill_group(process)
            process.wait()
            return ("amp_incompatible" if "linalg.inv: Low precision" in text else "nan_or_inf", process.returncode)
        time.sleep(30)
    text = read(log_path)
    if "out of memory" in text.lower():
        return "oom", process.returncode
    if "EADDRINUSE" in text or "address already in use" in text:
        return "address_in_use", process.returncode
    checkpoint = work_dir / f"epoch_{args.epochs}.pth"
    if process.returncode == 0 and checkpoint.is_file() and not terminal_nan(text):
        ap50 = parse_last(r"dota/AP50:\s*([0-9.]+)", text)
        if ap50 is None or ap50 <= 0:
            return "empty_or_degenerate_prediction", process.returncode
        return "complete", process.returncode
    return "process_failure", process.returncode


def persist_weights(source: Path, destination: Path, metadata: dict) -> None:
    checkpoint = torch.load(source, map_location="cpu")
    payload = {"state_dict": checkpoint["state_dict"], "meta": {**checkpoint.get("meta", {}), **metadata}}
    tmp = destination.with_suffix(".tmp")
    torch.save(payload, tmp)
    os.replace(tmp, destination)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--head", choices=["PSC", "CSL", "DCL"], required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--lr", type=float, required=True)
    parser.add_argument("--epochs", type=int, required=True)
    parser.add_argument("--stage", choices=["pilot", "final"], required=True)
    args = parser.parse_args()

    log_path = LOGS / args.stage / f"{args.run_id}.log"
    status_path = STATUS / f"{args.run_id}.json"
    work_dir = TMP_ROOT / args.run_id
    eval_path = ROOT / f"outputs/persistent_artifacts/m4_third_dataset_070/eval/{args.run_id}.json"
    persistent_checkpoint = PERSIST / f"{args.run_id}.pth"
    if status_path.is_file():
        old = json.loads(status_path.read_text())
        if old.get("status") in {"complete", "FAILED_BY_PREREGISTERED_GATE"} and eval_path.is_file() and (
                args.stage == "pilot" or persistent_checkpoint.is_file()):
            return 0

    attempts = []
    base_port = 31000 + int(hashlib.sha256(args.run_id.encode()).hexdigest()[:4], 16) % 1500
    final_status = "failed"
    amp_mode = ""
    for fp32 in (False, True):
        mode = "fp32_fallback" if fp32 else "amp"
        oom_count = 0
        address_count = 0
        while True:
            if work_dir.exists():
                shutil.rmtree(work_dir)
            work_dir.mkdir(parents=True)
            status, returncode = train_attempt(args, work_dir, log_path, fp32,
                                               base_port + len(attempts) + address_count)
            attempts.append({"mode": mode, "status": status, "returncode": returncode})
            if status == "complete":
                final_status = "complete"
                amp_mode = mode
                break
            if status == "address_in_use" and address_count < 20:
                address_count += 1
                time.sleep(5)
                continue
            if status == "oom" and oom_count < 6:
                oom_count += 1
                time.sleep(1200)
                continue
            break
        if final_status == "complete":
            break

    record = {
        "run_id": args.run_id, "head": args.head, "dataset": "FAIR1M-v1.0",
        "seed": args.seed, "lr": args.lr, "epochs": args.epochs, "stage": args.stage,
        "status": final_status, "amp_mode": amp_mode, "gpu_count": 4,
        "cuda_visible_devices": "0,1,2,3", "attempts": attempts,
        "log": str(log_path.relative_to(ROOT)),
    }
    if final_status != "complete":
        status_path.write_text(json.dumps(record, indent=2) + "\n")
        return 2

    source_checkpoint = work_dir / f"epoch_{args.epochs}.pth"
    eval_command = [
        str(PY), str(ROOT / "scripts/m4_third_dataset_eval_070.py"),
        "--run-id", args.run_id, "--head", args.head,
        "--config", str(CONFIGS / f"fair1m_{args.head.lower()}.py"),
        "--checkpoint", str(source_checkpoint),
    ]
    if args.stage == "pilot":
        eval_command.append("--pilot")
    eval_env = dict(os.environ, CUDA_VISIBLE_DEVICES="0",
                    PYTHONPATH=f"{ROOT / 'top_journal_v3_reaudit_055'}:{ROOT}:{os.environ.get('PYTHONPATH', '')}",
                    M069_BOOTSTRAP_WORKERS="40", OMP_NUM_THREADS="40")
    with log_path.open("a") as handle:
        eval_rc = subprocess.call(eval_command, stdout=handle, stderr=subprocess.STDOUT, env=eval_env)
    if eval_rc != 0 or not eval_path.is_file():
        record["status"] = "evaluation_failed"
        record["evaluation_returncode"] = eval_rc
        status_path.write_text(json.dumps(record, indent=2) + "\n")
        return 3
    if args.stage == "final":
        persist_weights(source_checkpoint, persistent_checkpoint, {
            "command": "070", "run_id": args.run_id, "head": args.head,
            "dataset": "FAIR1M-v1.0", "seed": args.seed, "lr": args.lr,
            "epochs": args.epochs,
        })
        record["checkpoint"] = str(persistent_checkpoint.relative_to(ROOT))
    record["evaluation"] = str(eval_path.relative_to(ROOT))
    record["status"] = "complete"
    status_path.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    shutil.rmtree(work_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
