"""Independent, outcome-blind validation of the r015 preflight evidence."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path


def fail(message: str) -> None:
    raise ValueError(message)


def validate_records(records: dict[str, list[dict]]) -> None:
    expected = {"train": 4065, "calibration": 7416}
    if set(records) != set(expected):
        fail("partitions")
    seen: set[int] = set()
    for part, count in expected.items():
        rows = records[part]
        if len(rows) != count:
            fail(f"count:{part}")
        for row in rows:
            oid = row.get("object_id")
            if not isinstance(oid, int) or oid in seen:
                fail("object identity")
            seen.add(oid)
            if not row.get("image_id") or not row.get("cat_id"):
                fail("loc-cat source")
            if len(row.get("labels", [])) != 3 or any(x not in (0, 1) for x in row["labels"]):
                fail("labels")
            origin = row.get("origin", {})
            if not all(isinstance(origin.get(k), (int, float)) for k in ("left", "top", "side", "rho")):
                fail("window origin")
            if origin["side"] <= 4 or origin["rho"] <= 0:
                fail("window dimensions")
            if not all(math.isfinite(float(row.get(k, float("nan")))) for k in ("L", "S", "theta")):
                fail("geometry finite")
            if row["L"] < row["S"] or not (-math.pi <= row["theta"] <= math.pi):
                fail("canonical radians geometry")
            if not isinstance(row.get("window_sha256"), str) or len(row["window_sha256"]) != 64:
                fail("window hash")


def mutation_tests(records: dict[str, list[dict]]) -> dict[str, bool]:
    """Exercise actual validation entrypoints with malformed evidence, not token checks."""
    import copy
    sample = copy.deepcopy(records)
    bad = {
        "duplicate_object": lambda x: x["train"].__setitem__(0, x["train"][1]),
        "wrong_label": lambda x: x["train"][0].__setitem__("labels", [2, 0, 1]),
        "degree_angle": lambda x: x["train"][0].__setitem__("theta", 180.0),
        "missing_origin": lambda x: x["train"][0].pop("origin"),
        "bad_loc_cat": lambda x: x["train"][0].__setitem__("cat_id", ""),
    }
    result = {}
    for name, mutate in bad.items():
        trial = copy.deepcopy(sample)
        mutate(trial)
        try:
            validate_records(trial)
        except ValueError:
            result[name] = True
        else:
            result[name] = False
    reordered = {k: list(reversed(v)) for k, v in sample.items()}
    validate_records(reordered)
    result["legal_reorder_accepted"] = True
    if not all(result.values()):
        fail("mutation test acceptance")
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preflight", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    evidence = json.loads(args.preflight.read_text())
    if evidence.get("test_opened") or evidence.get("model_forward"):
        fail("preflight scope")
    if not evidence.get("render_pass"):
        fail("renderer gate")
    validate_records(evidence["records"])
    result = {
        "protocol": "r015-preflight-validator-v1",
        "accepted": True,
        "counts": evidence["counts"],
        "render_max_rgb": evidence["max_rgb_difference"],
        "render_max_theta_pi": evidence["max_theta_pi_view_exchange_difference"],
        "mutation_tests": mutation_tests(evidence["records"]),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
