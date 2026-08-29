from __future__ import annotations

import base64
import ctypes
import errno
import itertools
import os
from pathlib import Path
import re
import secrets
import stat
import sys


RENAME_EXCHANGE = 2
JOURNAL_STAGE = re.compile(r"\.journal\.yaml-[0-9a-f]{16}\Z")


class _SwapAudit(RuntimeError):
    pass


def _journal_stage(name):
    return type(name) is str and JOURNAL_STAGE.fullmatch(name) is not None


def _swap_files_cas(
    path, swap, old, new, old_state, new_state, swap_parents, limit,
    matches, read, file_state, guarded_exchange, exchange,
):
    record_identity = swap_parents[-1][1] if swap_parents else None
    def swap_read():
        return read(swap, limit, parent_states=swap_parents)
    guarded_exchange(path, swap, exchange, right_expected=record_identity)
    public_new = matches(path, new_state, limit) and read(path, limit) == new
    swap_old = matches(swap, old_state, limit, swap_parents) and swap_read() == old
    if public_new and swap_old:
        return
    if public_new:
        competitor_state, competitor = file_state(swap, limit, swap_parents), swap_read()
        if not (
            matches(path, new_state, limit) and read(path, limit) == new
            and matches(swap, competitor_state, limit, swap_parents)
            and swap_read() == competitor
        ):
            raise _SwapAudit("paper exchange changed during competitor recovery")
        try:
            guarded_exchange(path, swap, exchange, right_expected=record_identity)
        except BaseException as error:
            raise _SwapAudit("paper competitor exchange recovery failed") from error
        if not (matches(path, competitor_state, limit) and read(path, limit) == competitor):
            raise _SwapAudit("paper competitor recovery requires audit")
        raise _SwapAudit("paper pre-exchange competitor was restored")
    raise _SwapAudit("paper post-exchange state requires audit")


def _encode(payload):
    return base64.b64encode(payload).decode("ascii")


def _decode(value):
    if type(value) is not str:
        raise ValueError("paper journal bytes are invalid")
    try:
        return base64.b64decode(value, validate=True)
    except ValueError as error:
        raise ValueError("paper journal bytes are invalid") from error


def _allocate_record(
    root, prefix, vault_getter, record_limit, fsync_dir, vault_guard=None,
):
    if vault_guard is not None:
        return _allocate_guarded(
            vault_guard.path, vault_guard, prefix, record_limit
        )
    vault = vault_getter(root, create=True)
    with _guard_directory(vault) as guard, _capacity_lock(guard):
        return _allocate_guarded(vault, guard, prefix, record_limit)


def _allocate_guarded(vault, guard, prefix, record_limit):
    names = os.listdir(guard.fd) if guard.fd >= 0 else os.listdir(vault)
    existing = [name for name in names if name != "capacity.lock"]
    if len(existing) >= record_limit:
        raise RuntimeError("paper recovery record capacity limit reached")
    for _ in range(32):
        name = f"{prefix}-{secrets.token_hex(16)}"
        try:
            if guard.fd >= 0:
                os.mkdir(name, dir_fd=guard.fd)
                os.fsync(guard.fd)
            else:
                os.mkdir(Path(vault) / name)
            return Path(vault) / name
        except FileExistsError:
            continue
    raise RuntimeError("paper recovery id allocation failed")


def _locate_vault(root, recovery_dir, create=False):
    vault = recovery_dir(root) / "cqc-paper-recovery"
    if not os.path.lexists(vault):
        if not create:
            return None
        try:
            os.mkdir(vault)
        except FileExistsError:
            pass
    return vault


def _empty_reservation(
    record, identity, keys, vault_guard=None, stage_check=None,
):
    names = _guarded_names(record, identity, 15, vault_guard)
    if names and (stage_check is None or any(not stage_check(name) for name in names)):
        return None
    offset = 3 if record.name.startswith("tx-") else 2
    operation = record.name[offset:]
    if len(operation) != 32 or any(
        character not in "0123456789abcdef" for character in operation
    ):
        raise RuntimeError("paper reservation record name is invalid")
    tx = {key: None for key in keys}
    tx.update({
        "schema_version": 1, "kind": "RESERVATION", "operation_id": operation,
        "phase": "COMMITTED", "outcome": "abandoned",
        "reason": "empty paper reservation abandoned", "record": record,
        "record_parents": (
            (record.parent, identity[0]), (record, identity[1]),
        ),
        "vault_guard": vault_guard,
    })
    return tx


def _identity(value):
    return (value.st_dev, value.st_ino, stat.S_IFMT(value.st_mode))


def _snapshot(value):
    return _identity(value) + (
        value.st_size, value.st_mtime_ns, value.st_ctime_ns,
    )


class _DirectoryGuard:
    def __init__(self, path, parent=None):
        self.path = Path(path)
        before = os.lstat(self.path)
        if not stat.S_ISDIR(before.st_mode) or _path_reparse(self.path, before):
            raise ValueError("paper transaction guard requires a plain directory")
        self.identity = _identity(before)
        self.fd = -1
        self.handle = None
        if os.name == "nt":
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            function = kernel.CreateFileW
            function.argtypes = [
                ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32,
                ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
            ]
            function.restype = ctypes.c_void_p
            handle = function(str(self.path), 0x80000000, 0x3, None, 3, 0x02200000, None)
            if handle in {None, ctypes.c_void_p(-1).value}:
                raise OSError(ctypes.get_last_error(), "paper directory guard open failed")
            self.handle = handle
            try:
                reparse = _win_handle_reparse(handle)
            except BaseException:
                self.close()
                raise
            if reparse:
                self.close()
                raise ValueError("paper transaction guard rejects a reparse directory")
        else:
            flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
            flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
            self.fd = (
                os.open(self.path.name, flags, dir_fd=parent.fd)
                if parent is not None else os.open(self.path, flags)
            )
            if _identity(os.fstat(self.fd)) != self.identity:
                self.close()
                raise ValueError("paper directory guard identity changed")
        self.check()

    def check(self):
        if _identity(os.lstat(self.path)) != self.identity:
            raise ValueError("paper directory guard identity changed")
        return self.identity

    def close(self):
        if self.fd >= 0:
            os.close(self.fd)
            self.fd = -1
        if self.handle is not None:
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            kernel.CloseHandle.restype = ctypes.c_int
            kernel.CloseHandle(self.handle)
            self.handle = None

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()


def _guard_directory(path, parent=None):
    return _DirectoryGuard(path, parent)


def _list_guarded(guard, limit):
    guard.check()
    names = os.listdir(guard.fd) if guard.fd >= 0 else os.listdir(guard.path)
    if len(names) > limit:
        raise RuntimeError("paper guarded directory exceeds entry limit")
    guard.check()
    return names


def _path_reparse(path, value=None):
    value = os.lstat(path) if value is None else value
    return (
        Path(path).is_symlink()
        or getattr(Path(path), "is_junction", lambda: False)()
        or bool(getattr(value, "st_file_attributes", 0) & 0x400)
    )


def _win_handle_reparse(handle):
    class _TagInfo(ctypes.Structure):
        _fields_ = [("attributes", ctypes.c_uint32), ("tag", ctypes.c_uint32)]
    info = _TagInfo()
    function = ctypes.WinDLL("kernel32", use_last_error=True).GetFileInformationByHandleEx
    function.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_void_p, ctypes.c_uint32]
    function.restype = ctypes.c_int
    if not function(handle, 9, ctypes.byref(info), ctypes.sizeof(info)):
        raise OSError(ctypes.get_last_error(), "paper reparse metadata read failed")
    return bool(info.attributes & 0x400)


def _win_leaf_fd(path):
    import msvcrt
    function = ctypes.WinDLL("kernel32", use_last_error=True).CreateFileW
    function.argtypes = [
        ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
        ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
    ]
    function.restype = ctypes.c_void_p
    handle = function(str(path), 0x80000000, 0x3, None, 3, 0x00200000, None)
    if handle in {None, ctypes.c_void_p(-1).value}:
        raise OSError(ctypes.get_last_error(), "paper guarded leaf open failed")
    try:
        if _win_handle_reparse(handle):
            raise ValueError("paper guarded leaf rejects a reparse point")
        descriptor = msvcrt.open_osfhandle(
            handle, os.O_RDONLY | getattr(os, "O_BINARY", 0)
        )
        handle = None
        return descriptor
    finally:
        if handle is not None:
            kernel = ctypes.WinDLL("kernel32", use_last_error=True)
            kernel.CloseHandle.argtypes = [ctypes.c_void_p]
            kernel.CloseHandle.restype = ctypes.c_int
            kernel.CloseHandle(handle)


def _leaf_snapshot(guard, name):
    guard.check()
    path = guard.path / name
    value = (
        os.stat(name, dir_fd=guard.fd, follow_symlinks=False)
        if guard.fd >= 0 else os.lstat(path)
    )
    if not stat.S_ISREG(value.st_mode) or (
        os.name == "nt" and _path_reparse(path, value)
    ):
        raise ValueError("paper guarded leaf must be a plain file")
    result = _snapshot(value)
    guard.check()
    return result


def _read_guarded(guard, name, limit):
    if type(name) is not str or Path(name).name != name:
        raise ValueError("paper guarded leaf name is invalid")
    flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    guard.check()
    descriptor = (
        os.open(name, flags, dir_fd=guard.fd) if guard.fd >= 0
        else _win_leaf_fd(guard.path / name) if os.name == "nt"
        else os.open(guard.path / name, flags)
    )
    before = path_before = None
    try:
        before_value = os.fstat(descriptor)
        if not stat.S_ISREG(before_value.st_mode):
            raise ValueError("paper guarded leaf must be a plain file")
        before = _snapshot(before_value)
        path_before = _leaf_snapshot(guard, name)
        if path_before[:3] != before[:3]:
            raise ValueError("paper guarded leaf changed during open")
        chunks = []
        total = 0
        while total <= limit:
            chunk = os.read(descriptor, min(65536, limit + 1 - total))
            if not chunk:
                break
            chunks.append(chunk)
            total += len(chunk)
        payload = b"".join(chunks)
        after = _snapshot(os.fstat(descriptor))
        if after != before or _leaf_snapshot(guard, name) != path_before:
            raise ValueError("paper guarded leaf snapshot changed")
        if len(payload) > limit:
            raise ValueError("paper guarded leaf changed or exceeds size limit")
    finally:
        os.close(descriptor)
        if path_before is not None and _leaf_snapshot(guard, name) != path_before:
            raise ValueError("paper guarded leaf snapshot changed after close")
    guard.check()
    return payload


def _write_guarded(guard, name, payload):
    if type(name) is not str or Path(name).name != name:
        raise ValueError("paper guarded leaf name is invalid")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    guard.check()
    descriptor = (
        os.open(name, flags, 0o600, dir_fd=guard.fd)
        if guard.fd >= 0 else os.open(guard.path / name, flags, 0o600)
    )
    try:
        _write_descriptor(descriptor, payload)
    finally:
        os.close(descriptor)
    guard.check()


def _write_descriptor(descriptor, payload):
    view = memoryview(payload)
    while view:
        written = os.write(descriptor, view)
        if written <= 0:
            raise OSError("short paper transaction write")
        view = view[written:]
    os.fsync(descriptor)


def _write_all(path, payload):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_BINARY", 0)
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags, 0o600)
    try:
        _write_descriptor(descriptor, payload)
    finally:
        os.close(descriptor)


def _move_guarded_leaf(guard, source_name, target_name):
    if os.name == "nt":
        raise RuntimeError("paper guarded leaf move is unavailable on Windows")
    for name in (source_name, target_name):
        if type(name) is not str or Path(name).name != name:
            raise ValueError("paper guarded leaf name is invalid")
    library = ctypes.CDLL(None, use_errno=True)
    if sys.platform.startswith("linux"):
        function = getattr(library, "renameat2", None)
        args = (guard.fd, os.fsencode(source_name), guard.fd, os.fsencode(target_name), 1)
    elif sys.platform == "darwin":
        function = getattr(library, "renameatx_np", None)
        args = (guard.fd, os.fsencode(source_name), guard.fd, os.fsencode(target_name), 4)
    else:
        function = None
    if function is None:
        raise RuntimeError("paper guarded leaf move primitive is unavailable")
    function.argtypes = [
        ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
    ]
    function.restype = ctypes.c_int
    if function(*args) != 0:
        code = ctypes.get_errno()
        if code in {errno.EEXIST, errno.ENOTEMPTY}:
            raise FileExistsError(code, os.strerror(code), target_name)
        raise RuntimeError("paper guarded leaf move failed closed")
    os.fsync(guard.fd)


def _guarded_move(
    source, target, windows_mover, source_expected=None, target_expected=None,
):
    source, target = Path(source), Path(target)
    with _guard_directory(source.parent) as left, _guard_directory(target.parent) as right:
        if source_expected is not None and left.identity != source_expected:
            raise RuntimeError("paper guarded source parent changed")
        if target_expected is not None and right.identity != target_expected:
            raise RuntimeError("paper guarded target parent changed")
        if left.identity[0] != right.identity[0]:
            raise ValueError("paper transaction paths cross filesystems")
        if os.name == "nt":
            result = windows_mover(source, target)
            left.check()
            right.check()
            return result
        library = ctypes.CDLL(None, use_errno=True)
        if sys.platform.startswith("linux"):
            function = getattr(library, "renameat2", None)
            args = (left.fd, os.fsencode(source.name), right.fd, os.fsencode(target.name), 1)
        elif sys.platform == "darwin":
            function = getattr(library, "renameatx_np", None)
            args = (left.fd, os.fsencode(source.name), right.fd, os.fsencode(target.name), 4)
        else:
            function = None
        if function is None:
            raise RuntimeError("paper guarded move primitive is unavailable")
        function.argtypes = [
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
        ]
        function.restype = ctypes.c_int
        if function(*args) != 0:
            code = ctypes.get_errno()
            if code in {errno.EEXIST, errno.ENOTEMPTY}:
                raise FileExistsError(code, os.strerror(code), target)
            raise RuntimeError("paper guarded move failed closed")
        os.fsync(left.fd)
        if right.fd != left.fd:
            os.fsync(right.fd)


def _guarded_exchange(
    left_path, right_path, windows_exchange, left_expected=None, right_expected=None,
):
    left_path, right_path = Path(left_path), Path(right_path)
    with _guard_directory(left_path.parent) as left, _guard_directory(right_path.parent) as right:
        if left_expected is not None and left.identity != left_expected:
            raise RuntimeError("paper guarded exchange parent changed")
        if right_expected is not None and right.identity != right_expected:
            raise RuntimeError("paper guarded exchange parent changed")
        if left.identity[0] != right.identity[0]:
            raise ValueError("paper transaction exchange crosses filesystems")
        if os.name == "nt":
            result = windows_exchange(left_path, right_path)
            left.check()
            right.check()
            return result
        library = ctypes.CDLL(None, use_errno=True)
        if sys.platform.startswith("linux"):
            function = getattr(library, "renameat2", None)
            args = (
                left.fd, os.fsencode(left_path.name), right.fd,
                os.fsencode(right_path.name), RENAME_EXCHANGE,
            )
        elif sys.platform == "darwin":
            function = getattr(library, "renameatx_np", None)
            args = (left.fd, os.fsencode(left_path.name), right.fd, os.fsencode(right_path.name), 2)
        else:
            function = None
        if function is None:
            raise RuntimeError("paper guarded exchange primitive is unavailable")
        function.argtypes = [
            ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint,
        ]
        function.restype = ctypes.c_int
        if function(*args) != 0:
            raise RuntimeError("paper guarded exchange failed closed")
        os.fsync(left.fd)
        if right.fd != left.fd:
            os.fsync(right.fd)


class _CapacityLock:
    def __init__(self, vault_guard):
        flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
        self.fd = (
            os.open("capacity.lock", flags, 0o600, dir_fd=vault_guard.fd)
            if vault_guard.fd >= 0
            else os.open(vault_guard.path / "capacity.lock", flags, 0o600)
        )
        if os.name == "nt":
            import msvcrt
            os.lseek(self.fd, 0, os.SEEK_SET)
            msvcrt.locking(self.fd, msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(self.fd, fcntl.LOCK_EX)

    def close(self):
        if self.fd < 0:
            return
        if os.name == "nt":
            import msvcrt
            os.lseek(self.fd, 0, os.SEEK_SET)
            msvcrt.locking(self.fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(self.fd, fcntl.LOCK_UN)
        os.close(self.fd)
        self.fd = -1

    def __enter__(self):
        return self

    def __exit__(self, *unused):
        self.close()


def _capacity_lock(vault_guard):
    return _CapacityLock(vault_guard)


class _VaultLock:
    def __init__(self, vault):
        self.guard = _guard_directory(vault)
        self.lock = None

    def __enter__(self):
        try:
            self.lock = _capacity_lock(self.guard)
            self.lock.__enter__()
            return self.guard
        except BaseException:
            self.guard.close()
            raise

    def __exit__(self, *unused):
        if self.lock is not None:
            self.lock.close()
        self.guard.close()


def _vault_lock(vault):
    return _VaultLock(vault)


def _transactional(function, vault_getter, recover_getter):
    def call(root, *args, **kwargs):
        vault = vault_getter(root, create=True)
        with _vault_lock(vault) as guard:
            recover_getter()(root, guard)
            kwargs["_vault_guard"] = guard
            return function(root, *args, **kwargs)
    return call


def _record_parents(record, expected=None):
    record = Path(record)
    current = (
        _identity(os.lstat(record.parent)), _identity(os.lstat(record)),
    )
    if expected is not None and current != expected:
        raise RuntimeError("paper recovery record ancestry changed")
    return ((record.parent, current[0]), (record, current[1]))


def _record_guards(record, expected=None, parent=None):
    record = Path(record)
    vault_guard = parent if parent is not None else _guard_directory(record.parent)
    owned_parent = parent is None
    record_guard = None
    try:
        record_guard = _guard_directory(record, vault_guard)
        current = (vault_guard.identity, record_guard.identity)
        if expected is not None and isinstance(expected[0][0], Path):
            expected = tuple(item[1] for item in expected)
        if expected is not None and current != expected:
            raise RuntimeError("paper recovery record ancestry changed")
        return vault_guard, record_guard
    except BaseException:
        if record_guard is not None:
            record_guard.close()
        if owned_parent:
            vault_guard.close()
        raise


def _close_guards(guards):
    guards[1].close()
    guards[0].close()


def _guarded_names(record, expected, limit, vault_guard=None):
    guards = _record_guards(record, expected, vault_guard)
    try:
        names = os.listdir(guards[1].fd) if guards[1].fd >= 0 else os.listdir(record)
        if len(names) > limit:
            raise RuntimeError("paper recovery record exceeds entry limit")
        guards[1].check()
        return names
    finally:
        guards[1].close()
        if vault_guard is None:
            guards[0].close()


def _write_record_blob(record, expected, name, payload, vault_guard=None):
    guards = _record_guards(record, expected, vault_guard)
    try:
        _write_guarded(guards[1], name, payload)
    finally:
        guards[1].close()
        if vault_guard is None:
            guards[0].close()


def _store_record_yaml(
    tx, phase, keys, validator, limit, yaml_dump, durable_replace,
):
    document = {key: value for key, value in tx.items() if key in keys}
    document["phase"] = phase
    validator(document, Path(tx["record"]))
    payload = yaml_dump(document, sort_keys=True).encode("utf-8")
    if len(payload) > limit:
        raise ValueError("paper transaction journal exceeds size limit")
    vault_guard = tx.get("vault_guard")
    guards = _record_guards(
        Path(tx["record"]), tx.get("record_parents"), vault_guard
    )
    try:
        guards[0].check()
        durable_replace(Path(tx["record"]) / "journal.yaml", payload, guards[1])
    finally:
        guards[1].close()
        if vault_guard is None:
            guards[0].close()
    tx["phase"] = phase
