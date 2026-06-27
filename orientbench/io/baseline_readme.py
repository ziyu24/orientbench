"""Parser for pth_data/readme.md baseline inventory.

Reads the markdown baseline catalog (read-only) and produces a normalized
inventory of baseline models. Field set follows 项目执行文件.md §4.2.

Design notes / conservative defaults (per 002 instruction):
  - Fields that cannot be reliably extracted are filled with `None`
    (json null) or the string ``"unknown"`` and a per-record / global
    warning is recorded. Nothing is silently dropped.
  - `valid` is normalized to a Python ``bool``.
  - ``mAP_best`` / ``epoch_best`` / ``id`` are coerced to numbers; on
    failure the raw string is kept and a warning is appended.
  - Relative pth/log/config link targets are resolved to absolute paths
    under ``pth_data_root`` while the original relative path is preserved.
  - ``inference_ready`` is inferred from (valid AND pth/log/config link
    fields all present). Actual on-disk presence is reported separately as
    ``pth_exists`` / ``log_exists`` / ``config_exists`` and never downgrades
    ``valid`` or ``inference_ready``.

This module performs parsing only; on-disk existence checks are optional
and gated by ``check_existence``.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# Required output fields (项目执行文件.md §4.2), in canonical order.
REQUIRED_FIELDS: List[str] = [
    "id",
    "model_id",
    "dataset",
    "train_val_or_trainval_test",
    "epoch_best",
    "mAP_best",
    "valid",
    "pth",
    "log",
    "config",
    "source",
    "mmrotate_stack",
    "env",
    "actual_gb",
    "per_gpu_bs",
    "gpus",
    "actual_lr",
    "optimizer",
    "scheduler",
    "angle",
    "metric",
    "eval_interval",
    "inference_ready",
]

_LINK_RE = re.compile(r"\[([^\]]*)\]\(([^)]*)\)")
_BOLD_RE = re.compile(r"[*`]")  # markdown bold/code emphasis markers
_SEP_CELL_RE = re.compile(r"^:?-{2,}:?$")


@dataclass
class Table:
    headers: List[str]
    rows: List[List[str]]
    start_line: int  # 1-based line number of the header row


@dataclass
class InventoryResult:
    records: List[Dict[str, Any]]
    warnings: List[str] = field(default_factory=list)
    source_readme: Optional[str] = None
    pth_data_root: Optional[str] = None

    @property
    def n_total(self) -> int:
        return len(self.records)

    @property
    def n_valid(self) -> int:
        return sum(1 for r in self.records if r.get("valid") is True)


# --------------------------------------------------------------------------
# Generic markdown table extraction
# --------------------------------------------------------------------------
def _split_row(line: str) -> List[str]:
    """Split a markdown table row into stripped cells (drop leading/trailing |)."""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def _is_separator_row(cells: List[str]) -> bool:
    return len(cells) > 0 and all(_SEP_CELL_RE.match(c.strip()) for c in cells if c.strip() != "") and any(
        _SEP_CELL_RE.match(c.strip()) for c in cells
    )


def extract_tables(text: str) -> List[Table]:
    """Extract every GitHub-flavored markdown table from ``text``.

    A table is a header pipe-row immediately followed by a separator
    pipe-row (``|---|---|``), then zero or more data pipe-rows.
    """
    lines = text.splitlines()
    tables: List[Table] = []
    i = 0
    n = len(lines)
    while i < n - 1:
        line = lines[i]
        nxt = lines[i + 1]
        if line.lstrip().startswith("|") and nxt.lstrip().startswith("|") and _is_separator_row(_split_row(nxt)):
            headers = _split_row(line)
            rows: List[List[str]] = []
            j = i + 2
            while j < n and lines[j].lstrip().startswith("|"):
                rows.append(_split_row(lines[j]))
                j += 1
            tables.append(Table(headers=headers, rows=rows, start_line=i + 1))
            i = j
        else:
            i += 1
    return tables


def _norm_header(h: str) -> str:
    return _BOLD_RE.sub("", h).strip().lower()


def _find_table(tables: List[Table], required_headers: List[str]) -> Optional[Table]:
    req = [r.lower() for r in required_headers]
    for t in tables:
        hset = {_norm_header(h) for h in t.headers}
        if all(any(r in h for h in hset) for r in req):
            return t
    return None


# --------------------------------------------------------------------------
# Value normalization helpers
# --------------------------------------------------------------------------
def normalize_valid(raw: str) -> Tuple[Optional[bool], Optional[str]]:
    """Normalize a ``valid`` cell to bool. Returns (value, warning)."""
    s = _BOLD_RE.sub("", str(raw)).strip().lower()
    truthy = {"valid", "true", "yes", "✓", "y", "1"}
    falsy = {"invalid", "false", "no", "✗", "x", "0"}
    if s in truthy:
        return True, None
    if s in falsy:
        return False, None
    # tolerate decorated forms like "valid (note)" / "✓ valid"
    if "invalid" in s:
        return False, None
    if "valid" in s:
        return True, None
    return None, f"could not normalize valid={raw!r} -> None"


def to_int(raw: str) -> Tuple[Any, Optional[str]]:
    s = _BOLD_RE.sub("", str(raw)).strip()
    try:
        return int(s), None
    except (ValueError, TypeError):
        try:
            f = float(s)
            if f.is_integer():
                return int(f), None
        except (ValueError, TypeError):
            pass
        return raw, f"could not convert to int: {raw!r}"


def to_float(raw: str) -> Tuple[Any, Optional[str]]:
    s = _BOLD_RE.sub("", str(raw)).strip()
    try:
        return float(s), None
    except (ValueError, TypeError):
        return raw, f"could not convert to float: {raw!r}"


def extract_link(cell: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (link_text, link_target) for the first markdown link in cell.

    If there is no markdown link, returns (None, cell-stripped-or-None).
    """
    m = _LINK_RE.search(cell)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    s = cell.strip()
    return None, (s or None)


def infer_stack_env(model_id: str) -> Tuple[str, str, Optional[str]]:
    """Best-effort (mmrotate_stack, env) from the compatibility table families.

    Returns (stack, env, warning). Unknown families -> ("unknown","unknown").
    """
    m = (model_id or "").lower()
    # order matters: most specific families first
    if "arsdetr" in m or "ars_detr" in m:
        return "ARS-DETR fork mmrotate 0.1.0", "ars", None
    if "lsknet" in m:
        return "mmrotate 0.3.4 (LSKNet repo / pcp-obb-soda env)", "pcp-obb-soda", None
    if "psc" in m:
        return "onedl-mmrotate 1.1.1 (PSC components)", "pcp-obb", None
    if "faa" in m:
        return "mmrotate 1.x (Phase-Tiny-OBB)", "pcp-obb", None
    if "oriented_rcnn_r50" in m:
        return "onedl-mmrotate 1.1.1", "pcp-obb", None
    return "unknown", "unknown", f"no compatibility-table family for model_id={model_id!r}"


# --------------------------------------------------------------------------
# Main parse
# --------------------------------------------------------------------------
def _build_metadata_index(meta_table: Optional[Table]) -> Dict[Any, Dict[str, str]]:
    """Index the detailed-metadata table by the leading ``#`` id."""
    idx: Dict[Any, Dict[str, str]] = {}
    if meta_table is None:
        return idx
    headers = [_norm_header(h) for h in meta_table.headers]
    for row in meta_table.rows:
        if not row:
            continue
        cells = dict(zip(headers, row))
        rid, _ = to_int(row[0])
        idx[rid] = cells
    return idx


def parse_baseline_readme(
    readme_path: str,
    pth_data_root: str,
    check_existence: bool = True,
) -> InventoryResult:
    with open(readme_path, "r", encoding="utf-8") as fh:
        text = fh.read()

    tables = extract_tables(text)
    warnings: List[str] = []

    main = _find_table(tables, ["model_id", "pth", "config", "valid"])
    if main is None:
        raise ValueError(
            "main baseline table (headers model_id/pth/config/valid) not found in readme; "
            "cannot parse — stopping."
        )
    meta = _find_table(tables, ["actual_gb", "optimizer", "scheduler", "angle"])
    if meta is None:
        warnings.append("detailed metadata table not found; gb/lr/optimizer/etc filled as unknown")
    meta_idx = _build_metadata_index(meta)

    main_headers = [_norm_header(h) for h in main.headers]

    # locate column positions in the main table by fuzzy name match
    def col(name_options: List[str]) -> Optional[int]:
        for i, h in enumerate(main_headers):
            for opt in name_options:
                if opt in h:
                    return i
        return None

    c_id = col(["#"])
    c_model = col(["model_id", "model"])
    c_dataset = col(["dataset"])
    c_split = col(["train/val", "train_val", "train/test"])
    c_epoch = col(["epoch_best", "epoch"])
    c_map = col(["map_best", "map"])
    c_valid = col(["valid"])
    c_pth = col(["pth"])
    c_log = col(["log"])
    c_config = col(["config"])
    c_source = col(["source"])

    records: List[Dict[str, Any]] = []
    for row in main.rows:
        if not row or all(c == "" for c in row):
            continue
        rec_warn: List[str] = []

        def get(ci: Optional[int]) -> str:
            return row[ci] if (ci is not None and ci < len(row)) else ""

        rid, w = to_int(get(c_id))
        if w:
            rec_warn.append(w)
        model_id = _BOLD_RE.sub("", get(c_model)).strip() or "unknown"
        dataset = get(c_dataset).strip() or "unknown"
        split = get(c_split).strip() or "unknown"

        epoch_best, w = to_int(get(c_epoch))
        if w:
            rec_warn.append(w)
        map_best, w = to_float(get(c_map))
        if w:
            rec_warn.append(w)
        valid, w = normalize_valid(get(c_valid))
        if w:
            rec_warn.append(w)

        _, pth_rel = extract_link(get(c_pth))
        _, log_rel = extract_link(get(c_log))
        _, cfg_rel = extract_link(get(c_config))
        source = get(c_source).strip() or None

        def resolve(rel: Optional[str]) -> Optional[str]:
            if not rel:
                return None
            if os.path.isabs(rel):
                return rel
            return os.path.normpath(os.path.join(pth_data_root, rel))

        pth_abs = resolve(pth_rel)
        log_abs = resolve(log_rel)
        cfg_abs = resolve(cfg_rel)

        # metadata join by id
        md = meta_idx.get(rid, {})
        if not md and meta is not None:
            rec_warn.append(f"no metadata-table row for id={rid!r}")

        def md_get(*names: str) -> Optional[str]:
            for nm in names:
                for k, v in md.items():
                    if nm in k:
                        return v
            return None

        actual_gb, w = (to_int(md_get("actual_gb")) if md_get("actual_gb") is not None else (None, None))
        if w:
            rec_warn.append(w)
        per_gpu_bs, w = (to_int(md_get("per_gpu_bs")) if md_get("per_gpu_bs") is not None else (None, None))
        if w:
            rec_warn.append(w)
        gpus, w = (to_int(md_get("gpus")) if md_get("gpus") is not None else (None, None))
        if w:
            rec_warn.append(w)
        actual_lr, w = (to_float(md_get("actual_lr")) if md_get("actual_lr") is not None else (None, None))
        if w:
            rec_warn.append(w)
        optimizer = (md_get("optimizer") or "unknown").strip()
        scheduler = (md_get("scheduler") or "unknown").strip()
        angle = (md_get("angle") or "unknown").strip()
        metric = (md_get("metric") or "unknown").strip()
        eval_interval = (md_get("eval_interval") or "unknown").strip()

        mmrotate_stack, env, w = infer_stack_env(model_id)
        if w:
            rec_warn.append(w)

        inference_ready = bool(valid is True and pth_rel and log_rel and cfg_rel)

        rec: Dict[str, Any] = {
            "id": rid,
            "model_id": model_id,
            "dataset": dataset,
            "train_val_or_trainval_test": split,
            "epoch_best": epoch_best,
            "mAP_best": map_best,
            "valid": valid,
            "pth": pth_rel,
            "pth_abs": pth_abs,
            "log": log_rel,
            "log_abs": log_abs,
            "config": cfg_rel,
            "config_abs": cfg_abs,
            "source": source,
            "mmrotate_stack": mmrotate_stack,
            "env": env,
            "actual_gb": actual_gb,
            "per_gpu_bs": per_gpu_bs,
            "gpus": gpus,
            "actual_lr": actual_lr,
            "optimizer": optimizer,
            "scheduler": scheduler,
            "angle": angle,
            "metric": metric,
            "eval_interval": eval_interval,
            "inference_ready": inference_ready,
            "pth_exists": None,
            "log_exists": None,
            "config_exists": None,
            "warnings": rec_warn,
        }

        if check_existence:
            rec["pth_exists"] = bool(pth_abs and os.path.exists(pth_abs))
            rec["log_exists"] = bool(log_abs and os.path.exists(log_abs))
            rec["config_exists"] = bool(cfg_abs and os.path.exists(cfg_abs))

        records.append(rec)

    return InventoryResult(
        records=records,
        warnings=warnings,
        source_readme=os.path.abspath(readme_path),
        pth_data_root=os.path.abspath(pth_data_root),
    )


# CSV column order for the flat exports.
CSV_COLUMNS: List[str] = [
    "id", "model_id", "dataset", "train_val_or_trainval_test",
    "epoch_best", "mAP_best", "valid",
    "pth", "pth_abs", "pth_exists",
    "log", "log_abs", "log_exists",
    "config", "config_abs", "config_exists",
    "source", "mmrotate_stack", "env",
    "actual_gb", "per_gpu_bs", "gpus", "actual_lr",
    "optimizer", "scheduler", "angle", "metric", "eval_interval",
    "inference_ready",
]
