"""Project-native argv entrypoint for the independent r007 verifier."""
from __future__ import annotations

import argparse
import sys

from .verify import main as verify


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", required=True)
    parser.add_argument("--primary", required=True)
    parser.add_argument("--out", required=True)
    values = parser.parse_args()
    sys.argv = ["verify", "--dataset-root", values.dataset_root, "--primary", values.primary, "--out", values.out]
    verify()
