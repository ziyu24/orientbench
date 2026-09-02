"""Run the frozen trainval candidate grid for one r004 detector."""
from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from .prepare_inference import MODELS


def main() -> None:
    p = argparse.ArgumentParser(); p.add_argument("--run-root", required=True, type=Path); p.add_argument("--pth-root", required=True, type=Path)
    p.add_argument("--tool", required=True, type=Path); p.add_argument("--python", required=True); p.add_argument("--model", choices=MODELS, required=True)
    args = p.parse_args()
    for kind, doses in (("blur", (.5,.75,1.,1.25,1.5)), ("downsample", (1.25,1.5,1.75,2.))):
        for dose in doses:
            label = f"{kind}_{dose:g}"
            root = args.run_root / "inference" / "trainval" / args.model / label
            output = root / "predictions.pkl"
            if output.exists():
                continue
            ckpt = args.pth_root / MODELS[args.model]["checkpoint"]
            subprocess.run([args.python, str(args.tool), str(root / "runtime_config.py"), str(ckpt), "--out", str(output)], check=True)


if __name__ == "__main__":
    main()
