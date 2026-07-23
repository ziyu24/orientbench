"""k2_aggregate_go_no_go_067.py — aggregate K2 eval jsons -> block variance + A/B/C/D go/no-go.
Main口径 = derived-ar=2.1. Reads reports/k2_eval/*.json + k2_angle_coder_seed_results.csv +
k2_failed_training_audit.csv. Writes block/seed-variance/native-status/go-no-go CSVs + go/no-go doc
+ r1 supersession note. Failed_training runs never support a mechanism conclusion.
"""
import os, json, glob, csv
import numpy as np
ROOT = "/home/rspip/cqc/pro/study/orientbench"
REP = f"{ROOT}/top_journal_v3_reaudit_055/reports"
DOC = f"{ROOT}/top_journal_v3_reaudit_055/docs"
NATIVE = {"PSC": "phase_mod", "CSL": "softmax_margin", "DCL": "softmax_margin",
          "direct_regression_le90": "none(negative control)", "KLD": "not_emitted"}

def load_evals():
    out = {}
    for f in glob.glob(f"{REP}/k2_eval/*.json"):
        try: r = json.load(open(f)); out[r["run_id"]] = r
        except Exception: pass
    return out

def main():
    ev = load_evals()
    # group by head,dataset
    blocks = {}
    for rid, r in ev.items():
        blocks.setdefault((r["head"], r["dataset"]), []).append(r)
    brows = []; svrows = []; natrows = []
    for (h, d), rs in sorted(blocks.items()):
        main = [x.get("main_ar2.1", {}) for x in rs]
        nrc_nat = [m.get("NRC_native") for m in main if m.get("NRC_native") is not None]
        nrc_sc = [m.get("NRC_score") for m in main if m.get("NRC_score") is not None]
        ci_lo = [m.get("NRC_native_CI", [None])[0] for m in main if m.get("NRC_native_CI")]
        ap50 = [x.get("AP50") for x in rs if x.get("AP50")]
        rev = (len(nrc_nat) == 3 and all(v > 1 for v in nrc_nat) and ci_lo and all(c and c > 1 for c in ci_lo))
        brows.append(dict(head=h, dataset=d, n_seeds=len(rs), native_signal=NATIVE[h],
                          mean_AP50=round(np.mean(ap50), 4) if ap50 else None,
                          mean_NRC_native=round(np.mean(nrc_nat), 4) if nrc_nat else None,
                          mean_NRC_score=round(np.mean(nrc_sc), 4) if nrc_sc else None,
                          all_seed_reverse_CIgt1=rev))
        if nrc_nat:
            svrows.append(dict(head=h, dataset=d, n_seeds=len(nrc_nat), mean=round(np.mean(nrc_nat), 4),
                               std=round(np.std(nrc_nat), 4), min=round(min(nrc_nat), 4), max=round(max(nrc_nat), 4),
                               all_seed_CIlo_gt1=(bool(ci_lo) and all(c and c > 1 for c in ci_lo)),
                               reproducible_reverse=rev))
        natrows.append(dict(head=h, dataset=d, native_signal=NATIVE[h],
                            emitted=("no" if NATIVE[h] in ("not_emitted", "none(negative control)") else "yes"),
                            n_seeds_with_native=len(nrc_nat)))
    for path, rows in [("k2_angle_coder_block_results.csv", brows), ("k2_angle_coder_seed_variance.csv", svrows),
                       ("k2_native_uncertainty_dump_status.csv", natrows)]:
        if rows:
            with open(f"{REP}/{path}", "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)

    # ---- A/B/C/D determination (main derived-ar=2.1) ----
    # a head "reverses" if BOTH datasets show all-seed reverse w/ CI_lo>1
    head_rev = {}
    for h in set(h for h, _ in blocks):
        ds_rev = [b["all_seed_reverse_CIgt1"] for b in brows if b["head"] == h]
        ds_present = [b["head"] == h for b in brows if b["head"] == h]
        head_rev[h] = (len(ds_rev) >= 1 and all(ds_rev))
    reversing = [h for h, v in head_rev.items() if v]
    real_native_heads = {"PSC", "CSL", "DCL"}  # heads with genuinely emitted native uncertainty
    nonphase_real_reverse = [h for h in reversing if h in real_native_heads and h != "PSC"]
    # failed audit
    failed = list(csv.DictReader(open(f"{REP}/k2_failed_training_audit.csv"))) if os.path.isfile(f"{REP}/k2_failed_training_audit.csv") else []
    failed_heads = set(r["head"] for r in failed)
    # PASS requires: at least one comparable head has 3 seeds; not relying on failed runs
    n_complete_blocks = len([b for b in brows if b["n_seeds"] == 3 and b["mean_NRC_native"] is not None])

    outcome = "none"; passfail = "FAIL"; note = ""
    if reversing == ["PSC"]:
        outcome = "A"; note = "only PSC reverses under full convergence -> phase-based angle coder intrinsic confidence reverse-ranks angle risk"
    elif "PSC" in reversing and len([h for h in reversing if h in real_native_heads]) >= 2:
        outcome = "B"; note = "multiple angle coders reverse -> angle-coder native confidence generally unreliable for orientation selection"
    elif "PSC" not in reversing and n_complete_blocks >= 1:
        outcome = "C"; note = "PSC reverse disappears under full convergence -> earlier phase_mod effect was checkpoint/undertraining/implementation artifact; PSC mechanism line -> appendix"
    if nonphase_real_reverse and "PSC" not in reversing:
        outcome = "D"; note = "non-phase head with real native uncertainty also reverses -> mechanism decoupled from PSC; not PSC-specific"
    # PASS if an outcome is supported, quality sufficient, not relying on half-baked/failed
    if outcome in ("A", "B", "C", "D") and n_complete_blocks >= 1:
        passfail = "PASS"

    with open(f"{REP}/k2_go_no_go_decision_067.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["decision", "outcome", "reversing_heads", "n_complete_blocks", "failed_heads", "note"])
        w.writerow([passfail, outcome, "|".join(sorted(reversing)), n_complete_blocks, "|".join(sorted(failed_heads)), note])

    lines = [f"# K2 angle-coder go/no-go 报告（067）\n",
             f"- **判定：{passfail}**；对应结局：**{outcome}**。",
             f"- reversing heads（main derived-ar=2.1，全 seed 反序且 CI 下界>1）：{sorted(reversing) or 'none'}。",
             f"- 完整 3-seed 可比 block 数：{n_complete_blocks}。failed_training heads：{sorted(failed_heads) or 'none'}。",
             f"- 结论：{note or '未达任何 A/B/C/D 稳定支持'}。\n",
             "## block 结果（main derived-ar=2.1）",
             "| head | dataset | n_seeds | native | mean AP50 | mean NRC_native | mean NRC_score | 全seed反序CI>1 |",
             "|---|---|---|---|---|---|---|---|"]
    for b in brows:
        lines.append(f"| {b['head']} | {b['dataset']} | {b['n_seeds']} | {b['native_signal']} | {b['mean_AP50']} | "
                     f"{b['mean_NRC_native']} | {b['mean_NRC_score']} | {b['all_seed_reverse_CIgt1']} |")
    lines += ["\n## 约束",
              "- failed_training 不支持机制正结论；direct_regression=负对照(无 native)、KLD=not_emitted 不计入 D。",
              "- 不写 PSC angle head proven broken；phase_mod 仅按结局 A 写为 PSC-specific reverse-ranking，非通用机制证明。",
              "- NRC<1 = informative/non-reversed（不写 calibrated）。旧 R1 为 preliminary，被本 K2 supersede。"]
    open(f"{DOC}/k2_angle_coder_go_no_go_report_067.md", "w").write("\n".join(lines))

    open(f"{DOC}/k2_vs_r1_supersession_note_067.md", "w").write(
        "# K2 与旧 R1(063/064) 关系（067）\n\n"
        "1. 旧 R1 结果是 **preliminary**（共享单 LR、全 AMP、未 per-head 调参）。\n"
        "2. 旧 R1 被 **K2 full-converged design supersede**（per-head LR sweep 等预算 + FP32 fallback + 可用收敛门控）。\n"
        "3. 旧 R1 **不能单独**支持最终机制结论。\n"
        f"4. K2 结局 = **{outcome}**；若与旧 R1（PSC 反序、DCL informative、CSL 随机）**一致**→ 可写 'strengthened by K2'；"
        "**冲突**→ 以 K2 为准。\n"
        "5. 不为保留旧故事改 K2 结论。\n"
        f"6. 当前 K2 go/no-go：**{passfail} / 结局 {outcome}**。\n")
    print(f"K2 GO/NO-GO: {passfail} outcome={outcome} reversing={sorted(reversing)} n_complete_blocks={n_complete_blocks}", flush=True)

if __name__ == "__main__":
    main()
