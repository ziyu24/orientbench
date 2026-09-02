"""Real prediction discovery (read-only scan).

Scans allowed roots for candidate prediction/result files, classifies file type,
attempts a SIZE-BOUNDED sniff (never fully loads huge files), and reports
schema status / conversion need. Does not run inference, generate predictions,
or modify pth_data.
"""
from __future__ import annotations

import csv
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_ROOTS = [
    os.fspath(PROJECT_ROOT.parent / "pth_data"),
    os.fspath(PROJECT_ROOT / "runs"),
    os.fspath(PROJECT_ROOT / "outputs"),  # read-only compatibility with old runs
]

CANDIDATE_EXTS = {".json", ".jsonl", ".csv", ".pkl", ".pickle"}
NAME_HINTS = ("bbox", "result", "dets", "prediction", "preds", "detection")
EXCLUDE_EXTS = {".pth", ".log", ".py", ".png", ".jpg", ".jpeg", ".bmp", ".txt", ".md"}
SNIFF_BYTES = 4096
FULL_PARSE_MAX = 5 * 1024 * 1024   # only fully parse files <= 5MB
MAX_CANDIDATES = 4000

_REQUIRED_PRED = {"score", "obb_cx", "obb_cy", "obb_w", "obb_h", "obb_theta"}


def _is_candidate(name: str) -> bool:
    low = name.lower()
    ext = os.path.splitext(low)[1]
    if ext in EXCLUDE_EXTS and not any(h in low for h in NAME_HINTS):
        return False
    if low.endswith(".log.json"):
        return True  # training-log scalars; recorded but flagged
    if ext in CANDIDATE_EXTS:
        return True
    return any(h in low for h in NAME_HINTS)


def _keys_to_schema_status(keys: set) -> Tuple[str, bool]:
    if _REQUIRED_PRED <= keys:
        return "matches_prediction_schema", False
    if {"bbox", "score"} <= keys or {"image_id", "bbox", "score", "category_id"} <= keys:
        return "coco_style_needs_conversion", True
    if {"obb_cx", "obb_theta"} <= keys and "score" not in keys:
        return "gt_like_needs_score", True
    if low_log_keys(keys):
        return "training_log_not_prediction", True
    return "unknown_needs_conversion", True


def low_log_keys(keys: set) -> bool:
    return bool(keys & {"lr", "loss", "memory", "grad_norm", "time", "epoch"}) and \
        not ({"bbox", "score"} & keys)


def _sniff_file(path: str, size: int) -> Tuple[str, str, bool, List[str]]:
    """Return (parse_status, schema_status, needs_conversion, warnings)."""
    ext = os.path.splitext(path)[1].lower()
    warns: List[str] = []
    if ext in (".pkl", ".pickle"):
        return "not_parsed_pickle_placeholder", "unknown_needs_conversion", True, \
            ["pickle not unpickled (placeholder); manual conversion required"]
    try:
        if ext == ".jsonl":
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    line = line.strip()
                    if line:
                        rec = json.loads(line)
                        keys = set(rec.keys()) if isinstance(rec, dict) else set()
                        ss, nc = _keys_to_schema_status(keys)
                        return "parseable_jsonl", ss, nc, warns
            return "empty", "unknown_needs_conversion", True, ["empty jsonl"]
        if ext == ".json":
            if size <= FULL_PARSE_MAX:
                with open(path, "r", encoding="utf-8", errors="replace") as fh:
                    data = json.load(fh)
                rec0 = data[0] if isinstance(data, list) and data else (data if isinstance(data, dict) else None)
                keys = set(rec0.keys()) if isinstance(rec0, dict) else set()
                ss, nc = _keys_to_schema_status(keys)
                return "parseable_json", ss, nc, warns
            # large json: byte sniff for key tokens
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                head = fh.read(SNIFF_BYTES)
            keys = set(re.findall(r'"([a-zA-Z_][a-zA-Z0-9_]*)"\s*:', head))
            ss, nc = _keys_to_schema_status(keys)
            warns.append(f"large json ({size}B) sniffed from first {SNIFF_BYTES}B only")
            return "sniffed_large_json", ss, nc, warns
        if ext == ".csv":
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                reader = csv.reader(fh)
                header = next(reader, [])
            keys = set(header)
            ss, nc = _keys_to_schema_status(keys)
            return "parseable_csv", ss, nc, warns
    except Exception as e:  # noqa: BLE001
        return "parse_error", "unknown_needs_conversion", True, [f"parse error: {e}"]
    return "unknown_type", "unknown_needs_conversion", True, ["unrecognized candidate"]


def probe_bbox_dim(path: str) -> Optional[int]:
    """Size-bounded probe of the first record's bbox length in a coco-style file."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            head = fh.read(16384)
    except OSError:
        return None
    m = re.search(r'"bbox"\s*:\s*\[([^\]]*)\]', head)
    if not m:
        return None
    inner = m.group(1).strip()
    if not inner:
        return 0
    return len([x for x in inner.split(",") if x.strip() != ""])


def classify_ingestion(record: Dict[str, Any]) -> Tuple[str, bool]:
    """Return (ingestion_status, can_enter_formal_orientation_risk).

    Tiers: ready_schema | convertible_bbox_only | convertible_needs_mapping
           | unsupported | missing | synthetic_internal
    bbox_only candidates can NEVER enter the formal orientation-risk gate.
    """
    origin = record.get("origin")
    if origin in ("orientbench_synthetic",):
        return "synthetic_internal", False
    ps = record.get("parse_status", "")
    ss = record.get("schema_status", "")
    if ps == "root_missing":
        return "missing", False
    if ss == "matches_prediction_schema" and origin == "external":
        return "ready_schema", True
    if ss == "training_log_not_prediction":
        return "unsupported", False
    if ps in ("not_parsed_pickle_placeholder", "parse_error", "unknown_type"):
        return "unsupported", False
    if ss == "coco_style_needs_conversion":
        dim = record.get("bbox_dim")
        if dim == 4:
            return "convertible_bbox_only", False     # HBB -> never formal angle gate
        if dim in (5, 8):
            return "convertible_needs_mapping", False  # has OBB but unverified + class map
        return "convertible_needs_mapping", False
    if ss in ("gt_like_needs_score", "unknown_needs_conversion"):
        return "convertible_needs_mapping", False
    return "unsupported", False


def _build_baseline_index(inventory_json: Optional[str]):
    idx = []  # (dir_prefix, id, model_id, dataset)
    if inventory_json and os.path.isfile(inventory_json):
        with open(inventory_json, "r", encoding="utf-8") as fh:
            inv = json.load(fh)
        for r in inv["records"]:
            cfg = r.get("config_abs")
            if cfg:
                idx.append((os.path.dirname(cfg), r.get("id"), r.get("model_id"), r.get("dataset")))
    # longest prefix first
    idx.sort(key=lambda t: -len(t[0]))
    return idx


def _match_baseline(path: str, idx):
    for prefix, bid, model_id, dataset in idx:
        if path.startswith(prefix):
            return bid, model_id, dataset
    # fall back: match on a 'baseline_*' directory token
    m = re.search(r"/(baseline_[^/]+)/", path)
    if m:
        for prefix, bid, model_id, dataset in idx:
            if "/" + m.group(1) + "/" in prefix + "/":
                return bid, model_id, dataset
    return None, None, None


def discover_predictions(
    roots: Optional[List[str]] = None,
    inventory_json: Optional[str] = None,
) -> Dict[str, Any]:
    roots = roots or DEFAULT_ROOTS
    bidx = _build_baseline_index(inventory_json)
    rows: List[Dict[str, Any]] = []
    capped = False
    for root in roots:
        if not os.path.isdir(root):
            rows.append({"baseline_id": None, "model_id": None, "dataset": None,
                         "candidate_path": root, "file_type": "root", "exists": False,
                         "size_bytes": 0, "parse_status": "root_missing",
                         "schema_status": "n/a", "needs_conversion": False,
                         "origin": "n/a", "warnings": ["scan root missing"]})
            continue
        for dirpath, dirnames, filenames in os.walk(root):
            for name in filenames:
                if not _is_candidate(name):
                    continue
                path = os.path.join(dirpath, name)
                if len(rows) >= MAX_CANDIDATES:
                    capped = True
                    break
                try:
                    size = os.path.getsize(path)
                except OSError:
                    size = 0
                parse_status, schema_status, needs_conv, warns = _sniff_file(path, size)
                bid, model_id, dataset = _match_baseline(path, bidx)
                origin = "orientbench_synthetic" if ("/outputs/bench_core/predictions/pred_" in path) else \
                         ("orientbench_output" if "/orientbench/outputs/" in path else "external")
                if origin == "orientbench_synthetic":
                    warns = warns + ["synthetic (our own), not a real detector output"]
                rec = {
                    "baseline_id": bid, "model_id": model_id, "dataset": dataset,
                    "candidate_path": path, "file_type": os.path.splitext(name)[1].lstrip(".") or "noext",
                    "exists": True, "size_bytes": size, "parse_status": parse_status,
                    "schema_status": schema_status, "needs_conversion": needs_conv,
                    "origin": origin, "warnings": warns,
                }
                if schema_status == "coco_style_needs_conversion":
                    rec["bbox_dim"] = probe_bbox_dim(path)
                status, can_formal = classify_ingestion(rec)
                rec["ingestion_status"] = status
                rec["can_enter_formal_orientation_risk"] = can_formal
                rows.append(rec)
            if capped:
                break
        if capped:
            break

    # 'real' = external, not training-log, prediction-ish
    real = [r for r in rows if r["origin"] == "external"
            and r["schema_status"] not in ("training_log_not_prediction",)
            and r["parse_status"] not in ("root_missing",)]
    coco = [r for r in real if r["schema_status"] == "coco_style_needs_conversion"]
    ready = [r for r in real if r["schema_status"] == "matches_prediction_schema"]
    status_counts: Dict[str, int] = {}
    for r in rows:
        st = r.get("ingestion_status", "unsupported")
        status_counts[st] = status_counts.get(st, 0) + 1
    return {
        "roots": roots, "n_candidates": len(rows), "capped": capped,
        "n_external": len([r for r in rows if r["origin"] == "external"]),
        "n_real_predictionish": len(real), "n_coco_needs_conversion": len(coco),
        "n_ready_schema": len(ready),
        "no_real_prediction_found": len(ready) == 0,
        "ingestion_status_counts": status_counts,
        "n_can_enter_formal_orientation_risk": sum(
            1 for r in rows if r.get("can_enter_formal_orientation_risk")),
        "records": rows,
    }
