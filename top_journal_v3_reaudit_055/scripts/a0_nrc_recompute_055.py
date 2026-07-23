"""A0-1 NRC protocol-drift recompute (055 re-audit).

Single authoritative source: 052 artifact-governed matched_17field tables
(real detector output, checkpoint sha256, carry aspect_ratio/near_square/split).
Recompute detection-score NRC(score->angle_error) under the FROZEN masked
protocol vs unmasked, to isolate the masked/unmasked protocol effect that B
flagged. #10/#11 (LSKNet) have no 052 table -> masked-only from features_v2,
explicitly flagged.

No training, no detector inference, no threshold/split change. Read-only.
"""
import json, os, csv, sys, math
import numpy as np
ROOT="/home/rspip/cqc/pro/study/orientbench"; sys.path.insert(0,ROOT); os.chdir(ROOT)
from orientbench.metrics.nrc_auc import nrc_auc
from orientbench.metrics.risk_coverage import risk_at_coverage, aurc

OUT=f"{ROOT}/top_journal_v3_reaudit_055/reports"
M052=f"{ROOT}/outputs/persistent_artifacts/orientbench_real_052/matched_tables"
FEAT=f"{ROOT}/measure_fix_v2/artifacts/features_v2"

# cells with authoritative 052 matched tables
CELLS_052=[("DIOR-R","22","rotated_retinanet_psc","DIOR#22"),
           ("FAIR1M-v1.0","24","rotated_retinanet_psc","FAIR1M#24"),
           ("SODA-A","23","rotated_retinanet_psc","SODA#23"),
           ("DOTA-v1.0","20","rotated_retinanet_psc","DOTA#20"),
           ("DIOR-R","3","oriented_rcnn","DIOR#3"),
           ("DIOR-R","61","rotated_rtmdet_s","DIOR#61"),
           ("SODA-A","4","oriented_rcnn","SODA#4")]
# cells only in (already-masked ar>=1.6) features_v2
CELLS_FEAT_ONLY=[("DIOR-R_10","DIOR#10","oriented_rcnn_lsknet"),
                 ("SODA-A_11","SODA#11","oriented_rcnn_lsknet")]

def metrics(score, err):
    score=np.asarray(score,float); err=np.asarray(err,float)
    m=np.isfinite(score)&np.isfinite(err); score,err=score[m],err[m]
    if score.size<50: return dict(n=int(score.size),nrc=float("nan"),aurc=float("nan"),r70=float("nan"),r90=float("nan"))
    return dict(n=int(score.size), nrc=round(nrc_auc(score,err)["nrc_auc"],4),
                aurc=round(aurc(score,err),4),
                r70=round(risk_at_coverage(score,err,0.7),3),
                r90=round(risk_at_coverage(score,err,0.9),3))

rows=[]
for ds,bid,det,name in CELLS_052:
    recs=[json.loads(l) for l in open(f"{M052}/{ds}/{bid}/matched_17field_full_052.jsonl")]
    score=np.array([r["score"] for r in recs])
    err=np.array([r["angle_error"] for r in recs])
    ar=np.array([r["aspect_ratio"] for r in recs])
    nsq=np.array([bool(r["near_square"]) for r in recs])
    split=np.array([r.get("d_cal_daudit_split_flag","") for r in recs])
    protocols={
        "unmasked_all":       np.ones(len(recs),bool),
        "masked_ar1.6_all":   ar>=1.6,
        "masked_ar1.3_all":   ar>=1.3,
        "masked_ar1.6_Daudit":(ar>=1.6)&(split=="D_audit"),
        "not_near_square_all":~nsq,
    }
    for proto,mask in protocols.items():
        mm=metrics(score[mask],err[mask])
        rows.append(dict(cell=name,dataset=ds,baseline_id=bid,detector=det,
                         source="052_matched_17field_full",protocol=proto,
                         near_square_handling=("excluded" if "masked" in proto or "not_near" in proto else "included"),
                         ar_threshold=("1.6" if "1.6" in proto else "1.3" if "1.3" in proto else "none"),
                         split=("D_audit" if "Daudit" in proto else "D_cal+D_audit"),
                         selector="detection_score", **mm))

# features_v2 (already ar>=1.6 masked), for #10/#11 and cross-check
for f,name,det in CELLS_FEAT_ONLY:
    recs=[json.loads(l) for l in open(f"{FEAT}/{f}.jsonl")]
    score=np.array([r["score"] for r in recs]); err=np.array([r["err"] for r in recs])
    split=np.array([r["split"] for r in recs])
    for proto,mask in {"masked_ar1.6_all(features_v2)":np.ones(len(recs),bool),
                       "masked_ar1.6_Daudit(features_v2)":split=="D_audit"}.items():
        mm=metrics(score[mask],err[mask])
        rows.append(dict(cell=name,dataset=f.rsplit("_",1)[0],baseline_id=f.rsplit("_",1)[1],detector=det,
                         source="features_v2_prefiltered_ar1.6",protocol=proto,
                         near_square_handling="excluded",ar_threshold="1.6",
                         split=("D_audit" if "Daudit" in proto else "D_cal+D_audit"),
                         selector="detection_score", **mm))

cols=["cell","dataset","baseline_id","detector","selector","source","protocol",
      "near_square_handling","ar_threshold","split","n","nrc","aurc","r70","r90"]
with open(f"{OUT}/a0_nrc_masked_unmasked_recompute_055.csv","w",newline="") as fh:
    w=csv.DictWriter(fh,fieldnames=cols); w.writeheader(); w.writerows(rows)

# compact console summary
print(f"{'cell':11s} {'unmasked':>9s} {'ar>=1.6':>9s} {'ar>=1.3':>9s} {'not_nsq':>9s}  n_ar1.6")
def g(name,proto):
    for r in rows:
        if r["cell"]==name and r["protocol"]==proto: return r
    return None
for _,_,_,name in CELLS_052:
    u=g(name,"unmasked_all"); a6=g(name,"masked_ar1.6_all"); a3=g(name,"masked_ar1.3_all"); nn=g(name,"not_near_square_all")
    print(f"{name:11s} {u['nrc']:9.3f} {a6['nrc']:9.3f} {a3['nrc']:9.3f} {nn['nrc']:9.3f}  {a6['n']}")
for f,name,_ in CELLS_FEAT_ONLY:
    a6=g(name,"masked_ar1.6_all(features_v2)")
    print(f"{name:11s} {'--':>9s} {a6['nrc']:9.3f} {'--':>9s} {'--':>9s}  {a6['n']} (features_v2)")
print("WROTE",f"{OUT}/a0_nrc_masked_unmasked_recompute_055.csv")
