#!/usr/bin/env python3
"""Regenerate all r044 figure pairs and their source tables."""
from pathlib import Path
import runpy

root = Path(__file__).resolve().parents[3]
script = root / "outputs/persistent_artifacts/orientbench_jprs_manuscript_r044_20260818/build_package.py"
runpy.run_path(str(script), run_name="__main__")
