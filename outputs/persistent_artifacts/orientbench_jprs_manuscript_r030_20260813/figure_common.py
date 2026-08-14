#!/usr/bin/env python3
"""Render r030 figures from frozen, already-computed evidence only."""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]
FIG = Path(__file__).resolve().parent
R27 = ROOT / "outputs/persistent_artifacts/orientbench_jprs_paper_package_r027_20260813"
R28 = ROOT / "outputs/persistent_artifacts/orientbench_corrective_audit_r028_20260813"
BUNDLE = ROOT / "audit_bundles/r028"

def finish(fig, name):
    fig.tight_layout()
    for ext in ("svg", "png"):
        fig.savefig(FIG / f"{name}.{ext}", dpi=220, bbox_inches="tight")
    plt.close(fig)

def ar_threshold_scan():
    d = pd.read_csv(R28 / "dota_tta_localization_corrected_ar_scan.csv")
    fig, ax = plt.subplots(figsize=(7.2, 4.5))
    for unit, z in d.groupby("unit"):
        ax.plot(z.cutoff, z.AUGRC, marker="o", markersize=2.5, label=unit)
    ax.axvline(2.1, color="black", linestyle="--", linewidth=1, label="frozen AR boundary")
    ax.set(xlabel="Minimum GT aspect ratio", ylabel="AUGRC of corrected TTA-localization",
           title="Descriptive DOTA AR-threshold scan")
    ax.grid(alpha=.25); ax.legend(frameon=False)
    finish(fig, "ar_threshold_scan")

def witness_effect_ci():
    w = pd.read_csv(R27 / "r023_formal_witnesses.csv")
    h = pd.read_csv(R27 / "r026_formal_hypotheses.csv")
    rows=[]
    for _,r in w.iterrows():
        rows.append((f"DIOR {r['key']} {r['endpoint']}",r.dod,r.dod_ci_low,r.dod_ci_high,True))
    for _,r in h.iterrows():
        rows.append((f"DOTA {r['key']} {r['endpoint']}",r.dod,r.dod_ci_low,r.dod_ci_high,bool(r.witness)))
    fig,ax=plt.subplots(figsize=(8.2,7.2)); y=np.arange(len(rows))
    for i,(label,x,lo,hi,ok) in enumerate(rows):
        color="#1565c0" if ok else "#8d6e63"
        ax.errorbar(x,i,xerr=[[x-lo],[hi-x]],fmt="o",color=color,
                    markerfacecolor=color if ok else "white",markeredgecolor=color,capsize=3)
    ax.axvline(0,color="black",linewidth=1);ax.set_yticks(y,[r[0] for r in rows]);ax.invert_yaxis()
    ax.set(xlabel="Difference-of-differences with 95% bootstrap CI",title="Formal AR-domain effects")
    ax.grid(axis="x",alpha=.25);finish(fig,"witness_effect_ci")

def geometric_tolerance():
    d=json.loads((BUNDLE/"dota/m4_delta_theta_075_frozen.json").read_text())
    x=np.asarray(d["ar"],float); y=np.asarray([np.nan if v is None else v for v in d["dtheta_075"]],float)
    keep=x<=10
    fig,ax=plt.subplots(figsize=(7.2,4.5));ax.plot(x[keep],y[keep],color="#6a1b9a",linewidth=2)
    ax.axvline(2.1,color="black",linestyle="--",linewidth=1);ax.axhline(15,color="#ef6c00",linestyle=":",linewidth=1)
    ax.set(xlabel="Aspect ratio",ylabel=r"Frozen $\delta_{0.75}$ (degrees)",title="Geometry-derived orientation tolerance")
    ax.grid(alpha=.25);finish(fig,"geometric_tolerance")

def bootstrap_distribution():
    b=np.load(BUNDLE/"dota/bootstrap.npy")
    bm=np.mean([b[:,2]-b[:,0],b[:,10]-b[:,8]],axis=0)
    ba=np.mean([b[:,6]-b[:,4],b[:,14]-b[:,12]],axis=0)
    d=bm-ba; point=0.014321113744247596
    fig,ax=plt.subplots(figsize=(7.2,4.5));ax.hist(d,bins=60,color="#00897b",alpha=.8)
    ax.axvline(point,color="black",linewidth=1.5,label="frozen point estimate")
    ax.axvspan(np.quantile(d,.025),np.quantile(d,.975),color="#ffb300",alpha=.2,label="95% interval")
    ax.set(xlabel="Dataset AUGRC difference-of-differences",ylabel="Archived bootstrap count",title="DOTA frozen bootstrap distribution")
    ax.legend(frameon=False);finish(fig,"bootstrap_distribution")

BUILDERS={
 "ar_threshold_scan":ar_threshold_scan,
 "witness_effect_ci":witness_effect_ci,
 "geometric_tolerance":geometric_tolerance,
 "bootstrap_distribution":bootstrap_distribution,
}

if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser();p.add_argument("name",choices=BUILDERS);a=p.parse_args();BUILDERS[a.name]()
