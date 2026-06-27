#!/usr/bin/env python3
"""01_inventory_baselines.py — parse pth_data/readme.md into baseline inventory.

Outputs (under --out-dir, default outputs/bench_core):
    baseline_inventory.json    full records + warnings + provenance
    baseline_inventory.csv     flat one-row-per-baseline export
    baseline_valid_only.csv    subset where valid is True

Read-only on the readme and pth_data. Does not start training, download,
or modify pth_data.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys

# allow running as a standalone script
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from orientbench.io.baseline_readme import (  # noqa: E402
    CSV_COLUMNS,
    parse_baseline_readme,
)

DEFAULT_README = "/home/rspip/cqc/pro/study/pth_data/readme.md"
DEFAULT_PTH_DATA = "/home/rspip/cqc/pro/study/pth_data"
DEFAULT_OUT_DIR = os.path.join(_PROJECT_ROOT, "outputs", "bench_core")


def _write_csv(path: str, records, columns) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=columns, extrasaction="ignore")
        w.writeheader()
        for r in records:
            row = {k: ("" if r.get(k) is None else r.get(k)) for k in columns}
            w.writerow(row)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--readme", default=DEFAULT_README, help="path to pth_data/readme.md")
    ap.add_argument("--pth-data-root", default=DEFAULT_PTH_DATA,
                    help="root for resolving relative pth/log/config links")
    ap.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="output directory")
    ap.add_argument("--no-existence-check", action="store_true",
                    help="skip on-disk pth/log/config existence checks")
    args = ap.parse_args(argv)

    if not os.path.isfile(args.readme):
        print(f"[FATAL] readme not found: {args.readme}", file=sys.stderr)
        return 2

    result = parse_baseline_readme(
        args.readme, args.pth_data_root, check_existence=not args.no_existence_check
    )

    os.makedirs(args.out_dir, exist_ok=True)
    json_path = os.path.join(args.out_dir, "baseline_inventory.json")
    csv_path = os.path.join(args.out_dir, "baseline_inventory.csv")
    valid_csv_path = os.path.join(args.out_dir, "baseline_valid_only.csv")

    n_total = result.n_total
    n_valid = result.n_valid
    n_invalid = n_total - n_valid
    valid_records = [r for r in result.records if r.get("valid") is True]

    # field-missing statistics (None / "unknown")
    missing_stats = {}
    for col in CSV_COLUMNS:
        miss = sum(
            1 for r in result.records
            if r.get(col) is None or r.get(col) == "unknown" or r.get(col) == ""
        )
        if miss:
            missing_stats[col] = miss

    n_with_warnings = sum(1 for r in result.records if r.get("warnings"))
    pth_missing = sum(1 for r in result.records if r.get("pth_exists") is False)

    payload = {
        "generated_from": result.source_readme,
        "pth_data_root": result.pth_data_root,
        "n_total": n_total,
        "n_valid": n_valid,
        "n_invalid": n_invalid,
        "n_records_with_warnings": n_with_warnings,
        "n_pth_not_on_disk": pth_missing,
        "field_missing_counts": missing_stats,
        "parse_warnings": result.warnings,
        "records": result.records,
    }

    with open(json_path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False, indent=2)

    _write_csv(csv_path, result.records, CSV_COLUMNS)
    _write_csv(valid_csv_path, valid_records, CSV_COLUMNS)

    print(f"[ok] parsed {n_total} baselines ({n_valid} valid, {n_invalid} invalid)")
    print(f"[ok] records with warnings: {n_with_warnings}; pth not on disk: {pth_missing}")
    if missing_stats:
        print(f"[ok] field-missing counts: {missing_stats}")
    print(f"[ok] wrote {json_path}")
    print(f"[ok] wrote {csv_path}")
    print(f"[ok] wrote {valid_csv_path}")

    # RHINO-style rotated DETR check (D2 R6 host candidate)
    rhino = [r for r in result.records if "rhino" in (r.get("model_id") or "").lower()]
    if rhino:
        print(f"[rhino] found {len(rhino)} RHINO-style baseline(s): "
              f"{[r['model_id'] for r in rhino]}")
    else:
        print("[rhino] NOT FOUND: RHINO-style rotated DETR absent in pth_data/readme.md")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
