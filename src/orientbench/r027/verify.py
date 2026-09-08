"""Independent check of r027's HBB diagnosis and access-limited conclusion."""
import argparse
import json
from pathlib import Path

from orientbench.r027.run import records


def main():
    p = argparse.ArgumentParser(); p.add_argument("--root", type=Path, required=True); a = p.parse_args(); root = a.root.resolve()
    cfg = json.loads((root / "configs/r027/protocol.json").read_text()); data = Path(cfg["dataset_root"])
    saved_path = root / "runs/r027/artifacts/input_qualification_corrected.json"
    saved = json.loads(saved_path.read_text())
    shared = {x.stem for x in (data / cfg["shared_v1_val_images"]).glob("*.png")}
    direct = records(data / cfg["current_v2_labels"], shared)
    report = {"current_hbb_matches_native_recount": direct == saved["current_hbb_on_shared_458"],
              "all_current_focus_horizontal": direct["focus"].get("objects", 0) == direct["geometry"].get("focus_axis_aligned", -1),
              "candidate_obb_absent": not saved["candidate_obb_package"]["exists"],
              "conclusion": saved["status"],
              "pass": direct == saved["current_hbb_on_shared_458"] and not saved["candidate_obb_package"]["exists"] and saved["status"] == "OBB_INPUT_NOT_ACQUIRED"}
    (root / "runs/r027/artifacts/independent_verify_corrected.json").write_text(json.dumps(report, indent=2) + "\n")
    if not report["pass"]: raise SystemExit("r027 verification failed")
    print(json.dumps(report, sort_keys=True))


if __name__ == "__main__": main()
