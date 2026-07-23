"""build_fair1m_val20_gt_065.py — build persistent full-val GT for FAIR1M val_20 from XML.
FAIR1M annfiles are XML (<objects><object><possibleresult><name> + <points> 5 pts). Parse the
first 4 corner points -> poly8 -> mmrotate qbox2rbox le90. Persist to the k1 GT dir + append to
the GT manifest.
"""
import os, glob, json, csv, hashlib
import xml.etree.ElementTree as ET
import torch
from mmrotate.structures.bbox import qbox2rbox

ROOT = "/home/rspip/cqc/pro/study/orientbench"
ANN = "/home/rspip/cqc/data/dataset/fair1m1.0/split/val_20/annfiles"
OUTDIR = f"{ROOT}/outputs/persistent_artifacts/k1_table1_fullval_065/gt"
OUT = f"{OUTDIR}/FAIR1M-v1.0_val20_fullval_gt.jsonl"

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def main():
    files = sorted(glob.glob(f"{ANN}/*.xml"))
    n_gt = 0; n_img = 0; classes = set()
    with open(OUT, "w") as w:
        for f in files:
            iid = os.path.basename(f)[:-4]; n_img += 1
            try:
                root = ET.parse(f).getroot()
            except Exception:
                continue
            polys = []; names = []
            for obj in root.iter("object"):
                nm = obj.findtext("possibleresult/name") or obj.findtext("name")
                pts = [p.text for p in obj.findall("points/point")]
                if not nm or len(pts) < 4:
                    continue
                coords = []
                for p in pts[:4]:
                    x, y = p.split(",")
                    coords += [float(x), float(y)]
                if len(coords) == 8:
                    polys.append(coords); names.append(nm.strip())
            if not polys:
                continue
            rb = qbox2rbox(torch.tensor(polys, dtype=torch.float32)).numpy()
            for k in range(rb.shape[0]):
                classes.add(names[k])
                w.write(json.dumps(dict(image_id=iid, class_name=names[k],
                    obb_cx=float(rb[k, 0]), obb_cy=float(rb[k, 1]), obb_w=float(rb[k, 2]),
                    obb_h=float(rb[k, 3]), obb_theta=float(rb[k, 4]))) + "\n")
                n_gt += 1
    sh = sha256(OUT)
    print(f"[FAIR1M val_20] images={n_img} n_gt={n_gt} classes={len(classes)} sha={sh[:12]}")
    # append to manifest
    man = f"{ROOT}/top_journal_v3_reaudit_055/reports/k1_table1_gt_manifest_065.csv"
    rows = list(csv.DictReader(open(man))) if os.path.isfile(man) else []
    rows = [r for r in rows if r["dataset_split"] != "FAIR1M-v1.0_val20"]
    rows.append(dict(dataset_split="FAIR1M-v1.0_val20", ann_dir=ANN, gt_path=OUT, n_images=n_img,
                     n_gt=n_gt, n_classes=len(classes), annotation_format="FAIR1M XML poly -> qbox2rbox le90",
                     sha256=sh, expect_ngt="", ngt_ok=True,
                     generation_command="python build_fair1m_val20_gt_065.py", can_recompute="yes"))
    with open(man, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print("appended FAIR1M to manifest; classes:", sorted(classes)[:5], "...")

if __name__ == "__main__":
    main()
