#!/usr/bin/env python3
"""Write the decision-facing metrics for the 200-instance human pilot."""
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np


def summarize(label: str, rows: list[dict], seed: int) -> dict:
    values = np.asarray([abs((float(row["angleA"]) - float(row["angleB"]) + 90) % 180 - 90)
                         for row in rows], dtype=float)
    result = {"subset": label, "n_usable": int(values.size)}
    if not values.size:
        return {**result, "mean_deg": "", "mean_cluster_ci95_low": "",
                "mean_cluster_ci95_high": "", "median_deg": "", "p90_deg": "",
                "p95_deg": "", "P_gt5": "", "P_gt5_cluster_ci95_low": "",
                "P_gt5_cluster_ci95_high": "", "P_gt10": "",
                "P_gt10_cluster_ci95_low": "", "P_gt10_cluster_ci95_high": ""}
    clusters = {}
    for row, value in zip(rows, values):
        clusters.setdefault(row["image_id"], []).append(float(value))
    keys = list(clusters)
    rng = np.random.default_rng(seed)
    bootstrap_mean = []
    bootstrap_p5 = []
    bootstrap_p10 = []
    for _ in range(10000):
        sampled = rng.choice(keys, size=len(keys), replace=True)
        sampled_values = np.asarray([value for key in sampled for value in clusters[key]])
        bootstrap_mean.append(float(sampled_values.mean()))
        bootstrap_p5.append(float((sampled_values > 5).mean()))
        bootstrap_p10.append(float((sampled_values > 10).mean()))
    mean_low, mean_high = np.percentile(bootstrap_mean, [2.5, 97.5])
    p5_low, p5_high = np.percentile(bootstrap_p5, [2.5, 97.5])
    p10_low, p10_high = np.percentile(bootstrap_p10, [2.5, 97.5])
    return {
        **result,
        "mean_deg": round(float(values.mean()), 4),
        "mean_cluster_ci95_low": round(float(mean_low), 4),
        "mean_cluster_ci95_high": round(float(mean_high), 4),
        "median_deg": round(float(np.median(values)), 4),
        "p90_deg": round(float(np.percentile(values, 90)), 4),
        "p95_deg": round(float(np.percentile(values, 95)), 4),
        "P_gt5": round(float((values > 5).mean()), 6),
        "P_gt5_cluster_ci95_low": round(float(p5_low), 6),
        "P_gt5_cluster_ci95_high": round(float(p5_high), 6),
        "P_gt10": round(float((values > 10).mean()), 6),
        "P_gt10_cluster_ci95_low": round(float(p10_low), 6),
        "P_gt10_cluster_ci95_high": round(float(p10_high), 6),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    with args.pairs.open(newline="") as handle:
        pairs = list(csv.DictReader(handle))
    usable = [row for row in pairs if row["human_usable"] == "True" and row["pair_status"] == "COMPLETE"]
    rows = [summarize("ALL", usable, 71210)]
    for index, dataset in enumerate(("DIOR-R", "FAIR1M-v1.0", "SODA-A"), 1):
        rows.append(summarize(
            dataset,
            [row for row in usable if row["dataset"] == dataset],
            71210 + index,
        ))
    rows.append(summarize(
        "ar>=2.1",
        [row for row in usable if float(row["matched_gt_aspect_ratio"]) >= 2.1],
        71214,
    ))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    audit = {
        "status": "PILOT_RESULTS_READY_FOR_HUMAN_REVIEW",
        "target_pairs": len(pairs),
        "usable_pairs": len(usable),
        "pair_status_counts": dict(Counter(row["pair_status"] for row in pairs)),
        "scale_up_decision": "NOT_AUTOMATIC; review pilot metrics before expanding to 1500",
        "metrics": ["mean", "median", "p90", "p95", "P(>5deg)", "P(>10deg)"],
        "strata_in_detailed_table": ["dataset", "class", "size", "aspect-ratio bin", "ar>=2.1"],
    }
    args.audit.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
