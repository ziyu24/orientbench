"""Single-host resource routing for project-bound SERVER execution.

The coordinator never discovers hosts and this module never opens a network
connection.  A SERVER process identifies its own fixed profile, resolves local
official data, and chooses local NVIDIA devices immediately before execution.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
from typing import Any, Callable, Mapping

from . import FabricError


GPU_COUNTS = {1, 2, 4}
PROFILES: dict[str, dict[str, object]] = {
    "26": {
        "dataset_roots": (
            "/home/rspip/cqc/data/dataset",
            "/dev/shm/cqc/data/dataset",
        ),
        "download_root": "/dev/shm/cqc/data/dataset",
        "pth_readme": "/home/rspip/cqc/study/pth_data/readme.md",
    },
    "46": {
        # The mounted 26 tree is a discovery/copy source, never an execution path.
        "dataset_roots": (
            "/home/rspip/cqc/data/dataset",
            "/dev/shm/zy/data/dataset",
        ),
        "source_roots": ("/home/rspip/cqc/data/dataset",),
        "download_root": "/dev/shm/zy/data/dataset",
        "cache_state_root": "/dev/shm/zy/data/.cqc-dataset-cache",
        "pth_readme": "/home/rspip/zy/study/pth_data/readme.md",
    },
}


def detect_profile(project_root: Path, configured: str | None = None) -> str:
    """Resolve the one local server profile; never inspect a peer node."""

    if configured is not None:
        profile = configured.strip()
        if profile not in PROFILES:
            raise FabricError("cqc.server-profile must be 26 or 46")
        return profile
    normalized = Path(project_root).resolve().as_posix().casefold()
    if "/zy/" in normalized:
        return "46"
    if "/cqc/" in normalized:
        return "26"
    raise FabricError(
        "cannot infer this project's fixed server profile; set local Git setting "
        "cqc.server-profile to 26 or 46"
    )


def profile_paths(
    profile: str, *, dataset_root: str | Path | None = None
) -> dict[str, object]:
    if profile not in PROFILES:
        raise FabricError("invalid local server profile")
    configured = PROFILES[profile]
    roots = list(configured["dataset_roots"])
    if dataset_root is not None:
        override = Path(dataset_root).expanduser()
        if not override.is_absolute():
            raise FabricError("cqc.dataset-root must be absolute")
        roots.insert(0, str(override))
    # Preserve order while avoiding a repeated mounted/default root.
    roots = list(dict.fromkeys(roots))
    return {
        "profile": profile,
        "dataset_roots": roots,
        "source_roots": (
            [str(Path(dataset_root).expanduser())]
            if dataset_root is not None and profile == "46"
            else list(configured.get("source_roots", roots))
        ),
        "download_root": configured["download_root"],
        "cache_state_root": configured.get("cache_state_root"),
        "pth_readme": configured["pth_readme"],
    }


def _casefold_child(parent: Path, name: str) -> Path | None:
    direct = parent / name
    if direct.exists():
        return direct
    try:
        matches = [item for item in parent.iterdir() if item.name.casefold() == name.casefold()]
    except OSError:
        return None
    if len(matches) > 1:
        raise FabricError(f"ambiguous local dataset directory: {name}")
    return matches[0] if matches else None


def _resolve_one(roots: list[str], dataset_id: str, version: str) -> Path:
    for root_text in roots:
        root = Path(root_text).expanduser()
        if not root.is_dir():
            continue
        dataset = _casefold_child(root, dataset_id)
        if dataset is None:
            continue
        versioned = _casefold_child(dataset, version) if dataset.is_dir() else None
        candidate = versioned if versioned is not None else dataset
        try:
            if candidate.is_dir() and next(candidate.iterdir(), None) is not None:
                return candidate.resolve()
        except OSError:
            continue
    raise FabricError(
        f"local official dataset is unavailable or empty: {dataset_id} ({version})"
    )


def resolve_datasets(
    profile: str,
    requirements: list[dict[str, Any]],
    *,
    dataset_root: str | Path | None = None,
) -> list[dict[str, str]]:
    """Resolve official datasets by name using only minimal local availability checks."""

    paths = profile_paths(profile, dataset_root=dataset_root)
    resolved: list[dict[str, str]] = []
    for requirement in requirements:
        if (
            type(requirement) is not dict
            or set(requirement) not in (
                {"dataset_id", "version"},
                {"dataset_id", "version", "shards"},
            )
            or type(requirement.get("dataset_id")) is not str
            or not requirement["dataset_id"].strip()
            or type(requirement.get("version")) is not str
            or not requirement["version"].strip()
        ):
            raise FabricError("invalid local dataset requirement")
        selected = _resolve_one(
            list(paths["dataset_roots"]),
            requirement["dataset_id"],
            requirement["version"],
        )
        resolved.append(
            {
                "dataset_id": requirement["dataset_id"],
                "version": requirement["version"],
                "local_path": str(selected),
                "status": "OFFICIAL_LOCAL_AVAILABLE",
            }
        )
    return resolved


def probe_gpus(*, runner: Callable[..., Any] = subprocess.run) -> list[dict[str, int]]:
    command = [
        "nvidia-smi",
        "--query-gpu=index,memory.free",
        "--format=csv,noheader,nounits",
    ]
    try:
        completed = runner(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            shell=False,
            timeout=5,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise FabricError("cannot probe local NVIDIA devices") from error
    if completed.returncode != 0:
        raise FabricError("cannot probe local NVIDIA devices")
    devices: list[dict[str, int]] = []
    for line in completed.stdout.splitlines():
        fields = [item.strip() for item in line.split(",")]
        if len(fields) != 2 or not fields[0].isdecimal() or not fields[1].isdecimal():
            raise FabricError("invalid local NVIDIA device probe")
        devices.append({"index": int(fields[0]), "free_mib": int(fields[1])})
    if not devices or len({item["index"] for item in devices}) != len(devices):
        raise FabricError("no unique local NVIDIA device is available")
    return devices


def select_gpu_devices(
    gpu_count: int,
    gpu_memory_mib: int | float,
    *,
    device_probe: Callable[[], list[dict[str, int]]] = probe_gpus,
) -> dict[str, object]:
    """Choose local devices without creating a cross-project reservation queue.

    ``gpu_memory_mib`` is a per-device preference, not an aggregate-capacity
    promise.  Devices satisfying it are preferred individually.  When there
    are not enough such devices, the least-loaded remaining devices are still
    returned so independent projects can compete and start immediately.  A
    real CUDA OOM is handled by the same-instruction engineering recovery
    path; preflight never waits for a GPU slot.
    """

    if type(gpu_count) is not int or gpu_count not in GPU_COUNTS:
        raise FabricError("GPU count must be 1, 2, or 4")
    if type(gpu_memory_mib) not in {int, float} or gpu_memory_mib < 0:
        raise FabricError("invalid GPU memory request")
    devices = device_probe()
    if any(
        type(item) is not dict
        or set(item) != {"index", "free_mib"}
        or type(item["index"]) is not int
        or type(item["free_mib"]) is not int
        or item["index"] < 0
        or item["free_mib"] < 0
        for item in devices
    ):
        raise FabricError("invalid local GPU probe result")
    devices = sorted(
        devices,
        key=lambda item: (
            item["free_mib"] < gpu_memory_mib,
            -item["free_mib"],
            item["index"],
        ),
    )
    selected = devices[:gpu_count]
    if len(selected) != gpu_count:
        raise FabricError("LOCAL_GPU_UNAVAILABLE: requested local GPU count is unavailable")
    under_target = [
        item["index"]
        for item in selected
        if item["free_mib"] < gpu_memory_mib
    ]
    return {
        "device_indexes": [item["index"] for item in selected],
        "observed_free_mib": {
            str(item["index"]): item["free_mib"] for item in selected
        },
        "requested_mib_per_device": gpu_memory_mib,
        "under_target_device_indexes": under_target,
        "all_devices_met_preference": not under_target,
        "competition_policy": "START_IMMEDIATELY_ALLOW_CROSS_PROJECT_SHARING",
    }


def select_gpus(
    gpu_count: int,
    gpu_memory_mib: int | float,
    *,
    device_probe: Callable[[], list[dict[str, int]]] = probe_gpus,
) -> list[int]:
    """Compatibility wrapper returning only physical device indexes."""

    return list(
        select_gpu_devices(
            gpu_count,
            gpu_memory_mib,
            device_probe=device_probe,
        )["device_indexes"]
    )


def preflight(
    project_root: Path,
    *,
    project_id: str,
    instruction_id: str,
    datasets: list[dict[str, Any]],
    gpu_count: int,
    gpu_memory_mib: int | float,
    configured_profile: str | None = None,
    dataset_root: str | Path | None = None,
    source_roots: list[str | Path] | None = None,
    cache_root: str | Path | None = None,
    cache_state_root: str | Path | None = None,
    device_probe: Callable[[], list[dict[str, int]]] = probe_gpus,
) -> dict[str, object]:
    profile = detect_profile(project_root, configured_profile)
    if profile == "46":
        from . import dataset_cache

        paths = profile_paths(profile, dataset_root=dataset_root)
        sources = (
            [Path(item) for item in source_roots]
            if source_roots is not None
            else [Path(item) for item in paths["source_roots"]]
        )
        target_root = Path(cache_root or str(paths["download_root"]))
        state_root = Path(cache_state_root or str(paths["cache_state_root"]))
        lease_id = f"{project_id}:{instruction_id}"
        routes = []
        identities: set[tuple[str, str]] = set()
        try:
            for requirement in datasets:
                if (
                    type(requirement) is not dict
                    or set(requirement) not in (
                        {"dataset_id", "version"},
                        {"dataset_id", "version", "shards"},
                    )
                ):
                    raise FabricError("invalid local dataset requirement")
                identity = (
                    str(requirement.get("dataset_id", "")).strip().casefold(),
                    str(requirement.get("version", "")).strip().casefold(),
                )
                if identity in identities:
                    raise FabricError("duplicate local dataset subset requirement")
                identities.add(identity)
                route = dataset_cache.acquire_subset(
                    source_roots=sources,
                    cache_root=target_root,
                    state_root=state_root,
                    dataset_id=requirement.get("dataset_id"),
                    subset_id=requirement.get("version"),
                    lease_id=lease_id,
                )
                route["canonical_dataset_id"] = route["dataset_id"]
                route["dataset_id"] = requirement["dataset_id"]
                routes.append(route)
        except BaseException:
            for route in reversed(routes):
                dataset_cache.release_subset(
                    cache_root=target_root,
                    state_root=state_root,
                    dataset_id=route["dataset_id"],
                    subset_id=route["subset_id"],
                    lease_id=lease_id,
                )
            raise
    else:
        routes = resolve_datasets(profile, datasets, dataset_root=dataset_root)
    try:
        gpu_selection = (
            select_gpu_devices(
                gpu_count,
                gpu_memory_mib,
                device_probe=device_probe,
            )
            if gpu_count
            else {
                "device_indexes": [],
                "observed_free_mib": {},
                "requested_mib_per_device": 0,
                "under_target_device_indexes": [],
                "all_devices_met_preference": True,
                "competition_policy": (
                    "START_IMMEDIATELY_ALLOW_CROSS_PROJECT_SHARING"
                ),
            }
        )
        device_indexes = list(gpu_selection["device_indexes"])
    except BaseException:
        if profile == "46":
            for route in reversed(routes):
                dataset_cache.release_subset(
                    cache_root=target_root,
                    state_root=state_root,
                    dataset_id=route["dataset_id"],
                    subset_id=route["subset_id"],
                    lease_id=route["lease_id"],
                )
        raise
    return {
        "execution_mode": "LOCAL_ONLY",
        "server_profile": profile,
        "project_id": project_id,
        "instruction_id": instruction_id,
        "gpu_device_indexes": device_indexes,
        "gpu_selection": gpu_selection,
        "dataset_routes": routes,
        "dataset_cache_root": (
            str(Path(cache_root or str(profile_paths(profile)["download_root"])).resolve())
            if profile == "46"
            else None
        ),
        "dataset_cache_state_root": (
            str(Path(cache_state_root or str(profile_paths(profile)["cache_state_root"])).resolve())
            if profile == "46"
            else None
        ),
        "pth_readme": profile_paths(profile, dataset_root=dataset_root)["pth_readme"],
    }


def release_preflight(receipt: Mapping[str, object]) -> list[dict[str, object]]:
    """Release all profile-46 subset leases represented by a preflight receipt."""

    if receipt.get("server_profile") != "46":
        return []
    from . import dataset_cache

    cache_root = receipt.get("dataset_cache_root")
    state_root = receipt.get("dataset_cache_state_root")
    routes = receipt.get("dataset_routes")
    if (
        type(cache_root) is not str
        or type(state_root) is not str
        or type(routes) is not list
    ):
        raise FabricError("invalid dataset cache receipt")
    results = []
    for route in routes:
        if (
            type(route) is not dict
            or type(route.get("dataset_id")) is not str
            or type(route.get("subset_id")) is not str
            or type(route.get("lease_id")) is not str
        ):
            raise FabricError("invalid dataset cache route")
        results.append(
            dataset_cache.release_subset(
                cache_root=Path(cache_root),
                state_root=Path(state_root),
                dataset_id=route["dataset_id"],
                subset_id=route["subset_id"],
                lease_id=route["lease_id"],
            )
        )
    return results


def execution_environment(
    receipt: Mapping[str, object], *, base: Mapping[str, str] | None = None
) -> dict[str, str]:
    """Build the environment passed to the guarded local command."""

    environment = dict(os.environ if base is None else base)
    indexes = receipt.get("gpu_device_indexes", [])
    routes = receipt.get("dataset_routes")
    pth_readme = receipt.get("pth_readme")
    if pth_readme is None and receipt.get("server_profile") in PROFILES:
        pth_readme = profile_paths(str(receipt["server_profile"]))["pth_readme"]
    if (
        type(indexes) is not list
        or any(type(item) is not int or item < 0 for item in indexes)
        or type(routes) is not list
        or any(type(item) is not dict for item in routes)
        or type(pth_readme) is not str
    ):
        raise FabricError("invalid local execution receipt")
    if indexes:
        environment["CUDA_VISIBLE_DEVICES"] = ",".join(str(item) for item in indexes)
    else:
        environment.pop("CUDA_VISIBLE_DEVICES", None)
    environment["CQC_DATASET_PATHS"] = json.dumps(
        {item["dataset_id"]: item["local_path"] for item in routes},
        ensure_ascii=False,
        sort_keys=True,
    )
    environment["CQC_PTH_README"] = pth_readme
    environment["CQC_SERVER_PROFILE"] = str(receipt.get("server_profile", ""))
    return environment


def assert_download_target(profile: str, target: Path) -> Path:
    """Enforce the fixed local scratch root for any future dataset acquisition."""

    root = Path(str(profile_paths(profile)["download_root"])).resolve()
    resolved = Path(target).expanduser().resolve()
    if resolved != root and root not in resolved.parents:
        raise FabricError(f"dataset writes on server {profile} must stay under {root}")
    return resolved
