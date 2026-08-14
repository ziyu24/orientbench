#!/usr/bin/env python3
"""Independent validator for the r032 asset-preflight bundle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq


UNITS = list("ABCDEFGH")
FIELDS = ["predicted_ar", "gt_ar", "class_id", "confidence", "predicted_width", "predicted_height", "canonical_angle_error", "row_key", "image_id", "mother_scene_id", "split_role", "official_annotation_id"]
REQUIRED = ["preflight.json", "legacy_quarantine_before.csv", "legacy_quarantine_after.csv", "source_inventory.csv", "field_availability.csv", "join_feasibility.csv", "official_annotation_inventory.csv", "dota_gt_provenance.json", "manuscript_support_inventory.csv", "r033_readiness.json", "execution_ledger.csv", "artifact_manifest.json", "validate_r032.py"]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fail(message: str) -> None:
    raise RuntimeError(message)


def set_sha(values) -> str:
    return hashlib.sha256(("\n".join(sorted(str(x) for x in values)) + "\n").encode()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-dir", type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--quiet", action="store_true")
    args = parser.parse_args()
    bundle = args.bundle_dir.resolve()
    root = Path(__file__).resolve().parents[2]
    checks = []
    try:
        for name in REQUIRED:
            if not (bundle / name).is_file():
                fail(f"missing required output: {name}")

        # Cheap structural checks deliberately precede expensive source recomputation,
        # so the four real mutation copies are rejected for their intended reasons.
        fields = pd.read_csv(bundle / "field_availability.csv", dtype=str, keep_default_na=False)
        expected = {(u, f) for u in UNITS for f in FIELDS}
        actual = list(zip(fields.unit, fields.field))
        if len(actual) != 96 or set(actual) != expected or len(actual) != len(set(actual)):
            fail("field matrix is not the exact 8x12 cartesian product")
        if not set(fields.status) <= {"DIRECT", "DERIVABLE", "MISSING"}:
            fail("invalid field status")
        for row in fields.to_dict("records"):
            if row["status"] == "DIRECT" and (not row["source_path"] or not row["source_column"]):
                fail(f"DIRECT lacks source evidence: {row['unit']}/{row['field']}")
            if row["status"] == "DERIVABLE" and (not row["source_path"] or not row["transform_source_path"] or not row["transform_line"]):
                fail(f"DERIVABLE lacks frozen transform: {row['unit']}/{row['field']}")
            if row["status"] == "MISSING" and row["source_path"]:
                fail(f"MISSING unexpectedly has source: {row['unit']}/{row['field']}")
        checks.append("field_cartesian_and_evidence")

        joins = pd.read_csv(bundle / "join_feasibility.csv", dtype=str, keep_default_na=False)
        join_ids = list(zip(joins.unit, joins.source_role))
        if len(join_ids) != len(set(join_ids)):
            fail("duplicate unit/source_role join row (manufactured cohort duplicate)")
        expected_roles = {(u, r) for u in UNITS for r in ("cohort", "features", "scores", "matched_geometry", "cluster_map", "class_labels")}
        if set(join_ids) != expected_roles:
            fail("join role cartesian set mismatch")
        for col in ("row_count", "unique_key_count", "duplicate_count", "cohort_missing_count", "cohort_drop_count", "extra_count"):
            if (pd.to_numeric(joins[col]) < 0).any():
                fail(f"negative join count: {col}")
        checks.append("join_structure")

        sources = pd.read_csv(bundle / "source_inventory.csv", dtype=str, keep_default_na=False)
        source_ids = list(zip(sources.unit, sources.semantic_role))
        if len(source_ids) != 40 or len(source_ids) != len(set(source_ids)):
            fail("source inventory must contain five unique source roles per unit")
        for row in sources.to_dict("records"):
            path = Path(row["absolute_path"])
            if not path.is_file() or path.stat().st_size != int(row["bytes"]):
                fail(f"source missing/size mismatch: {path}")
            if sha(path) != row["sha256"]:
                fail(f"source SHA mismatch: {path}")
            if path.suffix == ".parquet":
                metadata = pq.read_metadata(path)
                actual_schema, actual_count = "|".join(metadata.schema.names), metadata.num_rows
            elif path.suffix == ".csv":
                with path.open(newline="", encoding="utf-8") as handle:
                    reader = csv.reader(handle); actual_schema = "|".join(next(reader, [])); actual_count = sum(1 for _ in reader)
            elif path.suffix == ".jsonl":
                actual_count = 0; keys = None
                with path.open(encoding="utf-8") as handle:
                    for line in handle:
                        if line.strip():
                            actual_count += 1
                            if keys is None:
                                keys = sorted(json.loads(line))
                actual_schema = "|".join(keys or [])
            else:
                fail(f"unsupported inventoried format: {path}")
            if actual_count != int(row["row_count"]) or actual_schema != row["schema"]:
                fail(f"source schema/row-count mismatch: {path}")
        checks.append("source_paths_bytes_sha")

        before = (bundle / "legacy_quarantine_before.csv").read_bytes()
        after = (bundle / "legacy_quarantine_after.csv").read_bytes()
        if before != after:
            fail("quarantine before/after bytes differ")
        qrows = list(csv.DictReader((bundle / "legacy_quarantine_before.csv").open()))
        allowed = [
            "top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations/",
            "top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations_final/",
            "top_journal_v3_reaudit_055/corrective_audit_r028_20260813/mutations_v2/",
            "top_journal_v3_reaudit_055/corrective_audit_r028_20260813/r026_raw_revalidation/error.json",
            "top_journal_v3_reaudit_055/measurement_validity_r022_20260813/",
            "top_journal_v3_reaudit_055/measurement_validity_r023_20260813/",
        ]
        if any(not any(r["relative_path"].startswith(a) for a in allowed) for r in qrows):
            fail("quarantine path outside allowlist")
        checks.append("quarantine_binary_closure")

        official = pd.read_csv(bundle / "official_annotation_inventory.csv", dtype=str, keep_default_na=False)
        if set(official.dataset) != {"DIOR-R", "FAIR1M-v1.0", "SODA-A", "DOTA-v1.0"} or len(official) != 4:
            fail("official annotation dataset set mismatch")
        for row in official.to_dict("records"):
            manifest = Path(row["manifest_path"])
            # Temp mutation copies keep the original manifest path; resolve by basename.
            local = bundle / "official_manifests" / manifest.name
            if not local.is_file() or sha(local) != row["manifest_sha256"]:
                fail(f"official manifest mismatch: {row['dataset']}")
            entries = list(csv.DictReader(local.open()))
            if len(entries) != int(row["file_count"]) or sum(int(x["bytes"]) for x in entries) != int(row["bytes"]):
                fail(f"official manifest aggregate mismatch: {row['dataset']}")
        checks.append("official_manifests")

        readiness = json.loads((bundle / "r033_readiness.json").read_text())
        any_missing = (fields.status == "MISSING").any()
        any_join_failure = (joins.status != "PASS").any()
        expected_status = "ASSET_GAP_R032" if any_missing or any_join_failure else "ASSET_READY_FOR_R033"
        if readiness.get("status") != expected_status or bool(readiness.get("ready_for_r033")) != (expected_status == "ASSET_READY_FOR_R033"):
            fail("readiness mapping mismatch")
        if expected_status == "ASSET_GAP_R032" and len(readiness.get("gaps", [])) != int((fields.status == "MISSING").sum()):
            fail("readiness gap enumeration mismatch")
        checks.append("readiness_mapping")

        # Recompute cohort key coverage from real tables. JSONL keys are streamed.
        join_by = {(r["unit"], r["source_role"]): r for r in joins.to_dict("records")}
        for unit in UNITS:
            cohort_path = Path(join_by[(unit, "cohort")]["source_path"])
            cohort = pd.read_parquet(cohort_path)
            if unit in "ABCDEF":
                cohort = cohort.loc[cohort["unit"].astype(str) == unit]
            cvals = (cohort.image_id.astype(str) + "\x1f" + cohort.pred_id.astype(str)).tolist()
            cset = set(cvals)
            if len(cvals) != len(cset):
                fail(f"real cohort duplicate: {unit}")
            for role in ("features", "scores", "class_labels"):
                row = join_by[(unit, role)]
                if role == "class_labels" and unit in "GH":
                    vals = cvals
                else:
                    frame = pd.read_parquet(Path(row["source_path"]), columns=["image_id", "pred_id"])
                    vals = (frame.image_id.astype(str) + "\x1f" + frame.pred_id.astype(str)).tolist()
                sset = set(vals)
                if len(vals) - len(sset) != int(row["duplicate_count"]) or len(cset - sset) != int(row["cohort_missing_count"]) or len(sset - cset) != int(row["extra_count"]) or set_sha(sset - cset) != row["extras_sorted_key_sha256"]:
                    fail(f"real key coverage mismatch: {unit}/{role}")
            row = join_by[(unit, "matched_geometry")]
            vals = []
            with Path(row["source_path"]).open(encoding="utf-8") as handle:
                for line in handle:
                    if line.strip():
                        obj = json.loads(line)
                        vals.append(f"{obj['image_id']}\x1f{obj['pred_id']}")
            sset = set(vals)
            if len(vals) - len(sset) != int(row["duplicate_count"]) or len(cset - sset) != int(row["cohort_missing_count"]) or len(sset - cset) != int(row["extra_count"]) or set_sha(sset - cset) != row["extras_sorted_key_sha256"]:
                fail(f"real key coverage mismatch: {unit}/matched_geometry")
            row = join_by[(unit, "cluster_map")]
            cluster = pd.read_csv(Path(row["source_path"]), dtype=str)
            col = "tile_id" if "tile_id" in cluster else ("stem" if "stem" in cluster else "image_id")
            vals = cluster[col].astype(str).tolist(); sset = set(vals); images = set(cohort.image_id.astype(str))
            if len(vals) - len(sset) != int(row["duplicate_count"]) or len(images - sset) != int(row["cohort_missing_count"]) or len(sset - images) != int(row["extra_count"]) or set_sha(sset - images) != row["extras_sorted_key_sha256"]:
                fail(f"real cluster coverage mismatch: {unit}")
        checks.append("real_join_recomputation")

        manifest = json.loads((bundle / "artifact_manifest.json").read_text())
        listed = set()
        for row in manifest["files"]:
            path = bundle / row["relative_path"]
            if row["relative_path"] in listed or not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha(path) != row["sha256"]:
                fail(f"artifact manifest mismatch: {row['relative_path']}")
            listed.add(row["relative_path"])
        actual = {p.relative_to(bundle).as_posix() for p in bundle.rglob("*") if p.is_file() and p.name not in {"artifact_manifest.json", "validation_r032.json"}}
        if listed != actual:
            fail("artifact manifest path set mismatch")
        checks.append("artifact_manifest_path_bytes_sha")

        preflight = json.loads((bundle / "preflight.json").read_text())
        if preflight.get("dispatch_commit_sha") != "a9e1b7f278628962db0ecb82de1fda1a93509a73" or preflight.get("worker") != "server-primary":
            fail("execution identity mismatch")
        subprocess.run(["git", "merge-base", "--is-ancestor", preflight["dispatch_commit_sha"], "HEAD"], cwd=root, check=True)
        if subprocess.check_output(["git", "config", "--local", "paper.worker-id"], cwd=root, text=True).strip() != "server-primary":
            fail("live worker mismatch")
        checks.append("committed_execution_identity")

        result = {"status": "PASS", "checks": checks, "readiness": expected_status, "validated_bundle": str(bundle)}
        if args.output:
            args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
        if not args.quiet:
            print(json.dumps(result, indent=2))
        return 0
    except Exception as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
