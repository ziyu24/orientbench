"""Image-level finite-sample risk control for command 069.

The formal exchangeable unit is the complete evaluation-image universe, not
the subset of images that happen to have a matched ar>=2.1 prediction. D_cal
is deterministically split again: fit images define candidate thresholds (and
fit the appendix-only geometry score), calibration images are used only for
Hoeffding-Bentkus LTT, and D_audit is report-only.

Primary endpoint: detection score x geometry-normalized severe event.
The target-GT-fitted geometry score is emitted only as an appendix analysis
after the preregistered M2 failure. Instance-weighted risks are empirical and
receive image-cluster bootstrap intervals; instance-i.i.d. exact-binomial
calculations appear only in the explicitly labelled legacy comparison.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
from scipy.stats import beta
from sklearn.ensemble import HistGradientBoostingRegressor

sys.path.insert(0, "/home/rspip/cqc/pro/study/orientbench/scripts")
import m069_common as M
from orientbench.data.splits import assign_split


ROOT = Path("/home/rspip/cqc/pro/study/orientbench")
REP = ROOT / "top_journal_v3_reaudit_055" / "reports"
DOC = ROOT / "docs"
LOG = ROOT / "top_journal_v3_reaudit_055" / "logs" / "m069"
PROTO_PATH = REP / "m3_image_level_protocol_frozen.json"
FROZEN_PROTOCOL_SHA256 = "d88e0d4f3866ced04efc6e06dfb10ea55502bf409d827cb8b2eb7d048492a8e5"
RISK_EVENT = "geometry_normalized_severe"
BOOTSTRAP_REPS = 1000
_ROLE_VIEW_CACHE: dict[tuple[str, int, int, int, int, int], dict] = {}

# Each A--F forward artifact persists a complete image-universe CSV, including
# zero-GT/zero-match images, and hash-binds it in its manifest.  The registered
# annotation directories below are optional identity cross-checks only.
IMAGE_UNIVERSE = {
    "DIOR-R": {
        "path": ROOT / "top_journal_v3_reaudit_055" / "data_prep" / "DIOR" / "annfiles_dotaformat" / "test",
        "suffix": ".txt",
        "expected_images": 11738,
        "expected_gt": 124445,
    },
    "FAIR1M-v1.0": {
        "path": Path("/home/rspip/cqc/data/dataset/fair1m1.0/split/val_20/annfiles"),
        "suffix": ".xml",
        "expected_images": 4362,
        "expected_gt": 78644,
    },
    "SODA-A": {
        "path": Path("/home/rspip/cqc/data/dataset/SODA-A/dota_format_tiled_ss/val_tiled/annfiles"),
        "suffix": ".txt",
        "expected_images": 22994,
        "expected_gt": 449644,
    },
}

# The 052 DIOR matched tables were built against the known 5,863-image partial
# GT, not the 11,738-image K1 full-test GT. They must never enter formal M3.
KNOWN_PARTIAL_DIOR_FRAGMENT = "outputs/persistent_artifacts/orientbench_real_052/matched_tables/DIOR-R"


class InputValidationError(RuntimeError):
    """Raised before any result is written when formal M3 inputs are invalid."""


def lg(message: str) -> None:
    LOG.mkdir(parents=True, exist_ok=True)
    with (LOG / "m3.log").open("a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%F %T')}] {message}\n")
    print(message, flush=True)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def hash_ids(ids: np.ndarray) -> str:
    h = hashlib.sha256()
    for image_id in ids:
        h.update(str(image_id).encode("utf-8"))
        h.update(b"\n")
    return h.hexdigest()


def _atomic_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if not rows and not fieldnames:
        raise RuntimeError(f"refusing to write headerless empty CSV: {path}")
    tmp = path.with_suffix(path.suffix + ".tmp")
    names = fieldnames or list(rows[0].keys())
    with tmp.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=names, extrasaction="raise")
        writer.writeheader()
        writer.writerows(rows)
    os.replace(tmp, path)


def _atomic_json(path: Path, value: object) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)


def _atomic_text(path: Path, value: str) -> None:
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(value, encoding="utf-8")
    os.replace(tmp, path)


def validate_frozen_protocol() -> tuple[dict, str]:
    if not PROTO_PATH.is_file():
        raise InputValidationError(f"missing frozen M3 protocol: {PROTO_PATH}")
    protocol_sha = sha256_file(PROTO_PATH)
    if protocol_sha != FROZEN_PROTOCOL_SHA256:
        raise InputValidationError(
            f"frozen M3 protocol changed: expected {FROZEN_PROTOCOL_SHA256}, got {protocol_sha}"
        )
    protocol = json.loads(PROTO_PATH.read_text(encoding="utf-8"))
    required = {
        "exchangeable_unit": "image",
        "delta_confidence": 0.1,
    }
    for key, expected in required.items():
        if protocol.get(key) != expected:
            raise InputValidationError(f"invalid frozen protocol {key}: {protocol.get(key)!r}")
    if protocol.get("primary_loss", {}).get("range") != [0, 1]:
        raise InputValidationError("primary loss is not frozen as bounded [0,1]")
    if "exact binomial is NOT used" not in protocol.get("primary_loss", {}).get("note", ""):
        raise InputValidationError("frozen protocol does not prohibit primary-loss exact binomial")
    expected_scores = {
        "detection_score", "geometry_score_upper_bound", "phase_mod",
        "negative_phase_mod", "tta_neg_circular_var",
    }
    if set(protocol.get("scores_tested", [])) != expected_scores:
        raise InputValidationError(
            f"frozen score menu changed: {protocol.get('scores_tested')!r}"
        )
    # In the frozen text, "CALIBRATION split" is the outer frozen D_cal.
    # Its own `splits` field requires a deterministic fit/calib subdivision.
    # Candidate construction therefore uses D_cal-fit and HB LTT uses the
    # disjoint D_cal-calib.  Fail closed if either frozen clause disappears.
    sequence = protocol.get("candidate_threshold_sequence", {})
    if "CALIBRATION split" not in str(sequence.get("space", "")):
        raise InputValidationError("frozen candidate family no longer names the outer calibration split")
    split_text = str(protocol.get("splits", ""))
    if "fit/calib" not in split_text or "deterministic" not in split_text:
        raise InputValidationError("frozen protocol no longer requires deterministic D_cal fit/calib separation")
    return protocol, protocol_sha


def load_image_universe(cell: str, dataset: str) -> tuple[np.ndarray, dict]:
    """Load the manifest-hash-bound persistent universe for one formal cell.

    External annotation directories are an optional identity cross-check only;
    they are not the formal source and their absence does not block replay.
    """
    if dataset not in IMAGE_UNIVERSE:
        raise InputValidationError(f"no complete image-universe source registered for {dataset}")
    spec = IMAGE_UNIVERSE[dataset]
    path = Path(M.UNIVERSE[cell])
    if not path.is_file() or path.stat().st_size == 0 or "/dev/shm" in str(path):
        raise InputValidationError(f"missing or volatile persistent image universe for {cell}: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        fields = set(reader.fieldnames or [])
        rows = list(reader)
    required = {
        "cell", "dataset", "image_id", "image_path",
        "d_cal_daudit_split_flag", "n_gt", "n_predictions",
    }
    if not required.issubset(fields):
        raise InputValidationError(f"persistent image-universe schema mismatch for {cell}: {fields}")
    if any(row["cell"] != cell or row["dataset"] != dataset for row in rows):
        raise InputValidationError(f"persistent image-universe identity mismatch for {cell}")
    ids = [str(row["image_id"]) for row in rows]
    if len(ids) != len(set(ids)):
        raise InputValidationError(f"duplicate image ids in {path}")
    if len(ids) != spec["expected_images"]:
        raise InputValidationError(
            f"partial image universe for {dataset}: expected {spec['expected_images']}, found {len(ids)}"
        )
    splits = np.asarray([str(row["d_cal_daudit_split_flag"]) for row in rows], dtype=object)
    expected_splits = _row_role(np.asarray(ids, dtype=object))
    if not np.array_equal(splits, expected_splits):
        raise InputValidationError(f"persistent universe has frozen split drift for {cell}")
    try:
        n_gt = np.asarray([int(row["n_gt"]) for row in rows], dtype=np.int64)
        n_predictions = np.asarray([int(row["n_predictions"]) for row in rows], dtype=np.int64)
    except (TypeError, ValueError) as exc:
        raise InputValidationError(f"noninteger universe counts for {cell}") from exc
    if np.any(n_gt < 0) or np.any(n_predictions < 0) or int(n_gt.sum()) != spec["expected_gt"]:
        raise InputValidationError(
            f"persistent universe count mismatch for {cell}: n_gt={int(n_gt.sum())}"
        )
    manifest = json.loads(Path(M.MANIFEST[cell]).read_text(encoding="utf-8"))
    universe_sha = sha256_file(path)
    if (
        int(manifest.get("n_images", -1)) != len(ids)
        or int(manifest.get("n_gt", -1)) != int(n_gt.sum())
        or manifest.get("universe_sha256") != universe_sha
    ):
        raise InputValidationError(f"persistent universe manifest mismatch for {cell}")

    arr = np.asarray(ids, dtype=object)
    external_path = Path(spec["path"])
    external_status = "NOT_AVAILABLE_OPTIONAL"
    if external_path.is_dir() and "/dev/shm" not in str(external_path):
        external_ids = {
            p.stem for p in external_path.iterdir()
            if p.is_file() and p.suffix.lower() == spec["suffix"]
        }
        if external_ids != set(ids):
            raise InputValidationError(f"optional external universe cross-check disagrees for {cell}")
        external_status = "ID_SET_MATCH"
    meta = {
        "universe_path": str(path),
        "universe_images": len(ids),
        "universe_id_sha256": hash_ids(arr),
        "universe_sha256": universe_sha,
        "universe_gt": int(n_gt.sum()),
        "universe_predictions": int(n_predictions.sum()),
        "external_universe_crosscheck_path": str(external_path),
        "external_universe_crosscheck_status": external_status,
    }
    return arr, meta


def _load_cell_uncached(cell: str) -> dict:
    # A cache file is keyed only by cell name, not by source path or source SHA.
    # Bypass it so a newly resolved full-val lineage cannot accidentally reuse 052.
    return M.load_cell(cell, max_rows=10**18)


def _row_role(image_ids: np.ndarray) -> np.ndarray:
    return np.asarray([assign_split(str(image_id)) for image_id in image_ids], dtype=object)


def _universe_roles(universe: np.ndarray) -> dict[str, np.ndarray]:
    outer = _row_role(universe)
    inner = np.asarray([M.split_role(str(image_id)) for image_id in universe], dtype=object)
    return {
        "fit": universe[(outer == "D_cal") & (inner == "fit")],
        "calib": universe[(outer == "D_cal") & (inner == "calib")],
        "audit": universe[outer == "D_audit"],
    }


def validate_cell(cell: str, protocol: dict) -> tuple[dict, dict, dict]:
    dataset, detector, source_path, _ = M.CELLS[cell]
    try:
        M.verify_fullval_lineage(cell)
    except (FileNotFoundError, RuntimeError) as exc:
        raise InputValidationError(f"invalid full-validation manifest for {cell}: {exc}") from exc
    path = Path(source_path)
    if not path.is_file() or path.stat().st_size == 0:
        raise InputValidationError(f"missing/nonempty matched source for {cell}: {path}")
    if str(path).startswith("/dev/shm") or "/dev/shm/" in str(path):
        raise InputValidationError(f"volatile /dev/shm matched source for {cell}: {path}")
    if dataset == "DIOR-R" and KNOWN_PARTIAL_DIOR_FRAGMENT in str(path):
        raise InputValidationError(f"known partial-GT DIOR lineage rejected for {cell}: {path}")

    universe, universe_meta = load_image_universe(cell, dataset)
    C = _load_cell_uncached(cell)
    n_rows = len(C["score"])
    if n_rows == 0 or C["dataset"] != dataset or C["detector"] != detector:
        raise InputValidationError(f"cell identity/schema mismatch for {cell}")
    lengths = {key: len(value) for key, value in C.items() if isinstance(value, np.ndarray)}
    if not lengths or set(lengths.values()) != {n_rows}:
        raise InputValidationError(f"array-length mismatch for {cell}: {lengths}")

    universe_set = set(map(str, universe))
    observed_ids = set(map(str, C["img"]))
    missing_from_universe = observed_ids - universe_set
    if missing_from_universe:
        example = sorted(missing_from_universe)[:3]
        raise InputValidationError(f"{cell} matched ids outside full image universe: {example}")

    expected_split = _row_role(C["img"])
    if not np.array_equal(expected_split, C["split"]):
        bad = int(np.sum(expected_split != C["split"]))
        raise InputValidationError(f"{cell} has {bad} rows inconsistent with frozen D_cal/D_audit hash split")
    if set(map(str, np.unique(C["split"]))) != {"D_cal", "D_audit"}:
        raise InputValidationError(f"{cell} lacks both frozen outer splits")

    base = M.mask_ar(C, M.AR_MAIN)
    if int(base.sum()) < 100:
        raise InputValidationError(f"{cell} has too few finite ar>=2.1 matched instances")

    # The v2 frozen geometry carries an explicit conservative inverse-ar tail;
    # high-AR values must use that policy rather than be clamped or rejected.
    curve_path = REP / "m4_delta_theta_075_frozen.json"
    frozen_curve = json.loads(curve_path.read_text(encoding="utf-8"))
    frozen_ar_max = float(max(frozen_curve["ar"]))
    observed_ar_max = float(np.max(C["ar"][base]))
    if (
        frozen_curve.get("schema_version") != "m4_delta_theta_075_v2"
        or frozen_curve.get("high_ar_policy") != "conservative_inverse_ar_tail_minus_2solve_tol"
        or frozen_curve.get("threshold_semantics") != "smallest_strict_crossing_on_le90_first_lobe"
        or frozen_curve.get("stability_all_pass") is not True
    ):
        raise InputValidationError(
            f"{cell}: frozen geometry lacks the validated high-AR no-clamp policy"
        )
    probe = float(M.delta_theta_075(observed_ar_max))
    if not math.isfinite(probe) or probe < 0.0:
        raise InputValidationError(
            f"{cell}: invalid frozen delta-theta at observed ar={observed_ar_max:.6g}"
        )

    roles = _universe_roles(universe)
    for role, ids in roles.items():
        if len(ids) == 0:
            raise InputValidationError(f"empty complete-image role {cell}/{role}")

    source_sha = sha256_file(path)
    meta = {
        "cell": cell,
        "dataset": dataset,
        "detector": detector,
        "matched_path": str(path),
        "matched_sha256": source_sha,
        "matched_rows": n_rows,
        "eligible_ar21_rows": int(base.sum()),
        "observed_ar_max": observed_ar_max,
        "frozen_ar_grid_max": frozen_ar_max,
        "high_ar_policy": frozen_curve["high_ar_policy"],
        "risk_event_curve_sha256": sha256_file(curve_path),
        **universe_meta,
        "fit_images": len(roles["fit"]),
        "calib_images": len(roles["calib"]),
        "audit_images": len(roles["audit"]),
        "lineage_status": "FULLVAL_VALIDATED",
        "can_recompute": True,
        "protocol_sha256": sha256_file(PROTO_PATH),
    }
    return C, roles, meta


def _row_mask_for_images(row_ids: np.ndarray, image_ids: np.ndarray) -> np.ndarray:
    wanted = set(map(str, image_ids))
    return np.fromiter((str(image_id) in wanted for image_id in row_ids), dtype=bool, count=len(row_ids))


def geometry_appendix_score(C: dict, fit_mask: np.ndarray) -> np.ndarray:
    fit_idx = np.where(fit_mask & np.isfinite(C["ae"]))[0]
    if fit_idx.size < 200:
        raise InputValidationError(f"too few D_cal-fit instances for appendix geometry score: {fit_idx.size}")
    w = C["w"]
    h = C["h"]
    lo = np.minimum(w, h)
    hi = np.maximum(w, h)
    log_ar = np.log(np.maximum(hi, 1e-6) / np.maximum(lo, 1e-6))
    log_size = 0.5 * np.log(np.maximum(w * h, 1e-6))
    X = np.column_stack([C["score"], log_ar, log_size, w, h])
    if not np.isfinite(X[fit_idx]).all():
        raise InputValidationError("nonfinite appendix geometry features in D_cal-fit")
    model = HistGradientBoostingRegressor(
        max_depth=3,
        max_iter=200,
        learning_rate=0.05,
        random_state=0,
        l2_regularization=1.0,
    ).fit(X[fit_idx], C["ae"][fit_idx])
    out = np.full(len(C["score"]), np.nan, dtype=float)
    finite = np.isfinite(X).all(axis=1)
    out[finite] = -model.predict(X[finite])
    return out


def candidate_thresholds(fit_scores: np.ndarray, coverage_grid: list[float]) -> list[dict]:
    scores = np.asarray(fit_scores, dtype=float)
    scores = scores[np.isfinite(scores)]
    if scores.size < 100:
        raise InputValidationError(f"too few D_cal-fit scores to freeze candidates: {scores.size}")
    rows = []
    for index, coverage in enumerate(coverage_grid):
        threshold = float(np.quantile(scores, 1.0 - float(coverage)))
        rows.append(
            {
                "candidate_index": index,
                "target_coverage": float(coverage),
                "threshold": threshold,
                "fit_realized_instance_coverage": float(np.mean(scores >= threshold)),
                "fit_instances": int(scores.size),
            }
        )
    return rows


def image_summary(
    severe: np.ndarray,
    retained: np.ndarray,
    row_image_ids: np.ndarray,
    universe_ids: np.ndarray,
) -> dict:
    """Return image losses over every universe image, including zero-row images."""
    severe = np.asarray(severe, dtype=float)
    retained = np.asarray(retained, dtype=bool)
    row_image_ids = np.asarray(row_image_ids, dtype=object)
    universe_ids = np.asarray(universe_ids, dtype=object)
    if not (len(severe) == len(retained) == len(row_image_ids)):
        raise ValueError("row arrays have inconsistent lengths")
    if len(universe_ids) == 0 or len(set(map(str, universe_ids))) != len(universe_ids):
        raise ValueError("image universe must be nonempty and unique")
    position = {str(image_id): i for i, image_id in enumerate(universe_ids)}
    try:
        inverse = np.fromiter(
            (position[str(image_id)] for image_id in row_image_ids), dtype=np.int64, count=len(row_image_ids)
        )
    except KeyError as exc:
        raise ValueError(f"row image outside universe: {exc}") from exc

    n_images = len(universe_ids)
    total = np.bincount(inverse, minlength=n_images).astype(float)
    kept = np.bincount(inverse, weights=retained.astype(float), minlength=n_images)
    severe_kept = np.bincount(
        inverse, weights=(retained.astype(float) * severe), minlength=n_images
    )
    losses = np.divide(severe_kept, kept, out=np.zeros(n_images), where=kept > 0)
    per_image_coverage = np.divide(kept, total, out=np.zeros(n_images), where=total > 0)
    retained_total = int(round(float(kept.sum())))
    severe_total = int(round(float(severe_kept.sum())))
    eligible_total = int(round(float(total.sum())))
    return {
        "losses": losses,
        "events": (severe_kept > 0).astype(int),
        "eligible_by_image": total,
        "retained_by_image": kept,
        "severe_retained_by_image": severe_kept,
        "n_images": n_images,
        "mean_image_risk": float(losses.mean()),
        "nonempty_image_prop": float(np.mean(kept > 0)),
        "mean_instance_cov": float(per_image_coverage.mean()),
        "median_instance_cov": float(np.median(per_image_coverage)),
        "realized_instance_coverage": float(retained_total / eligible_total) if eligible_total else 0.0,
        "eligible_total": eligible_total,
        "retained_total": retained_total,
        "severe_total": severe_total,
        "empirical_instance_risk": float(severe_total / retained_total) if retained_total else math.nan,
    }


def clopper_pearson_upper(k: int, n: int, delta: float) -> float:
    """One-sided (1-delta) exact Clopper-Pearson upper bound."""
    if n <= 0 or k < 0 or k > n or not 0 < delta < 1:
        raise ValueError(f"invalid exact-binomial inputs k={k}, n={n}, delta={delta}")
    if k == n:
        return 1.0
    return float(beta.ppf(1.0 - delta, k + 1, n - k))


def instance_cluster_bootstrap_ci(summary: dict, n_boot: int, seed: int) -> tuple[float, float]:
    """Image-cluster bootstrap CI for empirical instance-weighted risk."""
    retained = np.asarray(summary["retained_by_image"], dtype=float)
    severe = np.asarray(summary["severe_retained_by_image"], dtype=float)
    if retained.sum() == 0:
        return math.nan, math.nan
    rng = np.random.RandomState(seed)
    n_images = len(retained)
    replicate_seeds = rng.randint(0, np.iinfo(np.int32).max, size=n_boot)

    def replicate(rep_seed):
        local = np.random.RandomState(int(rep_seed))
        draw = local.randint(0, n_images, size=n_images)
        denominator = float(retained[draw].sum())
        if denominator > 0:
            return float(severe[draw].sum() / denominator)
        return math.nan

    workers = min(max(1, int(os.environ.get("M069_BOOTSTRAP_WORKERS", "40"))), n_boot)
    if workers == 1:
        values = [value for value in map(replicate, replicate_seeds) if np.isfinite(value)]
    else:
        with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="m3-bootstrap") as pool:
            values = [value for value in pool.map(replicate, replicate_seeds) if np.isfinite(value)]
    if not values:
        return math.nan, math.nan
    return float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))


def _summary_for_role(
    C: dict,
    score: np.ndarray,
    severe: np.ndarray,
    base_mask: np.ndarray,
    role_ids: np.ndarray,
    threshold: float,
) -> dict:
    key = (str(C["cell"]), id(C["img"]), id(score), id(severe), id(base_mask), id(role_ids))
    view = _ROLE_VIEW_CACHE.get(key)
    if view is None:
        role_mask = _row_mask_for_images(C["img"], role_ids)
        selected_rows = base_mask & role_mask & np.isfinite(score)
        row_ids = C["img"][selected_rows]
        position = {str(image_id): i for i, image_id in enumerate(role_ids)}
        try:
            inverse = np.fromiter(
                (position[str(image_id)] for image_id in row_ids),
                dtype=np.int64,
                count=len(row_ids),
            )
        except KeyError as exc:
            raise InputValidationError(f"role row outside complete image universe: {exc}") from exc
        view = {
            "score": np.asarray(score[selected_rows], dtype=float),
            "severe": np.asarray(severe[selected_rows], dtype=float),
            "inverse": inverse,
            "eligible_by_image": np.bincount(inverse, minlength=len(role_ids)).astype(float),
            "n_images": len(role_ids),
        }
        _ROLE_VIEW_CACHE[key] = view

    retained = view["score"] >= threshold
    kept = np.bincount(
        view["inverse"], weights=retained.astype(float), minlength=view["n_images"]
    )
    severe_kept = np.bincount(
        view["inverse"],
        weights=retained.astype(float) * view["severe"],
        minlength=view["n_images"],
    )
    total = view["eligible_by_image"]
    losses = np.divide(severe_kept, kept, out=np.zeros(view["n_images"]), where=kept > 0)
    per_image_coverage = np.divide(
        kept, total, out=np.zeros(view["n_images"]), where=total > 0
    )
    retained_total = int(round(float(kept.sum())))
    severe_total = int(round(float(severe_kept.sum())))
    eligible_total = int(round(float(total.sum())))
    return {
        "losses": losses,
        "events": (severe_kept > 0).astype(int),
        "eligible_by_image": total,
        "retained_by_image": kept,
        "severe_retained_by_image": severe_kept,
        "n_images": view["n_images"],
        "mean_image_risk": float(losses.mean()),
        "nonempty_image_prop": float(np.mean(kept > 0)),
        "mean_instance_cov": float(per_image_coverage.mean()),
        "median_instance_cov": float(np.median(per_image_coverage)),
        "realized_instance_coverage": float(retained_total / eligible_total) if eligible_total else 0.0,
        "eligible_total": eligible_total,
        "retained_total": retained_total,
        "severe_total": severe_total,
        "empirical_instance_risk": float(severe_total / retained_total) if retained_total else math.nan,
    }


def image_ltt_path(
    C: dict,
    score: np.ndarray,
    severe: np.ndarray,
    base_mask: np.ndarray,
    roles: dict[str, np.ndarray],
    candidates: list[dict],
    alpha: float,
    delta: float,
    cell: str,
    score_name: str,
    result_role: str,
    source_meta: dict,
) -> tuple[list[dict], dict | None]:
    rows = []
    sequence_open = True
    selected_row = None
    for candidate in candidates:
        threshold = candidate["threshold"]
        calib = _summary_for_role(C, score, severe, base_mask, roles["calib"], threshold)
        audit = _summary_for_role(C, score, severe, base_mask, roles["audit"], threshold)
        pvalue = M.hb_pvalue(calib["mean_image_risk"], alpha, calib["n_images"])
        ucb = M.hb_ucb(calib["mean_image_risk"], calib["n_images"], delta)
        reached = sequence_open
        certified = bool(reached and pvalue <= delta)
        if certified and ucb > alpha + 1e-10:
            raise RuntimeError(
                f"HB inversion mismatch for {cell}/{score_name}/alpha={alpha}: ucb={ucb}"
            )
        if certified:
            state = "CERTIFIED"
        elif reached:
            state = "FIRST_FAILURE"
            sequence_open = False
        else:
            state = "NOT_TESTED_AFTER_FAILURE"

        row = {
            "cell": cell,
            "dataset": C["dataset"],
            "detector": C["detector"],
            "score": score_name,
            "result_role": result_role,
            "risk_event": RISK_EVENT,
            "mask_definition": "matched_gt_ar_ge_2.1_exclude_pred_or_gt_near_square",
            "aspect_ratio_source": "matched_GT_box",
            "eligible_instance_definition": "one_to_one_class_matched_prediction_IoU_ge_0.5_with_GT_ar_ge_2.1",
            "ar_threshold": M.AR_MAIN,
            "alpha": alpha,
            "delta": delta,
            "family_id": f"{cell}|{score_name}|{RISK_EVENT}|alpha={alpha}",
            "candidate_index": candidate["candidate_index"],
            "target_coverage": candidate["target_coverage"],
            "threshold": threshold,
            "threshold_source": "D_cal-fit_only",
            "fit_instances": candidate["fit_instances"],
            "fit_realized_instance_coverage": candidate["fit_realized_instance_coverage"],
            "fixed_sequence_state": state,
            "certified": certified,
            "selected": False,
            "calib_mean_image_risk": calib["mean_image_risk"],
            "risk_ucb_calib": ucb,
            "hb_pvalue_calib": pvalue,
            "calib_nonempty_image_prop": calib["nonempty_image_prop"],
            "calib_mean_instance_cov": calib["mean_instance_cov"],
            "calib_realized_instance_coverage": calib["realized_instance_coverage"],
            "calib_images": calib["n_images"],
            "calib_eligible_instances": calib["eligible_total"],
            "calib_retained": calib["retained_total"],
            "mean_image_risk_audit": audit["mean_image_risk"],
            "nonempty_image_prop": audit["nonempty_image_prop"],
            "mean_instance_cov": audit["mean_instance_cov"],
            "median_instance_cov": audit["median_instance_cov"],
            "audit_realized_instance_coverage": audit["realized_instance_coverage"],
            "audit_images": audit["n_images"],
            "audit_eligible_instances": audit["eligible_total"],
            "audit_retained": audit["retained_total"],
            "empirical_instance_risk_audit": audit["empirical_instance_risk"],
            "empirical_instance_risk_cluster_ci_lo": "",
            "empirical_instance_risk_cluster_ci_hi": "",
            "audit_used_for_selection": False,
            "formal_guarantee_unit": "complete_evaluation_image",
            "protocol_sha256": source_meta["protocol_sha256"],
            "matched_sha256": source_meta["matched_sha256"],
            "universe_id_sha256": source_meta["universe_id_sha256"],
            "risk_event_curve_sha256": source_meta["risk_event_curve_sha256"],
            "note": {
                "PRIMARY": "primary image-level HB LTT",
                "APPENDIX_GT_FIT_UPPER_BOUND": (
                    "appendix-only target-GT-fitted geometry upper-bound; Deployable gate not established"
                ),
                "PREREGISTERED_SCORE_MENU": (
                    "preregistered native/GT-free score-menu image-level HB LTT"
                ),
            }[result_role],
        }
        rows.append(row)
        if certified:
            selected_row = row

    if selected_row is not None:
        selected_row["selected"] = True
        audit = _summary_for_role(
            C, score, severe, base_mask, roles["audit"], float(selected_row["threshold"])
        )
        lo, hi = instance_cluster_bootstrap_ci(
            audit,
            n_boot=BOOTSTRAP_REPS,
            seed=17000 + sum(ord(ch) for ch in f"{cell}|{score_name}|{alpha}"),
        )
        selected_row["empirical_instance_risk_cluster_ci_lo"] = lo
        selected_row["empirical_instance_risk_cluster_ci_hi"] = hi
    return rows, selected_row


def legacy_instance_iid_path(
    C: dict,
    score: np.ndarray,
    severe: np.ndarray,
    base_mask: np.ndarray,
    roles: dict[str, np.ndarray],
    candidates: list[dict],
    alpha: float,
    delta: float,
) -> dict | None:
    """Reconstruct the old invalid instance-i.i.d. gate for audit comparison only."""
    sequence_open = True
    selected = None
    for candidate in candidates:
        threshold = candidate["threshold"]
        calib = _summary_for_role(C, score, severe, base_mask, roles["calib"], threshold)
        n = calib["retained_total"]
        if n == 0:
            ucb = 1.0
        else:
            ucb = clopper_pearson_upper(calib["severe_total"], n, delta)
        passed = bool(sequence_open and ucb <= alpha)
        if passed:
            selected = {**candidate, "ucb": ucb, "calib": calib}
        elif sequence_open:
            sequence_open = False
    return selected


def comparison_row(
    C: dict,
    score: np.ndarray,
    severe: np.ndarray,
    base_mask: np.ndarray,
    roles: dict[str, np.ndarray],
    alpha: float,
    score_name: str,
    result_role: str,
    new_selected: dict | None,
    old_selected: dict | None,
) -> dict:
    new_audit = None
    old_audit = None
    old_ci = (math.nan, math.nan)
    if new_selected is not None:
        new_audit = _summary_for_role(
            C, score, severe, base_mask, roles["audit"], float(new_selected["threshold"])
        )
    if old_selected is not None:
        old_audit = _summary_for_role(
            C, score, severe, base_mask, roles["audit"], float(old_selected["threshold"])
        )
        old_ci = instance_cluster_bootstrap_ci(
            old_audit,
            n_boot=BOOTSTRAP_REPS,
            seed=23000 + sum(ord(ch) for ch in f"{C['cell']}|{score_name}|{alpha}"),
        )

    def value(obj: dict | None, key: str, default=""):
        return obj[key] if obj is not None else default

    old_calib = value(old_selected, "calib", None)
    new_cov = value(new_audit, "realized_instance_coverage", math.nan)
    old_cov = value(old_audit, "realized_instance_coverage", math.nan)
    coverage_drop = old_cov - new_cov if np.isfinite(old_cov) and np.isfinite(new_cov) else ""
    new_ucb = value(new_selected, "risk_ucb_calib", math.nan)
    old_ucb = value(old_selected, "ucb", math.nan)
    ucb_change = new_ucb - old_ucb if np.isfinite(new_ucb) and np.isfinite(old_ucb) else ""
    threshold_change = (
        float(value(new_selected, "threshold")) - float(value(old_selected, "threshold"))
        if new_selected is not None and old_selected is not None
        else ""
    )
    effective_inflation = (
        float(old_calib["retained_total"] / old_calib["n_images"])
        if old_calib is not None and old_calib["n_images"]
        else ""
    )
    return {
        "cell": C["cell"],
        "dataset": C["dataset"],
        "detector": C["detector"],
        "score": score_name,
        "result_role": result_role,
        "risk_event": RISK_EVENT,
        "mask_definition": "matched_gt_ar_ge_2.1_exclude_pred_or_gt_near_square",
        "aspect_ratio_source": "matched_GT_box",
        "eligible_instance_definition": "one_to_one_class_matched_prediction_IoU_ge_0.5_with_GT_ar_ge_2.1",
        "ar_threshold": M.AR_MAIN,
        "alpha": alpha,
        "new_image_level_certified": new_selected is not None,
        "new_target_coverage": value(new_selected, "target_coverage"),
        "new_threshold": value(new_selected, "threshold"),
        "new_image_ucb_calib": value(new_selected, "risk_ucb_calib"),
        "new_calib_images": value(new_selected, "calib_images"),
        "new_calib_retained_instances": value(new_selected, "calib_retained"),
        "new_audit_realized_instance_coverage": value(new_audit, "realized_instance_coverage"),
        "new_audit_mean_image_risk": value(new_audit, "mean_image_risk"),
        "new_empirical_instance_risk_audit": value(new_audit, "empirical_instance_risk"),
        "new_empirical_instance_risk_cluster_ci_lo": value(
            new_selected, "empirical_instance_risk_cluster_ci_lo"
        ),
        "new_empirical_instance_risk_cluster_ci_hi": value(
            new_selected, "empirical_instance_risk_cluster_ci_hi"
        ),
        "old_instance_iid_certified_audit_only": old_selected is not None,
        "old_target_coverage": value(old_selected, "target_coverage"),
        "old_threshold": value(old_selected, "threshold"),
        "old_instance_iid_cp_ucb_calib_audit_only": value(old_selected, "ucb"),
        "old_calib_images": value(old_calib, "n_images"),
        "old_calib_retained_instances": value(old_calib, "retained_total"),
        "old_audit_realized_instance_coverage": value(old_audit, "realized_instance_coverage"),
        "old_empirical_instance_risk_audit": value(old_audit, "empirical_instance_risk"),
        "old_empirical_instance_risk_cluster_ci_lo": old_ci[0] if old_audit is not None else "",
        "old_empirical_instance_risk_cluster_ci_hi": old_ci[1] if old_audit is not None else "",
        "audit_instance_coverage_drop_old_minus_new": coverage_drop,
        "target_coverage_drop_old_minus_new": (
            float(value(old_selected, "target_coverage")) - float(value(new_selected, "target_coverage"))
            if old_selected is not None and new_selected is not None
            else ""
        ),
        "threshold_change_new_minus_old": threshold_change,
        "ucb_change_image_minus_old_iid": ucb_change,
        "effective_n_inflation_retained_instances_per_image": effective_inflation,
        "old_pass_new_fail": old_selected is not None and new_selected is None,
        "formal_guarantee": "new_image_level_only",
        "note": "old instance-i.i.d. exact-binomial is a labelled invalid-independence counterfactual only",
    }


def secondary_image_event_path(
    C: dict,
    score: np.ndarray,
    severe: np.ndarray,
    base_mask: np.ndarray,
    roles: dict[str, np.ndarray],
    candidates: list[dict],
    alpha: float,
    delta: float,
    cell: str,
) -> list[dict]:
    rows = []
    sequence_open = True
    selected_row = None
    for candidate in candidates:
        threshold = candidate["threshold"]
        calib = _summary_for_role(C, score, severe, base_mask, roles["calib"], threshold)
        audit = _summary_for_role(C, score, severe, base_mask, roles["audit"], threshold)
        k = int(calib["events"].sum())
        n = calib["n_images"]
        ucb = clopper_pearson_upper(k, n, delta)
        reached = sequence_open
        passed = bool(reached and ucb <= alpha)
        if passed:
            state = "CERTIFIED"
        elif reached:
            state = "FIRST_FAILURE"
            sequence_open = False
        else:
            state = "NOT_TESTED_AFTER_FAILURE"
        row = {
            "cell": cell,
            "dataset": C["dataset"],
            "detector": C["detector"],
            "score": "detection_score",
            "result_role": "SECONDARY",
            "risk_event": "image_has_any_geometry_normalized_severe",
            "mask_definition": "matched_gt_ar_ge_2.1_exclude_pred_or_gt_near_square",
            "aspect_ratio_source": "matched_GT_box",
            "eligible_instance_definition": "one_to_one_class_matched_prediction_IoU_ge_0.5_with_GT_ar_ge_2.1",
            "ar_threshold": M.AR_MAIN,
            "alpha": alpha,
            "delta": delta,
            "candidate_index": candidate["candidate_index"],
            "target_coverage": candidate["target_coverage"],
            "threshold": threshold,
            "threshold_source": "D_cal-fit_only",
            "fixed_sequence_state": state,
            "certified": passed,
            "selected": False,
            "calib_image_events": k,
            "calib_images": n,
            "exact_clopper_pearson_ucb_calib": ucb,
            "audit_image_event_rate": float(audit["events"].mean()),
            "audit_image_events": int(audit["events"].sum()),
            "audit_images": audit["n_images"],
            "audit_nonempty_image_prop": audit["nonempty_image_prop"],
            "audit_used_for_selection": False,
            "note": "strict binary image event; exact CP is secondary only, never the primary bounded loss",
        }
        rows.append(row)
        if passed:
            selected_row = row
    if selected_row is not None:
        selected_row["selected"] = True
    return rows


def run() -> None:
    _ROLE_VIEW_CACHE.clear()
    protocol, protocol_sha = validate_frozen_protocol()
    delta = float(protocol["delta_confidence"])
    alphas = [float(value) for value in protocol["alpha_risk_budgets"]]
    coverage_grid = [float(value) for value in protocol["candidate_threshold_sequence"]["coverage_grid"]]

    # Validate every formal input before writing any result, so a partial lineage
    # cannot leave a new partially-overwritten result family.
    loaded = {}
    input_manifest = []
    for cell in M.FROZEN_CELLS:
        C, roles, meta = validate_cell(cell, protocol)
        if meta["protocol_sha256"] != protocol_sha:
            raise InputValidationError(f"protocol hash drift while validating {cell}")
        loaded[cell] = (C, roles, meta)
        input_manifest.append(meta)

    main_rows: list[dict] = []
    comparison_rows: list[dict] = []
    secondary_rows: list[dict] = []
    empirical_rows: list[dict] = []
    primary_selected: list[dict] = []
    appendix_selected: list[dict] = []
    score_menu_selected: list[dict] = []

    for cell in M.FROZEN_CELLS:
        C, roles, meta = loaded[cell]
        base = M.mask_ar(C, M.AR_MAIN)
        severe, _ = M.geometry_severe(C)
        fit_row_mask = _row_mask_for_images(C["img"], roles["fit"])
        geometry_score = geometry_appendix_score(C, base & fit_row_mask)
        scores = [
            ("detection_score", np.asarray(C["score"], dtype=float), "PRIMARY"),
            ("geometry_score_upper_bound", geometry_score, "APPENDIX_GT_FIT_UPPER_BOUND"),
        ]
        tta = np.asarray(C.get("tta_circular_variance", []), dtype=float)
        if tta.size != len(C["score"]) or np.isfinite(tta[base & fit_row_mask]).sum() < 100:
            raise InputValidationError(f"{cell}: frozen TTA score has too few D_cal-fit values")
        scores.append(("tta_neg_circular_var", -tta, "PREREGISTERED_SCORE_MENU"))
        phase = np.asarray(C.get("phase_mod", []), dtype=float)
        if cell in M.PSC_CELLS and phase.size == len(C["score"]):
            if np.isfinite(phase[base & fit_row_mask]).sum() < 100:
                raise InputValidationError(f"{cell}: frozen phase score has too few D_cal-fit values")
            scores.extend([
                ("phase_mod", phase, "PREREGISTERED_SCORE_MENU"),
                ("negative_phase_mod", -phase, "PREREGISTERED_SCORE_MENU"),
            ])

        for score_name, score, result_role in scores:
            candidate_mask = base & fit_row_mask & np.isfinite(score)
            candidates = candidate_thresholds(score[candidate_mask], coverage_grid)
            for alpha in alphas:
                rows, selected = image_ltt_path(
                    C,
                    score,
                    severe,
                    base,
                    roles,
                    candidates,
                    alpha,
                    delta,
                    cell,
                    score_name,
                    result_role,
                    meta,
                )
                main_rows.extend(rows)
                if selected is not None:
                    if result_role == "PRIMARY":
                        primary_selected.append(selected)
                    elif result_role == "APPENDIX_GT_FIT_UPPER_BOUND":
                        appendix_selected.append(selected)
                    else:
                        score_menu_selected.append(selected)
                empirical_rows.append(
                    {
                        "cell": cell,
                        "dataset": C["dataset"],
                        "detector": C["detector"],
                        "score": score_name,
                        "result_role": result_role,
                        "alpha": alpha,
                        "selected_threshold_exists": selected is not None,
                        "threshold": selected["threshold"] if selected is not None else "",
                        "target_coverage": selected["target_coverage"] if selected is not None else "",
                        "audit_images": selected["audit_images"] if selected is not None else len(roles["audit"]),
                        "audit_retained_instances": selected["audit_retained"] if selected is not None else "",
                        "empirical_instance_weighted_risk": (
                            selected["empirical_instance_risk_audit"] if selected is not None else ""
                        ),
                        "image_cluster_bootstrap_ci_lo": (
                            selected["empirical_instance_risk_cluster_ci_lo"] if selected is not None else ""
                        ),
                        "image_cluster_bootstrap_ci_hi": (
                            selected["empirical_instance_risk_cluster_ci_hi"] if selected is not None else ""
                        ),
                        "formal_guarantee": False,
                        "note": (
                            "empirical instance-weighted risk with image-cluster bootstrap CI"
                            if selected is not None
                            else (
                                "no certified threshold; empirical instance-weighted risk with "
                                "image-cluster bootstrap CI unavailable"
                            )
                        ),
                    }
                )
                old_selected = legacy_instance_iid_path(
                    C, score, severe, base, roles, candidates, alpha, delta
                )
                comparison_rows.append(
                    comparison_row(
                        C,
                        score,
                        severe,
                        base,
                        roles,
                        alpha,
                        score_name,
                        result_role,
                        selected,
                        old_selected,
                    )
                )

        detection_candidates = candidate_thresholds(C["score"][base & fit_row_mask], coverage_grid)
        for alpha in alphas:
            secondary_rows.extend(
                secondary_image_event_path(
                    C,
                    np.asarray(C["score"], dtype=float),
                    severe,
                    base,
                    roles,
                    detection_candidates,
                    alpha,
                    delta,
                    cell,
                )
            )
        lg(f"{cell} corrected M3 complete-image analysis finished")

    if not main_rows or not comparison_rows or not secondary_rows:
        raise RuntimeError("corrected M3 produced an empty mandatory output")
    expected_score_aliases = {
        "detection_score", "geometry_score_upper_bound", "phase_mod",
        "negative_phase_mod", "tta_neg_circular_var",
    }
    emitted_scores = {row["score"] for row in main_rows}
    if emitted_scores != expected_score_aliases:
        raise RuntimeError(
            f"frozen M3 score menu incomplete: expected {sorted(expected_score_aliases)}, "
            f"got {sorted(emitted_scores)}"
        )
    expected_cells_by_score = {
        "detection_score": set(M.FROZEN_CELLS),
        "geometry_score_upper_bound": set(M.FROZEN_CELLS),
        "tta_neg_circular_var": set(M.FROZEN_CELLS),
        "phase_mod": set(M.PSC_CELLS),
        "negative_phase_mod": set(M.PSC_CELLS),
    }
    for score_name, expected_cells in expected_cells_by_score.items():
        actual_cells = {row["cell"] for row in main_rows if row["score"] == score_name}
        if actual_cells != expected_cells:
            raise RuntimeError(
                f"frozen M3 score/cell coverage mismatch for {score_name}: "
                f"expected {sorted(expected_cells)}, got {sorted(actual_cells)}"
            )

    # Formal verdict uses calibration certification only. D_audit metrics are
    # deliberately absent from the decision predicate.
    nondegenerate = [
        row
        for row in primary_selected
        if float(row["target_coverage"]) >= 0.3
        and float(row["calib_nonempty_image_prop"]) >= 0.3
    ]
    if nondegenerate:
        verdict = "PASS"
    elif primary_selected:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    _atomic_csv(REP / "m3_image_level_ltt.csv", main_rows)
    _atomic_csv(REP / "m3_instance_vs_image_comparison.csv", comparison_rows)
    _atomic_csv(REP / "m3_image_event_secondary_endpoint.csv", secondary_rows)
    _atomic_csv(REP / "m3_instance_weighted_empirical.csv", empirical_rows)
    _atomic_json(REP / "m3_input_lineage_manifest.json", input_manifest)
    _atomic_csv(
        REP / "m3_decision.csv",
        [
            {
                "decision": verdict,
                "primary_score": "detection_score",
                "primary_risk_event": RISK_EVENT,
                "n_primary_selected": len(primary_selected),
                "n_primary_nondegenerate": len(nondegenerate),
                "n_appendix_selected": len(appendix_selected),
                "n_preregistered_score_menu_selected": len(score_menu_selected),
                "audit_used_for_selection": False,
                "protocol_sha256": protocol_sha,
            }
        ],
    )

    selected_primary_lines = []
    for row in primary_selected:
        selected_primary_lines.append(
            f"| {row['cell']} | {row['alpha']} | {row['target_coverage']} | "
            f"{float(row['risk_ucb_calib']):.6g} | {float(row['mean_image_risk_audit']):.6g} | "
            f"{float(row['nonempty_image_prop']):.6g} | {float(row['audit_realized_instance_coverage']):.6g} |"
        )
    selected_appendix_lines = []
    for row in appendix_selected:
        selected_appendix_lines.append(
            f"| {row['cell']} | {row['alpha']} | {row['target_coverage']} | "
            f"{float(row['risk_ucb_calib']):.6g} |"
        )
    selected_menu_lines = []
    for row in score_menu_selected:
        selected_menu_lines.append(
            f"| {row['cell']} | {row['score']} | {row['alpha']} | {row['target_coverage']} | "
            f"{float(row['risk_ucb_calib']):.6g} |"
        )
    doc = "\n".join(
        [
            "# M3：图像级有限样本风险保证",
            "",
            "- 正式 exchangeable unit 是完整 evaluation-image universe；没有 eligible/retained prediction 的图像也以 L_I=0 进入统计。",
            "- eligible instance 是与 GT 同类、旋转 IoU>=0.5 的一对一匹配预测；未匹配预测没有可定义的 GT angle error，不进入分子或实例分母，但其图像仍留在完整图像总体中。",
            "- D_cal-fit 只定义候选阈值；独立 D_cal-calib 只做 Hoeffding-Bentkus fixed-sequence LTT；D_audit 只报告，不参与阈值、认证或总判定。",
            "- 冻结 JSON 中大写 `CALIBRATION split` 按其 `splits` 条款解释为外层 D_cal；外层再确定性拆成上述 fit/calib，避免候选阈值与 LTT 标定复用同一图像。",
            "- 正式 primary 是 detection_score × geometry-normalized severe event。主 bounded loss 不使用 exact binomial。",
            "- ar>=2.1 掩码与 delta_theta_0.75(ar) 的 ar 均来自 matched GT box；选择打分特征来自预测端。",
            "- geometry_score_upper_bound 使用目标域 GT error 拟合；M2 已通过，但 Deployable 门控未建立，故只列附录、不参与 primary 判定。",
            "- 冻结 score menu 的 phase_mod、negative_phase_mod 与 TTA circular variance 使用同一图像级 HB-LTT；它们不改变 detection_score primary 判定。",
            "- secondary Z_I 使用 exact Clopper-Pearson；实例风险仅为 empirical instance-weighted risk with image-cluster bootstrap CI。",
            f"- 冻结协议 SHA-256：`{protocol_sha}`；协议文件未修改。",
            f"- **M3 判定：{verdict}**。",
            "",
            "## Primary selected thresholds",
            "| cell | alpha | target coverage | calibration HB UCB | audit mean image risk | audit nonempty images | audit instance coverage |",
            "|---|---:|---:|---:|---:|---:|---:|",
            *(selected_primary_lines or ["| none | | | | | | |"]),
            "",
            "## Appendix-only geometry score",
            "| cell | alpha | target coverage | calibration HB UCB |",
            "|---|---:|---:|---:|",
            *(selected_appendix_lines or ["| none | | | |"]),
            "",
            "## Preregistered native/GT-free score menu",
            "| cell | score | alpha | target coverage | calibration HB UCB |",
            "|---|---|---:|---:|---:|",
            *(selected_menu_lines or ["| none | | | | |"]),
            "",
        ]
    )
    _atomic_text(DOC / "m3_image_level_risk_control.md", doc)
    print(
        f"M3_DONE {verdict} primary_selected={len(primary_selected)} "
        f"primary_nondegenerate={len(nondegenerate)} appendix_selected={len(appendix_selected)} "
        f"score_menu_selected={len(score_menu_selected)}",
        flush=True,
    )


if __name__ == "__main__":
    try:
        run()
    except InputValidationError as exc:
        lg(f"M3_INPUT_VALIDATION_FAILED: {exc}")
        raise SystemExit(str(exc))
