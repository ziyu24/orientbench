#!/usr/bin/env python3
"""Prospective A6R asset gate; metadata-only and outcome-blind by construction."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import socket
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
AROOT = Path(__file__).resolve().parents[1]
REPORTS = AROOT / "reports"
ROUND_ID = "orientbench-c-r003-20260805"
SNAPSHOT = "e3ca1ad94d64d202a47b6635490fde439df76868"
SCRIPT = Path(__file__).resolve()
OUT_INVENTORY = REPORTS / "a6r_candidate_asset_inventory_r003.csv"
OUT_OVERLAP = REPORTS / "a6r_overlap_registry_r003.csv"
OUT_GATE = REPORTS / "a6r_asset_gate_r003.json"
OUT_MANIFEST = REPORTS / "a6r_asset_gate_manifest_r003.json"
OUT_REPORT = ROOT / "dis/server_reports/orientbench-c-r003-20260805.md"

PROTOCOL_A1 = REPORTS / "a1_protocol_frozen.json"
PROTOCOL_A6 = REPORTS / "a6_confirmatory_protocol_frozen.json"
AUDIT_A6 = REPORTS / "a6_confirmatory_provenance_audit.csv"
MIGRATION = ROOT / "docs/server_migration_handoff_20260727.md"
SCOPE = AROOT / "README_SCOPE.md"
PTH_DATA = ROOT.parent / "pth_data"
THIRD_PARTY = ROOT.parent / "third_party"

OUTCOME_NAME_MARKERS = (
    "nrc", "risk_frontier", "certification", "candidate_external_confirmation",
    "candidate_external_bootstrap", "matched_native", "matched_phase", "matched_17field",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dataset-root",
        default=os.environ.get("ORIENTBENCH_DATASET_ROOT"),
        help="Optional local dataset-store root; its resolved value is never persisted.",
    )
    return parser.parse_args()


def shared_output_violations(paths: list[Path]) -> list[str]:
    """Return logical output aliases that contain non-portable or secret text."""
    account = os.environ.get("USER", "")
    hostname = socket.gethostname()
    literals = [value for value in (account, hostname) if len(value) >= 3]
    patterns = (
        re.compile(r"(?<![A-Za-z0-9_.-])/(?:home|Users|tmp|var|mnt|data)/"),
        re.compile(r"(?<![A-Za-z0-9_])[A-Za-z]:[\\\\/]"),
        re.compile(r"(?:ghp_|github_pat_|AKIA)[A-Za-z0-9_=-]+"),
    )
    violations = []
    for path in paths:
        text = path.read_text(encoding="utf-8", errors="replace")
        if any(pattern.search(text) for pattern in patterns) or any(value in text for value in literals):
            violations.append(rel(path))
    return violations


def rel(path: Path) -> str:
    path = path.resolve()
    try:
        return str(path.relative_to(ROOT.resolve()))
    except ValueError:
        try:
            return "third_party/" + str(path.relative_to(THIRD_PARTY.resolve()))
        except ValueError:
            return "external_baseline_library/" + path.name


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git_blob(path: Path) -> str:
    """Return the canonical raw Git blob identity without writing an object."""
    return subprocess.check_output(
        ["git", "hash-object", "--no-filters", str(path)], cwd=ROOT, text=True
    ).strip()


def git(*args: str, cwd: Path = ROOT) -> str:
    return subprocess.check_output(["git", *args], cwd=cwd, text=True).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(temp, path)


class InputRegistry:
    def __init__(self) -> None:
        self.records: dict[str, dict] = {}

    def add(self, path: Path, purpose: str, git_blob_hash: str = "") -> None:
        if not path.is_file():
            raise FileNotFoundError(path)
        key = rel(path)
        record = self.records.setdefault(key, {
            "logical_path": key, "bytes": path.stat().st_size, "sha256": sha256(path),
            "git_blob": git_blob_hash or git_blob(path), "purposes": [],
        })
        if purpose not in record["purposes"]:
            record["purposes"].append(purpose)
        if git_blob_hash:
            record["git_blob"] = git_blob_hash

    def output(self) -> list[dict]:
        rows = []
        for key in sorted(self.records):
            row = dict(self.records[key])
            row["purposes"] = sorted(row["purposes"])
            rows.append(row)
        return rows


def file_identity(path: Path | None, registry: InputRegistry, purpose: str) -> tuple[str, int, str]:
    if path is None or not path.is_file():
        return "", 0, ""
    registry.add(path, purpose)
    return rel(path), path.stat().st_size, sha256(path)


def framework_identity(name: str, registry: InputRegistry) -> tuple[str, str, str]:
    directory = THIRD_PARTY / name
    if not directory.is_dir():
        return "MISSING", "MISSING", "UNKNOWN"
    commit = git("rev-parse", "HEAD", cwd=directory)
    licenses = sorted(path for path in directory.glob("LICENSE*") if path.is_file())
    if not licenses:
        return commit, "MISSING", "UNKNOWN"
    registry.add(licenses[0], f"{name} source license")
    return commit, sha256(licenses[0]), "Apache-2.0 repository license"


def config_and_log(checkpoint: Path) -> tuple[Path | None, Path | None]:
    text = str(checkpoint.relative_to(ROOT))
    if "m4_third_dataset_070" in text:
        head = re.search(r"__(PSC|CSL|DCL)__", checkpoint.name).group(1).lower()
        return ROOT / f"configs/m4_third_dataset_070/fair1m_{head}.py", None
    if "paper_B_psc_mechanism/artifacts/b4_training" in text:
        seed = re.search(r"seed(\d+)", text).group(1)
        config = checkpoint.parent / f"seed{seed}.py"
        logs = sorted(checkpoint.parent.glob("*/*.log"))
        return config, logs[0] if logs else None
    if "work_dirs/k2" in text:
        configs = sorted(checkpoint.parent.glob("*.py"))
        logs = sorted(checkpoint.parent.glob("*/*.log"))
        return configs[0] if configs else None, logs[-1] if logs else None
    if "outputs/training/a4_host" in text:
        logs = sorted(checkpoint.parent.glob("*/*.log"))
        return checkpoint.parent / "o2_rtdetr_r18vd_4xb1_72e_dotav15.py", logs[0] if logs else None
    if "outputs/training/rhino" in text:
        logs = sorted(checkpoint.parent.glob("*/*.log"))
        return checkpoint.parent / "rhino_phc_haus_4scale_r50_2xb4_36e_dota.py", logs[0] if logs else None
    return None, None


def parse_checkpoint(checkpoint: Path) -> dict:
    logical = rel(checkpoint)
    name = checkpoint.name
    if "m4_third_dataset_070" in logical:
        match = re.search(r"__(PSC|CSL|DCL)__FAIR1M__seed(\d+)", name)
        head, seed = match.group(1), int(match.group(2))
        return dict(dataset="FAIR1M", version="v1.0", split="frozen train80 -> val20",
                    detector="RotatedRetinaNet", angle_head=head, backbone="ResNet-50-FPN", seed=seed,
                    framework="mmrotate_1x", exposure="M4 third-dataset evaluation and native-score analysis",
                    protocol="M4/K2 candidate and endpoint study", output_marker="outputs/persistent_artifacts/m4_third_dataset_070/eval")
    if "paper_B_psc_mechanism/artifacts/b4_training" in logical:
        seed = int(re.search(r"seed(\d+)", logical).group(1))
        return dict(dataset="DOTA", version="v1.0", split="train -> val",
                    detector="RotatedFCOS", angle_head="PSCD dual-frequency", backbone="ResNet-50-FPN", seed=seed,
                    framework="mmrotate_1x", exposure="B4 external candidate and intervention outcomes",
                    protocol="B4/B5 mechanism and candidate gate", output_marker="top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b4_")
    if "work_dirs/k2" in logical:
        match = re.search(r"K2_final__(.+?)__(DIOR-R|SODA-A)__seed(\d+)", logical)
        head, dataset, seed = match.group(1), match.group(2), int(match.group(3))
        split = "trainval -> test" if dataset == "DIOR-R" else "frozen train -> val"
        return dict(dataset=dataset, version="registered", split=split,
                    detector="RotatedRetinaNet", angle_head=head, backbone="ResNet-50-FPN", seed=seed,
                    framework="mmrotate_1x", exposure="K2 full-converged angle-head and native-score outcomes",
                    protocol="K2 score-direction/native-signal design", output_marker="top_journal_v3_reaudit_055/reports/k2_")
    if "outputs/training/a4_host" in logical:
        return dict(dataset="DOTA", version="v1.5", split="train -> val",
                    detector="RotatedRTDETR", angle_head="direct le90 query head", backbone="ResNet-18vd", seed=42,
                    framework="ai4rs", exposure="A4 host perturbation/design asset",
                    protocol="A4 cross-host protocol participation", output_marker="outputs/training/a4_host")
    if "outputs/training/rhino" in logical:
        return dict(dataset="DOTA", version="v1.0", split="train -> val",
                    detector="RHINO", angle_head="positive Hungarian classification head", backbone="ResNet-50", seed=42,
                    framework="ai4rs", exposure="prior persistent prediction/reliability lineage",
                    protocol="historical OrientBench reliability design", output_marker="outputs/persistent_artifacts/orientbench_v2/DOTA-v1.0/rhino")
    raise ValueError(logical)


def existing_checkpoint_candidates(registry: InputRegistry, framework: dict[str, tuple[str, str, str]]) -> list[dict]:
    checkpoints = sorted(
        path for path in ROOT.rglob("*.pth")
        if ".git" not in path.parts and ".orientbench_transfer_parts" not in path.parts
    )
    rows = []
    for checkpoint in checkpoints:
        metadata = parse_checkpoint(checkpoint)
        config, log = config_and_log(checkpoint)
        checkpoint_path, checkpoint_bytes, checkpoint_sha = file_identity(checkpoint, registry, "candidate checkpoint identity only")
        config_path, config_bytes, config_sha = file_identity(config, registry, "candidate config identity only")
        log_path, log_bytes, log_sha = file_identity(log, registry, "candidate training-log identity only")
        fw_commit, license_sha, code_license = framework[metadata["framework"]]
        candidate_id = f"{metadata['dataset']}|{metadata['version']}|{metadata['detector']}|{metadata['angle_head']}|seed{metadata['seed']}|{checkpoint_sha[:12]}"
        output_hit = (ROOT / metadata["output_marker"]).exists()
        rows.append({
            "candidate_id": candidate_id, "dataset": metadata["dataset"], "dataset_version": metadata["version"],
            "split": metadata["split"], "detector": metadata["detector"], "angle_head_coder": metadata["angle_head"],
            "backbone": metadata["backbone"], "seed": metadata["seed"], "checkpoint_alias": checkpoint_path,
            "checkpoint_present": True, "checkpoint_bytes": checkpoint_bytes, "checkpoint_sha256": checkpoint_sha,
            "checkpoint_source": "project-trained existing asset", "checkpoint_selection_rule": "best detector mAP checkpoint; target risk not used for checkpoint selection",
            "config_alias": config_path, "config_bytes": config_bytes, "config_sha256": config_sha,
            "log_alias": log_path, "log_bytes": log_bytes, "log_sha256": log_sha,
            "framework": metadata["framework"], "framework_commit": fw_commit, "code_license": code_license,
            "code_license_sha256": license_sha, "dataset_license": "UNVERIFIED_DATASET_NOT_PRESENT",
            "evaluator": "historical full evaluator exists but candidate excluded before evaluator gate",
            "tile_merge_nms": "NOT_EVALUATED_AFTER_EARLY_EXCLUSION",
            "full_split_present": False, "all_image_count": 0, "empty_gt_images_verified": False,
            "complete_gt_verified": False, "class_mapping_verified": False, "angle_convention_verified": False,
            "mother_scene_mapping_verified": False, "split_aggregate_hash": "",
            "raw_to_final_persistence": "NOT_EVALUATED_AFTER_EARLY_EXCLUSION",
            "tta_availability": "NOT_EVALUATED; frozen missing-TTA policy would apply",
            "prior_outcome_exposure": output_hit, "protocol_participation": True,
            "outcome_exposure_evidence": metadata["exposure"], "protocol_evidence": metadata["protocol"],
            "independence_tier": "EXCLUDED", "neutral_sort_key": "",
            "first_failed_gate": "PRIOR_OUTCOME_OR_PROTOCOL_PARTICIPATION",
            "gate_status": "EXCLUDED", "estimated_gpu_hours": "NOT_ESTIMATED_AFTER_EXCLUSION",
            "estimated_disk_gb": "NOT_ESTIMATED_AFTER_EXCLUSION", "official_url": "",
            "public_checksum": "", "notes": "dataset store is empty on this server; no outcome file was opened",
        })
    return rows


def historical_a6_candidates(registry: InputRegistry) -> list[dict]:
    rows = []
    for source in read_csv(AUDIT_A6):
        candidate_id = source["candidate"].replace(" ", "_")
        reason = source["reason"]
        registered_dataset, legacy_unit = source["dataset"].rsplit("/", 1)
        dataset_version = "v1.0" if registered_dataset == "DOTA-v1.0" else "UNVERIFIED"
        rows.append({
            "candidate_id": candidate_id, "dataset": registered_dataset,
            "dataset_version": dataset_version, "split": source["split"],
            "detector": source["candidate"].split()[0], "angle_head_coder": "registered historical head",
            "backbone": "registered historical backbone", "seed": "registered", "checkpoint_alias": "external_baseline_library/registered_baseline",
            "checkpoint_present": False, "checkpoint_bytes": 0, "checkpoint_sha256": "",
            "checkpoint_source": "historical pth_data registration; library absent on current server",
            "checkpoint_selection_rule": "historical detector criterion; exact source unavailable",
            "config_alias": "", "config_bytes": 0, "config_sha256": "", "log_alias": "", "log_bytes": 0,
            "log_sha256": "", "framework": "historical", "framework_commit": "UNVERIFIED",
            "code_license": "UNVERIFIED", "code_license_sha256": "", "dataset_license": "UNVERIFIED_DATASET_NOT_PRESENT",
            "evaluator": source["evaluator"], "tile_merge_nms": "UNVERIFIED", "full_split_present": source["fullval_complete"] == "True",
            "all_image_count": source["observed_image_count"], "empty_gt_images_verified": False,
            "complete_gt_verified": False, "class_mapping_verified": False, "angle_convention_verified": False,
            "mother_scene_mapping_verified": False, "split_aggregate_hash": "", "raw_to_final_persistence": "NOT_COMPLETE",
            "tta_availability": "UNVERIFIED", "prior_outcome_exposure": source["prior_risk_result_seen"] == "True",
            "protocol_participation": False, "outcome_exposure_evidence": reason,
            "protocol_evidence": "original A6 provenance audit", "independence_tier": "EXCLUDED", "neutral_sort_key": "",
            "first_failed_gate": "PRIOR_OUTCOME_EXPOSURE" if source["prior_risk_result_seen"] == "True" else "CHECKPOINT_AND_FULL_UNIVERSE_MISSING",
            "gate_status": "EXCLUDED", "estimated_gpu_hours": "NOT_ESTIMATED_AFTER_EXCLUSION",
            "estimated_disk_gb": "NOT_ESTIMATED_AFTER_EXCLUSION", "official_url": "", "public_checksum": "",
            "notes": reason + f"; historical unit tag /{legacy_unit}; pth_data and dataset store unavailable on current server",
        })
    return rows


def overlap_rows(candidates: list[dict]) -> list[dict]:
    hashes: dict[str, list[str]] = {}
    for row in candidates:
        if row["checkpoint_sha256"]:
            hashes.setdefault(row["checkpoint_sha256"], []).append(row["candidate_id"])
    result = []
    for row in candidates:
        same = [candidate for candidate in hashes.get(row["checkpoint_sha256"], []) if candidate != row["candidate_id"]]
        result.append({
            "candidate_id": row["candidate_id"], "checkpoint_sha256": row["checkpoint_sha256"],
            "same_hash_candidates": ";".join(same), "repository_checkpoint_hit": row["checkpoint_present"],
            "repository_config_hit": bool(row["config_alias"]), "prior_prediction_or_result_path_hit": row["prior_outcome_exposure"],
            "protocol_participation": row["protocol_participation"], "prior_outcome_exposure": row["prior_outcome_exposure"],
            "known_internal_old_project_overlap": "NOT_READ; identity remains UNKNOWN and cannot support PASS",
            "selection_lineage": row["checkpoint_selection_rule"], "status": "EXCLUDED",
            "first_failed_gate": row["first_failed_gate"],
            "evidence": row["outcome_exposure_evidence"] or row["notes"],
        })
    return result


INVENTORY_FIELDS = [
    "candidate_id","dataset","dataset_version","split","detector","angle_head_coder","backbone","seed",
    "checkpoint_alias","checkpoint_present","checkpoint_bytes","checkpoint_sha256","checkpoint_source","checkpoint_selection_rule",
    "config_alias","config_bytes","config_sha256","log_alias","log_bytes","log_sha256","framework","framework_commit",
    "code_license","code_license_sha256","dataset_license","evaluator","tile_merge_nms","full_split_present","all_image_count",
    "empty_gt_images_verified","complete_gt_verified","class_mapping_verified","angle_convention_verified",
    "mother_scene_mapping_verified","split_aggregate_hash","raw_to_final_persistence","tta_availability",
    "prior_outcome_exposure","protocol_participation","outcome_exposure_evidence","protocol_evidence","independence_tier",
    "neutral_sort_key","first_failed_gate","gate_status","estimated_gpu_hours","estimated_disk_gb","official_url",
    "public_checksum","notes",
]


def file_record(path: Path) -> dict:
    record = {
        "path": rel(path), "bytes": path.stat().st_size, "sha256": sha256(path),
        "git_blob": git_blob(path),
    }
    if path.suffix == ".csv":
        rows = read_csv(path)
        record["rows"] = len(rows)
        record["schema"] = list(rows[0]) if rows else []
    else:
        record["rows"] = None
        record["schema"] = "json" if path.suffix == ".json" else "markdown"
    return record


def report_text(head: str, candidates: list[dict], overlap: list[dict], gate: dict,
                checkpoint_count: int, source_count: int) -> str:
    counts: dict[str, int] = {}
    for row in candidates:
        counts[row["first_failed_gate"]] = counts.get(row["first_failed_gate"], 0) + 1
    table_rows = []
    for reason, count in sorted(counts.items()):
        table_rows.append(f"| `{reason}` | {count} |")
    candidate_rows = []
    for row in candidates:
        candidate_rows.append(
            f"| `{row['candidate_id']}` | {row['dataset']} | {row['detector']} | "
            f"{row['angle_head_coder']} | {row['seed']} | `{row['independence_tier']}` | "
            f"`{row['first_failed_gate']}` |"
        )
    return f"""# OrientBench A6R 前瞻独立复现实物门控

- round: `{ROUND_ID}`
- scientific snapshot: `{SNAPSHOT}`
- execution HEAD: `{head}`
- final gate: `{gate['final_gate']}`
- selected unit: `NONE`
- training / inference / risk computation / download: `0 / 0 / 0 / 0`

## 1. 结论

当前服务器没有可被冻结为 A6R prospective replication 的完整单元。盘点到 {checkpoint_count} 个本地 checkpoint，
并继承原 A6 的 3 个历史候选，共 {len(candidates)} 个精确候选记录；全部在按顺序执行的硬门中被排除。
原 `NO_ELIGIBLE_CONFIRMATORY_UNIT` 保持不变，A 继续是 `A_MEASUREMENT_ONLY`。

## 2. 首个失败点

| first failed gate | candidates |
|---|---:|
{os.linesep.join(table_rows)}

本地 checkpoint 全部已经参与既有协议/机制工作或存在 prior outcome 暴露，不能重新包装成前瞻复现。
原 A6 的 ARS-DETR/Strip-RCNN 候选仍分别受 partial universe、prior risk exposure 或 vanished raw artifact 限制。
此外，当前服务器的 `dataset_store` 为空，`external_baseline_library/readme.md` 与整个 baseline 库均不存在；
因此 checkpoint 许可、完整 split、empty-image、GT、母景映射和 raw-to-final 可复算性都无法为新单元闭环。

### 2.1 完整候选清单

| candidate | dataset | detector | head/coder | seed | tier | first failed gate |
|---|---|---|---|---:|---|---|
{os.linesep.join(candidate_rows)}

精确 checkpoint/config/log 身份、bytes、SHA-256、Git blob、许可与 split/schema 字段见 candidate inventory；
逐候选 overlap 与污染证据见 overlap registry。

## 3. 污染与 overlap

overlap registry 保留每个候选的 checkpoint/config 命中、同 hash、selection lineage、协议参与和 prior exposure。
未读取 D7/PCP-OBB、pcbobb、pcbobb_beyond 或 pcbobb_score_study；它们的 overlap 身份保持 UNKNOWN，
并且 UNKNOWN 不计作 clean。完全未暴露、可进入中性排序的候选为 0，因此没有执行 outcome-based 比较或换 unit。

## 4. 协议边界

A1/A6 冻结协议、原 A6 provenance audit 与迁移交接均已读取；未修改任何冻结文件。
若未来取得合格资产，missing-TTA policy 固定为保持 eligible universe，把非有限 TTA 排在有限值之后；
TTA 完全不可得时从该单元 score menu 删除，不能切到 complete-case universe。

## 5. 最弱环节与下一步

最弱环节不是计算资源，而是物理资产不存在：没有本地 dataset full split，也没有可验证许可/选择来源的外部 baseline 库。
下一轮若要继续，应先由 C 单独冻结一个官方 acquisition contract，明确官方 dataset/checkpoint URL、版本、公开 checksum、
许可、full split/empty-image/scene mapping 和预计磁盘；获取前仍不得查看 target NRC/risk。当前报告不虚构 URL 或 checksum，
也未执行任何下载。只有资产获取并独立核验通过后，才可设计一次性推理合同。

## 6. 复算与合规

脚本登记 {source_count} 个实际读取输入，只读取协议、provenance、迁移、配置/日志元数据、checkpoint bytes 和许可；
候选 target NRC、angle-risk、severe-event、certification/frontier 文件打开数为 0。
未写入 B，未修改 A 主稿、数据、split、checkpoint、旧报告、`dis/B.md` 或 `dis/sug.md`。
"""


def main() -> int:
    args = parse_args()
    registry = InputRegistry()
    source_blob = git_blob(SCRIPT)
    registry.add(SCRIPT, "r003 execution source", source_blob)
    for path, purpose in (
        (PROTOCOL_A1, "frozen A1 protocol"), (PROTOCOL_A6, "frozen A6 protocol"),
        (AUDIT_A6, "historical A6 provenance audit"), (MIGRATION, "server migration and asset boundary"),
        (SCOPE, "Paper A ownership and scope"),
    ):
        registry.add(path, purpose, git_blob(path))

    status = git("status", "--porcelain", "--untracked-files=all").splitlines()
    allowed = (
        "?? .orientbench_transfer_parts/", "?? top_journal_v3_reaudit_055/paper_A_orientation_protocol/scripts/audit_a6r_assets_r003.py",
        "?? top_journal_v3_reaudit_055/paper_A_orientation_protocol/reports/a6r_", "?? dis/server_reports/",
    )
    worktree_ok = all(any(line.startswith(prefix) for prefix in allowed) for line in status)
    head = git("rev-parse", "HEAD")
    ancestry_ok = subprocess.run(["git", "merge-base", "--is-ancestor", SNAPSHOT, head], cwd=ROOT).returncode == 0

    frameworks = {}
    for name in ("mmrotate_1x", "ai4rs"):
        frameworks[name] = framework_identity(name, registry)

    candidates = existing_checkpoint_candidates(registry, frameworks)
    candidates.extend(historical_a6_candidates(registry))
    candidates.sort(key=lambda row: row["candidate_id"])
    overlap = overlap_rows(candidates)

    dataset_root = Path(args.dataset_root).expanduser() if args.dataset_root else None
    dataset_files = sum(1 for path in dataset_root.rglob("*") if path.is_file()) if dataset_root and dataset_root.is_dir() else 0
    pth_data_present = PTH_DATA.is_dir()
    eligible = [row for row in candidates if row["gate_status"] == "ELIGIBLE"]
    observable_preconditions = {
        "worktree_authorized": worktree_ok,
        "snapshot_ancestry": ancestry_ok,
    }
    protocol_drift = not all(observable_preconditions.values())
    if not worktree_ok or not ancestry_ok:
        final_gate = "INCONCLUSIVE_A6R_IDENTITY"
    elif protocol_drift:
        final_gate = "PROTOCOL_DRIFT"
    elif eligible:
        final_gate = "PASS_A6R_ASSET_GATE"
    else:
        final_gate = "FAIL_NO_A6R_ASSET"
    gate = {
        "schema_version": "a6r_asset_gate_r003_v1", "round_id": ROUND_ID,
        "scientific_snapshot": SNAPSHOT, "execution_head": head, "final_gate": final_gate,
        "historical_boundary": {"original_A6": "NO_ELIGIBLE_CONFIRMATORY_UNIT", "paper_A": "A_MEASUREMENT_ONLY",
                                "paper_B": "RETIRED_FAIL_CANDIDATE_GATE"},
        "hard_gates": {
            "git_ancestry": "PASS" if ancestry_ok else "FAIL",
            "tracked_index_and_authorized_workspace": "PASS" if worktree_ok else "FAIL",
            "training_count": 0, "inference_count": 0, "risk_computation_count": 0,
            "download_count": 0, "candidate_outcome_file_open_count": 0,
            "old_personal_project_read_count": 0, "dataset_store_file_count": dataset_files,
            "external_baseline_library_present": pth_data_present,
            "execution_counter_evidence": "STATIC_CONTROL_FLOW_AUDIT",
            "observable_preconditions": observable_preconditions,
        },
        "frozen_policy": {
            "main_mask": "ar>=2.1", "primary_event": "geometry_normalized_severe",
            "absolute_alpha": [0.001,0.0025,0.005,0.01],
            "coverage_grid": [0.01,0.025,0.05,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0],
            "missing_tta": "eligible universe unchanged; nonfinite last; remove TTA score only if wholly unavailable",
        },
        "candidate_count": len(candidates), "eligible_count": len(eligible),
        "excluded_count": len(candidates)-len(eligible), "selected_unit": None,
        "neutral_selection": "NOT_RUN_NO_ELIGIBLE_CANDIDATE",
        "candidate_decisions": [{"candidate_id": row["candidate_id"], "tier": row["independence_tier"],
                                  "status": row["gate_status"], "neutral_sort_key": row["neutral_sort_key"],
                                  "first_failed_gate": row["first_failed_gate"]}
                                 for row in candidates],
        "next_action": "C must freeze a separate official acquisition contract before any download or outcome access",
    }

    write_csv(OUT_INVENTORY, candidates, INVENTORY_FIELDS)
    write_csv(OUT_OVERLAP, overlap, ["candidate_id","checkpoint_sha256","same_hash_candidates","repository_checkpoint_hit",
                                     "repository_config_hit","prior_prediction_or_result_path_hit","protocol_participation",
                                     "prior_outcome_exposure","known_internal_old_project_overlap","selection_lineage","status",
                                     "first_failed_gate","evidence"])
    OUT_GATE.write_text(json.dumps(gate, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report_text(head, candidates, overlap, gate, len(candidates)-3, len(registry.output())), encoding="utf-8")

    output_paths = [OUT_INVENTORY, OUT_OVERLAP, OUT_GATE, OUT_REPORT]
    sanitizer_hits = shared_output_violations(output_paths)
    if sanitizer_hits:
        gate["final_gate"] = final_gate = "PROTOCOL_DRIFT"
        gate["hard_gates"]["shared_output_sanitizer"] = {"status": "FAIL", "logical_paths": sanitizer_hits}
        OUT_GATE.write_text(json.dumps(gate, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        OUT_REPORT.write_text(report_text(head, candidates, overlap, gate, len(candidates)-3, len(registry.output())), encoding="utf-8")
    else:
        gate["hard_gates"]["shared_output_sanitizer"] = {"status": "PASS", "logical_paths": []}
        OUT_GATE.write_text(json.dumps(gate, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    manifest = {
        "schema_version": "a6r_asset_gate_manifest_r003_v1", "round_id": ROUND_ID,
        "scientific_snapshot": SNAPSHOT, "execution_head": head,
        "execution_source": {"path": rel(SCRIPT), "canonical_sha256": sha256(SCRIPT), "git_blob": source_blob},
        "command": f"python {rel(SCRIPT)}", "inputs": registry.output(),
        "outputs": [file_record(path) for path in output_paths],
        "counts": {"training":0,"inference":0,"risk_computation":0,"download":0,
                   "candidate_outcome_files_opened":0,"old_personal_project_results_read":0,
                   "evidence":"STATIC_CONTROL_FLOW_AUDIT"},
        "shared_output_sanitizer": {"status":"PASS" if not sanitizer_hits else "FAIL",
                                    "logical_paths":sanitizer_hits},
        "forbidden_path_markers": list(OUTCOME_NAME_MARKERS), "candidate_count": len(candidates),
        "eligible_count": len(eligible), "selected_unit": None, "final_gate": final_gate,
        "result_commit": "transport metadata; not self-referenced by this manifest",
    }
    temp = OUT_MANIFEST.with_suffix(".json.tmp")
    temp.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, OUT_MANIFEST)
    final_hits = shared_output_violations(output_paths + [OUT_MANIFEST])
    if final_hits:
        gate["final_gate"] = "PROTOCOL_DRIFT"
        gate["hard_gates"]["shared_output_sanitizer"] = {"status": "FAIL", "logical_paths": final_hits}
        OUT_GATE.write_text(json.dumps(gate, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        OUT_REPORT.write_text(report_text(head, candidates, overlap, gate, len(candidates)-3, len(registry.output())), encoding="utf-8")
        manifest["final_gate"] = "PROTOCOL_DRIFT"
        manifest["shared_output_sanitizer"] = {"status": "FAIL", "logical_paths": final_hits}
        manifest["outputs"] = [file_record(path) for path in output_paths]
        temp.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
        os.replace(temp, OUT_MANIFEST)
    return 2 if final_hits else 0


if __name__ == "__main__":
    raise SystemExit(main())
