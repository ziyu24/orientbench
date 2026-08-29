"""Compact, non-authoritative dispatch history for research_core v1.4.0."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import tempfile

import yaml


SHA256 = re.compile(r"[0-9a-f]{64}\Z")
INDEX_KEYS = {
    "epoch",
    "plan_id",
    "owner_role",
    "lifecycle",
    "result_code",
    "plan_path",
    "plan_sha256",
    "report_path",
    "summary",
}
RESULT_CODES = {
    "SUCCEEDED",
    "FAILED",
    "INCONCLUSIVE",
    "CONTESTED",
    "KILLED",
    "SUPERSEDED",
}


def _safe_relative(value: str, label: str) -> str:
    if type(value) is not str or not value or "\\" in value:
        raise ValueError(f"invalid {label}")
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts or "." in path.parts:
        raise ValueError(f"invalid {label}")
    return path.as_posix()


def _load_yaml(path: Path) -> dict:
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    if type(document) is not dict:
        raise ValueError(f"YAML mapping required: {path}")
    return document


def _atomic_yaml(path: Path, document: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, raw = tempfile.mkstemp(
        prefix=f".{path.name}-",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(raw)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(document, stream, allow_unicode=True, sort_keys=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _exclusive_yaml(path: Path, document: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        yaml.safe_dump(document, stream, allow_unicode=True, sort_keys=False)
        stream.flush()
        os.fsync(stream.fileno())
    return path


def _validate_entry(value: object) -> dict:
    if type(value) is not dict or set(value) != INDEX_KEYS:
        raise ValueError("invalid dispatch index entry")
    if type(value["epoch"]) is not int or value["epoch"] < 1:
        raise ValueError("invalid dispatch index epoch")
    if not re.fullmatch(r"[BC][0-9]{4}", str(value["plan_id"])):
        raise ValueError("invalid dispatch index plan identity")
    if value["owner_role"] != str(value["plan_id"])[0]:
        raise ValueError("invalid dispatch index owner")
    _safe_relative(value["plan_path"], "dispatch index plan path")
    _safe_relative(value["report_path"], "dispatch index report path")
    if SHA256.fullmatch(str(value["plan_sha256"])) is None:
        raise ValueError("invalid dispatch index plan SHA256")
    if type(value["lifecycle"]) is not str or not value["lifecycle"]:
        raise ValueError("invalid dispatch index lifecycle")
    if value["result_code"] not in RESULT_CODES:
        raise ValueError("invalid dispatch index result code")
    summary = value["summary"]
    if (
        type(summary) is not str
        or not summary.strip()
        or "\n" in summary
        or "\r" in summary
        or len(summary) > 240
    ):
        raise ValueError("invalid dispatch index summary")
    return value


def load_index(root: Path) -> dict:
    document = _load_yaml(Path(root) / "coordination/dispatch/INDEX.yaml")
    if (
        set(document) != {"schema_version", "entries"}
        or document["schema_version"] != 1
        or type(document["entries"]) is not list
    ):
        raise ValueError("invalid dispatch history index")
    epochs: list[int] = []
    for entry in document["entries"]:
        _validate_entry(entry)
        epochs.append(entry["epoch"])
    if epochs != sorted(epochs) or len(epochs) != len(set(epochs)):
        raise ValueError("dispatch history index epochs must be unique and ordered")
    return document


def _archive_path(root: Path, epoch: int) -> Path:
    if type(epoch) is not int or epoch < 1:
        raise ValueError("invalid dispatch archive epoch")
    return Path(root) / f"coordination/dispatch/archive/E{epoch:06d}.yaml"


def _entry(record: dict, *, result_code: str, summary: str) -> dict:
    value = {
        "epoch": record.get("epoch"),
        "plan_id": record.get("plan_id"),
        "owner_role": record.get("owner_role"),
        "lifecycle": record.get("lifecycle"),
        "result_code": result_code,
        "plan_path": record.get("plan_path"),
        "plan_sha256": record.get("plan_sha256"),
        "report_path": record.get("report_path"),
        "summary": summary.strip() if type(summary) is str else summary,
    }
    return _validate_entry(value)


def archive_record(
    root: Path,
    record: dict,
    *,
    result_code: str,
    summary: str,
) -> Path:
    root = Path(root).resolve()
    entry = _entry(record, result_code=result_code, summary=summary)
    index = load_index(root)
    if any(item["epoch"] == entry["epoch"] for item in index["entries"]):
        raise ValueError("dispatch epoch is already archived")
    if index["entries"] and entry["epoch"] <= index["entries"][-1]["epoch"]:
        raise ValueError("dispatch archive epoch is not append-only")
    path = _archive_path(root, entry["epoch"])
    _exclusive_yaml(path, record)
    try:
        updated = {
            "schema_version": 1,
            "entries": [*index["entries"], entry],
        }
        _atomic_yaml(root / "coordination/dispatch/INDEX.yaml", updated)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return path


def load_archive(root: Path, epoch: int) -> dict:
    document = _load_yaml(_archive_path(Path(root).resolve(), epoch))
    if document.get("epoch") != epoch:
        raise ValueError("dispatch archive epoch mismatch")
    return document


def update_archive(root: Path, epoch: int, record: dict) -> Path:
    root = Path(root).resolve()
    path = _archive_path(root, epoch)
    if not path.is_file() or path.is_symlink():
        raise ValueError("dispatch archive is missing")
    if record.get("epoch") != epoch:
        raise ValueError("dispatch archive epoch mismatch")
    _atomic_yaml(path, record)
    return path


def compact_view(
    root: Path,
    active: dict | None,
    *,
    recent: int = 10,
) -> dict:
    if type(recent) is not int or recent < 0 or recent > 100:
        raise ValueError("recent history limit must be between 0 and 100")
    index = load_index(Path(root).resolve())
    entries = index["entries"][-recent:] if recent else []
    return {
        "active": active,
        "recent": entries,
        "history_count": len(index["entries"]),
        "history_detail_command": "dispatch history --epoch EPOCH",
    }


def index_file_sha256(root: Path) -> str:
    path = Path(root).resolve() / "coordination/dispatch/INDEX.yaml"
    load_index(root)
    return hashlib.sha256(path.read_bytes()).hexdigest()
