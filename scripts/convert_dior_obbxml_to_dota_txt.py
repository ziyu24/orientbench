"""Convert DIOR-R OBB XML annotations -> DOTA-txt (poly8) for mmrotate DOTADataset.
Outputs into an orientbench-owned prep dir (does NOT write into the shared dataset).
Images are symlinked (no copy). Split membership follows DIOR splits/*.txt (unchanged).
Usage: python scripts/convert_dior_obbxml_to_dota_txt.py
"""
import os, sys, csv, glob, xml.etree.ElementTree as ET
from multiprocessing import Pool
SRC="/home/rspip/cqc/data/dataset/DIOR"
XML=f"{SRC}/annfiles/obb"; IMG=f"{SRC}/images"; SPL=f"{SRC}/splits"
PREP="/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/data_prep/DIOR"
CLASSES=('airplane','airport','baseballfield','basketballcourt','bridge','chimney','dam',
 'Expressway-Service-area','Expressway-toll-station','golffield','groundtrackfield','harbor',
 'overpass','ship','stadium','storagetank','tenniscourt','trainstation','vehicle','windmill')
CLSSET=set(CLASSES)

def parse_one(xmlp):
    try:
        root=ET.parse(xmlp).getroot()
    except Exception as e:
        return (os.path.basename(xmlp),None,f"xml_parse_error:{e}")
    lines=[]; bad=0
    for obj in root.findall("object"):
        name=(obj.findtext("name") or "").strip()
        diff=(obj.findtext("difficult") or "0").strip()
        rb=obj.find("robndbox")
        if rb is None or name not in CLSSET: bad+=1; continue
        try:
            pts=[float(rb.findtext(k)) for k in
                 ("x_left_top","y_left_top","x_right_top","y_right_top",
                  "x_right_bottom","y_right_bottom","x_left_bottom","y_left_bottom")]
        except Exception: bad+=1; continue
        if any(p!=p for p in pts): bad+=1; continue
        lines.append(" ".join(f"{p:.1f}" for p in pts)+f" {name} {diff}")
    return (os.path.basename(xmlp)[:-4], lines, None if bad==0 else f"skipped_objs:{bad}")

def convert_split(split_name, ids, out_ann):
    os.makedirs(out_ann,exist_ok=True)
    xmls=[f"{XML}/{i}.xml" for i in ids if os.path.isfile(f"{XML}/{i}.xml")]
    missing=[i for i in ids if not os.path.isfile(f"{XML}/{i}.xml")]
    with Pool(40) as p:
        res=p.map(parse_one, xmls, chunksize=64)
    n_files=0; n_obj=0; n_empty=0; warns=0
    for iid,lines,warn in res:
        if lines is None: warns+=1; continue
        with open(f"{out_ann}/{iid}.txt","w") as f: f.write("\n".join(lines)+("\n" if lines else ""))
        n_files+=1; n_obj+=len(lines)
        if not lines: n_empty+=1
        if warn: warns+=1
    return dict(split=split_name,n_ids=len(ids),n_ann_written=n_files,n_missing_xml=len(missing),
                n_objects=n_obj,n_empty_ann=n_empty,n_warnings=warns)

def main():
    stats=[]
    for split, splitfile, imgsub in [("trainval","trainval.txt","trainval"),("test","test.txt","test")]:
        ids=[l.strip() for l in open(f"{SPL}/{splitfile}") if l.strip()]
        out_ann=f"{PREP}/annfiles_dotaformat/{split}"
        st=convert_split(split, ids, out_ann); stats.append(st)
        # symlink images (no copy)
        link=f"{PREP}/dotaformat_images/{split}"; os.makedirs(os.path.dirname(link),exist_ok=True)
        if os.path.islink(link) or os.path.exists(link):
            try: os.remove(link)
            except IsADirectoryError: pass
        os.symlink(f"{IMG}/{imgsub}", link)
        n_img=len(os.listdir(f"{IMG}/{imgsub}"))
        st["n_images_linked"]=n_img
        print(f"[{split}] ids={st['n_ids']} ann={st['n_ann_written']} obj={st['n_objects']} empty={st['n_empty_ann']} missing_xml={st['n_missing_xml']} imgs={n_img}",flush=True)
    # sanity CSV
    out=f"/home/rspip/cqc/pro/study/orientbench/top_journal_v3_reaudit_055/reports/r1_dataset_preflight_060.csv"
    with open(out,"w",newline="") as f:
        w=csv.DictWriter(f,fieldnames=["split","n_ids","n_ann_written","n_missing_xml","n_objects","n_empty_ann","n_warnings","n_images_linked"])
        w.writeheader(); w.writerows(stats)
    print("WROTE",out)
if __name__=="__main__": main()
