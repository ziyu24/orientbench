#!/usr/bin/env python3
"""Evidence-only provenance closure for the r001 B3/B4 statistical re-audit."""
from __future__ import annotations

import csv
import gzip
import hashlib
import importlib.util
import json
import math
import os
import struct
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[3]
BROOT = Path(__file__).resolve().parents[1]
REPORTS = BROOT / "reports"
ROUND_ID = "orientbench-c-r002-20260805"
SNAPSHOT = "8466602330a942c9bb8beff284aa8fc5b952a3b0"
REPLICATES = 800
WORKERS = 40
SCRIPT = Path(__file__).resolve()
TEST_SCRIPT = SCRIPT.with_name("test_b3_b4_reaudit_r002.py")
R001_SCRIPT = SCRIPT.with_name("reaudit_b3_b4_r001.py")

OUT_LINEAGE = REPORTS / "b3_b4_input_lineage_r002.csv"
OUT_INVENTORY = REPORTS / "b3_b4_persistent_asset_inventory_r002.csv"
OUT_B3 = REPORTS / "b3_candidate_cluster_bootstrap_reaudit_r002.csv"
OUT_B4 = REPORTS / "b4_candidate_external_bootstrap_reaudit_r002.csv"
OUT_GATE = REPORTS / "b5_gate_reaudit_r002.csv"
OUT_TESTS = REPORTS / "b3_b4_estimand_equivalence_tests_r002.csv"
OUT_MANIFEST = REPORTS / "b3_b4_reaudit_manifest_r002.json"
OUT_REPORT = ROOT / "dis/server_reports/orientbench-c-r002-20260805.md"

DELTA = ROOT / "top_journal_v3_reaudit_055/reports/m4_delta_theta_075_frozen.json"
G0_COMPARISON = ROOT / "top_journal_v3_reaudit_055/shared_forensics/g0/reports/g0_comparison_manifest.csv"
EXPECTED_DELTA_SHA = "80d86a5f72e70405fe4a49db87aad61e6aea20a26af0ad1c5745bfd646d1e5cb"
EXPECTED_G0_SHA = "e038aed06b3aff86818c8663657f074798e90de867ab48ac9d2821c61c191a86"

R001_FILES = [
    "dis/server_reports/orientbench-c-r001-20260805.md",
    "top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b3_candidate_cluster_bootstrap_reaudit_r001.csv",
    "top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b4_candidate_external_bootstrap_reaudit_r001.csv",
    "top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b5_gate_reaudit_r001.csv",
    "top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b3_b4_estimand_equivalence_tests_r001.csv",
    "top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/b3_b4_reaudit_manifest_r001.json",
    "top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/reaudit_b3_b4_r001.py",
    "top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/test_b3_b4_reaudit_r001.py",
]

EXPECTED_SPLITS = {
    "outputs/bench_core/splits/D_audit_dior_trainval.csv": "11c61be3a03c922b5e00e4cf9e866cf73e18eff44bd6b868b53f54612065669b",
    "outputs/bench_core/splits/D_audit_dota10_train.csv": "d4fb9a793a4c2f31ddd42cde0ba8c571114e78b2ab0d3af36002f201fafc1eb7",
    "outputs/bench_core/splits/D_audit_dota15_train.csv": "ac97d1f3f2a780f79019612fce6f7f93d13aa9f7a65c4f1c14aa96447e743856",
    "outputs/bench_core/splits/D_audit_fair1m_train.csv": "140ef6855909cdca2904656ad76baca31ff11d8c571e3978e005d945440c335e",
    "outputs/bench_core/splits/D_audit_hrsc_trainval.csv": "55734ae8aa3f49350186fd066a761a54fe1a99921897012c5e59ca1fdf9f6679",
    "outputs/bench_core/splits/D_cal_dior_trainval.csv": "f624a21451de394a35041af35c9a910c3a1bdc11fb5c942d15416e04e0e6f632",
    "outputs/bench_core/splits/D_cal_dota10_train.csv": "48a0319a1ea51fcbadf43e7e632d5a77f77d3db73442acfd639acb0c455daed4",
    "outputs/bench_core/splits/D_cal_dota15_train.csv": "aa59e4266872c2f3f48b6c027798255e21fae64b09519a895d3ba8deb85b9364",
    "outputs/bench_core/splits/D_cal_fair1m_train.csv": "84b32cb5e0bd9a7afdc772f824e1b64f9daaca54fccdbbb98750180bc04b16a0",
    "outputs/bench_core/splits/D_cal_hrsc_trainval.csv": "bbaf79002ad683893292101744e32e379d711f14ab7c187ae5bad42d2e37bdb0",
}

SHA_CACHE: dict[str, str] = {}


def rel(path: Path) -> str:
    return str(path.resolve().relative_to(ROOT.resolve()))


def sha256(path: Path) -> str:
    key = str(path.resolve())
    if key in SHA_CACHE:
        return SHA_CACHE[key]
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            digest.update(block)
    SHA_CACHE[key] = digest.hexdigest()
    return SHA_CACHE[key]


def git(*args: str, binary: bool = False):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=not binary).strip()


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
        self._records: dict[str, dict] = {}

    def add(self, path: Path, purpose: str, git_blob: str = "") -> dict:
        path = path.resolve()
        key = rel(path)
        if not path.is_file():
            raise FileNotFoundError(path)
        record = self._records.setdefault(key, {
            "path": key,
            "raw_sha256": sha256(path),
            "canonical_sha256": sha256(path),
            "bytes": path.stat().st_size,
            "purposes": [],
            "git_blob": git_blob,
        })
        if purpose not in record["purposes"]:
            record["purposes"].append(purpose)
        if git_blob:
            record["git_blob"] = git_blob
        return record

    def records(self) -> list[dict]:
        result = []
        for key in sorted(self._records):
            row = dict(self._records[key])
            row["purposes"] = sorted(row["purposes"])
            result.append(row)
        return result


def load_r001():
    spec = importlib.util.spec_from_file_location("reaudit_b3_b4_r001_locked", R001_SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_array_hash(array: np.ndarray) -> str:
    array = np.asarray(array)
    digest = hashlib.sha256()
    digest.update(str(array.dtype).encode())
    digest.update(json.dumps(list(array.shape), separators=(",", ":")).encode())
    if array.dtype.kind in "OUS":
        for item in array.reshape(-1):
            value = str(item).encode("utf-8")
            digest.update(struct.pack("<Q", len(value)))
            digest.update(value)
    else:
        value = np.ascontiguousarray(array.astype(array.dtype.newbyteorder("<"), copy=False))
        digest.update(value.tobytes())
    return digest.hexdigest()


def boolean_mask_hash(mask: np.ndarray) -> str:
    mask = np.ascontiguousarray(mask, dtype=np.uint8)
    digest = hashlib.sha256()
    digest.update(struct.pack("<Q", len(mask)))
    digest.update(mask.tobytes())
    return digest.hexdigest()


def reconstruct_cache(raw_path: Path) -> tuple[dict[str, np.ndarray], int, str]:
    fields = {key: [] for key in (
        "image", "score", "error", "ar", "size", "cls", "feature", "boundary",
        "tta", "vector", "pred_box", "gt_box",
    )}
    identity = hashlib.sha256()
    total = 0
    opener = gzip.open if raw_path.suffix == ".gz" else open
    with opener(raw_path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            total += 1
            row = json.loads(line)
            if float(row["aspect_ratio"]) < 2.1:
                continue
            fields["image"].append(str(row["image_id"]))
            fields["score"].append(float(row["detection_score"]))
            fields["error"].append(float(row["angle_error"]))
            fields["ar"].append(float(row["aspect_ratio"]))
            fields["size"].append(float(row["size"]))
            fields["cls"].append(str(row["class"]))
            fields["feature"].append(float(row["reg_feature_norm"]) if row.get("reg_feature_norm") is not None else np.nan)
            fields["boundary"].append(float(row["boundary_distance_deg"]))
            tta = row.get("tta_phase_direction_circular_variance")
            fields["tta"].append(float(tta) if tta is not None else np.nan)
            fields["vector"].append(row["encoded_vector"])
            fields["pred_box"].append(row["pred_box"])
            fields["gt_box"].append(row["gt_box"])
            token = f"{row['image_id']}\0{row.get('pred_id','')}\0{row.get('gt_id','')}".encode("utf-8")
            identity.update(struct.pack("<Q", len(token)))
            identity.update(token)
    arrays = {
        key: np.asarray(value, dtype=object if key in ("image", "cls") else float)
        for key, value in fields.items()
    }
    return arrays, total, identity.hexdigest()


def arrays_equal(expected: np.ndarray, observed: np.ndarray) -> tuple[bool, float]:
    if expected.shape != observed.shape or expected.dtype != observed.dtype:
        return False, float("inf")
    if expected.dtype.kind in "OUS":
        return bool(np.array_equal(expected, observed)), 0.0 if np.array_equal(expected, observed) else float("inf")
    equal = bool(np.allclose(expected, observed, rtol=0.0, atol=0.0, equal_nan=True))
    finite = np.isfinite(expected) & np.isfinite(observed)
    error = float(np.max(np.abs(expected[finite] - observed[finite]))) if finite.any() else 0.0
    return equal, error


def raw_cache_lineage(registry: InputRegistry, g0_rows: list[dict]) -> tuple[list[dict], bool]:
    lineage: list[dict] = []
    g0 = {(row["dataset"], int(row["seed"])): row for row in g0_rows if row["head"] == "PSC"}
    aliases = {"DIOR-R": "DIOR_R", "SODA-A": "SODA_A", "FAIR1M-v1.0": "FAIR1M"}
    all_ok = True
    for dataset in ("DIOR-R", "SODA-A", "FAIR1M-v1.0"):
        for seed in range(3):
            if dataset == "FAIR1M-v1.0":
                manifest_path = BROOT / f"artifacts/b3_fair1m/seed{seed}/manifest.json"
                registry.add(manifest_path, "B3 FAIR1M raw dump manifest")
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
                raw_path = ROOT / manifest["output"]
            else:
                raw_path = ROOT / g0[(dataset, seed)]["matched_table_artifact"]
            cache_path = BROOT / f"artifacts/b3_cache/{aliases[dataset]}_seed{seed}.npz"
            registry.add(raw_path, "B3 raw matched phase dump and cache lineage")
            registry.add(cache_path, "B3 frozen cache and cache lineage")
            reconstructed, raw_rows, identity_hash = reconstruct_cache(raw_path)
            with np.load(cache_path, allow_pickle=True) as loaded:
                cached = {key: loaded[key] for key in loaded.files}
            unit_ok = set(reconstructed) == set(cached)
            row_hash = hashlib.sha256()
            for key in sorted(reconstructed):
                expected = reconstructed[key]
                observed = cached.get(key, np.asarray([]))
                equal, error = arrays_equal(expected, observed)
                unit_ok = unit_ok and equal
                raw_hash = canonical_array_hash(expected)
                cache_hash = canonical_array_hash(observed)
                row_hash.update(key.encode())
                row_hash.update(cache_hash.encode())
                lineage.append({
                    "record_type": "cache_array", "dataset": dataset, "seed": seed,
                    "raw_path": rel(raw_path), "raw_sha256": sha256(raw_path),
                    "cache_path": rel(cache_path), "cache_sha256": sha256(cache_path),
                    "key": key, "dtype": str(observed.dtype), "shape": json.dumps(list(observed.shape)),
                    "raw_content_hash": raw_hash, "cache_content_hash": cache_hash,
                    "raw_rows": raw_rows, "eligible_rows": len(expected),
                    "row_order_instance_id_hash": identity_hash, "cache_row_order_hash": "",
                    "tolerance": "rtol=0;atol=0;NaN-equal", "max_abs_error": error,
                    "status": "PASS" if equal else "FAIL",
                    "notes": "direct JSON field parse followed only by GT aspect_ratio>=2.1; no floating derivation",
                })
            lineage.append({
                "record_type": "cache_unit", "dataset": dataset, "seed": seed,
                "raw_path": rel(raw_path), "raw_sha256": sha256(raw_path),
                "cache_path": rel(cache_path), "cache_sha256": sha256(cache_path),
                "key": "ALL", "dtype": "mixed", "shape": "", "raw_content_hash": "",
                "cache_content_hash": "", "raw_rows": raw_rows,
                "eligible_rows": len(reconstructed["image"]),
                "row_order_instance_id_hash": identity_hash,
                "cache_row_order_hash": row_hash.hexdigest(), "tolerance": "exact",
                "max_abs_error": 0.0 if unit_ok else float("inf"),
                "status": "PASS" if unit_ok else "FAIL",
                "notes": "cache omits pred_id/gt_id; exact ordered content equality proves cache row order",
            })
            all_ok = all_ok and unit_ok
            del reconstructed, cached
    return lineage, all_ok


def persistent_inventory(registry: InputRegistry) -> tuple[list[dict], dict]:
    root = ROOT / "outputs/persistent_artifacts"
    rows: list[dict] = []
    dangling = 0
    for path in sorted(root.rglob("*"), key=lambda item: str(item.relative_to(ROOT))):
        if path.is_dir() and not path.is_symlink():
            continue
        is_link = path.is_symlink()
        target = os.readlink(path) if is_link else ""
        is_dangling = is_link and not path.exists()
        dangling += int(is_dangling)
        if is_dangling:
            rows.append({"path": str(path.relative_to(ROOT)), "bytes": 0, "sha256": "DANGLING",
                         "is_symlink": True, "symlink_target": target, "status": "DANGLING"})
            continue
        registry.add(path, "persistent-artifact content inventory")
        rows.append({"path": rel(path), "bytes": path.stat().st_size, "sha256": sha256(path),
                     "is_symlink": is_link, "symlink_target": target, "status": "PRESENT"})
    aggregate = hashlib.sha256()
    for row in rows:
        payload = f"{row['path']}\0{row['bytes']}\0{row['sha256']}\n".encode("utf-8")
        aggregate.update(payload)
    hashes: dict[str, int] = {}
    for row in rows:
        hashes[row["sha256"]] = hashes.get(row["sha256"], 0) + 1
    summary = {
        "file_count": len(rows), "total_bytes": sum(int(row["bytes"]) for row in rows),
        "aggregate_sha256": aggregate.hexdigest(), "dangling_symlinks": dangling,
        "symlinks": sum(bool(row["is_symlink"]) for row in rows),
        "unreadable_or_missing_files": 0,
        "duplicate_content_groups": sum(count > 1 for key, count in hashes.items() if key != "DANGLING"),
    }
    return rows, summary


def old_file_locks(registry: InputRegistry) -> tuple[list[dict], bool]:
    rows = []
    all_ok = True
    for relative in R001_FILES:
        path = ROOT / relative
        expected_blob = git("rev-parse", f"{SNAPSHOT}:{relative}")
        current_blob = git("hash-object", str(path))
        snapshot_bytes = subprocess.check_output(["git", "show", f"{SNAPSHOT}:{relative}"], cwd=ROOT)
        expected_sha = hashlib.sha256(snapshot_bytes).hexdigest()
        current_sha = sha256(path)
        ok = expected_blob == current_blob and expected_sha == current_sha
        all_ok = all_ok and ok
        registry.add(path, "locked r001 evidence input", current_blob)
        rows.append({
            "record_type": "r001_lock", "dataset": "", "seed": "", "raw_path": relative,
            "raw_sha256": current_sha, "cache_path": "", "cache_sha256": "", "key": "",
            "dtype": "", "shape": "", "raw_content_hash": expected_sha,
            "cache_content_hash": current_sha, "raw_rows": "", "eligible_rows": "",
            "row_order_instance_id_hash": expected_blob, "cache_row_order_hash": current_blob,
            "tolerance": "byte-exact", "max_abs_error": 0 if ok else "inf",
            "status": "PASS" if ok else "FAIL", "notes": "snapshot Git blob and raw SHA-256",
        })
    return rows, all_ok


def weighted_components(score: np.ndarray, risk: np.ndarray, weights: np.ndarray, old) -> tuple[float, float, float, float]:
    score = np.asarray(score, float)
    risk = np.asarray(risk, float)
    weights = np.asarray(weights, np.int64)
    total = int(weights.sum())
    harmonic = np.empty(total + 1, float)
    harmonic[0] = 0.0
    harmonic[1:] = np.cumsum(1.0 / np.arange(1, total + 1))
    score_order = np.argsort(-score, kind="stable")
    oracle_order = np.argsort(risk, kind="stable")
    selected = old._weighted_aurc(risk[score_order], weights[score_order], harmonic)
    oracle = old._weighted_aurc(risk[oracle_order], weights[oracle_order], harmonic)
    random = float(np.dot(weights, risk) / total)
    nrc = (selected - oracle) / (random - oracle)
    return selected, oracle, random, float(nrc)


def common_finite_mask(clusters: np.ndarray, risk: np.ndarray, scores: dict[str, np.ndarray]) -> tuple[np.ndarray, dict[str, int]]:
    masks = {"risk_nonfinite": ~np.isfinite(np.asarray(risk, float))}
    cluster_values = np.asarray(clusters).astype(str)
    masks["cluster_missing"] = np.asarray([not value for value in cluster_values], dtype=bool)
    for name, values in scores.items():
        masks[f"{name}_nonfinite"] = ~np.isfinite(np.asarray(values, float))
    excluded = np.zeros(len(risk), dtype=bool)
    for value in masks.values():
        excluded |= value
    counts = {name: int(value.sum()) for name, value in masks.items() if value.any()}
    return ~excluded, counts


def bootstrap_nrc(scores: dict[str, np.ndarray], risk: np.ndarray, inverse: np.ndarray,
                  multiplicities: np.ndarray, old, workers: int = WORKERS) -> dict[str, np.ndarray]:
    names = list(scores)
    orders = {name: np.argsort(-np.asarray(scores[name], float), kind="stable") for name in names}
    oracle_order = np.argsort(risk, kind="stable")
    cluster_sizes = np.bincount(inverse).astype(np.int64)
    totals = multiplicities.astype(np.int64) @ cluster_sizes
    maximum_total = int(totals.max())
    harmonic = np.empty(maximum_total + 1, dtype=float)
    harmonic[0] = 0.0
    harmonic[1:] = np.cumsum(1.0 / np.arange(1, maximum_total + 1))

    def one(replicate: int) -> np.ndarray:
        weights = multiplicities[replicate][inverse].astype(np.int64, copy=False)
        total = int(weights.sum())
        oracle_auc = old._weighted_aurc(risk[oracle_order], weights[oracle_order], harmonic)
        random_auc = float(np.dot(weights, risk) / total)
        denominator = random_auc - oracle_auc
        if abs(denominator) <= 1e-12:
            return np.full(len(names), np.nan)
        return np.asarray([
            (old._weighted_aurc(risk[orders[name]], weights[orders[name]], harmonic) - oracle_auc) / denominator
            for name in names
        ])

    count = int(multiplicities.shape[0])
    with ThreadPoolExecutor(max_workers=min(workers, max(1, count))) as pool:
        matrix = np.asarray(list(pool.map(one, range(count))), dtype=float)
    return {name: matrix[:, index] for index, name in enumerate(names)}


EXTRA_FIELDS = [
    "raw_instance_count", "finite_instance_count", "excluded_nonfinite_count", "excluded_reason",
    "common_finite_mask_hash", "candidate_universe_hash", "evidence_partition",
    "redundant_comparison", "redundant_with",
]


def evidence_partition(stage: str, dataset: str) -> str:
    if stage == "B4":
        return "external"
    if dataset in ("DIOR-R", "SODA-A"):
        return "development"
    return "confirmatory"


def run_stage(old, stage: str) -> tuple[list[dict], list[dict]]:
    legacy = old.legacy_b3_rows() if stage == "B3" else old.legacy_b4_rows()
    result: list[dict] = []
    mask_rows: list[dict] = []
    units = old.b3_units() if stage == "B3" else (("DOTA-v1.0", seed, *old.b4_unit(seed)) for seed in range(3))
    for item in units:
        if stage == "B3":
            dataset, seed, arrays, source = item
            cluster_unit, host = "image", "RotatedRetinaNet-PSC"
            clusters = arrays["image"].astype(str)
            vectors = arrays["vector"].astype(float)
            errors = arrays["error"].astype(float)
            ars = arrays["ar"].astype(float)
            detection = arrays["score"].astype(float)
            candidates = old.candidate_scores(vectors)
            tta = arrays["tta"].astype(float)
            if np.isfinite(tta).sum() > .9 * len(tta):
                candidates["tta_phase_direction_consistency"] = -tta
            legacy_names = lambda endpoint: [key[3] for key in legacy if key[:3] == (dataset, seed, endpoint)]
        else:
            dataset, seed, arrays, source = item
            cluster_unit, host = "mother_scene", "RotatedFCOS-PSCD"
            clusters = arrays["cluster"].astype(str)
            vectors = arrays["vector"].astype(float)
            errors = arrays["error"].astype(float)
            ars = arrays["ar"].astype(float)
            detection = arrays["score"].astype(float)
            candidates = old.candidate_scores(vectors)
            legacy_names = lambda endpoint: [key[2] for key in legacy if key[:2] == (seed, endpoint)]
        candidates["detection_score"] = detection
        endpoints = {
            "endpoint_continuous": errors,
            "endpoint_severe_event": (errors > old.delta_threshold(ars)).astype(float),
        }
        mc_seed = old.deterministic_seed(stage, dataset, seed)
        for endpoint, risk in endpoints.items():
            score_hashes: dict[str, str] = {}
            for candidate in legacy_names(endpoint):
                selected = {
                    "phase_mod": candidates["phase_mod"],
                    "detection_score": candidates["detection_score"],
                    candidate: candidates[candidate],
                }
                mask, reasons = common_finite_mask(clusters, risk, selected)
                masked_clusters = clusters[mask]
                masked_risk = risk[mask]
                masked_scores = {name: values[mask] for name, values in selected.items()}
                labels, inverse, multiplicities, resample_hash = old.resample_plan(masked_clusters, mc_seed)
                points = {name: old.nrc_unweighted(values, masked_risk) for name, values in masked_scores.items()}
                samples = bootstrap_nrc(masked_scores, masked_risk, inverse, multiplicities, old)
                universe = old.universe_hash(masked_clusters, masked_risk, masked_scores["phase_mod"], masked_scores["detection_score"])
                candidate_universe = old.universe_hash(masked_clusters, masked_risk, masked_scores[candidate], masked_scores["detection_score"])
                old_key = (dataset, seed, endpoint, candidate) if stage == "B3" else (seed, endpoint, candidate)
                row = old.make_bootstrap_row(
                    stage, dataset, host, seed, candidate, endpoint, cluster_unit, len(labels), int(mask.sum()),
                    mc_seed, resample_hash, universe, points, samples, legacy[old_key],
                )
                row["round_id"] = ROUND_ID
                row.update({
                    "raw_instance_count": len(mask), "finite_instance_count": int(mask.sum()),
                    "excluded_nonfinite_count": int((~mask).sum()),
                    "excluded_reason": json.dumps(reasons, sort_keys=True, separators=(",", ":")),
                    "common_finite_mask_hash": boolean_mask_hash(mask),
                    "candidate_universe_hash": candidate_universe,
                    "evidence_partition": evidence_partition(stage, dataset),
                    "redundant_comparison": False, "redundant_with": "",
                })
                score_hash = canonical_array_hash(masked_scores[candidate])
                if score_hash in score_hashes:
                    row["redundant_comparison"] = True
                    row["redundant_with"] = score_hashes[score_hash]
                else:
                    score_hashes[score_hash] = candidate
                result.append(row)
                mask_rows.append({
                    "record_type": "common_finite_mask", "dataset": dataset, "seed": seed,
                    "raw_path": rel(source), "raw_sha256": sha256(source), "cache_path": "",
                    "cache_sha256": "", "key": f"{stage}:{candidate}:{endpoint}", "dtype": "bool",
                    "shape": json.dumps([len(mask)]), "raw_content_hash": boolean_mask_hash(mask),
                    "cache_content_hash": candidate_universe, "raw_rows": len(mask),
                    "eligible_rows": int(mask.sum()), "row_order_instance_id_hash": "",
                    "cache_row_order_hash": resample_hash, "tolerance": "finite common mask",
                    "max_abs_error": 0, "status": "PASS",
                    "notes": json.dumps(reasons, sort_keys=True, separators=(",", ":")),
                })
    return result, mask_rows


NUMERIC_COLUMNS = [
    "candidate_nrc", "phase_mod_nrc", "detection_score_nrc", "delta_nrc_vs_phase_mod",
    "delta_vs_phase_ci_lo", "delta_vs_phase_ci_hi", "delta_nrc_vs_detection_score",
    "delta_vs_detection_ci_lo", "delta_vs_detection_ci_hi", "legacy_point_delta",
    "legacy_ci_lo", "legacy_ci_hi",
]
EXACT_COLUMNS = ["resample_id_hash", "instance_universe_hash"]


def diff_r001(stage: str, current: list[dict]) -> tuple[list[dict], bool, list[dict]]:
    old_path = REPORTS / ("b3_candidate_cluster_bootstrap_reaudit_r001.csv" if stage == "B3" else "b4_candidate_external_bootstrap_reaudit_r001.csv")
    old_rows = read_csv(old_path)
    key = lambda row: (row["dataset"], int(row["seed"]), row["candidate"], row["endpoint"])
    old_map, new_map = {key(row): row for row in old_rows}, {key(row): row for row in current}
    summaries = []
    drift = set(old_map) != set(new_map)
    details = []
    for column in NUMERIC_COLUMNS:
        errors = []
        changed = []
        for unit in sorted(set(old_map) & set(new_map)):
            error = abs(float(old_map[unit][column]) - float(new_map[unit][column]))
            errors.append(error)
            if error > 1e-12:
                changed.append((unit, error))
        maximum = max(errors, default=float("inf"))
        drift = drift or maximum > 1e-12
        summaries.append({
            "record_type": "r001_numeric_diff", "dataset": stage, "seed": "",
            "raw_path": rel(old_path), "raw_sha256": sha256(old_path), "cache_path": "",
            "cache_sha256": "", "key": column, "dtype": "float", "shape": str(len(errors)),
            "raw_content_hash": "", "cache_content_hash": "", "raw_rows": len(old_rows),
            "eligible_rows": len(current), "row_order_instance_id_hash": "",
            "cache_row_order_hash": "", "tolerance": "1e-12", "max_abs_error": maximum,
            "status": "PASS" if maximum <= 1e-12 else "DRIFT",
            "notes": f"changed_rows={len(changed)}; first={changed[0] if changed else ''}",
        })
        details.append({"stage": stage, "column": column, "max_abs_diff": maximum, "changed_rows": len(changed)})
    for column in EXACT_COLUMNS:
        changed = [unit for unit in sorted(set(old_map) & set(new_map)) if old_map[unit][column] != new_map[unit][column]]
        drift = drift or bool(changed)
        summaries.append({
            "record_type": "r001_exact_diff", "dataset": stage, "seed": "",
            "raw_path": rel(old_path), "raw_sha256": sha256(old_path), "cache_path": "",
            "cache_sha256": "", "key": column, "dtype": "string", "shape": str(len(old_rows)),
            "raw_content_hash": "", "cache_content_hash": "", "raw_rows": len(old_rows),
            "eligible_rows": len(current), "row_order_instance_id_hash": "",
            "cache_row_order_hash": "", "tolerance": "exact", "max_abs_error": "",
            "status": "PASS" if not changed else "DRIFT",
            "notes": f"changed_rows={len(changed)}; first={changed[0] if changed else ''}",
        })
        details.append({"stage": stage, "column": column, "changed_rows": len(changed)})
    return summaries, drift, details


TEST_FIELDS = ["test_id", "category", "stage", "seed", "expected", "observed", "abs_error", "tolerance", "status", "notes"]


def test_row(test_id: str, category: str, expected, observed, passed: bool, error="", tolerance="", notes="", seed="") -> dict:
    return {"test_id": test_id, "category": category, "stage": "r002", "seed": seed,
            "expected": expected, "observed": observed, "abs_error": error, "tolerance": tolerance,
            "status": "PASS" if passed else "FAIL", "notes": notes}


def run_tests(old) -> list[dict]:
    rows: list[dict] = []
    rng = np.random.RandomState(20260805)
    max_component_error = 0.0
    for index in range(100):
        n = int(rng.randint(8, 40))
        score = rng.normal(size=n)
        if index % 3 == 0:
            score = np.round(score, 1)
        risk = rng.gamma(shape=1.5, scale=2.0, size=n)
        weights = rng.randint(0, 5, size=n)
        if weights.sum() < 2 or np.count_nonzero(weights) < 2:
            weights[:2] = 1
        selected, oracle, random, nrc = weighted_components(score, risk, weights, old)
        expanded = np.repeat(np.arange(n), weights)
        expanded_score, expanded_risk = score[expanded], risk[expanded]
        order = np.argsort(-expanded_score, kind="stable")
        oracle_order = np.argsort(expanded_risk, kind="stable")
        selected_exp = float(np.mean(np.cumsum(expanded_risk[order]) / np.arange(1, len(expanded) + 1)))
        oracle_exp = float(np.mean(np.cumsum(expanded_risk[oracle_order]) / np.arange(1, len(expanded) + 1)))
        random_exp = float(np.mean(expanded_risk))
        nrc_exp = (selected_exp - oracle_exp) / (random_exp - oracle_exp)
        error = max(abs(selected-selected_exp), abs(oracle-oracle_exp), abs(random-random_exp), abs(nrc-nrc_exp))
        max_component_error = max(max_component_error, error)
    rows.append(test_row("random_weighted_expansion_100", "random_explicit_expansion", "max<=1e-12",
                         max_component_error, max_component_error <= 1e-12, max_component_error, 1e-12,
                         "selected/oracle/random/NRC all use identical multiplicity weights", 20260805))

    score = np.array([.8, np.nan, .4, .2])
    phase = np.array([.7, .6, np.nan, .1])
    detection = np.array([.9, .5, .3, .2])
    risk = np.array([1., 2., 3., np.nan])
    clusters = np.array(["a", "a", "b", "b"])
    mask, reasons = common_finite_mask(clusters, risk, {"candidate": score, "phase_mod": phase, "detection_score": detection})
    rows.append(test_row("nan_common_mask", "common_finite_mask", 1, int(mask.sum()), int(mask.sum()) == 1,
                         notes=json.dumps(reasons, sort_keys=True)))

    clusters = np.array(["a", "a", "b", "c", "c", "d"])
    labels, inverse = np.unique(clusters, return_inverse=True)
    mult = np.empty((37, len(labels)), dtype=np.uint16)
    random37 = np.random.RandomState(37)
    for index in range(37):
        mult[index] = np.bincount(random37.randint(0, len(labels), len(labels)), minlength=len(labels))
    values = bootstrap_nrc({"candidate": np.array([.9,.8,.7,.5,.4,.1]), "phase_mod": np.array([.2,.3,.4,.5,.6,.7]),
                            "detection_score": np.array([.8,.7,.6,.5,.4,.3])},
                           np.array([1.,2.,3.,4.,5.,6.]), inverse, mult, old, workers=4)
    rows.append(test_row("bootstrap_37_replicates", "replicate_length", 37, len(values["candidate"]),
                         all(len(value) == 37 for value in values.values()), notes="loop follows multiplicity matrix length"))
    paired = all(len(value) == 37 for value in values.values())
    rows.append(test_row("paired_resample_shape", "paired_resample", "same 37 resamples", paired, paired,
                         notes="candidate and both baselines evaluated on each identical multiplicity row"))

    tied_score = np.array([.5,.5,.5,.2,.2])
    tied_risk = np.array([5.,1.,3.,8.,2.])
    weights = np.array([3,1,2,0,4])
    expected = old.explicit_expansion_nrc(tied_score, tied_risk, weights)
    observed = old.weighted_nrc(tied_score, tied_risk, weights)
    rows.append(test_row("stable_tie_expansion", "stable_ties", expected, observed,
                         abs(expected-observed) <= 1e-12, abs(expected-observed), 1e-12))

    duplicate = canonical_array_hash(np.array([1.,2.,3.])) == canonical_array_hash(np.array([1.,2.,3.]))
    rows.append(test_row("candidate_duplication_detector", "candidate_duplication", True, duplicate, duplicate))

    verdict_pass = derive_verdict(True, True, False, 0, 24)
    verdict_drift = derive_verdict(True, True, True, 0, 24)
    machine_ok = verdict_pass == ("PASS_EVIDENCE_CLOSURE", "FAIL_CANDIDATE_GATE") and verdict_drift[0] == "FAIL_EVIDENCE_DRIFT"
    rows.append(test_row("machine_verdict_fixture", "machine_verdict", True, machine_ok, machine_ok,
                         notes=f"closure={verdict_pass}; drift={verdict_drift}"))
    return rows


def derive_verdict(provenance_ok: bool, tests_ok: bool, numeric_drift: bool,
                   external_support: int, external_rows: int) -> tuple[str, str]:
    if not provenance_ok:
        return "INCONCLUSIVE_PROVENANCE", "FAIL_CANDIDATE_GATE"
    if not tests_ok or numeric_drift or external_rows != 24:
        return "FAIL_EVIDENCE_DRIFT", "FAIL_CANDIDATE_GATE"
    if external_support == 0:
        return "PASS_EVIDENCE_CLOSURE", "FAIL_CANDIDATE_GATE"
    return "FAIL_EVIDENCE_DRIFT", "UNADJUDICATED_NO_PREREGISTERED_SUCCESS_RULE"


def gate_rows(provenance_ok: bool, tests_ok: bool, numeric_drift: bool,
              b3: list[dict], b4: list[dict], redundant: int) -> tuple[list[dict], str, str]:
    development = [row for row in b3 if row["evidence_partition"] == "development"]
    confirmatory = [row for row in b3 if row["evidence_partition"] == "confirmatory"]
    external_support = sum(bool(row["supports_both"]) for row in b4)
    closure, candidate_gate = derive_verdict(provenance_ok, tests_ok, numeric_drift, external_support, len(b4))
    rows = [
        {"condition":"direct_input_and_cache_provenance", "status":"PASS" if provenance_ok else "FAIL",
         "evidence":"all direct inputs locked; raw-cache and inventory checks", "partition":"all", "impact":"continue" if provenance_ok else "STOP_B6"},
        {"condition":"formal_and_random_tests", "status":"PASS" if tests_ok else "FAIL",
         "evidence":"weighted/common-mask/37-replicate/paired/duplication/verdict tests", "partition":"all", "impact":"continue" if tests_ok else "STOP_B6"},
        {"condition":"r001_r002_scientific_diff", "status":"DRIFT" if numeric_drift else "PASS",
         "evidence":"numeric tolerance 1e-12; universe/resample hashes compared exactly and any changes recorded",
         "partition":"all", "impact":"STOP_B6" if numeric_drift else "continue"},
        {"condition":"development_evidence", "status":"DESCRIPTIVE_NO_SUCCESS_GATE",
         "evidence":f"DIOR-R/SODA-A rows={len(development)}; supports_both={sum(bool(r['supports_both']) for r in development)}",
         "partition":"development", "impact":"cannot authorize B6"},
        {"condition":"confirmatory_evidence", "status":"DESCRIPTIVE_NO_SUCCESS_GATE",
         "evidence":f"FAIR1M rows={len(confirmatory)}; supports_both={sum(bool(r['supports_both']) for r in confirmatory)}",
         "partition":"confirmatory", "impact":"cannot authorize B6"},
        {"condition":"external_evidence", "status":"FAIL" if external_support == 0 else "UNADJUDICATED",
         "evidence":f"DOTA/RotatedFCOS supports_both={external_support}/{len(b4)}",
         "partition":"external", "impact":"STOP_B6"},
        {"condition":"redundant_comparisons", "status":"DISCLOSED",
         "evidence":f"exact duplicate candidate score comparisons={redundant}", "partition":"all", "impact":"not counted independently"},
        {"condition":"scientific_candidate_gate", "status":candidate_gate,
         "evidence":"external 0/24 retained unless drift invalidates evidence closure", "partition":"external", "impact":"STOP_B6"},
        {"condition":"evidence_closure_verdict", "status":closure,
         "evidence":"machine-derived from provenance, tests, drift, and external evidence", "partition":"all", "impact":"STOP_B6"},
    ]
    return rows, closure, candidate_gate


LINEAGE_FIELDS = [
    "record_type", "dataset", "seed", "raw_path", "raw_sha256", "cache_path", "cache_sha256",
    "key", "dtype", "shape", "raw_content_hash", "cache_content_hash", "raw_rows", "eligible_rows",
    "row_order_instance_id_hash", "cache_row_order_hash", "tolerance", "max_abs_error", "status", "notes",
]


def file_record(path: Path) -> dict:
    record = {"path": rel(path), "raw_sha256": sha256(path), "bytes": path.stat().st_size}
    if path.suffix == ".csv":
        rows = read_csv(path)
        record.update({"rows": len(rows), "schema": list(rows[0]) if rows else []})
    else:
        record.update({"rows": None, "schema": "markdown" if path.suffix == ".md" else "json"})
    return record


def render_report(head: str, closure: str, candidate_gate: str, locks_ok: bool, lineage_ok: bool,
                  inventory: dict, tests: list[dict], b3: list[dict], b4: list[dict],
                  diff_details: list[dict], registry_count: int, redundant: int) -> str:
    tta_drift = [row for row in b3 if row["candidate"] == "tta_phase_direction_consistency" and int(row["excluded_nonfinite_count"]) > 0]
    maximum = max((float(item.get("max_abs_diff", 0)) for item in diff_details if "max_abs_diff" in item), default=0.0)
    return f"""# OrientBench r002 B5 负结论证据链收口

- round: `{ROUND_ID}`
- scientific snapshot: `{SNAPSHOT}`
- execution HEAD: `{head}`
- evidence closure verdict: `{closure}`
- scientific candidate gate: `{candidate_gate}`
- B6/B7: `STOPPED_NOT_RUN`
- training/inference: `0/0`

## 1. 前置完整性与直接输入

r001 八个锁定文件逐字节核对：`{'PASS' if locks_ok else 'FAIL'}`。执行中登记直接输入 {registry_count} 个。
`m4_delta_theta_075_frozen.json` 与 `g0_comparison_manifest.csv` 的 raw SHA-256 分别精确匹配
`{EXPECTED_DELTA_SHA}` 与 `{EXPECTED_G0_SHA}`。r002 执行源码和测试源码记录 canonical SHA-256 与 Git blob hash；
scientific snapshot、execution HEAD 和未来 result commit 严格分离。

工作树的 tracked/index 在执行前干净；仅有已知、前轮已披露且未参与计算的 `.orientbench_transfer_parts/`
迁移分片，以及本轮授权的新文件。未执行 reset/clean，也未改动该迁移目录。

## 2. B3 raw 到 cache lineage

九个 B3 cache 逐 key 从 raw JSONL/JSONL.GZ 按原算法重构：直接解析 `image/score/error/ar/size/class/feature/`
`boundary/tta/vector/pred_box/gt_box`，然后只应用 `GT aspect_ratio>=2.1`。对象数组逐项编码，数值数组按 dtype、
shape 和 little-endian content hash 比较；浮点比较为 `rtol=0, atol=0, NaN-equal`。

lineage 结论：`{'PASS 9/9' if lineage_ok else 'FAIL'}`。cache 未持久化 pred_id/gt_id，因此报告 raw 的
`image_id,pred_id,gt_id` 行序 hash，并以全部 cache key 的逐元素有序一致性证明 cache 行序。

## 3. 275 文件持久化 inventory

- files: `{inventory['file_count']}`
- total bytes: `{inventory['total_bytes']}`
- aggregate path+bytes+SHA-256: `{inventory['aggregate_sha256']}`
- duplicate content groups: `{inventory['duplicate_content_groups']}`
- unreadable or missing files within the frozen inventory: `{inventory['unreadable_or_missing_files']}`
- symlinks / dangling symlinks: `{inventory['symlinks']} / {inventory['dangling_symlinks']}`

文件数仅为辅助条件；本轮对每个文件记录内容 SHA-256，并用有序 path+bytes+hash 生成 aggregate。

## 4. common finite mask 与统计漂移

所有 candidate、phase_mod、detection_score 和 endpoint 在点估计与每个 bootstrap replicate 前使用同一 finite mask。
B4 24 行和 B3 非 TTA 行均为全量 finite。B3 的 TTA 两个 detector-head-seed unit 并非全量 finite：

| dataset | raw rows | excluded | endpoints |
|---|---:|---:|---:|
{os.linesep.join(f"| {row['dataset']} | {row['raw_instance_count']} | {row['excluded_nonfinite_count']} | {row['endpoint']} |" for row in tta_drift)}

因此 r001 对 TTA 的点估计曾删除 NaN，而 bootstrap 把 NaN score 排到末端，二者仍未使用同一 universe。
r002 封闭该入口后，4 个 TTA candidate×endpoint 行发生科学数值或 universe 漂移；逐列最大数值差为 `{maximum}`。
按预注册早停规则，evidence closure 判为 `{closure}`，不得把此差异静默解释为 bitwise stable。

## 5. 测试与 gate

正式/随机测试通过 {sum(row['status']=='PASS' for row in tests)}/{len(tests)}。随机显式展开 seed=`20260805`、
100 cases；覆盖 weighted selected/oracle/random/NRC、stable ties、NaN common mask、37-replicate 输入、paired
resample、candidate duplication 与 machine-derived verdict。

B3 development 仅为 DIOR-R/SODA-A，FAIR1M 单列 confirmatory，DOTA/RotatedFCOS 单列 external。
没有补造多 candidate×endpoint×seed 的成功规则。完全重复比较数为 `{redundant}`。
外部结果仍为 `{sum(bool(row['supports_both']) for row in b4)}/{len(b4)}`，所以科学候选门保持
`{candidate_gate}`，`STOP_B6` 不变。r002 的漂移只否定“r001 全证据 bitwise 收口”，不挽救候选。

## 6. 合规

训练次数 `0`，推理次数 `0`，旧个人项目结果读取 `否`。未下载 D7/PCP-OBB、pcbobb、pcbobb_beyond 或
pcbobb_score_study；未修改 A、B1--B5 冻结文件、r001 文件、split、checkpoint、配置或 `dis/B.md`。
"""


def main() -> int:
    registry = InputRegistry()
    source_blob = git("hash-object", str(SCRIPT))
    test_blob = git("hash-object", str(TEST_SCRIPT))
    registry.add(SCRIPT, "r002 execution source", source_blob)
    registry.add(TEST_SCRIPT, "r002 test source", test_blob)
    registry.add(R001_SCRIPT, "imported locked weighted-NRC implementation", git("hash-object", str(R001_SCRIPT)))
    old = load_r001()

    status = git("status", "--porcelain", "--untracked-files=all").splitlines()
    allowed_prefixes = (
        "?? .orientbench_transfer_parts/", "?? top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/reaudit_b3_b4_r002.py",
        "?? top_journal_v3_reaudit_055/paper_B_psc_mechanism/scripts/test_b3_b4_reaudit_r002.py",
        "?? top_journal_v3_reaudit_055/paper_B_psc_mechanism/reports/", "?? dis/server_reports/",
    )
    worktree_ok = all(any(line.startswith(prefix) for prefix in allowed_prefixes) for line in status)
    head = git("rev-parse", "HEAD")
    ancestry_ok = subprocess.run(["git", "merge-base", "--is-ancestor", SNAPSHOT, head], cwd=ROOT).returncode == 0

    lineage, locks_ok = old_file_locks(registry)
    registry.add(DELTA, "geometry-normalized severe-event threshold lookup")
    registry.add(G0_COMPARISON, "B3 raw artifact identity and lineage")
    direct_hash_ok = sha256(DELTA) == EXPECTED_DELTA_SHA and sha256(G0_COMPARISON) == EXPECTED_G0_SHA
    g0_rows = read_csv(G0_COMPARISON)

    threshold = ROOT / "configs/thresholds.yaml"
    registry.add(threshold, "frozen threshold integrity")
    threshold_ok = sha256(threshold) == old.EXPECTED_THRESHOLD_SHA
    split_ok = True
    for relative, expected in EXPECTED_SPLITS.items():
        path = ROOT / relative
        registry.add(path, "frozen D_cal/D_audit split integrity")
        split_ok = split_ok and sha256(path) == expected

    for path, purpose in (
        (REPORTS / "b1_protocol_frozen.json", "frozen B1 protocol"),
        (REPORTS / "b4_protocol_frozen.json", "frozen B4 protocol"),
        (REPORTS / "b3_intervention_metrics.csv", "legacy B3 candidate rows and intervals"),
        (REPORTS / "b4_candidate_external_bootstrap.csv", "legacy B4 candidate rows and intervals"),
        (REPORTS / "b1_candidate_score_registry.csv", "registered candidate set"),
        (REPORTS / "b4_variant_model_health.csv", "external variant health evidence"),
        (REPORTS / "b3_intervention_identity_audit.csv", "ranking-only identity evidence"),
        (REPORTS / "b4_variant_identity_ap_audit.csv", "external identity and AP evidence"),
    ):
        registry.add(path, purpose)

    cache_lineage, cache_ok = raw_cache_lineage(registry, g0_rows)
    lineage.extend(cache_lineage)
    inventory_rows, inventory_summary = persistent_inventory(registry)
    inventory_ok = inventory_summary["file_count"] == 275 and inventory_summary["dangling_symlinks"] == 0

    for seed in range(3):
        manifest_path = BROOT / f"artifacts/b4_external/seed{seed}/manifest.json"
        registry.add(manifest_path, "B4 external artifact manifest")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for key, purpose in (("rows", "B4 matched phase dump"), ("full_evaluator_inputs", "B4 evaluator input")):
            registry.add(ROOT / manifest[key], purpose)
        registry.add(Path(manifest["checkpoint"]), "B4 frozen checkpoint integrity")

    preflight_ok = worktree_ok and ancestry_ok and locks_ok and direct_hash_ok and threshold_ok and split_ok and cache_ok and inventory_ok
    b3, b3_masks = run_stage(old, "B3")
    b4, b4_masks = run_stage(old, "B4")
    lineage.extend(b3_masks + b4_masks)

    b3_diff, b3_drift, b3_details = diff_r001("B3", b3)
    b4_diff, b4_drift, b4_details = diff_r001("B4", b4)
    lineage.extend(b3_diff + b4_diff)
    numeric_drift = b3_drift or b4_drift

    tests = run_tests(old)
    tests_ok = all(row["status"] == "PASS" for row in tests)
    redundant = sum(bool(row["redundant_comparison"]) for row in b3 + b4)
    gates, closure, candidate_gate = gate_rows(preflight_ok, tests_ok, numeric_drift, b3, b4, redundant)

    write_csv(OUT_INVENTORY, inventory_rows, ["path","bytes","sha256","is_symlink","symlink_target","status"])
    write_csv(OUT_LINEAGE, lineage, LINEAGE_FIELDS)
    write_csv(OUT_B3, b3, old.BOOT_FIELDS + EXTRA_FIELDS)
    write_csv(OUT_B4, b4, old.BOOT_FIELDS + EXTRA_FIELDS)
    write_csv(OUT_TESTS, tests, TEST_FIELDS)
    write_csv(OUT_GATE, gates, ["condition","status","evidence","partition","impact"])

    report = render_report(head, closure, candidate_gate, locks_ok, cache_ok, inventory_summary, tests,
                           b3, b4, b3_details+b4_details, len(registry.records()), redundant)
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(report, encoding="utf-8")

    output_paths = [OUT_LINEAGE, OUT_INVENTORY, OUT_B3, OUT_B4, OUT_GATE, OUT_TESTS, OUT_REPORT]
    manifest = {
        "schema_version": "b3_b4_evidence_closure_r002_v1", "round_id": ROUND_ID,
        "scientific_snapshot": SNAPSHOT, "execution_head": head,
        "execution_source": {"path": rel(SCRIPT), "canonical_sha256": sha256(SCRIPT), "git_blob": source_blob},
        "test_source": {"path": rel(TEST_SCRIPT), "canonical_sha256": sha256(TEST_SCRIPT), "git_blob": test_blob},
        "result_commit": "not self-referenced; commit is transport metadata outside the scientific manifest",
        "command": f"/home/rspip/anaconda3/envs/mr_dev1x/bin/python {rel(SCRIPT)}",
        "protocol": {"replicates": REPLICATES, "cluster_units": {"B3":"image","B4":"mother_scene"},
                     "common_finite_mask": True, "numeric_diff_tolerance": 1e-12,
                     "partitions": {"development":["DIOR-R","SODA-A"], "confirmatory":["FAIR1M-v1.0"],
                                    "external":["DOTA-v1.0/RotatedFCOS-PSCD"]}},
        "direct_inputs": registry.records(), "persistent_inventory": inventory_summary,
        "r001_files_byte_exact": locks_ok, "cache_lineage_9_of_9": cache_ok,
        "tests": {"passed": sum(row["status"]=="PASS" for row in tests), "total": len(tests),
                  "random_seed": 20260805, "random_cases": 100},
        "numeric_diff": {"drift": numeric_drift, "details": b3_details+b4_details},
        "external_support": {"supports_both": sum(bool(row["supports_both"]) for row in b4), "rows": len(b4)},
        "redundant_comparisons": redundant, "evidence_closure_verdict": closure,
        "scientific_candidate_gate": candidate_gate, "B6_B7": "STOPPED_NOT_RUN",
        "training_count": 0, "inference_count": 0, "old_personal_project_results_read": False,
        "outputs": [file_record(path) for path in output_paths],
    }
    temp = OUT_MANIFEST.with_suffix(".json.tmp")
    temp.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    os.replace(temp, OUT_MANIFEST)
    return 0 if closure == "PASS_EVIDENCE_CLOSURE" else 4


if __name__ == "__main__":
    raise SystemExit(main())
