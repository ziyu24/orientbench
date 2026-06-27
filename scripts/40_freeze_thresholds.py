#!/usr/bin/env python3
"""40_freeze_thresholds.py — freeze DOTA D2 thresholds (D1/R8 approved, token-gated).

Uses D_cal ONLY. Writes frozen DOTA gate values into configs/thresholds.yaml with
freeze metadata + data/code fingerprints, then records a sha256 of the frozen
file. B_C1/A_A4 stay pending (need RHINO/A4 hosts). Does NOT consult D_audit.
"""
from __future__ import annotations

import argparse
import hashlib
import os
import sys

import yaml

PROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIGS = os.path.join(PROOT, "configs")
REPORT_DIR = os.path.join(PROOT, "outputs", "bench_core", "reports")
PRED = os.path.join(PROOT, "outputs", "predictions", "DOTA-v1.0")
TOKEN = "SUPERVISOR_APPROVED_012_D1_R8_D6_HOST_TRAINING"


def _sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _code_fingerprint():
    h = hashlib.sha256()
    base = os.path.join(PROOT, "orientbench")
    for root, _d, files in os.walk(base):
        for f in sorted(files):
            if f.endswith(".py"):
                h.update(_sha256_file(os.path.join(root, f)).encode())
    return h.hexdigest()[:16]


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--approval-token", required=True)
    ap.add_argument("--freeze-time", required=True)
    args = ap.parse_args(argv)
    if args.approval_token != TOKEN:
        print("[FATAL] approval token mismatch; refusing to freeze")
        return 2

    cand_path = os.path.join(CONFIGS, "thresholds.calibration_candidate.yaml")
    cand = yaml.safe_load(open(cand_path, encoding="utf-8"))
    # integrity checks (D_cal only)
    assert cand["approval_status"] == "pending", "candidate already non-pending?"
    assert cand["n_D_cal_images"] > 0, "no D_cal images"
    obs = cand["observed_per_baseline"]
    assert len(obs) >= 3, "need >=3 detectors"
    for k, v in obs.items():
        dc = v["D_cal"]
        for fld in ("Risk@90", "NRC_AUC", "median_orient_err_deg", "n_matched"):
            assert fld in dc, f"{k} missing {fld}"
        assert dc["n_matched"] > 100, f"{k} too few matches"

    # data + code fingerprints (D_cal artifacts only)
    gt = os.path.join(PRED, "_dcal_subset", "gt_mmrotate.jsonl")
    data_fp = hashlib.sha256((_sha256_file(gt) + _sha256_file(cand_path)).encode()).hexdigest()[:16]
    code_fp = _code_fingerprint()

    thr = yaml.safe_load(open(os.path.join(CONFIGS, "thresholds.yaml"), encoding="utf-8"))
    thr["freeze_status"] = "partial_frozen_dota_d2"
    thr["freeze_time"] = args.freeze_time
    thr["responsible_role"] = {"B_C1": None, "A_A4": None, "D2": "supervisor"}
    thr["approval_token"] = args.approval_token
    thr["calibration_split"] = "D_cal"
    thr["metric_version"] = "orientation_risk_v1"
    thr["normalization_version"] = "longside_v1"
    thr["data_fingerprint"] = data_fp
    thr["code_fingerprint"] = code_fp
    thr["code_commit"] = "no_git_repo"
    # D2 frozen DOTA partial-audit gate (pre-registered + D_cal-referenced; NOT D_audit-fit)
    thr["D2"] = {
        "status": "frozen",
        "scope": "DOTA-v1.0 partial formal audit (baselines #1,#20,#32)",
        "spearman_mAP_NRC_max": 0.95,
        "fdr_method": "benjamini_hochberg",
        "per_detector_nrc_auc_pass_max": 1.0,
        "orientation_risk_metric": "angle_error_canonical_longside (deg)",
        "near_square_masked": True,
        "dcal_reference": {k: {"Risk@90_deg": obs[k]["D_cal"]["Risk@90"],
                               "NRC_AUC": obs[k]["D_cal"]["NRC_AUC"]} for k in obs},
        "gate_rule": ("per detector PASS if NRC_AUC <= 1.0; D2-independence stop if "
                      "Spearman(mAP rank, NRC rank) > 0.95"),
        "calibration_note": "thresholds from project file (§12.2) + 'beat random' principle, "
                            "referenced against D_cal; D_audit NOT consulted.",
    }
    # B_C1 / A_A4 remain pending (need RHINO / A4 hosts)
    thr.setdefault("B_C1", {})["status"] = "pending_host"
    thr.setdefault("A_A4", {})["status"] = "pending_host"
    cl = thr.get("change_log") or []
    cl.append({"time": args.freeze_time, "role": "supervisor",
               "action": "FREEZE DOTA D2 partial (D1/R8, token 012); B_C1/A_A4 pending hosts; "
                         f"data_fp={data_fp} code_fp={code_fp}"})
    thr["change_log"] = cl

    out = os.path.join(CONFIGS, "thresholds.yaml")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("# FROZEN (partial: DOTA D2). D1/R8 approved 012. Do NOT edit by hand.\n")
        yaml.safe_dump(thr, fh, allow_unicode=True, sort_keys=False)
    frozen_hash = _sha256_file(out)

    # mark candidate approved
    cand["approval_status"] = "approved_frozen_dota_d2"
    with open(cand_path, "w", encoding="utf-8") as fh:
        yaml.safe_dump(cand, fh, allow_unicode=True, sort_keys=False)

    rec = [f"# Threshold Freeze Record", "", f"> freeze_time: {args.freeze_time}",
           f"> approval_token: {args.approval_token}", "",
           f"- freeze_status: **partial_frozen_dota_d2** (B_C1/A_A4 pending hosts)",
           f"- calibration_split: D_cal (D_audit NOT consulted)",
           f"- metric_version: orientation_risk_v1 / normalization_version: longside_v1",
           f"- data_fingerprint: `{data_fp}`  code_fingerprint: `{code_fp}`",
           f"- **frozen thresholds.yaml sha256: `{frozen_hash}`**", "",
           "## Frozen DOTA D2 gate",
           "- per_detector_nrc_auc_pass_max = 1.0 (detector passes if NRC_AUC<=1.0, beats random)",
           "- spearman_mAP_NRC_max = 0.95 (D2 independence stop condition, project §12.2)",
           "- orientation_risk_metric = angle_error_canonical_longside (deg); near_square masked",
           "- D_cal reference: " + ", ".join(
               f"{k}:NRC={obs[k]['D_cal']['NRC_AUC']}/R@90={obs[k]['D_cal']['Risk@90']}deg" for k in obs),
           "", "此后不得因 D_audit 修改阈值；定义级错误只能另起版本并保留旧版本。"]
    with open(os.path.join(REPORT_DIR, "threshold_freeze_record.md"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(rec) + "\n")
    print(f"[ok] FROZEN DOTA D2. thresholds.yaml sha256={frozen_hash}")
    print(f"[ok] data_fp={data_fp} code_fp={code_fp}; wrote threshold_freeze_record.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
