"""build_k1_fullval_gt_065.py — build & persist full-val GT jsonl for the K1 table-1 cells.
Parses DOTA-txt annfiles -> {image_id, class_name, obb_cx/cy/w/h/theta (le90)} using mmrotate's
qbox2rbox (same convention as the evaluator). Persists to a NON-/dev/shm artifact dir + manifest
with n_images/n_gt/sha256. Datasets: DIOR-R test (expect 124445), FAIR1M val, SODA-A val_tiled.
"""
import os, glob, json, csv, hashlib
import numpy as np, torch
from mmrotate.structures.bbox import qbox2rbox

ROOT = "/home/rspip/cqc/pro/study/orientbench"
OUTDIR = f"{ROOT}/outputs/persistent_artifacts/k1_table1_fullval_065/gt"
os.makedirs(OUTDIR, exist_ok=True)
LOG = f"{ROOT}/top_journal_v3_reaudit_055/logs/k1_table1_gt_build_065.log"
os.makedirs(os.path.dirname(LOG), exist_ok=True)

SETS = {
    "DIOR-R_test": dict(
        ann=f"{ROOT}/top_journal_v3_reaudit_055/data_prep/DIOR/annfiles_dotaformat/test",
        expect_ngt=124445),
    "FAIR1M-v1.0_val": dict(
        ann="/home/rspip/cqc/data/dataset/fair1m1.0/split_ss_fair1m1.0/val/annfiles",
        expect_ngt=None),
    "SODA-A_val_tiled": dict(
        ann="/home/rspip/cqc/data/dataset/SODA-A/dota_format_tiled_ss/val_tiled/annfiles",
        expect_ngt=None),
}

def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""): h.update(b)
    return h.hexdigest()

def lg(m): open(LOG, "a").write(m + "\n"); print(m, flush=True)

def build(name, ann, expect):
    files = sorted(glob.glob(f"{ann}/*.txt"))
    out = f"{OUTDIR}/{name}_fullval_gt.jsonl"
    n_gt = 0; n_img = 0; classes = set()
    with open(out, "w") as w:
        for f in files:
            iid = os.path.basename(f)[:-4]; n_img += 1
            polys = []; names = []
            for line in open(f, errors="ignore"):
                p = line.split()
                if len(p) < 9: continue
                try: coords = [float(x) for x in p[:8]]
                except ValueError: continue
                polys.append(coords); names.append(p[8])
            if not polys: continue
            rb = qbox2rbox(torch.tensor(polys, dtype=torch.float32)).numpy()  # (N,5) le90
            for k in range(rb.shape[0]):
                classes.add(names[k])
                w.write(json.dumps(dict(image_id=iid, class_name=names[k],
                    obb_cx=float(rb[k, 0]), obb_cy=float(rb[k, 1]), obb_w=float(rb[k, 2]),
                    obb_h=float(rb[k, 3]), obb_theta=float(rb[k, 4]))) + "\n")
                n_gt += 1
    sh = sha256(out)
    ok = (expect is None) or (n_gt == expect)
    lg(f"[{name}] images={n_img} n_gt={n_gt} classes={len(classes)} expect={expect} OK={ok} sha={sh[:12]}")
    return dict(dataset_split=name, ann_dir=ann, gt_path=out, n_images=n_img, n_gt=n_gt,
                n_classes=len(classes), annotation_format="DOTA-txt poly8 -> qbox2rbox le90",
                sha256=sh, expect_ngt=expect, ngt_ok=ok,
                generation_command="python build_k1_fullval_gt_065.py", can_recompute="yes")

def main():
    open(LOG, "w").close()
    rows = [build(n, s["ann"], s["expect_ngt"]) for n, s in SETS.items()]
    man = f"{ROOT}/top_journal_v3_reaudit_055/reports/k1_table1_gt_manifest_065.csv"
    with open(man, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    # hard check DIOR
    dior = next(r for r in rows if r["dataset_split"] == "DIOR-R_test")
    if not dior["ngt_ok"]:
        lg(f"BLOCKER: DIOR-R test n_gt={dior['n_gt']} != 124445"); raise SystemExit(2)
    lg(f"WROTE manifest {man}")

if __name__ == "__main__":
    main()
