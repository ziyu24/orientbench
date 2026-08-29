from __future__ import annotations

import ctypes
import errno
import hashlib
import itertools
import os
from pathlib import Path
import secrets
import stat
import sys
import re

import yaml

from .paper_transaction_platform import (
    _decode, _guard_directory, _move_guarded_leaf, _read_guarded, _write_all,
    _write_guarded,
)


FILE_MAX = 65536
TREE_FILES_MAX = 128
TREE_BYTES_MAX = 262144
RENAME_EXCHANGE = 2
PHASES = {
    "PREPARING", "PREPARED", "SOURCE_MOVED", "VERSION_SWAPPED", "README_SWAPPED",
    "COMMITTED", "AUDIT",
}
JOURNAL_KEYS = {
    "schema_version", "kind", "operation_id", "phase", "outcome",
    "version_path", "version_old", "version_new", "source_old",
    "source_new", "source_token", "readme_path", "readme_old",
    "readme_new", "version_token", "version_new_token", "readme_token",
    "readme_new_token", "reason",
}
QUARANTINE_KEYS = {
    "schema_version", "kind", "operation_id", "phase", "outcome", "reason",
    "path", "expected_identity", "expected_payload", "expected_tree",
}
STATE_KEYS = {"identity", "size", "mtime_ns", "sha256"}
TREE_KEYS = {"identity", "entries", "bytes", "sha256"}
HEX = re.compile(r"[0-9a-f]{32}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
PAPER_VERSION = re.compile(rb"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\n\Z")


class _ClosedLoader(yaml.SafeLoader):
    pass


def _closed_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            if key in result:
                raise ValueError("paper recovery YAML has a duplicate key")
            result[key] = loader.construct_object(value_node, deep=deep)
        except TypeError as error:
            raise ValueError("paper recovery YAML key is invalid") from error
    return result


_ClosedLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _closed_mapping
)


def _closed_yaml(payload, label):
    try:
        text = payload.decode("utf-8")
        for event in yaml.parse(text):
            if isinstance(event, yaml.events.AliasEvent) or getattr(event, "anchor", None):
                raise ValueError("paper recovery YAML aliases are forbidden")
        return yaml.load(text, Loader=_ClosedLoader)
    except (UnicodeError, yaml.YAMLError, ValueError) as error:
        raise RuntimeError(f"{label} is invalid") from error


def _identity_value(value):
    return type(value) is list and len(value) == 3 and all(
        type(item) is int for item in value
    )


def _state_value(value):
    return (
        type(value) is dict and set(value) == STATE_KEYS
        and _identity_value(value.get("identity"))
        and type(value.get("size")) is int and value["size"] >= 0
        and type(value.get("mtime_ns")) is int
        and type(value.get("sha256")) is str and SHA.fullmatch(value["sha256"])
    )


def _tree_value(value):
    return (
        type(value) is dict and set(value) == TREE_KEYS
        and _identity_value(value.get("identity"))
        and type(value.get("entries")) is int and value["entries"] >= 0
        and type(value.get("bytes")) is int and 0 <= value["bytes"] <= TREE_BYTES_MAX
        and type(value.get("sha256")) is str and SHA.fullmatch(value["sha256"])
    )


def _versions(document):
    old, new = _decode(document["version_old"]), _decode(document["version_new"])
    first, second = PAPER_VERSION.fullmatch(old), PAPER_VERSION.fullmatch(new)
    if first is None or second is None:
        raise RuntimeError("paper transaction versions are invalid")
    before = tuple(int(item) for item in first.groups())
    after = tuple(int(item) for item in second.groups())
    valid = after in {
        (before[0] + 1, 0, 0), (before[0], before[1] + 1, 0),
        (before[0], before[1], before[2] + 1),
    }
    return old[:-1].decode("ascii"), new[:-1].decode("ascii"), valid


def _validate_journal(document, record):
    if type(document) is not dict or set(document) != JOURNAL_KEYS:
        raise RuntimeError("paper transaction journal schema is invalid")
    operation = document.get("operation_id")
    if document.get("kind") == "RESERVATION":
        offset = 3 if record.name.startswith("tx-") else 2
        fields = JOURNAL_KEYS - {
            "schema_version", "kind", "operation_id", "phase", "outcome", "reason",
        }
        if (
            type(document.get("schema_version")) is not int
            or document["schema_version"] != 1
            or type(operation) is not str or HEX.fullmatch(operation) is None
            or operation != record.name[offset:] or document.get("phase") != "COMMITTED"
            or document.get("outcome") != "abandoned"
            or type(document.get("reason")) is not str
            or not document["reason"] or len(document["reason"]) > 240
            or any(document[field] is not None for field in fields)
        ):
            raise RuntimeError("paper reservation journal schema is invalid")
        return
    if (
        type(document.get("schema_version")) is not int or document["schema_version"] != 1
        or type(document.get("kind")) is not str or document["kind"] not in {"BUMP", "VERSION"}
        or type(operation) is not str or HEX.fullmatch(operation) is None
        or operation != record.name[3:]
        or type(document.get("phase")) is not str or document["phase"] not in PHASES
        or document.get("outcome") not in {None, "abandoned", "rolled_back", "finalized"}
        or type(document.get("outcome")) not in {type(None), str}
        or type(document.get("reason")) not in {type(None), str}
        or (type(document.get("reason")) is str and len(document["reason"]) > 240)
        or not _state_value(document.get("version_token"))
        or (
            document.get("version_new_token") is not None
            and not _state_value(document["version_new_token"])
        )
    ):
        raise RuntimeError("paper transaction journal schema is invalid")
    if document["phase"] == "COMMITTED":
        if document["outcome"] not in {"abandoned", "rolled_back", "finalized"}:
            raise RuntimeError("paper transaction outcome is invalid")
    elif document["outcome"] is not None:
        raise RuntimeError("paper transaction outcome is invalid")
    if document["phase"] == "AUDIT" and not document["reason"]:
        raise RuntimeError("paper transaction audit reason is invalid")
    if document["kind"] == "VERSION":
        empty = ("source_old", "source_new", "source_token", "readme_path",
                 "readme_old", "readme_new", "readme_token", "readme_new_token")
        try:
            old_bytes = _decode(document["version_old"])
            new_bytes = _decode(document["version_new"])
        except ValueError as error:
            raise RuntimeError("paper VERSION transaction bytes are invalid") from error
        pattern = (
            re.compile(rb"v[0-9]{3}\n\Z")
            if document["version_path"] == "paper/review/VERSION" else PAPER_VERSION
        )
        if (
            document["version_path"] not in {"paper/VERSION", "paper/review/VERSION"}
            or pattern.fullmatch(old_bytes) is None or pattern.fullmatch(new_bytes) is None
            or (
                document["phase"] not in {"PREPARING", "COMMITTED"}
                and not _state_value(document.get("version_new_token"))
            )
            or any(document[field] is not None for field in empty)
        ):
            raise RuntimeError("paper VERSION transaction fields are invalid")
        return
    old, new, adjacent = _versions(document)
    suffix_old = Path(document.get("source_old", "")).suffix
    if (
        document["version_path"] != "paper/VERSION" or not adjacent
        or suffix_old not in {".md", ".tex"}
        or document["source_old"] != f"paper/manuscript/manuscript-{old}{suffix_old}"
        or document["source_new"] != f"paper/manuscript/manuscript-{new}{suffix_old}"
        or not _state_value(document.get("source_token"))
        or document["readme_path"] != "paper/README.md"
        or document["readme_old"] != "readme-old" or document["readme_new"] != "readme-new"
        or not _state_value(document.get("readme_token"))
        or (
            document.get("readme_new_token") is not None
            and not _state_value(document["readme_new_token"])
        )
        or (
            document["phase"] not in {"PREPARING", "COMMITTED"}
            and (
                not _state_value(document.get("version_new_token"))
                or not _state_value(document.get("readme_new_token"))
            )
        )
    ):
        raise RuntimeError("paper bump transaction fields are invalid")


def _validate_quarantine(document, record):
    if type(document) is not dict or set(document) != QUARANTINE_KEYS:
        raise RuntimeError("paper quarantine journal schema is invalid")
    operation, phase, outcome = (
        document.get("operation_id"), document.get("phase"), document.get("outcome")
    )
    outcomes = {
        "PREPARED": {None},
        "COMMITTED": {"absent", "quarantined_owned"},
        "AUDIT": {"restored_competitor", "both_retained", "source_state_unavailable"},
    }
    path = document.get("path")
    review = type(path) is str and re.fullmatch(r"paper/review/review-v[0-9]{3}\.yaml", path)
    stage = type(path) is str and re.fullmatch(r"\.paper-init-[A-Za-z0-9_-]+", path)
    try:
        expected_payload = None if document.get("expected_payload") is None else _decode(
            document["expected_payload"]
        )
    except ValueError as error:
        raise RuntimeError("paper quarantine payload binding is invalid") from error
    if (
        type(document.get("schema_version")) is not int or document["schema_version"] != 1
        or document.get("kind") != "QUARANTINE" or type(document.get("kind")) is not str
        or type(operation) is not str or HEX.fullmatch(operation) is None
        or operation != record.name[2:] or type(phase) is not str or phase not in outcomes
        or outcome not in outcomes.get(phase, set())
        or type(document.get("reason")) is not str or not document["reason"]
        or len(document["reason"]) > 240 or not _identity_value(document.get("expected_identity"))
        or (expected_payload is not None and len(expected_payload) > FILE_MAX)
        or not (path == "paper" or stage or review)
    ):
        raise RuntimeError("paper quarantine journal schema is invalid")
    tree = document.get("expected_tree")
    if review:
        if tree is not None:
            raise RuntimeError("paper quarantine review binding is invalid")
    elif expected_payload is not None or not _tree_value(tree):
        raise RuntimeError("paper quarantine tree binding is invalid")


def _relative(root, path):
    try:
        return Path(path).absolute().relative_to(Path(root).absolute()).as_posix()
    except ValueError as error:
        raise ValueError("paper transaction path escapes project") from error


def _project_path(root, relative):
    if type(relative) is not str or not relative or ".." in Path(relative).parts:
        raise RuntimeError("paper transaction path is invalid")
    path = Path(root) / relative
    if not path.absolute().is_relative_to(Path(root).absolute()):
        raise RuntimeError("paper transaction path escapes project")
    return path


def _identity(value):
    return (value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode))


def _snapshot(value):
    return (*_identity(value), value.st_size, value.st_mtime_ns)


def _linklike(path):
    try:
        if path.is_symlink() or getattr(path, "is_junction", lambda: False)():
            return True
        attributes = getattr(os.lstat(path), "st_file_attributes", 0)
    except OSError:
        return True
    return bool(attributes & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))


def _plain_dir(path, label):
    try:
        value = os.lstat(path)
    except OSError as error:
        raise ValueError(f"{label} is unavailable") from error
    if not stat.S_ISDIR(value.st_mode) or _linklike(Path(path)):
        raise ValueError(f"{label} must be a plain directory")
    return value


def _plain_file(path, label):
    try:
        value = os.lstat(path)
    except OSError as error:
        raise ValueError(f"{label} is unavailable") from error
    if not stat.S_ISREG(value.st_mode) or _linklike(Path(path)):
        raise ValueError(f"{label} must be a plain file")
    return value


def _check_parents(states):
    for path, expected in states:
        if _identity(_plain_dir(path, "paper transaction parent")) != tuple(expected):
            raise ValueError("paper transaction parent identity changed")


def _read(path, limit=FILE_MAX, label="paper transaction file", parent_states=()):
    _check_parents(parent_states)
    before = _plain_file(path, label)
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    try:
        descriptor = os.open(path, flags)
        opened = os.fstat(descriptor)
        if _snapshot(opened) != _snapshot(before):
            raise ValueError(f"{label} changed before read")
        payload = bytearray()
        while True:
            chunk = os.read(descriptor, limit + 1 - len(payload))
            if not chunk:
                break
            payload.extend(chunk)
            if len(payload) > limit:
                raise ValueError(f"{label} exceeds size limit")
        after = os.fstat(descriptor)
        if _snapshot(after) != _snapshot(opened):
            raise ValueError(f"{label} changed during read")
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    final = _plain_file(path, label)
    if _snapshot(final) != _snapshot(before):
        raise ValueError(f"{label} path changed")
    _check_parents(parent_states)
    return bytes(payload)


def _file_state(path, limit=FILE_MAX, parent_states=()):
    _check_parents(parent_states)
    value = _plain_file(path, "paper transaction state")
    payload = _read(path, limit, parent_states=parent_states)
    final = _plain_file(path, "paper transaction state")
    if _snapshot(final) != _snapshot(value):
        raise ValueError("paper transaction state changed")
    return {
        "identity": list(_identity(final)), "size": len(payload),
        "mtime_ns": final.st_mtime_ns,
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _matches_file(path, state, limit, parent_states=()):
    try:
        return _file_state(path, limit, parent_states) == state
    except ValueError:
        return False


def _tree_state(path, parent_states=()):
    _check_parents(parent_states)
    root = _plain_dir(path, "paper transaction tree")
    digest = hashlib.sha256()
    count = total = 0
    pending = [(Path(path), _identity(root))]
    while pending:
        parent, expected_parent = pending.pop()
        if _identity(_plain_dir(parent, "paper transaction tree component")) != expected_parent:
            raise ValueError("paper transaction tree component changed")
        component_states = (*parent_states, (parent, expected_parent))
        children = list(itertools.islice(parent.iterdir(), TREE_FILES_MAX + 2))
        if len(children) > TREE_FILES_MAX + 1:
            raise ValueError("paper transaction tree exceeds entry limit")
        for child in sorted(children, key=lambda item: item.name):
            count += 1
            if count > TREE_FILES_MAX:
                raise ValueError("paper transaction tree exceeds limits")
            if _linklike(child):
                raise ValueError("paper transaction tree contains a link")
            relative = child.relative_to(path).as_posix().encode("utf-8")
            value = os.lstat(child)
            digest.update(relative + b"\0")
            if stat.S_ISDIR(value.st_mode):
                digest.update(b"d\0")
                pending.append((child, _identity(value)))
                continue
            if not stat.S_ISREG(value.st_mode):
                raise ValueError("paper transaction tree is not closed")
            payload = _read(child, parent_states=component_states)
            total += len(payload)
            if total > TREE_BYTES_MAX:
                raise ValueError("paper transaction tree exceeds limits")
            digest.update(b"f\0" + hashlib.sha256(payload).digest())
        if _identity(_plain_dir(parent, "paper transaction tree component")) != expected_parent:
            raise ValueError("paper transaction tree component changed")
    final = _plain_dir(path, "paper transaction tree")
    if _identity(final) != _identity(root):
        raise ValueError("paper transaction tree identity changed")
    _check_parents(parent_states)
    return {
        "identity": list(_identity(root)), "entries": count, "bytes": total,
        "sha256": digest.hexdigest(),
    }


def _fsync_dir(path):
    if os.name == "nt":
        return
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _win_move(source, target, flags):
    function = ctypes.WinDLL("kernel32", use_last_error=True).MoveFileExW
    function.argtypes = [ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_uint32]
    function.restype = ctypes.c_int
    if not function(str(source), str(target), flags):
        code = ctypes.get_last_error()
        if code in {80, 183}:
            raise FileExistsError(code, "target exists", target)
        raise OSError(code, "MoveFileExW failed", target)


def _move_noreplace(source, target):
    source, target = Path(source), Path(target)
    if os.stat(source.parent).st_dev != os.stat(target.parent).st_dev:
        raise ValueError("paper transaction paths cross filesystems")
    if os.name == "nt":
        _win_move(source, target, 8)
        return
    library = ctypes.CDLL(None, use_errno=True)
    old, new = os.fsencode(source), os.fsencode(target)
    if sys.platform.startswith("linux"):
        function = getattr(library, "renameat2", None)
        args = (-100, old, -100, new, 1)
    elif sys.platform == "darwin":
        function = getattr(library, "renamex_np", None)
        args = (old, new, 0x00000004)
    else:
        function = None
    if function is None:
        raise RuntimeError("paper transaction no-replace primitive is unavailable")
    function.argtypes = (
        [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        if sys.platform.startswith("linux") else
        [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    )
    function.restype = ctypes.c_int
    if function(*args) == 0:
        _fsync_dir(source.parent)
        if target.parent != source.parent:
            _fsync_dir(target.parent)
        return
    code = ctypes.get_errno()
    if code in {errno.EEXIST, errno.ENOTEMPTY}:
        raise FileExistsError(code, os.strerror(code), target)
    if code in {errno.ENOSYS, errno.EINVAL, errno.ENOTSUP, errno.EXDEV}:
        raise RuntimeError("paper transaction no-replace primitive is unavailable")
    raise OSError(code, os.strerror(code), target)


def _move_from_fd_noreplace(parent_fd, name, target, target_guard=None):
    if os.name == "nt":
        raise RuntimeError("paper dirfd move is unavailable on Windows")
    library = ctypes.CDLL(None, use_errno=True)
    encoded = os.fsencode(name)
    target_fd = target_guard.fd if target_guard is not None else -100
    destination = os.fsencode(Path(target).name if target_guard is not None else Path(target))
    if sys.platform.startswith("linux"):
        function = getattr(library, "renameat2", None)
        args = (parent_fd, encoded, target_fd, destination, 1)
    elif sys.platform == "darwin":
        function = getattr(library, "renameatx_np", None)
        args = (parent_fd, encoded, target_fd, destination, 0x00000004)
    else:
        function = None
    if function is None:
        raise RuntimeError("paper dirfd no-replace primitive is unavailable")
    function.argtypes = [
        ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
    ]
    function.restype = ctypes.c_int
    if function(*args) == 0:
        os.fsync(parent_fd)
        if target_guard is not None:
            os.fsync(target_guard.fd)
        else:
            _fsync_dir(Path(target).parent)
        return
    code = ctypes.get_errno()
    if code in {errno.EEXIST, errno.ENOTEMPTY}:
        raise FileExistsError(code, os.strerror(code), target)
    if code in {errno.ENOSYS, errno.EINVAL, errno.ENOTSUP, errno.EXDEV}:
        raise RuntimeError("paper dirfd no-replace primitive is unavailable")
    raise OSError(code, os.strerror(code), target)


def _exchange(left, right):
    left, right = Path(left), Path(right)
    if os.stat(left.parent).st_dev != os.stat(right.parent).st_dev:
        raise ValueError("paper transaction exchange crosses filesystems")
    if os.name == "nt":
        backup = right.with_name(right.name + ".backup")
        if os.path.lexists(backup):
            raise RuntimeError("paper transaction exchange backup already exists")
        function = ctypes.WinDLL("kernel32", use_last_error=True).ReplaceFileW
        function.argtypes = [
            ctypes.c_wchar_p, ctypes.c_wchar_p, ctypes.c_wchar_p,
            ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p,
        ]
        function.restype = ctypes.c_int
        if not function(str(left), str(right), str(backup), 1, None, None):
            raise OSError(ctypes.get_last_error(), "ReplaceFileW failed", left)
        _win_move(backup, right, 8)
        return
    library = ctypes.CDLL(None, use_errno=True)
    old, new = os.fsencode(left), os.fsencode(right)
    if sys.platform.startswith("linux"):
        function = getattr(library, "renameat2", None)
        args = (-100, old, -100, new, RENAME_EXCHANGE)
    elif sys.platform == "darwin":
        function = getattr(library, "renamex_np", None)
        args = (old, new, 0x00000002)
    else:
        function = None
    if function is None:
        raise RuntimeError("paper transaction exchange primitive is unavailable")
    function.argtypes = (
        [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        if sys.platform.startswith("linux") else
        [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
    )
    function.restype = ctypes.c_int
    if function(*args) != 0:
        code = ctypes.get_errno()
        if code in {errno.ENOSYS, errno.EINVAL, errno.ENOTSUP, errno.EXDEV}:
            raise RuntimeError("paper transaction exchange primitive is unavailable")
        raise OSError(code, os.strerror(code), left)
    _fsync_dir(left.parent)
    if right.parent != left.parent:
        _fsync_dir(right.parent)


def _durable_replace(path, payload, parent_guard=None):
    path = Path(path)
    stage_name = "." + path.name + "-" + secrets.token_hex(8)
    owned_guard = parent_guard is None
    guard = _guard_directory(path.parent) if owned_guard else parent_guard
    try:
        _write_guarded(guard, stage_name, payload)
        try:
            if guard.fd >= 0:
                try:
                    os.stat(path.name, dir_fd=guard.fd, follow_symlinks=False)
                except FileNotFoundError:
                    _move_guarded_leaf(guard, stage_name, path.name)
                else:
                    os.replace(
                        stage_name, path.name,
                        src_dir_fd=guard.fd, dst_dir_fd=guard.fd,
                    )
                    os.fsync(guard.fd)
            elif os.path.lexists(path):
                _win_move(path.parent / stage_name, path, 1 | 8)
            else:
                _move_noreplace(path.parent / stage_name, path)
            guard.check()
        finally:
            stage = path.parent / stage_name
            if guard.fd >= 0:
                try:
                    os.stat(stage_name, dir_fd=guard.fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise RuntimeError("paper transaction staging requires audit")
            elif os.path.lexists(stage):
                raise RuntimeError("paper transaction staging requires audit")
    finally:
        if owned_guard:
            guard.close()
