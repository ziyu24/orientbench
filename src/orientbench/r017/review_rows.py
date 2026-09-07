"""Independent arithmetic review of retained r017 rows; no models or new outcomes."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np


def review(rows_path, summary_path, manifest_path):
    rows = json.loads(rows_path.read_text())
    reported = json.loads(summary_path.read_text())
    manifest = json.loads(manifest_path.read_text())
    expected = {(s, t) for s in (1701, 1702) for t in manifest["calibration_tiles"]}
    if len(rows) != 256 or {(r["seed"], r["tile"]) for r in rows} != expected:
        raise ValueError("incorrect frozen rows")
    for row in rows:
        if tuple(row["block"]) != tuple(int(v) // 2700 for v in row["tile"].split("_")):
            raise ValueError("wrong geographic block")
        actual = (row["loss_au"] - row["loss_av"] + row["loss_bv"] - row["loss_bu"]) / 2
        if abs(actual - row["primary"]) > 1e-12:
            raise ValueError("wrong crossed contrast")
    blocks = list(dict.fromkeys(tuple(row["block"]) for row in rows))
    if len(blocks) != 16:
        raise ValueError("wrong block count")
    metrics = [k for k in rows[0] if k.startswith(("loss_", "delta_")) or k == "primary"]
    seed_values = {str(s): {k: [float(np.mean([r[k] for r in rows if r["seed"] == s and tuple(r["block"]) == b]))
                              for b in blocks] for k in metrics} for s in (1701, 1702)}
    means = {k: np.mean([seed_values[str(s)][k] for s in (1701, 1702)], axis=0) for k in metrics}
    rng = np.random.Generator(np.random.PCG64(17017))
    draws = means["primary"][rng.integers(0, 16, (20000, 16))].mean(1)
    ci = np.quantile(draws, [.025, .975]).tolist()
    output = {"rows_sha256": hashlib.sha256(rows_path.read_bytes()).hexdigest(),
              "reported_summary_sha256": hashlib.sha256(summary_path.read_bytes()).hexdigest(),
              "rows": len(rows), "blocks": blocks, "metric_block_equal": {k: float(v.mean()) for k, v in means.items()},
              "primary_95_ci": ci, "seed_block_values": seed_values,
              "seed_block_equal": {s: {k: float(np.mean(v)) for k, v in values.items()} for s, values in seed_values.items()},
              "primary_vs_report_absolute_difference": abs(float(means["primary"].mean()) - reported["block_equal_primary"]),
              "ci_vs_report_max_absolute_difference": float(np.max(np.abs(np.asarray(ci) - reported["primary_95_ci"]))),
              "scope": "Numerical reproduction of actual cached-label outcomes. Does not validate the broken TTA or restore the planned rasterization/training recipe."}
    return output


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--rows", type=Path, required=True)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = review(args.rows, args.summary, args.manifest)
    args.out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("rows", "primary_95_ci", "primary_vs_report_absolute_difference", "ci_vs_report_max_absolute_difference")}))
