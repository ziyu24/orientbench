import hashlib
import os
from pathlib import Path
import re
import stat
import sys

import yaml

from .lessons_repository import recovery_git_dir
from .paper_transaction_io import (
    _closed_yaml,
    _durable_replace,
    _file_state,
    _fsync_dir,
    _identity,
    _matches_file,
    _move_noreplace,
)
from .paper_transaction_platform import (
    _allocate_record,
    _guard_directory,
    _guarded_move,
    _journal_stage,
    _leaf_snapshot,
    _list_guarded,
    _read_guarded,
    _record_guards,
    _record_parents,
    _store_record_yaml,
    _vault_lock,
    _write_descriptor,
)


PDF_MAX_BYTES = 64 * 1024 * 1024
VAULT_MAX_BYTES = 2 * PDF_MAX_BYTES
RECORDS_MAX = 64
ACTIVE_MAX = 8
JOURNAL_MAX = 8192
VERSION = re.compile(r"v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\Z")
HEX = re.compile(r"[0-9a-f]{32}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")
RECORD = re.compile(r"ex-([0-9a-f]{32})\Z")
N = r"(?:0|[1-9][0-9]*)"
V = fr"v{N}\.{N}\.{N}"
TEMP = re.compile(fr"paper/manuscript/\.manuscript-({V})\.([0-9a-f]{{32}})\.pdf\.tmp\Z")
TARGET = re.compile(fr"paper/manuscript/manuscript-({V})\.pdf\Z")
KEYS = set("schema_version kind operation_id phase outcome reason paper_version path target parent_identity expected_identity expected_file".split())
PHASES = set("RESERVED TEMP_CREATED PREPARED PUBLISHING RETRACTING COMMITTED AUDIT".split())
OUTCOMES = {
    "RESERVED": {None}, "TEMP_CREATED": {None}, "PREPARED": {None},
    "PUBLISHING": {None}, "RETRACTING": {None},
    "COMMITTED": {
        "absent", "abandoned", "published", "quarantined_owned",
        "target_conflict", "retracted_owned",
    },
    "AUDIT": {"restored_competitor", "both_retained", "state_unavailable"},
}
A = "paper export recovery requires audit"
S = "paper export recovery schema is invalid"


def vault_path(root, create=False):
    vault = recovery_git_dir(Path(root)) / "cqc-paper-export-recovery"
    if not os.path.lexists(vault):
        if not create:
            return vault
        try:
            os.mkdir(vault)
        except FileExistsError:
            pass
    with _guard_directory(vault):
        pass
    return vault
def _valid_identity(value):
    return type(value) is list and len(value) == 3 and all(type(item) is int for item in value)
def _valid_file(value):
    if type(value) is not dict or set(value) != {"identity", "size", "mtime_ns", "sha256"}:
        return False
    return (_valid_identity(value["identity"]) and type(value["size"]) is int
            and 0 <= value["size"] <= PDF_MAX_BYTES and type(value["mtime_ns"]) is int
            and type(value["sha256"]) is str and SHA.fullmatch(value["sha256"]) is not None)
def _validate(document, record):
    if type(document) is not dict or set(document) != KEYS:
        raise RuntimeError(S)
    match = RECORD.fullmatch(Path(record).name)
    operation = document.get("operation_id")
    phase = document.get("phase")
    outcome = document.get("outcome")
    if (
        match is None or type(operation) is not str or HEX.fullmatch(operation) is None
        or operation != match.group(1) or document.get("schema_version") != 1
        or document.get("kind") != "PDF_EXPORT" or phase not in PHASES
        or outcome not in OUTCOMES.get(phase, set())
        or type(document.get("reason")) is not str or not document["reason"]
        or len(document["reason"]) > 240
    ):
        raise RuntimeError(S)
    if outcome == "abandoned":
        if any(document.get(key) is not None for key in (
            "paper_version", "path", "target", "parent_identity",
            "expected_identity", "expected_file"
        )):
            raise RuntimeError("paper export abandoned record is invalid")
        return
    version, path, target = (
        document.get("paper_version"), document.get("path"), document.get("target")
    )
    temp_match = TEMP.fullmatch(path) if type(path) is str else None
    target_match = TARGET.fullmatch(target) if type(target) is str else None
    parent = document.get("parent_identity")
    identity, expected = document.get("expected_identity"), document.get("expected_file")
    if (
        type(version) is not str or VERSION.fullmatch(version) is None
        or temp_match is None or target_match is None
        or temp_match.group(1) != version or target_match.group(1) != version
        or temp_match.group(2) != operation
        or not _valid_identity(parent)
        or (identity is not None and not _valid_identity(identity))
        or (expected is not None and not _valid_file(expected))
        or (expected is not None and expected["identity"] != identity)
        or (phase in {"TEMP_CREATED", "PREPARED", "PUBLISHING"} and identity is None)
        or (phase in {"PREPARED", "PUBLISHING", "RETRACTING"} and expected is None)
    ):
        raise RuntimeError(S)


def _store(tx, phase, outcome=None):
    tx["outcome"] = outcome
    _store_record_yaml(tx, phase, KEYS, _validate, JOURNAL_MAX,
                       yaml.safe_dump, _durable_replace)
def _promote_stage(tx):
    stage = tx.pop("_stage", None)
    if stage is None:
        return
    record = Path(tx["record"])
    identity = tuple(tx["record_parents"][-1][1])
    _guarded_move(
        record / stage, record / "journal.yaml", _move_noreplace,
        source_expected=identity, target_expected=identity,
    )
def _load(record, vault_guard=None, promote=True):
    record = Path(record)
    guards = _record_guards(record, None, vault_guard)
    try:
        names = set(_list_guarded(guards[1], 12))
        stages = {name for name in names if _journal_stage(name)}
        if len(stages) > 8 or names - {"journal.yaml", "payload"} - stages:
            raise RuntimeError("paper export recovery record is not closed")
        if "journal.yaml" not in names:
            operation = RECORD.fullmatch(record.name)
            if operation is None:
                raise RuntimeError("paper export recovery record name is invalid")
            if names:
                if len(stages) != 1 or names != stages:
                    raise RuntimeError("paper export empty reservation is not closed")
                stage = next(iter(stages))
                payload = _read_guarded(guards[1], stage, JOURNAL_MAX)
                document = _closed_yaml(payload, "paper export recovery journal stage")
                _validate(document, record)
                document.update({
                    "record": record,
                    "record_parents": (
                        (record.parent, guards[0].identity),
                        (record, guards[1].identity),
                    ),
                    "vault_guard": vault_guard,
                    "_stage": stage,
                })
                if promote:
                    _promote_stage(document)
                return document
            tx = {
                "schema_version": 1, "kind": "PDF_EXPORT",
                "operation_id": operation.group(1), "phase": "COMMITTED",
                "outcome": "abandoned", "reason": "empty export reservation abandoned",
                "paper_version": None, "path": None, "target": None,
                "parent_identity": None,
                "expected_identity": None, "expected_file": None,
                "record": record, "record_parents": _record_parents(record),
                "vault_guard": vault_guard,
                "_empty": True,
            }
            if promote:
                _store(tx, "COMMITTED", "abandoned")
                tx.pop("_empty", None)
            return tx
        payload = _read_guarded(guards[1], "journal.yaml", JOURNAL_MAX)
        document = _closed_yaml(payload, "paper export recovery journal")
        _validate(document, record)
        document.update({
            "record": record,
            "record_parents": ((record.parent, guards[0].identity), (record, guards[1].identity)),
            "vault_guard": vault_guard,
        })
        return document
    finally:
        guards[1].close()
        if vault_guard is None:
            guards[0].close()


def load_record(record):
    return {key: value for key, value in _load(record).items() if key in KEYS}
def _path(root, relative):
    path = Path(root) / relative
    try:
        path.absolute().relative_to(Path(root).absolute())
    except ValueError as error:
        raise RuntimeError("paper export recovery path escapes project") from error
    return path
def _parent_guard(root, tx):
    guard = _guard_directory(Path(root) / "paper/manuscript")
    if list(guard.identity) != tx["parent_identity"]:
        guard.close()
        raise ValueError("paper export manuscript parent identity changed")
    return guard
def parent_guard(tx):
    return _parent_guard(Path(tx["root"]), tx)
def _guard_generation(guard):
    guard.check()
    value = os.fstat(guard.fd) if guard.fd >= 0 else os.lstat(guard.path)
    return (
        value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode),
        value.st_mtime_ns, value.st_ctime_ns,
    )
def parent_generation(guard):
    return _guard_generation(guard)
def check_parent_generation(guard, expected):
    if _guard_generation(guard) != expected:
        raise ValueError("paper export manuscript parent changed during runner")
def runner_output_path(guard, name):
    guard.check()
    if sys.platform == "win32":
        return str((guard.path / name).absolute())
    if guard.fd < 0:
        raise RuntimeError("paper export platform has no stable directory fd anchor")
    if sys.platform.startswith("linux"):
        anchored = Path(f"/proc/{os.getpid()}/fd/{guard.fd}")
    elif sys.platform == "darwin":
        anchored = Path(f"/dev/fd/{guard.fd}")
    else:
        raise RuntimeError("paper export platform has no stable runner anchor")
    if not anchored.is_dir():
        raise RuntimeError("paper export stable runner anchor is unavailable")
    return str(anchored / name)
def runner_options(guard):
    guard.check()
    if sys.platform == "win32" or sys.platform.startswith("linux"):
        return {}
    if sys.platform == "darwin" and guard.fd >= 0:
        return {"pass_fds": (guard.fd,)}
    raise RuntimeError("paper export platform cannot inherit a stable runner anchor")
def _guarded_file_state(guard, name, limit):
    before = _leaf_snapshot(guard, name)
    payload = _read_guarded(guard, name, limit)
    after = _leaf_snapshot(guard, name)
    if after != before:
        raise ValueError("paper export guarded leaf changed")
    return payload, {
        "identity": list(after[:3]), "size": len(payload),
        "mtime_ns": after[4], "sha256": hashlib.sha256(payload).hexdigest(),
    }
def _create_guarded(guard, name):
    if type(name) is not str or Path(name).name != name:
        raise ValueError("paper export temporary leaf name is invalid")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    guard.check()
    descriptor = (
        os.open(name, flags, 0o600, dir_fd=guard.fd)
        if guard.fd >= 0 else os.open(guard.path / name, flags, 0o600)
    )
    opened = None
    try:
        _write_descriptor(descriptor, b"")
        value = os.fstat(descriptor)
        if not stat.S_ISREG(value.st_mode):
            raise ValueError("paper export temporary leaf must be a plain file")
        opened = (
            value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode),
            value.st_size, value.st_mtime_ns, value.st_ctime_ns,
        )
        if _leaf_snapshot(guard, name) != opened:
            raise ValueError("paper export temporary leaf changed during create")
    finally:
        os.close(descriptor)
    if _leaf_snapshot(guard, name) != opened:
        raise ValueError("paper export temporary leaf changed after create")
    return {
        "identity": list(opened[:3]), "size": opened[3],
        "mtime_ns": opened[4], "sha256": hashlib.sha256(b"").hexdigest(),
    }
def _owned(path, tx):
    try:
        state = _file_state(path, PDF_MAX_BYTES)
        if state["identity"] != tx["expected_identity"]:
            return False
        expected = tx.get("expected_file")
        return ((expected is None or state == expected)
                and _file_state(path, PDF_MAX_BYTES) == state)
    except (OSError, ValueError):
        return False
def _move(source, target, tx, *, source_record=False, target_record=False):
    record_identity = tuple(tx["record_parents"][-1][1])
    parent_identity = tuple(tx["parent_identity"])
    return _guarded_move(
        source, target, _move_noreplace,
        source_expected=record_identity if source_record else parent_identity,
        target_expected=record_identity if target_record else parent_identity,
    )


def _quarantine(root, tx, path, outcome="quarantined_owned"):
    payload = Path(tx["record"]) / "payload"
    public_exists, payload_exists = os.path.lexists(path), os.path.lexists(payload)
    if public_exists and payload_exists:
        _store(tx, "AUDIT", "both_retained")
        raise RuntimeError(A)
    if tx.get("expected_file") is None:
        try:
            with _parent_guard(root, tx):
                state = _file_state(path, PDF_MAX_BYTES)
            if state["identity"] != tx["expected_identity"]:
                raise ValueError("paper export unbound leaf identity changed")
        except (OSError, ValueError):
            pass
        _store(tx, "AUDIT", "state_unavailable")
        raise RuntimeError(A)
    if public_exists:
        _move(path, payload, tx, target_record=True)
        payload_exists = True
    if not payload_exists:
        _store(tx, "COMMITTED", "absent")
        return
    if _owned(payload, tx):
        _store(tx, "COMMITTED", outcome)
        return
    try:
        _move(payload, path, tx, source_record=True)
        restored = True
    except BaseException:
        restored = False
    _store(tx, "AUDIT", "restored_competitor" if restored else "both_retained")
    raise RuntimeError(A)
def _recover_one(root, tx):
    phase = tx["phase"]
    if phase == "COMMITTED":
        return
    if phase == "AUDIT":
        raise RuntimeError(A)
    try:
        with _parent_guard(root, tx):
            pass
    except (OSError, ValueError) as error:
        _store(tx, "AUDIT", "state_unavailable")
        raise RuntimeError("paper export parent recovery requires audit") from error
    temporary = _path(root, tx["path"])
    target = _path(root, tx["target"])
    payload = Path(tx["record"]) / "payload"
    if phase == "RETRACTING":
        public_exists, payload_exists = os.path.lexists(target), os.path.lexists(payload)
        if payload_exists and not public_exists:
            if _owned(payload, tx):
                _store(tx, "COMMITTED", "retracted_owned")
                return
        if public_exists and not payload_exists:
            return _quarantine(root, tx, target, "retracted_owned")
        _store(tx, "AUDIT", "both_retained" if public_exists else "state_unavailable")
        raise RuntimeError("paper export retract recovery requires audit")
    target_owned = tx.get("expected_file") is not None and _owned(target, tx)
    if target_owned:
        if os.path.lexists(temporary) or os.path.lexists(payload):
            _store(tx, "AUDIT", "both_retained")
            raise RuntimeError(A)
        _store(tx, "COMMITTED", "published")
        return
    if os.path.lexists(payload):
        if os.path.lexists(temporary):
            _store(tx, "AUDIT", "both_retained")
            raise RuntimeError(A)
        return _quarantine(root, tx, temporary)
    if os.path.lexists(temporary):
        return _quarantine(
            root, tx, temporary,
            "target_conflict" if os.path.lexists(target) else "quarantined_owned",
        )
    if phase == "RESERVED" and tx.get("expected_identity") is None:
        _store(tx, "COMMITTED", "absent")
        return
    _store(tx, "AUDIT", "state_unavailable")
    raise RuntimeError(A)
def _records(guard):
    names = _list_guarded(guard, RECORDS_MAX + 2)
    if "capacity.lock" in names:
        names.remove("capacity.lock")
    if len(names) > RECORDS_MAX:
        raise RuntimeError("paper export recovery capacity exceeded")
    records = []
    total = 0
    for name in sorted(names):
        if RECORD.fullmatch(name) is None:
            raise RuntimeError("paper export recovery vault has unexpected entry")
        record = guard.path / name
        with _guard_directory(record, guard) as record_guard:
            children = _list_guarded(record_guard, 12)
            for child in children:
                if child == "journal.yaml" or _journal_stage(child):
                    total += len(_read_guarded(record_guard, child, JOURNAL_MAX))
                elif child == "payload":
                    value = (os.stat(child, dir_fd=record_guard.fd, follow_symlinks=False)
                             if record_guard.fd >= 0 else os.lstat(record / child))
                    if not stat.S_ISREG(value.st_mode) or value.st_size > PDF_MAX_BYTES:
                        raise RuntimeError("paper export recovery payload exceeds limit")
                    total += value.st_size
                else:
                    raise RuntimeError("paper export recovery record is not closed")
        records.append(record)
    if total > VAULT_MAX_BYTES:
        raise RuntimeError("paper export recovery vault exceeds byte capacity")
    return records
def _recover_locked(root, guard):
    records = _records(guard)
    transactions = [_load(record, guard, promote=False) for record in records]
    active = sum(tx["phase"] not in {"COMMITTED", "AUDIT"} for tx in transactions)
    if active > ACTIVE_MAX:
        raise RuntimeError("paper export active recovery capacity exceeded")
    for tx in transactions:
        if tx.pop("_empty", False):
            _store(tx, "COMMITTED", "abandoned")
        _promote_stage(tx)
        _recover_one(root, tx)
    return [_load(record, guard, promote=False) for record in records]
def recover(root):
    vault = vault_path(root, create=False)
    if not os.path.lexists(vault):
        return
    with _vault_lock(vault) as guard:
        _recover_locked(Path(root), guard)
def require_explicit_pdf(root, version, target, parent_identity):
    root, m = Path(root), "current-version PDF lacks explicit export proof"
    if (VERSION.fullmatch(version) is None
            or target != f"paper/manuscript/manuscript-{version}.pdf"):
        raise ValueError("current-version PDF target is invalid")
    v = vault_path(root, create=False)
    if not os.path.lexists(v): raise ValueError(m)
    with _vault_lock(v) as guard:
        n = sum(1 for tx in _recover_locked(root, guard)
                if tx["phase"] == "COMMITTED" and tx["outcome"] == "published"
                and tx["paper_version"] == version and tx["target"] == target
                and tx["parent_identity"] == list(parent_identity)
                and _owned(root / target, tx))
    if n > 1: raise ValueError("multiple explicit PDF export proofs")
    if not n: raise ValueError(m)
def begin(root, version):
    root = Path(root)
    if type(version) is not str or VERSION.fullmatch(version) is None:
        raise ValueError("paper export version is invalid")
    vault = vault_path(root, create=True)
    with _vault_lock(vault) as guard:
        records = _recover_locked(root, guard)
        if len(records) >= RECORDS_MAX:
            raise RuntimeError("paper export recovery record capacity reached")
        record = _allocate_record(root, "ex", vault_path, RECORDS_MAX, _fsync_dir, guard)
        operation = record.name[3:]
        with _guard_directory(root / "paper/manuscript") as manuscript_guard:
            parent_identity = list(manuscript_guard.identity)
        tx = {
            "schema_version": 1, "kind": "PDF_EXPORT", "operation_id": operation,
            "phase": "RESERVED", "outcome": None, "reason": "explicit PDF export",
            "paper_version": version, "path": f"paper/manuscript/.manuscript-{version}.{operation}.pdf.tmp",
            "target": f"paper/manuscript/manuscript-{version}.pdf",
            "parent_identity": parent_identity,
            "expected_identity": None, "expected_file": None,
            "record": record, "record_parents": _record_parents(record),
            "vault_guard": guard,
        }
        _store(tx, "RESERVED")
        tx.pop("vault_guard", None)
        tx["root"] = root
        return tx


def create_temp(tx, guard=None):
    root = Path(tx["root"])
    path = _path(root, tx["path"])
    owned_guard = guard is None
    current_guard = _parent_guard(root, tx) if owned_guard else guard
    try:
        if list(current_guard.identity) != tx["parent_identity"]:
            raise ValueError("paper export manuscript parent identity changed")
        created = _create_guarded(current_guard, path.name)
        payload, state = _guarded_file_state(
            current_guard, path.name, PDF_MAX_BYTES
        )
        if payload != b"" or state != created:
            raise ValueError("paper export temporary leaf changed after create")
        tx["expected_identity"] = state["identity"]
        tx["root"] = root
        _store(tx, "TEMP_CREATED")
        current_guard.check()
    finally:
        if owned_guard:
            current_guard.close()
    return path
def read_output(tx, guard):
    root = Path(tx["root"])
    path = _path(root, tx["path"])
    current, state = _guarded_file_state(guard, path.name, PDF_MAX_BYTES)
    if state["identity"] != tx["expected_identity"]:
        raise ValueError("paper export output identity changed")
    return current
def bind_output(tx, payload, guard=None):
    if type(payload) is not bytes or len(payload) > PDF_MAX_BYTES:
        raise ValueError("paper export output exceeds size limit")
    root = Path(tx["root"])
    path = _path(root, tx["path"])
    owned_guard = guard is None
    current_guard = _parent_guard(root, tx) if owned_guard else guard
    try:
        current, state = _guarded_file_state(current_guard, path.name, PDF_MAX_BYTES)
        current_guard.check()
    finally:
        if owned_guard:
            current_guard.close()
    if (current != payload or state["identity"] != tx["expected_identity"]
            or state["size"] != len(payload)
            or state["sha256"] != hashlib.sha256(payload).hexdigest()):
        raise ValueError("paper export output changed during binding")
    tx["expected_file"] = state
    _store(tx, "PREPARED")
def publish(tx):
    root = Path(tx["root"])
    temporary, target = _path(root, tx["path"]), _path(root, tx["target"])
    with _parent_guard(root, tx) as guard:
        _store(tx, "PUBLISHING")
        try:
            move_noreplace(
                temporary, target, expected_parent=tuple(tx["parent_identity"])
            )
        except FileExistsError:
            abort(tx, outcome="target_conflict")
            raise
        guard.check()
    if not _owned(target, tx):
        _store(tx, "AUDIT", "state_unavailable")
        raise RuntimeError("paper export publication requires audit")
    _store(tx, "COMMITTED", "published")
    return target
def abort(tx, outcome="quarantined_owned"):
    root = Path(tx["root"])
    vault = vault_path(root, create=True)
    with _vault_lock(vault) as guard:
        current = _load(tx["record"], guard)
        if current["phase"] == "COMMITTED":
            return
        if current["phase"] == "AUDIT":
            raise RuntimeError(A)
        current["root"] = root
        if current["phase"] == "PUBLISHING":
            _recover_one(root, current)
            tx.update({key: value for key, value in current.items() if key in KEYS})
            return
        temporary = _path(root, current["path"])
        _quarantine(root, current, temporary, outcome)
        tx.update({key: value for key, value in current.items() if key in KEYS})
def retract(tx):
    root = Path(tx["root"])
    vault = vault_path(root, create=True)
    with _vault_lock(vault) as guard:
        current = _load(tx["record"], guard)
        current["root"] = root
        target = _path(root, current["target"])
        _store(current, "RETRACTING")
        _quarantine(root, current, target, "retracted_owned")
        tx.update({key: value for key, value in current.items() if key in KEYS})


def move_noreplace(source, target, expected_parent=None):
    return _guarded_move(
        source, target, _move_noreplace,
        source_expected=expected_parent, target_expected=expected_parent,
    )
