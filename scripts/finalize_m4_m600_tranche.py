#!/usr/bin/env python3
"""Assemble primary m600 raw returns and a separate recheck resolution table."""
from __future__ import annotations

import csv
import json
import os
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "top_journal_v3_reaudit_055/annotation_tools/m4_angle_annotation"


def read(path: Path) -> list[dict]:
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))


def write(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = fields or list(rows[0])
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader(); writer.writerows(rows)
    os.replace(temporary, path)


def outcome(row: dict) -> str:
    if row["long_side_angle_deg_le90"].strip(): return "LABELED"
    if row["ambiguous"] == "1": return "AMBIGUOUS"
    if row["skip"] == "1": return "SKIP"
    return "PENDING"


def main() -> None:
    assignments = read(PKG / "internal/m600_tranche_assignment.csv")
    assignment = {(row["annotator_slot"], row["task_id"]): row for row in assignments}
    exports = {slot: read(PKG / f"annotator_{slot}/outputs_m600_plus_recheck/annotations_{slot}_m600_plus_recheck.csv")
               for slot in "AB"}
    primary_base = {
        "A": read(PKG / "internal/b526_A_combined.csv"),
        "B": read(PKG / "internal/b526_B_frozen_snapshot.csv"),
    }
    recheck_rows = []
    for slot in "AB":
        new_rows = []
        for row in exports[slot]:
            meta = assignment[(slot, row["task_id"])]
            if meta["task_kind"] == "NEW_M600_TARGET":
                new_rows.append(row)
                continue
            other = "B" if slot == "A" else "A"
            counterpart = {x["task_id"]: x for x in primary_base[other]}
            mapping = read(PKG / "internal/instance_id_mapping.csv")
            canonical_to_other = {x["canonical_anon_id"]: x["task_id"] for x in mapping
                                  if x["annotator_slot"] == other}
            other_row = counterpart[canonical_to_other[meta["canonical_anon_id"]]]
            new_state = outcome(row)
            disagreement = ""
            if new_state == "LABELED" and outcome(other_row) == "LABELED":
                a = float(row["long_side_angle_deg_le90"])
                b = float(other_row["long_side_angle_deg_le90"])
                disagreement = f"{abs((a-b+90)%180-90):.6f}"
            recheck_rows.append({
                **meta, "recheck_state": new_state,
                "recheck_angle": row["long_side_angle_deg_le90"],
                "counterpart_angle": other_row["long_side_angle_deg_le90"],
                "resolved_to_numeric_pair": str(bool(disagreement)),
                "resolved_disagreement_deg": disagreement,
            })
        target_tasks = read(PKG / f"annotator_{slot}/m600_target/task_manifest.csv")
        target_by_id = {row["task_id"]: row for row in target_tasks}
        combined = primary_base[slot] + new_rows
        by_id = {row["task_id"]: row for row in combined}
        if len(combined) != 600 or set(by_id) != set(target_by_id):
            raise RuntimeError(f"slot {slot} primary m600 set mismatch")
        ordered = []
        for task in target_tasks:
            row = by_id[task["task_id"]]
            row["task_order"] = task["task_order"]
            ordered.append(row)
        write(PKG / f"internal/m600_{slot}_combined.csv", ordered)
    write(ROOT / "reports/m4_m600_one_sided_recheck.csv", recheck_rows)
    audit = {
        "rechecks": len(recheck_rows),
        "recheck_state_counts": dict(Counter(row["recheck_state"] for row in recheck_rows)),
        "resolved_numeric_pairs": sum(row["resolved_to_numeric_pair"] == "True" for row in recheck_rows),
        "primary_annotations_unchanged": True,
    }
    (ROOT / "reports/m4_m600_one_sided_recheck_audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
