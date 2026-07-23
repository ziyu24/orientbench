"""Analyze independently collected M4 le90 long-axis annotations.

Human disagreement and the historical GT-corner-jitter proxy are written to
separate tables. Proxy rows are never described as human annotation variance or
``sigma_gt``. Partial human returns may be summarized, but remain HUMAN_BLOCKED.
"""

import argparse
import csv
import json
import os
from collections import Counter, defaultdict

import numpy as np


ROOT = "/home/rspip/cqc/pro/study/orientbench"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
PAIRS = f"{REP}/m4_human_annotation_pairs.csv"
MERGE_AUDIT = f"{REP}/m4_human_annotation_merge_audit.json"
OUT = f"{REP}/m4_human_annotation_disagreement.csv"
ANALYSIS_AUDIT = f"{REP}/m4_human_annotation_analysis_audit.json"
PROXY_OUT = f"{REP}/m4_gt_jitter_proxy_reference.csv"
K3_DATASET = f"{REP}/k3_gt_angle_noise_by_dataset.csv"
K3_GROUPED = f"{REP}/k3_gt_angle_noise_by_ar_size_class_066.csv"
EXPECTED_DATASETS = ("DIOR-R", "FAIR1M-v1.0", "SODA-A")

HUMAN_FIELDS = [
    "source_kind",
    "is_proxy",
    "dataset",
    "group_type",
    "group_value",
    "subset_definition",
    "n_pairs",
    "mean_circ_disagree_deg",
    "median_circ_disagree_deg",
    "p90_circ_disagree_deg",
    "p95_circ_disagree_deg",
    "P_gt5",
    "P_gt10",
    "status",
]

PROXY_FIELDS = [
    "source_kind",
    "is_proxy",
    "dataset",
    "group_type",
    "group_value",
    "subset_definition",
    "n",
    "mean_deg",
    "median_deg",
    "p90_deg",
    "p95_deg",
    "P_gt5",
    "P_gt10",
    "status",
    "note",
]


def normalize_dataset(value):
    mapping = {
        "DIOR-R_test": "DIOR-R",
        "FAIR1M-v1.0_val20": "FAIR1M-v1.0",
        "SODA-A_val_tiled": "SODA-A",
    }
    return mapping.get(value, value)


def circ_le90(angle_a, angle_b):
    """Absolute pi-periodic disagreement in degrees, in [0, 90]."""
    return abs((float(angle_a) - float(angle_b) + 90.0) % 180.0 - 90.0)


def summarize(values):
    values = np.asarray(values, dtype=float)
    if values.size == 0:
        return {
            "n_pairs": 0,
            "mean_circ_disagree_deg": "",
            "median_circ_disagree_deg": "",
            "p90_circ_disagree_deg": "",
            "p95_circ_disagree_deg": "",
            "P_gt5": "",
            "P_gt10": "",
        }
    return {
        "n_pairs": int(values.size),
        "mean_circ_disagree_deg": round(float(values.mean()), 4),
        "median_circ_disagree_deg": round(float(np.median(values)), 4),
        "p90_circ_disagree_deg": round(float(np.percentile(values, 90)), 4),
        "p95_circ_disagree_deg": round(float(np.percentile(values, 95)), 4),
        "P_gt5": round(float((values > 5.0).mean()), 6),
        "P_gt10": round(float((values > 10.0).mean()), 6),
    }


def human_row(dataset, group_type, group_value, subset_definition, values, status):
    return {
        "source_kind": "HUMAN_INDEPENDENT_DOUBLE_ANNOTATION",
        "is_proxy": "False",
        "dataset": dataset,
        "group_type": group_type,
        "group_value": group_value,
        "subset_definition": subset_definition,
        **summarize(values),
        "status": status,
    }


def write_csv(path, fieldnames, rows):
    temporary = path + ".tmp"
    with open(temporary, "w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temporary, path)


def write_proxy_reference():
    """Normalize K3 proxy statistics into a separately labeled reference table."""
    rows = []
    note = "GT corner-jitter proxy only; not human disagreement, annotation variance, or sigma_gt"
    if os.path.isfile(K3_DATASET):
        for source in csv.DictReader(open(K3_DATASET)):
            dataset = normalize_dataset(source["dataset"])
            rows.append({
                "source_kind": "GT_CORNER_JITTER_PROXY",
                "is_proxy": "True",
                "dataset": dataset,
                "group_type": "dataset",
                "group_value": "all",
                "subset_definition": "all proxy-sampled GT instances",
                "n": source.get("all_n", ""),
                "mean_deg": source.get("all_mean", ""),
                "median_deg": source.get("all_median", ""),
                "p90_deg": source.get("all_p90", ""),
                "p95_deg": source.get("all_p95", ""),
                "P_gt5": source.get("all_P_gt5", ""),
                "P_gt10": "",
                "status": "PROXY_REFERENCE_ONLY",
                "note": note,
            })
            rows.append({
                "source_kind": "GT_CORNER_JITTER_PROXY",
                "is_proxy": "True",
                "dataset": dataset,
                "group_type": "ar_sensitivity",
                "group_value": "ar>=1.6",
                "subset_definition": "historical K3 ar>=1.6 sensitivity; not the ar>=2.1 human endpoint",
                "n": source.get("masked_ar1.6_n", ""),
                "mean_deg": source.get("masked_ar1.6_mean", ""),
                "median_deg": source.get("masked_ar1.6_median", ""),
                "p90_deg": source.get("masked_ar1.6_p90", ""),
                "p95_deg": source.get("masked_ar1.6_p95", ""),
                "P_gt5": source.get("masked_ar1.6_P_gt5", ""),
                "P_gt10": "",
                "status": "PROXY_REFERENCE_ONLY",
                "note": note,
            })
    if os.path.isfile(K3_GROUPED):
        for source in csv.DictReader(open(K3_GROUPED)):
            rows.append({
                "source_kind": "GT_CORNER_JITTER_PROXY",
                "is_proxy": "True",
                "dataset": normalize_dataset(source["dataset"]),
                "group_type": source.get("dim", ""),
                "group_value": source.get("group", ""),
                "subset_definition": "historical K3 proxy stratum",
                "n": source.get("n", ""),
                "mean_deg": source.get("mean", ""),
                "median_deg": source.get("median", ""),
                "p90_deg": source.get("p90", ""),
                "p95_deg": source.get("p95", ""),
                "P_gt5": source.get("P_gt5", ""),
                "P_gt10": "",
                "status": "PROXY_REFERENCE_ONLY",
                "note": note,
            })
    write_csv(PROXY_OUT, PROXY_FIELDS, rows)
    return len(rows)


def main():
    global PAIRS, MERGE_AUDIT, OUT, ANALYSIS_AUDIT, PROXY_OUT
    parser = argparse.ArgumentParser()
    parser.add_argument("--pairs", default=PAIRS)
    parser.add_argument("--merge-audit", default=MERGE_AUDIT)
    parser.add_argument("--output", default=OUT)
    parser.add_argument("--analysis-audit", default=ANALYSIS_AUDIT)
    parser.add_argument("--proxy-output", default=PROXY_OUT)
    args = parser.parse_args()
    PAIRS, MERGE_AUDIT, OUT = args.pairs, args.merge_audit, args.output
    ANALYSIS_AUDIT, PROXY_OUT = args.analysis_audit, args.proxy_output
    proxy_rows = write_proxy_reference()
    pairs = list(csv.DictReader(open(PAIRS))) if os.path.isfile(PAIRS) else []
    merge_audit = json.load(open(MERGE_AUDIT)) if os.path.isfile(MERGE_AUDIT) else {"status": "MISSING_MERGE_AUDIT"}
    usable = []
    for row in pairs:
        if row.get("pair_status") != "COMPLETE" or row.get("human_usable") != "True":
            continue
        try:
            disagreement = circ_le90(row["angleA"], row["angleB"])
            aspect_ratio = float(row["matched_gt_aspect_ratio"])
        except (KeyError, TypeError, ValueError):
            continue
        usable.append({**row, "disagreement": disagreement, "aspect_ratio_numeric": aspect_ratio})

    by_dataset = defaultdict(list)
    for row in usable:
        by_dataset[row["dataset"]].append(row)

    overall_status = merge_audit.get("status", "UNKNOWN")
    result_status = "COMPLETE" if overall_status == "COMPLETE_INDEPENDENT_DOUBLE_ANNOTATION" else "PARTIAL_OR_HUMAN_BLOCKED"
    output_rows = []
    for dataset in EXPECTED_DATASETS:
        dataset_rows = by_dataset.get(dataset, [])
        output_rows.append(
            human_row(
                dataset,
                "dataset",
                "all",
                "all independently double-labeled usable instances",
                [row["disagreement"] for row in dataset_rows],
                result_status if dataset_rows else overall_status,
            )
        )
        ar21_rows = [row for row in dataset_rows if row["aspect_ratio_numeric"] >= 2.1]
        output_rows.append(
            human_row(
                dataset,
                "ar_main",
                "ar>=2.1",
                "matched_GT_aspect_ratio>=2.1",
                [row["disagreement"] for row in ar21_rows],
                result_status if ar21_rows else overall_status,
            )
        )
        for field, group_type in (
            ("matched_gt_class", "class"),
            ("matched_gt_size_bin", "size"),
            ("matched_gt_ar_bin", "ar_bin"),
        ):
            grouped = defaultdict(list)
            for row in dataset_rows:
                grouped[row.get(field, "unknown")].append(row["disagreement"])
            for group_value in sorted(grouped):
                output_rows.append(
                    human_row(
                        dataset,
                        group_type,
                        group_value,
                        f"{field}={group_value}",
                        grouped[group_value],
                        result_status,
                    )
                )
    write_csv(OUT, HUMAN_FIELDS, output_rows)

    audit = {
        "status": overall_status,
        "human_rows_written": len(output_rows),
        "usable_pairs": len(usable),
        "usable_pairs_by_dataset": dict(Counter(row["dataset"] for row in usable)),
        "proxy_table": {
            "path": PROXY_OUT,
            "rows": proxy_rows,
            "source_kind": "GT_CORNER_JITTER_PROXY",
            "strictly_separate_from_human": True,
        },
        "human_table": {
            "path": OUT,
            "source_kind": "HUMAN_INDEPENDENT_DOUBLE_ANNOTATION",
        },
    }
    with open(ANALYSIS_AUDIT + ".tmp", "w") as handle:
        json.dump(audit, handle, indent=2, ensure_ascii=False)
    os.replace(ANALYSIS_AUDIT + ".tmp", ANALYSIS_AUDIT)
    print(f"ANALYZE_{overall_status} usable_pairs={len(usable)} proxy_rows={proxy_rows}")


if __name__ == "__main__":
    main()
