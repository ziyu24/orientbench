"""Root-confined remote workspace preparation."""

from __future__ import annotations

from pathlib import Path
import re
import shutil

from . import FabricError


RUN_DIRECTORIES = ("source", "config", "logs", "checkpoints", "outputs", "tmp")
COMPONENT = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\Z")


def _component(value: str, label: str) -> str:
    if type(value) is not str or COMPONENT.fullmatch(value) is None:
        raise FabricError(f"invalid {label}")
    return value


def _plain_directory(path: Path, label: str) -> None:
    if path.is_symlink():
        raise FabricError(f"{label} must not be a symlink")
    if path.exists() and not path.is_dir():
        raise FabricError(f"{label} must be a directory")


def prepare_workspace(root: Path, project_id: str, run_id: str) -> Path:
    root = Path(root).absolute()
    _plain_directory(root, "workspace root")
    root.mkdir(parents=True, exist_ok=True)
    root = root.resolve(strict=True)
    projects = root / "projects"
    _plain_directory(projects, "projects root")
    projects.mkdir(exist_ok=True)
    if not projects.resolve(strict=True).is_relative_to(root):
        raise FabricError("projects root escaped workspace root")
    project = projects / _component(project_id, "project id")
    _plain_directory(project, "project directory")
    project.mkdir(exist_ok=True)
    runs = project / "runs"
    _plain_directory(runs, "project runs root")
    runs.mkdir(exist_ok=True)
    if not runs.resolve(strict=True).is_relative_to(project.resolve(strict=True)):
        raise FabricError("project runs root escaped project directory")
    run = runs / _component(run_id, "run id")
    if run.exists() or run.is_symlink():
        raise FileExistsError(f"run already exists: {run_id}")
    run.mkdir()
    try:
        for name in RUN_DIRECTORIES:
            (run / name).mkdir()
        if not run.resolve(strict=True).is_relative_to(project.resolve(strict=True)):
            raise FabricError("workspace escaped project directory")
    except BaseException:
        shutil.rmtree(run, ignore_errors=True)
        raise
    return run
