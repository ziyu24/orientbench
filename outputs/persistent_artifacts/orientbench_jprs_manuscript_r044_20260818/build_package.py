#!/usr/bin/env python3
"""Build r044 machine-readable tables and six editable figures from tracked evidence."""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
PAPER = ROOT / "docs/paper_jprs_r044"
TABLES = PAPER / "tables"
FIGS = PAPER / "figures"


def read_csv(rel):
    with (ROOT / rel).open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fields=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fields is None:
        fields = list(rows[0])
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def savefig(name):
    plt.tight_layout()
    for ext in ("svg", "png"):
        plt.savefig(FIGS / f"{name}.{ext}", dpi=220, bbox_inches="tight")
    svg = FIGS / f"{name}.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close()


def main():
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGS.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False})

    perturb_src = "top_journal_v3_reaudit_055/reports/pre_submission_s1s5_v1/s1a_full_pipeline_perturbation_v1.csv"
    perturb = read_csv(perturb_src)
    write_csv(TABLES / "controlled_perturbation.csv", perturb)

    geom_src = "top_journal_v3_reaudit_055/reports/m4_geometry_normalized_risk.csv"
    geom = read_csv(geom_src)
    write_csv(TABLES / "geometry_normalized_risk.csv", geom)

    human_src = "reports/m4_human_annotation_primary_summary_073.csv"
    human = read_csv(human_src)
    write_csv(TABLES / "human_disagreement.csv", human)

    curve_src = "top_journal_v3_reaudit_055/reports/m4_delta_theta_tau_curve.csv"
    curve = read_csv(curve_src)
    write_csv(TABLES / "geometry_tolerance_curve.csv", curve)

    nrc_src = "top_journal_v3_reaudit_055/reports/a0_masked_nrc_bootstrap_ci_055.csv"
    nrc = read_csv(nrc_src)
    write_csv(TABLES / "representative_nrc.csv", nrc)

    ltt_src = "top_journal_v3_reaudit_055/reports/m3_image_level_ltt.csv"
    ltt_all = read_csv(ltt_src)
    ltt = [r for r in ltt_all if r["score"] == "detection_score" and r["result_role"] == "PRIMARY" and r["alpha"] == "0.03" and r["selected"] == "True"]
    write_csv(TABLES / "image_level_ltt_primary.csv", ltt)

    cmp_src = "top_journal_v3_reaudit_055/reports/m3_instance_vs_image_comparison.csv"
    cmp_all = read_csv(cmp_src)
    cmp_rows = [r for r in cmp_all if r["score"] == "detection_score" and r["result_role"] == "PRIMARY" and r["alpha"] == "0.03"]
    write_csv(TABLES / "image_vs_iid_bound.csv", cmp_rows)

    reverse_src = "top_journal_v3_reaudit_055/reports/r3_reverse_perturbation.csv"
    reverse = read_csv(reverse_src)
    write_csv(TABLES / "reverse_control.csv", reverse)

    # Fig. 1: a real six-cell point summary, not a synthetic image example.
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    x = np.arange(len(perturb))
    ax.plot(x, [float(r["dAP50"]) for r in perturb], "o-", label=r"$\Delta$AP50")
    ax.plot(x, [float(r["dAP75"]) for r in perturb], "s-", label=r"$\Delta$AP75")
    ax2 = ax.twinx()
    ax2.plot(x, [float(r["d_angle"]) for r in perturb], "^-", color="#b23a48", label=r"$\Delta$ mean angle error")
    ax.axhline(0, color="0.55", lw=0.8)
    ax.set_xticks(x, [r["cell"].replace("-v1.0", "") for r in perturb], rotation=25, ha="right")
    ax.set_ylabel("Change in AP")
    ax2.set_ylabel("Change in angle error (deg)")
    ax.set_title("AP50 can remain unchanged while orientation quality collapses")
    lines = ax.get_lines()[:2] + ax2.get_lines()
    ax.legend(lines, [q.get_label() for q in lines], loc="center right", frameon=False)
    savefig("fig1_accuracy_reliability_separation")

    # Fig. 2: before/after panels for AP75 and mean angle error.
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 3.6))
    labels = [r["cell"].replace("-v1.0", "") for r in perturb]
    for ax, b, p, ylabel, title in [
        (axes[0], "base_AP75", "pert_AP75", "AP75", "Full-evaluator AP75"),
        (axes[1], "base_angle", "pert_angle", "Mean angle error (deg)", "Matched-pair orientation error"),
    ]:
        ax.bar(x - 0.18, [float(r[b]) for r in perturb], width=0.36, label="Original")
        ax.bar(x + 0.18, [float(r[p]) for r in perturb], width=0.36, label="Perturbed")
        ax.set_xticks(x, labels, rotation=30, ha="right")
        ax.set_ylabel(ylabel); ax.set_title(title)
    axes[0].legend(frameon=False)
    savefig("fig2_controlled_perturbation")

    # Fig. 3: exact deterministic rectangle tolerance curve from the frozen table.
    finite = [r for r in curve if float(r["ar"]) <= 8.0]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ar = np.array([float(r["ar"]) for r in finite])
    d75 = np.array([float(r["dtheta_075"]) for r in finite])
    d50 = np.array([np.nan if r["dtheta_050"] == "inf" else float(r["dtheta_050"]) for r in finite])
    ax.plot(ar, d75, label=r"$\delta_{0.75}(a)$", lw=2)
    ax.plot(ar, d50, label=r"$\delta_{0.50}(a)$", lw=2)
    ax.axvline(2.1, ls="--", color="0.35", label="reporting boundary a=2.1")
    ax.set(xlabel="Ground-truth aspect ratio a", ylabel="Tolerance angle (deg)", xlim=(1, 8), ylim=(0, 80), title="Rotation tolerance of congruent rectangles")
    ax.legend(frameon=False)
    savefig("fig3_geometry_tolerance")

    # Fig. 4: representative masked NRC with image-cluster intervals.
    fig, ax = plt.subplots(figsize=(7.2, 3.8))
    labels = [r["cell"].replace("-v1.0", "") + "\n" + r["selector"].replace("intrinsic_", "") for r in nrc]
    vals = np.array([float(r["nrc"]) for r in nrc])
    lo = np.array([float(r["ci_lo"]) for r in nrc]); hi = np.array([float(r["ci_hi"]) for r in nrc])
    colors = ["#2878b5" if r["selector"] == "detection_score" else "#d95f02" for r in nrc]
    ax.errorbar(np.arange(len(nrc)), vals, yerr=[vals-lo, hi-vals], fmt="none", ecolor="0.25", capsize=3)
    ax.scatter(np.arange(len(nrc)), vals, c=colors, s=35)
    ax.axhline(1, ls="--", color="0.4", label="random ranking")
    ax.set_xticks(np.arange(len(nrc)), labels, rotation=30, ha="right")
    ax.set_ylabel("NRC (lower is better)"); ax.set_title("Representative within-setting orientation-risk ranking")
    ax.legend(frameon=False)
    savefig("fig4_representative_nrc")

    # Fig. 5: formal image-level versus invalid iid counterfactual bounds.
    fig, ax = plt.subplots(figsize=(6.8, 3.8))
    labels = [r["cell"] for r in cmp_rows]
    xx = np.arange(len(cmp_rows))
    ax.bar(xx - .18, [float(r["new_image_ucb_calib"]) for r in cmp_rows], .36, label="Image-level HB UCB")
    ax.bar(xx + .18, [float(r["old_instance_iid_cp_ucb_calib_audit_only"]) for r in cmp_rows], .36, label="Instance-iid counterfactual")
    ax.set_xticks(xx, labels); ax.set_ylabel("Calibration upper bound")
    ax.set_title("The exchangeability unit changes the reported risk bound")
    ax.legend(frameon=False)
    savefig("fig5_image_vs_iid_bound")

    # Fig. 6: human double-annotation distribution summaries.
    fig, ax = plt.subplots(figsize=(7.0, 3.8))
    labels = [r["subset"] for r in human]
    xx = np.arange(len(human))
    mean = np.array([float(r["mean_deg"]) for r in human])
    lo = np.array([float(r["mean_cluster_ci95_low"]) for r in human]); hi = np.array([float(r["mean_cluster_ci95_high"]) for r in human])
    ax.errorbar(xx, mean, yerr=[mean-lo, hi-mean], fmt="o", capsize=4, color="#2a6f97", label="Mean and image-cluster 95% CI")
    ax.scatter(xx, [float(r["p90_deg"]) for r in human], marker="^", color="#bc4749", label="p90")
    ax.set_xticks(xx, labels, rotation=20, ha="right"); ax.set_ylabel("Circular disagreement (deg)")
    ax.set_title("Independent blinded long-axis annotations")
    ax.legend(frameon=False)
    savefig("fig6_human_disagreement")

    sources = {
        "fig1_accuracy_reliability_separation": perturb_src,
        "fig2_controlled_perturbation": perturb_src,
        "fig3_geometry_tolerance": curve_src,
        "fig4_representative_nrc": nrc_src,
        "fig5_image_vs_iid_bound": cmp_src,
        "fig6_human_disagreement": human_src,
    }
    manifest = []
    for stem, source in sources.items():
        for ext in ("svg", "png"):
            p = FIGS / f"{stem}.{ext}"
            manifest.append({"figure": stem, "format": ext, "generator": str(Path(__file__).resolve().relative_to(ROOT)), "canonical_source": source, "bytes": p.stat().st_size, "sha256": hashlib.sha256(p.read_bytes()).hexdigest()})
    write_csv(FIGS / "figure_manifest.csv", manifest)

    identity = [
        {"evidence_family":"controlled perturbation", "identity":"formal full-evaluator", "canonical_source":perturb_src, "allowed_use":"headline measurement-validity result"},
        {"evidence_family":"geometry-normalized risk", "identity":"formal", "canonical_source":geom_src, "allowed_use":"estimand and cross-unit descriptive rates"},
        {"evidence_family":"image-level LTT", "identity":"formal", "canonical_source":ltt_src, "allowed_use":"image-level finite-sample risk control"},
        {"evidence_family":"masked NRC", "identity":"audited descriptive", "canonical_source":nrc_src, "allowed_use":"within-setting ranking illustration"},
        {"evidence_family":"human double annotation", "identity":"human study", "canonical_source":human_src, "allowed_use":"noise anchor and threshold semantics"},
        {"evidence_family":"DOTA-v1.0", "identity":"post-outcome audited external replication", "canonical_source":"audit_bundles/r028/dota/r026_hypotheses.csv", "allowed_use":"local train/val only; no public-test comparison"},
    ]
    write_csv(TABLES / "evidence_identity.csv", identity)

    summary = {
        "schema_version": 1,
        "status": "BUILT_FROM_TRACKED_EVIDENCE",
        "gpu_used": 0,
        "training": 0,
        "inference": 0,
        "raw_dataset_access": 0,
        "figures": len(sources),
        "figure_files": len(sources) * 2,
        "tables": len(list(TABLES.glob("*.csv"))),
    }
    (Path(__file__).with_name("build_summary.json")).write_text(json.dumps(summary, indent=2) + "\n")


if __name__ == "__main__":
    main()
