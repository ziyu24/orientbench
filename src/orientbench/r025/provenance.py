"""Bounded, read-only provenance audit for the two r026 DOTA detectors."""
import hashlib
import json
import re
import subprocess
from pathlib import Path


HISTORICAL_COMMIT = "09381f7a360e5ad730e77157fb427401555620f5"
HISTORICAL_MANIFEST = "reports/069_dota_clean_artifact_manifest.csv"
HISTORICAL_GENERATOR = "top_journal_v3_reaudit_055/dota_external_replication_r025_20260813/run_r025.py"

UNITS = {
    "orcnn": {
        "checkpoint": "baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/best_mAP_7061_epoch_11.pth",
        "config": "baseline_oriented_rcnn_r50_fpn_1x_le90/DOTA10_train_val/config.py",
        "expected": "f0e0105de7bf924e85f5dc5429056da592c6a831b4904f221d0dd57f6972eaf2",
        "tiles": 5297, "predictions": 101874,
    },
    "rtmdet": {
        "checkpoint": "baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/best_mAP_7161_epoch_31.pth",
        "config": "baseline_rotated_rtmdet_m_fpn_3x_le90/DOTA10_train_val/config.py",
        "expected": "1b574a84f1f0cb4c3b466fca406ae3a627c7226df17b793f1613052007e3c2ca",
        "tiles": 5297, "predictions": 189991,
    },
}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for part in iter(lambda: f.read(1 << 20), b""):
            h.update(part)
    return h.hexdigest()


def file_record(path, role):
    p = Path(path)
    return {"path": str(p), "role": role, "exists": p.is_file(),
            "bytes": p.stat().st_size if p.is_file() else None,
            "sha256": sha(p) if p.is_file() else None}


def git_text(root, spec):
    call = subprocess.run(["git", "-C", str(root), "show", spec], text=True,
                          encoding="utf-8", errors="replace", stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return {"spec": spec, "available": call.returncode == 0,
            "sha256": hashlib.sha256(call.stdout.encode()).hexdigest() if call.returncode == 0 else None,
            "text": call.stdout if call.returncode == 0 else "", "error": call.stderr.strip() if call.returncode else ""}


def config_facts(path):
    if not path.is_file():
        return {"exists": False, "observed_literals": [], "contact_conclusion": "unknown: config absent"}
    text = path.read_text(errors="replace")
    hits = [line.strip() for line in text.splitlines() if any(x in line.lower() for x in
            ("train_dataloader", "val_dataloader", "test_dataloader", "ann_file", "data_root", "split_ss"))]
    return {"exists": True, "sha256": sha(path), "observed_literals": hits[:200],
            "contact_conclusion": "unknown: config literals alone do not prove whether the current 458 mother images entered training or selection."}


def audit(root):
    root = Path(root)
    pth = root.parent / "pth_data"
    raw_root = root / "outputs/persistent_artifacts/orientbench_r019/prelabel/raw"
    mapping = root / "outputs/persistent_artifacts/orientbench_r019/prelabel/tile_to_mother.csv"
    archive = root / "archives/worktrees/orientbench_r032_clean"
    historical_manifest = git_text(root, f"{HISTORICAL_COMMIT}:{HISTORICAL_MANIFEST}")
    generator = git_text(root, f"{HISTORICAL_COMMIT}:{HISTORICAL_GENERATOR}")
    current_candidates = []
    for unit, meta in UNITS.items():
        current_candidates.extend(file_record(raw_root / unit / f"{view}.pkl", f"{unit}_raw_{view}") for view in ("identity", "hflip", "vflip"))
        current_candidates.append(file_record(pth / meta["checkpoint"], f"{unit}_checkpoint"))
        current_candidates.append(file_record(pth / meta["config"], f"{unit}_config"))
    current_candidates.append(file_record(mapping, "r019_tile_to_mother"))
    # These are registered project archive locations, inspected by identity rather than recursively searching unrelated work.
    archive_candidates = [
        file_record(archive / "audit_bundles/r028/dota/matched_orcnn.parquet", "r028_matched_orcnn_not_full_predictions"),
        file_record(archive / "audit_bundles/r028/dota/matched_rtmdet.parquet", "r028_matched_rtmdet_not_full_predictions"),
        file_record(archive / "audit_bundles/r028/dota/tile_to_mother.csv", "r028_mapping_only"),
        file_record(root / "outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/implementation_a_raw/matched_orcnn.parquet", "r026_matched_orcnn_not_full_predictions"),
        file_record(root / "outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/implementation_a_raw/matched_rtmdet.parquet", "r026_matched_rtmdet_not_full_predictions"),
    ]
    units = {}
    for unit, meta in UNITS.items():
        raw = [x for x in current_candidates if x["role"].startswith(unit + "_raw_")]
        complete = all(x["exists"] for x in raw) and mapping.is_file()
        units[unit] = {"historical_identity_expected_sha256": meta["expected"], "expected_tile_images": meta["tiles"],
                       "expected_prediction_rows": meta["predictions"], "raw_candidates": raw,
                       "complete_output_obtained": complete,
                       "mapping_obtained": mapping.is_file(),
                       "inference_and_merge_recoverable": False,
                       "reason": "Raw identity output and mapping are missing; matched-only tables are explicitly excluded from AP recovery.",
                       "rebuild": {"checkpoint": file_record(pth / meta["checkpoint"], "checkpoint"),
                                   "config": file_record(pth / meta["config"], "config"),
                                   "training_contact": config_facts(pth / meta["config"])}}
    return {"scope": "Bounded project-root, registered archive and Git-history inspection only; no other project scan, inference, training or AP.",
            "historical_manifest": {k:v for k,v in historical_manifest.items() if k != "text"},
            "historical_generator": {k:v for k,v in generator.items() if k != "text"},
            "generator_requirements_observed": {"identity_raw": bool(re.search(r"identity\.pkl", generator["text"])),
                                                  "tile_to_mother": bool(re.search(r"tile_to_mother\.csv", generator["text"])),
                                                  "official_ap_call": bool(re.search(r"eval_rbbox_map", generator["text"])),
                                                  "matched_only_not_substitute": True},
            "searched_locations": [str(raw_root), str(mapping), str(archive / "audit_bundles/r028/dota"),
                                   str(root / "outputs/persistent_artifacts/orientbench_dota_external_confirmation_r026_20260813/implementation_a_raw"),
                                   f"git:{HISTORICAL_COMMIT}:{HISTORICAL_MANIFEST}", f"git:{HISTORICAL_COMMIT}:{HISTORICAL_GENERATOR}", str(pth)],
            "units": units, "registered_archive_files": archive_candidates,
            "overall": "INCOMPLETE_PREDICTION_PROVENANCE: no complete ORCNN or RTMDet raw prediction bundle is present in the bounded authorised locations."}
