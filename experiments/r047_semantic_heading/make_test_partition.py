import hashlib,json
from pathlib import Path
root=Path('/home/rspip/cqc/pro/study/orientbench'); src=Path('/home/rspip/cqc/data/dataset/HRSC2016/splits/test.txt'); ids=src.read_text().split()
out=root/'outputs/persistent_artifacts/orientbench_semantic_heading_r047_20260818/partitions';out.mkdir(parents=True,exist_ok=True)
cal=[];audit=[]
for iid in ids:
 h=hashlib.sha256(('r047-test|'+iid).encode()).hexdigest()
 (cal if int(h[-2:],16)%2==0 else audit).append(iid)
cal=sorted(cal);audit=sorted(audit)
(out/'T_cal_ids.txt').write_text('\n'.join(cal)+'\n');(out/'T_audit_ids.txt').write_text('\n'.join(audit)+'\n')
meta={'schema_version':1,'source_split':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'source_count':len(ids),'T_cal_count':len(cal),'T_audit_count':len(audit),'T_cal_ids_sha256':hashlib.sha256(('\n'.join(cal)+'\n').encode()).hexdigest(),'T_audit_ids_sha256':hashlib.sha256(('\n'.join(audit)+'\n').encode()).hexdigest(),'semantic_xml_opened':False}
(out/'TEST_PARTITION_SEAL.json').write_text(json.dumps(meta,indent=2)+'\n');print(json.dumps(meta))
