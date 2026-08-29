"""Host-global, subset-scoped dataset cache for server profile 46.

The mounted server-26 tree is a discovery/copy source only.  Every execution
uses a canonical path under server 46's tmpfs cache and holds one idempotent
lease for the exact dataset subset it requested.
"""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import re
import shutil
import uuid
from typing import Iterator, Sequence

from . import FabricError


_COMPONENT = re.compile(r"[a-z0-9][a-z0-9._-]{0,127}")


def _canonical(value: str, label: str) -> str:
    if type(value) is not str:
        raise FabricError(f"invalid dataset {label}")
    canonical = value.strip().casefold()
    if canonical in {"", ".", ".."} or _COMPONENT.fullmatch(canonical) is None:
        raise FabricError(f"invalid dataset {label}")
    return canonical


def _casefold_child(parent: Path, name: str) -> Path | None:
    direct = parent / name
    if direct.exists():
        return direct
    try:
        matches = [
            item for item in parent.iterdir()
            if item.name.casefold() == name.casefold()
        ]
    except OSError:
        return None
    if len(matches) > 1:
        raise FabricError(f"ambiguous dataset path component: {name}")
    return matches[0] if matches else None


def _nonempty_directory(path: Path) -> bool:
    try:
        return path.is_dir() and next(path.iterdir(), None) is not None
    except OSError:
        return False


def _source_subset(
    source_roots: Sequence[Path], dataset_id: str, subset_id: str
) -> Path:
    for root in source_roots:
        source_root = Path(root).expanduser()
        if not source_root.is_dir():
            continue
        dataset = _casefold_child(source_root, dataset_id)
        if dataset is None or not dataset.is_dir():
            continue
        subset = _casefold_child(dataset, subset_id)
        if subset is not None and _nonempty_directory(subset):
            return subset.resolve()
    raise FabricError(
        f"official dataset subset is unavailable or empty: "
        f"{dataset_id}/{subset_id}"
    )


@contextmanager
def _file_lock(path: Path) -> Iterator[None]:
    """Use one blocking OS advisory lock per canonical subset."""

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+b") as stream:
        if os.name == "nt":
            import msvcrt

            if path.stat().st_size == 0:
                stream.write(b"0")
                stream.flush()
            stream.seek(0)
            msvcrt.locking(stream.fileno(), msvcrt.LK_LOCK, 1)
            try:
                yield
            finally:
                stream.seek(0)
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _paths(
    cache_root: Path,
    state_root: Path,
    dataset_id: str,
    subset_id: str,
) -> tuple[str, str, Path, Path, Path]:
    dataset = _canonical(dataset_id, "name")
    subset = _canonical(subset_id, "subset")
    cache = Path(cache_root).expanduser().resolve()
    state = Path(state_root).expanduser().resolve()
    target = cache / dataset / subset
    record = state / "entries" / dataset / f"{subset}.json"
    lock = state / "locks" / f"{dataset}--{subset}.lock"
    return dataset, subset, target, record, lock


def _load_record(path: Path) -> dict[str, object] | None:
    if not path.exists():
        return None
    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise FabricError("dataset cache state is unreadable") from error
    if (
        type(document) is not dict
        or document.get("schema_version") != 1
        or document.get("state") not in {"COPYING", "READY"}
        or type(document.get("dataset_id")) is not str
        or type(document.get("subset_id")) is not str
        or type(document.get("leases")) is not list
        or any(type(item) is not str or not item for item in document["leases"])
    ):
        raise FabricError("dataset cache state is invalid")
    return document


def _write_record(path: Path, document: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(document, stream, ensure_ascii=True, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def acquire_subset(
    *,
    source_roots: Sequence[Path],
    cache_root: Path,
    state_root: Path,
    dataset_id: str,
    subset_id: str,
    lease_id: str,
) -> dict[str, object]:
    """Copy or hit one exact subset and add one idempotent project/run lease."""

    if type(lease_id) is not str or not lease_id.strip() or len(lease_id) > 255:
        raise FabricError("invalid dataset cache lease")
    dataset, subset, target, record_path, lock_path = _paths(
        cache_root, state_root, dataset_id, subset_id
    )
    with _file_lock(lock_path):
        record = _load_record(record_path)
        if target.exists():
            if record is None:
                raise FabricError(
                    f"unmanaged dataset cache target already exists: {dataset}/{subset}"
                )
            if (
                record["dataset_id"] != dataset
                or record["subset_id"] != subset
                or not _nonempty_directory(target)
            ):
                raise FabricError("dataset cache target does not match its state")
            record["state"] = "READY"
            leases = set(record["leases"])
            leases.add(lease_id)
            record["leases"] = sorted(leases)
            _write_record(record_path, record)
            return {
                "dataset_id": dataset,
                "version": subset,
                "subset_id": subset,
                "local_path": str(target.resolve()),
                "status": "CACHE_HIT",
                "lease_id": lease_id,
                "use_count": len(leases),
            }
        if record is not None:
            if record["state"] != "COPYING":
                raise FabricError("dataset cache state exists without its target")
            # A prior copier stopped before atomic publication.  Its exact
            # hidden temporary directory is safe to discard under this key lock.
            for stale in target.parent.glob(f".{subset}.copy-*"):
                if stale.is_dir() and not stale.is_symlink():
                    shutil.rmtree(stale)
            record_path.unlink(missing_ok=True)

        source = _source_subset(source_roots, dataset, subset)
        target.parent.mkdir(parents=True, exist_ok=True)
        temporary = target.parent / f".{subset}.copy-{uuid.uuid4().hex}"
        record = {
            "schema_version": 1,
            "state": "COPYING",
            "dataset_id": dataset,
            "subset_id": subset,
            "source_path": str(source),
            "leases": [lease_id],
        }
        _write_record(record_path, record)
        try:
            shutil.copytree(source, temporary, symlinks=False)
            if not _nonempty_directory(temporary):
                raise FabricError("copied dataset subset is empty")
            os.replace(temporary, target)
        except BaseException:
            record_path.unlink(missing_ok=True)
            raise
        finally:
            if temporary.exists():
                shutil.rmtree(temporary)
        record["state"] = "READY"
        _write_record(record_path, record)
        return {
            "dataset_id": dataset,
            "version": subset,
            "subset_id": subset,
            "local_path": str(target.resolve()),
            "status": "COPIED",
            "lease_id": lease_id,
            "use_count": 1,
        }


def release_subset(
    *,
    cache_root: Path,
    state_root: Path,
    dataset_id: str,
    subset_id: str,
    lease_id: str,
) -> dict[str, object]:
    """Drop one lease and evict only this subset when its count reaches zero."""

    dataset, subset, target, record_path, lock_path = _paths(
        cache_root, state_root, dataset_id, subset_id
    )
    with _file_lock(lock_path):
        record = _load_record(record_path)
        if record is None:
            if target.exists():
                raise FabricError("unmanaged dataset cache target cannot be released")
            return {"status": "NOT_HELD", "use_count": 0}
        leases = set(record["leases"])
        if lease_id not in leases:
            return {"status": "NOT_HELD", "use_count": len(leases)}
        leases.remove(lease_id)
        if leases:
            record["leases"] = sorted(leases)
            _write_record(record_path, record)
            return {"status": "RETAINED", "use_count": len(leases)}
        if target.exists():
            if target.is_symlink() or not target.is_dir():
                raise FabricError("dataset cache target is not a plain directory")
            shutil.rmtree(target)
        for stale in target.parent.glob(f".{subset}.copy-*"):
            if stale.is_dir() and not stale.is_symlink():
                shutil.rmtree(stale)
        record_path.unlink(missing_ok=True)
        try:
            target.parent.rmdir()
        except OSError:
            pass
        return {"status": "EVICTED", "use_count": 0}


def reconcile(
    *, cache_root: Path, state_root: Path, active_lease_ids: set[str]
) -> list[dict[str, object]]:
    """Drop leases not present in the caller's authoritative active-run set."""

    if type(active_lease_ids) is not set or any(
        type(item) is not str for item in active_lease_ids
    ):
        raise FabricError("invalid active dataset lease set")
    entries = Path(state_root).expanduser().resolve() / "entries"
    if not entries.exists():
        return []
    results: list[dict[str, object]] = []
    for path in sorted(entries.glob("*/*.json")):
        record = _load_record(path)
        if record is None:
            continue
        for lease in sorted(set(record["leases"]) - active_lease_ids):
            results.append(
                release_subset(
                    cache_root=cache_root,
                    state_root=state_root,
                    dataset_id=str(record["dataset_id"]),
                    subset_id=str(record["subset_id"]),
                    lease_id=lease,
                )
            )
    return results
