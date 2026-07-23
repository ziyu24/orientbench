#!/usr/bin/env python3
"""Analyze the genuine A/B overlap currently present in annotation drafts."""
from __future__ import annotations

import csv
import hashlib
import json
import os
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation"
REPORT = ROOT / "reports/m4_pilot_current_overlap_key_metrics.csv"
AUDIT = ROOT / "reports/m4_pilot_current_overlap_audit.json"
FIELDS = [
    "subset", "overlap_instances", "usable_angle_pairs", "mean_deg",
    "mean_image_cluster_bootstrap_ci95_low", "mean_image_cluster_bootstrap_ci95_high",
    "median_deg", "p90_deg", "p95_deg", "P_gt5", "P_gt10",
]


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def state(record: dict) -> str:
    if record.get("angle") is not None:
        return "ANGLE"
    if record.get("ambiguous"):
        return "AMBIGUOUS"
    if record.get("skip"):
        return "SKIP"
    return "PENDING"


def summarize(label: str, overlap_count: int, rows: list[dict], seed: int) -> dict:
    values = np.asarray([row["disagreement"] for row in rows], dtype=float)
    result = {"subset": label, "overlap_instances": overlap_count,
              "usable_angle_pairs": int(values.size)}
    if not values.size:
        return {**result, **{field: "" for field in FIELDS[3:]}}
    clusters = defaultdict(list)
    for row in rows:
        clusters[row["image_id"]].append(row["disagreement"])
    keys = list(clusters)
    rng = np.random.default_rng(seed)
    boot = []
    for _ in range(10000):
        sampled = rng.choice(keys, size=len(keys), replace=True)
        sampled_values = [value for key in sampled for value in clusters[key]]
        boot.append(float(np.mean(sampled_values)))
    low, high = np.percentile(boot, [2.5, 97.5])
    return {
        **result,
        "mean_deg": round(float(values.mean()), 4),
        "mean_image_cluster_bootstrap_ci95_low": round(float(low), 4),
        "mean_image_cluster_bootstrap_ci95_high": round(float(high), 4),
        "median_deg": round(float(np.median(values)), 4),
        "p90_deg": round(float(np.percentile(values, 90)), 4),
        "p95_deg": round(float(np.percentile(values, 95)), 4),
        "P_gt5": round(float((values > 5).mean()), 6),
        "P_gt10": round(float((values > 10).mean()), 6),
    }


def main() -> None:
    mapping_rows = list(csv.DictReader((PKG / "internal/instance_id_mapping.csv").open()))
    mapping = {(row["annotator_slot"], row["task_id"]): row["canonical_anon_id"]
               for row in mapping_rows}
    metadata = {row["anon_id"]: row for row in
                csv.DictReader((ROOT / "reports/m4_human_annotation_sampling_manifest.csv").open())}
    draft_paths = {slot: PKG / f"annotator_{slot}/outputs/draft_state.json" for slot in "AB"}
    drafts = {slot: json.loads(path.read_text()) for slot, path in draft_paths.items()}
    by_canonical = {
        slot: {mapping[(slot, task_id)]: record
               for task_id, record in drafts[slot]["records"].items()}
        for slot in "AB"
    }
    overlap = sorted(set(by_canonical["A"]) & set(by_canonical["B"]))
    pair_states = Counter()
    usable = []
    for canonical in overlap:
        a = by_canonical["A"][canonical]
        b = by_canonical["B"][canonical]
        state_a, state_b = state(a), state(b)
        pair_states[f"{state_a}|{state_b}"] += 1
        if state_a == state_b == "ANGLE":
            disagreement = abs((float(a["angle"]) - float(b["angle"]) + 90) % 180 - 90)
            usable.append({
                "canonical": canonical,
                "dataset": metadata[canonical]["dataset"],
                "image_id": metadata[canonical]["image_id"],
                "aspect_ratio": float(metadata[canonical]["matched_gt_aspect_ratio"]),
                "disagreement": disagreement,
            })

    output = [summarize("ALL", len(overlap), usable, 71001)]
    for index, dataset in enumerate(("DIOR-R", "FAIR1M-v1.0", "SODA-A"), 1):
        dataset_overlap = sum(metadata[item]["dataset"] == dataset for item in overlap)
        output.append(summarize(
            dataset, dataset_overlap,
            [row for row in usable if row["dataset"] == dataset],
            71001 + index,
        ))
    ar_overlap = sum(float(metadata[item]["matched_gt_aspect_ratio"]) >= 2.1 for item in overlap)
    output.append(summarize(
        "ar>=2.1", ar_overlap,
        [row for row in usable if row["aspect_ratio"] >= 2.1],
        71005,
    ))
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    temp = REPORT.with_suffix(".csv.tmp")
    with temp.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    os.replace(temp, REPORT)

    identity_a = drafts["A"].get("annotator_id", "")
    identity_b = drafts["B"].get("annotator_id", "")
    audit = {
        "status": "PRELIMINARY_OVERLAP_ONLY",
        "a_records": len(drafts["A"]["records"]),
        "b_records": len(drafts["B"]["records"]),
        "canonical_overlap": len(overlap),
        "usable_angle_pairs": len(usable),
        "overlap_by_dataset": dict(Counter(metadata[item]["dataset"] for item in overlap)),
        "usable_by_dataset": dict(Counter(row["dataset"] for row in usable)),
        "pair_state_counts": dict(pair_states),
        "annotator_identities_present_and_distinct": bool(
            identity_a and identity_b and identity_a != identity_b
        ),
        "draft_sha256": {slot: sha256(path) for slot, path in draft_paths.items()},
        "paper_interpretation": (
            "Promising inter-annotator agreement signal, but insufficient for a paper claim "
            "or a 1500-instance scale-up decision because only 17 usable matched angle pairs "
            "and 2 usable SODA-A pairs are available."
        ),
        "next_gate": "Complete the same canonical 200-instance pilot before deciding on 1500.",
    }
    AUDIT.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({"report": str(REPORT), **audit}, ensure_ascii=False))


if __name__ == "__main__":
    main()
