"""Project-native argv entrypoint for the host cqc-run executor."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__:
    from .qualification import main as qualification
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from orientbench.r007.qualification import main as qualification


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--out", required=True)
    values = parser.parse_args()
    sys.argv = ["qualification", "--dataset-root", values.dataset_root, "--out", values.out]
    qualification()
