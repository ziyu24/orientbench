"""Index official COG archive members against all 253 official metadata records."""
from __future__ import annotations
import argparse, csv, hashlib, json, tarfile
from collections import Counter
from pathlib import Path

def digest(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
 csv_path=a.root/'real/metadata_annotations/RarePlanes_Public_Metadata.csv'
 with csv_path.open(newline='') as f: rows=list(csv.DictReader(f))
 archives=[a.root/'real/tarballs/test/RarePlanes_test_PS-RGB_cog.tar.gz',a.root/'real/tarballs/train/RarePlanes_train_PS-RGB_cog.tar.gz']
 members=[]
 for arc in archives:
  with tarfile.open(arc,'r:gz') as t: members += [m.name for m in t.getmembers() if m.isfile() and m.name.lower().endswith(('.tif','.tiff'))]
 lower={name.lower():name for name in members}
 links=[]
 for r in rows:
  iid=r['image_id'].lower(); matches=sorted(v for k,v in lower.items() if iid in Path(k).stem)
  links.append({'image_id':r['image_id'],'loc_id':r['loc_id'],'cat_id':r['cat_id'],'members':matches})
 count=Counter(x['image_id'] for x in links)
 out={'protocol':'r010-official-cog-lineage-v1','archives':[{'path':str(x),'bytes':x.stat().st_size,'sha256':digest(x)} for x in archives], 'metadata_rows':len(rows),'unique_metadata_ids':len(count),'cog_members':len(members),'links':links,'all_one_to_one':len(rows)==253 and len(count)==253 and all(len(x['members'])==1 for x in links)}
 a.out.parent.mkdir(parents=True,exist_ok=True);a.out.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
