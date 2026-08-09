#!/usr/bin/env python3
"""Run one r019 DOTA unit on four GPUs with process-tree telemetry."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RUNTIME = ROOT / "outputs/persistent_artifacts/orientbench_r019/prelabel"
PYTHON = "/home/rspip/anaconda3/envs/mr_dev1x/bin/python"
WORKER = ROOT / "p3_selector/deployable_proxy_r019/scripts/forward_image_only_r019.py"


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def gpu_rows():
    command = ["nvidia-smi", "--query-gpu=index,utilization.gpu,memory.used", "--format=csv,noheader,nounits"]
    try:
        return subprocess.check_output(command, text=True).strip().splitlines()
    except Exception:
        return []


def process_snapshot(root_pids):
    """Read Linux procfs for the launched process trees without extra packages."""
    table = {}
    for item in Path("/proc").iterdir():
        if not item.name.isdigit():
            continue
        try:
            fields = (item / "stat").read_text().split()
            status = (item / "status").read_text().splitlines()
            ppid = int(fields[3]); rss_kb = 0
            for line in status:
                if line.startswith("VmRSS:"):
                    rss_kb = int(line.split()[1]); break
            table[int(item.name)] = (ppid, rss_kb * 1024)
        except (OSError, ValueError, IndexError):
            pass
    selected = set(root_pids)
    changed = True
    while changed:
        changed = False
        for pid, (ppid, _) in table.items():
            if ppid in selected and pid not in selected:
                selected.add(pid); changed = True
    rss = sum(table.get(pid, (0, 0))[1] for pid in selected)
    return len(selected), rss


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--unit", choices=("orcnn", "rtmdet"), required=True)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--mode", choices=("smoke", "full"), required=True)
    args = parser.parse_args()
    registry = RUNTIME / "image_only_registry.json"
    total = len(json.loads(registry.read_text())["tiles"])
    count = min(args.limit or total, total)
    base = RUNTIME / ("smoke" if args.mode == "smoke" else "raw") / args.unit
    base.mkdir(parents=True, exist_ok=True)
    processes = []
    commands = []
    started = time.time()
    for gpu in range(4):
        indices = list(range(gpu, count, 4))
        index_file = base / f"indices_gpu{gpu}.txt"
        index_file.write_text("".join(f"{i}\n" for i in indices))
        output = base / f"part_gpu{gpu}.pkl"
        guard = base / f"guard_gpu{gpu}.json"
        log = base / f"worker_gpu{gpu}.log"
        command = [PYTHON, str(WORKER), "--unit", args.unit, "--gpu", str(gpu),
                   "--registry", str(registry), "--indices", str(index_file),
                   "--output", str(output), "--guard-log", str(guard)]
        handle = log.open("w")
        proc = subprocess.Popen(command, cwd=ROOT, stdout=handle, stderr=subprocess.STDOUT,
                                start_new_session=True, env={**os.environ, "OMP_NUM_THREADS": "1", "MKL_NUM_THREADS": "1"})
        processes.append((proc, handle, output, guard, log, len(indices)))
        commands.append({"gpu": gpu, "command": command, "indices": len(indices), "pid": proc.pid})
    telemetry = []
    while any(proc.poll() is None for proc, *_ in processes):
        now = time.time()
        roots = [proc.pid for proc, *_ in processes if proc.poll() is None]
        workers, rss = process_snapshot(roots)
        telemetry.append({"timestamp": now, "elapsed_seconds": now-started, "process_count": workers,
                          "aggregate_cpu_percent": "procfs_interval_not_available", "aggregate_rss_bytes": rss,
                          "gpu_snapshot": "|".join(gpu_rows())})
        time.sleep(10)
    failures = []
    output_inventory = []
    access_count = 0
    for proc, handle, output, guard, log, expected in processes:
        handle.close()
        if proc.returncode != 0:
            failures.append({"pid": proc.pid, "returncode": proc.returncode, "log": str(log)})
        if not output.is_file():
            failures.append({"pid": proc.pid, "error": "missing output", "output": str(output)})
        else:
            output_inventory.append({"path": str(output), "bytes": output.stat().st_size,
                                     "sha256": sha(output), "expected_images": expected})
        if guard.is_file():
            access_count += int(json.loads(guard.read_text()).get("target_label_access_count", 0))
    tel = RUNTIME / "telemetry" / f"{args.mode}_{args.unit}.csv"
    tel.parent.mkdir(parents=True, exist_ok=True)
    with tel.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(telemetry[0]) if telemetry else ["timestamp"])
        writer.writeheader(); writer.writerows(telemetry)
    summary = {"unit": args.unit, "mode": args.mode, "images": count, "views": 3,
               "commands": commands, "outputs": output_inventory, "failures": failures,
               "target_label_access_count": access_count, "started": started, "ended": time.time(),
               "telemetry": str(tel), "status": "PASS" if not failures and access_count == 0 else "FAIL"}
    path = base / "orchestrator_summary.json"; path.write_text(json.dumps(summary, indent=2) + "\n")
    print(json.dumps({"status": summary["status"], "unit": args.unit, "mode": args.mode, "images": count}))
    raise SystemExit(0 if summary["status"] == "PASS" else 1)


if __name__ == "__main__":
    main()
