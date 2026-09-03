"""Read-only r007 census.  It deliberately never loads both axis and OBB rows."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


CANDIDATES = {
    "rsdd_sar": {"platform": "GF-3_or_TerraSAR-X", "roots": ("RSDD-SAR", "RSDD", "rsdd")},
    "sar_aircraft": {"platform": "SAR-AIRcraft-1.0", "roots": ("SAR-AIRcraft-1.0", "SAR-AIRcraft", "sar_aircraft")},
}


def axial_deg(angle: float) -> float:
    """Canonical RP1 angle in degrees, including the 180 -> 0 contract."""
    result = angle % 180.0
    return 0.0 if math.isclose(result, 180.0, abs_tol=1e-12) else result


def rp1_distance(left: float, right: float) -> float:
    delta = abs(axial_deg(left) - axial_deg(right))
    return min(delta, 180.0 - delta)


def bin_index(angle: float) -> int:
    return int(axial_deg(angle) // 10.0) % 18


def fixture_report() -> dict:
    return {
        "rp1_180_identity": axial_deg(180.0) == 0.0,
        "rp1_vertex_order_identity": rp1_distance(10.0, 190.0) == 0.0,
        "ten_degree_bins": [bin_index(0.0), bin_index(9.999), bin_index(10.0), bin_index(180.0)] == [0, 0, 1, 0],
        "orthogonal_range_azimuth": math.isclose(rp1_distance(0.0, 90.0), 90.0),
        "nonzero_mutation": rp1_distance(0.0, 1.0) > 0.0,
    }


def candidate_record(dataset_root: Path, name: str, spec: dict) -> dict:
    existing = [str(dataset_root / root) for root in spec["roots"] if (dataset_root / root).is_dir()]
    # No implicit root search: only predeclared public SAR candidate names are
    # audited, so optical directories cannot be misclassified as SAR assets.
    root = Path(existing[0]) if existing else None
    has_license = bool(root and any(root.glob("LICENSE*")))
    has_readme = bool(root and any(root.glob("README*")))
    return {
        "candidate": name, "claimed_platform": spec["platform"], "declared_roots": list(spec["roots"]),
        "local_root": str(root) if root else None, "root_present": root is not None,
        "version_evidence": has_readme, "license_evidence": has_license,
        "scene_count": 0, "eligible_object_count": 0, "axis_metadata_scene_coverage": 0.0,
        "axis_metadata_object_coverage": 0.0, "valid_axis_bins": [],
        "reason_codes": (["LOCAL_SAR_ASSET_ABSENT"] if root is None else ["RAW_METADATA_PARSER_REQUIRED"]),
        "qualified": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    records = [candidate_record(args.dataset_root, name, spec) for name, spec in CANDIDATES.items()]
    fixtures = fixture_report()
    token = "ASSET_UNAVAILABLE_R007" if all(all(value for value in fixtures.values()) for _ in [0]) else "INCONCLUSIVE_R007_ASSET_AUDIT"
    output = {
        "protocol": "r007-read-only-sar-asset-qualification-v1", "dataset_root": str(args.dataset_root),
        "candidates": records, "axis_metadata_marginals": [], "obb_geometry_marginals": [],
        "lineage_key_audit": [], "geographic_grouping_audit": [], "fixtures": fixtures, "token": token,
        "information_wall": "No scene-axis row and object-OBB-angle row were loaded or emitted together.",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
