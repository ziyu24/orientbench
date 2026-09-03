"""Project-native argv entrypoint for the host cqc-run executor."""
from __future__ import annotations

import argparse

from .qualification import main as qualification


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--out", required=True)
    values = parser.parse_args()
    import sys
    sys.argv = ["qualification", "--dataset-root", values.dataset_root, "--out", values.out]
    qualification()
