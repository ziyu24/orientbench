"""Host-global single-server execution and asset runtime."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml


API_VERSION = "2.1"


class FabricError(ValueError):
    """Raised when a local resource operation fails closed."""


def _json(value) -> None:
    payload = {"api_version": API_VERSION, **value}
    payload["api_version"] = API_VERSION
    print(json.dumps(payload, ensure_ascii=True, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    try:
        return _main(argv)
    except (
        FabricError,
        FileExistsError,
        FileNotFoundError,
        OSError,
        UnicodeError,
        yaml.YAMLError,
    ) as error:
        print(f"ERROR: {error}", file=__import__("sys").stderr)
        return 2


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="cqc-fabric")
    parser.add_argument("--api-version", action="store_true")
    commands = parser.add_subparsers(dest="command")

    local = commands.add_parser("local")
    local_commands = local.add_subparsers(dest="action", required=True)
    paths = local_commands.add_parser("paths")
    paths.add_argument("--profile", choices=("26", "46"), required=True)
    paths.add_argument("--dataset-root")
    resolve = local_commands.add_parser("resolve-datasets")
    resolve.add_argument("--profile", choices=("26", "46"), required=True)
    resolve.add_argument("--requirements", type=Path, required=True)
    resolve.add_argument("--dataset-root")
    download = local_commands.add_parser("check-download-target")
    download.add_argument("--profile", choices=("26", "46"), required=True)
    download.add_argument("--target", type=Path, required=True)
    reconcile = local_commands.add_parser("reconcile-cache")
    reconcile.add_argument("--profile", choices=("46",), required=True)
    reconcile.add_argument("--active-leases", type=Path, required=True)
    reconcile.add_argument("--cache-root", type=Path)
    reconcile.add_argument("--cache-state-root", type=Path)

    gpu = commands.add_parser("gpu")
    gpu_commands = gpu.add_subparsers(dest="action", required=True)
    gpu_select = gpu_commands.add_parser("select")
    gpu_select.add_argument("--count", type=int, required=True)
    gpu_select.add_argument("--memory-mib", type=float, default=0)

    workspace = commands.add_parser("workspace")
    workspace_commands = workspace.add_subparsers(dest="action", required=True)
    prepare = workspace_commands.add_parser("prepare")
    prepare.add_argument("--root", type=Path, required=True)
    prepare.add_argument("--project-id", required=True)
    prepare.add_argument("--run-id", required=True)

    artifacts = commands.add_parser("artifacts")
    artifact_commands = artifacts.add_subparsers(dest="action", required=True)
    for name in ("validate", "rebuild-check"):
        item = artifact_commands.add_parser(name)
        item.add_argument("--manifest", type=Path, required=True)
        item.add_argument("--manifests-root", type=Path, required=True)
    mark = artifact_commands.add_parser("mark-missing")
    mark.add_argument("--manifest", type=Path, required=True)
    mark.add_argument(
        "--status", choices=("MISSING", "DELETED", "REBUILD_REQUIRED"), required=True
    )
    mark.add_argument("--note", required=True)

    arguments = parser.parse_args(argv)
    if arguments.api_version:
        _json({})
        return 0
    if arguments.command is None:
        parser.error("a command is required")

    from . import artifacts as artifact_runtime
    from . import dataset_cache
    from . import local_execution
    from . import workspace as workspace_runtime

    if arguments.command == "local":
        if arguments.action == "paths":
            _json(
                local_execution.profile_paths(
                    arguments.profile, dataset_root=arguments.dataset_root
                )
            )
        elif arguments.action == "resolve-datasets":
            document = yaml.safe_load(arguments.requirements.read_text(encoding="utf-8"))
            requirements = document.get("datasets") if type(document) is dict else document
            if type(requirements) is not list:
                raise FabricError("dataset requirements must be a list")
            _json(
                {
                    "items": local_execution.resolve_datasets(
                        arguments.profile,
                        requirements,
                        dataset_root=arguments.dataset_root,
                    )
                }
            )
        elif arguments.action == "check-download-target":
            target = local_execution.assert_download_target(
                arguments.profile, arguments.target
            )
            _json({"status": "VALID", "target": str(target)})
        else:
            document = yaml.safe_load(
                arguments.active_leases.read_text(encoding="utf-8")
            )
            leases = (
                document.get("active_leases")
                if type(document) is dict
                else document
            )
            if type(leases) is not list or any(
                type(item) is not str or not item for item in leases
            ):
                raise FabricError("active dataset leases must be a string list")
            paths = local_execution.profile_paths("46")
            results = dataset_cache.reconcile(
                cache_root=arguments.cache_root or Path(str(paths["download_root"])),
                state_root=(
                    arguments.cache_state_root
                    or Path(str(paths["cache_state_root"]))
                ),
                active_lease_ids=set(leases),
            )
            _json({"status": "RECONCILED", "results": results})
        return 0
    if arguments.command == "gpu":
        _json(
            {
                "status": "SELECTED",
                "device_indexes": local_execution.select_gpus(
                    arguments.count, arguments.memory_mib
                ),
            }
        )
        return 0
    if arguments.command == "workspace":
        path = workspace_runtime.prepare_workspace(
            arguments.root, arguments.project_id, arguments.run_id
        )
        _json({"status": "PREPARED", "path": str(path)})
        return 0
    if arguments.command == "artifacts":
        if arguments.action == "mark-missing":
            _json(
                artifact_runtime.mark_missing(
                    arguments.manifest,
                    status=arguments.status,
                    note=arguments.note,
                )
            )
        else:
            document = artifact_runtime.load_manifest(
                arguments.manifest, manifests_root=arguments.manifests_root
            )
            if arguments.action == "rebuild-check" and not document["rebuildable"]:
                raise FabricError("artifact is not rebuildable")
            _json(document)
        return 0
    raise FabricError("unsupported command")
