"""Catalogue-level necessary geometry checks; no pixels, task outcomes, or PSF claims.

Input CSV must contain distinct acquisitions from ONE site/sensor/product and a
common angular convention. The caller must verify these facts from native records.
Published table transcription is supported only as an illustrative calculation.
No catalogue triplet implies common tile support or independent noise realizations.
The ray calculation treats off-nadir as a zenith-angle proxy. It is not a native
ground-incidence or RPC-calibrated ray; those need a separate convention check.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import itertools
import json
import math
from pathlib import Path


def angle_distance(a: float, b: float, period: float = 360.0) -> float:
    if period not in (180.0, 360.0) or not all(math.isfinite(v) for v in (a, b)):
        raise ValueError("finite angles and period 180 or 360 required")
    return abs((a - b + period / 2) % period - period / 2)


def ray_distance(a: dict, b: dict) -> float:
    """Angular separation proxy, using catalogue off-nadir as zenith angle."""
    theta_a, theta_b = map(math.radians, (a["off_nadir_deg"], b["off_nadir_deg"]))
    phi = math.radians(angle_distance(a["azimuth_deg"], b["azimuth_deg"]))
    cosine = math.cos(theta_a) * math.cos(theta_b)
    cosine += math.sin(theta_a) * math.sin(theta_b) * math.cos(phi)
    return math.degrees(math.acos(max(-1.0, min(1.0, cosine))))


def validate_rows(rows: list[dict]) -> list[dict]:
    if len(rows) > 120:
        raise ValueError("one catalogue per invocation, maximum 120 acquisitions")
    seen = set()
    validated = []
    for row in rows:
        key = row["catalog_id"]
        if not key or key in seen:
            raise ValueError("empty or duplicate acquisition ID")
        seen.add(key)
        values = {k: float(row[k]) for k in ("gsd_m", "off_nadir_deg", "azimuth_deg")}
        if not all(math.isfinite(v) for v in values.values()):
            raise ValueError("missing or nonfinite geometry")
        if values["gsd_m"] <= 0 or not 0 <= values["off_nadir_deg"] < 90:
            raise ValueError("invalid GSD/off-nadir")
        if not 0 <= values["azimuth_deg"] < 360:
            raise ValueError("azimuth must be converted explicitly to [0,360)")
        validated.append({"catalog_id": key, **values})
    return sorted(validated, key=lambda r: r["catalog_id"])


def enumerate_triplets(rows: list[dict], limits: dict, period: float) -> list[dict]:
    rows = validate_rows(rows)
    output = []
    for anchor, redundant, complement in itertools.permutations(rows, 3):
        near_az = angle_distance(anchor["azimuth_deg"], redundant["azimuth_deg"])
        near_ray = ray_distance(anchor, redundant)
        far_angle = angle_distance(anchor["azimuth_deg"], complement["azimuth_deg"], period)
        far_ray = ray_distance(anchor, complement)
        off_delta = abs(redundant["off_nadir_deg"] - complement["off_nadir_deg"])
        gsd_ratio = max(redundant["gsd_m"], complement["gsd_m"]) / min(redundant["gsd_m"], complement["gsd_m"])
        if (near_az <= limits["redundant_azimuth_max_deg"]
                and near_ray <= limits["redundant_ray_max_deg"]
                and far_angle >= limits["complementary_angle_min_deg"]
                and far_ray >= limits["complementary_ray_min_deg"]
                and off_delta <= limits["candidate_off_nadir_difference_max_deg"]
                and gsd_ratio <= limits["candidate_gsd_ratio_max"]):
            output.append({"anchor": anchor["catalog_id"], "redundant": redundant["catalog_id"],
                           "complement": complement["catalog_id"], "near_azimuth_deg": near_az,
                           "near_ray_deg": near_ray, "complement_angle_deg": far_angle,
                           "complement_ray_deg": far_ray, "candidate_off_nadir_difference_deg": off_delta,
                           "candidate_gsd_ratio": gsd_ratio})
    return output


def audit(csv_path: Path, config_path: Path) -> dict:
    raw = csv_path.read_bytes()
    rows = list(csv.DictReader(raw.decode("utf-8-sig").splitlines()))
    config_raw = config_path.read_bytes()
    protocol = json.loads(config_raw.decode("utf-8-sig"))
    primary = protocol["primary_geometry"]
    cases = [("primary", primary)] + [(f"sensitivity_{i+1}", {**primary, **change})
                                     for i, change in enumerate(protocol["geometry_sensitivity"])]
    results = []
    for name, limits in cases:
        for period in (360.0, 180.0):
            triples = enumerate_triplets(rows, limits, period)
            results.append({"case": name, "period_deg": period, "limits": limits,
                            "catalogue_triplets": len(triples),
                            "distinct_anchors": len({r["anchor"] for r in triples}),
                            "triplets": triples})
    return {"input_sha256": hashlib.sha256(raw).hexdigest(),
            "config_sha256": hashlib.sha256(config_raw).hexdigest(), "acquisitions": len(rows),
            "scope": "Catalogue geometry only. The 180-degree case is an azimuth-axis proxy, "
                     "NOT a measured PSF axis. Ray distances use off-nadir as a zenith proxy, "
                     "not native ground incidence or calibrated RPC rays. Input GSD values "
                     "are used as supplied; their native sampling provenance is not verified. "
                     "No time, illumination, common tile, label, "
                     "visibility, independent-noise, or physical-operator eligibility is asserted.",
            "results": results}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    args = parser.parse_args()
    print(json.dumps(audit(args.csv, args.config), sort_keys=True, indent=2))
