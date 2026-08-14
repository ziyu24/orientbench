#!/usr/bin/env python3
"""Run six real temp-copy mutations against the same raw r034 validator."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "outputs/persistent_artifacts/orientbench_circularity_decisive_r034_20260814"
HERE = Path(__file__).resolve().parent
VALIDATOR = HERE / "validate_r034.py"


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(8 << 20), b""): h.update(b)
    return h.hexdigest()


def break_link(path):
    temporary = path.with_name(path.name + ".private")
    shutil.copy2(path, temporary); os.replace(temporary, path)


def refresh_a_manifest(root, relative):
    manifest_path = root / "implementation_a/manifest.csv"; break_link(manifest_path)
    manifest = pd.read_csv(manifest_path); target = root / "implementation_a" / relative
    manifest.loc[manifest.path.eq(relative), ["bytes", "sha256"]] = [target.stat().st_size, sha(target)]
    manifest.to_csv(manifest_path, index=False, lineterminator="\n")


def mutate(root, name):
    if name == "k1_threshold_08_to_0":
        path = root / "implementation_a/protocol.json"; break_link(path); doc = json.loads(path.read_text()); doc["K1_ratio_threshold"] = 0.0; path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n"); refresh_a_manifest(root, "protocol.json")
    elif name == "primary_estimand_to_pooled":
        path = root / "implementation_a/protocol.json"; break_link(path); doc = json.loads(path.read_text()); doc["primary_estimand"] = "pooled"; path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n"); refresh_a_manifest(root, "protocol.json")
    elif name == "raw_risk_relation":
        path = root / "inputs/matched_rows_enriched.parquet"; break_link(path); frame = pd.read_parquet(path); frame.loc[0, "risk_raw"] = min(1.0, float(frame.loc[0, "risk_raw"]) + .01); frame.to_parquet(path, index=False, compression="zstd")
    elif name == "primary_dod_numeric":
        path = root / "implementation_a/primary_family.csv"; break_link(path); frame = pd.read_csv(path); frame.loc[0, "dod"] += .01; frame.to_csv(path, index=False, lineterminator="\n"); refresh_a_manifest(root, "primary_family.csv")
    elif name == "bootstrap_multiplicity":
        path = root / "implementation_a/multiplicities.npz"; break_link(path); values = np.load(path); arrays = {k: values[k].copy() for k in values.files}; a = arrays["DOTA-v1.0"]; nz = np.flatnonzero(a[0] > 0); a[0, nz[0]] -= 1; a[0, (nz[0] + 1) % a.shape[1]] += 1; np.savez_compressed(path, **arrays); refresh_a_manifest(root, "multiplicities.npz")
    elif name == "judgment_token":
        path = root / "implementation_a/judgment.json"; break_link(path); doc = json.loads(path.read_text()); doc["K2"] = False; doc["candidate_state"] = "SURVIVES_TOP_JOURNAL_ROUTE"; path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n"); refresh_a_manifest(root, "judgment.json")
    else: raise KeyError(name)


def main():
    names = ["k1_threshold_08_to_0", "primary_estimand_to_pooled", "raw_risk_relation", "primary_dod_numeric", "bootstrap_multiplicity", "judgment_token"]
    results = []
    HERE.joinpath("mutations").mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="work_", dir=HERE / "mutations") as temporary:
        base = Path(temporary)
        for name in names:
            target = base / name; shutil.copytree(SOURCE, target, copy_function=os.link); mutate(target, name)
            env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", NUMEXPR_NUM_THREADS="1")
            proc = subprocess.run([sys.executable, str(VALIDATOR), "--root", str(target), "--workers", "96", "--quiet"], cwd=ROOT, text=True, capture_output=True, env=env)
            diagnostic = (proc.stderr or proc.stdout).strip().splitlines()[-1:]
            results.append({"mutation": name, "exit_code": proc.returncode, "rejected": proc.returncode != 0, "diagnostic": diagnostic})
            if proc.returncode == 0: raise RuntimeError("mutation not rejected: " + name)
            shutil.rmtree(target)
    output = {"status": "PASS", "validator": str(VALIDATOR.relative_to(ROOT)), "real_subprocess_mutations": len(results), "results": results}
    (HERE / "mutations/mutation_results.json").write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(json.dumps(output, sort_keys=True))


if __name__ == "__main__": main()
