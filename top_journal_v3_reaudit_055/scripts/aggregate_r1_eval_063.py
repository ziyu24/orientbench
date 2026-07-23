"""aggregate_r1_eval_063.py — collect per-run eval JSONs into the matrix + block seed-variance.
Re-runnable: reflects whatever eval JSONs exist so far (partial or full). Writes:
 reports/r1_valid_heads_full_metrics_063.csv, reports/r1_valid_head_blocks_063.csv,
 updates reports/r1_angle_coder_matrix.csv + r1_angle_coder_matrix_seed_variance.csv.
No mechanism conclusion is emitted; NRC<1 labeled non-reversed, never calibrated.
"""
import os, json, glob, csv
import numpy as np
ROOT = "/home/rspip/cqc/pro/study/orientbench"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
EV = f"{REP}/r1_eval"

def load():
    out = {}
    for f in glob.glob(f"{EV}/*.json"):
        try: r = json.load(open(f)); out[r["run_id"]] = r
        except Exception: pass
    return out

def main():
    ev = load()
    cols = ["run_id", "angle_head", "dataset", "seed", "n_matched", "n_masked_ar16",
            "AP50_val_log", "AP50_self", "AP75_self", "masked_angle_error_mean",
            "native_signal", "masked_NRC_native", "masked_NRC_native_CI",
            "masked_NRC_score", "masked_AURC_native", "masked_Risk70_native", "masked_Risk90_native"]
    rows = []
    for rid in sorted(ev):
        r = ev[rid]; rows.append({c: r.get(c, "") for c in cols})
    with open(f"{REP}/r1_valid_heads_full_metrics_063.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)

    # block seed-variance (6 blocks)
    blocks = {}
    for rid, r in ev.items():
        if "masked_NRC_native" not in r: continue
        k = (r["angle_head"], r["dataset"]); blocks.setdefault(k, []).append(r)
    bcols = ["angle_head", "dataset", "n_seeds", "mean_AP50_val", "mean_AP75_self",
             "mean_angle_error", "mean_NRC_native", "std_NRC_native", "min_NRC_native",
             "max_NRC_native", "mean_NRC_score", "all_seed_native_reverse_NRCgt1",
             "native_CI_lo_min", "eligible_for_mechanism_interpretation", "note"]
    brows = []
    for (h, d), rs in sorted(blocks.items()):
        nv = [x["masked_NRC_native"] for x in rs]
        ns = [x.get("masked_NRC_score", np.nan) for x in rs]
        ap50 = [x.get("AP50_val_log") or 0 for x in rs]
        ap75 = [x.get("AP75_self") or 0 for x in rs]
        ae = [x.get("masked_angle_error_mean") or 0 for x in rs]
        ci_los = [x.get("masked_NRC_native_CI", [np.nan, np.nan])[0] for x in rs]
        all_rev = all(v > 1 for v in nv)
        ci_lo_min = min(ci_los) if ci_los else float("nan")
        brows.append(dict(angle_head=h, dataset=d, n_seeds=len(rs),
            mean_AP50_val=round(np.mean(ap50), 4), mean_AP75_self=round(np.mean(ap75), 4),
            mean_angle_error=round(np.mean(ae), 4), mean_NRC_native=round(np.mean(nv), 4),
            std_NRC_native=round(np.std(nv), 4), min_NRC_native=round(min(nv), 4),
            max_NRC_native=round(max(nv), 4), mean_NRC_score=round(np.nanmean(ns), 4),
            all_seed_native_reverse_NRCgt1=all_rev,
            native_CI_lo_min=round(ci_lo_min, 4) if ci_lo_min == ci_lo_min else "nan",
            eligible_for_mechanism_interpretation=("only_after_full_3seed_matrix_and_preregistered_A_or_B"),
            note=("3-seed complete" if len(rs) == 3 else f"{len(rs)}/3 seeds (partial)")))
    with open(f"{REP}/r1_valid_head_blocks_063.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=bcols); w.writeheader(); w.writerows(brows)
    print(f"aggregated {len(ev)} eval JSONs; {len(brows)} blocks with native NRC")
    for b in brows:
        print(f"  {b['angle_head']:4s} {b['dataset']:8s} seeds={b['n_seeds']} "
              f"NRC_native={b['mean_NRC_native']} (CI_lo_min={b['native_CI_lo_min']}) "
              f"NRC_score={b['mean_NRC_score']} allrev={b['all_seed_native_reverse_NRCgt1']}")

if __name__ == "__main__":
    main()
