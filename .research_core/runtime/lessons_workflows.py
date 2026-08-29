"""User-gated, local-only research lessons mutation workflows."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import tempfile
from typing import Any

import yaml

from .lessons import (
    _CARD_FIELDS,
    _CATEGORIES,
    _GIT_SHA,
    _HEX_64,
    _INDEX_ENTRY_FIELDS,
    _LESSON_ID,
    _REPOSITORY,
    _is_linklike,
    _is_schema_one,
    _read_bounded_yaml,
    _require_no_follow_path,
    _require_plain_mapping,
    _require_plain_path,
    _require_string,
    _require_string_list,
    load_lock,
)
from .lessons_repository import (
    CATEGORIES,
    LIST_LIMITS,
    TEXT_LIMITS,
    matches_creation_token,
    recovery_git_dir,
    retain_recovery,
    unsafe_path_text,
    validate_card_data,
    validate_repository,
)
from .storage import write_text_atomic


_FAILURE_ID = re.compile(r"F[0-9]{6}\Z")
_MAX_FAILURE = 64 * 1024
_MAX_PREVIEW = 64 * 1024
_MAX_PROMOTIONS = 8192
_MAX_SCHEMA = 32 * 1024
_FAILURE_FIELDS = {
    "schema_version", "failure_id", "status", "title", "category", "tags",
    "reproduction_conditions", "not_applicable_when", "attempts", "conclusion", "sources",
    "failure_signature", "root_cause", "confidence", "detection",
    "prevention", "recovery", "raw_evidence_summary", "error_excerpt",
    "enforcement", "deterministic", "reproducible", "uncontested",
}
_PROMOTION_FIELDS = {
    "failure_id", "failure_digest", "lesson_id", "lessons_base_sha",
    "card_path", "preview_digest", "status",
}
_SENSITIVE = re.compile(
    r"(?i)(?:password|passwd|credential|secret|token|ssh[_ -]?user|identity[_ -]?file)\s*[:=]"
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----|ssh://|https?://[^/\s:@]+:[^/\s@]+@"
)
_IPV4 = re.compile(r"(?<![0-9])(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?![0-9])")


class PromotionRollbackError(ValueError):
    """Promotion compensation could not restore all owned state."""


def _dump(value: dict[str, Any]) -> str:
    class NoAliasDumper(yaml.SafeDumper):
        def ignore_aliases(self, data: object) -> bool:
            return True

    return yaml.dump(value, Dumper=NoAliasDumper, allow_unicode=True, sort_keys=True)


def _digest(value: dict[str, Any]) -> str:
    data = json.dumps(value, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def _signed(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result["preview_digest"] = _digest(result)
    return result


def _verify_digest(value: dict[str, Any], label: str) -> None:
    claimed = value.get("preview_digest")
    unsigned = dict(value)
    unsigned.pop("preview_digest", None)
    if (type(claimed) is not str or _HEX_64.fullmatch(claimed) is None
            or claimed != _digest(unsigned)):
        raise ValueError(f"{label} preview digest does not match its content")


def _explicit(value: bool) -> None:
    if value is not True:
        raise ValueError("an explicit user request confirmation is required")


def _safe_text(value: object, label: str, limit: int = 4096) -> str:
    text = _require_string(value, label, max_bytes=limit)
    if _SENSITIVE.search(text) or _IPV4.search(text) or unsafe_path_text(text):
        raise ValueError(f"{label} contains sensitive connection, credential, or local path content")
    return text


def _relative(value: object, label: str) -> str:
    text = _require_string(value, label, max_bytes=1024)
    path = PurePosixPath(text)
    if (unsafe_path_text(text) or "\\" in text or path.is_absolute()
            or ".." in path.parts or not path.parts):
        raise ValueError(f"{label} must be a POSIX project-relative path without traversal")
    return path.as_posix()


def _output(root: Path, relative: PurePosixPath) -> Path:
    root = Path(root).absolute()
    _require_plain_path(root, label="project root", directory=True)
    current = root
    for part in relative.parts[:-1]:
        current /= part
        if current.exists():
            _require_plain_path(current, label="controlled project directory", directory=True)
        else:
            current.mkdir()
            _require_plain_path(current, label="controlled project directory", directory=True)
    target = current / relative.name
    if _is_linklike(target):
        raise ValueError("controlled project output must not be a link")
    if root.resolve() not in target.parent.resolve().parents and target.parent.resolve() != root.resolve():
        raise ValueError("controlled project output escapes the project root")
    return target


def _existing(root: Path, relative: PurePosixPath, label: str) -> Path:
    root = Path(root).absolute()
    path = root.joinpath(*relative.parts)
    _require_no_follow_path(root, path, label=label, directory=False)
    return path


def _canonical_input(root: Path, supplied: Path, relative: PurePosixPath, label: str) -> Path:
    root = Path(root).absolute()
    supplied = Path(supplied)
    path = (supplied if supplied.is_absolute() else root / supplied).absolute()
    expected = root.joinpath(*relative.parts).absolute()
    if path != expected:
        raise ValueError(f"{label} must use the canonical project path")
    _require_no_follow_path(root, path, label=label, directory=False)
    return path


def read_input_mapping(path: Path, *, label: str, max_bytes: int = _MAX_FAILURE) -> dict[str, Any]:
    return _read_bounded_yaml(Path(path), max_bytes=max_bytes, label=label)


def _validate_failure(value: dict[str, Any]) -> dict[str, Any]:
    failure = _require_plain_mapping(value, "failure request")
    if set(failure) != _FAILURE_FIELDS or not _is_schema_one(failure.get("schema_version")):
        raise ValueError("failure request fields do not match schema 1")
    failure_id = failure["failure_id"]
    if type(failure_id) is not str or _FAILURE_ID.fullmatch(failure_id) is None:
        raise ValueError("failure_id must use stable F000001 format")
    if failure["status"] not in {"FAILED", "INCONCLUSIVE"}:
        raise ValueError("failure status must be FAILED or INCONCLUSIVE")
    if failure["category"] not in CATEGORIES:
        raise ValueError("failure category is invalid")
    _safe_text(failure["title"], "failure title", TEXT_LIMITS["title"])
    tags = _require_string_list(failure["tags"], "failure tags", max_items=LIST_LIMITS["tags"])
    for tag in tags:
        _safe_text(tag, "failure tag", TEXT_LIMITS["tag"])
    field_limits = {
        "reproduction_conditions": ("applies_when", "condition"),
        "not_applicable_when": ("not_applicable_when", "condition"),
        "failure_signature": ("failure_signature", "failure_signature"),
        "detection": ("detection", "action"),
        "prevention": ("prevention", "action"),
        "recovery": ("recovery", "action"),
    }
    for field, (count_key, text_key) in field_limits.items():
        items = _require_string_list(
            failure[field], f"failure {field}", max_items=LIST_LIMITS[count_key]
        )
        if not items:
            raise ValueError(f"failure {field} must not be empty")
        for item in items:
            _safe_text(item, f"failure {field} item", TEXT_LIMITS[text_key])
    excerpts = _require_string_list(failure["error_excerpt"], "failure error_excerpt", max_items=20)
    for item in excerpts:
        if "\n" in item or "\r" in item:
            raise ValueError("failure error_excerpt items must each be one line")
        _safe_text(item, "failure error_excerpt item", TEXT_LIMITS["error_excerpt_line"])
    attempts = failure["attempts"]
    if type(attempts) is not list or not attempts or len(attempts) > 32:
        raise ValueError("failure attempts must be a non-empty bounded list")
    for position, raw in enumerate(attempts):
        item = _require_plain_mapping(raw, f"failure attempt {position}")
        if set(item) != {"action", "outcome"}:
            raise ValueError("failure attempt fields do not match schema 1")
        _safe_text(item["action"], "failure attempt action", TEXT_LIMITS["action"])
        _safe_text(item["outcome"], "failure attempt outcome", TEXT_LIMITS["action"])
    sources = failure["sources"]
    if type(sources) is not list or not sources or len(sources) > 64:
        raise ValueError("failure sources must be a non-empty bounded list")
    for position, source in enumerate(sources):
        _relative(source, f"failure source {position}")
    _safe_text(failure["conclusion"], "failure conclusion", TEXT_LIMITS["root_cause"])
    _safe_text(failure["root_cause"], "failure root_cause", TEXT_LIMITS["root_cause"])
    _safe_text(
        failure["raw_evidence_summary"], "failure raw_evidence_summary",
        TEXT_LIMITS["raw_evidence_summary"],
    )
    if failure["confidence"] not in {"LOW", "MEDIUM", "HIGH"}:
        raise ValueError("failure confidence is invalid")
    if failure["enforcement"] not in {"BLOCK", "WARN"}:
        raise ValueError("failure enforcement is invalid")
    for field in ("deterministic", "reproducible", "uncontested"):
        if type(failure[field]) is not bool:
            raise ValueError(f"failure {field} must be boolean")
    if failure["enforcement"] == "BLOCK" and not all(
        failure[field] is True for field in ("deterministic", "reproducible", "uncontested")
    ):
        raise ValueError("BLOCK failures must be deterministic, reproducible, and uncontested")
    if len(_dump(failure).encode("utf-8")) > _MAX_FAILURE:
        raise ValueError("failure request exceeds its size bound")
    return dict(failure)


def _git(root: Path, *arguments: str) -> str:
    if tuple(arguments) not in {("rev-parse", "HEAD"), ("status", "--porcelain")}:
        raise ValueError("unsupported Git operation for research lessons")
    root = Path(root).absolute()
    _require_plain_path(root, label="local lessons Git checkout", directory=True)
    try:
        result = subprocess.run(["git", *arguments], cwd=root, check=False, text=True,
                                encoding="utf-8", capture_output=True, timeout=15)
    except (OSError, subprocess.SubprocessError) as error:
        raise ValueError("local lessons Git read failed") from error
    if result.returncode:
        detail = result.stderr.strip().splitlines()
        raise ValueError(f"local lessons Git read failed: {(detail[0] if detail else 'Git command failed')[:512]}")
    return result.stdout.strip()


def _clean_head(root: Path) -> str:
    head = _git(root, "rev-parse", "HEAD")
    if _GIT_SHA.fullmatch(head) is None:
        raise ValueError("shared lessons HEAD must be 40 lowercase hexadecimal characters")
    if _git(root, "status", "--porcelain"):
        raise ValueError("shared lessons checkout must be clean")
    return head


def _file_identity(metadata: os.stat_result) -> tuple[int, int, int]:
    return metadata.st_dev, metadata.st_ino, metadata.st_mode


def _matches_creation_token(token: dict[str, Any]) -> bool:
    return matches_creation_token(token)


def _recovery_git_dir(root: Path) -> Path:
    return recovery_git_dir(root)


def _fsync_directory(directory: Path) -> None:
    try:
        descriptor = os.open(directory, os.O_RDONLY)
    except OSError:
        if os.name != "nt":
            raise
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _retain_creation_recovery(token: dict[str, Any]) -> dict[str, Any]:
    return retain_recovery(token["git_dir"], token, _matches_creation_token)


def _write_exclusive_atomic(path: Path, text: str, repository: Path) -> dict[str, Any]:
    """Publish complete bytes without an existence-check race."""
    content = text.encode("utf-8")
    git_dir = _recovery_git_dir(repository)
    if os.lstat(git_dir).st_dev != os.lstat(path.parent).st_dev:
        raise ValueError("recovery gitdir must share the target filesystem")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    reservation = None
    publish_error = None
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        source_identity = _file_identity(os.lstat(temporary))
        os.link(temporary, path)
        reservation = {
            "path": path,
            "git_dir": git_dir,
            "identity": source_identity,
            "bytes": content,
            "digest": hashlib.sha256(content).hexdigest(),
        }
        if not _matches_creation_token(reservation):
            raise PromotionRollbackError(
                "exclusive publish ownership could not be verified; state was preserved"
            )
        _fsync_directory(path.parent)
    except BaseException as error:
        publish_error = error
    try:
        temporary.unlink(missing_ok=True)
    except BaseException as error:
        if publish_error is None:
            publish_error = error
        else:
            try:
                temporary.unlink(missing_ok=True)
            except BaseException:
                pass
    if publish_error is None:
        return reservation
    if reservation is None:
        raise publish_error
    try:
        recovery = _retain_creation_recovery(reservation)
    except BaseException as rollback_error:
        raise PromotionRollbackError(
            "exclusive publish failed; recovery could not restore the working tree"
        ) from rollback_error
    recovery_id = recovery["recovery_id"]
    state = "working tree restored" if recovery["restored"] else "target reoccupied"
    raise PromotionRollbackError(
        f"exclusive publish failed; {state}; recovery retained as {recovery_id}"
    ) from publish_error


def record_failure(root: Path, request: dict[str, Any]) -> Path:
    failure = _validate_failure(request)
    path = _output(root, PurePosixPath("research", "failures", f"{failure['failure_id']}.yaml"))
    _write_exclusive_atomic(path, _dump(failure), Path(root))
    return path


def update_preview(root: Path, *, candidate_checkout: Path, explicit_user_request: bool) -> Path:
    _explicit(explicit_user_request)
    root, candidate = Path(root).absolute(), Path(candidate_checkout).absolute()
    base, head = load_lock(root), _clean_head(candidate)
    validate_repository(candidate)
    if _clean_head(candidate) != head or load_lock(root) != base:
        raise ValueError("lessons candidate or lock changed during update preview")
    document = _signed({"schema_version": 1, "kind": "LESSONS_UPDATE", "base_lock": base,
                        "candidate": {"repository": _REPOSITORY, "git_sha": head, "schema": 1}})
    path = _output(root, PurePosixPath("coordination", "lessons", "update-preview.yaml"))
    write_text_atomic(path, _dump(document), overwrite=True)
    return path


def _update_document(value: dict[str, Any]) -> dict[str, Any]:
    value = _require_plain_mapping(value, "lessons update preview")
    if set(value) != {"schema_version", "kind", "base_lock", "candidate", "preview_digest"}:
        raise ValueError("lessons update preview fields do not match schema 1")
    if not _is_schema_one(value["schema_version"]) or value["kind"] != "LESSONS_UPDATE":
        raise ValueError("lessons update preview schema or kind is invalid")
    base = _require_plain_mapping(value["base_lock"], "lessons update base lock")
    if (set(base) != {"schema_version", "repository", "schema", "git_sha"}
            or not _is_schema_one(base.get("schema_version")) or not _is_schema_one(base.get("schema"))
            or base.get("repository") != _REPOSITORY or type(base.get("git_sha")) is not str
            or _GIT_SHA.fullmatch(base["git_sha"]) is None):
        raise ValueError("lessons update base lock is invalid")
    candidate = _require_plain_mapping(value["candidate"], "lessons update candidate")
    if (set(candidate) != {"repository", "git_sha", "schema"} or candidate.get("repository") != _REPOSITORY
            or not _is_schema_one(candidate.get("schema")) or type(candidate.get("git_sha")) is not str
            or _GIT_SHA.fullmatch(candidate["git_sha"]) is None):
        raise ValueError("lessons update candidate binding is invalid")
    _verify_digest(value, "lessons update")
    return dict(value)


def apply_update(root: Path, *, preview_path: Path, explicit_user_request: bool) -> Path:
    _explicit(explicit_user_request)
    root = Path(root).absolute()
    path = _canonical_input(root, preview_path,
                            PurePosixPath("coordination", "lessons", "update-preview.yaml"),
                            "lessons update preview")
    preview = _update_document(_read_bounded_yaml(path, max_bytes=_MAX_PREVIEW,
                                                   label="lessons update preview"))
    current = load_lock(root)
    if current != preview["base_lock"]:
        raise ValueError("lessons lock drifted from the update preview base")
    candidate = preview["candidate"]
    updated = {"schema_version": 1, "repository": candidate["repository"],
               "schema": candidate["schema"], "git_sha": candidate["git_sha"]}
    if load_lock(root) != current:
        raise ValueError("lessons lock changed during update apply")
    target = _existing(root, PurePosixPath("coordination", "lessons", "LOCK.yaml"),
                       "project lessons lock")
    write_text_atomic(target, _dump(updated), overwrite=True)
    return target


def _load_failure(root: Path, failure_id: str) -> dict[str, Any]:
    if type(failure_id) is not str or _FAILURE_ID.fullmatch(failure_id) is None:
        raise ValueError("failure_id must use stable F000001 format")
    path = _existing(root, PurePosixPath("research", "failures", f"{failure_id}.yaml"),
                     "project failure record")
    result = _validate_failure(_read_bounded_yaml(path, max_bytes=_MAX_FAILURE,
                                                  label="project failure record"))
    if result["failure_id"] != failure_id:
        raise ValueError("failure record id does not match its path")
    return result


def _promotion_artifacts(
    failure: dict[str, Any], lock: dict[str, Any], lesson_id: str
) -> tuple[dict[str, Any], dict[str, Any]]:
    if lesson_id != f"L{failure['failure_id'][1:]}":
        raise ValueError("promotion lesson id does not bind its failure")
    card = {
        "schema_version": 1, "lesson_id": f"L{failure['failure_id'][1:]}",
        "title": failure["title"], "category": failure["category"], "tags": failure["tags"],
        "applies_when": failure["reproduction_conditions"],
        "not_applicable_when": failure["not_applicable_when"],
        "failure_signature": failure["failure_signature"], "root_cause": failure["root_cause"],
        "confidence": failure["confidence"], "detection": failure["detection"],
        "prevention": failure["prevention"], "recovery": failure["recovery"],
        "raw_evidence_summary": failure["raw_evidence_summary"],
        "error_excerpt": failure["error_excerpt"], "enforcement": failure["enforcement"],
        "deterministic": failure["deterministic"], "reproducible": failure["reproducible"],
        "uncontested": failure["uncontested"],
        "source_fingerprint": "sha256:" + _digest(failure),
        "created_sha": lock["git_sha"], "revised_sha": lock["git_sha"], "status": "ACTIVE",
    }
    entry = {"lesson_id": card["lesson_id"],
             "path": f"cards/{card['category']}/{card['lesson_id']}.yaml",
             "category": card["category"], "title": card["title"], "tags": list(card["tags"]),
             "enforcement": card["enforcement"], "status": card["status"]}
    validate_card_data(card, entry)
    return card, entry


def _promotion_document(value: dict[str, Any]) -> dict[str, Any]:
    value = _require_plain_mapping(value, "lessons promotion preview")
    fields = {"schema_version", "kind", "failure_id", "failure_digest",
              "base_lock", "card", "index_entry", "preview_digest"}
    if set(value) != fields or not _is_schema_one(value.get("schema_version")) or value.get("kind") != "LESSON_PROMOTION":
        raise ValueError("lessons promotion preview fields, schema, or kind are invalid")
    failure_id = value["failure_id"]
    if type(failure_id) is not str or _FAILURE_ID.fullmatch(failure_id) is None:
        raise ValueError("lessons promotion failure_id is invalid")
    if type(value["failure_digest"]) is not str or _HEX_64.fullmatch(value["failure_digest"]) is None:
        raise ValueError("lessons promotion failure digest is invalid")
    base_lock = _require_plain_mapping(value["base_lock"], "lessons promotion base lock")
    if (set(base_lock) != {"schema_version", "repository", "schema", "git_sha"}
            or not _is_schema_one(base_lock.get("schema_version"))
            or base_lock.get("repository") != _REPOSITORY
            or not _is_schema_one(base_lock.get("schema"))
            or type(base_lock.get("git_sha")) is not str
            or _GIT_SHA.fullmatch(base_lock["git_sha"]) is None):
        raise ValueError("lessons promotion base lock is invalid")
    card = _require_plain_mapping(value["card"], "lessons promotion card")
    entry = _require_plain_mapping(value["index_entry"], "lessons promotion index entry")
    validate_card_data(card, entry)
    if (card["lesson_id"] != f"L{failure_id[1:]}"
            or card["source_fingerprint"] != "sha256:" + value["failure_digest"]):
        raise ValueError("lessons promotion card does not bind its failure")
    _verify_digest(value, "lessons promotion")
    return dict(value)


def promotion_preview(root: Path, *, failure_id: str) -> Path:
    root = Path(root).absolute()
    failure, lock = _load_failure(root, failure_id), load_lock(root)
    lesson_id = f"L{failure_id[1:]}"
    card, entry = _promotion_artifacts(failure, lock, lesson_id)
    document = _signed({"schema_version": 1, "kind": "LESSON_PROMOTION",
                        "failure_id": failure_id, "failure_digest": _digest(failure),
                        "base_lock": lock, "card": card, "index_entry": entry})
    _promotion_document(document)
    if _load_failure(root, failure_id) != failure or load_lock(root) != lock:
        raise ValueError("failure record or lessons lock changed during promotion preview")
    path = _output(root, PurePosixPath("coordination", "lessons", f"promotion-{failure_id}.yaml"))
    write_text_atomic(path, _dump(document), overwrite=True)
    return path


def _promotions(root: Path) -> tuple[Path, dict[str, Any]]:
    path = _existing(root, PurePosixPath("coordination", "lessons", "PROMOTIONS.yaml"),
                     "project lessons promotions")
    value = _read_bounded_yaml(path, max_bytes=_MAX_PROMOTIONS, label="project lessons promotions")
    if set(value) != {"schema_version", "promotions"} or not _is_schema_one(value.get("schema_version")):
        raise ValueError("PROMOTIONS fields do not match schema 1")
    items = value["promotions"]
    if type(items) is not list or len(items) > 128:
        raise ValueError("PROMOTIONS promotions must be a bounded list")
    failures, lessons = set(), set()
    for position, raw in enumerate(items):
        item = _require_plain_mapping(raw, f"promotion mapping {position}")
        if set(item) != _PROMOTION_FIELDS:
            raise ValueError("promotion mapping fields do not match schema 1")
        if (type(item["failure_id"]) is not str or _FAILURE_ID.fullmatch(item["failure_id"]) is None
                or type(item["lesson_id"]) is not str or _LESSON_ID.fullmatch(item["lesson_id"]) is None
                or item["failure_id"] in failures or item["lesson_id"] in lessons):
            raise ValueError("promotion mapping ids are invalid or duplicated")
        if type(item["failure_digest"]) is not str or _HEX_64.fullmatch(item["failure_digest"]) is None:
            raise ValueError("promotion mapping failure digest is invalid")
        if type(item["lessons_base_sha"]) is not str or _GIT_SHA.fullmatch(item["lessons_base_sha"]) is None:
            raise ValueError("promotion mapping base SHA is invalid")
        _relative(item["card_path"], "promotion mapping card path")
        if (type(item["preview_digest"]) is not str or _HEX_64.fullmatch(item["preview_digest"]) is None
                or item["status"] != "STAGED_LOCAL"):
            raise ValueError("promotion mapping digest or status is invalid")
        failures.add(item["failure_id"]); lessons.add(item["lesson_id"])
    return path, value


def apply_promotion(root: Path, *, preview_path: Path, shared_checkout: Path,
                    explicit_user_request: bool) -> Path:
    _explicit(explicit_user_request)
    root, shared = Path(root).absolute(), Path(shared_checkout).absolute()
    match = re.fullmatch(r"promotion-(F[0-9]{6})\.yaml", Path(preview_path).name)
    if match is None:
        raise ValueError("promotion preview must use the canonical failure filename")
    failure_id, name = match.group(1), Path(preview_path).name
    path = _canonical_input(root, preview_path, PurePosixPath("coordination", "lessons", name),
                            "lessons promotion preview")
    preview = _promotion_document(_read_bounded_yaml(path, max_bytes=_MAX_PREVIEW,
                                                      label="lessons promotion preview"))
    if preview["failure_id"] != failure_id:
        raise ValueError("promotion preview filename does not bind its failure")
    lock, failure = load_lock(root), _load_failure(root, failure_id)
    if lock != preview["base_lock"]:
        raise ValueError("lessons lock drifted from promotion preview base")
    if _digest(failure) != preview["failure_digest"]:
        raise ValueError("promotion failure binding changed")
    expected_card, expected_entry = _promotion_artifacts(
        failure, lock, preview["card"].get("lesson_id")
    )
    if preview["card"] != expected_card or preview["index_entry"] != expected_entry:
        raise ValueError("promotion preview does not match canonical rebuilt artifacts")
    head = _clean_head(shared)
    if head != preview["base_lock"]["git_sha"]:
        raise ValueError("shared lessons HEAD does not match the promotion base")
    entries, card, entry = validate_repository(shared), expected_card, expected_entry
    if any(item["lesson_id"] == card["lesson_id"] for item in entries):
        raise FileExistsError("shared lesson id already exists")
    target = shared.joinpath(*PurePosixPath(entry["path"]).parts)
    if target.exists() or _is_linklike(target):
        raise FileExistsError("shared lesson card target already exists")
    _require_no_follow_path(shared, target.parent, label="shared lesson card category", directory=True)
    promotions_path, promotions = _promotions(root)
    if any(item["failure_id"] == failure_id or item["lesson_id"] == card["lesson_id"]
           for item in promotions["promotions"]):
        raise FileExistsError("project promotion mapping already exists")
    index_path, index_before = shared / "INDEX.yaml", (shared / "INDEX.yaml").read_bytes()
    promotions_before = promotions_path.read_bytes()
    clean_entries = [{key: value for key, value in item.items() if not key.startswith("_")}
                     for item in entries]
    updated_index = {"schema_version": 1, "entries": sorted([*clean_entries, entry],
                                                              key=lambda item: item["lesson_id"])}
    mapping = {"failure_id": failure_id, "failure_digest": preview["failure_digest"],
               "lesson_id": card["lesson_id"], "lessons_base_sha": preview["base_lock"]["git_sha"],
               "card_path": entry["path"], "preview_digest": preview["preview_digest"],
               "status": "STAGED_LOCAL"}
    updated_promotions = {"schema_version": 1, "promotions": [*promotions["promotions"], mapping]}
    if len(_dump(updated_promotions).encode("utf-8")) > _MAX_PROMOTIONS:
        raise ValueError("PROMOTIONS update exceeds its size bound")
    if _clean_head(shared) != head or load_lock(root) != lock or _load_failure(root, failure_id) != failure:
        raise ValueError("promotion inputs changed before apply")
    card_token = None
    index_written = promotions_written = False
    try:
        card_token = _write_exclusive_atomic(target, _dump(card), shared)
        write_text_atomic(index_path, _dump(updated_index), overwrite=True); index_written = True
        write_text_atomic(promotions_path, _dump(updated_promotions), overwrite=True); promotions_written = True
    except BaseException as apply_error:
        rollback_errors: list[tuple[str, BaseException]] = []
        recovery = None
        for label, current_path, baseline, known_written in (
            ("PROMOTIONS", promotions_path, promotions_before, promotions_written),
            ("INDEX", index_path, index_before, index_written),
        ):
            needs_restore = known_written
            try:
                needs_restore = current_path.read_bytes() != baseline or needs_restore
            except BaseException as error:
                rollback_errors.append((f"{label} state read", error))
                needs_restore = True
            if needs_restore:
                try:
                    write_text_atomic(
                        current_path, baseline.decode("utf-8"), overwrite=True
                    )
                except BaseException as error:
                    rollback_errors.append((f"{label} restore", error))
        if card_token is not None:
            try:
                recovery = _retain_creation_recovery(card_token)
            except BaseException as error:
                rollback_errors.append(("card recovery", error))
        if rollback_errors:
            labels = ", ".join(label for label, _ in rollback_errors)
            recovery_note = (
                f"; recovery retained as {recovery['recovery_id']}"
                if recovery is not None else ""
            )
            raise PromotionRollbackError(
                f"promotion compensation failed for {labels}{recovery_note}"
            ) from rollback_errors[0][1]
        if recovery is not None:
            state = "working tree restored" if recovery["restored"] else "target reoccupied"
            raise PromotionRollbackError(
                f"promotion apply failed; {state}; recovery retained as {recovery['recovery_id']}"
            ) from apply_error
        raise
    return promotions_path
