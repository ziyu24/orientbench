"""R3b — numerical IoU(delta-theta; aspect ratio) curves for concentric rectangles.
Reproducible; saves PNG + PDF + the underlying CSV. No detector, no training."""
import os, math, csv
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely import affinity
ROOT="/home/rspip/cqc/pro/study/orientbench"
FIG=f"{ROOT}/top_journal_v3_reaudit_055/figures"
os.makedirs(FIG,exist_ok=True)

def rect(w,h,deg):
    p=Polygon([(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)])
    return affinity.rotate(p,deg,origin=(0,0),use_radians=False)
def iou(a,b):
    i=a.intersection(b).area; u=a.area+b.area-i; return i/u if u>0 else 0.0

ars=[1.0,1.2,1.6,2.0,4.0,8.0]
deltas=np.arange(0,90.5,1.0)
rows=[]; curves={}
for ar in ars:
    w,h=math.sqrt(ar),1/math.sqrt(ar)  # area=1, ratio=ar
    base=rect(w,h,0.0)
    ys=[]
    for d in deltas:
        v=iou(base,rect(w,h,d)); ys.append(v); rows.append(dict(aspect_ratio=ar,delta_theta_deg=float(d),iou=round(v,6)))
    curves[ar]=np.array(ys)

# CSV
with open(f"{FIG}/iou_delta_theta_aspect_ratio.csv","w",newline="") as f:
    w_=csv.DictWriter(f,fieldnames=["aspect_ratio","delta_theta_deg","iou"]); w_.writeheader(); w_.writerows(rows)

# delta_theta at IoU=0.5 and 0.75 per ar
def dtheta_at(ar,tau):
    ys=curves[ar]
    below=np.where(ys<tau)[0]
    return float(deltas[below[0]]) if len(below) else float("nan")

plt.figure(figsize=(7,5))
for ar in ars:
    plt.plot(deltas,curves[ar],label=f"ar={ar:g}")
plt.axhline(0.5,ls="--",c="gray",lw=1); plt.axhline(0.75,ls=":",c="gray",lw=1)
plt.text(2,0.51,"IoU=0.5 (AP50)",fontsize=8,color="gray")
plt.text(2,0.76,"IoU=0.75 (AP75)",fontsize=8,color="gray")
plt.xlabel(r"angle deviation $\delta\theta$ (deg)"); plt.ylabel("rotated IoU")
plt.title("IoU vs angle deviation, by aspect ratio (concentric rectangles)")
plt.legend(loc="upper right",fontsize=8); plt.grid(alpha=0.3); plt.ylim(0.15,1.02)
plt.tight_layout()
plt.savefig(f"{FIG}/iou_delta_theta_aspect_ratio.png",dpi=150)
plt.savefig(f"{FIG}/iou_delta_theta_aspect_ratio.pdf")
print("dtheta@0.5 / @0.75 per ar:")
for ar in ars:
    print(f"  ar={ar:g}: IoU>0.5 up to {dtheta_at(ar,0.5)}deg, IoU>0.75 up to {dtheta_at(ar,0.75)}deg, min IoU={curves[ar].min():.3f}")
print("WROTE", f"{FIG}/iou_delta_theta_aspect_ratio.{{png,pdf,csv}}")
