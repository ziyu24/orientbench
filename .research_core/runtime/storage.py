from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
import tempfile

import yaml


def load_yaml(path: Path) -> dict:
    value = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    if type(value) is not dict:
        raise ValueError(f"YAML mapping required: {path}")
    return value


def project_path(root: Path, relative: str) -> Path:
    root = Path(root).resolve()
    posix = PurePosixPath(relative)
    if posix.is_absolute() or ".." in posix.parts or "\\" in relative:
        raise ValueError("project path escapes root")
    path = root.joinpath(*posix.parts)
    resolved = path.resolve()
    if resolved != root and root not in resolved.parents:
        raise ValueError("project path escapes root")
    return path


def write_text_atomic(path: Path, text: str, *, overwrite: bool) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        raise FileExistsError(path)
    handle, name = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
    try:
        with os.fdopen(handle, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text if text.endswith("\n") else text + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    except BaseException:
        try:
            os.unlink(name)
        except OSError:
            pass
        raise


def write_yaml_atomic(path: Path, value: dict, *, overwrite: bool) -> None:
    write_text_atomic(
        path,
        yaml.safe_dump(value, allow_unicode=True, sort_keys=False),
        overwrite=overwrite,
    )
