"""Compare independent and production r005 per-object loss recomputations."""
from __future__ import annotations
import argparse, json, math
from pathlib import Path


FIELDS = ("e0_rad", "e1_rad", "retained", "Y0", "C_miss", "C_ang", "DeltaY")


def _key(row):
    return (str(row["image_id"]), int(row["gt_index"]))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--production", type=Path, required=True)
    parser.add_argument("--independent", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    production, independent = json.loads(args.production.read_text()), json.loads(args.independent.read_text())
    result = {"cells": {}, "max_abs_difference": 0.0, "total_key_symmetric_difference": 0}
    for model, pdata in production["models"].items():
        for split, pcells in pdata.items():
            for pcell in pcells:
                condition = pcell["condition"]
                left = {_key(row): row for row in pcell["rows"]}
                right = {_key(row): row for row in independent["models"][model][split][condition]["rows"]}
                missing = sorted(set(left) ^ set(right))
                max_difference = 0.0
                for key in set(left) & set(right):
                    for field in FIELDS:
                        a, b = left[key][field], right[key][field]
                        if a is None or b is None:
                            difference = 0.0 if a is b else math.inf
                        else:
                            difference = abs(float(a) - float(b))
                        max_difference = max(max_difference, difference)
                result["cells"][f"{model}/{split}/{condition}"] = {
                    "production_objects": len(left), "independent_objects": len(right),
                    "key_symmetric_difference": len(missing), "key_examples": [list(item) for item in missing[:10]],
                    "max_abs_difference": max_difference,
                    "production_means": pcell["means"],
                    "independent_means": independent["models"][model][split][condition]["means"],
                }
                result["max_abs_difference"] = max(result["max_abs_difference"], max_difference)
                result["total_key_symmetric_difference"] += len(missing)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
