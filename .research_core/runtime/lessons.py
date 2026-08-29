"""Pure-local, SHA-pinned research-lessons matching for v1.6 projects.

Shared lesson cards are operational guidance, never scientific evidence.  This
module deliberately has no Git, subprocess, network, update, or promotion path.
"""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import stat
from typing import Any

import yaml

from .storage import write_text_atomic


__all__ = [
    "load_lock",
    "context_fingerprint",
    "check",
    "record_failure",
    "update_preview",
    "apply_update",
    "promotion_preview",
    "apply_promotion",
]


_REPOSITORY = "ziyu24/cqc_research_lessons"
_CONTEXT_DIMENSIONS = {
    "task",
    "data",
    "model",
    "metrics",
    "dependencies",
    "hardware",
    "failure_signatures",
    "node",
}
_CATEGORIES = {
    "methodology",
    "data",
    "metrics",
    "implementation",
    "environment",
    "compute",
}
_CARD_FIELDS = {
    "schema_version",
    "lesson_id",
    "title",
    "category",
    "tags",
    "applies_when",
    "not_applicable_when",
    "failure_signature",
    "root_cause",
    "confidence",
    "detection",
    "prevention",
    "recovery",
    "raw_evidence_summary",
    "error_excerpt",
    "enforcement",
    "deterministic",
    "reproducible",
    "uncontested",
    "source_fingerprint",
    "created_sha",
    "revised_sha",
    "status",
}
_INDEX_ENTRY_FIELDS = {
    "lesson_id",
    "path",
    "category",
    "title",
    "tags",
    "enforcement",
    "status",
}
_LESSON_ID = re.compile(r"L[0-9]{6}\Z")
_GIT_SHA = re.compile(r"[0-9a-f]{40}\Z")
_HEX_64 = re.compile(r"[0-9a-f]{64}\Z")
_MAX_LOCK_BYTES = 4096
_MAX_APPLIED_BYTES = 8192
_MAX_INDEX_BYTES = 256 * 1024
_MAX_CARD_BYTES = 64 * 1024
_MAX_INDEX_ENTRIES = 4096
_MAX_SELECTED_CARDS = 8
_MAX_TAGS = 64
_MAX_LIST_ITEMS = 128
_MAX_STRING_BYTES = 4096
_MAX_CONTEXT_BYTES = 64 * 1024
_MAX_CONTEXT_NODES = 4096
_MATCHER_VERSION = 1


class _StrictSafeLoader(yaml.SafeLoader):
    def compose_node(self, parent: object, index: object) -> yaml.Node:
        if self.check_event(yaml.AliasEvent):
            event = self.get_event()
            raise yaml.constructor.ConstructorError(
                None,
                None,
                "YAML aliases are not allowed",
                event.start_mark,
            )
        return super().compose_node(parent, index)

    def construct_mapping(
        self, node: yaml.MappingNode, deep: bool = False
    ) -> dict[object, object]:
        self.flatten_mapping(node)
        result: dict[object, object] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in result
            except TypeError as error:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    "found an unhashable mapping key",
                    key_node.start_mark,
                ) from error
            if duplicate:
                raise yaml.constructor.ConstructorError(
                    "while constructing a mapping",
                    node.start_mark,
                    f"found duplicate YAML key {key!r}",
                    key_node.start_mark,
                )
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _require_plain_mapping(value: object, label: str) -> dict[str, Any]:
    if type(value) is not dict or any(type(key) is not str for key in value):
        raise ValueError(f"{label} must be a mapping with string keys")
    return value


def _is_schema_one(value: object) -> bool:
    return type(value) is int and value == 1


def _is_current_matcher_version(value: object) -> bool:
    return type(value) is int and value == _MATCHER_VERSION


def _is_linklike(path: Path) -> bool:
    try:
        if path.is_symlink():
            return True
        is_junction = getattr(path, "is_junction", None)
        if is_junction is not None and is_junction():
            return True
        attributes = getattr(path.stat(follow_symlinks=False), "st_file_attributes", 0)
        return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    except FileNotFoundError:
        return False
    except OSError:
        return True


def _require_plain_path(path: Path, *, label: str, directory: bool) -> None:
    if _is_linklike(path):
        raise ValueError(f"{label} must not be a symlink, junction, or reparse point")
    try:
        mode = path.stat(follow_symlinks=False).st_mode
    except OSError as error:
        raise FileNotFoundError(f"{label} is missing or unreadable: {path}") from error
    expected = stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode)
    if not expected:
        kind = "directory" if directory else "file"
        raise ValueError(f"{label} must be a plain {kind}")


def _require_no_follow_path(
    root: Path,
    path: Path,
    *,
    label: str,
    directory: bool,
) -> None:
    root = Path(root).absolute()
    path = Path(path).absolute()
    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{label} escapes its controlled root") from error
    if not relative.parts:
        raise ValueError(f"{label} must be below its controlled root")
    _require_plain_path(root, label=f"{label} root", directory=True)
    current = root
    for position, part in enumerate(relative.parts):
        current /= part
        is_leaf = position == len(relative.parts) - 1
        _require_plain_path(
            current,
            label=f"{label} component",
            directory=directory if is_leaf else True,
        )
    resolved_root = root.resolve()
    resolved = path.resolve()
    if resolved == resolved_root or resolved_root not in resolved.parents:
        raise ValueError(f"{label} resolves outside its controlled root")


def _project_lessons_file(root: Path, filename: str, *, label: str) -> Path:
    if filename not in {"LOCK.yaml", "APPLIED.yaml"}:
        raise ValueError("unsupported project lessons file")
    project_root = Path(root).absolute()
    path = project_root / "coordination" / "lessons" / filename
    _require_no_follow_path(
        project_root,
        path,
        label=label,
        directory=False,
    )
    return path


def _read_bounded_yaml(path: Path, *, max_bytes: int, label: str) -> dict[str, Any]:
    path = Path(path)
    if _is_linklike(path) or not path.is_file():
        raise FileNotFoundError(f"{label} is not a plain local file: {path}")
    if path.stat().st_size > max_bytes:
        raise ValueError(f"{label} exceeds {max_bytes} bytes")
    text = path.read_text(encoding="utf-8")
    if len(text.encode("utf-8")) > max_bytes:
        raise ValueError(f"{label} exceeds {max_bytes} bytes")
    try:
        document = yaml.load(text, Loader=_StrictSafeLoader)
    except RecursionError as error:
        raise ValueError(f"invalid {label} YAML: parser recursion limit exceeded") from error
    except yaml.YAMLError as error:
        detail = getattr(error, "problem", None) or "parser error"
        raise ValueError(f"invalid {label} YAML: {detail}") from error
    return _require_plain_mapping(document, label)


def _require_string(value: object, label: str, *, max_bytes: int = _MAX_STRING_BYTES) -> str:
    if type(value) is not str or not value.strip():
        raise ValueError(f"{label} must be a non-empty string")
    if len(value.encode("utf-8")) > max_bytes:
        raise ValueError(f"{label} is too large")
    return value


def _require_string_list(
    value: object,
    label: str,
    *,
    max_items: int = _MAX_LIST_ITEMS,
    allow_empty: bool = True,
) -> list[str]:
    if type(value) is not list or len(value) > max_items:
        raise ValueError(f"{label} must be a bounded string list")
    if not allow_empty and not value:
        raise ValueError(f"{label} must not be empty")
    result: list[str] = []
    for index, item in enumerate(value):
        result.append(_require_string(item, f"{label}[{index}]", max_bytes=512))
    return result


def _normalize_token(value: str) -> str:
    return " ".join(value.strip().casefold().split())


def _validated_tags(value: object, label: str) -> tuple[str, ...]:
    tags = _require_string_list(
        value, label, max_items=_MAX_TAGS, allow_empty=False
    )
    normalized = tuple(_normalize_token(tag) for tag in tags)
    if any(not tag for tag in normalized) or len(set(normalized)) != len(normalized):
        raise ValueError(f"{label} contains an empty or duplicate tag")
    return normalized


def load_lock(root: Path) -> dict[str, Any]:
    """Load and validate the project's concrete lessons lock."""

    path = _project_lessons_file(
        Path(root), "LOCK.yaml", label="project lessons LOCK path"
    )
    lock = _read_bounded_yaml(path, max_bytes=_MAX_LOCK_BYTES, label="lessons lock")
    required = {"schema_version", "repository", "schema", "git_sha"}
    if set(lock) != required:
        raise ValueError("lessons lock fields do not match schema 1")
    if not _is_schema_one(lock["schema_version"]) or not _is_schema_one(
        lock["schema"]
    ):
        raise ValueError("lessons lock schema must be 1")
    if lock["repository"] != _REPOSITORY:
        raise ValueError("lessons lock repository does not match the contract")
    git_sha = lock["git_sha"]
    if type(git_sha) is not str or _GIT_SHA.fullmatch(git_sha) is None:
        raise ValueError("lessons lock git_sha must be 40 lowercase hexadecimal characters")
    return dict(lock)


def _require_lock_unchanged(root: Path, initial_lock: dict[str, Any]) -> None:
    if load_lock(root) != initial_lock:
        raise ValueError("lessons lock changed during check")


def _validate_context_value(value: object, *, depth: int, budget: list[int]) -> None:
    budget[0] += 1
    if budget[0] > _MAX_CONTEXT_NODES or depth > 16:
        raise ValueError("lessons context is too complex")
    if value is None or type(value) in {str, bool, int}:
        if type(value) is str and len(value.encode("utf-8")) > _MAX_STRING_BYTES:
            raise ValueError("lessons context string is too large")
        return
    if type(value) is float:
        if not math.isfinite(value):
            raise ValueError("lessons context numbers must be finite")
        return
    if type(value) is list:
        for item in value:
            _validate_context_value(item, depth=depth + 1, budget=budget)
        return
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or not key or len(key.encode("utf-8")) > 256:
                raise ValueError("lessons context keys must be bounded non-empty strings")
            _validate_context_value(item, depth=depth + 1, budget=budget)
        return
    raise TypeError("lessons context must contain only canonical JSON types")


def _canonical_context(context: dict[str, Any]) -> bytes:
    if type(context) is not dict:
        raise TypeError("lessons context must be a mapping")
    _validate_context_value(context, depth=0, budget=[0])
    try:
        payload = json.dumps(
            context,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    except (TypeError, ValueError) as error:
        raise ValueError("lessons context is not canonical JSON") from error
    if len(payload) > _MAX_CONTEXT_BYTES:
        raise ValueError("lessons context exceeds its size bound")
    return payload


def context_fingerprint(context: dict[str, Any]) -> str:
    """Hash the complete, canonical JSON context with SHA-256."""

    return hashlib.sha256(_canonical_context(context)).hexdigest()


def _scalar_token(value: object) -> str | None:
    if type(value) is str:
        return _normalize_token(value)
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) in {int, float}:
        return json.dumps(value, allow_nan=False, separators=(",", ":"))
    return None


def _collect_context_tokens(value: object, tokens: set[str], path: tuple[str, ...]) -> None:
    scalar = _scalar_token(value)
    if scalar is not None:
        if scalar:
            tokens.add(scalar)
            if path:
                tokens.add(f"{_normalize_token(path[-1])}:{scalar}")
                tokens.add(f"{'.'.join(_normalize_token(part) for part in path)}:{scalar}")
        return
    if type(value) is list:
        for item in value:
            _collect_context_tokens(item, tokens, path)
        return
    if type(value) is dict:
        for key, item in value.items():
            tokens.add(_normalize_token(key))
            _collect_context_tokens(item, tokens, (*path, key))


def _context_tokens(context: dict[str, Any]) -> set[str]:
    tokens: set[str] = set()
    for dimension in sorted(_CONTEXT_DIMENSIONS & set(context)):
        _collect_context_tokens(context[dimension], tokens, (dimension,))
    return tokens


def _validate_index(index: dict[str, Any]) -> list[dict[str, Any]]:
    if set(index) != {"schema_version", "entries"} or not _is_schema_one(
        index["schema_version"]
    ):
        raise ValueError("lessons INDEX fields do not match schema 1")
    entries = index["entries"]
    if type(entries) is not list or len(entries) > _MAX_INDEX_ENTRIES:
        raise ValueError("lessons INDEX entries must be a bounded list")
    seen_ids: set[str] = set()
    seen_paths: set[str] = set()
    result: list[dict[str, Any]] = []
    for position, raw in enumerate(entries):
        entry = _require_plain_mapping(raw, f"INDEX entry {position}")
        if set(entry) != _INDEX_ENTRY_FIELDS:
            raise ValueError(f"INDEX entry {position} fields do not match schema 1")
        lesson_id = entry["lesson_id"]
        if type(lesson_id) is not str or _LESSON_ID.fullmatch(lesson_id) is None:
            raise ValueError(f"INDEX entry {position} has an invalid lesson_id")
        category = entry["category"]
        if category not in _CATEGORIES:
            raise ValueError(f"INDEX entry {position} has an invalid category")
        _require_string(entry["title"], f"INDEX entry {position} title", max_bytes=512)
        tags = _validated_tags(entry["tags"], f"INDEX entry {position} tags")
        if entry["enforcement"] not in {"BLOCK", "WARN"}:
            raise ValueError(f"INDEX entry {position} has invalid enforcement")
        if entry["status"] not in {"ACTIVE", "CONTESTED", "SUPERSEDED"}:
            raise ValueError(f"INDEX entry {position} has invalid status")
        relative = _validate_card_relative_path(entry["path"], lesson_id, category)
        normalized_path = relative.as_posix()
        if lesson_id in seen_ids or normalized_path in seen_paths:
            raise ValueError("lessons INDEX contains duplicate ids or paths")
        seen_ids.add(lesson_id)
        seen_paths.add(normalized_path)
        item = dict(entry)
        item["_tags"] = tags
        item["_relative"] = relative
        result.append(item)
    return result


def _validate_card_relative_path(value: object, lesson_id: str, category: str) -> PurePosixPath:
    if type(value) is not str or "\\" in value:
        raise ValueError("lesson card path must be a POSIX relative path")
    relative = PurePosixPath(value)
    expected = PurePosixPath("cards", category, f"{lesson_id}.yaml")
    if relative.is_absolute() or ".." in relative.parts or relative != expected:
        raise ValueError("lesson card path escapes or violates the canonical layout")
    return relative


def _validate_card(card: dict[str, Any], entry: dict[str, Any]) -> dict[str, Any]:
    from .lessons_repository import validate_card_data

    plain_entry = {key: value for key, value in entry.items() if not key.startswith("_")}
    validate_card_data(card, plain_entry)
    return card


def _safe_card_path(checkout: Path, relative: PurePosixPath) -> Path:
    path = checkout.joinpath(*relative.parts)
    _require_no_follow_path(
        checkout,
        path,
        label="lesson card path",
        directory=False,
    )
    return path


def _result_item(
    lesson_id: str,
    git_sha: str,
    applicability: str,
    enforcement: str,
) -> dict[str, Any]:
    return {
        "lesson_id": lesson_id,
        "lessons_git_sha": git_sha,
        "applicability": applicability,
        "enforcement": enforcement,
        "scientific_evidence": False,
    }


def _validate_cached_result(value: dict[str, Any], git_sha: str, fingerprint: str) -> None:
    required = {
        "schema_version",
        "matcher_version",
        "lessons_git_sha",
        "context_fingerprint",
        "scientific_evidence",
        "applications",
        "blocks",
        "warnings",
        "unknowns",
    }
    if set(value) != required or not _is_schema_one(value["schema_version"]):
        raise ValueError("APPLIED cache fields do not match schema 1")
    if not _is_current_matcher_version(value["matcher_version"]):
        raise ValueError(
            f"APPLIED cache matcher_version must be {_MATCHER_VERSION}"
        )
    if value["lessons_git_sha"] != git_sha or value["context_fingerprint"] != fingerprint:
        raise ValueError("APPLIED cache key changed while loading")
    if value["scientific_evidence"] is not False:
        raise ValueError("lesson cards cannot be scientific evidence")
    item_fields = {
        "lesson_id",
        "lessons_git_sha",
        "applicability",
        "enforcement",
        "scientific_evidence",
    }
    validated: dict[str, list[dict[str, Any]]] = {}
    for field in ("applications", "blocks", "warnings", "unknowns"):
        items = value[field]
        if type(items) is not list or len(items) > _MAX_SELECTED_CARDS:
            raise ValueError("APPLIED cache contains an invalid bounded list")
        seen_ids: set[str] = set()
        for item in items:
            if type(item) is not dict or set(item) != item_fields:
                raise ValueError("APPLIED cache contains an invalid item")
            lesson_id = item["lesson_id"]
            if type(lesson_id) is not str or _LESSON_ID.fullmatch(lesson_id) is None:
                raise ValueError("APPLIED cache contains an invalid lesson_id")
            if lesson_id in seen_ids:
                raise ValueError("APPLIED cache contains a duplicate lesson_id")
            seen_ids.add(lesson_id)
            if (
                type(item["lessons_git_sha"]) is not str
                or item["lessons_git_sha"] != git_sha
                or item["scientific_evidence"] is not False
            ):
                raise ValueError("APPLIED cache item is not pinned or evidence-safe")
            if type(item["applicability"]) is not str or item["applicability"] not in {
                "APPLY",
                "NOT_APPLICABLE",
                "UNKNOWN",
            }:
                raise ValueError("APPLIED cache item has invalid applicability")
            if type(item["enforcement"]) is not str or item["enforcement"] not in {
                "BLOCK",
                "WARN",
                "UNKNOWN",
            }:
                raise ValueError("APPLIED cache item has invalid enforcement")
        validated[field] = items

    applications = validated["applications"]
    for item in applications:
        applicability = item["applicability"]
        enforcement = item["enforcement"]
        if applicability in {"APPLY", "NOT_APPLICABLE"}:
            if enforcement not in {"BLOCK", "WARN"}:
                raise ValueError("APPLIED cache application has invalid enforcement")
        elif enforcement != "UNKNOWN":
            raise ValueError("APPLIED cache UNKNOWN application must use UNKNOWN enforcement")
    expected = {
        "blocks": [
            item
            for item in applications
            if item["applicability"] == "APPLY"
            and item["enforcement"] == "BLOCK"
        ],
        "warnings": [
            item
            for item in applications
            if item["applicability"] == "APPLY"
            and item["enforcement"] == "WARN"
        ],
        "unknowns": [
            item
            for item in applications
            if item["applicability"] == "UNKNOWN"
            and item["enforcement"] == "UNKNOWN"
        ],
    }
    for field, derived in expected.items():
        if validated[field] != derived:
            raise ValueError(f"APPLIED cache {field} is not exactly derived from applications")


def _load_cached_result(path: Path, git_sha: str, fingerprint: str) -> dict[str, Any] | None:
    if not path.exists():
        return None
    applied = _read_bounded_yaml(
        path, max_bytes=_MAX_APPLIED_BYTES, label="lessons APPLIED cache"
    )
    if (
        applied.get("lessons_git_sha") != git_sha
        or applied.get("context_fingerprint") != fingerprint
    ):
        return None
    if not _is_current_matcher_version(applied.get("matcher_version")):
        return None
    _validate_cached_result(applied, git_sha, fingerprint)
    return applied


def _write_applied(path: Path, result: dict[str, Any]) -> None:
    text = yaml.safe_dump(
        result,
        allow_unicode=True,
        default_flow_style=False,
        sort_keys=True,
    )
    if len(text.encode("utf-8")) > _MAX_APPLIED_BYTES:
        raise ValueError("APPLIED cache exceeds its size bound")
    write_text_atomic(path, text, overwrite=True)


def check(root: Path, *, context: dict[str, Any], cache_root: Path) -> dict[str, Any]:
    """Match at most eight cards from the exact local SHA checkout and cache it."""

    root = Path(root).absolute()
    lock = load_lock(root)
    git_sha = lock["git_sha"]
    fingerprint = context_fingerprint(context)
    applied_path = _project_lessons_file(
        root, "APPLIED.yaml", label="project lessons APPLIED path"
    )
    cached = _load_cached_result(applied_path, git_sha, fingerprint)
    if cached is not None:
        _require_lock_unchanged(root, lock)
        return cached

    cache_root = Path(cache_root).absolute()
    _require_plain_path(
        cache_root,
        label="controlled local lessons cache root",
        directory=True,
    )
    checkout = cache_root / git_sha
    _require_no_follow_path(
        cache_root,
        checkout,
        label="pinned lessons checkout",
        directory=True,
    )

    index_path = checkout / "INDEX.yaml"
    _require_no_follow_path(
        checkout,
        index_path,
        label="lessons INDEX path",
        directory=False,
    )
    index = _read_bounded_yaml(
        index_path, max_bytes=_MAX_INDEX_BYTES, label="lessons INDEX"
    )
    entries = _validate_index(index)
    tokens = _context_tokens(context)
    ranked: list[tuple[int, str, dict[str, Any]]] = []
    for entry in entries:
        if entry["status"] == "SUPERSEDED":
            continue
        score = len(set(entry["_tags"]) & tokens)
        if score:
            ranked.append((-score, entry["lesson_id"], entry))
    ranked.sort(key=lambda item: (item[0], item[1]))

    applications: list[dict[str, Any]] = []
    blocks: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    unknowns: list[dict[str, Any]] = []
    for _, _, entry in ranked[:_MAX_SELECTED_CARDS]:
        card_path = _safe_card_path(checkout, entry["_relative"])
        card = _validate_card(
            _read_bounded_yaml(
                card_path,
                max_bytes=_MAX_CARD_BYTES,
                label=f"lesson card {entry['lesson_id']}",
            ),
            entry,
        )
        applies = set(_normalize_token(item) for item in card["applies_when"])
        excludes = set(
            _normalize_token(item) for item in card["not_applicable_when"]
        )
        if excludes & tokens:
            applicability = "NOT_APPLICABLE"
        elif applies and applies.issubset(tokens):
            applicability = "APPLY"
        else:
            applicability = "UNKNOWN"

        can_block = (
            card["enforcement"] == "BLOCK"
            and card["status"] == "ACTIVE"
            and card["deterministic"] is True
            and card["reproducible"] is True
            and card["uncontested"] is True
        )
        effective = "BLOCK" if can_block else "WARN"
        if applicability == "UNKNOWN":
            effective = "UNKNOWN"
        item = _result_item(entry["lesson_id"], git_sha, applicability, effective)
        applications.append(item)
        if applicability == "APPLY":
            (blocks if effective == "BLOCK" else warnings).append(dict(item))
        elif applicability == "UNKNOWN":
            unknowns.append(dict(item))

    result = {
        "schema_version": 1,
        "matcher_version": _MATCHER_VERSION,
        "lessons_git_sha": git_sha,
        "context_fingerprint": fingerprint,
        "scientific_evidence": False,
        "applications": applications,
        "blocks": blocks,
        "warnings": warnings,
        "unknowns": unknowns,
    }
    _validate_cached_result(result, git_sha, fingerprint)
    _require_lock_unchanged(root, lock)
    applied_path = _project_lessons_file(
        root, "APPLIED.yaml", label="project lessons APPLIED path"
    )
    _write_applied(applied_path, result)
    _require_lock_unchanged(root, lock)
    return result


def _workflows():
    from . import lessons_workflows

    return lessons_workflows


def _read_input_mapping(
    path: Path, *, label: str, max_bytes: int = 64 * 1024
) -> dict[str, Any]:
    return _workflows().read_input_mapping(path, label=label, max_bytes=max_bytes)


def record_failure(root: Path, request: dict[str, Any]) -> Path:
    return _workflows().record_failure(root, request)


def update_preview(
    root: Path, *, candidate_checkout: Path, explicit_user_request: bool
) -> Path:
    return _workflows().update_preview(
        root,
        candidate_checkout=candidate_checkout,
        explicit_user_request=explicit_user_request,
    )


def apply_update(
    root: Path, *, preview_path: Path, explicit_user_request: bool
) -> Path:
    return _workflows().apply_update(
        root,
        preview_path=preview_path,
        explicit_user_request=explicit_user_request,
    )


def promotion_preview(root: Path, *, failure_id: str) -> Path:
    return _workflows().promotion_preview(root, failure_id=failure_id)


def apply_promotion(
    root: Path,
    *,
    preview_path: Path,
    shared_checkout: Path,
    explicit_user_request: bool,
) -> Path:
    return _workflows().apply_promotion(
        root,
        preview_path=preview_path,
        shared_checkout=shared_checkout,
        explicit_user_request=explicit_user_request,
    )
