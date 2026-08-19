import hashlib,json
from pathlib import Path
root=Path('/home/rspip/cqc/pro/study/orientbench'); ids=Path('/home/rspip/cqc/data/dataset/HRSC2016/splits/val.txt').read_text().split()
out=root/'outputs/persistent_artifacts/orientbench_semantic_heading_r046_20260818/splits'; out.mkdir(parents=True,exist_ok=True)
fit=[]; cal=[]
for i in ids:
 (fit if int(hashlib.sha256(('r046|'+i).encode()).hexdigest()[-1],16)%2==0 else cal).append(i)
(out/'V_fit.txt').write_text('\n'.join(fit)+'\n'); (out/'V_cal.txt').write_text('\n'.join(cal)+'\n')
print(json.dumps({'fit':len(fit),'cal':len(cal)}))
