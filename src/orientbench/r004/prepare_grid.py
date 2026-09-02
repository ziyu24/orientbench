"""Materialise the frozen trainval intervention candidate grid for r004."""
from __future__ import annotations

import argparse
import subprocess
import sys


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--run-root", required=True); p.add_argument("--dataset-root", required=True); p.add_argument("--pth-root", required=True)
    args = p.parse_args()
    for corruption, doses in (("blur", (.5, .75, 1., 1.25, 1.5)), ("downsample", (1.25, 1.5, 1.75, 2.))):
        for dose in doses:
            for model in ("oriented_rcnn_r50", "rotated_rtmdet_m"):
                cmd = [sys.executable, "-m", "orientbench.r004.prepare_inference", "--run-root", args.run_root,
                       "--dataset-root", args.dataset_root, "--pth-root", args.pth_root, "--model", model,
                       "--split", "trainval", "--corruption", corruption, "--dose", str(dose)]
                subprocess.run(cmd, check=True)


if __name__ == "__main__":
    main()
