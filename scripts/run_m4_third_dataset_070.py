#!/usr/bin/env python3
"""Frozen two-at-a-time scheduler for Command-070 pilots and final runs."""
from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
PY = Path("/home/rspip/anaconda3/envs/mr_dev1x/bin/python")
RUNNER = ROOT / "scripts/m4_third_dataset_train_job_070.py"
STATUS = ROOT / "reports/m4_third_dataset_job_status"
LOG = ROOT / "logs/m4_third_dataset/master.log"
HEADS = ("PSC", "CSL", "DCL")
LRS = (0.0025, 0.005, 0.010)


def launch_batch(jobs: list[dict]) -> None:
    processes = []
    LOG.parent.mkdir(parents=True, exist_ok=True)
    for job in jobs:
        command = [str(PY), str(RUNNER)]
        for key, value in job.items():
            command.extend([f"--{key.replace('_', '-')}", str(value)])
        handle = LOG.open("a")
        processes.append((job, subprocess.Popen(command, stdout=handle, stderr=subprocess.STDOUT,
                                                cwd=ROOT), handle))
    failures = []
    for job, process, handle in processes:
        rc = process.wait()
        handle.close()
        if rc:
            failures.append((job["run_id"], rc))
    if failures:
        raise RuntimeError(f"failed jobs: {failures}")


def batched(jobs: list[dict]):
    for index in range(0, len(jobs), 2):
        yield jobs[index:index + 2]


def load_status(run_id: str) -> dict:
    return json.loads((STATUS / f"{run_id}.json").read_text())


def load_eval(run_id: str) -> dict:
    path = ROOT / f"outputs/persistent_artifacts/m4_third_dataset_070/eval/{run_id}.json"
    return json.loads(path.read_text())


def main() -> int:
    pilot_jobs = []
    for head in HEADS:
        for lr in LRS:
            pilot_jobs.append(dict(run_id=f"M4_070_pilot__{head}__FAIR1M__lr{lr:g}",
                                   head=head, seed=0, lr=lr, epochs=3, stage="pilot"))
    for batch in batched(pilot_jobs):
        launch_batch(batch)

    pilot_rows = []
    selection_rows = []
    selected = {}
    for head in HEADS:
        candidates = []
        for lr in LRS:
            run_id = f"M4_070_pilot__{head}__FAIR1M__lr{lr:g}"
            status = load_status(run_id)
            evaluation = load_eval(run_id)
            row = {
                "run_id": run_id, "head": head, "dataset": "FAIR1M-v1.0",
                "seed": 0, "lr": lr, "epochs": 3, "status": status["status"],
                "amp_mode": status["amp_mode"], "AP50": evaluation["AP50"],
                "AP75": evaluation["AP75"],
                "mean_angle_error": evaluation["mean_angle_error_all_matched"],
                "selection_metrics": "AP50_then_AP75_then_lower_angle_error",
            }
            pilot_rows.append(row)
            if row["status"] == "complete":
                candidates.append(row)
        if not candidates:
            raise RuntimeError(f"{head}: all pilot runs failed")
        winner = max(candidates, key=lambda row: (float(row["AP50"]), float(row["AP75"]),
                                                  -float(row["mean_angle_error"])))
        selected[head] = float(winner["lr"])
        selection_rows.append({
            "head": head, "dataset": "FAIR1M-v1.0", "selected_lr": winner["lr"],
            "pilot_run_id": winner["run_id"], "AP50": winner["AP50"],
            "AP75": winner["AP75"], "mean_angle_error": winner["mean_angle_error"],
            "rule": "max AP50; tie max AP75; tie min angle error; no reliability metric",
        })
    for path, rows in ((ROOT / "reports/m4_third_dataset_pilot_results.csv", pilot_rows),
                       (ROOT / "reports/m4_third_dataset_lr_selection.csv", selection_rows)):
        with path.open("w", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    seed0_jobs = [dict(run_id=f"M4_070_final__{head}__FAIR1M__seed0", head=head, seed=0,
                       lr=selected[head], epochs=12, stage="final") for head in HEADS]
    for batch in batched(seed0_jobs):
        launch_batch(batch)
    for job in seed0_jobs:
        if load_status(job["run_id"])["status"] != "complete" or load_eval(job["run_id"])["evaluation_status"] != "COMPLETE":
            raise RuntimeError(f"seed0 gate failed: {job['run_id']}")

    remaining = [dict(run_id=f"M4_070_final__{head}__FAIR1M__seed{seed}", head=head, seed=seed,
                      lr=selected[head], epochs=12, stage="final")
                 for seed in (1, 2) for head in HEADS]
    for batch in batched(remaining):
        launch_batch(batch)

    subprocess.run([str(PY), str(ROOT / "scripts/aggregate_m4_third_dataset_070.py")],
                   cwd=ROOT, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
