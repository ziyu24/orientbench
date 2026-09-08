"""Independent static check of the bounded r026 prediction-source audit."""
import argparse
import json
from pathlib import Path

from orientbench.r025.provenance import audit


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--root", type=Path, required=True)
    args = parser.parse_args(); root = args.root.resolve(); actual = audit(root)
    saved = json.loads((root / "runs/r026/artifacts/prediction_sources.json").read_text())
    (root / "runs/r026/artifacts/prediction_sources_corrected.json").write_text(json.dumps(actual, indent=2) + "\n")
    report = {"requirements_observed": actual["generator_requirements_observed"],
              "overall": actual["overall"],
              "unit_completeness": {u: x["complete_output_obtained"] for u, x in actual["units"].items()},
              "saved_matches_recomputed": saved == actual,
              "corrected_audit": "prediction_sources_corrected.json",
              "pass": all(actual["generator_requirements_observed"].values())
                      and not any(x["complete_output_obtained"] for x in actual["units"].values()),
              "independence": "Re-reads Git historical generator, bounded filesystem records and model metadata; does not trust a conclusion field."}
    (root / "runs/r026/artifacts/prediction_provenance_verify.json").write_text(json.dumps(report, indent=2) + "\n")
    if not report["pass"]:
        raise SystemExit("provenance verification failed")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__":
    main()
