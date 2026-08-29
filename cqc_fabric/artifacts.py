"""Centralized artifact manifests and rebuild closure."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import re
import tempfile
from typing import Any

import yaml

from . import FabricError


RECOVERY_METHODS = {"TRAIN", "DOWNLOAD", "DERIVE", "COPY_FROM_BACKUP"}
ARTIFACT_STATES = {"AVAILABLE", "MISSING", "DELETED", "REBUILD_REQUIRED"}
SHA = re.compile(r"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")
SHA256 = re.compile(r"[0-9a-f]{64}\Z")
MANIFEST_KEYS = {
    "schema_version",
    "artifact_id",
    "kind",
    "location",
    "size_bytes",
    "sha256",
    "provenance",
    "rebuild",
    "rebuildable",
    "status",
    "deletion_note",
}
PROVENANCE_KEYS = {
    "run_id",
    "git_sha",
    "source_sha256",
    "config_digest",
    "dataset_id",
    "dataset_version",
    "dataset_digest",
    "environment",
    "dependencies",
    "seed",
    "command",
}
REBUILD_KEYS = {
    "method",
    "steps",
    "inputs_available",
    "estimated_gpu",
    "estimated_cpu",
    "estimated_hours",
    "estimated_disk_gib",
}


def _argv(value: Any, label: str) -> list[str]:
    if (
        type(value) is not list
        or not value
        or any(type(item) is not str or not item for item in value)
    ):
        raise FabricError(f"{label} must be structured argv")
    return value


def _nonnegative(value: Any) -> bool:
    return type(value) in {int, float} and value >= 0


def validate_manifest(document: dict[str, Any]) -> dict[str, Any]:
    if (
        type(document) is not dict
        or set(document) != MANIFEST_KEYS
        or document.get("schema_version") != 1
    ):
        raise FabricError("invalid artifact manifest fields")
    if (
        type(document["artifact_id"]) is not str
        or not document["artifact_id"]
        or type(document["kind"]) is not str
        or not document["kind"]
    ):
        raise FabricError("invalid artifact identity")
    location = document["location"]
    if (
        type(location) is not dict
        or set(location) != {"node_id", "relative_path"}
        or type(location["node_id"]) is not str
        or not location["node_id"]
    ):
        raise FabricError("invalid artifact location")
    relative = PurePosixPath(str(location["relative_path"]))
    if relative.is_absolute() or ".." in relative.parts or not relative.parts:
        raise FabricError("invalid artifact relative path")
    if (
        type(document["size_bytes"]) is not int
        or document["size_bytes"] < 0
        or SHA256.fullmatch(str(document["sha256"])) is None
    ):
        raise FabricError("invalid artifact size or hash")
    provenance = document["provenance"]
    if type(provenance) is not dict or set(provenance) != PROVENANCE_KEYS:
        raise FabricError("invalid artifact provenance")
    if (
        SHA.fullmatch(str(provenance["git_sha"])) is None
        or any(
            SHA256.fullmatch(str(provenance[key])) is None
            for key in ("source_sha256", "config_digest", "dataset_digest")
        )
        or any(
            type(provenance[key]) is not str or not provenance[key].strip()
            for key in (
                "run_id",
                "dataset_id",
                "dataset_version",
                "environment",
            )
        )
        or type(provenance["seed"]) is not int
        or type(provenance["dependencies"]) is not list
        or any(type(item) is not str or not item for item in provenance["dependencies"])
    ):
        raise FabricError("invalid artifact provenance value")
    _argv(provenance["command"], "artifact command")
    rebuild = document["rebuild"]
    if type(rebuild) is not dict or set(rebuild) != REBUILD_KEYS:
        raise FabricError("invalid artifact rebuild fields")
    if (
        rebuild["method"] not in RECOVERY_METHODS
        or type(rebuild["steps"]) is not list
        or not rebuild["steps"]
    ):
        raise FabricError("invalid artifact recovery method")
    for step in rebuild["steps"]:
        _argv(step, "artifact recovery step")
    if type(rebuild["inputs_available"]) is not bool or not all(
        _nonnegative(rebuild[key])
        for key in (
            "estimated_gpu",
            "estimated_cpu",
            "estimated_hours",
            "estimated_disk_gib",
        )
    ):
        raise FabricError("invalid artifact recovery estimate")
    if document["rebuildable"] is not True:
        raise FabricError("artifact must be rebuildable")
    if not rebuild["inputs_available"]:
        raise FabricError("rebuildable artifact inputs are unavailable")
    if document["status"] not in ARTIFACT_STATES:
        raise FabricError("invalid artifact state")
    if document["deletion_note"] is not None and (
        type(document["deletion_note"]) is not str
        or not document["deletion_note"].strip()
    ):
        raise FabricError("invalid artifact deletion note")
    return document


def load_manifest(path: Path, *, manifests_root: Path) -> dict[str, Any]:
    root = Path(manifests_root).resolve(strict=True)
    candidate = Path(path)
    if (
        candidate.is_symlink()
        or not candidate.is_file()
        or not candidate.resolve(strict=True).is_relative_to(root)
    ):
        raise FabricError("artifact manifest must be a plain centralized file")
    try:
        document = yaml.safe_load(candidate.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise FabricError("cannot read artifact manifest") from error
    return validate_manifest(document)


def _atomic_yaml(path: Path, document: dict[str, Any]) -> None:
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            yaml.safe_dump(document, stream, sort_keys=False)
        os.replace(temporary_name, path)
    except BaseException:
        Path(temporary_name).unlink(missing_ok=True)
        raise


def mark_missing(path: Path, *, status: str, note: str) -> dict[str, Any]:
    if status not in {"MISSING", "DELETED", "REBUILD_REQUIRED"}:
        raise FabricError("invalid missing-artifact state")
    if type(note) is not str or not note.strip():
        raise FabricError("missing-artifact note is required")
    target = Path(path)
    try:
        document = yaml.safe_load(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError) as error:
        raise FabricError("cannot read artifact manifest") from error
    document = validate_manifest(document)
    document["status"] = status
    document["deletion_note"] = note
    _atomic_yaml(target, document)
    return validate_manifest(document)


def retention_usage(
    documents: list[dict[str, Any]], *, node_id: str
) -> dict[str, int]:
    selected = [
        validate_manifest(document)
        for document in documents
        if document.get("location", {}).get("node_id") == node_id
        and document.get("status") == "AVAILABLE"
    ]
    return {
        "count": len(selected),
        "total_bytes": sum(document["size_bytes"] for document in selected),
    }


def check_retention(
    documents: list[dict[str, Any]],
    *,
    node_id: str,
    max_count: int,
    max_total_gib: float,
) -> dict[str, int | bool]:
    if type(max_count) is not int or max_count < 0 or not _nonnegative(max_total_gib):
        raise FabricError("invalid artifact retention limit")
    usage = retention_usage(documents, node_id=node_id)
    maximum_bytes = int(max_total_gib * 1024**3)
    return {
        **usage,
        "within_limit": usage["count"] <= max_count
        and usage["total_bytes"] <= maximum_bytes,
        "max_count": max_count,
        "max_total_bytes": maximum_bytes,
    }
