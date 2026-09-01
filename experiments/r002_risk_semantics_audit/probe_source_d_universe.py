#!/usr/bin/env python3
"""Replay the archived production D label attachment without writing labels."""
from __future__ import annotations

import argparse
import importlib.util
import json
import pickle
import sys
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--annotations", required=True, type=Path)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("source_attach_labels", args.source)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    with (args.runtime / "raw/fair24/identity.pkl").open("rb") as stream:
        records = sorted(pickle.load(stream), key=lambda record: str(record["img_id"]))
    names = module.class_names("D")
    rows = []
    for record in records:
        rows.extend(module.match_one(record, args.annotations / f"{record['img_id']}.txt", names, "FAIR1M-v1.0"))
    current = pd.DataFrame(rows)
    legacy = pd.read_parquet(args.runtime / "labels/D.parquet")
    keys = ["image_id", "pred_id", "class_id"]
    payload = {
        "source_rows": len(current),
        "source_audit_rows": int((current.role == "D_audit").sum()),
        "legacy_rows": len(legacy),
        "legacy_audit_rows": int((legacy.role == "D_audit").sum()),
        "keys_equal": set(map(tuple, current[keys].to_numpy())) == set(map(tuple, legacy[keys].to_numpy())),
    }
    print(json.dumps(payload, sort_keys=True))
    if not (payload["keys_equal"] and payload["source_rows"] == payload["legacy_rows"]):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
