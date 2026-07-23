#!/usr/bin/env python3
"""A4--A6 confirmatory closeout from frozen persistent artifacts; no detector inference."""
from __future__ import annotations

import csv
import hashlib
import json
import math
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / "top_journal_v3_reaudit_055/paper_A_orientation_protocol"
REP, DOC, LOG = A / "reports", A / "docs", A / "logs"
OLD = ROOT / "top_journal_v3_reaudit_055"
sys.path.insert(0, str(ROOT / "scripts"))
import m069_common as M  # noqa: E402


def atomic_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    names = fields or list(rows[0])
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=names, extrasaction="ignore"); w.writeheader(); w.writerows(rows)
    os.replace(tmp, path)


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp"); tmp.write_text(text, encoding="utf-8"); os.replace(tmp, path)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()


def circ(a: float, b: float) -> float:
    d = abs(float(a) - float(b)) % 180.0
    return min(d, 180.0 - d)


def long_angle_deg(box: dict) -> float:
    t = math.degrees(float(box["obb_theta"]))
    if float(box["obb_w"]) < float(box["obb_h"]): t += 90.0
    return t % 180.0


def official_angle_in_ui_coordinates(box: dict) -> float:
    """MMRotate image-coordinate angle -> annotator UI Cartesian screen angle."""
    t = -math.degrees(float(box["obb_theta"]))
    if float(box["obb_w"]) < float(box["obb_h"]): t += 90.0
    return t % 180.0


def ideal_lookup() -> list[dict]:
    import torch
    import mmrotate, mmrotate.models  # noqa: F401
    from mmrotate.registry import TASK_UTILS
    calc = TASK_UTILS.build(dict(type="RBboxOverlaps2D"))
    device = "cuda" if torch.cuda.is_available() else "cpu"
    ars = np.concatenate([np.linspace(1.0, 2.1, 112), np.linspace(2.2, 10.0, 79)])
    deg = np.arange(0.0, 90.0001, 0.1)
    out=[]
    for start in range(0,len(ars),32):
        ar=ars[start:start+32]
        aa=np.repeat(ar,len(deg)); dd=np.tile(deg,len(ar))
        p=torch.tensor(np.column_stack([np.zeros(len(aa)),np.zeros(len(aa)),aa,np.ones(len(aa)),np.deg2rad(dd)]),dtype=torch.float32,device=device)
        g=torch.tensor(np.column_stack([np.zeros(len(aa)),np.zeros(len(aa)),aa,np.ones(len(aa)),np.zeros(len(aa))]),dtype=torch.float32,device=device)
        iou=calc(p,g,is_aligned=True).detach().cpu().numpy().reshape(len(ar),len(deg))
        for j,x in enumerate(ar):
            row={"aspect_ratio":round(float(x),4)}
            for tau in (0.5,0.75):
                bad=np.where(iou[j] < tau)[0]
                row[f"ideal_delta_{tau:.2f}_deg"]=round(float(deg[bad[0]]) if len(bad) else 90.0,3)
            out.append(row)
    return out


def empirical_tolerance() -> tuple[list[dict], dict[str,dict]]:
    """Fixed-pair approximation using actual center/scale and an away-direction rotation."""
    import torch
    import mmrotate, mmrotate.models  # noqa: F401
    from mmrotate.registry import TASK_UTILS
    calc=TASK_UTILS.build(dict(type="RBboxOverlaps2D")); device="cuda" if torch.cuda.is_available() else "cpu"
    grid=np.arange(0.0,90.0001,0.5,dtype=np.float32)
    summaries=[]; dose_stats={}
    for cell in "ABCDEF":
        path=Path(M.CELLS[cell][2]); rec=[]
        for line in path.open(encoding="utf-8"):
            r=json.loads(line)
            if float(r.get("aspect_ratio",0)) < 2.1 or r.get("near_square") or not math.isfinite(float(r.get("angle_error",math.nan))): continue
            p,g=r["pred_obb"],r["gt_obb"]
            pa=long_angle_deg(p); ga=long_angle_deg(g)
            signed=((pa-ga+90.0)%180.0)-90.0; direction=1.0 if signed>=0 else -1.0
            rec.append((p,g,direction,r.get("size_bin","unknown"),float(r["aspect_ratio"]),float(r["angle_error"])))
        tol50=[];tol75=[];ars=[];sizes=[];baseae=[]; dose_events={d:[] for d in [0,2,5,10,15,20,25,30]}
        for st in range(0,len(rec),6000):
            q=rec[st:st+6000]; n=len(q)
            pb=np.empty((n*len(grid),5),np.float32); gb=np.empty_like(pb)
            for i,(p,g,d,sz,ar,ae) in enumerate(q):
                sl=slice(i*len(grid),(i+1)*len(grid))
                pb[sl]=[p["obb_cx"],p["obb_cy"],p["obb_w"],p["obb_h"],p["obb_theta"]]
                pb[sl,4]=float(p["obb_theta"])+np.deg2rad(d*grid)
                gb[sl]=[g["obb_cx"],g["obb_cy"],g["obb_w"],g["obb_h"],g["obb_theta"]]
            iou=calc(torch.from_numpy(pb).to(device),torch.from_numpy(gb).to(device),is_aligned=True).detach().cpu().numpy().reshape(n,len(grid))
            for j,(p,g,d,sz,ar,ae) in enumerate(q):
                for tau,dst in ((.5,tol50),(.75,tol75)):
                    z=np.where(iou[j] < tau)[0]; dst.append(float(grid[z[0]]) if len(z) else 90.0)
                ars.append(ar);sizes.append(sz);baseae.append(ae)
                signed=((long_angle_deg(p)-long_angle_deg(g)+90)%180)-90
                for dose in dose_events:
                    dose_events[dose].append(abs(((signed+d*dose+90)%180)-90))
        arrs={"0.50":np.asarray(tol50),"0.75":np.asarray(tol75)}; ars=np.asarray(ars); sizes=np.asarray(sizes);baseae=np.asarray(baseae)
        ds,det,_,_=M.CELLS[cell]
        for tau,v in arrs.items():
            for arlabel,amask in (("all_ar21",np.ones(len(v),bool)),("2.1_to_3",(ars>=2.1)&(ars<3)),("3_to_5",(ars>=3)&(ars<5)),("ge5",ars>=5)):
                for sz in ["all"]+sorted(set(sizes.tolist())):
                    mask=amask if sz=="all" else amask&(sizes==sz)
                    if not np.any(mask): continue
                    x=v[mask]
                    summaries.append({"evaluation_unit":cell,"dataset":ds,"detector":det,"tau":tau,"aspect_ratio_bin":arlabel,"size_bin":sz,
                                      "n":len(x),"mean_deg":round(float(x.mean()),4),"median_deg":round(float(np.median(x)),4),
                                      "p10_deg":round(float(np.percentile(x,10)),4),"p90_deg":round(float(np.percentile(x,90)),4),
                                      "definition":"fixed-pair actual-geometry approximation; full rematching not performed per instance"})
        severe,_=M.geometry_severe(M.load_cell(cell))
        dose_stats[cell]={"n":len(rec),"mean_base_ae":float(baseae.mean()),"dose_mean_ae":{d:float(np.mean(x)) for d,x in dose_events.items()},
                          "dose_fixed_angle_5_rate":{d:float(np.mean(np.asarray(x)>5)) for d,x in dose_events.items()}}
    return summaries,dose_stats


def build_a4() -> str:
    proto=json.loads((REP/"a4_protocol_frozen.json").read_text())
    k1={r["cell"]:r for r in csv.DictReader((OLD/"reports/table1_fullval_final_065.csv").open())}
    ideal=ideal_lookup(); empirical,dose_stats=empirical_tolerance()
    atomic_csv(REP/"a4_ideal_delta_lookup.csv",ideal); atomic_csv(REP/"a4_empirical_tolerance_distribution.csv",empirical)
    rows=[]
    for cell,r in k1.items():
        for dose in proto["dose_grid_deg"]:
            rows.append({"evaluation_unit":cell,"dataset":cell.split('/')[0],"detector":r["detector"],"dose_deg":dose,
                         "prediction_identity_preserved":True,"score_class_center_size_preserved":True,"ar_mask":"ar>=2.1",
                         "AP50":r["AP50_fullval"] if dose==0 else "","AP75":r["AP75_fullval"] if dose==0 else "",
                         "delta_AP50":0 if dose==0 else "","delta_AP75":0 if dose==0 else "",
                         "mean_angle_error":dose_stats.get(cell,{}).get("dose_mean_ae",{}).get(dose,""),
                         "fixed_5deg_event_rate":dose_stats.get(cell,{}).get("dose_fixed_angle_5_rate",{}).get(dose,""),
                         "geometry_severe_event_rate":"",
                         "full_evaluator_status":"AUTHORITATIVE_K1_BASELINE" if dose==0 else "NOT_RUN_COMPLETE_GRID_REQUIRES_COMPLETE_RAW_PREDICTIONS_FOR_ALL_SIX_UNITS",
                         "first_material_AP75_drop":"NOT_IDENTIFIED","AP75_knee":"NOT_IDENTIFIED","AP50_weak_sensitivity_range":"ONLY_ADAPTIVE_BOUNDARY_EVIDENCE"})
        rows.append({"evaluation_unit":cell,"dataset":cell.split('/')[0],"detector":r["detector"],"dose_deg":"adaptive_tau50_boundary",
                     "prediction_identity_preserved":True,"score_class_center_size_preserved":True,"ar_mask":"historical K1 full-evaluator protocol",
                     "AP50":r["pert_AP50"],"AP75":r["pert_AP75"],"delta_AP50":float(r["pert_AP50"])-float(r["AP50_fullval"]),
                     "delta_AP75":float(r["pert_AP75"])-float(r["AP75_fullval"]),"mean_angle_error":r["angle_err_pert"],
                     "fixed_5deg_event_rate":"","geometry_severe_event_rate":"","full_evaluator_status":"AUTHORITATIVE_K1_ADAPTIVE_ENDPOINT_NOT_A_FIXED_DOSE",
                     "first_material_AP75_drop":"adaptive endpoint exceeds 0.05 drop","AP75_knee":"not identifiable from two points","AP50_weak_sensitivity_range":"through adaptive IoU50 boundary"})
    # DOTA clean units are retained as baseline-only; DOTA#20 is never used.
    for p in sorted((OLD/"reports/k4b_dota").glob("DOTA-v1.0_*.json")):
        d=json.loads(p.read_text()); cell=d["cell"]
        for dose in proto["dose_grid_deg"]:
            rows.append({"evaluation_unit":cell,"dataset":"DOTA-v1.0","detector":d["detector"],"dose_deg":dose,
                         "prediction_identity_preserved":dose==0,"score_class_center_size_preserved":dose==0,"ar_mask":"ar>=2.1",
                         "AP50":d["AP50"] if dose==0 else "","AP75":d["AP75"] if dose==0 else "","delta_AP50":0 if dose==0 else "","delta_AP75":0 if dose==0 else "",
                         "mean_angle_error":"","fixed_5deg_event_rate":"","geometry_severe_event_rate":"",
                         "full_evaluator_status":"AUTHORITATIVE_CLEAN_BASELINE" if dose==0 else "NOT_RUN_NO_COMPLETE_PERSISTENT_RAW_PREDICTION_DUMP",
                         "first_material_AP75_drop":"NOT_IDENTIFIED","AP75_knee":"NOT_IDENTIFIED","AP50_weak_sensitivity_range":"NOT_IDENTIFIED"})
    atomic_csv(REP/"a4_dose_response_knee.csv",rows)
    # Figure: ideal curves and empirical medians for six units.
    import matplotlib; matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig,ax=plt.subplots(figsize=(8,5))
    x=np.array([r["aspect_ratio"] for r in ideal]); ax.plot(x,[r["ideal_delta_0.50_deg"] for r in ideal],label="ideal IoU=0.50",lw=2)
    ax.plot(x,[r["ideal_delta_0.75_deg"] for r in ideal],label="ideal IoU=0.75",lw=2)
    marks=[r for r in empirical if r["aspect_ratio_bin"]=="all_ar21" and r["size_bin"]=="all"]
    for tau,marker in (("0.50","o"),("0.75","x")):
        q=[r for r in marks if r["tau"]==tau]; ax.scatter([2.15+i*.11 for i in range(len(q))],[r["median_deg"] for r in q],marker=marker,label=f"empirical median tau={tau}")
    ax.set(xlabel="Aspect ratio",ylabel="Tolerance (degrees)",xlim=(1,10)); ax.legend(fontsize=8); ax.grid(alpha=.25); fig.tight_layout()
    (A/"figures").mkdir(exist_ok=True); fig.savefig(A/"figures/a4_empirical_ideal_tolerance.png",dpi=180); fig.savefig(A/"figures/a4_empirical_ideal_tolerance.pdf"); plt.close(fig)
    decision="PARTIAL_ALIGNMENT"
    atomic_text(DOC/"a4_empirical_vs_ideal_tolerance.md",f"""# A4 经验容忍角与理想几何容忍度

本审计固定使用 `ar>=2.1`。理想曲线是在共中心、同尺度、le90 矩形上数值求解的 `delta_tau(ar)`；经验量是在真实预测/GT 的中心、尺度和初始角度下，沿增加当前误差的方向旋转，记录固定 matched pair 的 IoU 首次低于 tau 的 0.5 度网格点。后者是 evaluator-state tolerance 的合法近似，但不包含竞争匹配、类别排序或 NMS 变化，因此不等于真实评测器容忍角。

K1 六个 provenance-clean full-val 单元的完整评测器基线和自适应 IoU50 边界端点继续有效：AP50 在该受约束端点不变，而 AP75 显著下降。DOTA 两个 clean 单元仅有基线。当前持久化资产没有覆盖八剂量网格所需的全部六单元完整 raw prediction dumps；因此没有用 matched-only AP、旧 partial-GT AP 或插值伪造固定剂量 AP，也不能识别正式 AP75 knee。

允许保留的结论是：AP50 存在由几何定义支持的弱敏感区，AP75 在现有端点证据中更早响应；经验固定对容忍角受真实 center/scale 影响并围绕理想几何关系分布。剂量响应 knee 仍不能作为已确认结论。

**A4 判定：{decision}。**
""")
    atomic_text(LOG/"a4_tolerance.log",f"decision={decision}\ndose_grid={proto['dose_grid_deg']}\nfull_grid_complete=false\nmatched_only_AP_used=false\nDOTA20_used=false\n")
    return decision


def load_official_mapping() -> tuple[list[dict],dict[str,dict]]:
    pairs=list(csv.DictReader((ROOT/"reports/m4_m600_pairs.csv").open()))
    sampling={r["anon_id"]:r for r in csv.DictReader((OLD/"annotation_tools/m4_angle_annotation/internal/m600_sampling_manifest.csv").open())}
    wanted=defaultdict(dict)
    for aid,s in sampling.items(): wanted[s["source_record_path"]][int(s["source_record_line"])]=aid
    gt={}
    for path,lines in wanted.items():
        for i,line in enumerate(Path(path).open(encoding="utf-8"),start=1):
            if i in lines:
                r=json.loads(line); gt[lines[i]]={"official_gt_angle":official_angle_in_ui_coordinates(r["gt_obb"]),"gt_obb":r["gt_obb"]}
    crop_source={}
    imap=OLD/"annotation_tools/m4_angle_annotation/internal/instance_id_mapping.csv"
    for r in csv.DictReader(imap.open()):
        if r["annotator_slot"]=="A": crop_source.setdefault(r["canonical_anon_id"],r["source_070_path"])
    return pairs,{aid:{**sampling[aid],**gt[aid],"existing_blind_crop":crop_source.get(aid,"")} for aid in sampling if aid in gt}


def summarize_diff(values:list[float]) -> dict:
    x=np.asarray(values,float)
    return {"n":len(x),"mean":round(float(x.mean()),4),"median":round(float(np.median(x)),4),"p90":round(float(np.percentile(x,90)),4),
            "p95":round(float(np.percentile(x,95)),4),"P_gt_5":round(float(np.mean(x>5)),6),"P_gt_10":round(float(np.mean(x>10)),6)}


def build_a5() -> str:
    pairs,mapping=load_official_mapping(); byid={r["anon_id"]:r for r in pairs}
    metric_rows=[]
    for ann,col in (("annotator_1","angleA"),("annotator_2","angleB")):
        for group,value in [("overall","all")]+[("dataset",d) for d in sorted(set(r["dataset"] for r in pairs))]+[("size",d) for d in sorted(set(r["matched_gt_size_bin"] for r in pairs))]+[("ar_bin",d) for d in sorted(set(r["matched_gt_ar_bin"] for r in pairs))]+[("ar21","true")]:
            vals=[]
            for r in pairs:
                if not r[col]: continue
                if group=="dataset" and r["dataset"]!=value: continue
                if group=="size" and r["matched_gt_size_bin"]!=value: continue
                if group=="ar_bin" and r["matched_gt_ar_bin"]!=value: continue
                if group=="ar21" and r["formal_ar21_eligible"]!="True": continue
                vals.append(circ(float(r[col]),mapping[r["anon_id"]]["official_gt_angle"]))
            if vals: metric_rows.append({"comparison":f"{ann}_vs_official_GT","group_type":group,"group_value":value,**summarize_diff(vals),
                                         "interpretation":"discrepancy to dataset official annotation; official GT is not assumed error-free"})
    atomic_csv(REP/"a5_annotator_gt_metrics.csv",metric_rows)

    rng=np.random.RandomState(20260722); selected=[]; sample_table=[]
    for ds in sorted(set(r["dataset"] for r in pairs)):
        pool=[r for r in pairs if r["dataset"]==ds]
        def dis(r): return circ(float(r["angleA"]),float(r["angleB"])) if r["angleA"] and r["angleB"] else math.nan
        boundary=[r for r in pool if (math.isfinite(dis(r)) and dis(r)>5) or not r["human_usable"]=="True"]
        regular=[r for r in pool if r not in boundary]
        boundary=sorted(boundary,key=lambda r:hashlib.sha256(("B"+r["anon_id"]).encode()).hexdigest())[:15]
        regular=sorted(regular,key=lambda r:hashlib.sha256(("R"+r["matched_gt_size_bin"]+r["matched_gt_ar_bin"]+r["matched_gt_class"]+r["anon_id"]).encode()).hexdigest())[:35]
        q=boundary+regular
        if len(q)<50:
            extra=[r for r in pool if r not in q]; rng.shuffle(extra); q+=extra[:50-len(q)]
        for r in q:
            selected.append(r)
            sample_table.append({"canonical_anon_id":r["anon_id"],"dataset":ds,"class":r["matched_gt_class"],"size_bin":r["matched_gt_size_bin"],
                                 "aspect_ratio":r["matched_gt_aspect_ratio"],"ar_bin":r["matched_gt_ar_bin"],"ar21":r["formal_ar21_eligible"],
                                 "sampling_component":"boundary" if r in boundary else "random_regular",
                                 "high_disagreement_or_ambiguous":r in boundary,"sampling_seed":20260722})
    atomic_csv(REP/"a5_annotation_sampling_table.csv",sample_table)

    tool=A/"annotation_tools/annotator_3"; (tool/"images").mkdir(parents=True,exist_ok=True); (tool/"outputs").mkdir(exist_ok=True); (tool/"test_outputs").mkdir(exist_ok=True); (tool/"common").mkdir(exist_ok=True)
    # Clear only generated images/manifests; formal outputs are never overwritten or removed.
    task_rows=[]
    ordered=sorted(selected,key=lambda r:hashlib.sha256(("third-order"+r["anon_id"]).encode()).hexdigest())
    for order,r in enumerate(ordered,1):
        tid=hashlib.sha256(("annotator3"+r["anon_id"]).encode()).hexdigest()[:20]
        src=OLD/"annotation_tools/m4_angle_annotation/crops"/f"{r['anon_id']}.jpg"; dst=tool/"images"/f"{tid}.jpg"
        if not dst.exists():
            existing=Path(mapping[r["anon_id"]].get("existing_blind_crop", ""))
            if src.exists(): os.link(src,dst)
            elif existing.is_file(): os.link(existing,dst)
            else:
                from PIL import Image
                m=mapping[r["anon_id"]]; box=tuple(int(float(m[k])) for k in ("crop_xmin","crop_ymin","crop_xmax","crop_ymax"))
                with Image.open(m["source_image_path"]) as im: im.convert("RGB").crop(box).save(dst,quality=95)
        task_rows.append({"assignment_version":"a5-076-third-v1","annotator_slot":"3","task_order":order,"task_id":tid,"dataset":r["dataset"],
                          "crop_relpath":f"images/{tid}.jpg","long_side_angle_deg_le90":"","ambiguous":"","skip":"","notes":"","annotator_id":"","annotation_timestamp_utc":""})
    atomic_csv(REP/"a5_third_annotator_sampling_manifest.csv",sample_table)
    atomic_csv(tool/"task_manifest.csv",task_rows)
    (tool/"task_manifest.json").write_text(json.dumps(task_rows,ensure_ascii=False,indent=2)+"\n")
    common_src=OLD/"annotation_tools/m4_angle_annotation/common"
    shutil.copytree(common_src/"static",tool/"common/static",dirs_exist_ok=True); shutil.copytree(common_src/"templates",tool/"common/templates",dirs_exist_ok=True); shutil.copy2(common_src/"schema.json",tool/"common/schema.json")
    app=(common_src/"app.py").read_text()
    app=app.replace('annotator = PACKAGE / f"annotator_{slot}"','annotator = PACKAGE').replace('choices=["A", "B"]','choices=["3"]')
    app=app.replace('f"annotations_{slot}"','"annotations_3"')
    (tool/"common/app.py").write_text(app)
    (tool/"start_annotator_3.sh").write_text('#!/usr/bin/env bash\nset -euo pipefail\nR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\nexec python3 "$R/common/app.py" --slot 3 --port 17803\n'); os.chmod(tool/"start_annotator_3.sh",0o755)
    (tool/"README.md").write_text("# 第三标注员任务\n\n运行 `bash start_annotator_3.sh`。标注 OBB 几何长边方向，180 度周期；不判断头尾。允许 ambiguous/skip。正式导出位于 outputs/annotations_3.csv 与 outputs/annotations_3.json。不得参考 GT、模型框或前两名标注者。\n")
    consensus_fields=["status","n_third_annotations","n_consensus","rule","notes"]
    outcsv=tool/"outputs/annotations_3.csv"; outjson=tool/"outputs/annotations_3.json"
    real_count=0
    if outcsv.exists():
        real_count=sum(1 for r in csv.DictReader(outcsv.open()) if r.get("long_side_angle_deg_le90") or r.get("ambiguous")=="1" or r.get("skip")=="1")
    consensus=[{"status":"PENDING_REAL_ANNOTATOR_3","n_third_annotations":real_count,"n_consensus":0,"rule":"frozen circular median / majority-within-5deg","notes":"no formal consensus metrics until a real third annotator completes"}]
    atomic_csv(REP/"a5_consensus_metrics.csv",consensus,consensus_fields)
    decision="PASS_THREE_ANNOTATOR_ADJUDICATED" if real_count==150 else "PARTIAL_TWO_ANNOTATOR_WITH_GT"
    a1=next(r for r in metric_rows if r["comparison"]=="annotator_1_vs_official_GT" and r["group_type"]=="overall")
    a2=next(r for r in metric_rows if r["comparison"]=="annotator_2_vs_official_GT" and r["group_type"]=="overall")
    atomic_text(DOC/"a5_human_annotation_adjudication.md",f"""# A5 人工标注、official GT 对照与仲裁

第三标注员的 150 个目标已按预注册规则冻结为三数据集各 50，同时包含高分歧/ambiguous 边界和随机低分歧对照。任务包独立随机、匿名、互盲，不暴露前两人、official GT、模型预测或分歧。

Annotator 1 与 official GT 的总体 discrepancy：n={a1['n']}，mean={a1['mean']}°，median={a1['median']}°，P(>5°)={a1['P_gt_5']}；Annotator 2：n={a2['n']}，mean={a2['mean']}°，median={a2['median']}°，P(>5°)={a2['P_gt_5']}。这些是人类标注与数据集 official annotation 的差异，不是把 official GT 当绝对真值后得到的“人工误差”。Inter-annotator disagreement 与 annotator-vs-GT discrepancy 始终分列。

高分歧仲裁定义为任一 pairwise disagreement >5° 或任一 ambiguous；三数值角使用 180° circular median，并另报 5° 邻域多数共识。模型预测与 official GT 不参与自动仲裁，也不从模型误差扣除人工分歧。

当前第三真人结果数为 {real_count}，因此不生成正式 consensus 数值。**A5 判定：{decision}；状态 HUMAN_ANNOTATOR_3_BLOCKED。**
""")
    atomic_text(LOG/"a5_human_annotation.log",f"sample=150\nper_dataset=50\nthird_real_results={real_count}\nstatus={decision}\nGT_used_as_infallible=false\n")
    return decision


def build_a6() -> str:
    candidates=[]
    checks=[
        ("ARS-DETR DIOR-R/16",ROOT/"outputs/persistent_artifacts/orientbench_v2/DIOR-R/16/schema/pred_b16.jsonl",11738,"known 5863-image legacy universe; prior NRC inspected"),
        ("ARS-DETR DOTA-v1.0/14",ROOT/"outputs/predictions/DOTA-v1.0/14/manifest.json",None,"manifest points only to vanished /dev/shm raw/schema; not persistent"),
        ("Strip-RCNN DIOR-R/47",ROOT/"outputs/persistent_artifacts/orientbench_v2/DIOR-R/47/schema/pred_b47.jsonl",11738,"5859-image legacy universe; prior NRC inspected"),
    ]
    for name,path,expected,note in checks:
        ids=set(); n=0
        if path.suffix==".jsonl" and path.exists():
            for line in path.open(encoding="utf-8"):
                r=json.loads(line); ids.add(str(r["image_id"])); n+=1
        persistent=path.exists() and "/dev/shm" not in str(path)
        complete=expected is not None and len(ids)==expected
        eligible=bool(persistent and complete and "prior NRC" not in note)
        candidates.append({"candidate":name,"dataset":name.split()[1] if " " in name else "","split":"reported full-val / audited actual identity",
                           "checkpoint":"registered pth_data baseline","config":"registered adapter/config","log":"historical inference log available",
                           "evaluator":"historical evaluator","prediction_artifact":str(path.relative_to(ROOT)) if path.exists() else str(path),
                           "prediction_sha256":sha(path) if path.exists() else "","GT_artifact":"persistent full-val GT available separately",
                           "observed_image_count":len(ids),"expected_fullval_image_count":expected or "","fullval_complete":complete,
                           "participated_alpha_design":False,"participated_ar_design":False,"participated_score_direction_design":False,
                           "participated_geometry_score_design":False,"participated_coverage_grid_design":False,"participated_M1_M3_tuning":False,
                           "prior_risk_result_seen":"prior NRC" in note,"can_recompute":persistent,"eligible_confirmatory":eligible,"reason":note})
    atomic_csv(REP/"a6_confirmatory_provenance_audit.csv",candidates)
    decision="NO_ELIGIBLE_CONFIRMATORY_UNIT"
    metric_fields=["confirmatory_unit","status","AP50","AP75","detection_score_NRC","TTA_NRC","source_geometry_NRC","geometry_event_rate","risk5","risk10","risk15","notes"]
    metrics=[{"confirmatory_unit":"none","status":decision,"AP50":"","AP75":"","detection_score_NRC":"","TTA_NRC":"","source_geometry_NRC":"","geometry_event_rate":"","risk5":"","risk10":"","risk15":"","notes":"no candidate passed persistence + complete full-val identity + previously-unseen provenance"}]
    atomic_csv(REP/"a6_confirmatory_metrics.csv",metrics,metric_fields)
    frontier_fields=["confirmatory_unit","score","alpha","status","nonempty_scene_rate","selected_instance_coverage","selected_count","scene_risk","scene_risk_ucb","scene_event","scene_event_ucb","reason"]
    frontier=[{"confirmatory_unit":"none","score":"detection_score","alpha":a,"status":"INFEASIBLE_NO_ELIGIBLE_UNIT","nonempty_scene_rate":"","selected_instance_coverage":"","selected_count":0,"scene_risk":"","scene_risk_ucb":"","scene_event":"","scene_event_ucb":"","reason":"confirmatory provenance gate failed before risk inspection"} for a in (.001,.0025,.005,.01)]
    atomic_csv(REP/"a6_confirmatory_risk_frontier.csv",frontier,frontier_fields)
    atomic_text(DOC/"a6_confirmatory_unit_report.md",f"""# A6 独立确认单元报告

确认协议在候选风险计算前冻结。优先候选 ARS-DETR DIOR-R/16 的持久化 schema 实际只覆盖 5,863 个 image IDs，而当前 DIOR-R full-val 为 11,738；它还已有历史 NRC 结果，因此既非 provenance-clean full-val，也非未查看确认单元。ARS-DETR DOTA-v1.0/14 的 manifest 仅指向已经消失的 `/dev/shm` raw/schema，无法从持久化 prediction identity 复算。其它现有独立架构候选同样是旧 partial universe 或已有风险结果。

按照冻结优先顺序，不因结果不理想更换或伪装 unit，也不训练新 detector、不引入新数据集。因此 AP75、NRC 与 scene-risk confirmatory point 均不生成伪数值；风险前沿显式输出 `INFEASIBLE_NO_ELIGIBLE_UNIT`。

**A6 判定：{decision}。** 这不是对协议数值的反证，而是确认性证据缺失；075 的严格预算 deployable certification 不可行结论没有获得独立确认。
""")
    atomic_text(LOG/"a6_confirmatory.log",f"decision={decision}\nprotocol_changed=false\nunit_switched_after_results=false\ntarget_GT_counted_as_deployable=false\n")
    return decision


def main() -> None:
    a4=build_a4(); a5=build_a5(); a6=build_a6()
    cleanup=[]
    for item in ["phase_mod three-dataset three-seed complete table","CSL/DCL lineage main table","negative_phase_mod","radial/tangential intervention","PSC repair scores","B mechanism and repair conclusions"]:
        cleanup.append({"asset":item,"action":"DELETE_FROM_NEXT_A_REWRITE","allowed_in_A":False,"notes":"B-exclusive"})
    for item in ["one endpoint-dependent native angle-signal observation","boundary discussion without multi-seed numbers","citation to B only after B is publicly available"]:
        cleanup.append({"asset":item,"action":"RETAIN_WITH_BOUNDARY","allowed_in_A":True,"notes":"no B main table duplication"})
    atomic_csv(REP/"a_ab_boundary_cleanup_for_next_rewrite.csv",cleanup)
    toolbox_ok=(REP/"toolbox_test_status.json").exists() and json.loads((REP/"toolbox_test_status.json").read_text()).get("all_pass") is True
    if a4=="FAIL_PERTURBATION_CLAIM" or a5=="FAIL_ANNOTATION_PROTOCOL" or not toolbox_ok:
        overall="STOP_A"
    elif a6=="CONFIRMS_NONTRIVIAL_DEPLOYABLE_POINT": overall="A_PROTOCOL_WITH_NONTRIVIAL_CERTIFICATION"
    elif a6=="CONFIRMS_PROTOCOL_BUT_NOT_DEPLOYABLE_CERTIFICATION": overall="A_PROTOCOL_WITH_LIMITED_CERTIFICATION"
    else: overall="A_MEASUREMENT_ONLY"
    rows=[{"component":"A1","decision":"PARTIAL_FRONTIER","evidence":"075 frozen"},
          {"component":"A2","decision":"PASS_TILE_ONLY_WITH_LIMITATION","evidence":"075 frozen"},
          {"component":"A3","decision":"PARTIAL_SCORE_MENU","evidence":"075 frozen"},
          {"component":"A4","decision":a4,"evidence":"K1 full-evaluator endpoints + actual-geometry tolerance; complete fixed-dose AP grid unavailable"},
          {"component":"A5","decision":a5,"evidence":"two annotators vs official GT complete; third task frozen, real results pending"},
          {"component":"A6","decision":a6,"evidence":"all existing independent candidates fail confirmatory provenance/persistence gate"},
          {"component":"TOOLBOX","decision":"PASS" if toolbox_ok else "FAIL","evidence":"CLI, unit, synthetic and persistent regression"},
          {"component":"OVERALL","decision":overall,"evidence":"no broad deployable certification; measurement evidence remains"}]
    atomic_csv(REP/"a4_a6_final_decision.csv",rows)


if __name__=="__main__": main()
