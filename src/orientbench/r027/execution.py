"""Single bounded execution entry point for the restarted r027 audit."""
import argparse
import sys
from pathlib import Path

from orientbench.r025 import run as correspondence
from orientbench.r025 import verify as independent_verify
from orientbench.r027 import qualify


def invoke(entrypoint, arguments):
    prior = sys.argv
    try:
        sys.argv = [entrypoint.__module__, *arguments]
        entrypoint()
    finally:
        sys.argv = prior


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args()
    root = args.root.resolve()
    run_root = root / "runs/r027"
    qualification = run_root / "qualification"
    artifacts = run_root / "artifacts"
    invoke(qualify.main, ["--root", str(root), "--output-dir", str(qualification)])
    invoke(correspondence.main, ["--root", str(root), "--run-id", "r027", "--output-dir", str(artifacts)])
    invoke(independent_verify.main, ["--root", str(root), "--run-id", "r027", "--output-dir", str(artifacts)])


if __name__ == "__main__":
    main()
