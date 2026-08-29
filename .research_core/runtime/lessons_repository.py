"""Canonical, local-only validation for cqc_research_lessons checkouts."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import stat
from typing import Any

from .lessons import (
    _GIT_SHA,
    _is_linklike,
    _is_schema_one,
    _read_bounded_yaml,
    _require_no_follow_path,
    _require_plain_mapping,
)


CATEGORIES = {"methodology", "data", "metrics", "implementation", "environment", "compute"}
CARD_FIELDS = [
    "schema_version", "lesson_id", "title", "category", "tags", "applies_when",
    "not_applicable_when", "failure_signature", "root_cause", "confidence",
    "detection", "prevention", "recovery", "raw_evidence_summary", "error_excerpt",
    "enforcement", "deterministic", "reproducible", "uncontested",
    "source_fingerprint", "created_sha", "revised_sha", "status",
]
INDEX_ENTRY_FIELDS = ["lesson_id", "path", "category", "title", "tags", "enforcement", "status"]
TEXT_LIMITS = {
    "title": 200, "tag": 64, "condition": 512, "failure_signature": 512,
    "root_cause": 2048, "action": 512, "raw_evidence_summary": 2048,
    "error_excerpt_line": 512, "source_fingerprint": 80,
}
LIST_LIMITS = {
    "tags": 16, "applies_when": 16, "not_applicable_when": 16,
    "failure_signature": 16, "detection": 16, "prevention": 16,
    "recovery": 16, "error_excerpt_lines": 20,
}
CANONICAL_SCHEMA = {
    "schema_version": 1,
    "card": {
        "additional_fields": False,
        "fields": CARD_FIELDS,
        "categories": ["methodology", "data", "metrics", "implementation", "environment", "compute"],
        "enforcement": ["BLOCK", "WARN"],
        "status": ["ACTIVE", "CONTESTED", "SUPERSEDED"],
        "confidence": ["LOW", "MEDIUM", "HIGH"],
        "text_limits_bytes": TEXT_LIMITS,
        "list_limits": LIST_LIMITS,
    },
    "index": {
        "additional_fields": False,
        "fields": ["schema_version", "entries"],
        "entry_fields": INDEX_ENTRY_FIELDS,
    },
}
LESSON_ID = re.compile(r"L[0-9]{6}\Z")
SOURCE_FINGERPRINT = re.compile(r"sha256:[0-9a-f]{64}\Z")
SAFE_NETWORK_URL = re.compile(
    r"(?<!\w)(?:https?://|//)(?:[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?\."
    r"[A-Za-z]{2,})(?::[0-9]{1,5})?(?:[/?#][^\s]*)?",
    re.IGNORECASE,
)
FILE_URI = re.compile(r"(?<!\w)file:(?:/{1,3}|\\)", re.IGNORECASE)
WINDOWS_ABSOLUTE = re.compile(r"(?<!\w)[A-Za-z]:[\\/]")
POSIX_ABSOLUTE = re.compile(r"(?<!\w)/(?![/\s])")
PARENT_TRAVERSAL = re.compile(r"(?<!\w)\.\.[\\/]")
UNC_PATH = re.compile(r"\\\\[^\\\s]+[\\/]")
MAX_YAML_BYTES = 65536
MAX_INDEX_ENTRIES = 10000


def matches_creation_token(token: dict[str, Any]) -> bool:
    path = token["path"]
    try:
        metadata = os.lstat(path)
        identity = (metadata.st_dev, metadata.st_ino, metadata.st_mode)
        if not stat.S_ISREG(metadata.st_mode) or identity != token["identity"]:
            return False
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    except OSError:
        return False
    try:
        opened = os.fstat(descriptor)
        if (opened.st_dev, opened.st_ino, opened.st_mode) != token["identity"]:
            return False
        chunks, remaining = [], len(token["bytes"]) + 1
        while remaining:
            chunk = os.read(descriptor, min(65536, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        content = b"".join(chunks)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    try:
        final = os.lstat(path)
    except OSError:
        return False
    return (
        (after.st_dev, after.st_ino, after.st_mode) == token["identity"]
        and (final.st_dev, final.st_ino, final.st_mode) == token["identity"]
        and content == token["bytes"]
        and hashlib.sha256(content).hexdigest() == token["digest"]
    )


def _plain_directory(path: Path, label: str) -> Path:
    try:
        metadata = os.lstat(path)
    except OSError as error:
        raise ValueError(f"{label} is unavailable") from error
    if _is_linklike(path) or not stat.S_ISDIR(metadata.st_mode):
        raise ValueError(f"{label} must not be a link, junction, or reparse point")
    return path


def _plain_text(path: Path, label: str) -> str:
    try:
        before = os.lstat(path)
        if (_is_linklike(path) or not stat.S_ISREG(before.st_mode)
                or before.st_size > 4096):
            raise ValueError(f"{label} must be a bounded plain file")
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_BINARY", 0))
    except OSError as error:
        raise ValueError(f"{label} is unavailable") from error
    try:
        opened = os.fstat(descriptor)
        content = os.read(descriptor, 4097)
        after = os.fstat(descriptor)
    finally:
        os.close(descriptor)
    final = os.lstat(path)
    identities = {
        (item.st_dev, item.st_ino, item.st_mode)
        for item in (before, opened, after, final)
    }
    if len(identities) != 1 or len(content) > 4096:
        raise ValueError(f"{label} changed while it was read")
    try:
        return content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{label} must be UTF-8 text") from error


def _same_path(left: Path, right: Path) -> bool:
    return os.path.normcase(os.path.abspath(left)) == os.path.normcase(os.path.abspath(right))


def recovery_git_dir(root: Path) -> Path:
    root = _plain_directory(Path(root).absolute(), "recovery repository root")
    marker = root / ".git"
    if _is_linklike(marker):
        raise ValueError("recovery gitdir marker must not be a link, junction, or reparse point")
    try:
        metadata = os.lstat(marker)
    except OSError as error:
        raise ValueError("recovery gitdir marker is unavailable") from error
    if stat.S_ISDIR(metadata.st_mode):
        return _plain_directory(marker, "recovery gitdir")
    if not stat.S_ISREG(metadata.st_mode):
        raise ValueError("recovery gitdir marker must be a directory or linked-worktree file")
    pointer = _plain_text(marker, "linked-worktree gitdir marker")
    match = re.fullmatch(r"gitdir: ([^\r\n]+)\r?\n?", pointer)
    if match is None:
        raise ValueError("linked-worktree gitdir marker is invalid")
    supplied = Path(match.group(1))
    if not supplied.is_absolute():
        if ".." in supplied.parts:
            raise ValueError("linked-worktree gitdir escapes its repository")
        candidate = Path(os.path.abspath(root / supplied))
        try:
            candidate.relative_to(root)
        except ValueError as error:
            raise ValueError("linked-worktree gitdir escapes its repository") from error
        current = root
        for part in candidate.relative_to(root).parts:
            current /= part
            _plain_directory(current, "linked-worktree gitdir")
        return candidate

    candidate = _plain_directory(
        Path(os.path.abspath(supplied)), "absolute linked-worktree gitdir"
    )
    if candidate.parent.name != "worktrees":
        raise ValueError("absolute gitdir is not a canonical linked-worktree path")
    common = _plain_directory(candidate.parent.parent, "linked-worktree common gitdir")
    _plain_directory(candidate.parent, "linked-worktree metadata root")
    commondir = _plain_text(candidate / "commondir", "linked-worktree commondir").strip()
    if Path(commondir).is_absolute() or _same_path(candidate / commondir, common) is False:
        raise ValueError("linked-worktree commondir binding is invalid")
    backpointer = _plain_text(candidate / "gitdir", "linked-worktree backpointer").strip()
    if not _same_path(Path(backpointer), marker):
        raise ValueError("absolute linked-worktree gitdir backpointer is invalid")
    return candidate


def retain_recovery(
    git_dir: Path,
    token: dict[str, Any],
    matcher=matches_creation_token,
) -> dict[str, Any]:
    git_dir = _plain_directory(Path(git_dir), "recovery gitdir")
    vault = git_dir / "cqc-lessons-recovery"
    try:
        os.mkdir(vault)
    except FileExistsError:
        pass
    _plain_directory(vault, "lessons recovery vault")
    while True:
        recovery_id = secrets.token_hex(16)
        record = vault / recovery_id
        try:
            os.mkdir(record)
            break
        except FileExistsError:
            continue
    _plain_directory(record, "lessons recovery record")
    payload, proof = record / "payload", record / "proof"
    try:
        os.replace(token["path"], payload)
    except FileNotFoundError:
        return {"recovery_id": recovery_id, "owned": None, "restored": True}
    except BaseException as error:
        raise ValueError(f"recovery retained as {recovery_id}") from error
    try:
        os.link(payload, proof, follow_symlinks=False)
    except BaseException as error:
        raise ValueError(f"recovery retained as {recovery_id}") from error
    proof_token = dict(token)
    proof_token["path"] = proof
    owned = matcher(proof_token)
    restored = owned
    if not owned:
        try:
            os.link(payload, token["path"], follow_symlinks=False)
            restored = True
        except FileExistsError:
            restored = False
        except BaseException as error:
            raise ValueError(f"recovery retained as {recovery_id}") from error
    return {"recovery_id": recovery_id, "owned": owned, "restored": restored}


def _exact_equal(expected: object, actual: object) -> bool:
    if type(actual) is not type(expected):
        return False
    if type(expected) is dict:
        expected_mapping = expected
        actual_mapping = actual
        if len(actual_mapping) != len(expected_mapping):
            return False
        return all(
            key in actual_mapping
            and type(key) is str
            and _exact_equal(value, actual_mapping[key])
            for key, value in expected_mapping.items()
        )
    if type(expected) is list:
        return len(actual) == len(expected) and all(
            _exact_equal(expected_item, actual_item)
            for expected_item, actual_item in zip(expected, actual)
        )
    return actual == expected


def unsafe_path_text(value: str) -> bool:
    candidate = value.strip()
    without_urls = SAFE_NETWORK_URL.sub("", candidate)
    return bool(
        FILE_URI.search(candidate)
        or without_urls.startswith("\\")
        or WINDOWS_ABSOLUTE.search(without_urls)
        or POSIX_ABSOLUTE.search(without_urls)
        or PARENT_TRAVERSAL.search(without_urls)
        or UNC_PATH.search(without_urls)
    )


def _text(value: object, label: str, limit: int, *, allow_empty: bool = False) -> str:
    if type(value) is not str or (not allow_empty and not value.strip()):
        raise ValueError(f"{label} must be bounded text")
    if len(value.encode("utf-8")) > limit:
        raise ValueError(f"{label} exceeds its canonical limit")
    if unsafe_path_text(value):
        raise ValueError(f"{label} contains an unsafe path")
    return value


def _text_list(
    value: object,
    label: str,
    maximum_items: int,
    maximum_bytes: int,
    *,
    allow_empty: bool = False,
) -> list[str]:
    if type(value) is not list or len(value) > maximum_items or (not allow_empty and not value):
        raise ValueError(f"{label} must be a canonical bounded list")
    return [_text(item, label, maximum_bytes) for item in value]


def validate_card_data(card: dict[str, Any], entry: dict[str, Any] | None = None) -> dict[str, Any]:
    card = _require_plain_mapping(card, "lesson card")
    if set(card) != set(CARD_FIELDS) or not _is_schema_one(card.get("schema_version")):
        raise ValueError("lesson card fields do not match canonical schema 1")
    lesson_id = _text(card["lesson_id"], "lesson_id", 7)
    if LESSON_ID.fullmatch(lesson_id) is None:
        raise ValueError("lesson_id is not canonical")
    _text(card["title"], "title", TEXT_LIMITS["title"])
    _text(card["category"], "category", 32)
    if card["category"] not in CATEGORIES:
        raise ValueError("lesson category is not canonical")
    _text_list(card["tags"], "tags", LIST_LIMITS["tags"], TEXT_LIMITS["tag"])
    for field in ("applies_when", "not_applicable_when"):
        _text_list(card[field], field, LIST_LIMITS[field], TEXT_LIMITS["condition"])
    _text_list(
        card["failure_signature"], "failure_signature",
        LIST_LIMITS["failure_signature"], TEXT_LIMITS["failure_signature"],
    )
    _text(card["root_cause"], "root_cause", TEXT_LIMITS["root_cause"])
    if card["confidence"] not in {"LOW", "MEDIUM", "HIGH"}:
        raise ValueError("lesson confidence is not canonical")
    for field in ("detection", "prevention", "recovery"):
        _text_list(card[field], field, LIST_LIMITS[field], TEXT_LIMITS["action"])
    _text(card["raw_evidence_summary"], "raw_evidence_summary",
          TEXT_LIMITS["raw_evidence_summary"], allow_empty=True)
    excerpts = _text_list(
        card["error_excerpt"], "error_excerpt", LIST_LIMITS["error_excerpt_lines"],
        TEXT_LIMITS["error_excerpt_line"], allow_empty=True,
    )
    if sum(item.count("\n") + 1 for item in excerpts) > LIST_LIMITS["error_excerpt_lines"]:
        raise ValueError("error_excerpt exceeds its canonical line limit")
    if card["enforcement"] not in {"BLOCK", "WARN"}:
        raise ValueError("lesson enforcement is not canonical")
    for field in ("deterministic", "reproducible", "uncontested"):
        if type(card[field]) is not bool:
            raise ValueError(f"lesson {field} must be boolean")
    fingerprint = _text(
        card["source_fingerprint"], "source_fingerprint", TEXT_LIMITS["source_fingerprint"]
    )
    if SOURCE_FINGERPRINT.fullmatch(fingerprint) is None:
        raise ValueError("source_fingerprint is not canonical")
    for field in ("created_sha", "revised_sha"):
        sha = _text(card[field], field, 40)
        if _GIT_SHA.fullmatch(sha) is None:
            raise ValueError(f"{field} is not canonical")
    if card["status"] not in {"ACTIVE", "CONTESTED", "SUPERSEDED"}:
        raise ValueError("lesson status is not canonical")
    if card["enforcement"] == "BLOCK" and not (
        card["status"] == "ACTIVE" and card["deterministic"] is True
        and card["reproducible"] is True and card["uncontested"] is True
    ):
        raise ValueError("BLOCK lesson is not eligible")
    if entry is not None:
        for field in ("lesson_id", "category", "title", "tags", "enforcement", "status"):
            if entry.get(field) != card[field]:
                raise ValueError("INDEX entry does not match canonical card")
    return dict(card)


def _entry(value: object, position: int) -> dict[str, Any]:
    entry = _require_plain_mapping(value, f"INDEX entry {position}")
    if set(entry) != set(INDEX_ENTRY_FIELDS):
        raise ValueError("INDEX entry fields do not match canonical schema 1")
    lesson_id = entry["lesson_id"]
    if type(lesson_id) is not str:
        raise ValueError("INDEX lesson_id must be text")
    path = entry["path"]
    if type(path) is not str or unsafe_path_text(path) or "\\" in path:
        raise ValueError("INDEX path is unsafe")
    relative = PurePosixPath(path)
    if relative != PurePosixPath("cards", str(entry["category"]), f"{lesson_id}.yaml"):
        raise ValueError("INDEX path does not use canonical layout")
    return dict(entry)


def validate_repository(root: Path) -> list[dict[str, Any]]:
    root = Path(root).absolute()
    if _is_linklike(root) or not root.is_dir():
        raise ValueError("shared lessons repository root is unsafe")
    _require_no_follow_path(root, root / "README.md", label="lessons README", directory=False)
    schema_path = root / "SCHEMA.yaml"
    _require_no_follow_path(root, schema_path, label="lessons SCHEMA", directory=False)
    schema = _read_bounded_yaml(schema_path, max_bytes=MAX_YAML_BYTES, label="lessons SCHEMA")
    if (type(schema.get("schema_version")) is not int
            or schema["schema_version"] != 1
            or not _exact_equal(CANONICAL_SCHEMA, schema)):
        raise ValueError("lessons SCHEMA does not match canonical L1 metadata")
    cards_root = root / "cards"
    _require_no_follow_path(root, cards_root, label="lessons cards root", directory=True)
    for category in sorted(CATEGORIES):
        _require_no_follow_path(
            root, cards_root / category, label=f"lessons {category} category", directory=True
        )
    index_path = root / "INDEX.yaml"
    _require_no_follow_path(root, index_path, label="lessons INDEX", directory=False)
    index = _read_bounded_yaml(index_path, max_bytes=MAX_YAML_BYTES, label="lessons INDEX")
    if set(index) != {"schema_version", "entries"} or not _is_schema_one(index.get("schema_version")):
        raise ValueError("lessons INDEX does not match canonical schema 1")
    raw_entries = index["entries"]
    if type(raw_entries) is not list or len(raw_entries) > MAX_INDEX_ENTRIES:
        raise ValueError("lessons INDEX entries are not canonical")
    entries, ids, paths = [], set(), set()
    for position, raw in enumerate(raw_entries):
        entry = _entry(raw, position)
        if entry["lesson_id"] in ids or entry["path"] in paths:
            raise ValueError("lessons INDEX contains duplicate ids or paths")
        ids.add(entry["lesson_id"]); paths.add(entry["path"])
        card_path = root.joinpath(*PurePosixPath(entry["path"]).parts)
        _require_no_follow_path(root, card_path, label="lesson card", directory=False)
        card = _read_bounded_yaml(card_path, max_bytes=MAX_YAML_BYTES, label="lesson card")
        validate_card_data(card, entry)
        entries.append(entry)
    actual, scanned = set(), 0
    pending = [cards_root]
    while pending:
        directory = pending.pop()
        for path in directory.iterdir():
            scanned += 1
            if scanned > MAX_INDEX_ENTRIES:
                raise ValueError("lessons cards scan exceeds its bound")
            if _is_linklike(path):
                raise ValueError("lessons cards contain a link or reparse point")
            _require_no_follow_path(root, path, label="lessons cards entry", directory=path.is_dir())
            if path.is_dir():
                pending.append(path)
            elif path.is_file() and path.suffix.lower() in {".yaml", ".yml"}:
                actual.add(path.relative_to(root).as_posix())
    if actual != paths:
        raise ValueError("lessons cards and INDEX declarations do not match")
    return entries
