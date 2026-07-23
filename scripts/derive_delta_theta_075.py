"""Derive the frozen geometry-normalized orientation-risk threshold.

``delta_theta_tau(ar)`` is the smallest le90 long-axis angle difference for
which two congruent, concentric, same-scale rectangles of aspect ratio ``ar``
have IoU below ``tau``.  The scientific definition and the original freeze
time are unchanged; this revision removes the legacy ar>8 clamp by extending
the deterministic table and using a conservative inverse-ar tail beyond it.
"""

import argparse
import csv
import json
import math
import os

import numpy as np
from scipy.optimize import minimize_scalar


ROOT = "/home/rspip/cqc/pro/study/orientbench"
REPORT_DIR = f"{ROOT}/top_journal_v3_reaudit_055/reports"
OUT_CSV = f"{REPORT_DIR}/m4_delta_theta_tau_curve.csv"
OUT_JSON = f"{REPORT_DIR}/m4_delta_theta_075_frozen.json"
OUT_STABILITY_CSV = f"{REPORT_DIR}/m4_delta_theta_direct_solve_stability.csv"

FROZEN_AT = "2026-07-12 20:14:39 -0700"
TAU_MAIN = 0.75
ENGINEERING_TOLERANCE_DEG = 15.0
SOLVE_TOL_DEG = 1e-3
ANGLE_CONVENTION = "le90_pi_periodic_long_axis"
GEOMETRY_MODEL = "concentric_same_scale_congruent_rectangles"
AR_GRID_MAX = 1024.0
HIGH_AR_POLICY = "conservative_inverse_ar_tail_minus_2solve_tol"
INTERPOLATION_AUDIT_TOL_DEG = 1e-2
THRESHOLD_SEMANTICS = "smallest_strict_crossing_on_le90_first_lobe"

try:
    from shapely.affinity import rotate
    from shapely.geometry import Polygon

    _HAVE_SHAPELY = True
except Exception:
    _HAVE_SHAPELY = False


def _require_shapely():
    if not _HAVE_SHAPELY:
        raise RuntimeError("shapely is required for direct delta-theta solving")


def _rect(w, h):
    _require_shapely()
    return Polygon([(-w / 2, -h / 2), (w / 2, -h / 2),
                    (w / 2, h / 2), (-w / 2, h / 2)])


def iou_rot(ar, dtheta_deg, area=1.0):
    """IoU under the frozen le90, shared-center, same-scale geometry model."""
    ar = float(ar)
    if not math.isfinite(ar) or ar < 1.0:
        raise ValueError(f"aspect ratio must be finite and >=1, got {ar}")
    h = math.sqrt(float(area) / ar)
    w = ar * h
    a = _rect(w, h)
    b = rotate(a, float(dtheta_deg), origin=(0, 0), use_radians=False)
    inter = a.intersection(b).area
    union = 2 * a.area - inter
    return inter / union if union > 0 else 0.0


def dtheta_tau(ar, tau, hi=90.0, tol=SOLVE_TOL_DEG):
    """Directly solve the frozen threshold to ``tol`` degrees by bisection.

    The angle is le90/pi-periodic and restricted to [0, 90] degrees. ``inf``
    denotes near-square geometry whose IoU never drops below ``tau`` there.
    """
    ar = float(ar)
    tau = float(tau)
    tol = float(tol)
    if not math.isfinite(ar) or ar < 1.0:
        raise ValueError(f"aspect ratio must be finite and >=1, got {ar}")
    if not 0.0 < tau < 1.0:
        raise ValueError(f"tau must be in (0,1), got {tau}")
    if tol <= 0.0:
        raise ValueError(f"tol must be positive, got {tol}")
    upper = float(hi)
    endpoint_iou = iou_rot(ar, upper)
    if endpoint_iou >= tau:
        # Near-square rectangles are non-monotone on [0,90]: e.g. a square
        # returns to IoU=1 at 90 degrees but falls to sqrt(1/2) at 45 degrees.
        # Locate the first-lobe minimum before deciding that no crossing exists.
        minimum = minimize_scalar(
            lambda theta: iou_rot(ar, theta),
            bounds=(0.0, upper),
            method="bounded",
            options={"xatol": max(tol / 8.0, 1e-7)},
        )
        if not minimum.success:
            raise RuntimeError(f"IoU minimum search failed for ar={ar}, tau={tau}")
        if float(minimum.fun) >= tau - 1e-12:
            return float("inf")
        upper = float(minimum.x)

    # Rectangle IoU decreases from zero rotation to the first-lobe minimum;
    # this bracket therefore returns the *smallest* strict-threshold crossing.
    lo = 0.0
    while upper - lo >= tol:
        mid = 0.5 * (lo + upper)
        if iou_rot(ar, mid) >= tau:
            lo = mid
        else:
            upper = mid
    return 0.5 * (lo + upper)


def _build_ar_grid():
    # Preserve the original dense 1..8 grid exactly. A geometric extension
    # keeps interpolation error small while reaching highly elongated boxes.
    legacy = (list(np.arange(1.0, 2.0, 0.05)) +
              list(np.arange(2.0, 4.0, 0.1)) +
              list(np.arange(4.0, 8.01, 0.25)))
    extended = np.geomspace(8.0, AR_GRID_MAX, 257)[1:]
    return sorted({round(float(x), 6) for x in legacy + list(extended)})


AR_GRID = _build_ar_grid()


def build_curve(ar_grid=None):
    rows = []
    for ar in AR_GRID if ar_grid is None else ar_grid:
        ar = float(ar)
        rows.append({
            "ar": ar,
            "dtheta_050": dtheta_tau(ar, 0.50, tol=SOLVE_TOL_DEG),
            "dtheta_075": dtheta_tau(ar, TAU_MAIN, tol=SOLVE_TOL_DEG),
        })
    return rows


def _interpolator_from_arrays(ars, dtheta, solve_tol=SOLVE_TOL_DEG):
    ars = np.asarray(ars, dtype=float)
    dtheta = np.asarray(dtheta, dtype=float)
    finite = np.isfinite(ars) & np.isfinite(dtheta)
    if finite.sum() < 2:
        raise ValueError("delta-theta table has fewer than two finite points")
    fa = ars[finite]
    fd = dtheta[finite]
    order = np.argsort(fa)
    fa, fd = fa[order], fd[order]
    if np.any(np.diff(fa) <= 0):
        raise ValueError("delta-theta AR grid must be strictly increasing")
    if np.any(np.diff(fd) > 2 * solve_tol):
        raise ValueError("delta-theta curve must be non-increasing within solve tolerance")

    grid_max = float(fa[-1])
    # ar*dtheta approaches a constant for elongated rectangles. Use the lower
    # observed tail envelope and subtract a numerical margin so extrapolation
    # cannot recreate the unsafe legacy behavior of holding dtheta constant.
    tail = fa >= max(8.0, grid_max / 2.0)
    tail_constant = float(np.min(fa[tail] * fd[tail]))

    def interpolate(ar_val):
        ar_val = float(ar_val)
        if not math.isfinite(ar_val) or ar_val < 1.0:
            raise ValueError(f"aspect ratio must be finite and >=1, got {ar_val}")
        if ar_val < fa[0]:
            return float("inf")
        if ar_val <= grid_max:
            return float(np.interp(ar_val, fa, fd))
        return max(0.0, tail_constant / ar_val - 2.0 * solve_tol)

    interpolate.grid_max = grid_max
    interpolate.tail_constant = tail_constant
    interpolate.high_ar_policy = HIGH_AR_POLICY
    return interpolate


def load_interpolator(path=OUT_JSON):
    """Load the frozen table without ever clamping ar above its maximum.

    This also handles the legacy ar<=8 JSON safely: values above 8 use the
    conservative inverse-ar tail until the extended table is regenerated.
    """
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as fp:
            frozen = json.load(fp)
        ars = np.asarray(frozen["ar"], dtype=float)
        d075 = np.asarray(frozen["dtheta_075"], dtype=float)
    else:
        rows = build_curve()
        ars = np.asarray([r["ar"] for r in rows], dtype=float)
        d075 = np.asarray([r["dtheta_075"] for r in rows], dtype=float)
    return _interpolator_from_arrays(ars, d075)


def _stability_probe_ars(grid_max):
    return [1.0, 1.05, 1.1, 1.2, 1.6, 2.1, 2.15, 3.75, 8.0, 8.125, 12.3, 24.7,
            63.5, 127.3, 255.1, 511.7, 900.0, grid_max,
            1.5 * grid_max, 2.0 * grid_max]


def direct_solve_stability_rows(curve_rows):
    ars = np.asarray([r["ar"] for r in curve_rows], dtype=float)
    d075 = np.asarray([r["dtheta_075"] for r in curve_rows], dtype=float)
    interp = _interpolator_from_arrays(ars, d075)
    curve_finite = d075[np.isfinite(d075)]
    monotone = bool(np.all(np.diff(curve_finite) <= 2 * SOLVE_TOL_DEG))
    rows = []
    for ar in _stability_probe_ars(interp.grid_max):
        direct = dtheta_tau(ar, TAU_MAIN, tol=SOLVE_TOL_DEG)
        table = interp(ar)
        finite = math.isfinite(direct) and math.isfinite(table)
        signed = table - direct if finite else float("nan")
        abs_diff = abs(signed) if finite else float("nan")
        lower = max(0.0, direct - SOLVE_TOL_DEG) if math.isfinite(direct) else float("nan")
        upper = direct + SOLVE_TOL_DEG if math.isfinite(direct) else float("nan")
        bracket_ok = (iou_rot(ar, lower) >= TAU_MAIN and
                      iou_rot(ar, upper) < TAU_MAIN) if math.isfinite(direct) else True
        mode = "table_interpolation" if ar <= interp.grid_max else HIGH_AR_POLICY
        interpolation_ok = (abs_diff <= INTERPOLATION_AUDIT_TOL_DEG
                            if ar <= interp.grid_max else signed <= SOLVE_TOL_DEG)
        rows.append({
            "ar": ar,
            "tau": TAU_MAIN,
            "angle_convention": ANGLE_CONVENTION,
            "geometry_model": GEOMETRY_MODEL,
            "solve_tolerance_deg": SOLVE_TOL_DEG,
            "lookup_mode": mode,
            "direct_dtheta_deg": direct,
            "lookup_dtheta_deg": table,
            "lookup_minus_direct_deg": signed,
            "abs_diff_deg": abs_diff,
            "iou_at_direct_minus_tol": iou_rot(ar, lower) if math.isfinite(direct) else "",
            "iou_at_direct_plus_tol": iou_rot(ar, upper) if math.isfinite(direct) else "",
            "direct_bracket_ok": bracket_ok,
            "curve_monotone_nonincreasing": monotone,
            "stability_pass": bool(bracket_ok and monotone and interpolation_ok),
        })
    return rows


def _json_number(value):
    return None if not math.isfinite(value) else round(float(value), 4)


def main():
    _require_shapely()
    rows = build_curve()
    stability = direct_solve_stability_rows(rows)
    if not all(r["stability_pass"] for r in stability):
        failed = [r["ar"] for r in stability if not r["stability_pass"]]
        raise RuntimeError(f"delta-theta numerical stability audit failed at AR={failed}")

    os.makedirs(REPORT_DIR, exist_ok=True)
    with open(OUT_CSV, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=["ar", "dtheta_050", "dtheta_075"])
        writer.writeheader()
        writer.writerows(rows)
    with open(OUT_STABILITY_CSV, "w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=list(stability[0]))
        writer.writeheader()
        writer.writerows(stability)

    ars = [r["ar"] for r in rows]
    d075_raw = [r["dtheta_075"] for r in rows]
    finite_pairs = [(a, d) for a, d in zip(ars, d075_raw) if math.isfinite(d)]
    xs = [a for a, _ in finite_pairs]
    ys = [d for _, d in finite_pairs]
    derived_ar = float(np.interp(
        ENGINEERING_TOLERANCE_DEG,
        list(reversed(ys)),
        list(reversed(xs)),
    ))
    frozen = {
        "schema_version": "m4_delta_theta_075_v2",
        "frozen_at": FROZEN_AT,
        "definition_changed": False,
        "tau_main": TAU_MAIN,
        "engineering_tolerance_deg": ENGINEERING_TOLERANCE_DEG,
        "derived_ar_at_15deg": round(derived_ar, 3),
        "angle_convention": ANGLE_CONVENTION,
        "geometry_model": GEOMETRY_MODEL,
        "solve_method": "first_lobe_minimum_bracket_then_deterministic_bisection_on_polygon_iou",
        "threshold_semantics": THRESHOLD_SEMANTICS,
        "solve_tolerance_deg": SOLVE_TOL_DEG,
        "ar_grid_max": AR_GRID_MAX,
        "high_ar_policy": HIGH_AR_POLICY,
        "stability_audit": os.path.relpath(OUT_STABILITY_CSV, ROOT),
        "stability_all_pass": True,
        "ar": ars,
        "dtheta_075": [_json_number(x) for x in d075_raw],
        "dtheta_050": [_json_number(r["dtheta_050"]) for r in rows],
        "note": (
            "delta_theta_075(ar): minimum le90 long-axis rotation for congruent, "
            "concentric, same-scale rectangle IoU<0.75; None means the threshold "
            "is not crossed on [0,90] deg; ar>grid uses conservative inverse-ar tail"
        ),
    }
    with open(OUT_JSON, "w", encoding="utf-8") as fp:
        json.dump(frozen, fp, indent=2, ensure_ascii=True)
    print(f"DELTA_THETA_FROZEN derived_ar@15deg={derived_ar:.3f} "
          f"n_ar={len(ars)} grid_max={AR_GRID_MAX:g} stability=PASS")


def verify_frozen():
    """Read-only verification of the corrected frozen artifact."""
    _require_shapely()
    if not os.path.isfile(OUT_JSON) or not os.path.isfile(OUT_CSV) or not os.path.isfile(OUT_STABILITY_CSV):
        raise RuntimeError("missing frozen delta-theta artifact family")
    with open(OUT_JSON, encoding="utf-8") as fp:
        frozen = json.load(fp)
    expected = {
        "schema_version": "m4_delta_theta_075_v2",
        "frozen_at": FROZEN_AT,
        "definition_changed": False,
        "tau_main": TAU_MAIN,
        "angle_convention": ANGLE_CONVENTION,
        "geometry_model": GEOMETRY_MODEL,
        "solve_tolerance_deg": SOLVE_TOL_DEG,
        "ar_grid_max": AR_GRID_MAX,
        "high_ar_policy": HIGH_AR_POLICY,
        "threshold_semantics": THRESHOLD_SEMANTICS,
        "stability_all_pass": True,
    }
    drift = {key: (frozen.get(key), value) for key, value in expected.items() if frozen.get(key) != value}
    if drift:
        raise RuntimeError(f"frozen delta-theta metadata drift: {drift}")
    curve = list(csv.DictReader(open(OUT_CSV, encoding="utf-8")))
    if len(curve) != len(frozen.get("ar", [])):
        raise RuntimeError("frozen JSON/CSV curve length mismatch")
    for index, row in enumerate(curve):
        if abs(float(row["ar"]) - float(frozen["ar"][index])) > 1e-12:
            raise RuntimeError(f"frozen JSON/CSV AR mismatch at row {index}")
        for csv_key, json_key in (("dtheta_050", "dtheta_050"), ("dtheta_075", "dtheta_075")):
            csv_value = float(row[csv_key])
            json_value = frozen[json_key][index]
            if json_value is None:
                if math.isfinite(csv_value):
                    raise RuntimeError(f"frozen JSON/CSV finite-state mismatch at row {index}/{json_key}")
            elif abs(csv_value - float(json_value)) > 5.1e-5:
                raise RuntimeError(f"frozen JSON/CSV value mismatch at row {index}/{json_key}")
    stability = list(csv.DictReader(open(OUT_STABILITY_CSV, encoding="utf-8")))
    if not stability or any(row.get("stability_pass") != "True" for row in stability):
        raise RuntimeError("frozen stability CSV is empty or contains a failure")
    probed = {round(float(row["ar"]), 6) for row in stability}
    if not {1.0, 1.05, 1.1, 2.1}.issubset(probed):
        raise RuntimeError("frozen stability CSV lacks corrected near-square first-crossing probes")
    square_075 = dtheta_tau(1.0, 0.75)
    square_050 = dtheta_tau(1.0, 0.50)
    if not math.isfinite(square_075) or not math.isinf(square_050):
        raise RuntimeError("near-square first-crossing invariant failed")
    print(
        f"DELTA_THETA_VERIFY_OK frozen_at={FROZEN_AT} definition_changed=false "
        f"square_tau075={square_075:.6f} square_tau050=inf"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--verify-frozen", action="store_true", help="read-only frozen artifact verification")
    args = parser.parse_args()
    verify_frozen() if args.verify_frozen else main()
