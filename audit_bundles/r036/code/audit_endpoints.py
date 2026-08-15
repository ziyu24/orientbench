#!/usr/bin/env python3
"""Produce the r036 historical endpoint-consumption audit from repository evidence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "outputs/persistent_artifacts/orientbench_qsetod_kill_study_r036_20260814"
DATA = Path("/home/rspip/cqc/data/dataset")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(4 << 20), b""):
            h.update(block)
    return h.hexdigest()


def files(path: Path) -> list[Path]:
    return sorted(p for p in path.rglob("*") if p.is_file()) if path.is_dir() else []


def main() -> None:
    (OUT / "endpoint_audit").mkdir(parents=True, exist_ok=True)
    candidates = [
        {
            "endpoint": "DOTA-v1.5 val annotations", "path": DATA / "dota/dota1.5/val/annfiles",
            "historically_read": True, "historically_fitted": True, "historically_adjudicated": True,
            "evidence": "claude_code_and_supervisor.md:804,809,831,835,887,1007-1020; historical A4 and 4-detector matrix",
            "legality": "existing local project dataset; read-only", "status_if_present": "CONSUMED",
        },
        {
            "endpoint": "DOTA-v2.0 val annotations", "path": DATA / "dota/dota2.0/val/annfiles",
            "historically_read": False, "historically_fitted": False, "historically_adjudicated": False,
            "evidence": "repository search before r036 found no DOTA-v2.0 scientific execution/adjudication record",
            "legality": "existing local project dataset; read-only; future use still requires a new dispatch", "status_if_present": "CLEAN_ENDPOINT_PRESENT",
        },
        {
            "endpoint": "DIOR-R official test OBB labels", "path": DATA / "DIOR/annfiles/obb",
            "historically_read": True, "historically_fitted": True, "historically_adjudicated": True,
            "evidence": "r014 A/B/C matched_fullval derives from DIOR trainval->test baseline and was used through r034",
            "legality": "existing local project dataset; read-only", "status_if_present": "CONSUMED",
        },
        {
            "endpoint": "FAIR1M official test labels", "path": DATA / "fair1m1.0/raw/test/labelXml",
            "historically_read": False, "historically_fitted": False, "historically_adjudicated": False,
            "evidence": "local FAIR1M tree contains raw/train labels only; project used held-out val tiles",
            "legality": "official test labels unavailable locally", "status_if_present": "CLEAN_ENDPOINT_PRESENT",
        },
        {
            "endpoint": "SODA-A official test labels", "path": DATA / "SODA-A/Annotations/test",
            "historically_read": False, "historically_fitted": False, "historically_adjudicated": False,
            "evidence": "r014/r034 used SODA-A val tiled assets; exact Annotations/test path has no repository execution reference before r036",
            "legality": "existing local project dataset; read-only; future use still requires a new dispatch", "status_if_present": "CLEAN_ENDPOINT_PRESENT",
        },
        {
            "endpoint": "HRSC2016", "path": DATA / "HRSC2016/annfiles",
            "historically_read": True, "historically_fitted": False, "historically_adjudicated": True,
            "evidence": "r014 HRSC inclusion was executed and reported INCONCLUSIVE; project histories and matrices record consumption",
            "legality": "existing local project dataset; read-only", "status_if_present": "CONSUMED",
        },
        {
            "endpoint": "non-remote-sensing scene-text/industrial OBB", "path": DATA / "non_remote_obb",
            "historically_read": False, "historically_fitted": False, "historically_adjudicated": False,
            "evidence": "no local registered asset and no prior OrientBench endpoint record",
            "legality": "not present; no download authorized", "status_if_present": "CLEAN_ENDPOINT_PRESENT",
        },
    ]
    records, manifest = [], []
    for candidate in candidates:
        path = candidate.pop("path")
        children = files(path)
        present = path.is_dir() and len(children) > 0
        status = candidate.pop("status_if_present") if present else "ASSET_MISSING"
        records.append({**candidate, "absolute_path": str(path), "asset_present": present, "asset_file_count": len(children), "status": status, "clean": status == "CLEAN_ENDPOINT_PRESENT"})
        if status == "CLEAN_ENDPOINT_PRESENT":
            for child in children:
                manifest.append({"endpoint": candidate["endpoint"], "relative_path": str(child.relative_to(path)), "bytes": child.stat().st_size, "sha256": sha(child)})
    table = pd.DataFrame(records)
    table.to_csv(OUT / "endpoint_audit/endpoint_consumption_audit.csv", index=False)
    pd.DataFrame(manifest, columns=["endpoint", "relative_path", "bytes", "sha256"]).to_csv(OUT / "endpoint_audit/clean_endpoint_asset_manifest.csv", index=False)
    summary = {"schema": "r036_endpoint_audit_v1", "candidate_count": len(table), "clean_present_count": int(table.clean.sum()), "clean_present": table.loc[table.clean, "endpoint"].tolist(), "venue_cap_due_to_no_clean_endpoint": bool(not table.clean.any()), "note": "Inventory only; clean status does not authorize use, training, or inference."}
    (OUT / "endpoint_audit/summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
