"""Project-native argv entrypoint for the independent r007 verifier."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

if __package__:
    from .verify import main as verify
else:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from orientbench.r007.verify import main as verify


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--primary", required=True)
    parser.add_argument("--out", required=True)
    values = parser.parse_args()
    sys.argv = ["verify", "--dataset-root", values.dataset_root, "--primary", values.primary, "--out", values.out]
    verify()
