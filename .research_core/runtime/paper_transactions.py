from __future__ import annotations

import os
from pathlib import Path
import stat

import yaml

from .lessons_repository import recovery_git_dir
from .paper_transaction_platform import (
    _allocate_record, _close_guards, _empty_reservation, _encode, _guard_directory,
    _guarded_exchange, _guarded_move, _list_guarded, _journal_stage, _locate_vault,
    _read_guarded, _record_guards, _record_parents, _store_record_yaml, _SwapAudit,
    _swap_files_cas, _transactional, _vault_lock, _write_record_blob,
)
from .paper_transaction_io import (
    FILE_MAX, JOURNAL_KEYS, PHASES, QUARANTINE_KEYS, TREE_BYTES_MAX, _closed_yaml, _decode,
    _durable_replace, _exchange, _file_state, _fsync_dir, _identity, _matches_file,
    _move_from_fd_noreplace,
    _move_noreplace, _plain_dir, _plain_file, _project_path, _read, _relative,
    _tree_state, _validate_journal, _validate_quarantine,
)


JOURNAL_MAX = 16384
RECORDS_MAX = 64
ACTIVE_MAX=8
RECORD_BYTES_MAX = TREE_BYTES_MAX * 4 + JOURNAL_MAX
VAULT_BYTES_MAX = RECORD_BYTES_MAX * RECORDS_MAX
SOURCE_AUDIT = "paper source recovery requires audit"
TX_AUDIT = "paper transaction recovery requires audit"
Q_AUDIT = "paper quarantine recovery requires audit"
PARENTS="record_parents"


def _vault_path(root, create=False): return _locate_vault(root, recovery_git_dir, create)


def _vault(root, create=False, identities=None, guard=None):
    vault = _vault_path(root, create)
    if vault is None:
        return None
    if guard is None:
        with _vault_lock(vault) as owned:
            return _vault(root, create, identities, owned)
    guard.check()
    names = _list_guarded(guard, RECORDS_MAX + 1)
    records = [name for name in names if name != "capacity.lock"]
    if len(records) > RECORDS_MAX:
        raise RuntimeError("paper recovery vault exceeds record limit")
    vault_bytes = 0
    for name in names:
        if name == "capacity.lock":
            value = (
                os.stat(name, dir_fd=guard.fd, follow_symlinks=False)
                if guard.fd >= 0 else os.lstat(vault / name)
            )
            if not stat.S_ISREG(value.st_mode) or value.st_size > 1:
                raise RuntimeError("paper recovery capacity lock is invalid")
            continue
        if not name.startswith(("tx-", "q-")):
            raise RuntimeError("paper recovery vault has unexpected entry")
        entry = vault / name
        with _guard_directory(entry, guard) as record_guard:
            if identities is not None:
                identities[name] = (guard.identity, record_guard.identity)
            children = _list_guarded(record_guard, 15)
            stages = {child for child in children if _journal_stage(child)}
            if len(stages) > 8:
                raise RuntimeError("paper journal staging exceeds entry limit")
            allowed = ({"journal.yaml", "payload"} if name.startswith("q-") else
                       {"journal.yaml", "version-swap", "version-swap.backup",
                        "readme-old", "readme-new", "readme-swap",
                        "readme-swap.backup"})
            if set(children) - allowed - stages:
                raise RuntimeError("paper recovery record tree is not closed")
            parents = ((vault, guard.identity), (entry, record_guard.identity))
            record_bytes = 0
            for child_name in children:
                child = entry / child_name
                value = (
                    os.stat(child_name, dir_fd=record_guard.fd, follow_symlinks=False)
                    if record_guard.fd >= 0 else os.lstat(child)
                )
                if child_name == "payload" and stat.S_ISDIR(value.st_mode):
                    record_guard.check()
                    record_bytes += _tree_state(child, parents)["bytes"]
                    record_guard.check()
                elif not stat.S_ISREG(value.st_mode):
                    raise RuntimeError("paper recovery record contains link")
                else:
                    limit = (JOURNAL_MAX if child_name == "journal.yaml"
                             or child_name in stages else TREE_BYTES_MAX)
                    record_bytes += len(_read_guarded(record_guard, child_name, limit))
            if record_bytes > RECORD_BYTES_MAX:
                raise RuntimeError("paper recovery record exceeds total size limit")
            vault_bytes += record_bytes
    if vault_bytes > VAULT_BYTES_MAX:
        raise RuntimeError("paper recovery vault exceeds total size limit")
    guard.check()
    return vault


def _new_record(root, prefix, guard=None): return _allocate_record(root, prefix, _vault, RECORDS_MAX, _fsync_dir, guard)


def _locked(function): return _transactional(function, _vault_path, lambda: _recover_unlocked)


def _store_journal(tx, phase):
    if phase not in PHASES:
        raise ValueError("paper transaction phase invalid")
    _store_record_yaml(tx, phase, JOURNAL_KEYS, _validate_journal, JOURNAL_MAX,
                       yaml.safe_dump, _durable_replace)


def _load_journal(record, expected=None, vault_guard=None):
    allowed = {
        "journal.yaml", "version-swap", "version-swap.backup", "readme-old",
        "readme-new", "readme-swap", "readme-swap.backup",
    }
    guards = _record_guards(record, expected, vault_guard)
    try:
        names = set(_list_guarded(guards[1], len(allowed) + 8))
        stages = {name for name in names if _journal_stage(name)}
        if len(stages) > 8 or names - allowed - stages:
            raise RuntimeError("paper transaction record tree not closed")
        payload = _read_guarded(guards[1], "journal.yaml", JOURNAL_MAX)
        document = _closed_yaml(payload, "paper transaction journal")
        _validate_journal(document, record)
        document["record"] = record
        document[PARENTS] = (
            (record.parent, guards[0].identity), (record, guards[1].identity)
        )
        document["vault_guard"] = vault_guard
        return document
    finally:
        guards[1].close()
        if vault_guard is None:
            guards[0].close()


def _load_quarantine(record, expected=None, vault_guard=None):
    guards = _record_guards(record, expected, vault_guard)
    try:
        names = set(_list_guarded(guards[1], 10))
        stages = {name for name in names if _journal_stage(name)}
        if (
            len(stages) > 8 or names - {"journal.yaml", "payload"} - stages
            or "journal.yaml" not in names
        ):
            raise RuntimeError("paper quarantine record tree not closed")
        payload = _read_guarded(guards[1], "journal.yaml", JOURNAL_MAX)
        document = _closed_yaml(payload, "paper quarantine journal")
        (
            _validate_journal(document, record)
            if document.get("kind") == "RESERVATION"
            else _validate_quarantine(document, record)
        )
        document["record"] = record
        document[PARENTS] = (
            (record.parent, guards[0].identity), (record, guards[1].identity)
        )
        document["vault_guard"] = vault_guard
        return document
    finally:
        guards[1].close()
        if vault_guard is None:
            guards[0].close()


def _source_rollback(old, new, state):
    if os.path.lexists(old):
        if _matches_file(old, state, TREE_BYTES_MAX) and not os.path.lexists(new):
            return
        raise RuntimeError(SOURCE_AUDIT)
    if not _matches_file(new, state, TREE_BYTES_MAX):
        raise RuntimeError(SOURCE_AUDIT)
    _guarded_move(new, old, _move_noreplace)
    if not _matches_file(old, state, TREE_BYTES_MAX):
        raise RuntimeError(SOURCE_AUDIT)


def _source_finalize(old, new, state):
    if os.path.lexists(new):
        if _matches_file(new, state, TREE_BYTES_MAX) and not os.path.lexists(old):
            return
        raise RuntimeError(SOURCE_AUDIT)
    if not _matches_file(old, state, TREE_BYTES_MAX):
        raise RuntimeError(SOURCE_AUDIT)
    _guarded_move(old, new, _move_noreplace)


def _source_move_cas(old, new, state):
    if not _matches_file(old, state, TREE_BYTES_MAX):
        raise ValueError("paper source changed before transaction move")
    _guarded_move(old, new, _move_noreplace)
    if _matches_file(new, state, TREE_BYTES_MAX):
        return
    try:
        if os.path.lexists(old):
            raise RuntimeError(SOURCE_AUDIT)
        competitor = _file_state(new, TREE_BYTES_MAX)
        _guarded_move(new, old, _move_noreplace)
        if not _matches_file(old, competitor, TREE_BYTES_MAX):
            raise RuntimeError(SOURCE_AUDIT)
    except BaseException as error:
        raise RuntimeError(SOURCE_AUDIT) from error
    raise ValueError("paper source changed during transaction move")


def _swap_cas(path, swap, old, new, old_state, new_state, swap_parents=(),
              limit=JOURNAL_MAX):
    return _swap_files_cas(
        path, swap, old, new, old_state, new_state, swap_parents, limit,
        _matches_file, _read, _file_state, _guarded_exchange, _exchange,
    )


@_locked
def begin_bump(root, source, target, version_path, old_version, new_version,
               readme_path, old_readme, new_readme, *, _vault_guard=None):
    version_state = _file_state(version_path, JOURNAL_MAX)
    readme_state = _file_state(readme_path, TREE_BYTES_MAX)
    source_state = _file_state(source, TREE_BYTES_MAX)
    if _read(version_path, JOURNAL_MAX) != old_version:
        raise ValueError("paper transaction VERSION changed")
    if _read(readme_path, TREE_BYTES_MAX) != old_readme:
        raise ValueError("paper transaction README changed")
    record = _new_record(root, "tx", _vault_guard)
    swap = record / "version-swap"
    readme_old = record / "readme-old"
    readme_new = record / "readme-new"
    readme_swap = record / "readme-swap"
    tx = {
        "schema_version": 1, "kind": "BUMP", "operation_id": record.name[3:],
        "record": record, "phase": "PREPARING", "outcome": None,
        "version_path": _relative(root, version_path),
        "version_old": _encode(old_version), "version_new": _encode(new_version),
        "version_token": version_state, "version_new_token": None,
        "source_old": _relative(root, source), "source_new": _relative(root, target),
        "source_token": source_state, "readme_path": _relative(root, readme_path),
        "readme_old": "readme-old", "readme_new": "readme-new",
        "readme_token": readme_state, "readme_new_token": None,
        "reason": None,
    }
    tx[PARENTS] = _record_parents(record)
    tx["vault_guard"] = _vault_guard
    _store_journal(tx, "PREPARING")
    try:
        for name, payload in (
            ("version-swap", new_version), ("readme-old", old_readme),
            ("readme-new", new_readme), ("readme-swap", new_readme),
        ):
            _write_record_blob(
                record, tx[PARENTS], name, payload, _vault_guard
            )
        version_new_state = _file_state(swap, JOURNAL_MAX)
        readme_new_state = _file_state(readme_swap, TREE_BYTES_MAX)
        tx["version_new_token"] = version_new_state
        tx["readme_new_token"] = readme_new_state
        _store_journal(tx, "PREPARED")
    except BaseException as error:
        tx["outcome"] = "abandoned"
        tx["reason"] = str(error)[:240] or "paper preparation failed"
        _store_journal(tx, "COMMITTED")
        if isinstance(error, OSError):
            raise RuntimeError("paper bump preparation failed") from error
        raise
    try:
        _source_move_cas(source, target, source_state)
        _store_journal(tx, "SOURCE_MOVED")
        _swap_cas(
            version_path, swap, old_version, new_version,
            version_state, version_new_state, tx[PARENTS],
        )
        _store_journal(tx, "VERSION_SWAPPED")
        _swap_cas(
            readme_path, readme_swap, old_readme, new_readme,
            readme_state, readme_new_state,
        )
        _store_journal(tx, "README_SWAPPED")
        tx["outcome"] = "finalized"
        _store_journal(tx, "COMMITTED")
    except _SwapAudit as error:
        if not (
            _matches_file(version_path, version_new_state, JOURNAL_MAX)
            and _read(version_path, JOURNAL_MAX) == new_version
        ):
            _source_rollback(source, target, source_state)
        tx["reason"] = str(error)[:240]
        _store_journal(tx, "AUDIT")
        raise RuntimeError(TX_AUDIT) from error
    except BaseException as error:
        recovered = False
        try:
            if _read(version_path) == old_version:
                _source_rollback(source, target, source_state)
            else:
                _recover_bump(root, tx)
                recovered = True
        except BaseException as recovery_error:
            tx["reason"] = "ambiguous bump recovery"
            _store_journal(tx, "AUDIT")
            raise RuntimeError(TX_AUDIT) from recovery_error
        if not recovered:
            tx["reason"] = str(error)[:240]
            _store_journal(tx, "AUDIT")
        if isinstance(error, OSError):
            raise RuntimeError("paper bump transaction failed") from error
        raise


def _recover_bump(root, tx):
    version = _project_path(root, tx["version_path"])
    source = _project_path(root, tx["source_old"])
    target = _project_path(root, tx["source_new"])
    old, new = _decode(tx["version_old"]), _decode(tx["version_new"])
    state = tx["source_token"]
    current = _read(version)
    if current == old and _matches_file(version, tx["version_token"], JOURNAL_MAX):
        _source_rollback(source, target, state)
        tx["outcome"] = "rolled_back"
        _store_journal(tx, "COMMITTED")
        return
    if current == new and _matches_file(version, tx["version_new_token"], JOURNAL_MAX):
        _source_finalize(source, target, state)
        readme = _project_path(root, tx["readme_path"])
        parents = tx.get(PARENTS, ())
        old_readme = _read(
            Path(tx["record"]) / tx["readme_old"], parent_states=parents
        )
        new_readme = _read(
            Path(tx["record"]) / tx["readme_new"], parent_states=parents
        )
        if _read(readme, TREE_BYTES_MAX) == old_readme and _matches_file(
            readme, tx["readme_token"], TREE_BYTES_MAX
        ):
            _swap_cas(
                readme, Path(tx["record"]) / "readme-swap",
                old_readme, new_readme, tx["readme_token"],
                tx["readme_new_token"], parents, TREE_BYTES_MAX,
            )
        elif not (
            _read(readme, TREE_BYTES_MAX) == new_readme
            and _matches_file(readme, tx["readme_new_token"], TREE_BYTES_MAX)
        ):
            raise RuntimeError("paper transaction README recovery requires audit")
        tx["outcome"] = "finalized"
        _store_journal(tx, "COMMITTED")
        return
    _source_rollback(source, target, state)
    tx["reason"] = "ambiguous VERSION state"
    _store_journal(tx, "AUDIT")
    raise RuntimeError(TX_AUDIT)


@_locked
def begin_version(root, path, old, new, expected_identity=None, *, _vault_guard=None):
    old_state = _file_state(path, JOURNAL_MAX)
    if _read(path, JOURNAL_MAX) != old:
        raise ValueError("paper transaction VERSION changed")
    if expected_identity is not None and list(expected_identity) != old_state["identity"]:
        raise ValueError("paper transaction VERSION identity changed")
    record = _new_record(root, "tx", _vault_guard)
    swap = record / "version-swap"
    tx = {
        "schema_version": 1, "kind": "VERSION", "operation_id": record.name[3:],
        "record": record, "phase": "PREPARING", "outcome": None,
        "version_path": _relative(root, path), "version_old": _encode(old),
        "version_new": _encode(new), "version_token": old_state,
        "version_new_token": None, "source_old": None, "source_new": None,
        "source_token": None, "readme_path": None, "readme_old": None,
        "readme_new": None, "readme_token": None, "readme_new_token": None,
        "reason": None,
    }
    tx[PARENTS] = _record_parents(record)
    tx["vault_guard"] = _vault_guard
    _store_journal(tx, "PREPARING")
    try:
        _write_record_blob(
            record, tx[PARENTS], "version-swap", new, _vault_guard
        )
        new_state = _file_state(swap, JOURNAL_MAX)
        tx["version_new_token"] = new_state
        _store_journal(tx, "PREPARED")
    except BaseException as error:
        tx["outcome"] = "abandoned"
        tx["reason"] = str(error)[:240] or "paper preparation failed"
        _store_journal(tx, "COMMITTED")
        if isinstance(error, OSError):
            raise RuntimeError("paper VERSION preparation failed") from error
        raise
    try:
        _swap_cas(
            path, swap, old, new, old_state, new_state, tx[PARENTS],
        )
        tx["outcome"] = "finalized"
        _store_journal(tx, "COMMITTED")
    except _SwapAudit as error:
        tx["reason"] = str(error)[:240]
        _store_journal(tx, "AUDIT")
        raise RuntimeError(TX_AUDIT) from error
    except BaseException as error:
        try:
            _recover_version(root, tx)
        except BaseException:
            tx["reason"] = str(error)[:240]
            _store_journal(tx, "AUDIT")
        if isinstance(error, OSError):
            raise RuntimeError("paper VERSION transaction failed") from error
        raise


def _recover_version(root, tx):
    path = _project_path(root, tx["version_path"])
    current = _read(path)
    if current == _decode(tx["version_old"]) and _matches_file(
        path, tx["version_token"], JOURNAL_MAX
    ):
        tx["outcome"] = "rolled_back"
    elif current == _decode(tx["version_new"]) and _matches_file(
        path, tx["version_new_token"], JOURNAL_MAX
    ):
        tx["outcome"] = "finalized"
    else:
        tx["reason"] = "ambiguous VERSION state"
        _store_journal(tx, "AUDIT")
        raise RuntimeError(TX_AUDIT)
    _store_journal(tx, "COMMITTED")


def _quarantine_owned(payload, tx):
    try:
        parents = tx.get(PARENTS) or _record_parents(Path(tx["record"]))
        value = os.lstat(payload)
        owned = list(_identity(value)) == tx["expected_identity"]
        if owned and tx["expected_payload"] is not None:
            owned = _read(payload, parent_states=parents) == _decode(tx["expected_payload"])
        if owned and tx["expected_tree"] is not None:
            owned = _tree_state(payload, parents) == tx["expected_tree"]
        return owned
    except (OSError, ValueError):
        return False


def _store_quarantine(tx, phase, outcome):
    tx["outcome"] = outcome
    _store_record_yaml(tx, phase, QUARANTINE_KEYS, _validate_quarantine,
                       JOURNAL_MAX, yaml.safe_dump, _durable_replace)


def _recover_quarantine(root, tx):
    path = _project_path(root, tx["path"])
    payload = Path(tx["record"]) / "payload"
    public_exists, payload_exists = os.path.lexists(path), os.path.lexists(payload)
    if not public_exists and not payload_exists:
        _store_quarantine(tx, "AUDIT", "source_state_unavailable")
        raise RuntimeError(Q_AUDIT)
    if public_exists and not payload_exists:
        _guarded_move(path, payload, _move_noreplace)
        public_exists, payload_exists = False, True
    if public_exists and payload_exists:
        tx["reason"] = "public and quarantine paths both exist"
        _store_quarantine(tx, "AUDIT", "both_retained")
        raise RuntimeError(Q_AUDIT)
    if _quarantine_owned(payload, tx):
        _store_quarantine(tx, "COMMITTED", "quarantined_owned")
        return
    try:
        _guarded_move(payload, path, _move_noreplace)
        outcome = "restored_competitor"
    except BaseException:
        outcome = "both_retained"
    _store_quarantine(tx, "AUDIT", outcome)
    raise RuntimeError(Q_AUDIT)


def _recover_unlocked(root, vault_guard):
    identities = {}
    vault = _vault(root, identities=identities, guard=vault_guard)
    if vault is None:
        return
    active = 0
    records = [vault / name for name in identities]
    if len(records) > RECORDS_MAX:
        raise RuntimeError("paper recovery vault exceeds record limit")
    for record in sorted(records, key=lambda item: item.name):
        if record.name not in identities:
            raise RuntimeError("paper recovery vault changed during scan")
        tx = (
            _empty_reservation(
                record, identities[record.name], JOURNAL_KEYS, vault_guard,
                _journal_stage,
            )
            if record.name.startswith(("tx-", "q-")) else None
        )
        if tx is not None:
            _store_journal(tx, "COMMITTED")
            continue
        tx = (
            _load_journal(record, identities.get(record.name), vault_guard)
            if record.name.startswith("tx-")
            else _load_quarantine(record, identities.get(record.name), vault_guard)
        )
        if tx["phase"] == "AUDIT":
            raise RuntimeError(TX_AUDIT)
        if tx["phase"] == "COMMITTED":
            continue
        if tx["phase"] == "PREPARING":
            tx["outcome"] = "abandoned"
            tx["reason"] = tx.get("reason") or "interrupted paper preparation"
            _store_journal(tx, "COMMITTED")
            continue
        active += 1
        if active > ACTIVE_MAX:
            raise RuntimeError("paper transaction active journal limit exceeded")
        try:
            if tx["kind"] == "QUARANTINE":
                _recover_quarantine(root, tx)
            elif tx["kind"] == "BUMP":
                _recover_bump(root, tx)
            elif tx["kind"] == "VERSION":
                _recover_version(root, tx)
            else:
                raise RuntimeError("paper transaction kind is unsupported")
        except BaseException as error:
            if tx.get("phase") != "AUDIT":
                tx["reason"] = str(error)[:240]
                _store_journal(tx, "AUDIT")
            raise RuntimeError(TX_AUDIT) from error


def recover(root):
    vault = _vault_path(root)
    if vault is None:
        return
    with _vault_lock(vault) as guard:
        _recover_unlocked(root, guard)


@_locked
def quarantine(root, path, *, expected_identity, expected_payload=None,
               expected_tree=None, label="paper compensation", source_dir_fd=-1,
               _vault_guard=None):
    record = _new_record(root, "q", _vault_guard)
    payload = record / "payload"
    document = {
        "schema_version": 1, "kind": "QUARANTINE", "operation_id": record.name[2:],
        "phase": "PREPARED", "outcome": None, "reason": label,
        "path": _relative(root, path), "expected_identity": list(expected_identity),
        "expected_payload": (
            _encode(expected_payload) if expected_payload is not None else None
        ),
        "expected_tree": expected_tree,
    }
    document["record"] = record
    document[PARENTS] = _record_parents(record)
    document["vault_guard"] = _vault_guard
    _store_quarantine(document, "PREPARED", None)
    try:
        if source_dir_fd >= 0:
            guards = _record_guards(record, document[PARENTS])
            try:
                _move_from_fd_noreplace(
                    source_dir_fd, Path(path).name, payload, guards[1]
                )
            finally:
                _close_guards(guards)
        else:
            _guarded_move(
                path, payload, _move_noreplace,
                target_expected=document[PARENTS][-1][1],
            )
    except FileNotFoundError:
        _store_quarantine(document, "COMMITTED", "absent")
        return record
    owned = _quarantine_owned(payload, document)
    if owned:
        _store_quarantine(document, "COMMITTED", "quarantined_owned")
        return record
    try:
        _guarded_move(
            payload, path, _move_noreplace,
            source_expected=document[PARENTS][-1][1],
        )
        restored = True
    except BaseException:
        restored = False
    _store_quarantine(
        document, "AUDIT", "restored_competitor" if restored else "both_retained"
    )
    raise RuntimeError("paper compensation recovery retained for audit")


def file_identity(path): return _identity(_plain_file(path, "paper transaction file"))
def directory_identity(path): return _identity(_plain_dir(path, "paper transaction directory"))
def tree_state(path): return _tree_state(path)
def read_file(path, limit=TREE_BYTES_MAX): return _read(path, limit, "paper transaction input")
def move_noreplace(source, target): return _guarded_move(source, target, _move_noreplace)
