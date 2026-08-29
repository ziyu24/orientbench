from __future__ import annotations

from contextlib import contextmanager
import os
from pathlib import Path
import re
import subprocess
import threading
from typing import Iterator


INSTRUCTION_ID = re.compile(r"r[0-9]{3,}\Z")
_REGISTRY_GUARD = threading.Lock()
_THREAD_LOCKS: dict[str, threading.RLock] = {}
_HELD = threading.local()


def _git_common_dir(root: Path) -> Path:
    root = Path(root).resolve()
    completed = subprocess.run(
        ["git", "rev-parse", "--git-common-dir"], cwd=root,
        capture_output=True, text=True, encoding="utf-8", check=False,
        shell=False,
    )
    if completed.returncode != 0:
        return root / ".research_core"
    value = completed.stdout.strip()
    path = Path(value)
    return (path if path.is_absolute() else root / path).resolve()


def _thread_lock(path: Path) -> threading.RLock:
    identity = str(path)
    with _REGISTRY_GUARD:
        return _THREAD_LOCKS.setdefault(identity, threading.RLock())


def _lock_descriptor(path: Path) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink() or not path.parent.is_dir() or path.is_symlink():
        raise ValueError("transaction lock path is invalid")
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_CLOEXEC", 0)
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    try:
        if os.name == "nt":
            import msvcrt

            if os.fstat(descriptor).st_size == 0:
                os.write(descriptor, b"0")
                os.fsync(descriptor)
            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_LOCK, 1)
        else:
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_EX)
    except BaseException:
        os.close(descriptor)
        raise
    return descriptor


def _unlock_descriptor(descriptor: int) -> None:
    try:
        if os.name == "nt":
            import msvcrt

            os.lseek(descriptor, 0, os.SEEK_SET)
            msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


@contextmanager
def _advisory_lock(path: Path) -> Iterator[None]:
    path = Path(path).resolve()
    identity = str(path)
    local_lock = _thread_lock(path)
    with local_lock:
        held = getattr(_HELD, "paths", None)
        if held is None:
            held = {}
            _HELD.paths = held
        if identity in held:
            descriptor, depth = held[identity]
            next_depth = depth + 1
            held[identity] = (descriptor, next_depth)
            try:
                yield
            finally:
                descriptor, depth = held[identity]
                if depth == 1:
                    raise RuntimeError("transaction lock recursion state is invalid")
                next_depth = depth - 1
                held[identity] = (descriptor, next_depth)
            return
        descriptor = _lock_descriptor(path)
        initial_depth = 1
        held[identity] = (descriptor, initial_depth)
        try:
            yield
        finally:
            current_descriptor, depth = held.pop(identity)
            if current_descriptor != descriptor or depth != 1:
                raise RuntimeError("transaction lock ownership changed")
            _unlock_descriptor(descriptor)


@contextmanager
def project_control(root: Path) -> Iterator[None]:
    """Linearize project lock, sensitive settings and SERVER claim per clone."""

    path = _git_common_dir(root) / "cqc-project-operation-lock"
    with _advisory_lock(path):
        yield


@contextmanager
def journal(root: Path, instruction_id: str) -> Iterator[None]:
    """Serialize every read-modify-write of one durable execution journal."""

    if type(instruction_id) is not str or INSTRUCTION_ID.fullmatch(instruction_id) is None:
        raise ValueError("invalid r-prefixed instruction id")
    path = (
        _git_common_dir(root)
        / "cqc-execution"
        / instruction_id
        / "JOURNAL.lock"
    )
    with _advisory_lock(path):
        yield
